from sqlalchemy import select

from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository):
    async def create(self, user_id: str, title: str, duration_minutes: int | None = None) -> Task:
        task = Task(user_id=user_id, title=title, duration_minutes=duration_minutes)
        self._session.add(task)
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def list_for_user(self, user_id: str) -> list[Task]:
        result = await self._session.execute(
            select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc())
        )
        return list(result.scalars().all())

    async def set_status(self, task_id: str, user_id: str, status: str) -> Task | None:
        task = await self._session.get(Task, task_id)
        if task is None or str(task.user_id) != user_id:
            return None
        task.status = status
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def delete(self, task_id: str, user_id: str) -> bool:
        task = await self._session.get(Task, task_id)
        if task is None or str(task.user_id) != user_id:
            return False
        await self._session.delete(task)
        await self._session.commit()
        return True

    async def find_by_title(self, user_id: str, title: str) -> Task | None:
        """Case-insensitive substring match — a voice user can't supply a
        task id, and speech transcription rarely reproduces a title exactly.
        Prefers not-done tasks, since "complete X" almost always means the
        open task, not one already marked done."""
        result = await self._session.execute(
            select(Task)
            .where(Task.user_id == user_id, Task.title.ilike(f"%{title}%"))
            .order_by(Task.status != "completed", Task.created_at.desc())
        )
        return result.scalars().first()
