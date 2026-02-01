"""
Cortex Function Decorator System

This module provides decorators that enforce internal automation
when user triggers a function.

Core Principle (from new_goal.md):
- Triggering (when): User's responsibility
- Execution (what/how): Cortex's absolute responsibility

When user calls a function (e.g., "login 구현해줘"):
1. Decorator auto-loads relevant context (Python enforced)
2. AI executes function with injected context
3. Decorator auto-saves result (Python enforced - finally block)
4. Decorator auto-records reference (Python enforced - finally block)

All internal operations are guaranteed by Python code.
"""

import logging
import time
import json
import re
import os
from functools import wraps
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

# Cortex core imports (will be loaded at runtime to avoid circular imports)
_memory_manager = None
_reference_history = None
_context_manager = None
_rag_engine = None
_telemetry_client = None

logger = logging.getLogger(__name__)


def _lazy_import():
    """
    Lazy import Cortex core modules to avoid circular import issues.
    Called only when decorator is first used.
    """
    global _memory_manager, _reference_history, _context_manager, _rag_engine, _telemetry_client

    if _memory_manager is None:
        try:
            from . import memory_manager as mm
            from . import reference_history as rh
            from . import context_manager as cm
            from . import rag_engine as re_module

            _memory_manager = mm
            _reference_history = rh
            _context_manager = cm
            _rag_engine = re_module

            # Telemetry (optional)
            try:
                from . import telemetry_client as tc
                _telemetry_client = tc
                logger.info("[DECORATOR] Telemetry client imported")
            except ImportError:
                _telemetry_client = None
                logger.info("[DECORATOR] Telemetry not available")

            logger.info("[DECORATOR] Lazy import completed")
        except Exception as e:
            logger.error(f"[DECORATOR] Lazy import failed: {e}")
            raise


def _extract_keywords(func_name: str, args: tuple, kwargs: dict) -> List[str]:
    """
    Extract keywords from function name and arguments.

    Example:
        implement_feature("login 구현") -> ["login", "구현", "implement", "feature"]

    Args:
        func_name: Function name (e.g., "implement_feature")
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        List of extracted keywords
    """
    keywords = []

    # Extract from function name (camelCase or snake_case)
    func_words = re.findall(r'[A-Z][a-z]+|[a-z]+', func_name)
    keywords.extend(func_words)

    # Extract from first string argument (usually task description)
    if args and isinstance(args[0], str):
        # Simple tokenization: split by spaces and special chars
        tokens = re.findall(r'\w+', args[0])
        keywords.extend(tokens)

    # Extract from 'description' or 'query' keyword arguments
    for key in ['description', 'query', 'task', 'prompt']:
        if key in kwargs and isinstance(kwargs[key], str):
            tokens = re.findall(r'\w+', kwargs[key])
            keywords.extend(tokens)

    # Remove duplicates while preserving order
    unique_keywords = []
    seen = set()
    for kw in keywords:
        if kw.lower() not in seen:
            unique_keywords.append(kw.lower())
            seen.add(kw.lower())

    return unique_keywords[:10]  # Limit to top 10 keywords


def _emergency_save(func_name: str, result: Any, error: Optional[Exception],
                    project_id: str, branch_id: str):
    """
    Emergency save to local file when update_memory fails.

    This is the last resort to prevent data loss.
    Saves to ~/.cortex/emergency_saves/

    Args:
        func_name: Function that was executed
        result: Function result (may be None if error occurred)
        error: Exception that occurred (if any)
        project_id: Project ID
        branch_id: Branch ID
    """
    import os
    from pathlib import Path

    try:
        emergency_dir = Path.home() / ".cortex" / "emergency_saves"
        emergency_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{project_id}_{func_name}_{timestamp}.json"
        filepath = emergency_dir / filename

        data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "project_id": project_id,
            "branch_id": branch_id,
            "function": func_name,
            "result": str(result) if result else None,
            "error": str(error) if error else None,
            "error_type": type(error).__name__ if error else None
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.critical(f"[EMERGENCY_SAVE] Saved to {filepath}")
        print(f"[EMERGENCY_SAVE] Data saved to emergency file: {filepath}")

    except Exception as e:
        logger.critical(f"[EMERGENCY_SAVE] Even emergency save failed: {e}")
        print(f"[EMERGENCY_SAVE] CRITICAL: Even emergency save failed: {e}")


def cortex_function(
    auto_load_context: bool = True,
    auto_save: bool = True,
    auto_record: bool = True,
    project_id: Optional[str] = None,
    branch_id: Optional[str] = None
):
    """
    Decorator that enforces internal automation when user triggers a function.

    When user calls decorated function (e.g., "login 구현해줘"):
    1. PHASE 1 (BEFORE function): Auto-load context
       - Extract keywords from arguments
       - Query Reference History
       - Load suggested contexts
       - Search previous conversations
       - Inject all into _cortex_context parameter

    2. PHASE 2: Execute AI function with injected context

    3. PHASE 3 (AFTER function, in finally): Auto-save and auto-record
       - update_memory (100% guaranteed via finally)
       - record_reference (100% guaranteed via finally)

    Args:
        auto_load_context: If True, automatically load relevant contexts before function
        auto_save: If True, automatically save result after function (via finally)
        auto_record: If True, automatically record reference history (via finally)
        project_id: Project ID (if None, will try to get from kwargs)
        branch_id: Branch ID (if None, will try to get from kwargs)

    Example:
        @cortex_function(auto_load_context=True, auto_save=True)
        def implement_feature(description: str, _cortex_context=None):
            # At this point, Decorator has already:
            # ✅ Extracted keywords: ["login", "구현"]
            # ✅ Queried Reference History: ["auth.py", "user.py"]
            # ✅ Loaded auth.py, user.py automatically
            # ✅ Searched previous conversations: "JWT 방식 사용"
            # ✅ Injected all into _cortex_context

            context = _cortex_context or {}
            # AI sees:
            # - context['loaded_files']: [auth.py content, user.py content]
            # - context['previous_conversations']: ["JWT 방식 사용하기로 함"]
            # - context['previous_work']: "Previous login work used auth.py, user.py"

            code = generate_code(context)
            return code

            # After function returns, Decorator automatically:
            # ✅ Saves work to update_memory (via finally)
            # ✅ Records reference history (via finally)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Lazy import on first use
            _lazy_import()

            func_name = func.__name__
            start_time = time.time()

            # Get project_id and branch_id from kwargs or use defaults
            _project_id = kwargs.get('project_id', project_id)
            _branch_id = kwargs.get('branch_id', branch_id)

            if not _project_id:
                logger.warning(f"[DECORATOR] {func_name}: project_id not provided, auto features disabled")
                # If no project_id, just execute function without automation
                return func(*args, **kwargs)

            # ========================================
            # PHASE 1: Auto Context Loading (BEFORE function)
            # ========================================
            loaded_contexts = []
            previous_conversations = []
            suggestions = {}
            keywords = []

            if auto_load_context:
                logger.info(f"[DECORATOR] {func_name}: Starting auto context loading")

                try:
                    # 1. Extract keywords from arguments
                    keywords = _extract_keywords(func_name, args, kwargs)
                    logger.info(f"[DECORATOR] {func_name}: Extracted keywords: {keywords}")

                    # 2. Query Reference History (Python enforced)
                    if _reference_history and keywords:
                        try:
                            query_str = " ".join(keywords)
                            suggestions = _reference_history.suggest(
                                query=query_str,
                                project_id=_project_id,
                                branch_id=_branch_id,
                                top_k=5
                            )
                            logger.info(f"[DECORATOR] {func_name}: Reference History suggestions: {suggestions.get('contexts', [])}")
                        except Exception as e:
                            logger.warning(f"[DECORATOR] {func_name}: Reference History query failed: {e}")

                    # 3. Auto-load suggested contexts (Python enforced)
                    if suggestions and suggestions.get('contexts'):
                        for ctx_id in suggestions['contexts'][:3]:  # Limit to top 3
                            try:
                                ctx = _context_manager.load_context(
                                    context_id=ctx_id,
                                    project_id=_project_id,
                                    branch_id=_branch_id
                                )
                                loaded_contexts.append(ctx)
                                logger.info(f"[DECORATOR] {func_name}: Loaded context: {ctx_id}")
                            except Exception as e:
                                logger.warning(f"[DECORATOR] {func_name}: Context load failed {ctx_id}: {e}")

                    # 4. Search previous conversations (Python enforced)
                    if _rag_engine and keywords:
                        try:
                            query_str = " ".join(keywords)
                            prev = _rag_engine.search(
                                query=query_str,
                                project_id=_project_id,
                                branch_id=_branch_id,
                                top_k=3
                            )
                            previous_conversations = prev.get('results', [])
                            logger.info(f"[DECORATOR] {func_name}: Found {len(previous_conversations)} previous conversations")
                        except Exception as e:
                            logger.warning(f"[DECORATOR] {func_name}: Previous conversation search failed: {e}")

                    # 5. Inject context into AI function
                    injected_context = {
                        'loaded_files': loaded_contexts,
                        'previous_work': suggestions,
                        'previous_conversations': previous_conversations,
                        'keywords': keywords,
                        'auto_loaded': True,
                        'timestamp': datetime.utcnow().isoformat() + "Z"
                    }
                    kwargs['_cortex_context'] = injected_context

                    logger.info(f"[DECORATOR] {func_name}: Context injection complete")
                    logger.info(f"[DECORATOR] {func_name}: - Loaded files: {len(loaded_contexts)}")
                    logger.info(f"[DECORATOR] {func_name}: - Previous conversations: {len(previous_conversations)}")

                except Exception as e:
                    logger.error(f"[DECORATOR] {func_name}: Auto context loading failed: {e}")
                    # Continue execution even if context loading fails

            # ========================================
            # PHASE 2: Execute AI Function
            # ========================================
            result = None
            error = None

            try:
                logger.info(f"[DECORATOR] {func_name}: Executing function")
                result = func(*args, **kwargs)
                logger.info(f"[DECORATOR] {func_name}: Function execution completed")
            except Exception as e:
                error = e
                logger.error(f"[DECORATOR] {func_name}: Function execution error: {e}")

            # ========================================
            # PHASE 3: Auto Save (AFTER function, guaranteed by finally)
            # ========================================
            finally:
                execution_time = time.time() - start_time

                # 6. Auto-save work content (100% guaranteed)
                if auto_save and _memory_manager:
                    try:
                        # Prepare content summary
                        content_parts = [
                            f"Function: {func_name}",
                            f"Execution time: {execution_time:.2f}s"
                        ]

                        if keywords:
                            content_parts.append(f"Keywords: {', '.join(keywords)}")

                        if loaded_contexts:
                            ctx_ids = [ctx.get('id', 'unknown') for ctx in loaded_contexts]
                            content_parts.append(f"Loaded contexts: {', '.join(ctx_ids)}")

                        if result:
                            result_preview = str(result)[:200]
                            content_parts.append(f"Result: {result_preview}")

                        if error:
                            content_parts.append(f"Error: {type(error).__name__}: {str(error)}")

                        content = "\n".join(content_parts)

                        # Create MemoryManager instance for this project
                        mm_instance = _memory_manager.MemoryManager(project_id=_project_id)

                        # Prepare context for Phase 9 hallucination detection
                        verification_context = {
                            "project_id": _project_id,
                            "function_name": func_name,
                            "execution_time": execution_time,
                            "project_path": os.getcwd()
                        }

                        mm_instance.update_memory(
                            project_id=_project_id,
                            branch_id=_branch_id,
                            content=content,
                            role="assistant",
                            verified=False,  # Enable Phase 9 hallucination detection
                            context=verification_context
                        )
                        logger.info(f"[AUTO_SAVE] {func_name}: Saved to memory")

                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        logger.critical(f"[AUTO_SAVE] {func_name}: Failed: {e}")
                        # Emergency save as last resort
                        _emergency_save(func_name, result, error, _project_id, _branch_id or "unknown")

                # 7. Auto-record reference history (100% guaranteed)
                if auto_record and _reference_history and loaded_contexts and not error:
                    try:
                        contexts_used = [ctx.get('id') for ctx in loaded_contexts if ctx.get('id')]

                        if contexts_used:
                            # Create ReferenceHistory instance for this project
                            rh_instance = _reference_history.ReferenceHistory(project_id=_project_id)
                            rh_instance.record_reference(
                                project_id=_project_id,
                                branch_id=_branch_id,
                                task_keywords=keywords,
                                contexts_used=contexts_used,
                                query=" ".join(keywords) if keywords else func_name
                            )
                            logger.info(f"[AUTO_RECORD] {func_name}: Reference history recorded")
                    except Exception as e:
                        logger.warning(f"[AUTO_RECORD] {func_name}: Failed: {e}")

            if error:
                raise error

            return result

        return wrapper
    return decorator


def async_cortex_function(
    auto_load_context: bool = True,
    auto_save: bool = True,
    auto_record: bool = True,
    project_id: Optional[str] = None,
    branch_id: Optional[str] = None
):
    """
    Async-compatible version of cortex_function decorator.

    Enforces internal automation when user triggers an async function.
    Identical to cortex_function but works with async def functions.

    When user calls decorated async function:
    1. PHASE 1 (BEFORE function): Auto-load context
       - Extract keywords from arguments
       - Query Reference History
       - Load suggested contexts
       - Search previous conversations
       - Inject all into _cortex_context parameter

    2. PHASE 2: Execute async AI function with injected context

    3. PHASE 3 (AFTER function, in finally): Auto-save and auto-record
       - update_memory (100% guaranteed via finally)
       - record_reference (100% guaranteed via finally)

    Args:
        auto_load_context: If True, automatically load relevant contexts before function
        auto_save: If True, automatically save result after function (via finally)
        auto_record: If True, automatically record reference history (via finally)
        project_id: Project ID (if None, will try to get from kwargs)
        branch_id: Branch ID (if None, will try to get from kwargs)

    Example:
        @async_cortex_function(auto_load_context=True, auto_save=True)
        async def call_tool(name: str, arguments: dict, _cortex_context=None):
            # At this point, Decorator has already:
            # ✅ Extracted keywords
            # ✅ Queried Reference History
            # ✅ Loaded suggested contexts automatically
            # ✅ Searched previous conversations
            # ✅ Injected all into _cortex_context

            context = _cortex_context or {}
            result = await process_tool(name, arguments, context)
            return result

            # After function returns, Decorator automatically:
            # ✅ Saves work to update_memory (via finally)
            # ✅ Records reference history (via finally)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Lazy import on first use
            _lazy_import()

            func_name = func.__name__
            start_time = time.time()

            # Get project_id and branch_id from kwargs or args (MCP pattern support)
            # MCP tools pattern: async def call_tool(name: str, arguments: dict)
            # where arguments dict contains project_id and branch_id
            _project_id = kwargs.get('project_id', project_id)
            _branch_id = kwargs.get('branch_id', branch_id)

            # If not in kwargs, check args[1] for MCP-style arguments dict
            if not _project_id and len(args) > 1 and isinstance(args[1], dict):
                arguments_dict = args[1]
                _project_id = arguments_dict.get('project_id')
                _branch_id = arguments_dict.get('branch_id')


            if not _project_id:
                logger.warning(f"[DECORATOR] {func_name}: project_id not provided, auto features disabled")
                # If no project_id, just execute function without automation
                return await func(*args, **kwargs)

            # ========================================
            # PHASE 1: Auto Context Loading (BEFORE function)
            # ========================================
            loaded_contexts = []
            previous_conversations = []
            suggestions = {}
            keywords = []

            if auto_load_context:
                logger.info(f"[DECORATOR] {func_name}: Starting auto context loading")

                try:
                    # 1. Extract keywords from arguments
                    keywords = _extract_keywords(func_name, args, kwargs)
                    logger.info(f"[DECORATOR] {func_name}: Extracted keywords: {keywords}")

                    # 2. Query Reference History (sync function)
                    if _reference_history and keywords:
                        try:
                            query_str = " ".join(keywords)
                            suggestions = _reference_history.suggest(
                                query=query_str,
                                project_id=_project_id,
                                branch_id=_branch_id,
                                top_k=5
                            )
                            logger.info(f"[DECORATOR] {func_name}: Reference History suggestions: {suggestions.get('contexts', [])}")
                        except Exception as e:
                            logger.warning(f"[DECORATOR] {func_name}: Reference History query failed: {e}")

                    # 3. Auto-load suggested contexts (sync function)
                    if suggestions and suggestions.get('contexts'):
                        for ctx_id in suggestions['contexts'][:3]:  # Limit to top 3
                            try:
                                ctx = _context_manager.load_context(
                                    context_id=ctx_id,
                                    project_id=_project_id,
                                    branch_id=_branch_id
                                )
                                loaded_contexts.append(ctx)
                                logger.info(f"[DECORATOR] {func_name}: Loaded context: {ctx_id}")
                            except Exception as e:
                                logger.warning(f"[DECORATOR] {func_name}: Context load failed {ctx_id}: {e}")

                    # 4. Search previous conversations (sync function)
                    if _rag_engine and keywords:
                        try:
                            query_str = " ".join(keywords)
                            prev = _rag_engine.search(
                                query=query_str,
                                project_id=_project_id,
                                branch_id=_branch_id,
                                top_k=3
                            )
                            previous_conversations = prev.get('results', [])
                            logger.info(f"[DECORATOR] {func_name}: Found {len(previous_conversations)} previous conversations")
                        except Exception as e:
                            logger.warning(f"[DECORATOR] {func_name}: Previous conversation search failed: {e}")

                    # 5. Inject context into AI function
                    injected_context = {
                        'loaded_files': loaded_contexts,
                        'previous_work': suggestions,
                        'previous_conversations': previous_conversations,
                        'keywords': keywords,
                        'auto_loaded': True,
                        'timestamp': datetime.utcnow().isoformat() + "Z"
                    }
                    kwargs['_cortex_context'] = injected_context

                    logger.info(f"[DECORATOR] {func_name}: Context injection complete")
                    logger.info(f"[DECORATOR] {func_name}: - Loaded files: {len(loaded_contexts)}")
                    logger.info(f"[DECORATOR] {func_name}: - Previous conversations: {len(previous_conversations)}")

                except Exception as e:
                    logger.error(f"[DECORATOR] {func_name}: Auto context loading failed: {e}")
                    # Continue execution even if context loading fails

            # ========================================
            # PHASE 2: Execute Async Function
            # ========================================
            result = None
            error = None

            try:
                logger.info(f"[DECORATOR] {func_name}: Executing async function")
                result = await func(*args, **kwargs)  # AWAIT async function
                logger.info(f"[DECORATOR] {func_name}: Function execution completed")
            except Exception as e:
                error = e
                logger.error(f"[DECORATOR] {func_name}: Function execution error: {e}")

            # ========================================
            # PHASE 3: Auto Save (AFTER function, guaranteed by finally)
            # ========================================
            finally:
                execution_time = time.time() - start_time

                # 6. Auto-save work content (100% guaranteed)
                if auto_save and _memory_manager:
                    try:
                        # Prepare content summary
                        content_parts = [
                            f"Function: {func_name}",
                            f"Execution time: {execution_time:.2f}s"
                        ]

                        if keywords:
                            content_parts.append(f"Keywords: {', '.join(keywords)}")

                        if loaded_contexts:
                            ctx_ids = [ctx.get('id', 'unknown') for ctx in loaded_contexts]
                            content_parts.append(f"Loaded contexts: {', '.join(ctx_ids)}")

                        if result:
                            result_preview = str(result)[:200]
                            content_parts.append(f"Result: {result_preview}")

                        if error:
                            content_parts.append(f"Error: {type(error).__name__}: {str(error)}")

                        content = "\n".join(content_parts)

                        # Create MemoryManager instance for this project
                        mm_instance = _memory_manager.MemoryManager(project_id=_project_id)

                        # Prepare context for Phase 9 hallucination detection
                        verification_context = {
                            "project_id": _project_id,
                            "function_name": func_name,
                            "execution_time": execution_time,
                            "project_path": os.getcwd()
                        }

                        mm_instance.update_memory(
                            project_id=_project_id,
                            branch_id=_branch_id,
                            content=content,
                            role="assistant",
                            verified=False,  # Enable Phase 9 hallucination detection
                            context=verification_context
                        )
                        logger.info(f"[AUTO_SAVE] {func_name}: Saved to memory")

                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        logger.critical(f"[AUTO_SAVE] {func_name}: Failed: {e}")
                        # Emergency save as last resort
                        _emergency_save(func_name, result, error, _project_id, _branch_id or "unknown")

                # 7. Auto-record reference history (100% guaranteed)
                if auto_record and _reference_history and loaded_contexts and not error:
                    try:
                        contexts_used = [ctx.get('id') for ctx in loaded_contexts if ctx.get('id')]

                        if contexts_used:
                            # Create ReferenceHistory instance for this project
                            rh_instance = _reference_history.ReferenceHistory(project_id=_project_id)
                            rh_instance.record_reference(
                                project_id=_project_id,
                                branch_id=_branch_id,
                                task_keywords=keywords,
                                contexts_used=contexts_used,
                                query=" ".join(keywords) if keywords else func_name
                            )
                            logger.info(f"[AUTO_RECORD] {func_name}: Reference history recorded")
                    except Exception as e:
                        logger.warning(f"[AUTO_RECORD] {func_name}: Failed: {e}")

                # 8. Telemetry recording (100% guaranteed, non-blocking)
                if _telemetry_client:
                    try:
                        # Determine module name from MCP tool name
                        # MCP tools pattern: async def call_tool(name: str, arguments: dict)
                        tool_name = args[0] if args else func_name
                        module_map = {
                            "update_memory": "memory_manager",
                            "create_branch": "memory_manager",
                            "search_context": "rag_engine",
                            "get_active_summary": "memory_manager",
                            "initialize_context": "memory_manager",
                            "load_context": "context_manager",
                            "suggest_contexts": "reference_history",
                            "create_snapshot": "backup_manager",
                            "restore_snapshot": "backup_manager",
                            "link_git_branch": "git_sync",
                        }
                        module_name = module_map.get(tool_name, "general")

                        success = error is None
                        latency_ms = execution_time * 1000

                        _telemetry_client.record_call(
                            module_name=module_name,
                            success=success,
                            latency_ms=latency_ms
                        )

                        # Record error if function failed
                        if error:
                            _telemetry_client.record_error(
                                error_type=type(error).__name__,
                                error_message=str(error),
                                tool_name=tool_name,
                                severity="error"
                            )

                        logger.info(f"[TELEMETRY] {func_name}: Recorded (module={module_name}, success={success}, latency={latency_ms:.1f}ms)")
                    except Exception as e:
                        logger.warning(f"[TELEMETRY] {func_name}: Failed: {e}")

            if error:
                raise error

            return result

        return async_wrapper
    return decorator


# Example usage (for documentation purposes)
if __name__ == "__main__":
    # This is just an example, actual usage will be in cortex_tools.py

    @cortex_function(auto_load_context=True, auto_save=True)
    def implement_feature(description: str, project_id: str, branch_id: str,
                         _cortex_context: Optional[Dict] = None):
        """
        Example function showing how decorator works.

        User triggers: "login 기능 구현해줘"

        At this point, Decorator has already:
        ✅ Extracted keywords: ["login", "기능", "구현"]
        ✅ Queried Reference History: ["auth.py", "user.py"]
        ✅ Loaded auth.py, user.py automatically
        ✅ Searched previous conversations: "JWT 방식 사용"
        ✅ Injected all into _cortex_context

        After function returns, Decorator automatically:
        ✅ Saves work to update_memory
        ✅ Records reference history
        """
        context = _cortex_context or {}

        # AI sees:
        # - context['loaded_files']: [auth.py content, user.py content]
        # - context['previous_conversations']: ["JWT 방식 사용하기로 함"]
        # - context['previous_work']: "Previous login work used auth.py, user.py"

        print(f"Implementing: {description}")
        print(f"Context loaded: {len(context.get('loaded_files', []))} files")
        print(f"Previous work: {context.get('previous_work', {}).get('tier', 'none')}")

        # AI writes code using provided context
        code = f"// {description} implementation\n// Using context: {context.get('keywords', [])}"

        return code
