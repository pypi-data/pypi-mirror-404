"""
VM Manager service.

Handles virtual machine related operations.
"""

from __future__ import annotations

from typing import List, Optional

from ..api import VirtualizorClient
from ..models import VMInfo, VMStatus


class VMManager:
    """Manages virtual machine operations."""

    def __init__(self, client: VirtualizorClient) -> None:
        """
        Initialize VM manager with API client.

        Args:
            client: VirtualizorClient instance.
        """
        self._client = client

    def list_all(self, status_filter: Optional[VMStatus] = None) -> List[VMInfo]:
        """
        List all VMs with optional status filter.

        Args:
            status_filter: Filter by VMStatus (UP or DOWN).

        Returns:
            List of VMInfo objects.
        """
        vms = self._client.list_vms()

        if status_filter:
            vms = [vm for vm in vms if vm.status == status_filter]

        return vms

    def get_vm(self, vpsid: str) -> Optional[VMInfo]:
        """
        Get specific VM by ID.

        Args:
            vpsid: VM ID.

        Returns:
            VMInfo object or None if not found.
        """
        vms = self._client.list_vms()
        for vm in vms:
            if vm.vpsid == str(vpsid):
                return vm
        return None

    def get_internal_ip(self, vpsid: str) -> Optional[str]:
        """
        Get internal IPv4 address of VM.

        Args:
            vpsid: VM ID.

        Returns:
            IPv4 address string or None.
        """
        vm = self.get_vm(vpsid)
        return vm.ipv4 if vm else None

    def vm_exists(self, vpsid: str) -> bool:
        """
        Check if VM exists.

        Args:
            vpsid: VM ID.

        Returns:
            True if VM exists.
        """
        return self.get_vm(vpsid) is not None

    def get_vm_count(self) -> int:
        """Get total number of VMs."""
        return len(self._client.list_vms())

    def get_single_vm(self) -> Optional[VMInfo]:
        """
        Get VM if only one exists.

        Returns:
            VMInfo if exactly one VM exists, None otherwise.
        """
        vms = self._client.list_vms()
        if len(vms) == 1:
            return vms[0]
        return None
