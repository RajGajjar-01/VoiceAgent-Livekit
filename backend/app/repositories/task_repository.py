from sqlalchemy import select

from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository):
    async def create(self, user_id: str, title: str) -> Task:
        task = Task(user_id=user_id, title=title)
        self._session.add(task)
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def list_for_user(self, user_id: str) -> list[Task]:
        result = await self._session.execute(
            select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc())
        )
        return list(result.scalars().all())

    async def mark_done(self, task_id: str, user_id: str) -> Task | None:
        task = await self._session.get(Task, task_id)
        if task is None or str(task.user_id) != user_id:
            return None
        task.done = True
        await self._session.commit()
        await self._session.refresh(task)
        return task
