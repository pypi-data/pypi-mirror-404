"""
PyTorch file format parser.

Handles both ZIP-based and legacy tar-based PyTorch formats.
"""

import zipfile
import tarfile
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple, BinaryIO

from pickle_scanner.formats.pickle_parser import PickleParser, PickleStream


@dataclass
class TorchPickleEntry:
    """A pickle entry within a PyTorch archive."""
    name: str
    data: bytes
    stream: Optional[PickleStream] = None


@dataclass
class TorchArchive:
    """Parsed PyTorch archive."""
    path: str
    format: str  # 'zip' or 'tar' or 'legacy'
    pickle_entries: List[TorchPickleEntry] = field(default_factory=list)
    tensor_entries: List[str] = field(default_factory=list)
    version: Optional[str] = None
    errors: List[str] = field(default_factory=list)


class TorchParser:
    """Parser for PyTorch model files."""

    def __init__(self, path: Optional[Path] = None, data: Optional[bytes] = None):
        self.path = path
        self.data = data
        self.errors: List[str] = []

    def parse(self) -> TorchArchive:
        """Parse a PyTorch file and extract pickle streams."""
        if self.path:
            with open(self.path, 'rb') as f:
                data = f.read()
        elif self.data:
            data = self.data
        else:
            raise ValueError("No path or data provided")

        archive = TorchArchive(
            path=str(self.path) if self.path else "<bytes>",
            format='unknown'
        )

        # Try ZIP format first (most common for modern PyTorch)
        if data[:4] in (b'PK\x03\x04', b'PK\x05\x06'):
            self._parse_zip(data, archive)
        # Try tar format (legacy)
        elif self._looks_like_tar(data):
            self._parse_tar(data, archive)
        # Try as raw pickle
        else:
            self._parse_raw_pickle(data, archive)

        return archive

    def _looks_like_tar(self, data: bytes) -> bool:
        """Check if data might be a tar archive."""
        if len(data) < 512:
            return False
        # Tar magic at offset 257
        magic = data[257:262]
        return magic in (b'ustar', b'ustar ')

    def _parse_zip(self, data: bytes, archive: TorchArchive) -> None:
        """Parse a ZIP-based PyTorch file."""
        archive.format = 'zip'

        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                names = zf.namelist()

                # Read version if present
                version_files = [n for n in names if 'version' in n.lower()]
                if version_files:
                    try:
                        archive.version = zf.read(version_files[0]).decode('utf-8').strip()
                    except:
                        pass

                # Find and parse pickle files
                for name in names:
                    if name.endswith('.pkl') or name.endswith('.pickle') or name.endswith('data.pkl'):
                        try:
                            pkl_data = zf.read(name)
                            parser = PickleParser(pkl_data)
                            stream = parser.parse()
                            entry = TorchPickleEntry(name, pkl_data, stream)
                            archive.pickle_entries.append(entry)
                        except Exception as e:
                            archive.errors.append(f"Error parsing {name}: {e}")

                    # Track tensor storage files
                    elif '/data/' in name or name.endswith('.storage'):
                        archive.tensor_entries.append(name)

        except zipfile.BadZipFile as e:
            archive.errors.append(f"Invalid ZIP file: {e}")
            archive.format = 'invalid_zip'

    def _parse_tar(self, data: bytes, archive: TorchArchive) -> None:
        """Parse a tar-based PyTorch file (legacy format)."""
        archive.format = 'tar'

        try:
            with tarfile.open(fileobj=io.BytesIO(data), mode='r:*') as tf:
                for member in tf.getmembers():
                    if member.name.endswith('.pkl') or member.name.endswith('.pickle'):
                        try:
                            f = tf.extractfile(member)
                            if f:
                                pkl_data = f.read()
                                parser = PickleParser(pkl_data)
                                stream = parser.parse()
                                entry = TorchPickleEntry(member.name, pkl_data, stream)
                                archive.pickle_entries.append(entry)
                        except Exception as e:
                            archive.errors.append(f"Error parsing {member.name}: {e}")

                    elif 'tensor' in member.name.lower() or member.name.endswith('.data'):
                        archive.tensor_entries.append(member.name)

        except tarfile.TarError as e:
            archive.errors.append(f"Invalid tar file: {e}")
            archive.format = 'invalid_tar'

    def _parse_raw_pickle(self, data: bytes, archive: TorchArchive) -> None:
        """Parse as raw pickle data."""
        archive.format = 'raw_pickle'

        try:
            parser = PickleParser(data)
            stream = parser.parse()
            entry = TorchPickleEntry('root.pkl', data, stream)
            archive.pickle_entries.append(entry)
        except Exception as e:
            archive.errors.append(f"Error parsing as raw pickle: {e}")


def parse_torch_file(path: Path) -> TorchArchive:
    """Convenience function to parse a PyTorch file."""
    parser = TorchParser(path=path)
    return parser.parse()


def parse_torch_bytes(data: bytes) -> TorchArchive:
    """Convenience function to parse PyTorch data from bytes."""
    parser = TorchParser(data=data)
    return parser.parse()
