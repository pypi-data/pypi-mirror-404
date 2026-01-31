"""
Virtualizor Forwarding Tool

CLI tool for managing domain/port forwarding in Virtualizor VPS environments
with multi-host support and Rich TUI.
"""

__version__ = "1.0.7"
__author__ = "Rizz"
__email__ = "rizkyadhypratama@gmail.com"
__github__ = "https://github.com/iam-rizz/python-domain-forwarding-virtualizor"
__telegram__ = "https://t.me/rizzid03"
__forum__ = "https://t.me/IPv6Indonesia"
__pypi__ = "virtualizor-forwarding"

from .models import (
    Protocol,
    VMStatus,
    HostProfile,
    Config,
    VMInfo,
    ForwardingRule,
    HAProxyConfig,
    APIResponse,
    ValidationResult,
    BatchResult,
)
from .config import ConfigManager
from .api import VirtualizorClient, APIError, APIConnectionError, AuthenticationError
from .tui import TUIRenderer
from .cli import CLI, main

__all__ = [
    # Models
    "Protocol",
    "VMStatus",
    "HostProfile",
    "Config",
    "VMInfo",
    "ForwardingRule",
    "HAProxyConfig",
    "APIResponse",
    "ValidationResult",
    "BatchResult",
    # Core classes
    "ConfigManager",
    "VirtualizorClient",
    "TUIRenderer",
    "CLI",
    "main",
    # Exceptions
    "APIError",
    "APIConnectionError",
    "AuthenticationError",
]
