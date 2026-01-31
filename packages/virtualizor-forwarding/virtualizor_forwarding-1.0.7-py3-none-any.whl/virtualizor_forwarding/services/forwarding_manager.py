"""
Forwarding Manager service.

Handles port forwarding operations with validation.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from ..api import VirtualizorClient
from ..models import (
    ForwardingRule,
    HAProxyConfig,
    APIResponse,
    ValidationResult,
    Protocol,
)


class ForwardingManager:
    """Manages port forwarding operations."""

    def __init__(self, client: VirtualizorClient) -> None:
        """
        Initialize forwarding manager with API client.

        Args:
            client: VirtualizorClient instance.
        """
        self._client = client

    def list_rules(self, vpsid: str) -> List[ForwardingRule]:
        """
        List all forwarding rules for VM.

        Args:
            vpsid: VM ID.

        Returns:
            List of ForwardingRule objects.
        """
        return self._client.get_forwarding(vpsid)

    def add_rule(self, vpsid: str, rule: ForwardingRule) -> APIResponse:
        """
        Add new forwarding rule with validation.

        Args:
            vpsid: VM ID.
            rule: ForwardingRule to add.

        Returns:
            APIResponse with result.
        """
        return self._client.add_forwarding(vpsid, rule)

    def edit_rule(self, vpsid: str, vdfid: str, rule: ForwardingRule) -> APIResponse:
        """
        Edit existing forwarding rule.

        Args:
            vpsid: VM ID.
            vdfid: Forwarding rule ID.
            rule: Updated ForwardingRule.

        Returns:
            APIResponse with result.
        """
        return self._client.edit_forwarding(vpsid, vdfid, rule)

    def delete_rules(self, vpsid: str, vdfids: List[str]) -> APIResponse:
        """
        Delete forwarding rules.

        Args:
            vpsid: VM ID.
            vdfids: List of forwarding rule IDs.

        Returns:
            APIResponse with result.
        """
        return self._client.delete_forwarding(vpsid, vdfids)

    def get_rule_by_id(self, vpsid: str, vdfid: str) -> Optional[ForwardingRule]:
        """
        Get specific forwarding rule by ID.

        Args:
            vpsid: VM ID.
            vdfid: Forwarding rule ID.

        Returns:
            ForwardingRule or None if not found.
        """
        rules = self.list_rules(vpsid)
        for rule in rules:
            if rule.id == vdfid:
                return rule
        return None

    def get_haproxy_config(self, vpsid: str) -> HAProxyConfig:
        """
        Get HAProxy configuration for port validation.

        Args:
            vpsid: VM ID.

        Returns:
            HAProxyConfig object.
        """
        return self._client.get_server_config(vpsid)

    def validate_port(
        self,
        port: int,
        haproxy_config: HAProxyConfig,
        protocol: Optional[Protocol] = None,
    ) -> ValidationResult:
        """
        Validate port against HAProxy configuration.

        Args:
            port: Port number to validate.
            haproxy_config: HAProxy configuration.
            protocol: Optional protocol for special handling.

        Returns:
            ValidationResult with validation status.
        """
        # Basic port range validation
        if not isinstance(port, int) or port < 1 or port > 65535:
            return ValidationResult.failure(
                "Port must be a number between 1-65535",
                suggestions=["Use a port number in valid range (1-65535)"],
            )

        # Allow standard ports for HTTP/HTTPS
        if protocol == Protocol.HTTP and port == 80:
            return ValidationResult.success()
        if protocol == Protocol.HTTPS and port == 443:
            return ValidationResult.success()

        # Check reserved ports
        reserved_ports = haproxy_config.get_reserved_ports_list()
        if port in reserved_ports:
            suggestions = []
            if haproxy_config.allowed_ports:
                suggestions.append(f"Allowed ports: {haproxy_config.allowed_ports}")
            if haproxy_config.reserved_ports:
                suggestions.append(f"Reserved ports: {haproxy_config.reserved_ports}")

            return ValidationResult.failure(
                f"Port {port} is already reserved/in use", suggestions=suggestions
            )

        # Check allowed ports (if restriction exists)
        allowed_ports = haproxy_config.get_allowed_ports_list()
        if allowed_ports and port not in allowed_ports:
            return ValidationResult.failure(
                f"Port {port} is not in allowed ports list",
                suggestions=[f"Allowed ports: {haproxy_config.allowed_ports}"],
            )

        return ValidationResult.success()

    @staticmethod
    def auto_configure_ports(protocol: Protocol) -> Tuple[Optional[int], Optional[int]]:
        """
        Get auto-configured ports based on protocol.

        Args:
            protocol: Protocol type.

        Returns:
            Tuple of (src_port, dest_port) or (None, None) for TCP.
        """
        if protocol == Protocol.HTTP:
            return (80, 80)
        elif protocol == Protocol.HTTPS:
            return (443, 443)
        else:  # TCP
            return (None, None)

    def get_source_ip_for_tcp(self, vpsid: str) -> Optional[str]:
        """
        Get source IP from HAProxy config for TCP protocol.

        Args:
            vpsid: VM ID.

        Returns:
            Source IP string or None.
        """
        config = self.get_haproxy_config(vpsid)
        return config.get_first_src_ip()

    @staticmethod
    def merge_rule_update(
        current: ForwardingRule,
        protocol: Optional[Protocol] = None,
        src_hostname: Optional[str] = None,
        src_port: Optional[int] = None,
        dest_port: Optional[int] = None,
        dest_ip: Optional[str] = None,
    ) -> ForwardingRule:
        """
        Merge partial update with current rule values.

        Args:
            current: Current ForwardingRule.
            protocol: New protocol or None to keep current.
            src_hostname: New hostname or None to keep current.
            src_port: New source port or None to keep current.
            dest_port: New destination port or None to keep current.
            dest_ip: New destination IP or None to keep current.

        Returns:
            New ForwardingRule with merged values.
        """
        return ForwardingRule(
            id=current.id,
            protocol=protocol if protocol is not None else current.protocol,
            src_hostname=(
                src_hostname if src_hostname is not None else current.src_hostname
            ),
            src_port=src_port if src_port is not None else current.src_port,
            dest_ip=dest_ip if dest_ip is not None else current.dest_ip,
            dest_port=dest_port if dest_port is not None else current.dest_port,
        )

    @staticmethod
    def parse_comma_ids(ids_string: str) -> List[str]:
        """
        Parse comma-separated IDs string.

        Args:
            ids_string: Comma-separated IDs (e.g., "1,2,3").

        Returns:
            List of trimmed ID strings.
        """
        if not ids_string:
            return []
        return [id_str.strip() for id_str in ids_string.split(",") if id_str.strip()]
