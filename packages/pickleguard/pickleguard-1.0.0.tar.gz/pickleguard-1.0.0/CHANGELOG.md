# Changelog

All notable changes to PickleGuard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-31

### Added

- Initial release of PickleGuard
- Static analysis engine for pickle files (no code execution)
- Support for pickle protocols 0-5
- PyTorch ZIP and tar container parsing
- NumPy .npy/.npz file support
- SafeTensors and ONNX format detection
- Comprehensive dangerous callable database (200+ entries)
- Obfuscation detection:
  - INST opcode bypass detection
  - Nested module path analysis (e.g., `torch.serialization.os.system`)
  - STACK_GLOBAL dynamic name detection
  - BUILD attribute injection detection
  - Extension registry abuse detection
  - High-entropy encoded payload detection
  - Unicode homoglyph attack detection
  - Protocol 0 evasion detection
- ML framework pattern recognition:
  - PyTorch reconstruction patterns
  - NumPy array patterns
  - scikit-learn model patterns
  - HuggingFace Transformers patterns
- Safe builtin whitelisting to eliminate false positives
- Multi-factor risk scoring system
- Output formats: text, JSON, SARIF
- Command-line interface with batch scanning
- Custom rule support via YAML configuration

### Performance

Tested on PickleBall dataset (84 malicious samples) and 268 benign HuggingFace models:

| Metric | Result |
|--------|--------|
| True Positive Rate | 96.4% |
| False Positive Rate | 0.0% |
