"""
Obfuscation detection for pickle streams.

Detects various techniques used to evade pickle security scanners.
"""

import math
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Set, Tuple

from pickle_scanner.core.opcodes import ParsedOpcode, OpcodeCategory
from pickle_scanner.core.stack_machine import GlobalRef, StackMachine


class ObfuscationTechnique(Enum):
    """Known obfuscation techniques."""
    INST_OPCODE = auto()            # Using deprecated INST instead of GLOBAL+REDUCE
    NESTED_MODULE_PATH = auto()      # torch.serialization.os.system
    STACK_GLOBAL_DYNAMIC = auto()    # STACK_GLOBAL with computed names
    BUILD_ATTRIBUTE_INJECTION = auto()  # Using BUILD to set __reduce__
    EXTENSION_REGISTRY = auto()      # EXT1/2/4 abuse
    ENCODED_PAYLOAD = auto()         # High-entropy strings (base64, etc.)
    MODULE_ALIASING = auto()         # Import dangerous module under safe name
    ATTRIBUTE_CHAIN = auto()         # __class__.__bases__[0].__subclasses__
    UNICODE_HOMOGLYPH = auto()       # Using lookalike Unicode characters
    SPLIT_PAYLOAD = auto()           # Payload split across multiple strings
    PROTO0_EVASION = auto()          # Using protocol 0 to avoid binary detection


@dataclass
class ObfuscationFinding:
    """A detected obfuscation technique."""
    technique: ObfuscationTechnique
    position: int
    description: str
    severity: int  # 0-30 penalty points
    evidence: str = ""


# Dangerous module segments in nested paths
DANGEROUS_SEGMENTS = {
    'os', 'subprocess', 'builtins', '__builtin__', 'importlib',
    'runpy', 'code', 'pty', 'commands', 'socket', 'ctypes',
    'marshal', 'pickle', '_pickle', 'cPickle', 'sys', 'types',
    'shutil', 'tempfile', 'multiprocessing', 'threading',
}

# Dangerous attribute names
DANGEROUS_ATTRS = {
    '__reduce__', '__reduce_ex__', '__class__', '__bases__',
    '__subclasses__', '__mro__', '__globals__', '__builtins__',
    '__code__', '__call__', '__init__', '__new__', '__getattr__',
    '__setattr__', '__delattr__', '__import__',
}


class ObfuscationDetector:
    """Detects obfuscation techniques in pickle streams."""

    def __init__(self):
        self.findings: List[ObfuscationFinding] = []

    def analyze(
        self,
        opcodes: List[ParsedOpcode],
        machine: Optional[StackMachine] = None
    ) -> List[ObfuscationFinding]:
        """Analyze opcodes for obfuscation techniques."""
        self.findings = []

        self._check_inst_usage(opcodes)
        self._check_nested_module_paths(opcodes, machine)
        self._check_stack_global_dynamic(opcodes, machine)
        self._check_build_injection(opcodes, machine)
        self._check_extension_registry(opcodes)
        self._check_encoded_payloads(opcodes)
        self._check_attribute_chains(opcodes, machine)
        self._check_unicode_homoglyphs(opcodes)
        self._check_proto0_evasion(opcodes)

        return self.findings

    def _check_inst_usage(self, opcodes: List[ParsedOpcode]) -> None:
        """Check for INST opcode usage (deprecated but bypasses some scanners)."""
        for op in opcodes:
            if op.name == 'INST':
                self.findings.append(ObfuscationFinding(
                    technique=ObfuscationTechnique.INST_OPCODE,
                    position=op.position,
                    description="Uses deprecated INST opcode which bypasses GLOBAL+REDUCE detection",
                    severity=20,
                    evidence=f"INST {op.arg}"
                ))

    def _check_nested_module_paths(
        self,
        opcodes: List[ParsedOpcode],
        machine: Optional[StackMachine]
    ) -> None:
        """Check for nested module paths like torch.serialization.os.system."""
        # Safe built-in types that are commonly used in pickle reconstruction
        safe_builtins = {
            'set', 'frozenset', 'list', 'dict', 'tuple', 'str', 'bytes', 'bytearray',
            'int', 'float', 'complex', 'bool', 'type', 'object', 'slice', 'range',
            'map', 'filter', 'zip', 'enumerate', 'reversed', 'sorted',
            'property', 'classmethod', 'staticmethod', 'super',
            # Python 2 compatibility types
            'long', 'unicode', 'basestring', 'xrange', 'buffer', 'file',
            # Safe built-in functions for object manipulation
            'getattr', 'hasattr', 'isinstance', 'issubclass', 'len', 'repr', 'hash',
            'id', 'dir', 'callable', 'iter', 'next', 'all', 'any', 'min', 'max', 'sum',
            'abs', 'round', 'pow', 'divmod', 'ord', 'chr', 'bin', 'hex', 'oct', 'format',
        }

        globals_to_check = []

        # Get globals from machine if available
        if machine:
            globals_to_check.extend(machine.globals_found)
        else:
            # Extract from opcodes directly
            for op in opcodes:
                if op.name in ('GLOBAL', 'INST'):
                    if isinstance(op.arg, tuple) and len(op.arg) == 2:
                        module, name = op.arg
                        globals_to_check.append((GlobalRef(module, name, op.name), op.position))

        for ref, pos in globals_to_check:
            # Skip safe builtin accesses like __builtin__.set
            if ref.module in ('builtins', '__builtin__', '__builtins__') and ref.name in safe_builtins:
                continue

            # Check module path
            module_parts = ref.module.split('.')
            is_safe_builtin = False
            for part in module_parts:
                if part.lower() in DANGEROUS_SEGMENTS:
                    # Check if the name is a safe builtin type
                    if ref.name in safe_builtins:
                        is_safe_builtin = True
                        break
                    self.findings.append(ObfuscationFinding(
                        technique=ObfuscationTechnique.NESTED_MODULE_PATH,
                        position=pos,
                        description=f"Module path contains dangerous segment '{part}'",
                        severity=25,
                        evidence=f"{ref.module}.{ref.name}"
                    ))
                    break

            if is_safe_builtin:
                continue

            # Check name path
            name_parts = ref.name.split('.')
            for part in name_parts:
                if part.lower() in DANGEROUS_SEGMENTS:
                    self.findings.append(ObfuscationFinding(
                        technique=ObfuscationTechnique.NESTED_MODULE_PATH,
                        position=pos,
                        description=f"Name contains dangerous segment '{part}'",
                        severity=25,
                        evidence=f"{ref.module}.{ref.name}"
                    ))
                    break

    def _check_stack_global_dynamic(
        self,
        opcodes: List[ParsedOpcode],
        machine: Optional[StackMachine]
    ) -> None:
        """Check for STACK_GLOBAL with dynamically computed names."""
        for i, op in enumerate(opcodes):
            if op.name == 'STACK_GLOBAL':
                # STACK_GLOBAL takes names from stack, not literal args
                # This makes static analysis harder
                self.findings.append(ObfuscationFinding(
                    technique=ObfuscationTechnique.STACK_GLOBAL_DYNAMIC,
                    position=op.position,
                    description="STACK_GLOBAL takes module/name from stack (dynamic)",
                    severity=15,
                    evidence="STACK_GLOBAL opcode detected"
                ))

    def _check_build_injection(
        self,
        opcodes: List[ParsedOpcode],
        machine: Optional[StackMachine]
    ) -> None:
        """Check for BUILD operations that might inject dangerous attributes."""
        if machine:
            for call in machine.build_calls:
                state = call.state
                if isinstance(state, dict):
                    for key in state.keys():
                        if isinstance(key, str) and key in DANGEROUS_ATTRS:
                            self.findings.append(ObfuscationFinding(
                                technique=ObfuscationTechnique.BUILD_ATTRIBUTE_INJECTION,
                                position=call.position,
                                description=f"BUILD sets dangerous attribute '{key}'",
                                severity=30,
                                evidence=f"BUILD with {key} in state"
                            ))

    def _check_extension_registry(self, opcodes: List[ParsedOpcode]) -> None:
        """Check for extension registry opcodes (EXT1/2/4)."""
        for op in opcodes:
            if op.name in ('EXT1', 'EXT2', 'EXT4'):
                self.findings.append(ObfuscationFinding(
                    technique=ObfuscationTechnique.EXTENSION_REGISTRY,
                    position=op.position,
                    description="Extension registry opcode - may reference unknown callables",
                    severity=20,
                    evidence=f"{op.name} code={op.arg}"
                ))

    def _check_encoded_payloads(self, opcodes: List[ParsedOpcode]) -> None:
        """Check for high-entropy strings that might be encoded payloads."""
        for op in opcodes:
            if op.name in ('STRING', 'BINSTRING', 'SHORT_BINSTRING',
                          'UNICODE', 'BINUNICODE', 'SHORT_BINUNICODE'):
                if isinstance(op.arg, str) and len(op.arg) > 20:
                    entropy = self._calculate_entropy(op.arg)
                    if entropy > 4.5:  # High entropy threshold
                        # Check for base64-like patterns
                        if self._looks_like_base64(op.arg):
                            self.findings.append(ObfuscationFinding(
                                technique=ObfuscationTechnique.ENCODED_PAYLOAD,
                                position=op.position,
                                description=f"High-entropy string (entropy={entropy:.2f}), may be encoded payload",
                                severity=15,
                                evidence=f"String length={len(op.arg)}, starts with: {op.arg[:30]}..."
                            ))

    def _check_attribute_chains(
        self,
        opcodes: List[ParsedOpcode],
        machine: Optional[StackMachine]
    ) -> None:
        """Check for dangerous attribute chain patterns."""
        if machine:
            for ref, pos in machine.globals_found:
                full_path = f"{ref.module}.{ref.name}"
                # Check for common exploit patterns
                patterns = [
                    r'__class__.*__bases__',
                    r'__subclasses__',
                    r'__globals__',
                    r'__builtins__',
                    r'__mro__',
                ]
                for pattern in patterns:
                    if re.search(pattern, full_path, re.IGNORECASE):
                        self.findings.append(ObfuscationFinding(
                            technique=ObfuscationTechnique.ATTRIBUTE_CHAIN,
                            position=pos,
                            description=f"Potential attribute chain exploit pattern",
                            severity=25,
                            evidence=full_path
                        ))
                        break

    def _check_unicode_homoglyphs(self, opcodes: List[ParsedOpcode]) -> None:
        """Check for Unicode homoglyph attacks (lookalike characters)."""
        # Common homoglyphs used in attacks
        homoglyphs = {
            '\u0435': 'e',  # Cyrillic е
            '\u0430': 'a',  # Cyrillic а
            '\u043e': 'o',  # Cyrillic о
            '\u0441': 'c',  # Cyrillic с
            '\u0440': 'p',  # Cyrillic р
            '\u0443': 'y',  # Cyrillic у
            '\u0445': 'x',  # Cyrillic х
            '\u0455': 's',  # Cyrillic ѕ
            '\u0456': 'i',  # Cyrillic і
            '\u04bb': 'h',  # Cyrillic һ
        }

        for op in opcodes:
            if op.name in ('GLOBAL', 'INST', 'UNICODE', 'BINUNICODE', 'SHORT_BINUNICODE'):
                text = ""
                if isinstance(op.arg, tuple):
                    text = f"{op.arg[0]}.{op.arg[1]}"
                elif isinstance(op.arg, str):
                    text = op.arg

                for char, replacement in homoglyphs.items():
                    if char in text:
                        self.findings.append(ObfuscationFinding(
                            technique=ObfuscationTechnique.UNICODE_HOMOGLYPH,
                            position=op.position,
                            description=f"Unicode homoglyph detected: '{char}' looks like '{replacement}'",
                            severity=20,
                            evidence=text
                        ))
                        break

    def _check_proto0_evasion(self, opcodes: List[ParsedOpcode]) -> None:
        """Check for protocol 0 usage (text-based, harder to detect)."""
        # Protocol 0 doesn't start with PROTO opcode
        has_proto = any(op.name == 'PROTO' for op in opcodes)
        if not has_proto and opcodes:
            # Check for dangerous operations in protocol 0
            has_dangerous = any(
                op.category in (OpcodeCategory.GLOBAL, OpcodeCategory.REDUCE)
                for op in opcodes
            )
            if has_dangerous:
                self.findings.append(ObfuscationFinding(
                    technique=ObfuscationTechnique.PROTO0_EVASION,
                    position=0,
                    description="Uses text-based protocol 0 which may evade binary pattern detection",
                    severity=10,
                    evidence="No PROTO opcode found, using protocol 0/1"
                ))

    @staticmethod
    def _calculate_entropy(data: str) -> float:
        """Calculate Shannon entropy of a string."""
        if not data:
            return 0.0

        freq = {}
        for char in data:
            freq[char] = freq.get(char, 0) + 1

        length = len(data)
        entropy = 0.0
        for count in freq.values():
            if count > 0:
                p = count / length
                entropy -= p * math.log2(p)

        return entropy

    @staticmethod
    def _looks_like_base64(data: str) -> bool:
        """Check if string looks like base64 encoded data."""
        # Base64 uses A-Za-z0-9+/= characters
        base64_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
        if len(data) < 20:
            return False

        # Check if most characters are base64
        base64_count = sum(1 for c in data if c in base64_chars)
        return base64_count / len(data) > 0.9


def detect_obfuscation(
    opcodes: List[ParsedOpcode],
    machine: Optional[StackMachine] = None
) -> List[ObfuscationFinding]:
    """Convenience function to detect obfuscation."""
    detector = ObfuscationDetector()
    return detector.analyze(opcodes, machine)
