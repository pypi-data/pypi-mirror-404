"""
Data models for Virtualizor Forwarding Tool.

This module contains all dataclasses and enums used throughout the application.
"""

from __future__ import annotations

import base64
import ipaddress
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple


class Protocol(Enum):
    """Supported forwarding protocols."""

    HTTP = "HTTP"
    HTTPS = "HTTPS"
    TCP = "TCP"

    @classmethod
    def from_string(cls, value: str) -> "Protocol":
        """Create Protocol from string, case-insensitive."""
        return cls(value.upper())


class VMStatus(Enum):
    """Virtual machine status."""

    UP = "up"
    DOWN = "down"

    @classmethod
    def from_int(cls, value: int) -> "VMStatus":
        """Create VMStatus from integer (1=up, 0=down)."""
        return cls.UP if value == 1 else cls.DOWN


@dataclass
class HostProfile:
    """Configuration for a single Virtualizor host."""

    name: str
    api_url: str
    api_key: str
    api_pass: str  # Base64 encoded

    def get_decoded_pass(self) -> str:
        """Decode and return API password."""
        try:
            return base64.b64decode(self.api_pass).decode("utf-8")
        except Exception:
            # If not encoded, return as-is
            return self.api_pass

    @classmethod
    def create(
        cls, name: str, api_url: str, api_key: str, api_pass: str
    ) -> "HostProfile":
        """Create HostProfile with encoded password."""
        encoded_pass = base64.b64encode(api_pass.encode("utf-8")).decode("utf-8")
        return cls(name=name, api_url=api_url, api_key=api_key, api_pass=encoded_pass)

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "HostProfile":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Config:
    """Application configuration with multiple host profiles."""

    hosts: Dict[str, HostProfile] = field(default_factory=dict)
    default_host: Optional[str] = None
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "hosts": {name: profile.to_dict() for name, profile in self.hosts.items()},
            "default_host": self.default_host,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create from dictionary."""
        hosts = {
            name: HostProfile.from_dict(profile_data)
            for name, profile_data in data.get("hosts", {}).items()
        }
        return cls(
            hosts=hosts,
            default_host=data.get("default_host"),
            version=data.get("version", "1.0"),
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Config":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class VMInfo:
    """Virtual machine information."""

    vpsid: str
    hostname: str
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    status: VMStatus = VMStatus.DOWN

    def get_short_ipv6(self) -> str:
        """Return shortened IPv6 address."""
        if not self.ipv6 or self.ipv6 == "-":
            return "-"
        try:
            # Remove prefix if present
            ip_str = self.ipv6.split("/")[0]
            addr = ipaddress.IPv6Address(ip_str)
            return str(addr.compressed)
        except Exception:
            return self.ipv6

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "vpsid": self.vpsid,
            "hostname": self.hostname,
            "ipv4": self.ipv4,
            "ipv6": self.ipv6,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VMInfo":
        """Create from dictionary."""
        status = data.get("status", "down")
        if isinstance(status, int):
            vm_status = VMStatus.from_int(status)
        elif isinstance(status, str):
            vm_status = VMStatus(status.lower())
        else:
            vm_status = VMStatus.DOWN

        return cls(
            vpsid=str(data.get("vpsid", "")),
            hostname=data.get("hostname", ""),
            ipv4=data.get("ipv4"),
            ipv6=data.get("ipv6"),
            status=vm_status,
        )

    @classmethod
    def from_api_response(cls, vpsid: str, data: Dict[str, Any]) -> "VMInfo":
        """Create from Virtualizor API response."""
        ips = data.get("ips", {})
        ipv4 = None
        ipv6 = None

        for ip in ips.values():
            if isinstance(ip, str):
                if ":" in ip:
                    ipv6 = ip
                elif "." in ip:
                    ipv4 = ip

        status_val = data.get("status", 0)
        status = (
            VMStatus.from_int(int(status_val))
            if isinstance(status_val, (int, str))
            else VMStatus.DOWN
        )

        return cls(
            vpsid=str(vpsid),
            hostname=data.get("hostname", ""),
            ipv4=ipv4,
            ipv6=ipv6,
            status=status,
        )


@dataclass
class ForwardingRule:
    """Port forwarding rule configuration."""

    protocol: Protocol
    src_hostname: str
    src_port: int
    dest_ip: str
    dest_port: int
    id: Optional[str] = None  # None for new rules

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "protocol": self.protocol.value,
            "src_hostname": self.src_hostname,
            "src_port": self.src_port,
            "dest_ip": self.dest_ip,
            "dest_port": self.dest_port,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ForwardingRule":
        """Create from dictionary."""
        protocol = data.get("protocol", "TCP")
        if isinstance(protocol, str):
            protocol = Protocol.from_string(protocol)

        return cls(
            id=data.get("id"),
            protocol=protocol,
            src_hostname=data.get("src_hostname", ""),
            src_port=int(data.get("src_port", 0)),
            dest_ip=data.get("dest_ip", ""),
            dest_port=int(data.get("dest_port", 0)),
        )

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "ForwardingRule":
        """Create from Virtualizor API response."""
        return cls.from_dict(data)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "ForwardingRule":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class HAProxyConfig:
    """HAProxy configuration for port validation."""

    allowed_ports: Optional[str] = None
    reserved_ports: Optional[str] = None
    reserved_http_ports: Optional[str] = None
    src_ips: Optional[str] = None

    def get_allowed_ports_list(self) -> List[int]:
        """Parse allowed ports string to list of integers."""
        if not self.allowed_ports:
            return []
        return self._parse_port_string(self.allowed_ports)

    def get_reserved_ports_list(self) -> List[int]:
        """Parse reserved ports string to list of integers."""
        if not self.reserved_ports:
            return []
        return self._parse_port_string(self.reserved_ports)

    def get_first_src_ip(self) -> Optional[str]:
        """Get first source IP from src_ips."""
        if not self.src_ips:
            return None
        return self.src_ips.split(",")[0].strip()

    @staticmethod
    def _parse_port_string(port_str: str) -> List[int]:
        """Parse port string (e.g., '80,443,8000-9000') to list of ports."""
        ports = []
        for part in port_str.split(","):
            part = part.strip()
            if "-" in part:
                try:
                    start, end = part.split("-")
                    ports.extend(range(int(start), int(end) + 1))
                except ValueError:
                    continue
            else:
                try:
                    ports.append(int(part))
                except ValueError:
                    continue
        return ports

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "HAProxyConfig":
        """Create from Virtualizor API response."""
        haconfigs = data.get("server_haconfigs", {})
        if not haconfigs:
            return cls()

        # Handle both dict and list responses from API
        if isinstance(haconfigs, dict):
            config = next(iter(haconfigs.values()), {})
        elif isinstance(haconfigs, list) and haconfigs:
            config = haconfigs[0] if isinstance(haconfigs[0], dict) else {}
        else:
            return cls()

        return cls(
            allowed_ports=config.get("haproxy_allowedports"),
            reserved_ports=config.get("haproxy_reservedports"),
            reserved_http_ports=config.get("haproxy_reservedports_http"),
            src_ips=config.get("haproxy_src_ips"),
        )


@dataclass
class APIResponse:
    """API response wrapper."""

    success: bool
    message: Optional[str] = None
    error: Optional[Dict[str, Any]] = None
    raw_response: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_response(cls, data: Dict[str, Any]) -> "APIResponse":
        """Create from API response dictionary."""
        done = data.get("done", {})
        error = data.get("error")

        success = bool(done) and not error
        message = done.get("msg") if isinstance(done, dict) else None

        return cls(
            success=success,
            message=message,
            error=error if error and error != {} else None,
            raw_response=data,
        )

    def get_error_message(self) -> Optional[str]:
        """Extract error message from error dict."""
        if not self.error:
            return None

        if isinstance(self.error, str):
            return self.error

        if isinstance(self.error, dict):
            # Try common error keys
            for key in ["src_port", "src_hostname", "msg", "message"]:
                if key in self.error:
                    return str(self.error[key])
            # Return first value if any
            if self.error:
                return str(next(iter(self.error.values())))

        return str(self.error)


@dataclass
class ValidationResult:
    """Result of validation operation."""

    valid: bool
    message: Optional[str] = None
    suggestions: Optional[List[str]] = None

    @classmethod
    def success(cls) -> "ValidationResult":
        """Create successful validation result."""
        return cls(valid=True)

    @classmethod
    def failure(
        cls, message: str, suggestions: Optional[List[str]] = None
    ) -> "ValidationResult":
        """Create failed validation result."""
        return cls(valid=False, message=message, suggestions=suggestions or [])


@dataclass
class BatchResult:
    """Result of batch operation."""

    total: int
    succeeded: int
    failed: int
    errors: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def is_complete_success(self) -> bool:
        """Check if all operations succeeded."""
        return self.failed == 0

    @property
    def is_partial_success(self) -> bool:
        """Check if some operations succeeded."""
        return self.succeeded > 0 and self.failed > 0

    def add_success(self) -> None:
        """Record a successful operation."""
        self.succeeded += 1

    def add_failure(self, error: Dict[str, Any]) -> None:
        """Record a failed operation."""
        self.failed += 1
        self.errors.append(error)
