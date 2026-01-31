"""
TUI (Text User Interface) components using Rich library.

Provides beautiful terminal output with tables, panels, and prompts.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Iterator

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.tree import Tree
from rich.text import Text
from rich.style import Style

from .models import VMInfo, ForwardingRule, HostProfile, Protocol, VMStatus


class TUIRenderer:
    """Rich-based TUI renderer for terminal output."""

    # Protocol colors
    PROTOCOL_COLORS = {
        Protocol.HTTP: "green",
        Protocol.HTTPS: "cyan",
        Protocol.TCP: "yellow",
    }

    # Status colors
    STATUS_COLORS = {
        VMStatus.UP: "green",
        VMStatus.DOWN: "red",
    }

    def __init__(
        self, console: Optional[Console] = None, no_color: bool = False
    ) -> None:
        """
        Initialize TUI renderer.

        Args:
            console: Rich Console instance (creates new if None).
            no_color: Disable colors if True.
        """
        self._console = console or Console(no_color=no_color, force_terminal=True)
        self._no_color = no_color

    @property
    def console(self) -> Console:
        """Get console instance."""
        return self._console

    def print(self, *args: Any, **kwargs: Any) -> None:
        """Print to console."""
        self._console.print(*args, **kwargs)

    def print_error(self, message: str) -> None:
        """Print error message."""
        self._console.print(f"[red]✗[/red] {message}")

    def print_success(self, message: str) -> None:
        """Print success message."""
        self._console.print(f"[green]✓[/green] {message}")

    def print_warning(self, message: str) -> None:
        """Print warning message."""
        self._console.print(f"[yellow]![/yellow] {message}")

    def print_info(self, message: str) -> None:
        """Print info message."""
        self._console.print(f"[blue]ℹ[/blue] {message}")

    def render_vm_table(
        self, vms: List[VMInfo], title: str = "Virtual Machines"
    ) -> None:
        """
        Render VM list as Rich table.

        Args:
            vms: List of VMInfo objects.
            title: Table title.
        """
        table = Table(title=title, show_header=True, header_style="bold")
        table.add_column("VPSID", style="cyan", justify="right")
        table.add_column("Hostname", style="white")
        table.add_column("IPv4", style="white")
        table.add_column("IPv6", style="dim")
        table.add_column("Status", justify="center")

        for vm in vms:
            status_color = self.STATUS_COLORS.get(vm.status, "white")
            status_text = f"[{status_color}]{vm.status.value.upper()}[/{status_color}]"

            table.add_row(
                vm.vpsid,
                vm.hostname,
                vm.ipv4 or "-",
                vm.get_short_ipv6(),
                status_text,
            )

        self._console.print(table)

    def render_forwarding_table(
        self, rules: List[ForwardingRule], title: str = "Forwarding Rules"
    ) -> None:
        """
        Render forwarding rules as Rich table.

        Args:
            rules: List of ForwardingRule objects.
            title: Table title.
        """
        table = Table(title=title, show_header=True, header_style="bold")
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Protocol", justify="center")
        table.add_column("Source", style="white")
        table.add_column("Destination", style="white")

        for rule in rules:
            proto_color = self.PROTOCOL_COLORS.get(rule.protocol, "white")
            proto_text = f"[{proto_color}]{rule.protocol.value}[/{proto_color}]"

            source = f"{rule.src_hostname}:{rule.src_port}"
            dest = f"{rule.dest_ip}:{rule.dest_port}"

            table.add_row(rule.id or "-", proto_text, source, dest)

        self._console.print(table)

    def render_host_tree(
        self, hosts: Dict[str, HostProfile], default_host: Optional[str] = None
    ) -> None:
        """
        Render host profiles as Rich tree.

        Args:
            hosts: Dictionary of host profiles.
            default_host: Name of default host.
        """
        tree = Tree("[bold]Configured Hosts[/bold]")

        for name, profile in hosts.items():
            is_default = name == default_host
            label = f"[cyan]{name}[/cyan]"
            if is_default:
                label += " [green](default)[/green]"

            branch = tree.add(label)
            branch.add(f"URL: {profile.api_url}")
            branch.add(f"API Key: {profile.api_key[:8]}...")

        self._console.print(tree)

    def render_confirmation(self, title: str, data: Dict[str, Any]) -> None:
        """
        Render confirmation panel.

        Args:
            title: Panel title.
            data: Key-value data to display.
        """
        content = "\n".join(f"[cyan]{k}:[/cyan] {v}" for k, v in data.items())
        panel = Panel(content, title=title, border_style="blue")
        self._console.print(panel)

    def render_comparison(self, before: ForwardingRule, after: ForwardingRule) -> None:
        """
        Render before/after comparison table.

        Args:
            before: Original ForwardingRule.
            after: Updated ForwardingRule.
        """
        table = Table(title="Changes", show_header=True, header_style="bold")
        table.add_column("Field", style="cyan")
        table.add_column("Before", style="red")
        table.add_column("After", style="green")

        fields = [
            ("Protocol", before.protocol.value, after.protocol.value),
            ("Source Host", before.src_hostname, after.src_hostname),
            ("Source Port", str(before.src_port), str(after.src_port)),
            ("Dest IP", before.dest_ip, after.dest_ip),
            ("Dest Port", str(before.dest_port), str(after.dest_port)),
        ]

        for field_name, old_val, new_val in fields:
            if old_val != new_val:
                table.add_row(field_name, old_val, new_val)

        self._console.print(table)

    def render_rule_detail(self, rule: ForwardingRule) -> None:
        """
        Render single rule detail panel.

        Args:
            rule: ForwardingRule to display.
        """
        proto_color = self.PROTOCOL_COLORS.get(rule.protocol, "white")
        content = (
            f"[cyan]ID:[/cyan] {rule.id or 'New'}\n"
            f"[cyan]Protocol:[/cyan] [{proto_color}]{rule.protocol.value}[/{proto_color}]\n"
            f"[cyan]Source:[/cyan] {rule.src_hostname}:{rule.src_port}\n"
            f"[cyan]Destination:[/cyan] {rule.dest_ip}:{rule.dest_port}"
        )
        panel = Panel(content, title="Forwarding Rule", border_style="blue")
        self._console.print(panel)

    # Prompt methods
    def prompt_select(
        self, message: str, choices: List[str], default: Optional[str] = None
    ) -> str:
        """
        Prompt user to select from choices.

        Args:
            message: Prompt message.
            choices: List of choices.
            default: Default choice.

        Returns:
            Selected choice.
        """
        choices_str = ", ".join(choices)
        prompt_msg = f"{message} [{choices_str}]"
        while True:
            result = Prompt.ask(prompt_msg, default=default, console=self._console)
            if result in choices:
                return result
            self.print_error(f"Invalid choice. Please select from: {choices_str}")

    def prompt_input(self, message: str, default: Optional[str] = None) -> str:
        """
        Prompt user for text input.

        Args:
            message: Prompt message.
            default: Default value.

        Returns:
            User input.
        """
        return Prompt.ask(message, default=default or "", console=self._console)

    def prompt_int(self, message: str, default: Optional[int] = None) -> int:
        """
        Prompt user for integer input.

        Args:
            message: Prompt message.
            default: Default value.

        Returns:
            Integer input.
        """
        return IntPrompt.ask(message, default=default, console=self._console)

    def prompt_confirm(self, message: str, default: bool = False) -> bool:
        """
        Prompt user for confirmation.

        Args:
            message: Prompt message.
            default: Default value.

        Returns:
            True if confirmed.
        """
        return Confirm.ask(message, default=default, console=self._console)

    @contextmanager
    def show_spinner(self, message: str) -> Iterator[None]:
        """
        Show spinner during operation.

        Args:
            message: Spinner message.

        Yields:
            None.
        """
        with self._console.status(f"[bold blue]{message}[/bold blue]"):
            yield

    @contextmanager
    def show_progress(
        self, total: int, description: str = "Processing"
    ) -> Iterator[Progress]:
        """
        Show progress bar for batch operations.

        Args:
            total: Total items.
            description: Progress description.

        Yields:
            Progress instance.
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self._console,
        ) as progress:
            task = progress.add_task(description, total=total)
            progress._task_id = task  # Store for external access
            yield progress

    def prompt_vm_selection(self, vms: List[VMInfo]) -> Optional[VMInfo]:
        """
        Interactive VM selection.

        Args:
            vms: List of available VMs.

        Returns:
            Selected VMInfo or None.
        """
        if not vms:
            self.print_error("No VMs available")
            return None

        # Auto-select if only one
        if len(vms) == 1:
            self.print_info(f"Auto-selected VM: {vms[0].hostname} ({vms[0].vpsid})")
            return vms[0]

        # Show table and prompt
        self.render_vm_table(vms)
        vpsid = self.prompt_input("Enter VPSID")

        for vm in vms:
            if vm.vpsid == vpsid:
                return vm

        self.print_error(f"VM with VPSID {vpsid} not found")
        return None

    def prompt_rule_selection(
        self, rules: List[ForwardingRule]
    ) -> Optional[ForwardingRule]:
        """
        Interactive rule selection.

        Args:
            rules: List of available rules.

        Returns:
            Selected ForwardingRule or None.
        """
        if not rules:
            self.print_error("No forwarding rules available")
            return None

        # Auto-select if only one
        if len(rules) == 1:
            self.print_info(f"Auto-selected rule ID: {rules[0].id}")
            return rules[0]

        # Show table and prompt
        self.render_forwarding_table(rules)
        vdfid = self.prompt_input("Enter Rule ID")

        for rule in rules:
            if rule.id == vdfid:
                return rule

        self.print_error(f"Rule with ID {vdfid} not found")
        return None

    def prompt_protocol(self, default: Optional[Protocol] = None) -> Protocol:
        """
        Prompt for protocol selection.

        Args:
            default: Default protocol.

        Returns:
            Selected Protocol.
        """
        choices = ["HTTP", "HTTPS", "TCP"]
        default_str = default.value if default else "TCP"
        result = self.prompt_select("Protocol", choices, default=default_str)
        return Protocol.from_string(result)

    def render_connection_test_table(
        self,
        results: List[tuple],
        default_host: Optional[str] = None,
    ) -> None:
        """
        Render connection test results as Rich table.

        Args:
            results: List of (host_name, success, error, elapsed_ms) tuples.
            default_host: Name of default host.
        """
        table = Table(
            title="Connection Test Results",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
        )
        table.add_column("Status", justify="center", width=8)
        table.add_column("Host", style="white")
        table.add_column("API Response", justify="right")
        table.add_column("Details", style="dim")

        for host_name, success, error, elapsed in results:
            # Status icon
            if success:
                status = "[green]✓ OK[/green]"
            else:
                status = "[red]✗ FAIL[/red]"

            # Host name with default indicator
            host_display = f"[cyan]{host_name}[/cyan]"
            if host_name == default_host:
                host_display += " [yellow]★[/yellow]"

            # Response time with color coding (adjusted for API calls)
            elapsed_sec = elapsed / 1000
            if elapsed_sec < 1:
                time_color = "green"
            elif elapsed_sec < 2:
                time_color = "yellow"
            else:
                time_color = "red"
            time_display = f"[{time_color}]{elapsed_sec:.2f}s[/{time_color}]"

            # Details
            if success:
                details = "[green]Connected[/green]"
            else:
                details = f"[red]{error}[/red]"

            table.add_row(status, host_display, time_display, details)

        self._console.print(table)
