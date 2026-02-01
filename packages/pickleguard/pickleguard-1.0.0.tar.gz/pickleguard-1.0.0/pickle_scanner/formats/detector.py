"""
File format detection for ML model files.

Detects:
- Raw pickle streams
- PyTorch ZIP containers (.pt, .pth, .bin)
- SafeTensors files
- ONNX files
- Numpy files (.npy, .npz)
"""

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Optional, BinaryIO, Tuple
import struct


class FileFormat(Enum):
    """Detected file formats."""
    UNKNOWN = auto()
    PICKLE = auto()           # Raw pickle stream
    PYTORCH_ZIP = auto()      # PyTorch ZIP container
    PYTORCH_LEGACY = auto()   # Legacy PyTorch (tar-based)
    SAFETENSORS = auto()      # SafeTensors (safe)
    ONNX = auto()             # ONNX format
    NUMPY_NPY = auto()        # Numpy .npy
    NUMPY_NPZ = auto()        # Numpy .npz (ZIP)
    KERAS_H5 = auto()         # Keras HDF5


# File magic bytes
MAGIC_BYTES = {
    b'PK\x03\x04': FileFormat.PYTORCH_ZIP,  # ZIP (PyTorch uses ZIP)
    b'PK\x05\x06': FileFormat.PYTORCH_ZIP,  # Empty ZIP
    b'\x93NUMPY': FileFormat.NUMPY_NPY,     # NumPy .npy
    b'\x89HDF': FileFormat.KERAS_H5,        # HDF5
}

# Pickle protocol magic bytes
PICKLE_PROTO_MAGIC = b'\x80'  # Protocol 2+ start with PROTO opcode

# SafeTensors has a specific header format
SAFETENSORS_MIN_HEADER = 8  # uint64 header size


@dataclass
class FormatInfo:
    """Information about detected format."""
    format: FileFormat
    confidence: float  # 0.0 to 1.0
    details: str = ""
    pickle_locations: list = None  # For ZIP containers

    def __post_init__(self):
        if self.pickle_locations is None:
            self.pickle_locations = []


def detect_format(path: Path) -> FormatInfo:
    """Detect format of a file by path."""
    if not path.exists():
        return FormatInfo(FileFormat.UNKNOWN, 0.0, "File not found")

    try:
        with open(path, 'rb') as f:
            return detect_format_from_bytes(f.read(8192), path.suffix)
    except Exception as e:
        return FormatInfo(FileFormat.UNKNOWN, 0.0, f"Error reading file: {e}")


def detect_format_from_bytes(data: bytes, suffix: str = "") -> FormatInfo:
    """Detect format from bytes."""
    if len(data) < 4:
        return FormatInfo(FileFormat.UNKNOWN, 0.0, "File too small")

    suffix = suffix.lower()

    # Check magic bytes first
    for magic, fmt in MAGIC_BYTES.items():
        if data.startswith(magic):
            if fmt == FileFormat.PYTORCH_ZIP:
                return _analyze_zip(data, suffix)
            elif fmt == FileFormat.NUMPY_NPY:
                return FormatInfo(FileFormat.NUMPY_NPY, 1.0, "NumPy array file")
            elif fmt == FileFormat.KERAS_H5:
                return FormatInfo(FileFormat.KERAS_H5, 0.9, "HDF5/Keras file")

    # Check for SafeTensors (JSON header with uint64 length prefix)
    if _is_safetensors(data):
        return FormatInfo(FileFormat.SAFETENSORS, 0.95, "SafeTensors format (safe)")

    # Check for ONNX (protobuf)
    if _is_onnx(data, suffix):
        return FormatInfo(FileFormat.ONNX, 0.8, "ONNX protobuf format")

    # Check for pickle
    pickle_info = _detect_pickle(data)
    if pickle_info:
        return pickle_info

    # Unknown
    return FormatInfo(FileFormat.UNKNOWN, 0.0, "Unknown format")


def _analyze_zip(data: bytes, suffix: str) -> FormatInfo:
    """Analyze a ZIP file to determine if it's PyTorch."""
    import zipfile
    import io

    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()

            # Look for PyTorch signatures
            has_data_pkl = any('data.pkl' in n for n in names)
            has_version = any('version' in n for n in names)
            has_tensors = any(n.endswith('.storage') or '/data/' in n for n in names)

            pickle_files = [n for n in names if n.endswith('.pkl') or n.endswith('.pickle')]

            if has_data_pkl or (has_tensors and suffix in ('.pt', '.pth', '.bin')):
                return FormatInfo(
                    FileFormat.PYTORCH_ZIP,
                    0.95,
                    f"PyTorch ZIP container with {len(pickle_files)} pickle files",
                    pickle_files
                )

            # Check for npz
            if suffix == '.npz' or all(n.endswith('.npy') for n in names):
                return FormatInfo(FileFormat.NUMPY_NPZ, 0.9, "NumPy npz archive")

            # Generic ZIP with pickles
            if pickle_files:
                return FormatInfo(
                    FileFormat.PYTORCH_ZIP,
                    0.7,
                    f"ZIP with {len(pickle_files)} pickle files",
                    pickle_files
                )

            return FormatInfo(FileFormat.UNKNOWN, 0.3, "ZIP archive without known ML patterns")

    except zipfile.BadZipFile:
        return FormatInfo(FileFormat.UNKNOWN, 0.0, "Invalid ZIP file")


def _is_safetensors(data: bytes) -> bool:
    """Check if data looks like SafeTensors format."""
    if len(data) < 8:
        return False

    try:
        # SafeTensors starts with uint64 header size in little-endian
        header_size = struct.unpack('<Q', data[:8])[0]

        # Header size should be reasonable (< 100MB)
        if header_size > 100_000_000:
            return False

        # If we have enough data, check if header looks like JSON
        if len(data) > 8:
            # JSON header should start with '{'
            header_start = data[8:9]
            if header_start == b'{':
                return True

        # Could be SafeTensors with header size within data bounds
        return 8 < header_size < len(data)

    except struct.error:
        return False


def _is_onnx(data: bytes, suffix: str) -> bool:
    """Check if data might be ONNX format."""
    # ONNX is protobuf, check for common protobuf patterns
    if suffix == '.onnx':
        # Protobuf wire format check
        if len(data) > 4:
            # Field 1, wire type 0 (ir_version) or field 1, wire type 2 (string)
            return data[0] in (0x08, 0x0a)
    return False


def _detect_pickle(data: bytes) -> Optional[FormatInfo]:
    """Detect if data is a pickle stream."""
    if len(data) < 2:
        return None

    # Protocol 2+ start with PROTO opcode
    if data[0:1] == PICKLE_PROTO_MAGIC:
        protocol = data[1]
        if 2 <= protocol <= 5:
            return FormatInfo(
                FileFormat.PICKLE,
                0.95,
                f"Pickle protocol {protocol}"
            )

    # Protocol 0 starts with text-based opcodes
    # Common starts: ( for MARK, c for GLOBAL, I for INT, etc.
    proto0_starts = b'(cCdFgIlLNpPRSVX'
    if data[0:1] in [bytes([b]) for b in proto0_starts]:
        # Further verify by looking for STOP opcode
        if b'.' in data[:1000]:
            return FormatInfo(
                FileFormat.PICKLE,
                0.8,
                "Pickle protocol 0 (text-based)"
            )

    # Protocol 1 uses binary opcodes but no PROTO
    proto1_opcodes = b'}])KMJqhj'
    if data[0:1] in [bytes([b]) for b in proto1_opcodes]:
        return FormatInfo(
            FileFormat.PICKLE,
            0.7,
            "Pickle protocol 1 (binary)"
        )

    return None


def is_safe_format(fmt: FileFormat) -> bool:
    """Check if format is inherently safe (no code execution)."""
    return fmt in (
        FileFormat.SAFETENSORS,
        FileFormat.NUMPY_NPY,
        FileFormat.ONNX,
    )
