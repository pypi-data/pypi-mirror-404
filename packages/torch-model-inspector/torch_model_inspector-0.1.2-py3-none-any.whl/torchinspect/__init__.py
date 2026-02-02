"""Lightweight utilities for inspecting PyTorch model shapes."""

from .core import (
    AnalyzeResult,
    LayerRecord,
    analyze,
    count_parameters,
    print_report,
    suggest_fixes,
)

__all__ = [
    "LayerRecord",
    "AnalyzeResult",
    "analyze",
    "suggest_fixes",
    "print_report",
    "count_parameters",
]
