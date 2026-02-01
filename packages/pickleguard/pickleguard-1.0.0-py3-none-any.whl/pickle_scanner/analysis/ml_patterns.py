"""
ML framework pattern recognition.

Identifies safe ML framework patterns to reduce false positives.
"""

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Tuple, Set

from pickle_scanner.core.stack_machine import GlobalRef


class MLFramework(Enum):
    """Detected ML frameworks."""
    UNKNOWN = auto()
    PYTORCH = auto()
    NUMPY = auto()
    SKLEARN = auto()
    TENSORFLOW = auto()
    KERAS = auto()
    SCIPY = auto()
    PANDAS = auto()
    JOBLIB = auto()
    XGBOOST = auto()
    LIGHTGBM = auto()
    CATBOOST = auto()
    HUGGINGFACE = auto()


@dataclass
class MLPatternMatch:
    """A matched ML framework pattern."""
    framework: MLFramework
    module: str
    name: str
    description: str
    is_safe: bool = True


# Safe ML framework patterns - these are standard reconstruction functions
# that don't execute arbitrary code
SAFE_ML_PATTERNS = [
    # PyTorch tensor reconstruction
    (r'^torch\._utils$', r'^_rebuild_tensor.*', MLFramework.PYTORCH, "PyTorch tensor rebuild"),
    (r'^torch$', r'^_utils$', MLFramework.PYTORCH, "PyTorch utils module"),
    (r'^torch\.storage$', r'^_load_from_bytes$', MLFramework.PYTORCH, "PyTorch storage load"),
    (r'^torch$', r'^.*Storage$', MLFramework.PYTORCH, "PyTorch storage type"),
    (r'^torch\..*Storage$', r'.*', MLFramework.PYTORCH, "PyTorch storage class"),
    (r'^torch$', r'^(Float|Double|Half|Int|Long|Short|Byte|Bool|BFloat16|Complex)Tensor$', MLFramework.PYTORCH, "PyTorch tensor type"),
    (r'^torch$', r'^.*Tensor$', MLFramework.PYTORCH, "PyTorch tensor class"),
    (r'^torch\.nn\.modules\..+$', r'.*', MLFramework.PYTORCH, "PyTorch nn module"),
    (r'^torch\.nn\.parameter$', r'^Parameter$', MLFramework.PYTORCH, "PyTorch Parameter"),
    (r'^torch\.nn$', r'^Parameter$', MLFramework.PYTORCH, "PyTorch Parameter"),
    (r'^torch\.cuda$', r'.*', MLFramework.PYTORCH, "PyTorch CUDA"),
    (r'^torch$', r'^device$', MLFramework.PYTORCH, "PyTorch device"),
    (r'^torch$', r'^dtype$', MLFramework.PYTORCH, "PyTorch dtype"),
    (r'^torch$', r'^Size$', MLFramework.PYTORCH, "PyTorch Size"),
    (r'^torch\.ao\.quantization', r'.*', MLFramework.PYTORCH, "PyTorch quantization"),
    (r'^torch\.distributed', r'.*', MLFramework.PYTORCH, "PyTorch distributed"),
    (r'^torch\.optim', r'.*', MLFramework.PYTORCH, "PyTorch optimizer"),

    # NumPy reconstruction
    (r'^numpy\.core\.multiarray$', r'^_reconstruct$', MLFramework.NUMPY, "NumPy array reconstruct"),
    (r'^numpy\.core\.multiarray$', r'^scalar$', MLFramework.NUMPY, "NumPy scalar"),
    (r'^numpy$', r'^dtype$', MLFramework.NUMPY, "NumPy dtype"),
    (r'^numpy$', r'^ndarray$', MLFramework.NUMPY, "NumPy ndarray"),
    (r'^numpy\.core$', r'.*', MLFramework.NUMPY, "NumPy core"),
    (r'^numpy\.ma\.core$', r'.*', MLFramework.NUMPY, "NumPy masked array"),
    (r'^numpy\.random', r'.*', MLFramework.NUMPY, "NumPy random"),
    (r'^numpy$', r'^(int|uint|float|complex|bool|str|bytes|object|void)\d*$', MLFramework.NUMPY, "NumPy scalar type"),
    (r'^numpy$', r'^(array|zeros|ones|empty)$', MLFramework.NUMPY, "NumPy array creation"),

    # Scikit-learn
    (r'^sklearn\..+$', r'.*', MLFramework.SKLEARN, "Scikit-learn class"),
    (r'^sklearn$', r'.*', MLFramework.SKLEARN, "Scikit-learn"),

    # Joblib
    (r'^joblib\..+$', r'.*', MLFramework.JOBLIB, "Joblib class"),
    (r'^joblib$', r'.*', MLFramework.JOBLIB, "Joblib"),

    # SciPy
    (r'^scipy\..+$', r'.*', MLFramework.SCIPY, "SciPy class"),
    (r'^scipy$', r'.*', MLFramework.SCIPY, "SciPy"),

    # Pandas
    (r'^pandas\.core\..+$', r'.*', MLFramework.PANDAS, "Pandas core class"),
    (r'^pandas$', r'^(DataFrame|Series|Index)$', MLFramework.PANDAS, "Pandas data structure"),

    # XGBoost
    (r'^xgboost\..+$', r'.*', MLFramework.XGBOOST, "XGBoost class"),
    (r'^xgboost$', r'.*', MLFramework.XGBOOST, "XGBoost"),

    # LightGBM
    (r'^lightgbm\..+$', r'.*', MLFramework.LIGHTGBM, "LightGBM class"),
    (r'^lightgbm$', r'.*', MLFramework.LIGHTGBM, "LightGBM"),

    # CatBoost
    (r'^catboost\..+$', r'.*', MLFramework.CATBOOST, "CatBoost class"),
    (r'^catboost$', r'.*', MLFramework.CATBOOST, "CatBoost"),

    # HuggingFace Transformers
    (r'^transformers\..+$', r'.*', MLFramework.HUGGINGFACE, "HuggingFace Transformers class"),
    (r'^transformers$', r'.*', MLFramework.HUGGINGFACE, "HuggingFace Transformers"),

    # Standard library safe patterns
    (r'^collections$', r'^OrderedDict$', MLFramework.UNKNOWN, "OrderedDict"),
    (r'^collections$', r'^defaultdict$', MLFramework.UNKNOWN, "defaultdict"),
    (r'^collections$', r'^Counter$', MLFramework.UNKNOWN, "Counter"),
    (r'^collections$', r'^deque$', MLFramework.UNKNOWN, "deque"),
    (r'^collections$', r'^namedtuple$', MLFramework.UNKNOWN, "namedtuple"),
    (r'^copy$', r'^deepcopy$', MLFramework.UNKNOWN, "deepcopy"),
    (r'^copy_reg$', r'.*', MLFramework.UNKNOWN, "copy_reg (Python 2)"),
    (r'^copyreg$', r'.*', MLFramework.UNKNOWN, "copyreg"),
    (r'^datetime$', r'^(datetime|date|time|timedelta)$', MLFramework.UNKNOWN, "datetime"),
    (r'^decimal$', r'^Decimal$', MLFramework.UNKNOWN, "Decimal"),
    (r'^fractions$', r'^Fraction$', MLFramework.UNKNOWN, "Fraction"),
    (r'^functools$', r'^partial$', MLFramework.UNKNOWN, "functools.partial"),
    (r'^re$', r'^_compile$', MLFramework.UNKNOWN, "compiled regex"),
    (r'^_sre$', r'^compile$', MLFramework.UNKNOWN, "compiled regex"),
    (r'^uuid$', r'^UUID$', MLFramework.UNKNOWN, "UUID"),
    (r'^pathlib$', r'^(Pure)?(Posix|Windows)?Path$', MLFramework.UNKNOWN, "pathlib.Path"),
    (r'^enum$', r'.*', MLFramework.UNKNOWN, "enum"),
    (r'^dataclasses$', r'.*', MLFramework.UNKNOWN, "dataclass"),
]

# Compile patterns for efficiency
_COMPILED_PATTERNS = [
    (re.compile(mod), re.compile(name), framework, desc)
    for mod, name, framework, desc in SAFE_ML_PATTERNS
]


class MLPatternMatcher:
    """Matcher for ML framework patterns."""

    def __init__(self):
        self.patterns = _COMPILED_PATTERNS
        self.detected_frameworks: Set[MLFramework] = set()
        self.matches: List[MLPatternMatch] = []

    def match(self, module: str, name: str) -> Optional[MLPatternMatch]:
        """Try to match a callable against known ML patterns."""
        for mod_pattern, name_pattern, framework, desc in self.patterns:
            if mod_pattern.match(module) and name_pattern.match(name):
                match = MLPatternMatch(
                    framework=framework,
                    module=module,
                    name=name,
                    description=desc,
                    is_safe=True
                )
                self.matches.append(match)
                if framework != MLFramework.UNKNOWN:
                    self.detected_frameworks.add(framework)
                return match
        return None

    def match_global(self, ref: GlobalRef) -> Optional[MLPatternMatch]:
        """Match a GlobalRef against known patterns."""
        return self.match(ref.module, ref.name)

    def analyze_globals(self, globals_found: List[Tuple[GlobalRef, int]]) -> List[MLPatternMatch]:
        """Analyze all globals and return matches."""
        results = []
        for ref, _ in globals_found:
            match = self.match_global(ref)
            if match:
                results.append(match)
        return results

    def get_primary_framework(self) -> MLFramework:
        """Get the primary detected ML framework."""
        if MLFramework.PYTORCH in self.detected_frameworks:
            return MLFramework.PYTORCH
        elif MLFramework.SKLEARN in self.detected_frameworks:
            return MLFramework.SKLEARN
        elif MLFramework.NUMPY in self.detected_frameworks:
            return MLFramework.NUMPY
        elif MLFramework.HUGGINGFACE in self.detected_frameworks:
            return MLFramework.HUGGINGFACE
        elif self.detected_frameworks:
            return next(iter(self.detected_frameworks))
        return MLFramework.UNKNOWN


def is_safe_ml_pattern(module: str, name: str) -> Tuple[bool, Optional[str]]:
    """Check if a callable is a safe ML pattern."""
    for mod_pattern, name_pattern, _, desc in _COMPILED_PATTERNS:
        if mod_pattern.match(module) and name_pattern.match(name):
            return True, desc
    return False, None


def detect_ml_framework(globals_found: List[Tuple[GlobalRef, int]]) -> MLFramework:
    """Detect the ML framework from globals."""
    matcher = MLPatternMatcher()
    matcher.analyze_globals(globals_found)
    return matcher.get_primary_framework()
