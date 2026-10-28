import random
import string
from typing import List, Set


class TaskManager:
    active_tasks: Set[str] = set()

    @staticmethod
    def generate_task_id(length: int = 8) -> str:
        chars = string.ascii_letters + string.digits
        return "".join(random.choice(chars) for _ in range(length))

    @classmethod
    def start_task(cls) -> str:
        task_id = cls.generate_task_id()
        cls.active_tasks.add(task_id)
        return task_id

    @classmethod
    def end_task(cls, task_id: str) -> None:
        cls.active_tasks.discard(task_id)

    @classmethod
    def is_active(cls, task_id: str) -> bool:
        return task_id in cls.active_tasks

    @classmethod
    def get_active_tasks(cls) -> List[str]:
        """
        Mengembalikan daftar task ID yang aktif.
        """
        return list(cls.active_tasks)


task = TaskManager()
