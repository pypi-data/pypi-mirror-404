"""
Virtualizor API client.

Handles all communication with the Virtualizor API.
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional
import requests
import urllib3

from .models import (
    HostProfile,
    VMInfo,
    ForwardingRule,
    HAProxyConfig,
    APIResponse,
)


class APIError(Exception):
    """API related errors."""


class APIConnectionError(APIError):
    """Connection related errors."""


class AuthenticationError(APIError):
    """Authentication related errors."""


class VirtualizorClient:
    """Client for Virtualizor API communication."""

    DEFAULT_TIMEOUT = 30

    def __init__(self, host_profile: HostProfile, verify_ssl: bool = False) -> None:
        """
        Initialize client with host profile.

        Args:
            host_profile: HostProfile containing API credentials.
            verify_ssl: Whether to verify SSL certificates. Default False
                       for self-signed certificates common in Virtualizor panels.
        """
        self._profile = host_profile
        self._base_url = host_profile.api_url
        self._api_key = host_profile.api_key
        self._api_pass = host_profile.get_decoded_pass()
        self._verify_ssl = verify_ssl

        # Suppress SSL warnings only when verification is disabled
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _build_url(self, action: str, **params: Any) -> str:
        """Build API URL with parameters."""
        base_params = {
            "act": action,
            "api": "json",
            "apikey": self._api_key,
            "apipass": self._api_pass,
        }
        base_params.update(params)

        query = "&".join(f"{k}={v}" for k, v in base_params.items())
        return f"{self._base_url}?{query}"

    def _request(
        self,
        action: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        **params: Any,
    ) -> Dict[str, Any]:
        """
        Make API request.

        Args:
            action: API action name.
            method: HTTP method (GET or POST).
            data: POST data if applicable.
            **params: Additional URL parameters.

        Returns:
            JSON response as dictionary.

        Raises:
            APIConnectionError: If connection fails.
            AuthenticationError: If authentication fails.
            APIError: For other API errors.
        """
        url = self._build_url(action, **params)

        try:
            if method.upper() == "POST":
                response = requests.post(
                    url,
                    data=data,
                    timeout=self.DEFAULT_TIMEOUT,
                    verify=self._verify_ssl,
                )
            else:
                response = requests.get(
                    url, timeout=self.DEFAULT_TIMEOUT, verify=self._verify_ssl
                )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout as exc:
            raise APIConnectionError(
                "Connection timeout. Please check:\n"
                "  - Network connectivity\n"
                "  - API URL is correct\n"
                "  - Server is responding"
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise APIConnectionError(
                f"Failed to connect to API:\n"
                f"  URL: {self._base_url}\n"
                f"  Error: {exc}\n"
                "Please verify the API URL and network connectivity."
            ) from exc
        except requests.exceptions.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Please verify:\n"
                    "  - API Key is correct\n"
                    "  - API Password is correct"
                ) from exc
            raise APIError(f"HTTP error: {exc}") from exc
        except requests.exceptions.JSONDecodeError as exc:
            raise APIError("Invalid JSON response from API") from exc
        except Exception as exc:
            raise APIError(f"API request failed: {exc}") from exc

    def test_connection(self) -> bool:
        """
        Test API connection and credentials.

        Returns:
            True if connection successful.

        Raises:
            APIConnectionError: If connection fails.
            AuthenticationError: If authentication fails.
        """
        try:
            response = self._request("listvs")
            # Check if we got valid response
            return "vs" in response or "error" not in response
        except (APIConnectionError, AuthenticationError):
            raise
        except Exception as exc:
            raise APIConnectionError(f"Connection test failed: {exc}") from exc

    def list_vms(self) -> List[VMInfo]:
        """
        Retrieve list of all VMs from server.

        Returns:
            List of VMInfo objects.

        Raises:
            APIError: If API call fails.
        """
        response = self._request("listvs")

        vs_data = response.get("vs", {})
        if not vs_data:
            return []

        vms = []
        for vpsid, vm_data in vs_data.items():
            try:
                vm = VMInfo.from_api_response(vpsid, vm_data)
                vms.append(vm)
            except (KeyError, ValueError, TypeError):
                continue

        return vms

    def get_forwarding(self, vpsid: str) -> List[ForwardingRule]:
        """
        Get forwarding rules for specific VM.

        Args:
            vpsid: VM ID.

        Returns:
            List of ForwardingRule objects.
        """
        response = self._request("managevdf", svs=vpsid)

        haproxy_data = response.get("haproxydata", {})
        if not haproxy_data:
            return []

        # Handle both dict and list responses from API
        rules = []
        if isinstance(haproxy_data, dict):
            rule_items = haproxy_data.values()
        elif isinstance(haproxy_data, list):
            rule_items = haproxy_data
        else:
            return []

        for rule_data in rule_items:
            try:
                rule = ForwardingRule.from_api_response(rule_data)
                rules.append(rule)
            except (KeyError, ValueError, TypeError):
                continue

        return rules

    def add_forwarding(self, vpsid: str, rule: ForwardingRule) -> APIResponse:
        """
        Add new forwarding rule.

        Args:
            vpsid: VM ID.
            rule: ForwardingRule to add.

        Returns:
            APIResponse with result.
        """
        data = {
            "vdf_action": "addvdf",
            "protocol": rule.protocol.value,
            "src_hostname": rule.src_hostname,
            "src_port": str(rule.src_port),
            "dest_ip": rule.dest_ip,
            "dest_port": str(rule.dest_port),
        }

        response = self._request("managevdf", method="POST", data=data, svs=vpsid)
        return APIResponse.from_response(response)

    def edit_forwarding(
        self, vpsid: str, vdfid: str, rule: ForwardingRule
    ) -> APIResponse:
        """
        Edit existing forwarding rule.

        Args:
            vpsid: VM ID.
            vdfid: Forwarding rule ID.
            rule: Updated ForwardingRule.

        Returns:
            APIResponse with result.
        """
        data = {
            "vdf_action": "editvdf",
            "vdfid": vdfid,
            "protocol": rule.protocol.value,
            "src_hostname": rule.src_hostname,
            "src_port": str(rule.src_port),
            "dest_ip": rule.dest_ip,
            "dest_port": str(rule.dest_port),
        }

        response = self._request("managevdf", method="POST", data=data, svs=vpsid)
        return APIResponse.from_response(response)

    def delete_forwarding(self, vpsid: str, vdfids: List[str]) -> APIResponse:
        """
        Delete forwarding rules.

        Args:
            vpsid: VM ID.
            vdfids: List of forwarding rule IDs to delete.

        Returns:
            APIResponse with result.
        """
        data = {
            "vdf_action": "delvdf",
            "ids": ",".join(vdfids),
        }

        response = self._request("managevdf", method="POST", data=data, svs=vpsid)
        return APIResponse.from_response(response)

    def get_server_config(self, vpsid: str) -> HAProxyConfig:
        """
        Get HAProxy configuration for port validation.

        Args:
            vpsid: VM ID.

        Returns:
            HAProxyConfig object.
        """
        response = self._request("managevdf", svs=vpsid, novnc="6710", do="add")
        return HAProxyConfig.from_api_response(response)

    def get_vm_internal_ip(self, vpsid: str) -> Optional[str]:
        """
        Get internal IPv4 address of VM.

        Args:
            vpsid: VM ID.

        Returns:
            IPv4 address string or None.
        """
        vms = self.list_vms()
        for vm in vms:
            if vm.vpsid == str(vpsid):
                return vm.ipv4
        return None


# Backward compatibility alias
ConnectionError = APIConnectionError
