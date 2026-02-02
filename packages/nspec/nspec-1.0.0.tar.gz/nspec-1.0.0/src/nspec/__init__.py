"""Nspec validator - strict fRIMPL compliance checking.

This package provides comprehensive validation for Feature Requests (FR)
and Implementation Plans (IMPL) documents, enforcing format requirements,
dependency relationships, and task tracking.

Architecture:
    validators.py - Format validation (Layer 1)
    datasets.py - Dataset loading (Layer 2)
    checkers.py - Cross-document validation (Layers 3-6)
    tasks.py - Task parsing and progress tracking
    cli.py - Command-line interface
    __main__.py - Entry point

Usage:
    python -m src.tools.nspec --validate
    python -m src.tools.nspec --generate
    python -m src.tools.nspec --progress [spec_id]
"""

from nspec.datasets import DatasetLoader, NspecDatasets
from nspec.tasks import Task, TaskParser
from nspec.validators import FRValidator, IMPLValidator

__all__ = [
    "FRValidator",
    "IMPLValidator",
    "NspecDatasets",
    "DatasetLoader",
    "Task",
    "TaskParser",
]
