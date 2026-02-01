#!/usr/bin/env python3
"""
PickleGuard CLI - Detect malicious pickle files.

Usage:
    pickleguard scan <path> [options]
    pickleguard scan <directory> --recursive [options]
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from pickle_scanner.core.scanner import PickleScanner, ScannerConfig, ScanResult
from pickle_scanner.reporting.report import ScanReport, RiskLevel
from pickle_scanner.reporting.json_output import JSONReporter, SARIFReporter
from pickle_scanner.rules.engine import RuleEngine
from pickle_scanner.rules.builtin import BUILTIN_RULES


# ANSI color codes
class Colors:
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    @classmethod
    def disable(cls):
        cls.RED = ''
        cls.YELLOW = ''
        cls.GREEN = ''
        cls.BLUE = ''
        cls.CYAN = ''
        cls.BOLD = ''
        cls.RESET = ''


def colorize_risk(level: RiskLevel) -> str:
    """Return colored risk level string."""
    colors = {
        RiskLevel.CRITICAL: Colors.RED + Colors.BOLD,
        RiskLevel.HIGH: Colors.RED,
        RiskLevel.MEDIUM: Colors.YELLOW,
        RiskLevel.LOW: Colors.BLUE,
        RiskLevel.SAFE: Colors.GREEN,
    }
    color = colors.get(level, '')
    return f"{color}{level.name}{Colors.RESET}"


def print_report(report: ScanReport, verbose: bool = False, show_safe: bool = False) -> None:
    """Print a formatted report to console."""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}File:{Colors.RESET} {report.file_path}")
    print(f"{Colors.BOLD}Format:{Colors.RESET} {report.format}")
    if report.protocol is not None:
        print(f"{Colors.BOLD}Protocol:{Colors.RESET} {report.protocol}")

    print(f"\n{Colors.BOLD}Risk Assessment:{Colors.RESET}")
    print(f"  Level: {colorize_risk(report.risk_level)}")
    print(f"  Score: {report.risk_score}/100")
    print(f"  Confidence: {report.threat_score.confidence:.0%}")

    if report.ml_framework_detected:
        print(f"\n{Colors.BOLD}ML Framework:{Colors.RESET} {report.ml_framework_detected}")

    if report.obfuscation_techniques:
        print(f"\n{Colors.BOLD}Obfuscation Detected:{Colors.RESET}")
        for tech in report.obfuscation_techniques:
            print(f"  - {Colors.YELLOW}{tech}{Colors.RESET}")

    if report.findings:
        print(f"\n{Colors.BOLD}Findings ({len(report.findings)}):{Colors.RESET}")
        for finding in sorted(report.findings, key=lambda f: -f.severity.value):
            severity_color = {
                4: Colors.RED + Colors.BOLD,
                3: Colors.RED,
                2: Colors.YELLOW,
                1: Colors.BLUE,
                0: Colors.CYAN,
            }.get(finding.severity.value, '')

            print(f"\n  [{severity_color}{finding.severity.name}{Colors.RESET}] {finding.rule}")
            print(f"    {finding.message}")
            if finding.callable:
                print(f"    Callable: {Colors.CYAN}{finding.callable}{Colors.RESET}")
            if finding.arguments and verbose:
                print(f"    Arguments: {finding.arguments}")
            if finding.evidence and verbose:
                print(f"    Evidence: {finding.evidence}")
            print(f"    Position: {finding.position}")

    if verbose and report.globals_observed:
        print(f"\n{Colors.BOLD}Globals Observed ({len(report.globals_observed)}):{Colors.RESET}")
        for g in report.globals_observed:
            if g.is_dangerous:
                status = f"{Colors.RED}DANGEROUS{Colors.RESET}"
            elif g.is_safe_ml:
                if not show_safe:
                    continue
                status = f"{Colors.GREEN}SAFE ML{Colors.RESET}"
            else:
                status = "unknown"
            print(f"  {g.module}.{g.name} [{status}] @ {g.position}")

    if report.errors:
        print(f"\n{Colors.BOLD}Errors:{Colors.RESET}")
        for error in report.errors:
            print(f"  {Colors.YELLOW}⚠ {error}{Colors.RESET}")

    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")


def print_summary(reports: List[ScanReport]) -> None:
    """Print batch scan summary."""
    total = len(reports)
    malicious = sum(1 for r in reports if r.is_malicious)
    high_risk = sum(1 for r in reports if r.risk_level == RiskLevel.HIGH)
    medium_risk = sum(1 for r in reports if r.risk_level == RiskLevel.MEDIUM)
    low_risk = sum(1 for r in reports if r.risk_level == RiskLevel.LOW)
    safe = sum(1 for r in reports if r.risk_level == RiskLevel.SAFE)
    errors = sum(1 for r in reports if r.errors)

    print(f"\n{Colors.BOLD}{'='*60}")
    print(f"SCAN SUMMARY")
    print(f"{'='*60}{Colors.RESET}")
    print(f"Total files scanned: {total}")
    print(f"  {Colors.RED}CRITICAL:{Colors.RESET} {sum(1 for r in reports if r.risk_level == RiskLevel.CRITICAL)}")
    print(f"  {Colors.RED}HIGH:{Colors.RESET}     {high_risk}")
    print(f"  {Colors.YELLOW}MEDIUM:{Colors.RESET}   {medium_risk}")
    print(f"  {Colors.BLUE}LOW:{Colors.RESET}      {low_risk}")
    print(f"  {Colors.GREEN}SAFE:{Colors.RESET}     {safe}")
    if errors:
        print(f"  {Colors.YELLOW}ERRORS:{Colors.RESET}   {errors}")
    print(f"\n{Colors.BOLD}Detection rate:{Colors.RESET} {malicious}/{total} ({100*malicious/max(1,total):.1f}%)")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")


def find_pickle_files(directory: Path, recursive: bool = True) -> List[Path]:
    """Find pickle/model files in a directory."""
    extensions = {'.pkl', '.pickle', '.pt', '.pth', '.bin', '.npy', '.npz', '.joblib'}

    files = []
    if recursive:
        for ext in extensions:
            files.extend(directory.rglob(f'*{ext}'))
        # Also check files without extension that might be pickles
        for f in directory.rglob('*'):
            if f.is_file() and f.suffix == '' and f.stat().st_size < 100_000_000:  # 100MB limit
                files.append(f)
    else:
        for f in directory.iterdir():
            if f.is_file() and (f.suffix in extensions or f.suffix == ''):
                files.append(f)

    return sorted(set(files))


def scan_command(args) -> int:
    """Handle scan command."""
    path = Path(args.path)

    if not path.exists():
        print(f"{Colors.RED}Error: Path not found: {path}{Colors.RESET}", file=sys.stderr)
        return 1

    # Configure scanner
    config = ScannerConfig(
        verbose=args.verbose,
        include_safe_patterns=args.show_safe_patterns,
    )

    scanner = PickleScanner(config)
    reports: List[ScanReport] = []

    if path.is_file():
        # Single file scan
        result = scanner.scan_file(path)
        reports.append(result.report)
    else:
        # Directory scan
        files = find_pickle_files(path, recursive=args.recursive)
        if not files:
            print(f"{Colors.YELLOW}No pickle files found in {path}{Colors.RESET}")
            return 0

        print(f"Scanning {len(files)} files...\n")

        for f in files:
            result = scanner.scan_file(f)
            reports.append(result.report)

            if args.verbose or result.report.is_malicious:
                # Show progress for dangerous files immediately
                if result.report.is_malicious:
                    print(f"{Colors.RED}[!]{Colors.RESET} {f}: {colorize_risk(result.report.risk_level)}")
                elif args.verbose:
                    print(f"[·] {f}: {colorize_risk(result.report.risk_level)}")

    # Output results
    if args.format == 'json':
        reporter = JSONReporter(pretty=True)
        if args.output:
            if len(reports) == 1:
                reporter.save_report(reports[0], Path(args.output))
            else:
                reporter.save_batch(reports, Path(args.output))
            print(f"Report saved to {args.output}")
        else:
            if len(reports) == 1:
                print(reporter.format_report(reports[0]))
            else:
                print(reporter.format_batch(reports))

    elif args.format == 'sarif':
        reporter = SARIFReporter()
        if args.output:
            if len(reports) == 1:
                reporter.save_report(reports[0], Path(args.output))
            else:
                reporter.save_batch(reports, Path(args.output))
            print(f"SARIF report saved to {args.output}")
        else:
            if len(reports) == 1:
                print(reporter.format_report(reports[0]))
            else:
                print(reporter.format_batch(reports))

    else:  # text format
        for report in reports:
            print_report(report, verbose=args.verbose, show_safe=args.show_safe_patterns)

        if len(reports) > 1:
            print_summary(reports)

    # Return code based on findings
    if any(r.risk_level >= RiskLevel.HIGH for r in reports):
        return 2  # High risk found
    elif any(r.risk_level >= RiskLevel.MEDIUM for r in reports):
        return 1  # Medium risk found
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='PickleGuard - Detect malicious pickle files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s scan model.pt                  # Scan a single file
  %(prog)s scan ./models/ --recursive     # Scan directory recursively
  %(prog)s scan model.pt --format json    # Output as JSON
  %(prog)s scan ./models/ --format sarif  # SARIF for CI/CD
        """
    )

    parser.add_argument('--no-color', action='store_true',
                        help='Disable colored output')
    parser.add_argument('--version', action='version', version='pickleguard 1.0.0')

    subparsers = parser.add_subparsers(dest='command', help='Command')

    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan file(s) for threats')
    scan_parser.add_argument('path', help='File or directory to scan')
    scan_parser.add_argument('-r', '--recursive', action='store_true',
                            help='Recursively scan directories')
    scan_parser.add_argument('-f', '--format', choices=['text', 'json', 'sarif'],
                            default='text', help='Output format (default: text)')
    scan_parser.add_argument('-o', '--output', help='Output file path')
    scan_parser.add_argument('-v', '--verbose', action='store_true',
                            help='Verbose output')
    scan_parser.add_argument('--show-safe-patterns', action='store_true',
                            help='Show safe ML patterns in output')
    scan_parser.add_argument('--rules', help='Custom rules YAML file')

    args = parser.parse_args()

    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    if args.command == 'scan':
        return scan_command(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
