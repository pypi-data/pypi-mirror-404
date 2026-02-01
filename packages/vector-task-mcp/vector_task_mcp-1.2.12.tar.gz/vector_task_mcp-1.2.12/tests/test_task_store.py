"""
TaskStore Unit Tests
====================

Tests for src/task_store.py including:
- Task CRUD operations
- Status propagation in hierarchies
- Deep hierarchy status propagation (4 levels)
- Parent-child relationship management
"""

import pytest
from unittest.mock import patch
from pathlib import Path


class TestDeepHierarchyStatusPropagation:
    """
    Test suite for deep hierarchy status propagation.

    Verifies that status changes in deeply nested tasks correctly
    propagate up through the entire parent chain to the root.

    Bug context (memory #72):
    - When deep nested subtasks complete (3+ levels deep), parent tasks
      at certain depths remained `in_progress` instead of updating correctly.
    - Fix: Continue recursion to grandparent even when siblings not finished.
    """

    def test_deep_hierarchy_tested_status_propagation(self, task_store, deep_hierarchy):
        """
        Test that 'tested' status propagates correctly and parents get 'completed'.

        Expected behavior:
        - Child with 'tested' status counts as finished
        - Parent should get 'completed' (not 'tested') when all children finish
        - This tests the fix for tested/validated status propagation
        """
        level0_id = deep_hierarchy['level0_id']
        level1_id = deep_hierarchy['level1_id']
        level2_id = deep_hierarchy['level2_id']
        level3_id = deep_hierarchy['level3_id']

        # Start and complete with 'tested' status at leaf
        task_store.update_task(level3_id, status='in_progress')
        task_store.update_task(level3_id, status='tested')

        # Verify all parents got 'completed' (not 'tested')
        for task_id, level_name in [
            (level2_id, "Level2"),
            (level1_id, "Level1"),
            (level0_id, "Root")
        ]:
            task = task_store.get_task_by_id(task_id)
            assert task.status == 'completed', (
                f"{level_name} (id={task_id}) should be 'completed' (not 'tested'). "
                f"Parent tasks always get 'completed' when children finish. "
                f"Actual status: {task.status}"
            )

    def test_deep_hierarchy_validated_status_propagation(self, task_store, deep_hierarchy):
        """
        Test that 'validated' status propagates correctly and parents get 'completed'.

        Same as tested, but with 'validated' status.
        """
        level0_id = deep_hierarchy['level0_id']
        level1_id = deep_hierarchy['level1_id']
        level2_id = deep_hierarchy['level2_id']
        level3_id = deep_hierarchy['level3_id']

        # Start and complete with 'validated' status at leaf
        task_store.update_task(level3_id, status='in_progress')
        task_store.update_task(level3_id, status='validated')

        # Verify all parents got 'completed' (not 'validated')
        for task_id, level_name in [
            (level2_id, "Level2"),
            (level1_id, "Level1"),
            (level0_id, "Root")
        ]:
            task = task_store.get_task_by_id(task_id)
            assert task.status == 'completed', (
                f"{level_name} should be 'completed' not 'validated'. "
                f"Actual: {task.status}"
            )


class TestStatusPropagationEdgeCases:
    """
    Edge case tests for status propagation.
    """

    def test_root_task_no_parent_propagation(self, task_store):
        """
        Test that root tasks (no parent) don't cause errors on status change.
        """
        root = task_store.create_task(
            title="Root Only",
            content="A standalone root task"
        )
        root_id = root['task_id']

        # Should not raise any errors
        task_store.update_task(root_id, status='in_progress')
        task = task_store.get_task_by_id(root_id)
        assert task.status == 'in_progress'

        task_store.update_task(root_id, status='completed')
        task = task_store.get_task_by_id(root_id)
        assert task.status == 'completed'

    def test_mixed_finish_statuses_complete_parent(self, task_store):
        """
        Test that parent completes when children have mixed finish statuses.

        Child1: completed
        Child2: tested
        Child3: validated

        Parent should become 'completed' when all are finished.
        """
        root = task_store.create_task(title="Root", content="Root task")
        root_id = root['task_id']

        child1 = task_store.create_task(
            title="Child 1", content="First", parent_id=root_id
        )
        child2 = task_store.create_task(
            title="Child 2", content="Second", parent_id=root_id
        )
        child3 = task_store.create_task(
            title="Child 3", content="Third", parent_id=root_id
        )

        # Complete children with different statuses
        task_store.update_task(child1['task_id'], status='in_progress')
        task_store.update_task(child1['task_id'], status='completed')

        task_store.update_task(child2['task_id'], status='in_progress')
        task_store.update_task(child2['task_id'], status='tested')

        task_store.update_task(child3['task_id'], status='in_progress')
        task_store.update_task(child3['task_id'], status='validated')

        # Root should be completed
        root_task = task_store.get_task_by_id(root_id)
        assert root_task.status == 'completed', (
            "Root should be 'completed' when all children have finish statuses. "
            f"Actual: {root_task.status}"
        )


class TestTaskCRUD:
    """
    Basic CRUD operation tests for TaskStore.
    """

    def test_create_task(self, task_store):
        """Test basic task creation."""
        result = task_store.create_task(
            title="Test Task",
            content="Test content"
        )

        assert result['success'] is True
        assert result['task_id'] > 0
        assert result['status'] == 'pending'

    def test_create_task_with_parent(self, task_store):
        """Test creating child task with parent_id."""
        parent = task_store.create_task(title="Parent", content="Parent content")
        child = task_store.create_task(
            title="Child",
            content="Child content",
            parent_id=parent['task_id']
        )

        assert child['success'] is True

        # Verify relationship
        child_task = task_store.get_task_by_id(child['task_id'])
        assert child_task.parent_id == parent['task_id']

    def test_update_task_status(self, task_store):
        """Test updating task status."""
        result = task_store.create_task(title="Task", content="Content")
        task_id = result['task_id']

        # Update to in_progress
        update_result = task_store.update_task(task_id, status='in_progress')
        assert update_result['success'] is True
        assert update_result['task']['status'] == 'in_progress'

    def test_delete_task(self, task_store):
        """Test task deletion."""
        result = task_store.create_task(title="To Delete", content="Will be deleted")
        task_id = result['task_id']

        deleted = task_store.delete_task(task_id)
        assert deleted is True

        # Verify task no longer exists
        task = task_store.get_task_by_id(task_id)
        assert task is None

    def test_get_task_by_id(self, task_store):
        """Test retrieving task by ID."""
        result = task_store.create_task(
            title="Retrieve Me",
            content="Content to retrieve",
            priority="high"
        )
        task_id = result['task_id']

        task = task_store.get_task_by_id(task_id)
        assert task is not None
        assert task.id == task_id
        assert task.title == "Retrieve Me"
        assert task.priority == "high"

    def test_get_nonexistent_task(self, task_store):
        """Test retrieving non-existent task returns None."""
        task = task_store.get_task_by_id(99999)
        assert task is None


class TestTaskSearch:
    """
    Tests for task search and filtering functionality.
    """

    def test_search_by_status(self, task_store, sample_task_data):
        """Test filtering tasks by status."""
        # Create tasks
        for data in sample_task_data:
            task_store.create_task(**data)

        # Get first task and set to in_progress
        tasks, _ = task_store.search_tasks(limit=10)
        if tasks:
            task_store.update_task(tasks[0].id, status='in_progress')

        # Search by status
        in_progress_tasks, count = task_store.search_tasks(status='in_progress')
        assert count >= 1
        for task in in_progress_tasks:
            assert task.status == 'in_progress'

    def test_search_by_parent_id(self, task_store, simple_hierarchy):
        """Test filtering tasks by parent_id."""
        root_id = simple_hierarchy['root_id']

        children, count = task_store.search_tasks(parent_id=root_id)
        assert count == 1
        assert children[0].parent_id == root_id

    def test_search_with_query(self, task_store, sample_task_data):
        """Test semantic search with query."""
        # Create tasks
        for data in sample_task_data:
            task_store.create_task(**data)

        # Search with query
        results, count = task_store.search_tasks(query="authentication security")
        assert count > 0


class TestTaskStats:
    """
    Tests for task statistics functionality.
    """

    def test_get_stats_empty_db(self, task_store):
        """Test stats on empty database."""
        stats = task_store.get_stats()
        assert stats.total_tasks == 0
        assert stats.pending_count == 0
        assert stats.in_progress_count == 0

    def test_get_stats_with_tasks(self, task_store, sample_task_data):
        """Test stats with existing tasks."""
        # Create tasks
        for data in sample_task_data:
            task_store.create_task(**data)

        stats = task_store.get_stats()
        assert stats.total_tasks == len(sample_task_data)
        assert stats.pending_count == len(sample_task_data)  # All start as pending


class TestBulkOperations:
    """
    Tests for bulk task operations.
    """

    def test_create_tasks_bulk(self, task_store):
        """Test bulk task creation."""
        tasks_to_create = [
            {"title": "Bulk Task 1", "content": "Content 1"},
            {"title": "Bulk Task 2", "content": "Content 2"},
            {"title": "Bulk Task 3", "content": "Content 3"},
        ]

        result = task_store.create_tasks_bulk(tasks_to_create)
        assert result['success'] is True
        assert result['count'] == 3
        assert len(result['created_task_ids']) == 3

    def test_delete_tasks_bulk(self, task_store):
        """Test bulk task deletion."""
        # Create tasks first
        task_ids = []
        for i in range(3):
            result = task_store.create_task(
                title=f"Delete Task {i}",
                content=f"Content {i}"
            )
            task_ids.append(result['task_id'])

        # Delete in bulk
        result = task_store.delete_tasks_bulk(task_ids)
        assert result['success'] is True
        assert result['deleted_count'] == 3

        # Verify all deleted
        for task_id in task_ids:
            task = task_store.get_task_by_id(task_id)
            assert task is None