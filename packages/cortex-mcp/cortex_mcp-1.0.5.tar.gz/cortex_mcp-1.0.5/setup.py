#!/usr/bin/env python3
"""
setup.py for cortex-mcp

This file provides backward compatibility for tools that don't fully support
PEP 517/518 (pyproject.toml-only builds).

Modern Python packaging (Python 3.11+) should use pyproject.toml directly.
This file simply delegates to setuptools' pyproject.toml support.
"""

from setuptools import setup

# All configuration is in pyproject.toml
# This setup.py exists only for backward compatibility
if __name__ == "__main__":
    setup()
