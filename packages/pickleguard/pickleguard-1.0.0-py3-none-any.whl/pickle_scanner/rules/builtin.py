"""
Built-in detection rules.
"""

BUILTIN_RULES = """
rules:
  - name: "os_system_execution"
    severity: critical
    description: "Direct system command execution via os.system"
    tags: ["rce", "command_execution"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "os"
        name: "system"

  - name: "os_popen_execution"
    severity: critical
    description: "Command execution via os.popen"
    tags: ["rce", "command_execution"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "os"
        name: "popen.*"

  - name: "subprocess_execution"
    severity: critical
    description: "Command execution via subprocess module"
    tags: ["rce", "command_execution"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "subprocess"

  - name: "eval_execution"
    severity: critical
    description: "Arbitrary code execution via eval()"
    tags: ["rce", "code_execution"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "(builtins|__builtin__)"
        name: "eval"

  - name: "exec_execution"
    severity: critical
    description: "Arbitrary code execution via exec()"
    tags: ["rce", "code_execution"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "(builtins|__builtin__)"
        name: "exec"

  - name: "import_function"
    severity: high
    description: "Dynamic import via __import__()"
    tags: ["import", "code_execution"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "(builtins|__builtin__)"
        name: "__import__"

  - name: "nested_module_traversal"
    severity: high
    description: "Module path contains dangerous segments"
    tags: ["obfuscation", "evasion"]
    conditions:
      - opcode: [GLOBAL, STACK_GLOBAL, INST]
        name_contains: ["os.", "subprocess.", "builtins.", "__builtin__.", "importlib."]

  - name: "marshal_deserialize"
    severity: critical
    description: "Marshal deserialization (code execution)"
    tags: ["deserialization", "code_execution"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "marshal"
        name: "loads?"

  - name: "pickle_chain"
    severity: critical
    description: "Nested pickle deserialization"
    tags: ["deserialization", "chain"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "(pickle|_pickle|cPickle)"
        name: "loads?"

  - name: "code_object_creation"
    severity: critical
    description: "Code object creation for RCE"
    tags: ["code_execution", "advanced"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "types"
        name: "(CodeType|FunctionType)"

  - name: "ctypes_usage"
    severity: critical
    description: "Native code execution via ctypes"
    tags: ["native", "code_execution"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "ctypes"

  - name: "socket_creation"
    severity: high
    description: "Network socket creation"
    tags: ["network", "exfiltration"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "socket"

  - name: "urllib_request"
    severity: high
    description: "URL request (network access)"
    tags: ["network", "exfiltration"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "urllib.request"

  - name: "requests_library"
    severity: high
    description: "HTTP request via requests library"
    tags: ["network", "exfiltration"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "requests"

  - name: "file_write"
    severity: high
    description: "File system modification"
    tags: ["filesystem", "persistence"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "builtins"
        name: "open"

  - name: "shutil_operations"
    severity: high
    description: "File operations via shutil"
    tags: ["filesystem", "modification"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "shutil"
        name: "(rmtree|move|copy.*)"

  - name: "pty_spawn"
    severity: critical
    description: "PTY spawn for shell access"
    tags: ["shell", "command_execution"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "pty"
        name: "(spawn|fork)"

  - name: "runpy_execution"
    severity: critical
    description: "Module/script execution via runpy"
    tags: ["code_execution"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "runpy"

  - name: "yaml_unsafe_load"
    severity: critical
    description: "Unsafe YAML deserialization"
    tags: ["deserialization", "chain"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "yaml"
        name: "(load|unsafe_load|full_load)"

  - name: "webbrowser_open"
    severity: medium
    description: "Browser launch (possible phishing)"
    tags: ["external", "browser"]
    conditions:
      - opcode: [GLOBAL, INST]
        module: "webbrowser"
        name: "open.*"
"""
