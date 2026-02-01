"""
PickleGuard - Production-grade static analysis for detecting malicious pickle files.

Protects ML pipelines from pickle-based attacks through:
- Deep opcode analysis with obfuscation detection
- Pure static analysis (no code execution)
- ML-aware whitelisting to eliminate false positives
- Support for PyTorch, NumPy, and raw pickle formats
"""

from pickle_scanner.core.scanner import PickleScanner, ScanResult
from pickle_scanner.reporting.report import Finding, RiskLevel, ThreatScore

__version__ = "1.0.0"
__all__ = ["PickleScanner", "ScanResult", "Finding", "RiskLevel", "ThreatScore"]
