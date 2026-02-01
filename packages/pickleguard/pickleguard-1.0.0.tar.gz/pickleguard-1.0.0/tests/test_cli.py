"""Tests for CLI functionality."""

import pickle
import tempfile
import os
import subprocess
import sys

import pytest


class TestCLI:
    """Test command-line interface."""

    def test_cli_help(self):
        """Test that --help works."""
        result = subprocess.run(
            [sys.executable, "-m", "pickle_scanner", "--help"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        assert result.returncode == 0
        assert "pickle_scanner" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_cli_scan_safe_file(self):
        """Test CLI scanning a safe file."""
        # Create safe pickle
        data = {"safe": True}
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            pickle.dump(data, f)
            temp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pickle_scanner", "scan", temp_path],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(__file__))
            )
            assert result.returncode == 0
            assert "SAFE" in result.stdout or "safe" in result.stdout.lower()
        finally:
            os.unlink(temp_path)

    def test_cli_json_output(self):
        """Test CLI JSON output format."""
        import json

        data = {"test": 123}
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            pickle.dump(data, f)
            temp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pickle_scanner", "scan", temp_path, "-f", "json"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(__file__))
            )
            assert result.returncode == 0
            # Should be valid JSON
            output = json.loads(result.stdout)
            assert "files" in output or "risk_level" in output
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
