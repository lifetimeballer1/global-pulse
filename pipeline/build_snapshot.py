#!/usr/bin/env python3
"""Compatibility entry point for the canonical Global Pulse refresh pipeline.

The repository previously had a stub clean pipeline which only rewrote the
manifest and could make GitHub Actions report a successful refresh without
actually collecting new intelligence.  Keep this entry point for callers,
but delegate all work to the production orchestrator at the repository root.
"""
from __future__ import annotations
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / "refresh_pipeline.py"), run_name="__main__")
