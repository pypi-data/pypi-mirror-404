"""
Task Store Module
==================

Provides SQLite-vec based task storage with vector embeddings for semantic task search.
Handles database initialization, task CRUD operations, and vector search.
"""

import asyncio
import sqlite3
import sqlite_vec
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from zoneinfo import ZoneInfo

from .models import Task, TaskStatus, TaskStats, Config, Priority, decimal_hours_to_hhmm, hhmm_to_minutes, minutes_to_hhmm, hhmm_add, is_decimal_hours_format
from .security import (
    SecurityError, sanitize_input, validate_task_status,
    validate_task_params, validate_task_update_params,
    generate_content_hash, validate_file_path, validate_parent_id,
    validate_bulk_tasks_params, validate_bulk_task_ids
)
from .embeddings import get_embedding_model, EmbeddingModel


class TaskStore:
    """Thread-safe task storage using sqlite-vec for semantic search."""

    def __init__(self, db_path: Path, embedding_model_name: str = None, timezone: str = None):
        """
        Initialize task store.

        Args:
            db_path: Path to SQLite database file
            embedding_model_name: Name of embedding model to use
            timezone: Timezone for timestamp storage (default: UTC)
        """
        self.db_path = Path(db_path)
        self.embedding_model_name = embedding_model_name or Config.EMBEDDING_MODEL
        self.timezone = timezone or "UTC"

        # Lazy-loaded embedding model (async initialization)
        self._embedding_model: EmbeddingModel | None = None
        self._model_loading_task: asyncio.Task | None = None

        # Lazy-loaded database initialization (async)
        self._db_initialized: bool = False
        self._db_init_task: asyncio.Task | None = None

        # Validate database path
        validate_file_path(self.db_path)

    async def _ensure_db_initialized_async(self) -> None:
        """
        Ensure database is initialized with async lazy loading.

        Creates asyncio.Task on first call for background initialization.
        All concurrent callers await the SAME task (no duplicate initialization).
        """
        if self._db_initialized:
            return

        if self._db_init_task is None:
            self._db_init_task = asyncio.create_task(
                asyncio.to_thread(self._init_database)
            )

        await self._db_init_task
        self._db_initialized = True

    def _ensure_db_initialized_sync(self) -> None:
        """
        Ensure database is initialized with synchronous loading (fallback for non-async contexts).

        Blocks if database not yet initialized (synchronous fallback).
        """
        if not self._db_initialized:
            self._init_database()
            self._db_initialized = True

    async def get_embedding_model_async(self) -> EmbeddingModel:
        """
        Get embedding model with async lazy loading.

        Returns cached model if already loaded.
        Creates asyncio.Task on first call for background loading.
        All concurrent callers await the SAME task (no duplicate loading).

        Returns:
            EmbeddingModel instance
        """
        if self._embedding_model is not None:
            return self._embedding_model

        if self._model_loading_task is None:
            self._model_loading_task = asyncio.create_task(
                asyncio.to_thread(get_embedding_model, self.embedding_model_name)
            )

        self._embedding_model = await self._model_loading_task
        return self._embedding_model

    def _get_embedding_model_sync(self) -> EmbeddingModel:
        """
        Get embedding model with synchronous loading (fallback for non-async contexts).

        Returns cached model if already loaded.
        Blocks if model not yet loaded (synchronous fallback).

        Returns:
            EmbeddingModel instance
        """
        if self._embedding_model is None:
            self._embedding_model = get_embedding_model(self.embedding_model_name)
        return self._embedding_model

    @property
    def embedding_model(self) -> EmbeddingModel:
        """
        Property for backwards compatibility.

        Provides synchronous access to embedding model.
        Use get_embedding_model_async() for async contexts.

        Returns:
            EmbeddingModel instance
        """
        return self._get_embedding_model_sync()

    def _init_database(self) -> None:
        """Initialize sqlite-vec database with required tables."""
        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize task store: {e}")

        try:
            # Create tasks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_id INTEGER,
                    status TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    comment TEXT,
                    content_hash TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL,
                    start_at TEXT,
                    finish_at TEXT
                )
            """)

            # Migration: Add comment column if it doesn't exist
            cursor = conn.execute("PRAGMA table_info(tasks)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'comment' not in columns:
                conn.execute("ALTER TABLE tasks ADD COLUMN comment TEXT")

            # Migration: Add priority column if it doesn't exist
            cursor = conn.execute("PRAGMA table_info(tasks)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'priority' not in columns:
                conn.execute("ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'")

            # Migration: Add tags column if it doesn't exist
            cursor = conn.execute("PRAGMA table_info(tasks)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'tags' not in columns:
                conn.execute("ALTER TABLE tasks ADD COLUMN tags TEXT")

            # Migration: Add estimate column if it doesn't exist
            cursor = conn.execute("PRAGMA table_info(tasks)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'estimate' not in columns:
                conn.execute("ALTER TABLE tasks ADD COLUMN estimate REAL")

            # Migration: Add order column if it doesn't exist
            cursor = conn.execute("PRAGMA table_info(tasks)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'order' not in columns:
                conn.execute('ALTER TABLE tasks ADD COLUMN "order" INTEGER')

            # Migration: Add time_spent column if it doesn't exist
            cursor = conn.execute("PRAGMA table_info(tasks)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'time_spent' not in columns:
                conn.execute("ALTER TABLE tasks ADD COLUMN time_spent REAL DEFAULT 0.0")

            # Create vector table using vec0
            conn.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS task_vectors USING vec0(
                    embedding float[{Config.EMBEDDING_DIM}]
                );
            """)

            # Create task_time_log table for time tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_time_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    start_status TEXT NOT NULL,
                    finish_status TEXT,
                    time_spent REAL DEFAULT 0.0,
                    start_at TEXT NOT NULL,
                    finish_at TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_status ON tasks(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_created ON tasks(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_parent ON tasks(parent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_hash ON tasks(content_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_priority ON tasks(status, priority, created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_tags ON tasks(tags)")
            conn.execute('CREATE INDEX IF NOT EXISTS idx_task_parent_order ON tasks(parent_id, "order")')
            conn.execute("CREATE INDEX IF NOT EXISTS idx_time_log_task_id ON task_time_log(task_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_time_log_incomplete ON task_time_log(task_id) WHERE finish_at IS NULL")

            # Additional indexes for CRM filtering performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_start_at ON tasks(start_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_finish_at ON tasks(finish_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_estimate ON tasks(estimate)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_status_parent ON tasks(status, parent_id)")
            conn.execute('CREATE INDEX IF NOT EXISTS idx_task_order ON tasks("order")')
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_time_spent ON tasks(time_spent)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_time_log_start_at ON task_time_log(start_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_time_log_finish_at ON task_time_log(finish_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_time_log_finish_status ON task_time_log(finish_status)")

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to initialize database: {e}")
        finally:
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get SQLite connection with sqlite-vec loaded."""
        conn = sqlite3.connect(str(self.db_path))
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        # Enable WAL mode for safe concurrent access
        conn.execute("PRAGMA journal_mode=WAL")
        # Enable foreign key enforcement
        conn.execute("PRAGMA foreign_keys = ON")
        conn.enable_load_extension(False)
        return conn

    def _propagate_time_to_parents(self, conn: sqlite3.Connection, task_id: int, time_delta: float) -> None:
        """
        Recursively propagate time_delta to all parent tasks.

        Args:
            conn: Active database connection (must be within transaction)
            task_id: Current task ID
            time_delta: Time to propagate in HH.MM format
        """
        if time_delta <= 0:
            return

        # Get parent_id of current task
        cursor = conn.execute('SELECT parent_id FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if not row or not row[0]:  # No parent
            return

        parent_id = row[0]

        # Fetch current parent time_spent
        cursor = conn.execute(
            'SELECT time_spent FROM tasks WHERE id = ?',
            (parent_id,)
        )
        parent_row = cursor.fetchone()
        current_parent_time = parent_row[0] if parent_row and parent_row[0] else 0.0

        # Auto-convert old decimal hours format to HH.MM if needed
        if current_parent_time > 0 and is_decimal_hours_format(current_parent_time):
            current_parent_time = decimal_hours_to_hhmm(current_parent_time)

        # Calculate new time_spent using HH.MM arithmetic
        new_parent_time = hhmm_add(current_parent_time, time_delta)

        # Update parent's time_spent
        conn.execute(
            'UPDATE tasks SET time_spent = ? WHERE id = ?',
            (new_parent_time, parent_id)
        )
        # Recursively propagate to grandparent
        self._propagate_time_to_parents(conn, parent_id, time_delta)

    def _propagate_completed_to_parents(self, conn: sqlite3.Connection, task_id: int) -> None:
        """
        Recursively propagate 'completed' status to parent tasks when ALL children are finished.

        Rules:
        - Parent gets 'completed' ONLY when ALL children are in finish statuses (completed/tested/validated)
        - Recursively propagates up the parent chain with same check at each level

        Args:
            conn: Active database connection (must be within transaction)
            task_id: Current task ID whose status just changed to a finish status
        """
        # Get parent_id of current task
        cursor = conn.execute('SELECT parent_id FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if not row or not row[0]:  # No parent
            return

        parent_id = row[0]
        finish_statuses = TaskStatus.finish_statuses()

        # Check if ALL children of parent are in finish statuses
        placeholders = ','.join('?' * len(finish_statuses))
        cursor = conn.execute(f'''
            SELECT COUNT(*) FROM tasks
            WHERE parent_id = ? AND status NOT IN ({placeholders})
        ''', (parent_id, *finish_statuses))
        non_finished = cursor.fetchone()[0]

        if non_finished == 0:
            # All children finished → set parent to 'completed'
            conn.execute('UPDATE tasks SET status = ? WHERE id = ?', ('completed', parent_id))
            # Recursively check grandparent
            self._propagate_completed_to_parents(conn, parent_id)

    def _propagate_pending_to_parents(self, conn: sqlite3.Connection, task_id: int) -> None:
        """
        Recursively propagate 'pending' status to parent tasks when ANY child returns to pending.

        Rules:
        - Parent gets 'pending' when ANY child becomes 'pending'
        - Recursively propagates up the parent chain

        Args:
            conn: Active database connection (must be within transaction)
            task_id: Current task ID whose status just changed to 'pending'
        """
        # Get parent_id of current task
        cursor = conn.execute('SELECT parent_id FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if not row or not row[0]:  # No parent
            return

        parent_id = row[0]

        # Set parent to 'pending' unconditionally
        conn.execute('UPDATE tasks SET status = ? WHERE id = ?', ('pending', parent_id))
        # Recursively propagate to grandparent
        self._propagate_pending_to_parents(conn, parent_id)

    def _start_time_session(self, conn: sqlite3.Connection, task_id: int, start_status: str) -> None:
        """
        Create new time session record in task_time_log table.
        Only creates session for the specified task (no parent propagation).

        Args:
            conn: Active database connection (must be within transaction)
            task_id: Task ID to create session for
            start_status: Status at session start (typically 'in_progress')
        """
        now = datetime.now(timezone.utc).isoformat()

        try:
            conn.execute('''
                INSERT INTO task_time_log (task_id, start_status, start_at, time_spent)
                VALUES (?, ?, ?, 0.0)
            ''', (task_id, start_status, now))
        except Exception as e:
            raise RuntimeError(f"Failed to start time session for task {task_id}: {e}")

    def _finish_time_session(self, conn: sqlite3.Connection, task_id: int, time_spent: float, finish_status: str) -> None:
        """
        Complete existing time session record in task_time_log table.
        Only completes session for the specified task (no parent propagation).

        Args:
            conn: Active database connection (must be within transaction)
            task_id: Task ID to finish session for
            time_spent: Time spent in HH.MM format (e.g., 1.30 = 1 hour 30 minutes)
            finish_status: Status at session finish (e.g., completed, stopped, tested)
        """
        now = datetime.now(timezone.utc).isoformat()

        try:
            # Find incomplete session for this task
            cursor = conn.execute('''
                SELECT id FROM task_time_log
                WHERE task_id = ? AND finish_at IS NULL
                LIMIT 1
            ''', (task_id,))

            session = cursor.fetchone()

            # If no incomplete session found, return silently (no error)
            if not session:
                return

            # Update session with finish_at, time_spent, and finish_status
            conn.execute('''
                UPDATE task_time_log
                SET finish_at = ?, time_spent = ?, finish_status = ?
                WHERE id = ?
            ''', (now, time_spent, finish_status, session[0]))
        except Exception as e:
            raise RuntimeError(f"Failed to finish time session for task {task_id}: {e}")

    def _get_status_history(self, conn: sqlite3.Connection, task_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get status transition history from task_time_log.
        Includes both completed and incomplete (open) sessions.
        Open sessions appear first with to/at/spent as null.

        Args:
            conn: Database connection
            task_id: Task ID to get history for
            limit: Maximum records to return (default 5)

        Returns:
            List of dicts with keys: from, to, at, spent
            Ordered by: open sessions first, then finish_at DESC
        """
        cursor = conn.execute(
            """
            SELECT start_status, finish_status, finish_at, time_spent
            FROM task_time_log
            WHERE task_id = ?
            ORDER BY
                CASE WHEN finish_at IS NULL THEN 0 ELSE 1 END,
                finish_at DESC
            LIMIT ?
            """,
            (task_id, limit)
        )

        history = []
        for row in cursor.fetchall():
            history.append({
                "from": row[0],
                "to": row[1],
                "at": row[2],
                "spent": row[3]
            })

        return history

    def create_task(
        self,
        title: str,
        content: str,
        parent_id: Optional[int] = None,
        comment: Optional[str] = None,
        priority: Optional[str] = None,
        tags: Optional[List[str]] = None,
        estimate: Optional[float] = None,
        order: Optional[int] = None,
        embedding_model: Optional[EmbeddingModel] = None
    ) -> Dict[str, Any]:
        """
        Create a new task with vector embedding.

        Args:
            title: Task title
            content: Task content
            parent_id: Optional parent task ID for subtasks
            comment: Optional comment/note for the task
            priority: Optional priority level (low, medium, high, critical)
            tags: Optional list of tags for categorization
            estimate: Optional time estimate in hours
            order: Optional order position (auto-assigned if None, shifts siblings if provided)
            embedding_model: Optional pre-loaded embedding model (for async callers)

        Returns:
            Dict with operation result and task data
        """
        self._ensure_db_initialized_sync()
        # Use provided model or fall back to sync loading
        model = embedding_model or self._get_embedding_model_sync()
        # Validate parameters (including comment, priority, tags, and order)
        (title, content, _, validated_parent_id, validated_comment, validated_priority,
         validated_tags, validated_order) = validate_task_params(
            title, content, parent_id=parent_id, comment=comment, priority=priority, tags=tags, order=order
        )

        # Generate content hash from title + content (tags not included in hash)
        combined = f"{title}\n{content}\n{' '.join(validated_tags)}"
        content_hash = generate_content_hash(f"{title}\n{content}")

        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to create task: {e}")

        try:
            # Check if task already exists
            existing = conn.execute(
                "SELECT id FROM tasks WHERE content_hash = ?",
                (content_hash,)
            ).fetchone()

            if existing:
                return {
                    "success": False,
                    "message": "Task already exists",
                    "task_id": existing[0]
                }

            # Generate embedding from title + content
            embedding = model.encode_single(combined)

            # Calculate or validate order
            if validated_order is None:
                # Auto-assign: get next order for this parent
                cursor = conn.execute(
                    'SELECT COALESCE(MAX("order"), 0) + 1 FROM tasks WHERE parent_id IS ?',
                    (validated_parent_id,)
                )
                order_value = cursor.fetchone()[0]
            else:
                # Shift existing siblings to make room
                conn.execute(
                    'UPDATE tasks SET "order" = "order" + 1 WHERE parent_id IS ? AND "order" >= ?',
                    (validated_parent_id, validated_order)
                )
                order_value = validated_order

            # Store task
            now = datetime.now(ZoneInfo(self.timezone)).isoformat()
            cursor = conn.execute("""
                INSERT INTO tasks (parent_id, status, title, content, comment, priority, tags, content_hash, created_at, estimate, "order")
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (validated_parent_id, TaskStatus.PENDING.value, title, content, validated_comment, validated_priority, json.dumps(validated_tags), content_hash, now, estimate, order_value))

            task_id = cursor.lastrowid

            # Validate self-reference before committing
            validate_parent_id(task_id, validated_parent_id, conn)

            # Store vector using sqlite-vec serialization
            embedding_blob = sqlite_vec.serialize_float32(embedding)
            conn.execute(
                "INSERT INTO task_vectors (rowid, embedding) VALUES (?, ?)",
                (task_id, embedding_blob)
            )

            conn.commit()

            return {
                "success": True,
                "task_id": task_id,
                "title": title,
                "content": content,
                "comment": validated_comment,
                "priority": validated_priority,
                "tags": validated_tags,
                "status": TaskStatus.PENDING.value,
                "created_at": now,
                "order": order_value
            }

        except SecurityError as e:
            conn.rollback()
            raise e
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to create task: {e}")
        finally:
            conn.close()

    def create_tasks_bulk(
        self,
        tasks: List[dict],
        embedding_model: Optional[EmbeddingModel] = None
    ) -> Dict[str, Any]:
        """
        Create multiple tasks in a single transaction with batch embedding generation.

        Args:
            tasks: List of task dictionaries, each containing:
                - title: Task title (required)
                - content: Task content (required)
                - parent_id: Optional parent task ID
                - comment: Optional comment/note
            embedding_model: Optional pre-loaded embedding model (for async callers)

        Returns:
            Dict with operation result:
                - success: True if all tasks created, False otherwise
                - created_task_ids: List of created task IDs
                - count: Number of tasks created
                - message: Success or error message
                - skipped: Optional list of skipped tasks (duplicates)

        Raises:
            SecurityError: If validation fails
            RuntimeError: If database operation fails
        """
        self._ensure_db_initialized_sync()
        # Use provided model or fall back to sync loading
        model = embedding_model or self._get_embedding_model_sync()
        # Validate parameters
        validated_tasks, _ = validate_bulk_tasks_params(tasks, Config.MAX_BULK_CREATE)

        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to create tasks: {e}")

        try:
            now = datetime.now(ZoneInfo(self.timezone)).isoformat()
            created_task_ids = []
            skipped_tasks = []
            task_insert_data = []
            combined_texts = []
            task_metadata = []

            # First pass: validate and prepare data
            for index, validated_tuple in enumerate(validated_tasks):
                title, content, _, validated_parent_id, validated_comment, validated_priority, validated_tags, validated_order = validated_tuple

                # Generate content hash from title + content (tags not included)
                combined = f"{title}\n{content}\n{' '.join(validated_tags)}"
                content_hash = generate_content_hash(f"{title}\n{content}")

                # Check if task already exists
                existing = conn.execute(
                    "SELECT id FROM tasks WHERE content_hash = ?",
                    (content_hash,)
                ).fetchone()

                if existing:
                    skipped_tasks.append({
                        "index": index,
                        "task_id": existing[0],
                        "title": title[:50],
                        "reason": "Task already exists"
                    })
                    continue

                # Extract estimate and order from original task dict
                estimate = tasks[index].get("estimate") if index < len(tasks) else None
                order = tasks[index].get("order") if index < len(tasks) else None

                # Store metadata for later use
                task_metadata.append({
                    "title": title,
                    "content": content,
                    "parent_id": validated_parent_id,
                    "comment": validated_comment,
                    "priority": validated_priority,
                    "tags": validated_tags,
                    "content_hash": content_hash,
                    "estimate": estimate,
                    "order": validated_order if validated_order else order
                })

                combined_texts.append(combined)

            # If all tasks were skipped, return early
            if not task_metadata:
                return {
                    "success": True,
                    "created_task_ids": [],
                    "count": 0,
                    "message": f"No tasks created (all {len(skipped_tasks)} tasks already exist)",
                    "skipped": skipped_tasks
                }

            # Batch generate embeddings for all valid tasks
            embeddings = model.encode(combined_texts)

            # Second pass: insert tasks and vectors in single transaction
            for idx, metadata in enumerate(task_metadata):
                # Insert task
                cursor = conn.execute("""
                    INSERT INTO tasks (parent_id, status, title, content, comment, priority, tags, content_hash, created_at, estimate, "order")
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metadata["parent_id"],
                    TaskStatus.PENDING.value,
                    metadata["title"],
                    metadata["content"],
                    metadata["comment"],
                    metadata["priority"],
                    json.dumps(metadata["tags"]),
                    metadata["content_hash"],
                    now,
                    metadata["estimate"],
                    metadata["order"]
                ))

                task_id = cursor.lastrowid
                created_task_ids.append(task_id)

                # Validate self-reference before continuing
                validate_parent_id(task_id, metadata["parent_id"], conn)

                # Store vector using sqlite-vec serialization
                embedding_blob = sqlite_vec.serialize_float32(embeddings[idx])
                conn.execute(
                    "INSERT INTO task_vectors (rowid, embedding) VALUES (?, ?)",
                    (task_id, embedding_blob)
                )

            # Commit all operations
            conn.commit()

            result = {
                "success": True,
                "created_task_ids": created_task_ids,
                "count": len(created_task_ids),
                "message": f"Successfully created {len(created_task_ids)} task(s)"
            }

            if skipped_tasks:
                result["skipped"] = skipped_tasks
                result["message"] += f" ({len(skipped_tasks)} skipped as duplicates)"

            return result

        except SecurityError as e:
            conn.rollback()
            raise e
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to create tasks in bulk: {e}")
        finally:
            conn.close()

    def update_task(
        self,
        task_id: int,
        embedding_model: Optional[EmbeddingModel] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update an existing task.

        Args:
            task_id: Task ID to update
            embedding_model: Optional pre-loaded embedding model (for async callers, only used if title/content/tags change)
            **kwargs: Fields to update (title, content, status, parent_id, start_at, finish_at)

        Returns:
            Dict with updated task data
        """
        self._ensure_db_initialized_sync()
        # Validate parameters
        task_id, validated_kwargs = validate_task_update_params(task_id, **kwargs)

        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to update task: {e}")

        try:
            # Validate self-reference and parent existence if parent_id is being updated
            if 'parent_id' in validated_kwargs:
                validate_parent_id(task_id, validated_kwargs['parent_id'], conn)

            # Check if task exists
            existing = conn.execute(
                "SELECT id, title, content, status FROM tasks WHERE id = ?",
                (task_id,)
            ).fetchone()

            if not existing:
                return {
                    "success": False,
                    "message": f"Task {task_id} not found"
                }

            # Build UPDATE query dynamically
            update_fields = []
            update_values = []

            regenerate_embedding = False
            new_title = existing[1]
            new_content = existing[2]

            # Auto-set timestamps on status changes
            # Auto-calculate time_spent on status change to stopped/completed
            time_delta = 0.0  # Track time spent for parent propagation
            status_changed = False
            new_status = None
            old_status = None  # Track old status for session management
            if 'status' in validated_kwargs:
                current_status = existing[3]  # status is 4th column (index 3)
                old_status = current_status  # Save old status before change
                new_status = validated_kwargs['status']
                status_changed = True

                finish_statuses = TaskStatus.finish_statuses()

                # Auto-convert old decimal hours format to HH.MM on any update
                cursor = conn.execute(
                    'SELECT time_spent FROM tasks WHERE id = ?',
                    (task_id,)
                )
                ts_row = cursor.fetchone()
                if ts_row and ts_row[0] is not None and ts_row[0] > 0:
                    old_time_spent = ts_row[0]
                    if is_decimal_hours_format(old_time_spent):
                        converted_time_spent = decimal_hours_to_hhmm(old_time_spent)
                        update_fields.append('"time_spent" = ?')
                        update_values.append(converted_time_spent)

                # Auto-set start_at when changing to in_progress (only if not explicitly provided)
                if new_status == 'in_progress' and current_status != 'in_progress':
                    if 'start_at' not in validated_kwargs:
                        validated_kwargs['start_at'] = datetime.now(ZoneInfo(self.timezone)).isoformat()

                if new_status in finish_statuses and current_status not in finish_statuses:
                    # Finishing task (completed/tested/validated) - set finish_at timestamp (only if not explicitly provided)
                    if 'finish_at' not in validated_kwargs:
                        validated_kwargs['finish_at'] = datetime.now(ZoneInfo(self.timezone)).isoformat()
                elif new_status not in finish_statuses and current_status in finish_statuses:
                    # Un-finishing task - clear finish_at (only if not explicitly provided)
                    if 'finish_at' not in validated_kwargs:
                        validated_kwargs['finish_at'] = None

                # Calculate time_spent when changing to stopped or any finish status
                finish_and_stopped = finish_statuses + ('stopped',)
                if new_status in finish_and_stopped and current_status not in finish_and_stopped:
                    # Fetch current task's start_at and existing time_spent
                    cursor = conn.execute(
                        'SELECT start_at, time_spent FROM tasks WHERE id = ?',
                        (task_id,)
                    )
                    row = cursor.fetchone()

                    if row:
                        start_at_str = row[0]
                        current_time_spent = row[1] if row[1] is not None else 0.0

                        # Auto-convert old decimal hours format to HH.MM if needed
                        if current_time_spent > 0 and is_decimal_hours_format(current_time_spent):
                            current_time_spent = decimal_hours_to_hhmm(current_time_spent)

                        # Calculate time delta if start_at exists
                        if start_at_str:
                            start_at = datetime.fromisoformat(start_at_str)
                            now = datetime.now(ZoneInfo(self.timezone))
                            time_delta_hours = (now - start_at).total_seconds() / 3600

                            # Protect against negative time (e.g., if start_at was in future)
                            if time_delta_hours < 0:
                                time_delta_hours = 0.0

                            # Convert time_delta to HH.MM format
                            time_delta = decimal_hours_to_hhmm(time_delta_hours)

                        # Calculate new cumulative time_spent using HH.MM arithmetic
                        new_time_spent = hhmm_add(current_time_spent, time_delta)

                        # Add to update fields
                        update_fields.append('"time_spent" = ?')
                        update_values.append(new_time_spent)

            for key, value in validated_kwargs.items():
                if key == 'title':
                    update_fields.append("title = ?")
                    update_values.append(value)
                    new_title = value
                    regenerate_embedding = True
                elif key == 'content':
                    update_fields.append("content = ?")
                    update_values.append(value)
                    new_content = value
                    regenerate_embedding = True
                elif key == 'status':
                    update_fields.append("status = ?")
                    update_values.append(value)
                elif key == 'parent_id':
                    update_fields.append("parent_id = ?")
                    update_values.append(value)
                elif key == 'start_at':
                    update_fields.append("start_at = ?")
                    update_values.append(value)
                elif key == 'finish_at':
                    update_fields.append("finish_at = ?")
                    update_values.append(value)
                elif key == 'comment':
                    update_fields.append("comment = ?")
                    update_values.append(value)
                elif key == 'priority':
                    update_fields.append("priority = ?")
                    update_values.append(value)
                elif key == 'tags':
                    update_fields.append("tags = ?")
                    update_values.append(json.dumps(value))
                    regenerate_embedding = True
                elif key == 'estimate':
                    update_fields.append("estimate = ?")
                    update_values.append(value)
                elif key == 'order':
                    update_fields.append('"order" = ?')
                    update_values.append(value)

            # Handle order change with shift logic
            if 'order' in validated_kwargs and validated_kwargs['order'] is not None:
                new_order = validated_kwargs['order']

                # Get current task's order and parent_id
                cursor = conn.execute(
                    'SELECT "order", parent_id FROM tasks WHERE id = ?',
                    (task_id,)
                )
                current = cursor.fetchone()
                if current:
                    old_order, current_parent_id = current

                    # Determine parent_id (use new if being changed, else current)
                    target_parent_id = validated_kwargs.get('parent_id', current_parent_id)

                    if old_order != new_order or validated_kwargs.get('parent_id') is not None:
                        if validated_kwargs.get('parent_id') is not None and validated_kwargs['parent_id'] != current_parent_id:
                            # Moving to different parent - shift down old siblings, shift up new siblings
                            if old_order is not None:
                                conn.execute(
                                    'UPDATE tasks SET "order" = "order" - 1 WHERE parent_id IS ? AND "order" > ? AND id != ?',
                                    (current_parent_id, old_order, task_id)
                                )
                            conn.execute(
                                'UPDATE tasks SET "order" = "order" + 1 WHERE parent_id IS ? AND "order" >= ? AND id != ?',
                                (target_parent_id, new_order, task_id)
                            )
                        elif old_order is not None and old_order != new_order:
                            # Same parent, reordering
                            if new_order > old_order:
                                # Moving down: shift range up
                                conn.execute(
                                    'UPDATE tasks SET "order" = "order" - 1 WHERE parent_id IS ? AND "order" > ? AND "order" <= ? AND id != ?',
                                    (current_parent_id, old_order, new_order, task_id)
                                )
                            else:
                                # Moving up: shift range down
                                conn.execute(
                                    'UPDATE tasks SET "order" = "order" + 1 WHERE parent_id IS ? AND "order" >= ? AND "order" < ? AND id != ?',
                                    (current_parent_id, new_order, old_order, task_id)
                                )

            # If title, content, or tags changed, regenerate hash and embedding
            if regenerate_embedding:
                # Fetch current tags if tags not being updated
                if 'tags' not in validated_kwargs:
                    current_tags_row = conn.execute(
                        "SELECT tags FROM tasks WHERE id = ?",
                        (task_id,)
                    ).fetchone()
                    new_tags = json.loads(current_tags_row[0]) if current_tags_row[0] else []
                else:
                    new_tags = validated_kwargs['tags']

                combined = f"{new_title}\n{new_content}\n{' '.join(new_tags)}"
                new_hash = generate_content_hash(f"{new_title}\n{new_content}")
                update_fields.append("content_hash = ?")
                update_values.append(new_hash)

                # Generate new embedding (use provided model or fall back to sync loading)
                model = embedding_model or self._get_embedding_model_sync()
                embedding = model.encode_single(combined)
                embedding_blob = sqlite_vec.serialize_float32(embedding)

                # Update vector
                conn.execute(
                    "UPDATE task_vectors SET embedding = ? WHERE rowid = ?",
                    (embedding_blob, task_id)
                )

            # Execute update
            if update_fields:
                update_values.append(task_id)
                conn.execute(f"""
                    UPDATE tasks
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """, update_values)

            # Propagate time_delta to parent tasks (recursive)
            if time_delta > 0:
                self._propagate_time_to_parents(conn, task_id, time_delta)

            # Time session tracking - start/finish sessions on in_progress transitions
            if status_changed and old_status is not None:
                # Start session when entering in_progress
                if new_status == 'in_progress' and old_status != 'in_progress':
                    self._start_time_session(conn, task_id, old_status)
                # Finish session when exiting in_progress (always close, even with 0 time)
                elif old_status == 'in_progress' and new_status != 'in_progress':
                    self._finish_time_session(conn, task_id, time_delta, new_status)

            # Propagate 'completed' status to parent when ALL children are finished
            if status_changed and new_status in TaskStatus.finish_statuses():
                self._propagate_completed_to_parents(conn, task_id)

            # Propagate 'pending' status to parent when ANY child returns to pending
            if status_changed and new_status == 'pending':
                self._propagate_pending_to_parents(conn, task_id)

            conn.commit()

            # Fetch updated task
            result = conn.execute("""
                SELECT id, parent_id, status, priority, title, content, comment, tags, created_at, start_at, finish_at, content_hash, estimate, "order", time_spent
                FROM tasks
                WHERE id = ?
            """, (task_id,)).fetchone()

            task = Task.from_db_row(result)

            return {
                "success": True,
                "task": task.to_dict()
            }

        except SecurityError as e:
            conn.rollback()
            raise e
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to update task: {e}")
        finally:
            conn.close()

    def delete_task(self, task_id: int) -> bool:
        """
        Delete a task by ID.

        Args:
            task_id: Task ID to delete

        Returns:
            True if deleted, False if not found
        """
        self._ensure_db_initialized_sync()
        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to delete task: {e}")

        try:
            # Get task's order and parent_id for shift logic
            cursor = conn.execute(
                'SELECT parent_id, "order" FROM tasks WHERE id = ?',
                (task_id,)
            )
            task_info = cursor.fetchone()

            if not task_info:
                return False

            # Delete from both tables
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.execute("DELETE FROM task_vectors WHERE rowid = ?", (task_id,))

            # Shift remaining siblings down to close the gap
            parent_id, deleted_order = task_info
            if deleted_order is not None:
                conn.execute(
                    'UPDATE tasks SET "order" = "order" - 1 WHERE parent_id IS ? AND "order" > ?',
                    (parent_id, deleted_order)
                )

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to delete task: {e}")
        finally:
            conn.close()

    def delete_tasks_bulk(self, task_ids: List[int]) -> Dict[str, Any]:
        """
        Delete multiple tasks in a single transaction.

        Args:
            task_ids: List of task IDs to delete

        Returns:
            Dict with operation result:
                - success: True if all found tasks deleted, False otherwise
                - deleted_count: Number of tasks deleted
                - deleted_task_ids: List of deleted task IDs
                - message: Success or error message
                - not_found: Optional list of task IDs not found

        Raises:
            SecurityError: If validation fails
            RuntimeError: If database operation fails
        """
        self._ensure_db_initialized_sync()
        # Validate and deduplicate task IDs
        deduplicated_task_ids = validate_bulk_task_ids(task_ids, Config.MAX_BULK_DELETE)

        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to delete tasks: {e}")

        try:
            # Check which tasks exist
            placeholders = ','.join('?' * len(deduplicated_task_ids))
            existing_ids_query = f"SELECT id FROM tasks WHERE id IN ({placeholders})"
            existing_rows = conn.execute(existing_ids_query, deduplicated_task_ids).fetchall()
            existing_ids = [row[0] for row in existing_rows]

            # Determine which IDs were not found
            not_found_ids = [task_id for task_id in deduplicated_task_ids if task_id not in existing_ids]

            # If no tasks exist, return early
            if not existing_ids:
                return {
                    "success": False,
                    "deleted_count": 0,
                    "deleted_task_ids": [],
                    "message": f"No tasks found to delete (0 of {len(deduplicated_task_ids)})",
                    "not_found": not_found_ids
                }

            # Delete from both tables in single transaction
            delete_placeholders = ','.join('?' * len(existing_ids))

            conn.execute(
                f"DELETE FROM tasks WHERE id IN ({delete_placeholders})",
                existing_ids
            )

            conn.execute(
                f"DELETE FROM task_vectors WHERE rowid IN ({delete_placeholders})",
                existing_ids
            )

            conn.commit()

            result = {
                "success": True,
                "deleted_count": len(existing_ids),
                "deleted_task_ids": existing_ids,
                "message": f"Successfully deleted {len(existing_ids)} task(s)"
            }

            if not_found_ids:
                result["not_found"] = not_found_ids
                result["message"] += f" ({len(not_found_ids)} not found)"

            return result

        except SecurityError as e:
            conn.rollback()
            raise e
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to delete tasks in bulk: {e}")
        finally:
            conn.close()

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """
        Get a task by ID.

        Args:
            task_id: Task ID to retrieve

        Returns:
            Task object or None if not found
        """
        self._ensure_db_initialized_sync()
        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to get task: {e}")

        try:
            result = conn.execute("""
                SELECT id, parent_id, status, priority, title, content, comment, tags, created_at, start_at, finish_at, content_hash, estimate, "order", time_spent
                FROM tasks
                WHERE id = ?
            """, (task_id,)).fetchone()

            if result:
                task = Task.from_db_row(result)
                # Attach full status history for single task retrieval
                task.status_history = self._get_status_history(conn, task_id, limit=1000)
                return task
            return None

        except Exception as e:
            raise RuntimeError(f"Failed to get task by ID: {e}")
        finally:
            conn.close()

    def get_subtask_ids(self, parent_id: int) -> list[int]:
        """
        Get list of subtask IDs for a parent task.

        Args:
            parent_id: Parent task ID

        Returns:
            List of subtask IDs ordered by order ASC, created_at ASC
        """
        self._ensure_db_initialized_sync()
        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to get subtask IDs: {e}")

        try:
            results = conn.execute("""
                SELECT id
                FROM tasks
                WHERE parent_id = ?
                ORDER BY "order" ASC NULLS LAST, created_at ASC
            """, (parent_id,)).fetchall()

            return [row[0] for row in results]

        except Exception as e:
            raise RuntimeError(f"Failed to get subtask IDs: {e}")
        finally:
            conn.close()

    def get_next_child(self, parent_id: int) -> Optional[Task]:
        """
        Get the next child task to work on for a given parent.

        Logic (same as get_next_task but scoped to children):
        1. First check: any child with status="in_progress" → return first one
        2. If none in_progress: find last completed child, return first pending child created after it
        3. If no completed: return first pending child by order/created_at

        Args:
            parent_id: Parent task ID

        Returns:
            Task object or None if no suitable child task found
        """
        self._ensure_db_initialized_sync()
        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to get next child task: {e}")

        try:
            # First check for in_progress child tasks
            in_progress = conn.execute("""
                SELECT id, parent_id, status, priority, title, content, comment, tags, created_at, start_at, finish_at, content_hash, estimate, "order", time_spent
                FROM tasks
                WHERE status = ? AND parent_id = ?
                ORDER BY "order" ASC NULLS LAST, created_at ASC
                LIMIT 1
            """, (TaskStatus.IN_PROGRESS.value, parent_id)).fetchone()

            if in_progress:
                return Task.from_db_row(in_progress)

            # Find last finished child task (completed/tested/validated)
            finish_statuses = TaskStatus.finish_statuses()
            placeholders = ','.join('?' * len(finish_statuses))
            last_finished = conn.execute(f"""
                SELECT created_at
                FROM tasks
                WHERE status IN ({placeholders}) AND parent_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (*finish_statuses, parent_id)).fetchone()

            if last_finished:
                # Get first pending child task created after last finished
                next_pending = conn.execute("""
                    SELECT id, parent_id, status, priority, title, content, comment, tags, created_at, start_at, finish_at, content_hash, estimate, "order", time_spent
                    FROM tasks
                    WHERE status = ? AND parent_id = ? AND created_at > ?
                    ORDER BY "order" ASC NULLS LAST, CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 WHEN 'low' THEN 4 END, created_at ASC
                    LIMIT 1
                """, (TaskStatus.PENDING.value, parent_id, last_finished[0])).fetchone()

                if next_pending:
                    return Task.from_db_row(next_pending)

            # No completed child tasks or no pending after completed, get first pending child
            first_pending = conn.execute("""
                SELECT id, parent_id, status, priority, title, content, comment, tags, created_at, start_at, finish_at, content_hash, estimate, "order", time_spent
                FROM tasks
                WHERE status = ? AND parent_id = ?
                ORDER BY "order" ASC NULLS LAST, CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 WHEN 'low' THEN 4 END, created_at ASC
                LIMIT 1
            """, (TaskStatus.PENDING.value, parent_id)).fetchone()

            if first_pending:
                return Task.from_db_row(first_pending)

            return None

        except Exception as e:
            raise RuntimeError(f"Failed to get next child task: {e}")
        finally:
            conn.close()

    def get_last_task(self) -> Optional[Task]:
        """
        Get the most recently created task.

        Returns:
            Task object or None if no tasks exist
        """
        self._ensure_db_initialized_sync()
        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to get last task: {e}")

        try:
            result = conn.execute("""
                SELECT id, parent_id, status, priority, title, content, comment, tags, created_at, start_at, finish_at, content_hash, estimate, "order", time_spent
                FROM tasks
                ORDER BY created_at DESC
                LIMIT 1
            """).fetchone()

            if result:
                return Task.from_db_row(result)
            return None

        except Exception as e:
            raise RuntimeError(f"Failed to get last task: {e}")
        finally:
            conn.close()

    def get_next_task(self) -> Optional[Task]:
        """
        Get the next task to work on.

        Logic:
        1. First check: any tasks with status="in_progress" → return first one
        2. If none in_progress: find last completed task, then return first pending task created after it
        3. If no completed: return first pending task by created_at

        Returns:
            Task object or None if no suitable task found
        """
        self._ensure_db_initialized_sync()
        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to get next task: {e}")

        try:
            # First check for in_progress tasks
            in_progress = conn.execute("""
                SELECT id, parent_id, status, priority, title, content, comment, tags, created_at, start_at, finish_at, content_hash, estimate, "order", time_spent
                FROM tasks
                WHERE status = ?
                ORDER BY "order" ASC NULLS LAST, created_at ASC
                LIMIT 1
            """, (TaskStatus.IN_PROGRESS.value,)).fetchone()

            if in_progress:
                return Task.from_db_row(in_progress)

            # Find last finished task (completed/tested/validated)
            finish_statuses = TaskStatus.finish_statuses()
            placeholders = ','.join('?' * len(finish_statuses))
            last_finished = conn.execute(f"""
                SELECT created_at
                FROM tasks
                WHERE status IN ({placeholders})
                ORDER BY created_at DESC
                LIMIT 1
            """, finish_statuses).fetchone()

            if last_finished:
                # Get first pending task created after last finished
                next_pending = conn.execute("""
                    SELECT id, parent_id, status, priority, title, content, comment, tags, created_at, start_at, finish_at, content_hash, estimate, "order", time_spent
                    FROM tasks
                    WHERE status = ? AND created_at > ?
                    ORDER BY "order" ASC NULLS LAST, CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 WHEN 'low' THEN 4 END, created_at ASC
                    LIMIT 1
                """, (TaskStatus.PENDING.value, last_finished[0])).fetchone()

                if next_pending:
                    return Task.from_db_row(next_pending)

            # No completed tasks or no pending after completed, get first pending
            first_pending = conn.execute("""
                SELECT id, parent_id, status, priority, title, content, comment, tags, created_at, start_at, finish_at, content_hash, estimate, "order", time_spent
                FROM tasks
                WHERE status = ?
                ORDER BY "order" ASC NULLS LAST, CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 WHEN 'low' THEN 4 END, created_at ASC
                LIMIT 1
            """, (TaskStatus.PENDING.value,)).fetchone()

            if first_pending:
                return Task.from_db_row(first_pending)

            return None

        except Exception as e:
            raise RuntimeError(f"Failed to get next task: {e}")
        finally:
            conn.close()

    def search_tasks(
        self,
        query: str = None,
        limit: int = 10,
        offset: int = 0,
        status: str = None,
        parent_id: int = None,
        tags: List[str] = None,
        ids: List[int] = None,
        embedding_model: Optional[EmbeddingModel] = None
    ) -> Tuple[List[Task], int]:
        """
        Search tasks using vector similarity or list all with filters.

        Args:
            query: Optional search query for semantic search
            limit: Maximum number of results
            offset: Number of results to skip for pagination
            status: Optional status filter
            parent_id: Optional parent_id filter
            tags: Optional list of tags to filter by (OR logic - matches if ANY tag present)
            ids: Optional list of task IDs to filter by (AND logic with other filters)
            embedding_model: Optional pre-loaded embedding model (for async callers, only used if query provided)

        Returns:
            Tuple of (List of Task objects, total count matching filters)
        """
        self._ensure_db_initialized_sync()
        # Validate parameters
        if limit is not None:
            limit = min(max(1, limit), Config.MAX_MEMORIES_PER_SEARCH)
        else:
            limit = 10

        if offset is not None and (not isinstance(offset, int) or offset < 0):
            raise ValueError("offset must be a non-negative integer")
        if offset and offset > 10000:
            raise ValueError("offset must not exceed 10000")

        if status is not None:
            status = validate_task_status(status)

        if parent_id is not None and not isinstance(parent_id, int):
            raise ValueError("parent_id must be an integer")

        # Validate tags (optional)
        validated_tags = None
        if tags is not None:
            if not isinstance(tags, list):
                raise ValueError("tags must be a list")
            # Sanitize tags using existing sanitize_input
            validated_tags = []
            for tag in tags:
                if isinstance(tag, str) and tag.strip():
                    validated_tags.append(sanitize_input(tag.lower().strip(), 100))
            if not validated_tags:
                validated_tags = None  # Empty list = no filter

        # Validate ids (optional)
        validated_ids = None
        if ids is not None:
            if not isinstance(ids, list):
                raise ValueError("ids must be a list")
            validated_ids = []
            for task_id in ids:
                if not isinstance(task_id, int):
                    raise ValueError("All ids must be integers")
                validated_ids.append(task_id)
            if not validated_ids:
                validated_ids = None  # Empty list = no filter

        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to search tasks: {e}")

        try:
            # If query provided, do vector search
            if query:
                query = sanitize_input(query)

                # Generate query embedding
                # Use provided model or fall back to sync loading (only if query provided)
                model = embedding_model or self._get_embedding_model_sync()
                query_embedding = model.encode_single(query)
                query_blob = sqlite_vec.serialize_float32(query_embedding)

                # Build search query
                base_query = """
                    SELECT
                        t.id, t.parent_id, t.status, t.priority, t.title, t.content, t.comment, t.tags, t.created_at, t.start_at, t.finish_at, t.content_hash, t.estimate, t."order", t.time_spent,
                        vec_distance_cosine(v.embedding, ?) as distance
                    FROM tasks t
                    JOIN task_vectors v ON t.id = v.rowid
                """

                params = [query_blob]
                where_clauses = []

                # Add filters
                if status:
                    where_clauses.append("t.status = ?")
                    params.append(status)

                if parent_id is not None:
                    where_clauses.append("t.parent_id = ?")
                    params.append(parent_id)

                # Add tags filter if provided (OR logic - match ANY tag)
                if validated_tags:
                    tag_conditions = " OR ".join(["EXISTS (SELECT 1 FROM json_each(t.tags) WHERE value = ?)" for _ in validated_tags])
                    where_clauses.append(f"({tag_conditions})")
                    for tag in validated_tags:
                        params.append(tag)

                # Add ids filter if provided
                if validated_ids:
                    placeholders = ','.join(['?'] * len(validated_ids))
                    where_clauses.append(f"t.id IN ({placeholders})")
                    params.extend(validated_ids)

                # Add WHERE clause if filters exist
                if where_clauses:
                    base_query += " WHERE " + " AND ".join(where_clauses)

                # Get total count
                count_query = """
                    SELECT COUNT(DISTINCT t.id)
                    FROM tasks t
                    JOIN task_vectors v ON t.id = v.rowid
                """
                if where_clauses:
                    count_query += " WHERE " + " AND ".join(where_clauses)

                count_params = params[1:] if len(params) > 1 else []
                total_count = conn.execute(count_query, count_params).fetchone()[0]

                # Add ORDER BY, LIMIT, and OFFSET
                base_query += " ORDER BY distance LIMIT ? OFFSET ?"
                params.append(limit)
                params.append(offset)

                results = conn.execute(base_query, params).fetchall()

            else:
                # No query, just list with filters
                base_query = """
                    SELECT id, parent_id, status, priority, title, content, comment, tags, created_at, start_at, finish_at, content_hash, estimate, "order", time_spent
                    FROM tasks
                """

                params = []
                where_clauses = []

                if status:
                    where_clauses.append("status = ?")
                    params.append(status)

                if parent_id is not None:
                    where_clauses.append("parent_id = ?")
                    params.append(parent_id)

                # Add tags filter if provided (OR logic - match ANY tag)
                if validated_tags:
                    tag_conditions = " OR ".join(["EXISTS (SELECT 1 FROM json_each(tags) WHERE value = ?)" for _ in validated_tags])
                    where_clauses.append(f"({tag_conditions})")
                    for tag in validated_tags:
                        params.append(tag)

                # Add ids filter if provided
                if validated_ids:
                    placeholders = ','.join(['?'] * len(validated_ids))
                    where_clauses.append(f"id IN ({placeholders})")
                    params.extend(validated_ids)

                if where_clauses:
                    base_query += " WHERE " + " AND ".join(where_clauses)

                # Get total count
                count_query = "SELECT COUNT(*) FROM tasks"
                if where_clauses:
                    count_query += " WHERE " + " AND ".join(where_clauses)

                total_count = conn.execute(count_query, params).fetchone()[0]

                # Add ORDER BY, LIMIT, and OFFSET
                base_query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.append(limit)
                params.append(offset)

                results = conn.execute(base_query, params).fetchall()

            # Format results
            tasks = []
            for row in results:
                # Exclude distance column if present (vector search)
                task_row = row[:-1] if query else row
                tasks.append(Task.from_db_row(task_row))

            return (tasks, total_count)

        except SecurityError as e:
            raise e
        except Exception as e:
            raise RuntimeError(f"Failed to search tasks: {e}")
        finally:
            conn.close()

    def get_all_tags(self) -> List[str]:
        """
        Get all unique tags across all tasks.

        Returns:
            List[str]: Sorted list of unique tags
        """
        self._ensure_db_initialized_sync()
        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to get tags: {e}")

        try:
            # Get all non-null tags from database
            results = conn.execute("""
                SELECT tags
                FROM tasks
                WHERE tags IS NOT NULL AND tags != '[]'
            """).fetchall()

            # Parse JSON arrays and collect unique tags
            unique_tags = set()
            for row in results:
                if row[0]:
                    try:
                        tags_list = json.loads(row[0])
                        if isinstance(tags_list, list):
                            unique_tags.update(tags_list)
                    except (json.JSONDecodeError, TypeError):
                        continue

            # Return sorted list
            return sorted(list(unique_tags))

        except Exception as e:
            raise RuntimeError(f"Failed to get unique tags: {e}")
        finally:
            conn.close()

    def get_stats(
        self,
        created_after: str = None,
        created_before: str = None,
        start_after: str = None,
        start_before: str = None,
        finish_after: str = None,
        finish_before: str = None,
        status: str = None,
        priority: str = None,
        tags: List[str] = None,
        parent_id: int = None
    ) -> TaskStats:
        """
        Get task statistics with optional filters.

        Args:
            created_after: Filter tasks created after this timestamp (ISO 8601)
            created_before: Filter tasks created before this timestamp (ISO 8601)
            start_after: Filter tasks started after this timestamp (ISO 8601)
            start_before: Filter tasks started before this timestamp (ISO 8601)
            finish_after: Filter tasks finished after this timestamp (ISO 8601)
            finish_before: Filter tasks finished before this timestamp (ISO 8601)
            status: Filter by status (pending, in_progress, completed, tested, validated, stopped)
            priority: Filter by priority (low, medium, high, critical)
            tags: Filter by tags (OR logic - matches ANY tag in list)
            parent_id: Filter by parent_id (None for root tasks)

        Returns:
            TaskStats object with comprehensive statistics
        """
        self._ensure_db_initialized_sync()
        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to get stats: {e}")

        try:
            # Build WHERE clause dynamically
            where_clauses = []
            params = []

            # Date filters
            if created_after:
                where_clauses.append("created_at >= ?")
                params.append(created_after)
            if created_before:
                where_clauses.append("created_at <= ?")
                params.append(created_before)
            if start_after:
                where_clauses.append("start_at >= ?")
                params.append(start_after)
            if start_before:
                where_clauses.append("start_at <= ?")
                params.append(start_before)
            if finish_after:
                where_clauses.append("finish_at >= ?")
                params.append(finish_after)
            if finish_before:
                where_clauses.append("finish_at <= ?")
                params.append(finish_before)

            # Status filter
            if status:
                where_clauses.append("status = ?")
                params.append(status)

            # Priority filter
            if priority:
                where_clauses.append("priority = ?")
                params.append(priority)

            # Parent_id filter
            if parent_id is not None:
                if parent_id == 0:
                    # Filter for root tasks (parent_id IS NULL)
                    where_clauses.append("parent_id IS NULL")
                else:
                    where_clauses.append("parent_id = ?")
                    params.append(parent_id)

            # Tags filter (OR logic)
            if tags:
                tag_placeholders = ",".join(["?"] * len(tags))
                where_clauses.append(f"""
                    id IN (
                        SELECT t.id FROM tasks t, JSON_EACH(t.tags) AS tag
                        WHERE tag.value IN ({tag_placeholders})
                    )
                """)
                params.extend(tags)

            # Build final WHERE clause
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            # Total tasks
            total_tasks = conn.execute(
                f"SELECT COUNT(*) FROM tasks WHERE {where_sql}",
                params
            ).fetchone()[0]

            # Count by status
            status_counts = dict(conn.execute(
                f"""
                SELECT status, COUNT(*)
                FROM tasks
                WHERE {where_sql}
                GROUP BY status
                """,
                params
            ).fetchall())

            # Count by priority
            priority_counts = dict(conn.execute(
                f"""
                SELECT priority, COUNT(*)
                FROM tasks
                WHERE {where_sql}
                GROUP BY priority
                """,
                params
            ).fetchall())

            # Count tasks with subtasks (tasks that are parents)
            with_subtasks = conn.execute(
                f"""
                SELECT COUNT(DISTINCT parent_id)
                FROM tasks
                WHERE parent_id IS NOT NULL AND {where_sql}
                """,
                params
            ).fetchone()[0]

            # Root task count (parent_id IS NULL)
            root_task_count = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM tasks
                WHERE parent_id IS NULL AND {where_sql}
                """,
                params
            ).fetchone()[0]

            # Parent task count (tasks that have children)
            parent_task_count = conn.execute(
                f"""
                SELECT COUNT(DISTINCT parent_id)
                FROM tasks
                WHERE parent_id IS NOT NULL AND {where_sql}
                """,
                params
            ).fetchone()[0]

            # Estimate metrics
            estimate_row = conn.execute(
                f"""
                SELECT
                    SUM(estimate),
                    AVG(estimate)
                FROM tasks
                WHERE estimate IS NOT NULL AND {where_sql}
                """,
                params
            ).fetchone()
            total_estimate = estimate_row[0] or 0.0
            avg_estimate = estimate_row[1] or 0.0

            # Time spent metrics - fetch all time_spent values for proper HH.MM aggregation
            time_spent_rows = conn.execute(
                f"""
                SELECT time_spent
                FROM tasks
                WHERE time_spent > 0 AND {where_sql}
                    AND id NOT IN (SELECT DISTINCT parent_id FROM tasks WHERE parent_id IS NOT NULL)
                """,
                params
            ).fetchall()

            # Convert HH.MM to minutes, sum, then convert back
            if time_spent_rows:
                time_minutes = [hhmm_to_minutes(row[0]) for row in time_spent_rows if row[0]]
                total_minutes = sum(time_minutes)
                avg_minutes = total_minutes / len(time_minutes) if time_minutes else 0
                total_time_spent = minutes_to_hhmm(total_minutes)
                avg_time_spent = minutes_to_hhmm(int(avg_minutes))
            else:
                total_time_spent = 0.0
                avg_time_spent = 0.0

            # Overdue count - fetch tasks for overdue calculation (compare in minutes for HH.MM format)
            overdue_rows = conn.execute(
                f"""
                SELECT time_spent, estimate
                FROM tasks
                WHERE time_spent > 0
                    AND estimate IS NOT NULL
                    AND estimate > 0
                    AND {where_sql}
                    AND id NOT IN (SELECT DISTINCT parent_id FROM tasks WHERE parent_id IS NOT NULL)
                """,
                params
            ).fetchall()

            # Count overdue: time_spent (HH.MM) > estimate (hours) - convert both to minutes
            overdue_count = 0
            for time_spent_val, estimate_val in overdue_rows:
                time_minutes = hhmm_to_minutes(time_spent_val)
                estimate_minutes = int(estimate_val * 60)  # estimate is in decimal hours
                if time_minutes > estimate_minutes:
                    overdue_count += 1

            # Estimate accuracy calculation
            accuracy_rows = conn.execute(
                f"""
                SELECT estimate, time_spent
                FROM tasks
                WHERE estimate IS NOT NULL
                    AND time_spent > 0
                    AND {where_sql}
                    AND id NOT IN (SELECT DISTINCT parent_id FROM tasks WHERE parent_id IS NOT NULL)
                """,
                params
            ).fetchall()

            estimate_accuracy = 0.0
            if accuracy_rows:
                deviations = []
                for estimate, time_spent in accuracy_rows:
                    time_minutes = hhmm_to_minutes(time_spent)
                    estimate_minutes = int(estimate * 60)  # estimate is in decimal hours
                    if estimate_minutes > 0:
                        deviation_pct = abs(time_minutes - estimate_minutes) / estimate_minutes * 100
                        deviations.append(deviation_pct)
                avg_deviation = sum(deviations) / len(deviations)
                estimate_accuracy = 100 - avg_deviation

            # Tag usage
            tag_usage = {}
            tags_rows = conn.execute(
                f"""
                SELECT tags
                FROM tasks
                WHERE tags IS NOT NULL
                    AND tags != '[]'
                    AND {where_sql}
                """,
                params
            ).fetchall()

            for (tags_json,) in tags_rows:
                try:
                    task_tags = json.loads(tags_json)
                    if isinstance(task_tags, list):
                        for tag in task_tags:
                            tag_usage[tag] = tag_usage.get(tag, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    continue

            stats = TaskStats(
                total_tasks=total_tasks,
                by_status=status_counts,
                pending_count=status_counts.get(TaskStatus.PENDING.value, 0),
                in_progress_count=status_counts.get(TaskStatus.IN_PROGRESS.value, 0),
                completed_count=status_counts.get(TaskStatus.COMPLETED.value, 0),
                tested_count=status_counts.get(TaskStatus.TESTED.value, 0),
                validated_count=status_counts.get(TaskStatus.VALIDATED.value, 0),
                stopped_count=status_counts.get(TaskStatus.STOPPED.value, 0),
                canceled_count=status_counts.get(TaskStatus.CANCELED.value, 0),
                draft_count=status_counts.get(TaskStatus.DRAFT.value, 0),
                with_subtasks=with_subtasks,
                by_priority=priority_counts,
                root_task_count=root_task_count,
                parent_task_count=parent_task_count,
                total_estimate=total_estimate,
                total_time_spent=total_time_spent,
                avg_estimate=avg_estimate,
                avg_time_spent=avg_time_spent,
                overdue_count=overdue_count,
                estimate_accuracy=estimate_accuracy,
                tag_usage=tag_usage
            )

            return stats

        except Exception as e:
            raise RuntimeError(f"Failed to get statistics: {e}")
        finally:
            conn.close()
