"""Format detection and parsing modules."""

from pickle_scanner.formats.detector import (
    FileFormat,
    detect_format,
    detect_format_from_bytes,
)
from pickle_scanner.formats.pickle_parser import PickleParser, PickleStream
from pickle_scanner.formats.torch_parser import TorchParser, TorchArchive

__all__ = [
    "FileFormat",
    "detect_format",
    "detect_format_from_bytes",
    "PickleParser",
    "PickleStream",
    "TorchParser",
    "TorchArchive",
]
