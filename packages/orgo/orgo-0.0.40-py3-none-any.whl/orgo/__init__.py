# src/orgo/__init__.py
"""Orgo SDK: Desktop infrastructure for AI agents"""

from .project import Project
from .computer import Computer
from .forge import Forge

# Workspace is an alias for Project (preferred name going forward)
Workspace = Project

__all__ = ["Project", "Workspace", "Computer", "Forge"]
