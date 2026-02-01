"""
Threat intelligence database for dangerous callables.

Contains known dangerous Python callables and their risk levels.
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Set, Tuple, Optional, List
import re


class RiskLevel(IntEnum):
    """Risk levels for callables."""
    SAFE = 0
    LOW = 25
    MEDIUM = 50
    HIGH = 75
    CRITICAL = 100


@dataclass
class CallableRisk:
    """Risk information for a callable."""
    module: str
    name: str
    risk_level: RiskLevel
    description: str
    category: str
    cve_references: List[str] = None

    def __post_init__(self):
        if self.cve_references is None:
            self.cve_references = []

    @property
    def full_path(self) -> str:
        return f"{self.module}.{self.name}"


# Critical callables - direct code execution
CRITICAL_CALLABLES: Dict[Tuple[str, str], CallableRisk] = {
    # OS command execution
    ("os", "system"): CallableRisk(
        "os", "system", RiskLevel.CRITICAL,
        "Execute shell command", "command_execution"
    ),
    # posix is the Unix implementation of os module
    ("posix", "system"): CallableRisk(
        "posix", "system", RiskLevel.CRITICAL,
        "Execute shell command (Unix)", "command_execution"
    ),
    ("posix", "popen"): CallableRisk(
        "posix", "popen", RiskLevel.CRITICAL,
        "Open pipe to command (Unix)", "command_execution"
    ),
    ("nt", "system"): CallableRisk(
        "nt", "system", RiskLevel.CRITICAL,
        "Execute shell command (Windows)", "command_execution"
    ),
    ("os", "popen"): CallableRisk(
        "os", "popen", RiskLevel.CRITICAL,
        "Open pipe to command", "command_execution"
    ),
    ("os", "popen2"): CallableRisk(
        "os", "popen2", RiskLevel.CRITICAL,
        "Open pipe to command", "command_execution"
    ),
    ("os", "popen3"): CallableRisk(
        "os", "popen3", RiskLevel.CRITICAL,
        "Open pipe to command", "command_execution"
    ),
    ("os", "popen4"): CallableRisk(
        "os", "popen4", RiskLevel.CRITICAL,
        "Open pipe to command", "command_execution"
    ),
    ("os", "spawn"): CallableRisk(
        "os", "spawn", RiskLevel.CRITICAL,
        "Spawn new process", "command_execution"
    ),
    ("os", "spawnl"): CallableRisk(
        "os", "spawnl", RiskLevel.CRITICAL,
        "Spawn new process", "command_execution"
    ),
    ("os", "spawnle"): CallableRisk(
        "os", "spawnle", RiskLevel.CRITICAL,
        "Spawn new process", "command_execution"
    ),
    ("os", "spawnlp"): CallableRisk(
        "os", "spawnlp", RiskLevel.CRITICAL,
        "Spawn new process", "command_execution"
    ),
    ("os", "spawnlpe"): CallableRisk(
        "os", "spawnlpe", RiskLevel.CRITICAL,
        "Spawn new process", "command_execution"
    ),
    ("os", "spawnv"): CallableRisk(
        "os", "spawnv", RiskLevel.CRITICAL,
        "Spawn new process", "command_execution"
    ),
    ("os", "spawnve"): CallableRisk(
        "os", "spawnve", RiskLevel.CRITICAL,
        "Spawn new process", "command_execution"
    ),
    ("os", "spawnvp"): CallableRisk(
        "os", "spawnvp", RiskLevel.CRITICAL,
        "Spawn new process", "command_execution"
    ),
    ("os", "spawnvpe"): CallableRisk(
        "os", "spawnvpe", RiskLevel.CRITICAL,
        "Spawn new process", "command_execution"
    ),
    ("os", "execl"): CallableRisk(
        "os", "execl", RiskLevel.CRITICAL,
        "Replace process with new program", "command_execution"
    ),
    ("os", "execle"): CallableRisk(
        "os", "execle", RiskLevel.CRITICAL,
        "Replace process with new program", "command_execution"
    ),
    ("os", "execlp"): CallableRisk(
        "os", "execlp", RiskLevel.CRITICAL,
        "Replace process with new program", "command_execution"
    ),
    ("os", "execlpe"): CallableRisk(
        "os", "execlpe", RiskLevel.CRITICAL,
        "Replace process with new program", "command_execution"
    ),
    ("os", "execv"): CallableRisk(
        "os", "execv", RiskLevel.CRITICAL,
        "Replace process with new program", "command_execution"
    ),
    ("os", "execve"): CallableRisk(
        "os", "execve", RiskLevel.CRITICAL,
        "Replace process with new program", "command_execution"
    ),
    ("os", "execvp"): CallableRisk(
        "os", "execvp", RiskLevel.CRITICAL,
        "Replace process with new program", "command_execution"
    ),
    ("os", "execvpe"): CallableRisk(
        "os", "execvpe", RiskLevel.CRITICAL,
        "Replace process with new program", "command_execution"
    ),
    ("os", "fork"): CallableRisk(
        "os", "fork", RiskLevel.CRITICAL,
        "Fork process", "process_control"
    ),
    ("os", "forkpty"): CallableRisk(
        "os", "forkpty", RiskLevel.CRITICAL,
        "Fork process with PTY", "process_control"
    ),
    ("os", "kill"): CallableRisk(
        "os", "kill", RiskLevel.HIGH,
        "Send signal to process", "process_control"
    ),
    ("os", "killpg"): CallableRisk(
        "os", "killpg", RiskLevel.HIGH,
        "Send signal to process group", "process_control"
    ),

    # subprocess module
    ("subprocess", "call"): CallableRisk(
        "subprocess", "call", RiskLevel.CRITICAL,
        "Execute command", "command_execution"
    ),
    ("subprocess", "check_call"): CallableRisk(
        "subprocess", "check_call", RiskLevel.CRITICAL,
        "Execute command with check", "command_execution"
    ),
    ("subprocess", "check_output"): CallableRisk(
        "subprocess", "check_output", RiskLevel.CRITICAL,
        "Execute command and capture output", "command_execution"
    ),
    ("subprocess", "run"): CallableRisk(
        "subprocess", "run", RiskLevel.CRITICAL,
        "Execute command", "command_execution"
    ),
    ("subprocess", "Popen"): CallableRisk(
        "subprocess", "Popen", RiskLevel.CRITICAL,
        "Create subprocess", "command_execution"
    ),
    ("subprocess", "getoutput"): CallableRisk(
        "subprocess", "getoutput", RiskLevel.CRITICAL,
        "Execute shell command", "command_execution"
    ),
    ("subprocess", "getstatusoutput"): CallableRisk(
        "subprocess", "getstatusoutput", RiskLevel.CRITICAL,
        "Execute shell command", "command_execution"
    ),

    # pty module
    ("pty", "spawn"): CallableRisk(
        "pty", "spawn", RiskLevel.CRITICAL,
        "Spawn process with PTY", "command_execution"
    ),
    ("pty", "fork"): CallableRisk(
        "pty", "fork", RiskLevel.CRITICAL,
        "Fork with PTY", "command_execution"
    ),

    # Code execution - builtins
    ("builtins", "eval"): CallableRisk(
        "builtins", "eval", RiskLevel.CRITICAL,
        "Evaluate Python expression", "code_execution"
    ),
    ("builtins", "exec"): CallableRisk(
        "builtins", "exec", RiskLevel.CRITICAL,
        "Execute Python code", "code_execution"
    ),
    ("builtins", "compile"): CallableRisk(
        "builtins", "compile", RiskLevel.CRITICAL,
        "Compile Python code", "code_execution"
    ),
    ("builtins", "__import__"): CallableRisk(
        "builtins", "__import__", RiskLevel.HIGH,
        "Import module dynamically", "import"
    ),
    ("builtins", "open"): CallableRisk(
        "builtins", "open", RiskLevel.MEDIUM,
        "Open file", "file_access"
    ),
    ("builtins", "input"): CallableRisk(
        "builtins", "input", RiskLevel.LOW,
        "Read user input", "user_interaction"
    ),

    # __builtins__ variants
    ("__builtin__", "eval"): CallableRisk(
        "__builtin__", "eval", RiskLevel.CRITICAL,
        "Evaluate Python expression", "code_execution"
    ),
    ("__builtin__", "exec"): CallableRisk(
        "__builtin__", "exec", RiskLevel.CRITICAL,
        "Execute Python code", "code_execution"
    ),
    ("__builtin__", "compile"): CallableRisk(
        "__builtin__", "compile", RiskLevel.CRITICAL,
        "Compile Python code", "code_execution"
    ),
    ("__builtin__", "__import__"): CallableRisk(
        "__builtin__", "__import__", RiskLevel.HIGH,
        "Import module dynamically", "import"
    ),

    # importlib
    ("importlib", "import_module"): CallableRisk(
        "importlib", "import_module", RiskLevel.HIGH,
        "Import module dynamically", "import"
    ),
    ("importlib.util", "find_spec"): CallableRisk(
        "importlib.util", "find_spec", RiskLevel.MEDIUM,
        "Find module spec", "import"
    ),

    # runpy
    ("runpy", "run_module"): CallableRisk(
        "runpy", "run_module", RiskLevel.CRITICAL,
        "Run module as script", "code_execution"
    ),
    ("runpy", "run_path"): CallableRisk(
        "runpy", "run_path", RiskLevel.CRITICAL,
        "Run file as script", "code_execution"
    ),
    ("runpy", "_run_code"): CallableRisk(
        "runpy", "_run_code", RiskLevel.CRITICAL,
        "Execute code object (internal)", "code_execution"
    ),
    ("runpy", "_run_module_code"): CallableRisk(
        "runpy", "_run_module_code", RiskLevel.CRITICAL,
        "Execute module code (internal)", "code_execution"
    ),

    # code module
    ("code", "interact"): CallableRisk(
        "code", "interact", RiskLevel.CRITICAL,
        "Start interactive interpreter", "code_execution"
    ),
    ("code", "compile_command"): CallableRisk(
        "code", "compile_command", RiskLevel.HIGH,
        "Compile interactive command", "code_execution"
    ),

    # execfile variants (Python 2 builtin, various reimplementations)
    ("builtins", "execfile"): CallableRisk(
        "builtins", "execfile", RiskLevel.CRITICAL,
        "Execute Python file", "code_execution"
    ),
    ("__builtin__", "execfile"): CallableRisk(
        "__builtin__", "execfile", RiskLevel.CRITICAL,
        "Execute Python file (Python 2)", "code_execution"
    ),

    # File operations
    ("io", "open"): CallableRisk(
        "io", "open", RiskLevel.MEDIUM,
        "Open file", "file_access"
    ),
    ("io", "FileIO"): CallableRisk(
        "io", "FileIO", RiskLevel.MEDIUM,
        "Low-level file I/O", "file_access"
    ),
    ("pathlib", "Path"): CallableRisk(
        "pathlib", "Path", RiskLevel.LOW,
        "Create path object", "file_access"
    ),
    # Pathlib Path methods that write
    ("pathlib.Path", "write_text"): CallableRisk(
        "pathlib.Path", "write_text", RiskLevel.HIGH,
        "Write text to file", "file_modification"
    ),
    ("pathlib.Path", "write_bytes"): CallableRisk(
        "pathlib.Path", "write_bytes", RiskLevel.HIGH,
        "Write bytes to file", "file_modification"
    ),
    ("pathlib.Path", "unlink"): CallableRisk(
        "pathlib.Path", "unlink", RiskLevel.HIGH,
        "Delete file", "file_modification"
    ),
    ("pathlib.Path", "rmdir"): CallableRisk(
        "pathlib.Path", "rmdir", RiskLevel.HIGH,
        "Delete directory", "file_modification"
    ),
    ("pathlib.Path", "rename"): CallableRisk(
        "pathlib.Path", "rename", RiskLevel.MEDIUM,
        "Rename file", "file_modification"
    ),
    ("pathlib.Path", "mkdir"): CallableRisk(
        "pathlib.Path", "mkdir", RiskLevel.LOW,
        "Create directory", "file_modification"
    ),
    ("pathlib.Path", "touch"): CallableRisk(
        "pathlib.Path", "touch", RiskLevel.LOW,
        "Create empty file", "file_modification"
    ),

    # shutil - file operations
    ("shutil", "rmtree"): CallableRisk(
        "shutil", "rmtree", RiskLevel.HIGH,
        "Remove directory tree", "file_modification"
    ),
    ("shutil", "move"): CallableRisk(
        "shutil", "move", RiskLevel.MEDIUM,
        "Move file or directory", "file_modification"
    ),
    ("shutil", "copy"): CallableRisk(
        "shutil", "copy", RiskLevel.MEDIUM,
        "Copy file", "file_modification"
    ),
    ("shutil", "copy2"): CallableRisk(
        "shutil", "copy2", RiskLevel.MEDIUM,
        "Copy file with metadata", "file_modification"
    ),
    ("shutil", "copytree"): CallableRisk(
        "shutil", "copytree", RiskLevel.MEDIUM,
        "Copy directory tree", "file_modification"
    ),

    # os file operations
    ("os", "remove"): CallableRisk(
        "os", "remove", RiskLevel.HIGH,
        "Remove file", "file_modification"
    ),
    ("os", "unlink"): CallableRisk(
        "os", "unlink", RiskLevel.HIGH,
        "Remove file", "file_modification"
    ),
    ("os", "rmdir"): CallableRisk(
        "os", "rmdir", RiskLevel.HIGH,
        "Remove directory", "file_modification"
    ),
    ("os", "removedirs"): CallableRisk(
        "os", "removedirs", RiskLevel.HIGH,
        "Remove directories", "file_modification"
    ),
    ("os", "rename"): CallableRisk(
        "os", "rename", RiskLevel.MEDIUM,
        "Rename file", "file_modification"
    ),
    ("os", "renames"): CallableRisk(
        "os", "renames", RiskLevel.MEDIUM,
        "Rename file recursively", "file_modification"
    ),
    ("os", "replace"): CallableRisk(
        "os", "replace", RiskLevel.MEDIUM,
        "Replace file", "file_modification"
    ),
    ("os", "mkdir"): CallableRisk(
        "os", "mkdir", RiskLevel.LOW,
        "Create directory", "file_modification"
    ),
    ("os", "makedirs"): CallableRisk(
        "os", "makedirs", RiskLevel.LOW,
        "Create directories", "file_modification"
    ),
    ("os", "chmod"): CallableRisk(
        "os", "chmod", RiskLevel.HIGH,
        "Change file permissions", "file_modification"
    ),
    ("os", "chown"): CallableRisk(
        "os", "chown", RiskLevel.HIGH,
        "Change file owner", "file_modification"
    ),

    # Network operations
    ("socket", "socket"): CallableRisk(
        "socket", "socket", RiskLevel.HIGH,
        "Create network socket", "network"
    ),
    ("socket", "create_connection"): CallableRisk(
        "socket", "create_connection", RiskLevel.HIGH,
        "Create network connection", "network"
    ),
    ("urllib.request", "urlopen"): CallableRisk(
        "urllib.request", "urlopen", RiskLevel.HIGH,
        "Open URL", "network"
    ),
    ("urllib.request", "urlretrieve"): CallableRisk(
        "urllib.request", "urlretrieve", RiskLevel.HIGH,
        "Download file from URL", "network"
    ),
    ("urllib.request", "Request"): CallableRisk(
        "urllib.request", "Request", RiskLevel.MEDIUM,
        "Create URL request", "network"
    ),
    ("http.client", "HTTPConnection"): CallableRisk(
        "http.client", "HTTPConnection", RiskLevel.HIGH,
        "Create HTTP connection", "network"
    ),
    ("http.client", "HTTPSConnection"): CallableRisk(
        "http.client", "HTTPSConnection", RiskLevel.HIGH,
        "Create HTTPS connection", "network"
    ),
    ("ftplib", "FTP"): CallableRisk(
        "ftplib", "FTP", RiskLevel.HIGH,
        "Create FTP connection", "network"
    ),
    ("smtplib", "SMTP"): CallableRisk(
        "smtplib", "SMTP", RiskLevel.HIGH,
        "Create SMTP connection", "network"
    ),

    # requests library (third-party but common)
    ("requests", "get"): CallableRisk(
        "requests", "get", RiskLevel.HIGH,
        "HTTP GET request", "network"
    ),
    ("requests", "post"): CallableRisk(
        "requests", "post", RiskLevel.HIGH,
        "HTTP POST request", "network"
    ),
    ("requests", "put"): CallableRisk(
        "requests", "put", RiskLevel.HIGH,
        "HTTP PUT request", "network"
    ),
    ("requests", "delete"): CallableRisk(
        "requests", "delete", RiskLevel.HIGH,
        "HTTP DELETE request", "network"
    ),
    ("requests", "request"): CallableRisk(
        "requests", "request", RiskLevel.HIGH,
        "HTTP request", "network"
    ),
    ("requests", "Session"): CallableRisk(
        "requests", "Session", RiskLevel.HIGH,
        "Create HTTP session", "network"
    ),

    # Deserialization chains (can lead to RCE)
    ("pickle", "loads"): CallableRisk(
        "pickle", "loads", RiskLevel.CRITICAL,
        "Deserialize pickle data - nested RCE", "deserialization"
    ),
    ("pickle", "load"): CallableRisk(
        "pickle", "load", RiskLevel.CRITICAL,
        "Deserialize pickle from file - nested RCE", "deserialization"
    ),
    ("_pickle", "loads"): CallableRisk(
        "_pickle", "loads", RiskLevel.CRITICAL,
        "Deserialize pickle data (C implementation)", "deserialization"
    ),
    ("cPickle", "loads"): CallableRisk(
        "cPickle", "loads", RiskLevel.CRITICAL,
        "Deserialize pickle data (legacy C)", "deserialization"
    ),
    ("marshal", "loads"): CallableRisk(
        "marshal", "loads", RiskLevel.CRITICAL,
        "Deserialize marshal data", "deserialization"
    ),
    ("marshal", "load"): CallableRisk(
        "marshal", "load", RiskLevel.CRITICAL,
        "Deserialize marshal from file", "deserialization"
    ),
    ("yaml", "load"): CallableRisk(
        "yaml", "load", RiskLevel.CRITICAL,
        "Deserialize YAML (unsafe)", "deserialization"
    ),
    ("yaml", "unsafe_load"): CallableRisk(
        "yaml", "unsafe_load", RiskLevel.CRITICAL,
        "Deserialize YAML (unsafe)", "deserialization"
    ),
    ("yaml", "full_load"): CallableRisk(
        "yaml", "full_load", RiskLevel.HIGH,
        "Deserialize YAML (full)", "deserialization"
    ),
    ("jsonpickle", "decode"): CallableRisk(
        "jsonpickle", "decode", RiskLevel.CRITICAL,
        "Deserialize jsonpickle", "deserialization"
    ),
    ("shelve", "open"): CallableRisk(
        "shelve", "open", RiskLevel.HIGH,
        "Open shelve database (uses pickle)", "deserialization"
    ),
    ("dill", "loads"): CallableRisk(
        "dill", "loads", RiskLevel.CRITICAL,
        "Deserialize dill data", "deserialization"
    ),
    ("cloudpickle", "loads"): CallableRisk(
        "cloudpickle", "loads", RiskLevel.CRITICAL,
        "Deserialize cloudpickle data", "deserialization"
    ),
    # numpy.load can execute pickle if allow_pickle=True
    ("numpy", "load"): CallableRisk(
        "numpy", "load", RiskLevel.HIGH,
        "NumPy load (may unpickle if allow_pickle=True)", "deserialization"
    ),
    ("numpy", "loads"): CallableRisk(
        "numpy", "loads", RiskLevel.HIGH,
        "NumPy loads (may unpickle)", "deserialization"
    ),

    # Code object creation (for sophisticated attacks)
    ("types", "CodeType"): CallableRisk(
        "types", "CodeType", RiskLevel.CRITICAL,
        "Create code object", "code_execution"
    ),
    ("types", "FunctionType"): CallableRisk(
        "types", "FunctionType", RiskLevel.CRITICAL,
        "Create function from code", "code_execution"
    ),
    ("types", "LambdaType"): CallableRisk(
        "types", "LambdaType", RiskLevel.CRITICAL,
        "Create lambda function", "code_execution"
    ),
    ("types", "MethodType"): CallableRisk(
        "types", "MethodType", RiskLevel.HIGH,
        "Create bound method", "code_execution"
    ),
    ("types", "ModuleType"): CallableRisk(
        "types", "ModuleType", RiskLevel.MEDIUM,
        "Create module object", "code_execution"
    ),

    # ctypes (can call arbitrary C functions)
    ("ctypes", "CDLL"): CallableRisk(
        "ctypes", "CDLL", RiskLevel.CRITICAL,
        "Load C library", "native_code"
    ),
    ("ctypes", "cdll"): CallableRisk(
        "ctypes", "cdll", RiskLevel.CRITICAL,
        "C library loader", "native_code"
    ),
    ("ctypes", "windll"): CallableRisk(
        "ctypes", "windll", RiskLevel.CRITICAL,
        "Windows DLL loader", "native_code"
    ),
    ("ctypes", "oledll"): CallableRisk(
        "ctypes", "oledll", RiskLevel.CRITICAL,
        "OLE DLL loader", "native_code"
    ),
    ("ctypes", "pydll"): CallableRisk(
        "ctypes", "pydll", RiskLevel.CRITICAL,
        "Python DLL loader", "native_code"
    ),
    ("ctypes", "pythonapi"): CallableRisk(
        "ctypes", "pythonapi", RiskLevel.CRITICAL,
        "Python C API access", "native_code"
    ),
    ("ctypes", "cast"): CallableRisk(
        "ctypes", "cast", RiskLevel.HIGH,
        "Cast pointer", "native_code"
    ),
    ("ctypes", "memmove"): CallableRisk(
        "ctypes", "memmove", RiskLevel.CRITICAL,
        "Copy memory", "native_code"
    ),
    ("ctypes", "memset"): CallableRisk(
        "ctypes", "memset", RiskLevel.CRITICAL,
        "Set memory", "native_code"
    ),
    ("ctypes", "string_at"): CallableRisk(
        "ctypes", "string_at", RiskLevel.HIGH,
        "Read memory as string", "native_code"
    ),

    # multiprocessing
    ("multiprocessing", "Process"): CallableRisk(
        "multiprocessing", "Process", RiskLevel.HIGH,
        "Create new process", "process_control"
    ),
    ("multiprocessing", "Pool"): CallableRisk(
        "multiprocessing", "Pool", RiskLevel.HIGH,
        "Create process pool", "process_control"
    ),

    # threading
    ("threading", "Thread"): CallableRisk(
        "threading", "Thread", RiskLevel.MEDIUM,
        "Create new thread", "concurrency"
    ),

    # getattr/setattr for attribute manipulation
    ("builtins", "getattr"): CallableRisk(
        "builtins", "getattr", RiskLevel.MEDIUM,
        "Get attribute dynamically", "introspection"
    ),
    ("builtins", "setattr"): CallableRisk(
        "builtins", "setattr", RiskLevel.MEDIUM,
        "Set attribute dynamically", "introspection"
    ),
    ("builtins", "delattr"): CallableRisk(
        "builtins", "delattr", RiskLevel.MEDIUM,
        "Delete attribute dynamically", "introspection"
    ),
    ("builtins", "globals"): CallableRisk(
        "builtins", "globals", RiskLevel.MEDIUM,
        "Access global namespace", "introspection"
    ),
    ("builtins", "locals"): CallableRisk(
        "builtins", "locals", RiskLevel.LOW,
        "Access local namespace", "introspection"
    ),
    ("builtins", "vars"): CallableRisk(
        "builtins", "vars", RiskLevel.LOW,
        "Access object namespace", "introspection"
    ),

    # Apply functions
    ("functools", "reduce"): CallableRisk(
        "functools", "reduce", RiskLevel.MEDIUM,
        "Apply function cumulatively", "functional"
    ),

    # sys module
    ("sys", "exit"): CallableRisk(
        "sys", "exit", RiskLevel.MEDIUM,
        "Exit interpreter", "process_control"
    ),
    ("sys", "modules"): CallableRisk(
        "sys", "modules", RiskLevel.MEDIUM,
        "Access loaded modules", "introspection"
    ),

    # webbrowser - can be used for phishing, data exfiltration
    ("webbrowser", "open"): CallableRisk(
        "webbrowser", "open", RiskLevel.HIGH,
        "Open URL in browser (potential phishing)", "external_app"
    ),
    ("webbrowser", "open_new"): CallableRisk(
        "webbrowser", "open_new", RiskLevel.HIGH,
        "Open URL in new browser (potential phishing)", "external_app"
    ),
    ("webbrowser", "open_new_tab"): CallableRisk(
        "webbrowser", "open_new_tab", RiskLevel.HIGH,
        "Open URL in new tab (potential phishing)", "external_app"
    ),

    # tempfile (for staging attacks)
    ("tempfile", "NamedTemporaryFile"): CallableRisk(
        "tempfile", "NamedTemporaryFile", RiskLevel.LOW,
        "Create named temp file", "file_access"
    ),
    ("tempfile", "mktemp"): CallableRisk(
        "tempfile", "mktemp", RiskLevel.LOW,
        "Create temp filename", "file_access"
    ),
}

# Patterns for wildcard matching
DANGEROUS_MODULE_PATTERNS = [
    re.compile(r'^subprocess$'),
    re.compile(r'^os$'),
    re.compile(r'^pty$'),
    re.compile(r'^commands$'),  # Legacy Python 2
    re.compile(r'^runpy$'),     # Script execution
    re.compile(r'^posix$'),     # Unix os implementation
    re.compile(r'^nt$'),        # Windows os implementation
]


class ThreatDatabase:
    """Database of known dangerous callables."""

    def __init__(self):
        self.callables = dict(CRITICAL_CALLABLES)
        self._module_patterns = list(DANGEROUS_MODULE_PATTERNS)
        # Known dangerous functions that may appear in nested paths
        self._dangerous_funcs = {
            'system', 'popen', 'popen2', 'popen3', 'popen4',
            'spawn', 'spawnl', 'spawnle', 'spawnlp', 'spawnlpe',
            'spawnv', 'spawnve', 'spawnvp', 'spawnvpe',
            'exec', 'execl', 'execle', 'execlp', 'execlpe',
            'execv', 'execve', 'execvp', 'execvpe',
            'eval', 'compile', '__import__', 'execfile',
            'call', 'check_call', 'check_output', 'run', 'Popen',
            'loads', 'load', 'urlopen', 'urlretrieve',
            '_run_code', '_run_module_code', 'run_module', 'run_path',
        }

    def lookup(self, module: str, name: str) -> Optional[CallableRisk]:
        """Look up a callable in the database."""
        # Direct lookup
        key = (module, name)
        if key in self.callables:
            return self.callables[key]

        # Check for module-level patterns
        for pattern in self._module_patterns:
            if pattern.match(module):
                # Return a generic risk for dangerous modules
                return CallableRisk(
                    module, name, RiskLevel.HIGH,
                    f"Function from dangerous module '{module}'",
                    "dangerous_module"
                )

        # Check for nested module paths like "torch serialization.os.system"
        # The dangerous callable may be embedded in the name field
        full_path = f"{module}.{name}"
        nested_risk = self._check_nested_path(full_path, module, name)
        if nested_risk:
            return nested_risk

        return None

    def _check_nested_path(self, full_path: str, module: str, name: str) -> Optional[CallableRisk]:
        """Check for dangerous patterns in nested module paths."""
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

        # Check if this is a safe builtin access (e.g., __builtin__.set)
        if module in ('builtins', '__builtin__', '__builtins__') and name in safe_builtins:
            return None  # Safe, not dangerous

        # Split on dots to find embedded dangerous modules
        parts = full_path.replace(' ', '.').split('.')

        for i, part in enumerate(parts):
            # Check if this part is a dangerous module
            if part in ('os', 'subprocess', 'builtins', '__builtin__', 'pty', 'commands', 'posix', 'nt', 'runpy'):
                # Get the remaining parts as the function name
                remaining = parts[i + 1:] if i + 1 < len(parts) else []
                if remaining:
                    func_name = remaining[0]
                    # Skip if it's a safe builtin type
                    if func_name in safe_builtins:
                        continue
                    if func_name in self._dangerous_funcs:
                        return CallableRisk(
                            part, func_name, RiskLevel.CRITICAL,
                            f"Nested path contains {part}.{func_name} - likely obfuscated attack",
                            "nested_module_attack"
                        )
                    # Even without specific function, the module is dangerous
                    return CallableRisk(
                        part, '.'.join(remaining), RiskLevel.HIGH,
                        f"Nested path contains dangerous module '{part}'",
                        "nested_module_attack"
                    )

            # Check for dangerous deserialization modules
            if part in ('pickle', '_pickle', 'cPickle', 'marshal', 'yaml'):
                remaining = parts[i + 1:] if i + 1 < len(parts) else []
                if remaining and remaining[0] in ('load', 'loads', 'unsafe_load'):
                    return CallableRisk(
                        part, remaining[0], RiskLevel.CRITICAL,
                        f"Nested deserialization chain: {part}.{remaining[0]}",
                        "deserialization_chain"
                    )

            # Check for pathlib.Path with dangerous methods
            if part == 'Path' and i > 0 and parts[i-1] == 'pathlib':
                remaining = parts[i + 1:] if i + 1 < len(parts) else []
                if remaining:
                    func_name = remaining[0]
                    if func_name in ('write_text', 'write_bytes', 'unlink', 'rmdir'):
                        return CallableRisk(
                            'pathlib.Path', func_name, RiskLevel.HIGH,
                            f"File modification via pathlib.Path.{func_name}",
                            "file_modification"
                        )

            # Check for dangerous function names anywhere in the path (e.g., _pydev_bundle._pydev_execfile.execfile)
            if part in self._dangerous_funcs:
                return CallableRisk(
                    module, name, RiskLevel.CRITICAL,
                    f"Dangerous function '{part}' found in callable path",
                    "dangerous_function"
                )

        return None

    def add_callable(self, risk: CallableRisk) -> None:
        """Add a callable to the database."""
        self.callables[(risk.module, risk.name)] = risk

    def get_risk_level(self, module: str, name: str) -> RiskLevel:
        """Get risk level for a callable."""
        risk = self.lookup(module, name)
        return risk.risk_level if risk else RiskLevel.SAFE


# Module-level convenience function
_default_db = ThreatDatabase()


def is_dangerous_callable(module: str, name: str) -> Tuple[bool, Optional[CallableRisk]]:
    """Check if a callable is dangerous."""
    risk = _default_db.lookup(module, name)
    if risk and risk.risk_level >= RiskLevel.MEDIUM:
        return True, risk
    return False, risk


def get_threat_database() -> ThreatDatabase:
    """Get the default threat database."""
    return _default_db
