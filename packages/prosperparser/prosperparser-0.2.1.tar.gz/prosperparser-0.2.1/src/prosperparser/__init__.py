"""
Copyright (c) 2026 Andrew Robbins. All rights reserved.

prosperparser: A package for filtering the output of ProsperousPlus.
"""

from __future__ import annotations

from . import cli
from ._version import version as __version__

__all__ = ["__version__"]

def run_cli():
    cli.run()
