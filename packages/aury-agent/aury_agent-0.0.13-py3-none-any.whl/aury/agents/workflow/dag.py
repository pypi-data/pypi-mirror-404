"""Generic DAG executor."""
from __future__ import annotations

from typing import Any, Callable, TypeVar

T = TypeVar("T")


class DAGExecutor:
    """Generic DAG parallel executor."""
    
    def __init__(
        self,
        tasks: list[T],
        get_task_id: Callable[[T], str],
        get_dependencies: Callable[[T], list[str]],
    ):
        self.tasks = {get_task_id(task): task for task in tasks}
        self.get_task_id = get_task_id
        self.get_dependencies = get_dependencies
        
        self.completed: set[str] = set()
        self.failed: set[str] = set()
        self.running: set[str] = set()
        self.skipped: set[str] = set()
    
    def get_ready_tasks(self) -> list[T]:
        """Get tasks ready for execution.
        
        A task is ready when all its dependencies are completed or skipped.
        If a dependency has failed, the task will never be ready.
        """
        ready = []
        processed = self.completed | self.failed | self.running | self.skipped
        
        for task_id, task in self.tasks.items():
            if task_id in processed:
                continue
            
            deps = self.get_dependencies(task)
            deps_satisfied = all(
                dep_id in (self.completed | self.skipped)
                for dep_id in deps
            )
            
            if deps_satisfied:
                ready.append(task)
        
        return ready
    
    def is_blocked(self) -> bool:
        """Check if DAG is blocked due to failed dependencies.
        
        Returns True if there are unprocessed tasks that can never run
        because their dependencies have failed.
        """
        if not self.failed:
            return False
        
        processed = self.completed | self.failed | self.running | self.skipped
        
        for task_id, task in self.tasks.items():
            if task_id in processed:
                continue
            
            # Check if any dependency has failed
            deps = self.get_dependencies(task)
            for dep_id in deps:
                if dep_id in self.failed:
                    return True
        
        return False
    
    def mark_running(self, task_id: str) -> None:
        self.running.add(task_id)
    
    def mark_completed(self, task_id: str) -> None:
        self.running.discard(task_id)
        self.completed.add(task_id)
    
    def mark_failed(self, task_id: str) -> None:
        self.running.discard(task_id)
        self.failed.add(task_id)
    
    def mark_skipped(self, task_id: str) -> None:
        self.skipped.add(task_id)
    
    def is_finished(self) -> bool:
        total_processed = len(self.completed) + len(self.failed) + len(self.skipped)
        return total_processed == len(self.tasks)
    
    def has_failures(self) -> bool:
        return len(self.failed) > 0
    
    def get_status(self) -> dict[str, Any]:
        pending = (
            len(self.tasks)
            - len(self.completed)
            - len(self.failed)
            - len(self.skipped)
            - len(self.running)
        )
        return {
            "total": len(self.tasks),
            "completed": len(self.completed),
            "failed": len(self.failed),
            "skipped": len(self.skipped),
            "running": len(self.running),
            "pending": pending,
        }
    
    def reset(self) -> None:
        self.completed.clear()
        self.failed.clear()
        self.running.clear()
        self.skipped.clear()
