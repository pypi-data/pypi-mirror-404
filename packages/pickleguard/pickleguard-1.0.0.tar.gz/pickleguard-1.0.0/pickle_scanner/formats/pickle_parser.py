"""
Pickle stream parser for security analysis.

Parses pickle streams without executing them, extracting opcodes and arguments.
"""

import struct
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Iterator, BinaryIO, Any
import io
import codecs

from pickle_scanner.core.opcodes import (
    ParsedOpcode,
    OpcodeInfo,
    OPCODE_MAP,
    get_opcode,
)


@dataclass
class PickleStream:
    """Represents a parsed pickle stream."""
    data: bytes
    protocol: int = 0
    opcodes: List[ParsedOpcode] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.data)


class PickleParser:
    """Parser for pickle byte streams."""

    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.protocol = 0
        self.errors: List[str] = []

    def parse(self) -> PickleStream:
        """Parse the pickle stream and return structured data."""
        stream = PickleStream(self.data)
        self.pos = 0

        while self.pos < len(self.data):
            try:
                opcode = self._read_opcode()
                if opcode:
                    stream.opcodes.append(opcode)
                    if opcode.name == 'PROTO':
                        stream.protocol = opcode.arg if opcode.arg is not None else 0
                        self.protocol = stream.protocol
                    if opcode.name == 'STOP':
                        break
                else:
                    # Unknown opcode, try to skip
                    self.errors.append(f"Unknown opcode at position {self.pos}: {self.data[self.pos:self.pos+1]!r}")
                    self.pos += 1
            except Exception as e:
                self.errors.append(f"Parse error at position {self.pos}: {e}")
                self.pos += 1

        stream.errors = self.errors
        return stream

    def _read_opcode(self) -> Optional[ParsedOpcode]:
        """Read a single opcode and its arguments."""
        if self.pos >= len(self.data):
            return None

        start_pos = self.pos
        code = self.data[self.pos:self.pos+1]
        self.pos += 1

        info = get_opcode(code)
        if not info:
            self.pos = start_pos
            return None

        arg = self._read_argument(info)
        raw_bytes = self.data[start_pos:self.pos]

        return ParsedOpcode(info, start_pos, arg, raw_bytes)

    def _read_argument(self, info: OpcodeInfo) -> Any:
        """Read the argument for an opcode based on its type."""
        arg_type = info.arg_type

        if arg_type == 'none':
            return None

        elif arg_type == 'uint1':
            return self._read_uint(1)

        elif arg_type == 'uint2':
            return self._read_uint(2)

        elif arg_type == 'uint4':
            return self._read_uint(4)

        elif arg_type == 'int4':
            return self._read_int(4)

        elif arg_type == 'uint8':
            return self._read_uint(8)

        elif arg_type == 'float8':
            return self._read_float8()

        elif arg_type == 'decimalnl':
            return self._read_decimalnl()

        elif arg_type == 'line':
            return self._read_line()

        elif arg_type == 'pair_line':
            return self._read_pair_line()

        elif arg_type == 'string':
            return self._read_string4()

        elif arg_type == 'bytes1':
            return self._read_bytes1()

        elif arg_type == 'bytes1_utf8':
            return self._read_bytes1_utf8()

        elif arg_type == 'bytes4':
            return self._read_bytes4()

        elif arg_type == 'bytes8':
            return self._read_bytes8()

        elif arg_type == 'unicode':
            return self._read_unicode_line()

        elif arg_type == 'unicode4':
            return self._read_unicode4()

        elif arg_type == 'unicode8':
            return self._read_unicode8()

        elif arg_type == 'long1':
            return self._read_long1()

        elif arg_type == 'long4':
            return self._read_long4()

        else:
            self.errors.append(f"Unknown argument type: {arg_type}")
            return None

    def _read_uint(self, size: int) -> int:
        """Read unsigned integer."""
        if self.pos + size > len(self.data):
            raise ValueError(f"Not enough data for uint{size*8}")

        data = self.data[self.pos:self.pos+size]
        self.pos += size

        if size == 1:
            return data[0]
        elif size == 2:
            return struct.unpack('<H', data)[0]
        elif size == 4:
            return struct.unpack('<I', data)[0]
        elif size == 8:
            return struct.unpack('<Q', data)[0]
        else:
            return int.from_bytes(data, 'little', signed=False)

    def _read_int(self, size: int) -> int:
        """Read signed integer."""
        if self.pos + size > len(self.data):
            raise ValueError(f"Not enough data for int{size*8}")

        data = self.data[self.pos:self.pos+size]
        self.pos += size

        if size == 4:
            return struct.unpack('<i', data)[0]
        else:
            return int.from_bytes(data, 'little', signed=True)

    def _read_float8(self) -> float:
        """Read 8-byte float (big-endian for pickle)."""
        if self.pos + 8 > len(self.data):
            raise ValueError("Not enough data for float8")

        data = self.data[self.pos:self.pos+8]
        self.pos += 8
        return struct.unpack('>d', data)[0]

    def _read_decimalnl(self) -> str:
        """Read a decimal newline-terminated string."""
        return self._read_line()

    def _read_line(self) -> str:
        """Read a newline-terminated line."""
        end = self.data.find(b'\n', self.pos)
        if end == -1:
            # No newline found, read to end
            line = self.data[self.pos:]
            self.pos = len(self.data)
        else:
            line = self.data[self.pos:end]
            self.pos = end + 1

        try:
            return line.decode('utf-8', errors='replace')
        except:
            return line.decode('latin-1', errors='replace')

    def _read_pair_line(self) -> Tuple[str, str]:
        """Read two newline-terminated lines (for GLOBAL, INST)."""
        module = self._read_line()
        name = self._read_line()
        return (module, name)

    def _read_string4(self) -> str:
        """Read a 4-byte length-prefixed string (BINSTRING)."""
        length = self._read_uint(4)
        if self.pos + length > len(self.data):
            raise ValueError(f"String length {length} exceeds data")

        data = self.data[self.pos:self.pos+length]
        self.pos += length

        # BINSTRING uses Latin-1 encoding
        return data.decode('latin-1', errors='replace')

    def _read_bytes1(self) -> bytes:
        """Read 1-byte length-prefixed bytes."""
        length = self._read_uint(1)
        if self.pos + length > len(self.data):
            raise ValueError(f"Bytes length {length} exceeds data")

        data = self.data[self.pos:self.pos+length]
        self.pos += length
        return data

    def _read_bytes1_utf8(self) -> str:
        """Read 1-byte length-prefixed UTF-8 string."""
        data = self._read_bytes1()
        return data.decode('utf-8', errors='replace')

    def _read_bytes4(self) -> bytes:
        """Read 4-byte length-prefixed bytes."""
        length = self._read_uint(4)
        if self.pos + length > len(self.data):
            raise ValueError(f"Bytes length {length} exceeds data")

        data = self.data[self.pos:self.pos+length]
        self.pos += length
        return data

    def _read_bytes8(self) -> bytes:
        """Read 8-byte length-prefixed bytes."""
        length = self._read_uint(8)
        if self.pos + length > len(self.data):
            raise ValueError(f"Bytes length {length} exceeds data")

        data = self.data[self.pos:self.pos+length]
        self.pos += length
        return data

    def _read_unicode_line(self) -> str:
        """Read raw-unicode-escaped newline-terminated string."""
        line = self._read_line()
        try:
            # Protocol 0 UNICODE uses raw-unicode-escape
            return codecs.decode(line, 'raw_unicode_escape')
        except:
            return line

    def _read_unicode4(self) -> str:
        """Read 4-byte length-prefixed UTF-8 string."""
        length = self._read_uint(4)
        if self.pos + length > len(self.data):
            raise ValueError(f"Unicode length {length} exceeds data")

        data = self.data[self.pos:self.pos+length]
        self.pos += length
        return data.decode('utf-8', errors='replace')

    def _read_unicode8(self) -> str:
        """Read 8-byte length-prefixed UTF-8 string."""
        length = self._read_uint(8)
        if self.pos + length > len(self.data):
            raise ValueError(f"Unicode length {length} exceeds data")

        data = self.data[self.pos:self.pos+length]
        self.pos += length
        return data.decode('utf-8', errors='replace')

    def _read_long1(self) -> int:
        """Read a LONG1 (1-byte length, then bytes for long)."""
        length = self._read_uint(1)
        if length == 0:
            return 0

        if self.pos + length > len(self.data):
            raise ValueError(f"Long length {length} exceeds data")

        data = self.data[self.pos:self.pos+length]
        self.pos += length
        return int.from_bytes(data, 'little', signed=True)

    def _read_long4(self) -> int:
        """Read a LONG4 (4-byte length, then bytes for long)."""
        length = self._read_int(4)  # Signed!
        if length < 0:
            raise ValueError(f"Negative long length: {length}")
        if length == 0:
            return 0

        if self.pos + length > len(self.data):
            raise ValueError(f"Long length {length} exceeds data")

        data = self.data[self.pos:self.pos+length]
        self.pos += length
        return int.from_bytes(data, 'little', signed=True)


def parse_pickle(data: bytes) -> PickleStream:
    """Convenience function to parse pickle data."""
    parser = PickleParser(data)
    return parser.parse()


def iter_opcodes(data: bytes) -> Iterator[ParsedOpcode]:
    """Iterate over opcodes in a pickle stream."""
    stream = parse_pickle(data)
    yield from stream.opcodes
