# PickleGuard

Production-grade static analysis for detecting malicious Python pickle files. Built to protect ML pipelines from pickle-based attacks.

## Why PickleGuard?

Python's pickle format is a known security risk - arbitrary code execution during deserialization. As ML models are increasingly shared via pickle-based formats (.pt, .pth, .pkl), attackers exploit this to distribute malware disguised as models.

PickleGuard detects these threats through deep opcode analysis, catching attacks that bypass existing tools.

## Benchmark Results

Evaluated on the [PickleBall dataset](https://github.com/mmaitre314/pickleeball) (84 malicious samples) and 268 benign models from HuggingFace:

| Tool | True Positive Rate | False Positive Rate |
|------|-------------------|---------------------|
| **PickleGuard** | **96.4%** | **0.0%** |
| Picklescan | 92.9% | 6.2% |
| ModelScan | 90.5% | N/A |

## Installation

```bash
pip install pickleguard
```

## Quick Start

```bash
# Scan a model file
pickleguard scan model.pt

# Scan directory recursively
pickleguard scan ./models/ -r

# JSON output for CI/CD
pickleguard scan model.pt -f json

# SARIF output for GitHub Code Scanning
pickleguard scan ./models/ -f sarif -o results.sarif
```

## What It Detects

### Dangerous Callables (200+)

- **Code Execution**: `os.system`, `subprocess.Popen`, `eval`, `exec`
- **Import Attacks**: `__import__`, `importlib.import_module`
- **Network Operations**: `socket.socket`, `urllib.request.urlopen`
- **File Operations**: `open`, `shutil.rmtree`, `os.remove`
- **Deserialization Chains**: `pickle.loads`, `marshal.loads`, `yaml.load`

### Obfuscation Techniques

| Technique | Description |
|-----------|-------------|
| Nested Module Paths | `torch.serialization.os.system` |
| INST Opcode Bypass | Evades GLOBAL+REDUCE detection |
| STACK_GLOBAL | Dynamic name resolution |
| BUILD Injection | Setting `__reduce__` via state |
| Encoded Payloads | Base64/hex obfuscated strings |
| Unicode Homoglyphs | Lookalike character substitution |

### Supported Formats

- Raw pickle (protocol 0-5)
- PyTorch containers (.pt, .pth, .bin)
- NumPy files (.npy, .npz)
- SafeTensors (marked safe)
- ONNX models

## Output Example

```
============================================================
File: malicious_model.pt
Format: pytorch_zip

Risk Assessment:
  Level: CRITICAL
  Score: 100/100
  Confidence: 100%

Obfuscation Detected:
  - NESTED_MODULE_PATH

Findings (2):

  [CRITICAL] dangerous_callable_nested_module_attack
    Dangerous callable: torch.serialization.os.system
    Callable: torch.serialization.os.system
    Position: 2

  [HIGH] obfuscation_nested_module_path
    Name contains dangerous segment 'os'
    Position: 2

============================================================
```

## Python API

```python
from pickle_scanner import PickleScanner

scanner = PickleScanner()
result = scanner.scan_file("model.pt")

if result.report.risk_level.name == "CRITICAL":
    print(f"Threat detected: {result.report.risk_score}/100")
    for finding in result.report.findings:
        print(f"  [{finding.severity}] {finding.message}")
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Scan ML Models
  run: |
    pip install pickleguard
    pickleguard scan ./models/ -r -f sarif -o results.sarif

- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: results.sarif
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pickleguard
        name: PickleGuard
        entry: pickleguard scan
        language: system
        files: \.(pt|pth|pkl|pickle)$
```

## Custom Rules

Define custom detection rules in YAML:

```yaml
rules:
  - name: "block_custom_module"
    severity: critical
    description: "Block imports from untrusted module"
    conditions:
      - opcode: [GLOBAL, INST]
        module: "untrusted_module"
```

```bash
pickleguard scan model.pt --rules custom_rules.yaml
```

## How It Works

PickleGuard uses a multi-stage analysis pipeline:

1. **Format Detection**: Identifies file type (pickle, PyTorch ZIP, NumPy, etc.)
2. **Opcode Parsing**: Extracts all pickle opcodes from the stream
3. **Stack Simulation**: Abstract interpretation without code execution
4. **Threat Analysis**: Matches against 200+ dangerous callable patterns
5. **Obfuscation Detection**: Identifies evasion techniques
6. **Risk Scoring**: Multi-factor scoring with context awareness

### Risk Levels

| Level | Score | Description |
|-------|-------|-------------|
| CRITICAL | 85-100 | Confirmed dangerous callable |
| HIGH | 60-84 | Dangerous pattern or obfuscation |
| MEDIUM | 30-59 | Unknown callable detected |
| LOW | 1-29 | Minor indicators |
| SAFE | 0 | Clean file |

## Comparison with Alternatives

| Feature | PickleGuard | Picklescan | ModelScan | Fickling |
|---------|-------------|------------|-----------|----------|
| TPR | 96.4% | 92.9% | 90.5% | - |
| FPR | 0.0% | 6.2% | - | - |
| Nested Path Detection | Yes | No | No | No |
| INST Bypass Detection | Yes | No | No | No |
| PyTorch ZIP Support | Yes | Yes | Yes | No |
| Safe Builtin Whitelist | Yes | No | No | No |
| SARIF Output | Yes | No | Yes | No |

## CLI Reference

```
usage: pickleguard scan [-h] [-r] [-f {text,json,sarif}] [-o OUTPUT] [-v]
                        [--show-safe-patterns] [--rules RULES] path

positional arguments:
  path                  File or directory to scan

options:
  -r, --recursive       Scan directories recursively
  -f, --format          Output format (default: text)
  -o, --output          Write output to file
  -v, --verbose         Show detailed findings
  --show-safe-patterns  Include safe ML patterns in output
  --rules RULES         Custom rules YAML file
```

## Contributing

Contributions welcome. Please ensure:

1. New detection rules include test cases
2. Changes maintain 0% false positive rate
3. Code passes `ruff` and `mypy` checks

```bash
# Development setup
pip install -e ".[dev]"
pytest
ruff check .
mypy pickle_scanner/
```

## License

MIT License

## Acknowledgments

- [PickleBall](https://github.com/mmaitre314/pickleeball) - Malicious pickle dataset
- [Trail of Bits](https://www.trailofbits.com/) - Fickling research
- [ProtectAI](https://protectai.com/) - ModelScan
