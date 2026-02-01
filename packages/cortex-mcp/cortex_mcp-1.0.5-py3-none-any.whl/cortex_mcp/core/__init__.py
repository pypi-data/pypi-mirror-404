"""
Cortex MCP - Core Modules
"""

from .automation_manager import AutomationManager, get_automation_manager
from .backup_manager import BackupManager, get_backup_manager
from .cloud_sync import CloudSync
from .context_manager import ContextManager, context_manager
from .crypto_utils import CryptoUtils
from .git_sync import GitSync, get_git_sync
from .memory_manager import MemoryManager
from .rag_engine import RAGEngine
from .reference_history import ReferenceHistory, get_reference_history

__all__ = [
    "MemoryManager",
    "RAGEngine",
    "CloudSync",
    "CryptoUtils",
    "ContextManager",
    "context_manager",
    "ReferenceHistory",
    "get_reference_history",
    "GitSync",
    "get_git_sync",
    "BackupManager",
    "get_backup_manager",
    "AutomationManager",
    "get_automation_manager",
]
