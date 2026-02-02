"""
Vector Task MCP Server - Core Package
======================================

This package provides vector-based task management capabilities for Claude Desktop
using sqlite-vec and sentence-transformers.

Modules:
    models: Data models and type definitions
    security: Security utilities and validation
    embeddings: Sentence transformer wrapper (requires sentence-transformers)
    task_store: SQLite-vec operations and task storage (requires sqlite-vec)
"""

__version__ = "1.0.0"
__author__ = "Vector Task MCP Server"

# Core modules that don't require external dependencies
from .models import Task, TaskStatus, Priority, TaskStats, Config
from .security import SecurityError, validate_working_dir, sanitize_input

# Optional imports that require external dependencies
def get_embedding_model(model_name: str):
    """Get embedding model (requires sentence-transformers)"""
    from .embeddings import get_embedding_model as _get_model
    return _get_model(model_name)

def get_task_store(db_path, embedding_model_name=None):
    """Get task store (requires sqlite-vec)"""
    from .task_store import TaskStore
    return TaskStore(db_path, embedding_model_name)

__all__ = [
    "Task",
    "TaskStatus",
    "Priority",
    "TaskStats",
    "Config",
    "SecurityError",
    "validate_working_dir",
    "sanitize_input",
    "get_embedding_model",
    "get_task_store"
]
