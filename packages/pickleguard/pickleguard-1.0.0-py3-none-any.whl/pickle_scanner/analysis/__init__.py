"""Analysis modules for threat detection."""

from pickle_scanner.analysis.threat_intel import (
    ThreatDatabase,
    CallableRisk,
    RiskLevel,
    is_dangerous_callable,
)
from pickle_scanner.analysis.obfuscation import (
    ObfuscationDetector,
    ObfuscationTechnique,
)
from pickle_scanner.analysis.ml_patterns import (
    MLPatternMatcher,
    MLFramework,
    is_safe_ml_pattern,
)

__all__ = [
    "ThreatDatabase",
    "CallableRisk",
    "RiskLevel",
    "is_dangerous_callable",
    "ObfuscationDetector",
    "ObfuscationTechnique",
    "MLPatternMatcher",
    "MLFramework",
    "is_safe_ml_pattern",
]
