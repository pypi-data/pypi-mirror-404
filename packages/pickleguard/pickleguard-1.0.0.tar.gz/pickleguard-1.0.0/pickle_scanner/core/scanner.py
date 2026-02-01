"""
Main pickle security scanner.

Orchestrates format detection, parsing, analysis, and reporting.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Union
import os

from pickle_scanner.core.opcodes import ParsedOpcode
from pickle_scanner.core.stack_machine import StackMachine, GlobalRef
from pickle_scanner.formats.detector import (
    detect_format,
    detect_format_from_bytes,
    FileFormat,
    FormatInfo,
    is_safe_format,
)
from pickle_scanner.formats.pickle_parser import PickleParser, PickleStream
from pickle_scanner.formats.torch_parser import TorchParser, TorchArchive
from pickle_scanner.analysis.threat_intel import (
    ThreatDatabase,
    get_threat_database,
    is_dangerous_callable,
    RiskLevel as ThreatRiskLevel,
)
from pickle_scanner.analysis.obfuscation import (
    ObfuscationDetector,
    ObfuscationFinding,
    detect_obfuscation,
)
from pickle_scanner.analysis.ml_patterns import (
    MLPatternMatcher,
    detect_ml_framework,
    is_safe_ml_pattern,
    MLFramework,
)
from pickle_scanner.reporting.report import (
    ScanReport,
    Finding,
    ThreatScore,
    GlobalInfo,
    RiskLevel,
    Severity,
)


@dataclass
class ScanResult:
    """Result of a pickle scan."""
    report: ScanReport
    success: bool = True
    error: Optional[str] = None


@dataclass
class ScannerConfig:
    """Configuration for the scanner."""
    # Analysis options
    deep_analysis: bool = True      # Enable stack machine analysis
    detect_obfuscation: bool = True # Check for obfuscation techniques
    ml_pattern_matching: bool = True # Recognize safe ML patterns

    # Scoring adjustments
    ml_context_bonus: int = -15     # Score reduction for recognized ML patterns
    obfuscation_penalty_max: int = 30  # Maximum obfuscation penalty

    # Output options
    verbose: bool = False
    include_safe_patterns: bool = False  # Include safe pattern matches in report


class PickleScanner:
    """Main pickle security scanner."""

    def __init__(self, config: Optional[ScannerConfig] = None):
        self.config = config or ScannerConfig()
        self.threat_db = get_threat_database()
        self._last_error: Optional[str] = None

    def scan_file(self, path: Union[str, Path]) -> ScanResult:
        """Scan a file for pickle-based threats."""
        path = Path(path)

        if not path.exists():
            return ScanResult(
                report=ScanReport(file_path=str(path), format="unknown"),
                success=False,
                error=f"File not found: {path}"
            )

        try:
            file_size = path.stat().st_size
            with open(path, 'rb') as f:
                data = f.read()

            result = self.scan_bytes(data, str(path))
            result.report.file_size = file_size
            return result

        except Exception as e:
            return ScanResult(
                report=ScanReport(file_path=str(path), format="unknown"),
                success=False,
                error=f"Error reading file: {e}"
            )

    def scan_bytes(self, data: bytes, source: str = "<bytes>") -> ScanResult:
        """Scan bytes for pickle-based threats."""
        # Detect format
        format_info = detect_format_from_bytes(data)

        # Create report
        report = ScanReport(
            file_path=source,
            format=format_info.format.name.lower(),
            file_size=len(data),
        )

        # Safe formats don't need scanning
        if is_safe_format(format_info.format):
            report.threat_score = ThreatScore(
                base_score=0,
                confidence=format_info.confidence,
            )
            return ScanResult(report=report)

        # Route to appropriate parser
        try:
            if format_info.format == FileFormat.PYTORCH_ZIP:
                self._scan_pytorch(data, report, format_info)
            elif format_info.format == FileFormat.PICKLE:
                self._scan_raw_pickle(data, report)
            elif format_info.format == FileFormat.NUMPY_NPZ:
                self._scan_npz(data, report)
            else:
                # Try as raw pickle
                self._scan_raw_pickle(data, report)

        except Exception as e:
            report.errors.append(f"Analysis error: {e}")
            self._last_error = str(e)

        return ScanResult(report=report)

    def _scan_pytorch(
        self,
        data: bytes,
        report: ScanReport,
        format_info: FormatInfo
    ) -> None:
        """Scan a PyTorch ZIP container."""
        parser = TorchParser(data=data)
        archive = parser.parse()

        report.format = f"pytorch_{archive.format}"
        report.pickle_count = len(archive.pickle_entries)
        report.errors.extend(archive.errors)

        # Analyze each pickle entry
        for entry in archive.pickle_entries:
            if entry.stream:
                self._analyze_pickle_stream(entry.stream, report)

        # Finalize scoring
        self._finalize_report(report)

    def _scan_raw_pickle(self, data: bytes, report: ScanReport) -> None:
        """Scan a raw pickle stream."""
        parser = PickleParser(data)
        stream = parser.parse()

        report.protocol = stream.protocol
        report.errors.extend(stream.errors)

        self._analyze_pickle_stream(stream, report)
        self._finalize_report(report)

    def _scan_npz(self, data: bytes, report: ScanReport) -> None:
        """Scan a NumPy npz file (can contain pickles)."""
        import zipfile
        import io

        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for name in zf.namelist():
                    if name.endswith('.npy'):
                        npy_data = zf.read(name)
                        # Check if npy uses pickle (object arrays)
                        if b'\x93NUMPY' in npy_data[:10]:
                            # NumPy format, check for object dtype
                            # Object arrays use pickle internally
                            if b"'O'" in npy_data[:200] or b"object" in npy_data[:200]:
                                report.errors.append(f"Object array in {name} may contain pickle")
        except Exception as e:
            report.errors.append(f"NPZ parse error: {e}")

        self._finalize_report(report)

    def _analyze_pickle_stream(self, stream: PickleStream, report: ScanReport) -> None:
        """Analyze a parsed pickle stream."""
        # Run stack machine simulation if enabled
        machine = None
        if self.config.deep_analysis:
            machine = StackMachine()
            machine.protocol = stream.protocol
            for opcode in stream.opcodes:
                machine.process_opcode(opcode)
            report.errors.extend(machine.errors)

        # Analyze globals
        if machine:
            self._analyze_globals(machine.globals_found, report)

            # Analyze reduce calls for argument extraction
            for call in machine.reduce_calls:
                if call.callable_ref:
                    self._check_reduce_call(call, report)

        else:
            # Fallback: extract globals directly from opcodes
            self._analyze_globals_from_opcodes(stream.opcodes, report)

        # Detect obfuscation
        if self.config.detect_obfuscation:
            obfuscation_findings = detect_obfuscation(stream.opcodes, machine)
            for finding in obfuscation_findings:
                report.obfuscation_techniques.append(finding.technique.name)
                report.threat_score.obfuscation_penalty += finding.severity

                # Add finding
                report.add_finding(Finding(
                    rule=f"obfuscation_{finding.technique.name.lower()}",
                    severity=Severity.HIGH if finding.severity >= 20 else Severity.MEDIUM,
                    position=finding.position,
                    message=finding.description,
                    evidence=finding.evidence,
                ))

        # ML framework detection
        if self.config.ml_pattern_matching and machine:
            framework = detect_ml_framework(machine.globals_found)
            if framework != MLFramework.UNKNOWN:
                report.ml_framework_detected = framework.name

    def _analyze_globals(
        self,
        globals_found: List[Tuple[GlobalRef, int]],
        report: ScanReport
    ) -> None:
        """Analyze global references for threats."""
        ml_matcher = MLPatternMatcher() if self.config.ml_pattern_matching else None
        dangerous_count = 0
        safe_ml_count = 0

        for ref, position in globals_found:
            # Check if dangerous
            is_dangerous, risk_info = is_dangerous_callable(ref.module, ref.name)

            # Check if safe ML pattern
            is_safe_ml = False
            ml_desc = None
            if ml_matcher:
                match = ml_matcher.match_global(ref)
                if match:
                    is_safe_ml = True
                    ml_desc = match.description
                    safe_ml_count += 1

            # Create global info
            global_info = GlobalInfo(
                module=ref.module,
                name=ref.name,
                position=position,
                opcode=ref.opcode,
                is_dangerous=is_dangerous,
                is_safe_ml=is_safe_ml,
                risk_description=risk_info.description if risk_info else ml_desc,
            )
            report.add_global(global_info)

            # Generate findings for dangerous callables
            if is_dangerous and risk_info:
                dangerous_count += 1

                # Determine severity
                if risk_info.risk_level >= ThreatRiskLevel.CRITICAL:
                    severity = Severity.CRITICAL
                elif risk_info.risk_level >= ThreatRiskLevel.HIGH:
                    severity = Severity.HIGH
                elif risk_info.risk_level >= ThreatRiskLevel.MEDIUM:
                    severity = Severity.MEDIUM
                else:
                    severity = Severity.LOW

                report.add_finding(Finding(
                    rule=f"dangerous_callable_{risk_info.category}",
                    severity=severity,
                    position=position,
                    message=f"Dangerous callable: {ref.full_path} - {risk_info.description}",
                    callable=ref.full_path,
                    opcode=ref.opcode,
                    evidence=f"{ref.opcode} {ref.module} {ref.name}",
                ))

                # Update base score
                report.threat_score.base_score = max(
                    report.threat_score.base_score,
                    risk_info.risk_level
                )

        # Apply ML context adjustment
        if safe_ml_count > 0 and dangerous_count == 0:
            report.threat_score.context_adjustment = self.config.ml_context_bonus

    def _analyze_globals_from_opcodes(
        self,
        opcodes: List[ParsedOpcode],
        report: ScanReport
    ) -> None:
        """Fallback: analyze globals directly from opcodes."""
        for op in opcodes:
            if op.name in ('GLOBAL', 'INST'):
                if isinstance(op.arg, tuple) and len(op.arg) == 2:
                    module, name = op.arg
                elif isinstance(op.arg, str) and '\n' in op.arg:
                    parts = op.arg.split('\n')
                    module, name = parts[0], parts[1] if len(parts) > 1 else ""
                else:
                    continue

                ref = GlobalRef(module, name, op.name)
                is_dangerous, risk_info = is_dangerous_callable(module, name)

                global_info = GlobalInfo(
                    module=module,
                    name=name,
                    position=op.position,
                    opcode=op.name,
                    is_dangerous=is_dangerous,
                    risk_description=risk_info.description if risk_info else None,
                )
                report.add_global(global_info)

                if is_dangerous and risk_info:
                    severity = Severity.CRITICAL if risk_info.risk_level >= ThreatRiskLevel.CRITICAL else Severity.HIGH

                    report.add_finding(Finding(
                        rule=f"dangerous_callable_{risk_info.category}",
                        severity=severity,
                        position=op.position,
                        message=f"Dangerous callable: {module}.{name}",
                        callable=f"{module}.{name}",
                        opcode=op.name,
                    ))

                    report.threat_score.base_score = max(
                        report.threat_score.base_score,
                        risk_info.risk_level
                    )

    def _check_reduce_call(self, call, report: ScanReport) -> None:
        """Check a REDUCE call for additional context."""
        ref = call.callable_ref
        if not ref:
            return

        # Try to extract argument information
        args_str = None
        if call.args is not None:
            try:
                args_str = repr(call.args)[:200]  # Limit length
            except:
                pass

        # Find existing finding and update with args
        for finding in report.findings:
            if finding.callable == ref.full_path and finding.position == call.position:
                finding.arguments = args_str
                break

    def _finalize_report(self, report: ScanReport) -> None:
        """Finalize the report with scoring adjustments."""
        # Cap obfuscation penalty
        report.threat_score.obfuscation_penalty = min(
            report.threat_score.obfuscation_penalty,
            self.config.obfuscation_penalty_max
        )

        # Calculate confidence based on analysis completeness
        confidence = 1.0
        if report.errors:
            confidence -= 0.1 * min(len(report.errors), 3)
        if report.format == "unknown":
            confidence -= 0.2

        report.threat_score.confidence = max(0.5, confidence)

        # Deduplicate obfuscation techniques
        report.obfuscation_techniques = list(set(report.obfuscation_techniques))


def scan_file(path: Union[str, Path], config: Optional[ScannerConfig] = None) -> ScanResult:
    """Convenience function to scan a file."""
    scanner = PickleScanner(config)
    return scanner.scan_file(path)


def scan_bytes(data: bytes, source: str = "<bytes>", config: Optional[ScannerConfig] = None) -> ScanResult:
    """Convenience function to scan bytes."""
    scanner = PickleScanner(config)
    return scanner.scan_bytes(data, source)
