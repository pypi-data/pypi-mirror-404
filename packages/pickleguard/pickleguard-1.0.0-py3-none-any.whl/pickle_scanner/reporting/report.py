"""
Report data structures for scan results.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional, Dict, Any
from datetime import datetime


class RiskLevel(IntEnum):
    """Risk classification levels."""
    SAFE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def from_score(cls, score: int) -> 'RiskLevel':
        """Convert numeric score to risk level."""
        if score >= 85:
            return cls.CRITICAL
        elif score >= 60:
            return cls.HIGH
        elif score >= 30:
            return cls.MEDIUM
        elif score > 0:
            return cls.LOW
        return cls.SAFE

    def __str__(self) -> str:
        return self.name


class Severity(IntEnum):
    """Finding severity levels."""
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Finding:
    """A security finding in the scan."""
    rule: str
    severity: Severity
    position: int
    message: str
    callable: Optional[str] = None
    arguments: Optional[str] = None
    evidence: str = ""
    opcode: Optional[str] = None
    remediation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule": self.rule,
            "severity": self.severity.name.lower(),
            "position": self.position,
            "message": self.message,
            "callable": self.callable,
            "arguments": self.arguments,
            "evidence": self.evidence,
            "opcode": self.opcode,
            "remediation": self.remediation,
        }


@dataclass
class ThreatScore:
    """Multi-factor threat scoring."""
    base_score: int = 0           # 0-100 from callable risk
    obfuscation_penalty: int = 0  # +0-30 for obfuscation techniques
    context_adjustment: int = 0   # -20 to +20 based on ML patterns
    confidence: float = 1.0       # 0.0-1.0 confidence level

    @property
    def final_score(self) -> int:
        """Calculate final score clamped to 0-100."""
        return min(100, max(0, self.base_score + self.obfuscation_penalty + self.context_adjustment))

    @property
    def risk_level(self) -> RiskLevel:
        """Get risk level from final score."""
        return RiskLevel.from_score(self.final_score)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "base_score": self.base_score,
            "obfuscation_penalty": self.obfuscation_penalty,
            "context_adjustment": self.context_adjustment,
            "final_score": self.final_score,
            "confidence": self.confidence,
            "risk_level": str(self.risk_level),
        }


@dataclass
class GlobalInfo:
    """Information about a global reference."""
    module: str
    name: str
    position: int
    opcode: str
    is_dangerous: bool = False
    is_safe_ml: bool = False
    risk_description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "name": self.name,
            "full_path": f"{self.module}.{self.name}",
            "position": self.position,
            "opcode": self.opcode,
            "is_dangerous": self.is_dangerous,
            "is_safe_ml": self.is_safe_ml,
            "risk_description": self.risk_description,
        }


@dataclass
class ScanReport:
    """Complete scan report for a file."""
    file_path: str
    format: str
    protocol: Optional[int] = None
    scan_time: datetime = field(default_factory=datetime.utcnow)

    # Scoring
    threat_score: ThreatScore = field(default_factory=ThreatScore)

    # Findings
    findings: List[Finding] = field(default_factory=list)

    # Details
    globals_observed: List[GlobalInfo] = field(default_factory=list)
    obfuscation_techniques: List[str] = field(default_factory=list)
    ml_framework_detected: Optional[str] = None

    # Metadata
    file_size: int = 0
    pickle_count: int = 1  # For containers with multiple pickles
    errors: List[str] = field(default_factory=list)

    @property
    def risk_score(self) -> int:
        """Get the final risk score."""
        return self.threat_score.final_score

    @property
    def risk_level(self) -> RiskLevel:
        """Get the risk level."""
        return self.threat_score.risk_level

    @property
    def is_malicious(self) -> bool:
        """Check if likely malicious (HIGH or CRITICAL risk)."""
        return self.risk_level >= RiskLevel.HIGH

    @property
    def finding_count(self) -> int:
        """Get total finding count."""
        return len(self.findings)

    @property
    def critical_finding_count(self) -> int:
        """Get critical finding count."""
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    def add_finding(self, finding: Finding) -> None:
        """Add a finding to the report."""
        self.findings.append(finding)

    def add_global(self, info: GlobalInfo) -> None:
        """Add a global observation."""
        self.globals_observed.append(info)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file": self.file_path,
            "format": self.format,
            "protocol": self.protocol,
            "scan_time": self.scan_time.isoformat(),
            "risk_score": self.risk_score,
            "risk_level": str(self.risk_level),
            "confidence": self.threat_score.confidence,
            "threat_score": self.threat_score.to_dict(),
            "findings": [f.to_dict() for f in self.findings],
            "globals_observed": [g.to_dict() for g in self.globals_observed],
            "obfuscation_techniques": self.obfuscation_techniques,
            "ml_framework_detected": self.ml_framework_detected,
            "file_size": self.file_size,
            "pickle_count": self.pickle_count,
            "errors": self.errors,
            "summary": {
                "total_findings": self.finding_count,
                "critical_findings": self.critical_finding_count,
                "is_malicious": self.is_malicious,
            }
        }

    def summary(self) -> str:
        """Generate a human-readable summary."""
        lines = [
            f"File: {self.file_path}",
            f"Format: {self.format}",
            f"Risk Level: {self.risk_level} (score: {self.risk_score})",
            f"Confidence: {self.threat_score.confidence:.0%}",
            f"Findings: {self.finding_count} ({self.critical_finding_count} critical)",
        ]

        if self.ml_framework_detected:
            lines.append(f"ML Framework: {self.ml_framework_detected}")

        if self.obfuscation_techniques:
            lines.append(f"Obfuscation: {', '.join(self.obfuscation_techniques)}")

        return "\n".join(lines)
