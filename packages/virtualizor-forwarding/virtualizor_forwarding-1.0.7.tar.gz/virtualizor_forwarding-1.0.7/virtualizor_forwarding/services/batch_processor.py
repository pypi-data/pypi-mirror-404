"""
Batch Processor service.

Handles batch import/export and execution of forwarding rules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Callable

from ..models import ForwardingRule, BatchResult, ValidationResult, HAProxyConfig
from .forwarding_manager import ForwardingManager


class BatchProcessor:
    """Handles batch operations for forwarding rules."""

    def __init__(self, forwarding_manager: ForwardingManager) -> None:
        """
        Initialize batch processor.

        Args:
            forwarding_manager: ForwardingManager instance.
        """
        self._manager = forwarding_manager

    def import_rules(self, filepath: str) -> List[ForwardingRule]:
        """
        Import forwarding rules from JSON file.

        Args:
            filepath: Path to JSON file.

        Returns:
            List of ForwardingRule objects.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If JSON is invalid.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return [ForwardingRule.from_dict(item) for item in data]
        elif isinstance(data, dict) and "rules" in data:
            return [ForwardingRule.from_dict(item) for item in data["rules"]]
        else:
            raise ValueError("Invalid JSON format. Expected list or {rules: [...]}")

    def export_rules(self, vpsid: str, filepath: str) -> int:
        """
        Export forwarding rules to JSON file.

        Args:
            vpsid: VM ID.
            filepath: Output file path.

        Returns:
            Number of rules exported.
        """
        rules = self._manager.list_rules(vpsid)
        data = {"vpsid": vpsid, "rules": [rule.to_dict() for rule in rules]}

        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return len(rules)

    def validate_batch(
        self, rules: List[ForwardingRule], haproxy_config: HAProxyConfig
    ) -> List[ValidationResult]:
        """
        Validate batch of rules before execution.

        Args:
            rules: List of ForwardingRule to validate.
            haproxy_config: HAProxy configuration for port validation.

        Returns:
            List of ValidationResult, one per rule.
        """
        results = []
        for rule in rules:
            result = self._manager.validate_port(
                rule.src_port, haproxy_config, rule.protocol
            )
            results.append(result)
        return results

    def execute_batch(
        self,
        vpsid: str,
        rules: List[ForwardingRule],
        dry_run: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> BatchResult:
        """
        Execute batch add operation.

        Args:
            vpsid: VM ID.
            rules: List of ForwardingRule to add.
            dry_run: If True, validate only without executing.
            progress_callback: Optional callback(current, total) for progress.

        Returns:
            BatchResult with operation summary.
        """
        result = BatchResult(total=len(rules), succeeded=0, failed=0)

        if not rules:
            return result

        for i, rule in enumerate(rules):
            if progress_callback:
                progress_callback(i + 1, len(rules))

            if dry_run:
                self._process_dry_run(vpsid, rule, result)
            else:
                self._process_add_rule(vpsid, rule, result)

        return result

    def _process_dry_run(
        self, vpsid: str, rule: ForwardingRule, result: BatchResult
    ) -> None:
        """Process a single rule in dry-run mode (validation only)."""
        haproxy_config = self._manager.get_haproxy_config(vpsid)
        validation = self._manager.validate_port(
            rule.src_port, haproxy_config, rule.protocol
        )
        if validation.valid:
            result.add_success()
        else:
            result.add_failure(
                {
                    "rule": rule.to_dict(),
                    "error": validation.message,
                    "suggestions": validation.suggestions,
                }
            )

    def _process_add_rule(
        self, vpsid: str, rule: ForwardingRule, result: BatchResult
    ) -> None:
        """Process a single rule by adding it."""
        try:
            response = self._manager.add_rule(vpsid, rule)
            if response.success:
                result.add_success()
            else:
                result.add_failure(
                    {
                        "rule": rule.to_dict(),
                        "error": response.get_error_message(),
                    }
                )
        except Exception as e:  # noqa: BLE001
            result.add_failure({"rule": rule.to_dict(), "error": str(e)})
