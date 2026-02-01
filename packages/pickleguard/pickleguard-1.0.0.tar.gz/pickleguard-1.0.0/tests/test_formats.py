"""Tests for format detection."""

import tempfile
import os
from pathlib import Path

import pytest

from pickle_scanner.formats.detector import detect_format, FileFormat


class TestFormatDetection:
    """Test format detection functionality."""

    def test_detect_raw_pickle(self):
        """Test detection of raw pickle format."""
        # Protocol 4 pickle header
        pickle_data = b"\x80\x04\x95\x00\x00\x00\x00\x00\x00\x00."

        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            f.write(pickle_data)
            temp_path = f.name

        try:
            result = detect_format(Path(temp_path))
            assert result.format == FileFormat.PICKLE
        finally:
            os.unlink(temp_path)

    def test_detect_pytorch_zip(self):
        """Test detection of PyTorch ZIP format."""
        import zipfile

        # Create minimal PyTorch-like ZIP
        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
            temp_path = f.name
            with zipfile.ZipFile(f, 'w') as zf:
                zf.writestr("archive/data.pkl", b"\x80\x04\x95\x00\x00\x00\x00\x00\x00\x00.")

        try:
            result = detect_format(Path(temp_path))
            assert result.format == FileFormat.PYTORCH_ZIP
        finally:
            os.unlink(temp_path)

    def test_detect_safetensors(self):
        """Test detection of SafeTensors format (marked as safe)."""
        # SafeTensors header starts with 8-byte little-endian length
        safetensors_data = b"\x08\x00\x00\x00\x00\x00\x00\x00{\"test\":}"

        with tempfile.NamedTemporaryFile(suffix=".safetensors", delete=False) as f:
            f.write(safetensors_data)
            temp_path = f.name

        try:
            result = detect_format(Path(temp_path))
            assert result.format == FileFormat.SAFETENSORS
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
