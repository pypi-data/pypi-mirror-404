"""
JSON output formatter for scan reports.
"""

import json
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, TextIO
from pathlib import Path

from pickle_scanner.reporting.report import ScanReport, RiskLevel


@dataclass
class BatchScanResult:
    """Results from scanning multiple files."""
    total_files: int
    malicious_count: int
    benign_count: int
    error_count: int
    reports: List[ScanReport]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "summary": {
                "total_files": self.total_files,
                "malicious_count": self.malicious_count,
                "benign_count": self.benign_count,
                "error_count": self.error_count,
                "detection_rate": self.malicious_count / max(1, self.total_files),
            },
            "files": [r.to_dict() for r in self.reports]
        }


class JSONReporter:
    """JSON format reporter."""

    def __init__(self, pretty: bool = True, indent: int = 2):
        self.pretty = pretty
        self.indent = indent if pretty else None

    def format_report(self, report: ScanReport) -> str:
        """Format a single report as JSON."""
        return json.dumps(
            report.to_dict(),
            indent=self.indent,
            default=str,
            ensure_ascii=False,
        )

    def format_batch(self, reports: List[ScanReport]) -> str:
        """Format multiple reports as JSON."""
        malicious = sum(1 for r in reports if r.is_malicious)
        errors = sum(1 for r in reports if r.errors)

        result = BatchScanResult(
            total_files=len(reports),
            malicious_count=malicious,
            benign_count=len(reports) - malicious - errors,
            error_count=errors,
            reports=reports,
        )

        return json.dumps(
            result.to_dict(),
            indent=self.indent,
            default=str,
            ensure_ascii=False,
        )

    def write_report(self, report: ScanReport, output: TextIO) -> None:
        """Write a single report to a file object."""
        output.write(self.format_report(report))
        output.write("\n")

    def write_batch(self, reports: List[ScanReport], output: TextIO) -> None:
        """Write multiple reports to a file object."""
        output.write(self.format_batch(reports))
        output.write("\n")

    def save_report(self, report: ScanReport, path: Path) -> None:
        """Save a report to a file."""
        with open(path, 'w', encoding='utf-8') as f:
            self.write_report(report, f)

    def save_batch(self, reports: List[ScanReport], path: Path) -> None:
        """Save multiple reports to a file."""
        with open(path, 'w', encoding='utf-8') as f:
            self.write_batch(reports, f)


class SARIFReporter:
    """SARIF format reporter for IDE/CI integration."""

    SARIF_VERSION = "2.1.0"
    SCHEMA_URI = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"

    def __init__(self, tool_name: str = "pickle-scanner", tool_version: str = "1.0.0"):
        self.tool_name = tool_name
        self.tool_version = tool_version

    def format_report(self, report: ScanReport) -> str:
        """Format a single report as SARIF."""
        sarif = self._create_sarif_structure([report])
        return json.dumps(sarif, indent=2, default=str)

    def format_batch(self, reports: List[ScanReport]) -> str:
        """Format multiple reports as SARIF."""
        sarif = self._create_sarif_structure(reports)
        return json.dumps(sarif, indent=2, default=str)

    def _create_sarif_structure(self, reports: List[ScanReport]) -> Dict[str, Any]:
        """Create the SARIF structure."""
        # Collect all unique rules
        rules = self._collect_rules(reports)

        # Create results
        results = []
        for report in reports:
            for finding in report.findings:
                results.append(self._finding_to_result(report, finding))

        return {
            "$schema": self.SCHEMA_URI,
            "version": self.SARIF_VERSION,
            "runs": [{
                "tool": {
                    "driver": {
                        "name": self.tool_name,
                        "version": self.tool_version,
                        "informationUri": "https://github.com/anthropics/pickle-scanner",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }]
        }

    def _collect_rules(self, reports: List[ScanReport]) -> Dict[str, Dict[str, Any]]:
        """Collect unique rules from all reports."""
        rules = {}
        for report in reports:
            for finding in report.findings:
                if finding.rule not in rules:
                    rules[finding.rule] = {
                        "id": finding.rule,
                        "name": finding.rule.replace("_", " ").title(),
                        "shortDescription": {
                            "text": finding.message,
                        },
                        "defaultConfiguration": {
                            "level": self._severity_to_level(finding.severity.value),
                        },
                        "properties": {
                            "security-severity": str(finding.severity.value * 2.5),
                        }
                    }
        return rules

    def _finding_to_result(self, report: ScanReport, finding: 'Finding') -> Dict[str, Any]:
        """Convert a finding to a SARIF result."""
        return {
            "ruleId": finding.rule,
            "level": self._severity_to_level(finding.severity.value),
            "message": {
                "text": finding.message,
            },
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": report.file_path,
                    },
                    "region": {
                        "byteOffset": finding.position,
                    }
                }
            }],
            "properties": {
                "callable": finding.callable,
                "evidence": finding.evidence,
            }
        }

    @staticmethod
    def _severity_to_level(severity: int) -> str:
        """Convert severity to SARIF level."""
        if severity >= 4:
            return "error"
        elif severity >= 3:
            return "warning"
        elif severity >= 2:
            return "note"
        return "none"

    def save_report(self, report: ScanReport, path: Path) -> None:
        """Save a report to a file."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.format_report(report))
            f.write("\n")

    def save_batch(self, reports: List[ScanReport], path: Path) -> None:
        """Save multiple reports to a file."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.format_batch(reports))
            f.write("\n")
