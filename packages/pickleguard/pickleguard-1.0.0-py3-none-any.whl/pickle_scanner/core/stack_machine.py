"""
Abstract stack machine interpreter for pickle analysis.

Simulates pickle unpickling without actually executing dangerous operations.
Tracks data flow and identifies dangerous callable invocations.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum, auto

from pickle_scanner.core.opcodes import ParsedOpcode, OpcodeCategory


class ItemType(Enum):
    """Types of items on the abstract stack."""
    UNKNOWN = auto()
    NONE = auto()
    BOOL = auto()
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    BYTES = auto()
    LIST = auto()
    TUPLE = auto()
    DICT = auto()
    SET = auto()
    FROZENSET = auto()
    MARK = auto()
    GLOBAL = auto()         # A global reference (module.name)
    REDUCED = auto()        # Result of REDUCE operation
    BUILT = auto()          # Result of BUILD operation
    PERSID = auto()         # Persistent ID


@dataclass
class GlobalRef:
    """Reference to a global (module.name)."""
    module: str
    name: str
    opcode: str = "GLOBAL"  # GLOBAL, STACK_GLOBAL, or INST

    def __str__(self) -> str:
        return f"{self.module}.{self.name}"

    @property
    def full_path(self) -> str:
        return f"{self.module}.{self.name}"


@dataclass
class ReduceCall:
    """Represents a REDUCE call (callable invocation)."""
    callable_ref: Optional[GlobalRef]
    args: Any
    position: int


@dataclass
class BuildCall:
    """Represents a BUILD operation."""
    obj: Any
    state: Any
    position: int


@dataclass
class StackItem:
    """An item on the abstract stack."""
    item_type: ItemType
    value: Any = None
    position: int = 0  # Opcode position that created this
    source_opcode: str = ""

    @classmethod
    def mark(cls, position: int = 0) -> 'StackItem':
        return cls(ItemType.MARK, None, position, "MARK")

    @classmethod
    def none(cls, position: int = 0) -> 'StackItem':
        return cls(ItemType.NONE, None, position, "NONE")

    @classmethod
    def bool_val(cls, value: bool, position: int = 0) -> 'StackItem':
        return cls(ItemType.BOOL, value, position, "NEWTRUE" if value else "NEWFALSE")

    @classmethod
    def int_val(cls, value: int, position: int = 0, opcode: str = "INT") -> 'StackItem':
        return cls(ItemType.INT, value, position, opcode)

    @classmethod
    def float_val(cls, value: float, position: int = 0) -> 'StackItem':
        return cls(ItemType.FLOAT, value, position, "FLOAT")

    @classmethod
    def string(cls, value: str, position: int = 0, opcode: str = "STRING") -> 'StackItem':
        return cls(ItemType.STRING, value, position, opcode)

    @classmethod
    def bytes_val(cls, value: bytes, position: int = 0, opcode: str = "BINBYTES") -> 'StackItem':
        return cls(ItemType.BYTES, value, position, opcode)

    @classmethod
    def list_val(cls, items: list, position: int = 0) -> 'StackItem':
        return cls(ItemType.LIST, items, position, "LIST")

    @classmethod
    def tuple_val(cls, items: tuple, position: int = 0) -> 'StackItem':
        return cls(ItemType.TUPLE, items, position, "TUPLE")

    @classmethod
    def dict_val(cls, items: dict, position: int = 0) -> 'StackItem':
        return cls(ItemType.DICT, items, position, "DICT")

    @classmethod
    def global_ref(cls, ref: GlobalRef, position: int = 0) -> 'StackItem':
        return cls(ItemType.GLOBAL, ref, position, ref.opcode)

    @classmethod
    def reduced(cls, call: ReduceCall, position: int = 0) -> 'StackItem':
        return cls(ItemType.REDUCED, call, position, "REDUCE")

    @classmethod
    def built(cls, call: BuildCall, position: int = 0) -> 'StackItem':
        return cls(ItemType.BUILT, call, position, "BUILD")

    @classmethod
    def unknown(cls, position: int = 0, opcode: str = "") -> 'StackItem':
        return cls(ItemType.UNKNOWN, None, position, opcode)


@dataclass
class StackMachine:
    """Abstract pickle stack machine for static analysis."""
    stack: List[StackItem] = field(default_factory=list)
    memo: Dict[int, StackItem] = field(default_factory=dict)
    metastack: List[List[StackItem]] = field(default_factory=list)
    protocol: int = 0

    # Analysis results
    globals_found: List[Tuple[GlobalRef, int]] = field(default_factory=list)
    reduce_calls: List[ReduceCall] = field(default_factory=list)
    build_calls: List[BuildCall] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def push(self, item: StackItem) -> None:
        """Push an item onto the stack."""
        self.stack.append(item)

    def pop(self) -> StackItem:
        """Pop an item from the stack."""
        if not self.stack:
            self.errors.append("Stack underflow")
            return StackItem.unknown()
        return self.stack.pop()

    def peek(self) -> StackItem:
        """Peek at the top of the stack."""
        if not self.stack:
            return StackItem.unknown()
        return self.stack[-1]

    def pop_mark(self) -> List[StackItem]:
        """Pop all items above the topmost mark."""
        items = []
        while self.stack:
            item = self.stack.pop()
            if item.item_type == ItemType.MARK:
                return list(reversed(items))
            items.append(item)
        self.errors.append("No mark found on stack")
        return list(reversed(items))

    def find_mark(self) -> int:
        """Find the position of the topmost mark."""
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i].item_type == ItemType.MARK:
                return i
        return -1

    def process_opcode(self, opcode: ParsedOpcode) -> None:
        """Process a single opcode."""
        handler = getattr(self, f'_op_{opcode.name}', None)
        if handler:
            try:
                handler(opcode)
            except Exception as e:
                self.errors.append(f"Error processing {opcode.name} at {opcode.position}: {e}")
        else:
            self._op_unknown(opcode)

    # Protocol markers
    def _op_PROTO(self, op: ParsedOpcode) -> None:
        self.protocol = op.arg if op.arg is not None else 0

    def _op_FRAME(self, op: ParsedOpcode) -> None:
        pass  # Frame hints, ignore

    def _op_STOP(self, op: ParsedOpcode) -> None:
        pass  # End of pickle

    # Stack manipulation
    def _op_MARK(self, op: ParsedOpcode) -> None:
        self.push(StackItem.mark(op.position))

    def _op_POP(self, op: ParsedOpcode) -> None:
        self.pop()

    def _op_POP_MARK(self, op: ParsedOpcode) -> None:
        self.pop_mark()

    def _op_DUP(self, op: ParsedOpcode) -> None:
        if self.stack:
            self.push(self.stack[-1])

    # Memo operations
    def _op_PUT(self, op: ParsedOpcode) -> None:
        if self.stack:
            idx = int(op.arg) if op.arg is not None else 0
            self.memo[idx] = self.stack[-1]

    def _op_BINPUT(self, op: ParsedOpcode) -> None:
        self._op_PUT(op)

    def _op_LONG_BINPUT(self, op: ParsedOpcode) -> None:
        self._op_PUT(op)

    def _op_MEMOIZE(self, op: ParsedOpcode) -> None:
        if self.stack:
            self.memo[len(self.memo)] = self.stack[-1]

    def _op_GET(self, op: ParsedOpcode) -> None:
        idx = int(op.arg) if op.arg is not None else 0
        if idx in self.memo:
            self.push(self.memo[idx])
        else:
            self.push(StackItem.unknown(op.position, "GET"))

    def _op_BINGET(self, op: ParsedOpcode) -> None:
        self._op_GET(op)

    def _op_LONG_BINGET(self, op: ParsedOpcode) -> None:
        self._op_GET(op)

    # Data push operations
    def _op_NONE(self, op: ParsedOpcode) -> None:
        self.push(StackItem.none(op.position))

    def _op_NEWTRUE(self, op: ParsedOpcode) -> None:
        self.push(StackItem.bool_val(True, op.position))

    def _op_NEWFALSE(self, op: ParsedOpcode) -> None:
        self.push(StackItem.bool_val(False, op.position))

    def _op_INT(self, op: ParsedOpcode) -> None:
        try:
            val = int(op.arg) if op.arg is not None else 0
        except (ValueError, TypeError):
            val = 0
        self.push(StackItem.int_val(val, op.position, "INT"))

    def _op_BININT(self, op: ParsedOpcode) -> None:
        val = op.arg if isinstance(op.arg, int) else 0
        self.push(StackItem.int_val(val, op.position, "BININT"))

    def _op_BININT1(self, op: ParsedOpcode) -> None:
        val = op.arg if isinstance(op.arg, int) else 0
        self.push(StackItem.int_val(val, op.position, "BININT1"))

    def _op_BININT2(self, op: ParsedOpcode) -> None:
        val = op.arg if isinstance(op.arg, int) else 0
        self.push(StackItem.int_val(val, op.position, "BININT2"))

    def _op_LONG(self, op: ParsedOpcode) -> None:
        try:
            val = int(op.arg) if op.arg is not None else 0
        except (ValueError, TypeError):
            val = 0
        self.push(StackItem.int_val(val, op.position, "LONG"))

    def _op_LONG1(self, op: ParsedOpcode) -> None:
        val = op.arg if isinstance(op.arg, int) else 0
        self.push(StackItem.int_val(val, op.position, "LONG1"))

    def _op_LONG4(self, op: ParsedOpcode) -> None:
        val = op.arg if isinstance(op.arg, int) else 0
        self.push(StackItem.int_val(val, op.position, "LONG4"))

    def _op_FLOAT(self, op: ParsedOpcode) -> None:
        try:
            val = float(op.arg) if op.arg is not None else 0.0
        except (ValueError, TypeError):
            val = 0.0
        self.push(StackItem.float_val(val, op.position))

    def _op_BINFLOAT(self, op: ParsedOpcode) -> None:
        val = op.arg if isinstance(op.arg, float) else 0.0
        self.push(StackItem.float_val(val, op.position))

    def _op_STRING(self, op: ParsedOpcode) -> None:
        val = op.arg if isinstance(op.arg, str) else str(op.arg) if op.arg else ""
        self.push(StackItem.string(val, op.position, "STRING"))

    def _op_BINSTRING(self, op: ParsedOpcode) -> None:
        val = op.arg if isinstance(op.arg, str) else str(op.arg) if op.arg else ""
        self.push(StackItem.string(val, op.position, "BINSTRING"))

    def _op_SHORT_BINSTRING(self, op: ParsedOpcode) -> None:
        val = op.arg if isinstance(op.arg, str) else str(op.arg) if op.arg else ""
        self.push(StackItem.string(val, op.position, "SHORT_BINSTRING"))

    def _op_UNICODE(self, op: ParsedOpcode) -> None:
        val = op.arg if isinstance(op.arg, str) else str(op.arg) if op.arg else ""
        self.push(StackItem.string(val, op.position, "UNICODE"))

    def _op_BINUNICODE(self, op: ParsedOpcode) -> None:
        val = op.arg if isinstance(op.arg, str) else str(op.arg) if op.arg else ""
        self.push(StackItem.string(val, op.position, "BINUNICODE"))

    def _op_SHORT_BINUNICODE(self, op: ParsedOpcode) -> None:
        val = op.arg if isinstance(op.arg, str) else str(op.arg) if op.arg else ""
        self.push(StackItem.string(val, op.position, "SHORT_BINUNICODE"))

    def _op_BINUNICODE8(self, op: ParsedOpcode) -> None:
        val = op.arg if isinstance(op.arg, str) else str(op.arg) if op.arg else ""
        self.push(StackItem.string(val, op.position, "BINUNICODE8"))

    def _op_BINBYTES(self, op: ParsedOpcode) -> None:
        val = op.arg if isinstance(op.arg, bytes) else bytes(op.arg) if op.arg else b""
        self.push(StackItem.bytes_val(val, op.position, "BINBYTES"))

    def _op_SHORT_BINBYTES(self, op: ParsedOpcode) -> None:
        val = op.arg if isinstance(op.arg, bytes) else bytes(op.arg) if op.arg else b""
        self.push(StackItem.bytes_val(val, op.position, "SHORT_BINBYTES"))

    def _op_BINBYTES8(self, op: ParsedOpcode) -> None:
        val = op.arg if isinstance(op.arg, bytes) else bytes(op.arg) if op.arg else b""
        self.push(StackItem.bytes_val(val, op.position, "BINBYTES8"))

    def _op_BYTEARRAY8(self, op: ParsedOpcode) -> None:
        val = op.arg if isinstance(op.arg, bytes) else bytes(op.arg) if op.arg else b""
        self.push(StackItem.bytes_val(val, op.position, "BYTEARRAY8"))

    def _op_NEXT_BUFFER(self, op: ParsedOpcode) -> None:
        self.push(StackItem.unknown(op.position, "NEXT_BUFFER"))

    def _op_READONLY_BUFFER(self, op: ParsedOpcode) -> None:
        pass  # Modifies top of stack, but doesn't change type

    # Container operations
    def _op_EMPTY_LIST(self, op: ParsedOpcode) -> None:
        self.push(StackItem.list_val([], op.position))

    def _op_EMPTY_TUPLE(self, op: ParsedOpcode) -> None:
        self.push(StackItem.tuple_val((), op.position))

    def _op_EMPTY_DICT(self, op: ParsedOpcode) -> None:
        self.push(StackItem.dict_val({}, op.position))

    def _op_EMPTY_SET(self, op: ParsedOpcode) -> None:
        self.push(StackItem(ItemType.SET, set(), op.position, "EMPTY_SET"))

    def _op_LIST(self, op: ParsedOpcode) -> None:
        items = self.pop_mark()
        self.push(StackItem.list_val([i.value for i in items], op.position))

    def _op_TUPLE(self, op: ParsedOpcode) -> None:
        items = self.pop_mark()
        self.push(StackItem.tuple_val(tuple(i.value for i in items), op.position))

    def _op_TUPLE1(self, op: ParsedOpcode) -> None:
        item = self.pop()
        self.push(StackItem.tuple_val((item.value,), op.position))

    def _op_TUPLE2(self, op: ParsedOpcode) -> None:
        b = self.pop()
        a = self.pop()
        self.push(StackItem.tuple_val((a.value, b.value), op.position))

    def _op_TUPLE3(self, op: ParsedOpcode) -> None:
        c = self.pop()
        b = self.pop()
        a = self.pop()
        self.push(StackItem.tuple_val((a.value, b.value, c.value), op.position))

    def _op_DICT(self, op: ParsedOpcode) -> None:
        items = self.pop_mark()
        d = {}
        for i in range(0, len(items), 2):
            if i + 1 < len(items):
                key = items[i].value
                val = items[i + 1].value
                if key is not None:
                    d[key] = val
        self.push(StackItem.dict_val(d, op.position))

    def _op_FROZENSET(self, op: ParsedOpcode) -> None:
        items = self.pop_mark()
        self.push(StackItem(ItemType.FROZENSET, frozenset(i.value for i in items), op.position, "FROZENSET"))

    def _op_APPEND(self, op: ParsedOpcode) -> None:
        item = self.pop()
        if self.stack and self.stack[-1].item_type == ItemType.LIST:
            if isinstance(self.stack[-1].value, list):
                self.stack[-1].value.append(item.value)

    def _op_APPENDS(self, op: ParsedOpcode) -> None:
        items = self.pop_mark()
        if self.stack and self.stack[-1].item_type == ItemType.LIST:
            if isinstance(self.stack[-1].value, list):
                self.stack[-1].value.extend(i.value for i in items)

    def _op_SETITEM(self, op: ParsedOpcode) -> None:
        value = self.pop()
        key = self.pop()
        if self.stack and self.stack[-1].item_type == ItemType.DICT:
            if isinstance(self.stack[-1].value, dict) and key.value is not None:
                self.stack[-1].value[key.value] = value.value

    def _op_SETITEMS(self, op: ParsedOpcode) -> None:
        items = self.pop_mark()
        if self.stack and self.stack[-1].item_type == ItemType.DICT:
            d = self.stack[-1].value
            if isinstance(d, dict):
                for i in range(0, len(items), 2):
                    if i + 1 < len(items):
                        key = items[i].value
                        val = items[i + 1].value
                        if key is not None:
                            d[key] = val

    def _op_ADDITEMS(self, op: ParsedOpcode) -> None:
        items = self.pop_mark()
        if self.stack and self.stack[-1].item_type == ItemType.SET:
            if isinstance(self.stack[-1].value, set):
                self.stack[-1].value.update(i.value for i in items)

    # Global lookups (CRITICAL for security analysis)
    def _op_GLOBAL(self, op: ParsedOpcode) -> None:
        if isinstance(op.arg, tuple) and len(op.arg) == 2:
            module, name = op.arg
        elif isinstance(op.arg, str) and '\n' in op.arg:
            parts = op.arg.split('\n')
            module, name = parts[0], parts[1] if len(parts) > 1 else ""
        else:
            module, name = str(op.arg), ""

        ref = GlobalRef(module, name, "GLOBAL")
        self.globals_found.append((ref, op.position))
        self.push(StackItem.global_ref(ref, op.position))

    def _op_STACK_GLOBAL(self, op: ParsedOpcode) -> None:
        name_item = self.pop()
        module_item = self.pop()

        module = str(module_item.value) if module_item.value else ""
        name = str(name_item.value) if name_item.value else ""

        ref = GlobalRef(module, name, "STACK_GLOBAL")
        self.globals_found.append((ref, op.position))
        self.push(StackItem.global_ref(ref, op.position))

    def _op_INST(self, op: ParsedOpcode) -> None:
        """INST opcode - deprecated but still dangerous.

        INST module name
        Creates an instance by calling module.name(*args)
        where args are popped from the stack up to the mark.
        """
        if isinstance(op.arg, tuple) and len(op.arg) == 2:
            module, name = op.arg
        elif isinstance(op.arg, str) and '\n' in op.arg:
            parts = op.arg.split('\n')
            module, name = parts[0], parts[1] if len(parts) > 1 else ""
        else:
            module, name = str(op.arg), ""

        args = self.pop_mark()

        ref = GlobalRef(module, name, "INST")
        self.globals_found.append((ref, op.position))

        # INST is essentially a GLOBAL + REDUCE in one
        call = ReduceCall(ref, tuple(a.value for a in args), op.position)
        self.reduce_calls.append(call)
        self.push(StackItem.reduced(call, op.position))

    # REDUCE - function call (CRITICAL for security)
    def _op_REDUCE(self, op: ParsedOpcode) -> None:
        args = self.pop()
        callable_item = self.pop()

        callable_ref = None
        if callable_item.item_type == ItemType.GLOBAL:
            callable_ref = callable_item.value

        call = ReduceCall(callable_ref, args.value, op.position)
        self.reduce_calls.append(call)
        self.push(StackItem.reduced(call, op.position))

    # Object construction
    def _op_OBJ(self, op: ParsedOpcode) -> None:
        items = self.pop_mark()
        if items:
            cls_item = items[0]
            args = items[1:]
            if cls_item.item_type == ItemType.GLOBAL:
                ref = cls_item.value
                call = ReduceCall(ref, tuple(a.value for a in args), op.position)
                self.reduce_calls.append(call)
                self.push(StackItem.reduced(call, op.position))
            else:
                self.push(StackItem.unknown(op.position, "OBJ"))
        else:
            self.push(StackItem.unknown(op.position, "OBJ"))

    def _op_NEWOBJ(self, op: ParsedOpcode) -> None:
        args = self.pop()
        cls_item = self.pop()

        if cls_item.item_type == ItemType.GLOBAL:
            ref = cls_item.value
            call = ReduceCall(ref, args.value, op.position)
            self.reduce_calls.append(call)
            self.push(StackItem.reduced(call, op.position))
        else:
            self.push(StackItem.unknown(op.position, "NEWOBJ"))

    def _op_NEWOBJ_EX(self, op: ParsedOpcode) -> None:
        kwargs = self.pop()
        args = self.pop()
        cls_item = self.pop()

        if cls_item.item_type == ItemType.GLOBAL:
            ref = cls_item.value
            call = ReduceCall(ref, (args.value, kwargs.value), op.position)
            self.reduce_calls.append(call)
            self.push(StackItem.reduced(call, op.position))
        else:
            self.push(StackItem.unknown(op.position, "NEWOBJ_EX"))

    def _op_BUILD(self, op: ParsedOpcode) -> None:
        state = self.pop()
        obj = self.pop()

        call = BuildCall(obj, state.value, op.position)
        self.build_calls.append(call)
        self.push(StackItem.built(call, op.position))

    # Extension registry
    def _op_EXT1(self, op: ParsedOpcode) -> None:
        self.push(StackItem.unknown(op.position, "EXT1"))

    def _op_EXT2(self, op: ParsedOpcode) -> None:
        self.push(StackItem.unknown(op.position, "EXT2"))

    def _op_EXT4(self, op: ParsedOpcode) -> None:
        self.push(StackItem.unknown(op.position, "EXT4"))

    # Persistent IDs
    def _op_PERSID(self, op: ParsedOpcode) -> None:
        self.push(StackItem(ItemType.PERSID, op.arg, op.position, "PERSID"))

    def _op_BINPERSID(self, op: ParsedOpcode) -> None:
        pid = self.pop()
        self.push(StackItem(ItemType.PERSID, pid.value, op.position, "BINPERSID"))

    def _op_unknown(self, op: ParsedOpcode) -> None:
        """Handle unknown opcodes."""
        self.errors.append(f"Unknown opcode: {op.name} at position {op.position}")
        self.push(StackItem.unknown(op.position, op.name))
