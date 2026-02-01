"""
Cortex MCP - Intelligent Long-Term Memory Server for LLMs

Zero-Effort, Zero-Trust, Zero-Loss

A Model Context Protocol (MCP) server that provides persistent memory
capabilities for Large Language Models, enabling seamless context
preservation across sessions.

Usage:
    pip install cortex-mcp
    cortex-mcp --license YOUR-LICENSE-KEY

Features:
    - Smart Context: Lazy loading with 70% token savings
    - Reference History: AI-powered context recommendations
    - Hybrid RAG: Semantic + keyword search
    - Git Integration: Auto-sync with git branches
    - Cloud Sync: Encrypted backup to Google Drive
    - Plan A/B: Auto/semi-auto mode based on user feedback

GitHub: https://github.com/syab726/cortex
"""

__version__ = "1.0.5"
__author__ = "Cortex Team"
__email__ = "beta@cortex-mcp.com"
__license__ = "MIT"

from .core.license_manager import LicenseManager, LicenseStatus, LicenseType, get_license_manager
from .core.memory_manager import MemoryManager

__all__ = [
    "__version__",
    "MemoryManager",
    "LicenseManager",
    "get_license_manager",
    "LicenseType",
    "LicenseStatus",
]
