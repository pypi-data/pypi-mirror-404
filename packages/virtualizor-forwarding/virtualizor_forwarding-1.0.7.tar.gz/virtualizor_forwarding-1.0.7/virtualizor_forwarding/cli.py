"""
CLI (Command Line Interface) for Virtualizor Forwarding Tool.

Main entry point for all commands.
"""

from __future__ import annotations

import argparse
import json as json_module
import sys
import time
from typing import Optional, List

from . import __version__, __author__, __github__, __telegram__, __forum__, __email__
from .config import ConfigManager
from .api import VirtualizorClient, APIError, AuthenticationError
from .models import HostProfile, Protocol, ForwardingRule, VMStatus, BatchResult
from .services.vm_manager import VMManager
from .services.forwarding_manager import ForwardingManager
from .services.batch_processor import BatchProcessor
from .tui import TUIRenderer
from .utils import parse_comma_ids
from .updater import check_update_cached, get_latest_version, is_update_available

# Help text constants - user-friendly descriptions
_HELP_HOST_PROFILE = "Name of the host profile (e.g., NAT-US1, NAT-ID3)"
_HELP_VM_ID = "Virtual Machine ID (VPSID) from 'vf vm list'"
_HELP_SRC_PORT = "Source port number (external port)"
_HELP_DEST_PORT = "Destination port number (internal port on VM)"
_HELP_INTERACTIVE = "Use interactive mode with prompts"
_HELP_JSON_OUTPUT = "Output result in JSON format"
_HELP_PROTOCOL = "Forwarding protocol: HTTP, HTTPS, or TCP"
_HELP_DOMAIN = "Domain name or hostname for HTTP/HTTPS forwarding"
_HELP_DEST_IP = "Destination IP address (VM internal IP)"

# Warning messages
_MSG_NO_HOSTS = "No hosts configured. Use 'vf config add' to add one first."


class CLI:
    """Main CLI application."""

    def __init__(self) -> None:
        """Initialize CLI."""
        self._config_manager = ConfigManager()
        self._tui: Optional[TUIRenderer] = None
        self._verbose = False
        self._debug = False

    def _get_tui(self, no_color: bool = False) -> TUIRenderer:
        """Get or create TUI renderer."""
        if self._tui is None:
            self._tui = TUIRenderer(no_color=no_color)
        return self._tui

    def _get_client(self, host_name: Optional[str] = None) -> VirtualizorClient:
        """
        Get API client for specified or default host.

        Args:
            host_name: Host name or None for default.

        Returns:
            VirtualizorClient instance.

        Raises:
            SystemExit: If no host configured.
        """
        config = self._config_manager.load()

        if host_name:
            profile = config.hosts.get(host_name)
            if not profile:
                self._get_tui().print_error(f"Host '{host_name}' not found")
                sys.exit(1)
        else:
            profile = self._config_manager.get_default()
            if not profile:
                self._get_tui().print_error(
                    "No default host configured. Use 'config add' first."
                )
                sys.exit(1)

        return VirtualizorClient(profile)

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run CLI with arguments.

        Args:
            args: Command line arguments (uses sys.argv if None).

        Returns:
            Exit code.
        """
        parser = self._create_parser()
        parsed = parser.parse_args(args)

        self._verbose = getattr(parsed, "verbose", False)
        self._debug = getattr(parsed, "debug", False)
        no_color = getattr(parsed, "no_color", False)
        self._tui = TUIRenderer(no_color=no_color)

        # Handle --version flag
        if getattr(parsed, "version", False):
            self._print_version()
            return 0

        if not hasattr(parsed, "func"):
            parser.print_help()
            return 0

        # Background update check (once per day, non-blocking)
        self._check_update_background()

        try:
            return parsed.func(parsed)
        except KeyboardInterrupt:
            self._tui.print_warning("Operation cancelled")
            return 130
        except APIError as e:
            self._tui.print_error(str(e))
            return 1
        except Exception as e:
            if self._debug:
                raise
            self._tui.print_error(f"Error: {e}")
            return 1

    def _print_version(self) -> None:
        """Print version information."""
        print(f"Virtualizor Forwarding Tool v{__version__}")
        print(f"Author: {__author__}")
        print(f"GitHub: {__github__}")

    def _check_update_background(self) -> None:
        """Check for updates in background (cached, once per day)."""
        try:
            latest, is_new = check_update_cached()
            if latest and is_update_available(latest):
                self._tui.print_info(
                    f"New version available: {latest} (current: {__version__})"
                )
                self._tui.console.print(
                    "  Run: [cyan]pip install --upgrade virtualizor-forwarding[/cyan]\n"
                )
        except Exception:  # noqa: BLE001
            pass  # Silently ignore update check errors

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser with all subcommands."""
        parser = argparse.ArgumentParser(
            prog="vf",
            description="Virtualizor Domain/Port Forwarding Manager",
        )
        parser.add_argument(
            "--version", "-V", action="store_true", help="Show version and exit"
        )
        parser.add_argument(
            "--host", "-H", help="Use specific host profile", metavar="NAME"
        )
        parser.add_argument(
            "--no-color", action="store_true", help="Disable colored output"
        )
        parser.add_argument(
            "--verbose", "-v", action="store_true", help="Verbose output"
        )
        parser.add_argument("--debug", action="store_true", help="Debug mode")

        subparsers = parser.add_subparsers(title="commands", dest="command")

        # About command
        about_parser = subparsers.add_parser("about", help="Show about information")
        about_parser.set_defaults(func=self._cmd_about)

        # Update command
        update_parser = subparsers.add_parser("update", help="Check for updates")
        update_parser.set_defaults(func=self._cmd_update)

        # Config commands
        self._add_config_commands(subparsers)

        # VM commands
        self._add_vm_commands(subparsers)

        # Forward commands
        self._add_forward_commands(subparsers)

        # Batch commands
        self._add_batch_commands(subparsers)

        return parser

    def _add_config_commands(self, subparsers: argparse._SubParsersAction) -> None:
        """Add config subcommands."""
        config_parser = subparsers.add_parser(
            "config", help="Manage host configurations"
        )
        config_sub = config_parser.add_subparsers(
            title="config commands", dest="config_cmd"
        )

        # config add
        add_parser = config_sub.add_parser("add", help="Add new host profile")
        add_parser.add_argument("name", help=_HELP_HOST_PROFILE)
        add_parser.add_argument("--url", required=True, help="API URL")
        add_parser.add_argument("--key", required=True, help="API Key")
        add_parser.add_argument(
            "--pass", dest="password", required=True, help="API Password"
        )
        add_parser.add_argument("--default", action="store_true", help="Set as default")
        add_parser.set_defaults(func=self._cmd_config_add)

        # config remove
        rm_parser = config_sub.add_parser("remove", help="Remove host profile")
        rm_parser.add_argument("name", help=_HELP_HOST_PROFILE)
        rm_parser.set_defaults(func=self._cmd_config_remove)

        # config list
        list_parser = config_sub.add_parser("list", help="List host profiles")
        list_parser.set_defaults(func=self._cmd_config_list)

        # config set-default
        default_parser = config_sub.add_parser("set-default", help="Set default host")
        default_parser.add_argument("name", help=_HELP_HOST_PROFILE)
        default_parser.set_defaults(func=self._cmd_config_set_default)

        # config test
        test_parser = config_sub.add_parser("test", help="Test host connection(s)")
        test_parser.add_argument(
            "name", nargs="?", help=f"{_HELP_HOST_PROFILE} (tests ALL hosts if omitted)"
        )
        test_parser.set_defaults(func=self._cmd_config_test)

    def _add_vm_commands(self, subparsers: argparse._SubParsersAction) -> None:
        """Add VM subcommands."""
        vm_parser = subparsers.add_parser("vm", help="Manage virtual machines")
        vm_sub = vm_parser.add_subparsers(title="vm commands", dest="vm_cmd")

        # vm list
        list_parser = vm_sub.add_parser("list", help="List virtual machines")
        list_parser.add_argument(
            "--status", "-s", choices=["up", "down"], help="Filter by status"
        )
        list_parser.add_argument(
            "--all-hosts", action="store_true", help="List from all configured hosts"
        )
        list_parser.add_argument(
            "--json", "-j", action="store_true", help=_HELP_JSON_OUTPUT
        )
        list_parser.set_defaults(func=self._cmd_vm_list)

    def _add_forward_commands(self, subparsers: argparse._SubParsersAction) -> None:
        """Add forward subcommands."""
        fwd_parser = subparsers.add_parser("forward", help="Manage port forwarding")
        fwd_sub = fwd_parser.add_subparsers(
            title="forward commands", dest="forward_cmd"
        )

        # forward list
        list_parser = fwd_sub.add_parser("list", help="List forwarding rules")
        list_parser.add_argument("--vpsid", "-v", help=_HELP_VM_ID)
        list_parser.add_argument(
            "--auto", action="store_true", help="Auto-select if single VM"
        )
        list_parser.add_argument(
            "--json", "-j", action="store_true", help=_HELP_JSON_OUTPUT
        )
        list_parser.set_defaults(func=self._cmd_forward_list)

        # forward add
        add_parser = fwd_sub.add_parser("add", help="Add forwarding rule")
        add_parser.add_argument("--vpsid", "-v", help=_HELP_VM_ID)
        add_parser.add_argument(
            "--protocol", "-p", choices=["HTTP", "HTTPS", "TCP"], help=_HELP_PROTOCOL
        )
        add_parser.add_argument("--domain", "-d", help=_HELP_DOMAIN)
        add_parser.add_argument("--src-port", "-s", type=int, help=_HELP_SRC_PORT)
        add_parser.add_argument("--dest-port", "-t", type=int, help=_HELP_DEST_PORT)
        add_parser.add_argument(
            "--dest-ip", help=f"{_HELP_DEST_IP} (default: VM internal IP)"
        )
        add_parser.add_argument(
            "--interactive", "-i", action="store_true", help=_HELP_INTERACTIVE
        )
        add_parser.set_defaults(func=self._cmd_forward_add)

        # forward edit
        edit_parser = fwd_sub.add_parser("edit", help="Edit forwarding rule")
        edit_parser.add_argument("--vpsid", "-v", help=_HELP_VM_ID)
        edit_parser.add_argument("--vdfid", "-f", help="Forwarding rule ID")
        edit_parser.add_argument(
            "--protocol", "-p", choices=["HTTP", "HTTPS", "TCP"], help=_HELP_PROTOCOL
        )
        edit_parser.add_argument("--domain", "-d", help=_HELP_DOMAIN)
        edit_parser.add_argument("--src-port", "-s", type=int, help=_HELP_SRC_PORT)
        edit_parser.add_argument("--dest-port", "-t", type=int, help=_HELP_DEST_PORT)
        edit_parser.add_argument("--dest-ip", help=_HELP_DEST_IP)
        edit_parser.add_argument(
            "--interactive", "-i", action="store_true", help=_HELP_INTERACTIVE
        )
        edit_parser.set_defaults(func=self._cmd_forward_edit)

        # forward delete
        del_parser = fwd_sub.add_parser("delete", help="Delete forwarding rules")
        del_parser.add_argument("--vpsid", "-v", help=_HELP_VM_ID)
        del_parser.add_argument(
            "--vdfid", "-f", help="Forwarding rule ID(s), comma-separated"
        )
        del_parser.add_argument(
            "--force", action="store_true", help="Skip confirmation"
        )
        del_parser.add_argument(
            "--interactive", "-i", action="store_true", help=_HELP_INTERACTIVE
        )
        del_parser.set_defaults(func=self._cmd_forward_delete)

    def _add_batch_commands(self, subparsers: argparse._SubParsersAction) -> None:
        """Add batch subcommands."""
        batch_parser = subparsers.add_parser("batch", help="Batch operations")
        batch_sub = batch_parser.add_subparsers(
            title="batch commands", dest="batch_cmd"
        )

        # batch import
        import_parser = batch_sub.add_parser("import", help="Import rules from JSON")
        import_parser.add_argument("--vpsid", "-v", required=True, help=_HELP_VM_ID)
        import_parser.add_argument(
            "--from-file", "-f", required=True, help="JSON file path"
        )
        import_parser.add_argument(
            "--dry-run", action="store_true", help="Validate only"
        )
        import_parser.set_defaults(func=self._cmd_batch_import)

        # batch export
        export_parser = batch_sub.add_parser("export", help="Export rules to JSON")
        export_parser.add_argument("--vpsid", "-v", required=True, help=_HELP_VM_ID)
        export_parser.add_argument(
            "--to-file", "-o", required=True, help="Output file path"
        )
        export_parser.set_defaults(func=self._cmd_batch_export)

    # About and Update command handlers
    def _cmd_about(self, _args: argparse.Namespace) -> int:
        """Handle about command - show detailed info."""
        from rich.panel import Panel
        from rich.table import Table

        # Create info table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        table.add_row("Version", f"v{__version__}")
        table.add_row("Author", __author__)
        table.add_row("Email", __email__)
        table.add_row("GitHub", __github__)
        table.add_row("Telegram", __telegram__)
        table.add_row("Forum", __forum__)

        panel = Panel(
            table,
            title="[bold cyan]Virtualizor Forwarding Tool[/bold cyan]",
            subtitle="[dim]Domain/Port Forwarding Manager[/dim]",
            border_style="cyan",
        )
        self._tui.console.print(panel)

        # Check for updates
        latest, _ = check_update_cached()
        if latest and is_update_available(latest):
            self._tui.print_info(f"New version available: {latest}")
            self._tui.console.print(
                "  Run: [cyan]pip install --upgrade virtualizor-forwarding[/cyan]"
            )
        else:
            self._tui.print_success("You are using the latest version")

        return 0

    def _cmd_update(self, _args: argparse.Namespace) -> int:
        """Handle update command - check for updates."""
        self._tui.print_info("Checking for updates...")

        latest = get_latest_version()
        if not latest:
            self._tui.print_error("Failed to check for updates. Check your internet connection.")
            return 1

        if is_update_available(latest):
            self._tui.print_warning(f"New version available: {latest} (current: {__version__})")
            self._tui.console.print(
                "\n  To update, run:\n"
                "  [cyan]pip install --upgrade virtualizor-forwarding[/cyan]\n"
            )
        else:
            self._tui.print_success(f"You are using the latest version ({__version__})")

        return 0

    # Config command handlers
    def _cmd_config_add(self, args: argparse.Namespace) -> int:
        """Handle config add command."""
        profile = HostProfile.create(
            name=args.name,
            api_url=args.url,
            api_key=args.key,
            api_pass=args.password,
        )
        self._config_manager.add_host(args.name, profile)

        if args.default:
            self._config_manager.set_default(args.name)

        self._tui.print_success(f"Host '{args.name}' added successfully")
        return 0

    def _cmd_config_remove(self, args: argparse.Namespace) -> int:
        """Handle config remove command."""
        self._config_manager.remove_host(args.name)
        self._tui.print_success(f"Host '{args.name}' removed")
        return 0

    def _cmd_config_list(self, _args: argparse.Namespace) -> int:
        """Handle config list command."""
        config = self._config_manager.load()
        if not config.hosts:
            self._tui.print_warning(_MSG_NO_HOSTS)
            return 1

        self._tui.render_host_tree(config.hosts, config.default_host)
        return 0

    def _cmd_config_set_default(self, args: argparse.Namespace) -> int:
        """Handle config set-default command."""
        self._config_manager.set_default(args.name)
        self._tui.print_success(f"Default host set to '{args.name}'")
        return 0

    def _cmd_config_test(self, args: argparse.Namespace) -> int:
        """Handle config test command."""
        host_name = args.name or getattr(args, "host", None)

        # If no host specified, test all hosts
        if not host_name:
            return self._cmd_config_test_all()

        # Test specific host
        client = self._get_client(host_name)

        with self._tui.show_spinner(f"Testing connection to '{host_name}'..."):
            try:
                client.test_connection()
                self._tui.print_success(f"Connection to '{host_name}' successful!")
                return 0
            except AuthenticationError:
                self._tui.print_error(
                    f"Authentication failed for '{host_name}'. Check API credentials."
                )
                return 1
            except Exception as e:
                self._tui.print_error(f"Connection to '{host_name}' failed: {e}")
                return 1

    def _cmd_config_test_all(self) -> int:
        """Test connection to all configured hosts."""
        config = self._config_manager.load()

        if not config.hosts:
            self._tui.print_warning(_MSG_NO_HOSTS)
            return 1

        self._tui.print_info(f"Testing {len(config.hosts)} host(s)...\n")

        results = []
        for host_name, profile in config.hosts.items():
            start_time = time.time()
            try:
                client = VirtualizorClient(profile)
                client.test_connection()
                elapsed = (time.time() - start_time) * 1000  # ms
                results.append((host_name, True, None, elapsed))
            except AuthenticationError:
                elapsed = (time.time() - start_time) * 1000
                results.append((host_name, False, "Auth failed", elapsed))
            except Exception as e:
                elapsed = (time.time() - start_time) * 1000
                error_msg = str(e)[:30] + "..." if len(str(e)) > 30 else str(e)
                results.append((host_name, False, error_msg, elapsed))

        # Render results table
        self._tui.render_connection_test_table(results, config.default_host)

        # Summary
        success_count = sum(1 for _, success, _, _ in results if success)
        fail_count = len(results) - success_count

        print()
        if fail_count == 0:
            self._tui.print_success(
                f"All {success_count} host(s) connected successfully!"
            )
            return 0
        if success_count == 0:
            self._tui.print_error(f"All {fail_count} host(s) failed to connect")
            return 1
        self._tui.print_warning(
            f"Results: {success_count} succeeded, {fail_count} failed"
        )
        return 1

    # VM command handlers
    def _cmd_vm_list(self, args: argparse.Namespace) -> int:
        """Handle vm list command."""
        if args.all_hosts:
            return self._cmd_vm_list_all_hosts(args)

        client = self._get_client(getattr(args, "host", None))
        vm_manager = VMManager(client)

        with self._tui.show_spinner("Fetching VMs..."):
            status_filter = VMStatus(args.status) if args.status else None
            vms = vm_manager.list_all(status_filter)

        if args.json:
            data = [vm.to_dict() for vm in vms]
            print(json_module.dumps(data, indent=2))
        else:
            if not vms:
                self._tui.print_warning("No VMs found")
            else:
                self._tui.render_vm_table(vms)

        return 0

    def _cmd_vm_list_all_hosts(self, args: argparse.Namespace) -> int:
        """List VMs from all configured hosts."""
        config = self._config_manager.load()

        if not config.hosts:
            self._tui.print_warning(_MSG_NO_HOSTS)
            return 1

        # Get status filter if provided
        status_filter = VMStatus(args.status) if args.status else None

        all_vms_data = []  # For JSON output
        total_vms = 0

        for host_name, profile in config.hosts.items():
            vms = self._fetch_vms_from_host(host_name, profile, status_filter)
            if vms is None:
                continue

            if args.json:
                self._collect_vms_for_json(vms, host_name, all_vms_data)
            else:
                self._display_host_vms(vms, host_name)

            total_vms += len(vms)

        return self._output_all_hosts_result(args.json, all_vms_data, total_vms, config)

    def _fetch_vms_from_host(
        self,
        host_name: str,
        profile: HostProfile,
        status_filter: Optional[VMStatus] = None,
    ) -> Optional[List]:
        """Fetch VMs from a single host, return None on error."""
        with self._tui.show_spinner(f"Fetching VMs from '{host_name}'..."):
            try:
                client = VirtualizorClient(profile)
                vm_manager = VMManager(client)
                return vm_manager.list_all(status_filter)
            except AuthenticationError:
                self._tui.print_error(
                    f"Authentication failed for '{host_name}'. Skipping..."
                )
                return None
            except APIError as e:
                self._tui.print_error(f"Failed to fetch from '{host_name}': {e}")
                return None

    def _collect_vms_for_json(
        self, vms: List, host_name: str, all_vms_data: List
    ) -> None:
        """Collect VMs data for JSON output."""
        for vm in vms:
            vm_dict = vm.to_dict()
            vm_dict["host"] = host_name
            all_vms_data.append(vm_dict)

    def _display_host_vms(self, vms: List, host_name: str) -> None:
        """Display VMs table for a single host."""
        if vms:
            self._tui.render_vm_table(vms, title=f"VMs on {host_name} ({len(vms)})")
            print()  # Empty line between hosts
        else:
            self._tui.print_warning(f"No VMs found on '{host_name}'")

    def _output_all_hosts_result(
        self, is_json: bool, all_vms_data: List, total_vms: int, config
    ) -> int:
        """Output final result for all hosts listing."""
        if is_json:
            print(json_module.dumps(all_vms_data, indent=2))
        else:
            self._tui.print_success(
                f"Total: {total_vms} VM(s) across {len(config.hosts)} host(s)"
            )
        return 0

    # Forward command handlers
    def _cmd_forward_list(self, args: argparse.Namespace) -> int:
        """Handle forward list command."""
        client = self._get_client(getattr(args, "host", None))
        vm_manager = VMManager(client)
        fwd_manager = ForwardingManager(client)

        vpsid = args.vpsid
        if not vpsid:
            vms = vm_manager.list_all()
            if args.auto and len(vms) == 1:
                vpsid = vms[0].vpsid
                self._tui.print_info(f"Auto-selected VM: {vms[0].hostname}")
            else:
                vm = self._tui.prompt_vm_selection(vms)
                if not vm:
                    return 1
                vpsid = vm.vpsid

        with self._tui.show_spinner("Fetching forwarding rules..."):
            rules = fwd_manager.list_rules(vpsid)

        if args.json:
            data = [rule.to_dict() for rule in rules]
            print(json_module.dumps(data, indent=2))
        else:
            if not rules:
                self._tui.print_warning("No forwarding rules found")
            else:
                self._tui.render_forwarding_table(rules)

        return 0

    def _cmd_forward_add(self, args: argparse.Namespace) -> int:
        """Handle forward add command."""
        client = self._get_client(getattr(args, "host", None))
        vm_manager = VMManager(client)
        fwd_manager = ForwardingManager(client)

        # Get VPSID
        vpsid = self._get_vpsid_for_forward(args, vm_manager)
        if not vpsid:
            return 1

        # Get protocol
        protocol = Protocol.from_string(args.protocol) if args.protocol else None
        if not protocol or args.interactive:
            protocol = self._tui.prompt_protocol(protocol)

        # Get rule parameters
        rule = self._build_forward_rule(args, vpsid, protocol, vm_manager, fwd_manager)
        if not rule:
            return 1

        # Show confirmation
        self._tui.render_rule_detail(rule)
        if not self._tui.prompt_confirm("Add this forwarding rule?", default=True):
            self._tui.print_warning("Cancelled")
            return 0

        # Execute
        return self._execute_add_rule(fwd_manager, vpsid, rule)

    def _get_vpsid_for_forward(
        self, args: argparse.Namespace, vm_manager: VMManager
    ) -> Optional[str]:
        """Get VPSID from args or prompt user."""
        vpsid = args.vpsid
        if not vpsid or args.interactive:
            vms = vm_manager.list_all()
            vm = self._tui.prompt_vm_selection(vms)
            if not vm:
                return None
            vpsid = vm.vpsid
        return vpsid

    def _build_forward_rule(
        self,
        args: argparse.Namespace,
        vpsid: str,
        protocol: Protocol,
        vm_manager: VMManager,
        fwd_manager: ForwardingManager,
    ) -> Optional[ForwardingRule]:
        """Build forwarding rule from args and prompts."""
        # Auto-configure ports for HTTP/HTTPS
        auto_src, auto_dest = fwd_manager.auto_configure_ports(protocol)

        # Get source hostname
        src_hostname = self._get_source_hostname(args, vpsid, protocol, fwd_manager)

        # Get ports
        src_port, dest_port = self._get_ports(args, auto_src, auto_dest)

        # Get destination IP
        dest_ip = args.dest_ip
        if not dest_ip:
            dest_ip = vm_manager.get_internal_ip(vpsid)
        if not dest_ip or args.interactive:
            dest_ip = self._tui.prompt_input("Destination IP", default=dest_ip)

        return ForwardingRule(
            protocol=protocol,
            src_hostname=src_hostname,
            src_port=src_port,
            dest_ip=dest_ip,
            dest_port=dest_port,
        )

    def _get_source_hostname(
        self,
        args: argparse.Namespace,
        vpsid: str,
        protocol: Protocol,
        fwd_manager: ForwardingManager,
    ) -> str:
        """Get source hostname from args or prompt."""
        src_hostname = args.domain
        if not src_hostname or args.interactive:
            if protocol == Protocol.TCP:
                src_ip = fwd_manager.get_source_ip_for_tcp(vpsid)
                src_hostname = self._tui.prompt_input("Source IP", default=src_ip)
            else:
                src_hostname = self._tui.prompt_input("Domain name")
        return src_hostname

    def _get_ports(
        self,
        args: argparse.Namespace,
        auto_src: Optional[int],
        auto_dest: Optional[int],
    ) -> tuple:
        """Get source and destination ports from args or prompts."""
        src_port = args.src_port or auto_src
        dest_port = args.dest_port or auto_dest

        if src_port is None or args.interactive:
            src_port = self._tui.prompt_int(_HELP_SRC_PORT, default=src_port)
        if dest_port is None or args.interactive:
            dest_port = self._tui.prompt_int(_HELP_DEST_PORT, default=dest_port)

        return src_port, dest_port

    def _execute_add_rule(
        self, fwd_manager: ForwardingManager, vpsid: str, rule: ForwardingRule
    ) -> int:
        """Execute add rule and return exit code."""
        with self._tui.show_spinner("Adding forwarding rule..."):
            response = fwd_manager.add_rule(vpsid, rule)

        if response.success:
            self._tui.print_success("Forwarding rule added successfully")
            return 0
        self._tui.print_error(f"Failed: {response.get_error_message()}")
        return 1

    def _cmd_forward_edit(self, args: argparse.Namespace) -> int:
        """Handle forward edit command."""
        client = self._get_client(getattr(args, "host", None))
        vm_manager = VMManager(client)
        fwd_manager = ForwardingManager(client)

        # Get VPSID
        vpsid = self._get_vpsid_for_forward(args, vm_manager)
        if not vpsid:
            return 1

        # Get rule to edit
        current_rule, vdfid = self._get_rule_to_edit(args, vpsid, fwd_manager)
        if not current_rule:
            return 1

        # Build updated rule
        updated_rule = self._build_updated_rule(args, current_rule, fwd_manager)

        # Show comparison and confirm
        self._tui.render_comparison(current_rule, updated_rule)
        if not self._tui.prompt_confirm("Apply these changes?", default=True):
            self._tui.print_warning("Cancelled")
            return 0

        # Execute
        return self._execute_edit_rule(fwd_manager, vpsid, vdfid, updated_rule)

    def _get_rule_to_edit(
        self, args: argparse.Namespace, vpsid: str, fwd_manager: ForwardingManager
    ) -> tuple:
        """Get rule to edit from args or prompt."""
        vdfid = args.vdfid
        if not vdfid or args.interactive:
            rules = fwd_manager.list_rules(vpsid)
            rule = self._tui.prompt_rule_selection(rules)
            if not rule:
                return None, None
            return rule, rule.id

        current_rule = fwd_manager.get_rule_by_id(vpsid, vdfid)
        if not current_rule:
            self._tui.print_error(f"Rule {vdfid} not found")
            return None, None
        return current_rule, vdfid

    def _build_updated_rule(
        self,
        args: argparse.Namespace,
        current_rule: ForwardingRule,
        fwd_manager: ForwardingManager,
    ) -> ForwardingRule:
        """Build updated rule from args and current rule."""
        # Get protocol
        protocol = Protocol.from_string(args.protocol) if args.protocol else None
        if args.interactive:
            protocol = self._tui.prompt_protocol(current_rule.protocol)

        # Auto-configure ports if protocol changed
        auto_src, auto_dest = None, None
        if protocol and protocol != current_rule.protocol:
            auto_src, auto_dest = fwd_manager.auto_configure_ports(protocol)

        # Get updated values
        src_hostname = args.domain
        if args.interactive:
            src_hostname = self._tui.prompt_input(
                "Domain/IP", default=current_rule.src_hostname
            )

        src_port = args.src_port or auto_src
        if args.interactive:
            src_port = self._tui.prompt_int(
                _HELP_SRC_PORT, default=src_port or current_rule.src_port
            )

        dest_port = args.dest_port or auto_dest
        if args.interactive:
            dest_port = self._tui.prompt_int(
                _HELP_DEST_PORT, default=dest_port or current_rule.dest_port
            )

        dest_ip = args.dest_ip
        if args.interactive:
            dest_ip = self._tui.prompt_input("Dest IP", default=current_rule.dest_ip)

        return fwd_manager.merge_rule_update(
            current_rule,
            protocol=protocol,
            src_hostname=src_hostname,
            src_port=src_port,
            dest_port=dest_port,
            dest_ip=dest_ip,
        )

    def _execute_edit_rule(
        self,
        fwd_manager: ForwardingManager,
        vpsid: str,
        vdfid: str,
        updated_rule: ForwardingRule,
    ) -> int:
        """Execute edit rule and return exit code."""
        with self._tui.show_spinner("Updating forwarding rule..."):
            response = fwd_manager.edit_rule(vpsid, vdfid, updated_rule)

        if response.success:
            self._tui.print_success("Forwarding rule updated successfully")
            return 0
        self._tui.print_error(f"Failed: {response.get_error_message()}")
        return 1

    def _cmd_forward_delete(self, args: argparse.Namespace) -> int:
        """Handle forward delete command."""
        client = self._get_client(getattr(args, "host", None))
        vm_manager = VMManager(client)
        fwd_manager = ForwardingManager(client)

        # Get VPSID
        vpsid = self._get_vpsid_for_forward(args, vm_manager)
        if not vpsid:
            return 1

        # Get rule IDs to delete
        vdfids = self._get_rule_ids_to_delete(args, vpsid, fwd_manager)
        if not vdfids:
            self._tui.print_error("No rule IDs specified")
            return 1

        # Confirm deletion
        if not args.force:
            self._tui.print_warning(
                f"About to delete {len(vdfids)} rule(s): {', '.join(vdfids)}"
            )
            if not self._tui.prompt_confirm("Are you sure?", default=False):
                self._tui.print_warning("Cancelled")
                return 0

        # Execute
        return self._execute_delete_rules(fwd_manager, vpsid, vdfids)

    def _get_rule_ids_to_delete(
        self, args: argparse.Namespace, vpsid: str, fwd_manager: ForwardingManager
    ) -> List[str]:
        """Get rule IDs to delete from args or prompt."""
        if args.vdfid:
            return parse_comma_ids(args.vdfid)
        if args.interactive:
            rules = fwd_manager.list_rules(vpsid)
            rule = self._tui.prompt_rule_selection(rules)
            if rule:
                return [rule.id]
        return []

    def _execute_delete_rules(
        self, fwd_manager: ForwardingManager, vpsid: str, vdfids: List[str]
    ) -> int:
        """Execute delete rules and return exit code."""
        with self._tui.show_spinner("Deleting forwarding rules..."):
            response = fwd_manager.delete_rules(vpsid, vdfids)

        if response.success:
            self._tui.print_success(f"Deleted {len(vdfids)} forwarding rule(s)")
            return 0
        self._tui.print_error(f"Failed: {response.get_error_message()}")
        return 1

    # Batch command handlers
    def _cmd_batch_import(self, args: argparse.Namespace) -> int:
        """Handle batch import command."""
        client = self._get_client(getattr(args, "host", None))
        fwd_manager = ForwardingManager(client)
        batch_processor = BatchProcessor(fwd_manager)

        # Import rules from file
        try:
            rules = batch_processor.import_rules(args.from_file)
        except FileNotFoundError:
            self._tui.print_error(f"File not found: {args.from_file}")
            return 1
        except ValueError as e:
            self._tui.print_error(f"Invalid JSON: {e}")
            return 1

        self._tui.print_info(f"Loaded {len(rules)} rules from {args.from_file}")

        if args.dry_run:
            self._tui.print_info("Dry run mode - validating only")

        # Execute batch with progress
        with self._tui.show_progress(len(rules), "Processing rules") as progress:
            task_id = progress._task_id  # noqa: SLF001

            def update_progress(current: int, _total: int) -> None:
                progress.update(task_id, completed=current)

            result = batch_processor.execute_batch(
                args.vpsid,
                rules,
                dry_run=args.dry_run,
                progress_callback=update_progress,
            )

        # Show results
        return self._show_batch_results(result)

    def _show_batch_results(self, result: BatchResult) -> int:
        """Show batch operation results and return exit code."""
        if result.is_complete_success:
            self._tui.print_success(f"All {result.total} rules processed successfully")
        elif result.is_partial_success:
            self._tui.print_warning(
                f"Partial success: {result.succeeded}/{result.total} succeeded, "
                f"{result.failed} failed"
            )
        else:
            self._tui.print_error(f"All {result.total} rules failed")

        # Show errors (max 5)
        for error in result.errors[:5]:
            self._tui.print_error(f"  - {error.get('error', 'Unknown error')}")

        if len(result.errors) > 5:
            self._tui.print_warning(f"  ... and {len(result.errors) - 5} more errors")

        return 0 if result.is_complete_success else 1

    def _cmd_batch_export(self, args: argparse.Namespace) -> int:
        """Handle batch export command."""
        client = self._get_client(getattr(args, "host", None))
        fwd_manager = ForwardingManager(client)
        batch_processor = BatchProcessor(fwd_manager)

        with self._tui.show_spinner("Exporting rules..."):
            count = batch_processor.export_rules(args.vpsid, args.to_file)

        self._tui.print_success(f"Exported {count} rules to {args.to_file}")
        return 0


def main() -> int:
    """Main entry point."""
    cli = CLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
