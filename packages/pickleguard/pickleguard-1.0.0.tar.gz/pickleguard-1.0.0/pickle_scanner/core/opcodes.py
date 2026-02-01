"""
Pickle opcode definitions and parsing utilities.

Supports pickle protocols 0-5.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Dict, Tuple, Any


class OpcodeCategory(Enum):
    """Categories of pickle opcodes."""
    STACK = auto()          # Stack manipulation
    MEMO = auto()           # Memo operations
    DATA = auto()           # Push data onto stack
    BUILD = auto()          # Object construction
    GLOBAL = auto()         # Global/module lookups
    REDUCE = auto()         # Function calls
    MARK = auto()           # Mark for tuple/list/dict
    CONTAINER = auto()      # List, dict, set operations
    PROTOCOL = auto()       # Protocol markers
    EXTENSION = auto()      # Extension registry


@dataclass
class OpcodeInfo:
    """Information about a pickle opcode."""
    code: bytes
    name: str
    category: OpcodeCategory
    arg_type: str  # 'none', 'uint1', 'uint2', 'uint4', 'int4', 'uint8', 'float8',
                   # 'string', 'bytes', 'unicode', 'line', 'pair_line', 'decimalnl'
    protocol: int  # Minimum protocol version
    description: str

    @property
    def is_dangerous(self) -> bool:
        """Check if this opcode can lead to code execution."""
        return self.category in (OpcodeCategory.GLOBAL, OpcodeCategory.REDUCE,
                                 OpcodeCategory.EXTENSION, OpcodeCategory.BUILD)


# All pickle opcodes across protocols 0-5
OPCODES = [
    # Protocol 0 (ASCII)
    OpcodeInfo(b'(', 'MARK', OpcodeCategory.MARK, 'none', 0, 'push special markobject on stack'),
    OpcodeInfo(b'.', 'STOP', OpcodeCategory.PROTOCOL, 'none', 0, 'every pickle ends with STOP'),
    OpcodeInfo(b'0', 'POP', OpcodeCategory.STACK, 'none', 0, 'discard topmost stack item'),
    OpcodeInfo(b'1', 'POP_MARK', OpcodeCategory.STACK, 'none', 0, 'discard stack top through topmost markobject'),
    OpcodeInfo(b'2', 'DUP', OpcodeCategory.STACK, 'none', 0, 'duplicate top stack item'),
    OpcodeInfo(b'F', 'FLOAT', OpcodeCategory.DATA, 'decimalnl', 0, 'push float object'),
    OpcodeInfo(b'I', 'INT', OpcodeCategory.DATA, 'decimalnl', 0, 'push integer or bool'),
    OpcodeInfo(b'J', 'BININT', OpcodeCategory.DATA, 'int4', 1, 'push 4-byte signed int'),
    OpcodeInfo(b'K', 'BININT1', OpcodeCategory.DATA, 'uint1', 1, 'push 1-byte unsigned int'),
    OpcodeInfo(b'L', 'LONG', OpcodeCategory.DATA, 'decimalnl', 0, 'push long integer'),
    OpcodeInfo(b'M', 'BININT2', OpcodeCategory.DATA, 'uint2', 1, 'push 2-byte unsigned int'),
    OpcodeInfo(b'N', 'NONE', OpcodeCategory.DATA, 'none', 0, 'push None'),
    OpcodeInfo(b'P', 'PERSID', OpcodeCategory.DATA, 'line', 0, 'push persistent id'),
    OpcodeInfo(b'Q', 'BINPERSID', OpcodeCategory.DATA, 'none', 1, 'push persistent id from stack'),
    OpcodeInfo(b'R', 'REDUCE', OpcodeCategory.REDUCE, 'none', 0, 'apply callable to args'),
    OpcodeInfo(b'S', 'STRING', OpcodeCategory.DATA, 'line', 0, 'push string'),
    OpcodeInfo(b'T', 'BINSTRING', OpcodeCategory.DATA, 'string', 1, 'push string'),
    OpcodeInfo(b'U', 'SHORT_BINSTRING', OpcodeCategory.DATA, 'bytes1', 1, 'push string (<256 bytes)'),
    OpcodeInfo(b'V', 'UNICODE', OpcodeCategory.DATA, 'unicode', 0, 'push Unicode string'),
    OpcodeInfo(b'X', 'BINUNICODE', OpcodeCategory.DATA, 'unicode4', 1, 'push Unicode string'),
    OpcodeInfo(b'a', 'APPEND', OpcodeCategory.CONTAINER, 'none', 0, 'append stack top to list below'),
    OpcodeInfo(b'b', 'BUILD', OpcodeCategory.BUILD, 'none', 0, 'call __setstate__ or __dict__.update()'),
    OpcodeInfo(b'c', 'GLOBAL', OpcodeCategory.GLOBAL, 'pair_line', 0, 'push self.find_class(module, name)'),
    OpcodeInfo(b'd', 'DICT', OpcodeCategory.CONTAINER, 'none', 0, 'build dict from stack items'),
    OpcodeInfo(b'e', 'APPENDS', OpcodeCategory.CONTAINER, 'none', 1, 'extend list on stack by topmost slice'),
    OpcodeInfo(b'g', 'GET', OpcodeCategory.MEMO, 'decimalnl', 0, 'push item from memo'),
    OpcodeInfo(b'h', 'BINGET', OpcodeCategory.MEMO, 'uint1', 1, 'push item from memo (1-byte key)'),
    OpcodeInfo(b'i', 'INST', OpcodeCategory.GLOBAL, 'pair_line', 0, 'build & push class instance'),
    OpcodeInfo(b'j', 'LONG_BINGET', OpcodeCategory.MEMO, 'uint4', 1, 'push item from memo (4-byte key)'),
    OpcodeInfo(b'l', 'LIST', OpcodeCategory.CONTAINER, 'none', 0, 'build list from topmost stack items'),
    OpcodeInfo(b'o', 'OBJ', OpcodeCategory.BUILD, 'none', 1, 'build object from stack'),
    OpcodeInfo(b'p', 'PUT', OpcodeCategory.MEMO, 'decimalnl', 0, 'store stack top in memo'),
    OpcodeInfo(b'q', 'BINPUT', OpcodeCategory.MEMO, 'uint1', 1, 'store stack top in memo (1-byte key)'),
    OpcodeInfo(b'r', 'LONG_BINPUT', OpcodeCategory.MEMO, 'uint4', 1, 'store stack top in memo (4-byte key)'),
    OpcodeInfo(b's', 'SETITEM', OpcodeCategory.CONTAINER, 'none', 0, 'add key/value to dict'),
    OpcodeInfo(b't', 'TUPLE', OpcodeCategory.CONTAINER, 'none', 0, 'build tuple from stack items'),
    OpcodeInfo(b'u', 'SETITEMS', OpcodeCategory.CONTAINER, 'none', 1, 'add key/value pairs to dict'),
    OpcodeInfo(b'}', 'EMPTY_DICT', OpcodeCategory.CONTAINER, 'none', 1, 'push empty dict'),
    OpcodeInfo(b')', 'EMPTY_TUPLE', OpcodeCategory.CONTAINER, 'none', 1, 'push empty tuple'),
    OpcodeInfo(b']', 'EMPTY_LIST', OpcodeCategory.CONTAINER, 'none', 1, 'push empty list'),

    # Protocol 2
    OpcodeInfo(b'\x80', 'PROTO', OpcodeCategory.PROTOCOL, 'uint1', 2, 'identify pickle protocol'),
    OpcodeInfo(b'\x81', 'NEWOBJ', OpcodeCategory.BUILD, 'none', 2, 'build object by calling cls.__new__'),
    OpcodeInfo(b'\x82', 'EXT1', OpcodeCategory.EXTENSION, 'uint1', 2, 'push object from extension registry'),
    OpcodeInfo(b'\x83', 'EXT2', OpcodeCategory.EXTENSION, 'uint2', 2, 'push object from extension registry'),
    OpcodeInfo(b'\x84', 'EXT4', OpcodeCategory.EXTENSION, 'int4', 2, 'push object from extension registry'),
    OpcodeInfo(b'\x85', 'TUPLE1', OpcodeCategory.CONTAINER, 'none', 2, 'build 1-tuple from stack top'),
    OpcodeInfo(b'\x86', 'TUPLE2', OpcodeCategory.CONTAINER, 'none', 2, 'build 2-tuple from stack'),
    OpcodeInfo(b'\x87', 'TUPLE3', OpcodeCategory.CONTAINER, 'none', 2, 'build 3-tuple from stack'),
    OpcodeInfo(b'\x88', 'NEWTRUE', OpcodeCategory.DATA, 'none', 2, 'push True'),
    OpcodeInfo(b'\x89', 'NEWFALSE', OpcodeCategory.DATA, 'none', 2, 'push False'),
    OpcodeInfo(b'\x8a', 'LONG1', OpcodeCategory.DATA, 'long1', 2, 'push long from <256 bytes'),
    OpcodeInfo(b'\x8b', 'LONG4', OpcodeCategory.DATA, 'long4', 2, 'push long from 4-byte length'),

    # Protocol 3
    OpcodeInfo(b'B', 'BINBYTES', OpcodeCategory.DATA, 'bytes4', 3, 'push bytes'),
    OpcodeInfo(b'C', 'SHORT_BINBYTES', OpcodeCategory.DATA, 'bytes1', 3, 'push bytes (<256 bytes)'),

    # Protocol 4
    OpcodeInfo(b'\x8c', 'SHORT_BINUNICODE', OpcodeCategory.DATA, 'bytes1_utf8', 4, 'push short unicode'),
    OpcodeInfo(b'\x8d', 'BINUNICODE8', OpcodeCategory.DATA, 'unicode8', 4, 'push long unicode'),
    OpcodeInfo(b'\x8e', 'BINBYTES8', OpcodeCategory.DATA, 'bytes8', 4, 'push long bytes'),
    OpcodeInfo(b'\x8f', 'EMPTY_SET', OpcodeCategory.CONTAINER, 'none', 4, 'push empty set'),
    OpcodeInfo(b'\x90', 'ADDITEMS', OpcodeCategory.CONTAINER, 'none', 4, 'add items to set'),
    OpcodeInfo(b'\x91', 'FROZENSET', OpcodeCategory.CONTAINER, 'none', 4, 'build frozenset from stack'),
    OpcodeInfo(b'\x92', 'NEWOBJ_EX', OpcodeCategory.BUILD, 'none', 4, 'build object with kwargs'),
    OpcodeInfo(b'\x93', 'STACK_GLOBAL', OpcodeCategory.GLOBAL, 'none', 4, 'push global from stack'),
    OpcodeInfo(b'\x94', 'MEMOIZE', OpcodeCategory.MEMO, 'none', 4, 'store top to memo'),
    OpcodeInfo(b'\x95', 'FRAME', OpcodeCategory.PROTOCOL, 'uint8', 4, 'frame with given size'),

    # Protocol 5
    OpcodeInfo(b'\x96', 'BYTEARRAY8', OpcodeCategory.DATA, 'bytes8', 5, 'push bytearray'),
    OpcodeInfo(b'\x97', 'NEXT_BUFFER', OpcodeCategory.DATA, 'none', 5, 'push next out-of-band buffer'),
    OpcodeInfo(b'\x98', 'READONLY_BUFFER', OpcodeCategory.DATA, 'none', 5, 'make buffer read-only'),
]

# Build lookup maps
OPCODE_MAP: Dict[bytes, OpcodeInfo] = {op.code: op for op in OPCODES}
OPCODE_BY_NAME: Dict[str, OpcodeInfo] = {op.name: op for op in OPCODES}


def get_opcode(code: bytes) -> Optional[OpcodeInfo]:
    """Get opcode info by code byte."""
    return OPCODE_MAP.get(code)


def get_opcode_by_name(name: str) -> Optional[OpcodeInfo]:
    """Get opcode info by name."""
    return OPCODE_BY_NAME.get(name)


@dataclass
class ParsedOpcode:
    """A parsed opcode with its arguments."""
    info: OpcodeInfo
    position: int
    arg: Any = None
    raw_bytes: bytes = b''

    @property
    def name(self) -> str:
        return self.info.name

    @property
    def category(self) -> OpcodeCategory:
        return self.info.category


# Dangerous opcode combinations
DANGEROUS_PATTERNS = [
    # GLOBAL followed by REDUCE = function call
    ('GLOBAL', 'REDUCE'),
    ('STACK_GLOBAL', 'REDUCE'),
    # INST is self-contained dangerous opcode
    ('INST',),
    # OBJ can also call constructors
    ('OBJ',),
    # NEWOBJ variations
    ('NEWOBJ',),
    ('NEWOBJ_EX',),
    # BUILD can invoke __setstate__
    ('BUILD',),
    # Extension registry abuse
    ('EXT1',),
    ('EXT2',),
    ('EXT4',),
]
