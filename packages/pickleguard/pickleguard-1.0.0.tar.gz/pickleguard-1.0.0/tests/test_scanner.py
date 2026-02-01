"""Tests for the main scanner functionality."""

import pickle
import tempfile
import os
from pathlib import Path

import pytest

from pickle_scanner import PickleScanner, RiskLevel


class TestPickleScanner:
    """Test the main PickleScanner class."""

    def test_scanner_initialization(self):
        """Test that scanner can be initialized."""
        scanner = PickleScanner()
        assert scanner is not None

    def test_scan_safe_pickle(self):
        """Test scanning a safe pickle file."""
        # Create a safe pickle
        safe_data = {"key": "value", "number": 42, "list": [1, 2, 3]}

        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            pickle.dump(safe_data, f)
            temp_path = f.name

        try:
            scanner = PickleScanner()
            result = scanner.scan_file(temp_path)
            assert result.report.risk_level == RiskLevel.SAFE
            assert result.report.risk_score == 0
        finally:
            os.unlink(temp_path)

    def test_scan_malicious_pickle_os_system(self):
        """Test detection of os.system in pickle."""
        # Create a malicious pickle using raw opcodes
        malicious_pickle = (
            b"cos\nsystem\n"  # GLOBAL os system
            b"(S'echo test'\n"  # STRING 'echo test'
            b"tR."  # TUPLE, REDUCE, STOP
        )

        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            f.write(malicious_pickle)
            temp_path = f.name

        try:
            scanner = PickleScanner()
            result = scanner.scan_file(temp_path)
            assert result.report.risk_level == RiskLevel.CRITICAL
            assert result.report.risk_score > 80
            assert any("os.system" in str(f.message) or "os" in str(f.callable)
                      for f in result.report.findings)
        finally:
            os.unlink(temp_path)

    def test_scan_malicious_pickle_eval(self):
        """Test detection of builtins.eval in pickle."""
        malicious_pickle = (
            b"c__builtin__\neval\n"  # GLOBAL __builtin__ eval
            b"(S'print(1)'\n"  # STRING
            b"tR."  # TUPLE, REDUCE, STOP
        )

        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            f.write(malicious_pickle)
            temp_path = f.name

        try:
            scanner = PickleScanner()
            result = scanner.scan_file(temp_path)
            assert result.report.risk_level == RiskLevel.CRITICAL
        finally:
            os.unlink(temp_path)

    def test_scan_nonexistent_file(self):
        """Test scanning a file that doesn't exist."""
        scanner = PickleScanner()
        result = scanner.scan_file("/nonexistent/path/file.pkl")
        assert result.error is not None


class TestSafeBuiltins:
    """Test that safe builtins don't trigger false positives."""

    def test_builtin_set_is_safe(self):
        """Test that __builtin__.set doesn't trigger false positive."""
        # Create pickle with set
        data = {1, 2, 3}

        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            pickle.dump(data, f)
            temp_path = f.name

        try:
            scanner = PickleScanner()
            result = scanner.scan_file(temp_path)
            # Should be safe - set is a legitimate builtin
            assert result.report.risk_level == RiskLevel.SAFE
        finally:
            os.unlink(temp_path)

    def test_builtin_frozenset_is_safe(self):
        """Test that frozenset doesn't trigger false positive."""
        data = frozenset([1, 2, 3])

        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            pickle.dump(data, f)
            temp_path = f.name

        try:
            scanner = PickleScanner()
            result = scanner.scan_file(temp_path)
            assert result.report.risk_level == RiskLevel.SAFE
        finally:
            os.unlink(temp_path)


class TestObfuscationDetection:
    """Test obfuscation detection capabilities."""

    def test_inst_opcode_detection(self):
        """Test detection of INST opcode usage."""
        # INST is protocol 0 opcode for instantiation
        malicious_pickle = b"(ios\nsystem\nS'echo pwned'\no."

        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            f.write(malicious_pickle)
            temp_path = f.name

        try:
            scanner = PickleScanner()
            result = scanner.scan_file(temp_path)
            # Should detect dangerous callable
            assert result.report.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
