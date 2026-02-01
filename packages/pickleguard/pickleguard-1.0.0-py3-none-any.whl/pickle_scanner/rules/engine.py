"""
Rule matching engine for custom detection rules.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import re
import yaml

from pickle_scanner.core.opcodes import ParsedOpcode
from pickle_scanner.core.stack_machine import StackMachine, GlobalRef
from pickle_scanner.reporting.report import Finding, Severity


@dataclass
class RuleCondition:
    """A condition in a detection rule."""
    opcode: Optional[List[str]] = None  # Opcodes to match
    module: Optional[str] = None         # Module pattern (regex)
    name: Optional[str] = None           # Name pattern (regex)
    name_contains: Optional[List[str]] = None  # Name contains any of these
    follows_global: bool = False         # Must follow a GLOBAL opcode

    def matches_opcode(self, opcode: ParsedOpcode) -> bool:
        """Check if condition matches an opcode."""
        if self.opcode and opcode.name not in self.opcode:
            return False
        return True

    def matches_global(self, ref: GlobalRef) -> bool:
        """Check if condition matches a global reference."""
        if self.module:
            if not re.match(self.module, ref.module):
                return False
        if self.name:
            if not re.match(self.name, ref.name):
                return False
        if self.name_contains:
            full_name = f"{ref.module}.{ref.name}"
            if not any(substr in full_name for substr in self.name_contains):
                return False
        return True


@dataclass
class Rule:
    """A detection rule."""
    name: str
    severity: str  # critical, high, medium, low, info
    description: str
    conditions: List[RuleCondition]
    tags: List[str] = field(default_factory=list)
    enabled: bool = True

    def get_severity(self) -> Severity:
        """Convert string severity to Severity enum."""
        mapping = {
            'critical': Severity.CRITICAL,
            'high': Severity.HIGH,
            'medium': Severity.MEDIUM,
            'low': Severity.LOW,
            'info': Severity.INFO,
        }
        return mapping.get(self.severity.lower(), Severity.MEDIUM)


class RuleEngine:
    """Engine for matching rules against pickle analysis."""

    def __init__(self):
        self.rules: List[Rule] = []

    def load_rules_from_yaml(self, yaml_content: str) -> None:
        """Load rules from YAML content."""
        data = yaml.safe_load(yaml_content)
        if not data or 'rules' not in data:
            return

        for rule_data in data['rules']:
            conditions = []
            for cond_data in rule_data.get('conditions', []):
                condition = RuleCondition(
                    opcode=cond_data.get('opcode'),
                    module=cond_data.get('module'),
                    name=cond_data.get('name'),
                    name_contains=cond_data.get('name_contains'),
                    follows_global=cond_data.get('follows_global', False),
                )
                conditions.append(condition)

            rule = Rule(
                name=rule_data['name'],
                severity=rule_data.get('severity', 'medium'),
                description=rule_data.get('description', ''),
                conditions=conditions,
                tags=rule_data.get('tags', []),
                enabled=rule_data.get('enabled', True),
            )
            self.rules.append(rule)

    def load_rules_from_file(self, path: str) -> None:
        """Load rules from a YAML file."""
        with open(path, 'r') as f:
            self.load_rules_from_yaml(f.read())

    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the engine."""
        self.rules.append(rule)

    def match(
        self,
        opcodes: List[ParsedOpcode],
        machine: Optional[StackMachine] = None
    ) -> List[Finding]:
        """Match rules against parsed opcodes and return findings."""
        findings = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            matches = self._match_rule(rule, opcodes, machine)
            for match_info in matches:
                findings.append(Finding(
                    rule=rule.name,
                    severity=rule.get_severity(),
                    position=match_info.get('position', 0),
                    message=rule.description,
                    callable=match_info.get('callable'),
                    evidence=match_info.get('evidence', ''),
                    opcode=match_info.get('opcode'),
                ))

        return findings

    def _match_rule(
        self,
        rule: Rule,
        opcodes: List[ParsedOpcode],
        machine: Optional[StackMachine]
    ) -> List[Dict[str, Any]]:
        """Match a single rule."""
        matches = []

        # Check against globals from machine
        if machine and machine.globals_found:
            for ref, position in machine.globals_found:
                for condition in rule.conditions:
                    if condition.matches_global(ref):
                        matches.append({
                            'position': position,
                            'callable': ref.full_path,
                            'opcode': ref.opcode,
                            'evidence': f"{ref.opcode} {ref.module} {ref.name}",
                        })

        # Check against raw opcodes
        prev_was_global = False
        prev_global = None

        for i, opcode in enumerate(opcodes):
            for condition in rule.conditions:
                if not condition.matches_opcode(opcode):
                    continue

                # Check follows_global condition
                if condition.follows_global and not prev_was_global:
                    continue

                # For GLOBAL/INST opcodes, extract module/name
                if opcode.name in ('GLOBAL', 'INST'):
                    if isinstance(opcode.arg, tuple) and len(opcode.arg) == 2:
                        ref = GlobalRef(opcode.arg[0], opcode.arg[1], opcode.name)
                        if condition.matches_global(ref):
                            matches.append({
                                'position': opcode.position,
                                'callable': ref.full_path,
                                'opcode': opcode.name,
                                'evidence': f"{opcode.name} at offset {opcode.position}",
                            })

                # For REDUCE after GLOBAL
                elif opcode.name == 'REDUCE' and condition.follows_global and prev_global:
                    matches.append({
                        'position': opcode.position,
                        'callable': prev_global.full_path if prev_global else None,
                        'opcode': opcode.name,
                        'evidence': f"REDUCE following {prev_global.full_path if prev_global else 'unknown'}",
                    })

            # Track previous opcode state
            if opcode.name in ('GLOBAL', 'STACK_GLOBAL', 'INST'):
                prev_was_global = True
                if isinstance(opcode.arg, tuple) and len(opcode.arg) == 2:
                    prev_global = GlobalRef(opcode.arg[0], opcode.arg[1], opcode.name)
            else:
                prev_was_global = opcode.name != 'REDUCE'  # Keep tracking through data ops
                if not prev_was_global:
                    prev_global = None

        return matches
