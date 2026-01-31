"""Background task management."""

import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    """Status of a background task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskProgress:
    """Progress information for a background task."""

    task_id: str
    status: TaskStatus
    progress: int = 0  # 0-100
    speed: str = ""  # e.g., "5.2 MB/s"
    error: str | None = None
    result: Any = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "progress": self.progress,
            "speed": self.speed,
            "error": self.error,
            "result": self.result,
        }


@dataclass
class Task:
    """A background task."""

    task_id: str
    progress: TaskProgress
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    _task: asyncio.Task | None = None


class TaskManager:
    """Manages background tasks."""

    def __init__(self):
        self._tasks: dict[str, Task] = {}

    def create_task_id(self) -> str:
        """Generate a unique task ID."""
        return uuid.uuid4().hex[:12]

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def get_progress(self, task_id: str) -> TaskProgress | None:
        """Get task progress by ID."""
        task = self._tasks.get(task_id)
        return task.progress if task else None

    def create_task(self) -> Task:
        """Create a new task and register it."""
        task_id = self.create_task_id()
        progress = TaskProgress(task_id=task_id, status=TaskStatus.PENDING)
        task = Task(task_id=task_id, progress=progress)
        self._tasks[task_id] = task
        return task

    def start_task(self, task: Task, coro: asyncio.coroutines) -> None:
        """Start running a task coroutine."""
        task.progress.status = TaskStatus.RUNNING
        task._task = asyncio.create_task(self._run_task(task, coro))

    async def _run_task(self, task: Task, coro: asyncio.coroutines) -> None:
        """Run a task and update status on completion."""
        try:
            result = await coro
            if task.progress.status == TaskStatus.RUNNING:
                task.progress.status = TaskStatus.COMPLETED
                task.progress.progress = 100
                task.progress.result = result
        except asyncio.CancelledError:
            task.progress.status = TaskStatus.CANCELLED
        except Exception as e:
            task.progress.status = TaskStatus.FAILED
            task.progress.error = str(e)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.progress.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
            return False

        task.cancel_event.set()
        if task._task:
            task._task.cancel()

        task.progress.status = TaskStatus.CANCELLED
        return True

    def cleanup_task(self, task_id: str) -> None:
        """Remove a completed task from tracking."""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            if task.progress.status in (
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            ):
                del self._tasks[task_id]


# Global task manager instance
task_manager = TaskManager()
