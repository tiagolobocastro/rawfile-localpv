from concurrent.futures import Executor, Future
from enum import StrEnum
import shutil
from typing import Callable, TypedDict
import time
from config import config
from utils.snapshot_manager import manager as snapshot_manager
from utils.volume_manager import manager as volume_manager
from pathlib import Path
import json
import hashlib
from threading import Lock
from utils.logs import logger
import os


class TaskManagerShuttingDown(Exception):
    def __init__(self):
        super().__init__("Task Manager is shutting down")


class TaskName(StrEnum):
    CREATE_SNAPSHOT = "CreateSnapshot"
    CREATE_VOLUME = "CreateVolume"


class TaskState(StrEnum):
    PENDING = "Pending"
    RUNNING = "Running"
    FAILED = "Failed"
    COMPLETED = "Completed"


task_mapping: dict[TaskName, Callable] = {
    TaskName.CREATE_SNAPSHOT: snapshot_manager.create_snapshot,
    TaskName.CREATE_VOLUME: volume_manager.create_volume,
}


class TaskInfo(TypedDict):
    task: str
    args: list
    kwargs: dict
    retry_count: int
    state: TaskState


class TaskManager:
    def __init__(
        self, executor: Executor, tasks_store_path: Path, retry_interval=5, max_retry=5
    ):
        self._executor = executor
        self._tasks: dict = {}
        self._shutting_down = False
        self._retry_interval = retry_interval
        self._max_retry = max_retry
        self._tasks_store_path = tasks_store_path
        self._tasks_store_path.parent.mkdir(exist_ok=True, parents=True)
        self._tasks_store_path.touch(exist_ok=True)
        self._lock = Lock()
        for task_id, task in self.get_tasks(state=TaskState.RUNNING).items():
            task["state"] = TaskState.FAILED
            logger.warning(
                "Marking stuck task as failed in case of crash",
                task_id=task_id,
                task=task,
            )
            if task["retry_count"] > 0:
                task["retry_count"] -= 1
            self.save_task(task_id, task)
        self._executor.submit(self.retry_worker)

    def retry_worker(self):
        while not self._shutting_down:
            try:
                self.retry_all()
                for task_id, _ in self.get_tasks(retriable=False).items():
                    self.remove_task(task_id)
                for task_id, _ in self.get_tasks(state=TaskState.COMPLETED).items():
                    self.remove_task(task_id)
            except Exception as e:
                # Note that this should not happen unless there's an I/O reading the
                # task state information or if there's a logic bug in the task management/state storing
                # since we don't run the tasks directly here
                logger.error("TaskManager Worker encountered an error", error=e)
            time.sleep(self._retry_interval)
        logger.info("TaskManager Worker exit after shutdown request...")

    def retry_all(self):
        logger.debug("Retrying all retriable tasks", running=len(self._tasks))
        for task_id, failed_task in self.get_tasks(retriable=True).items():
            logger.debug("Retrying task", task_id=task_id, task=failed_task)
            self.remove_task(task_id)
            self.run_task(
                TaskName(failed_task["task"]),
                *failed_task["args"],
                **failed_task["kwargs"],
            )

    def hash_task_info(self, task: TaskName, *args, **kwargs):
        raw = json.dumps(kwargs) + json.dumps(args) + task.value
        return hashlib.md5(raw.encode()).hexdigest()

    def get_tasks(
        self, state: TaskState | None = None, retriable: bool | None = None
    ) -> dict[str, TaskInfo]:
        with self._lock:
            with open(self._tasks_store_path) as tasks_file:
                data = json.loads(tasks_file.read() or "{}")
                if retriable is not None:
                    if retriable:
                        data = {
                            k: v
                            for k, v in data.items()
                            if v["retry_count"] < self._max_retry
                            and v["state"] == TaskState.FAILED
                        }
                    else:
                        data = {
                            k: v
                            for k, v in data.items()
                            if v["retry_count"] >= self._max_retry
                        }
                if state is not None:
                    data = {k: v for k, v in data.items() if v["state"] == state}
                return data

    def get_task(self, task_id) -> None:
        self.get_tasks().get(task_id, None)

    def remove_task(self, task_id: str):
        logger.debug("Removing task", task_id=task_id)
        with self._lock:
            with open(self._tasks_store_path, "r+") as tasks_file:
                current: dict[str, TaskInfo] = json.loads(tasks_file.read() or "{}")
                current.pop(task_id)
                tasks_file.truncate(0)
                tasks_file.seek(0)
                json.dump(current, tasks_file)
                os.fsync(tasks_file.fileno())

    def done_callback(self, task_id: str):
        state: TaskState
        task_info: TaskInfo = self._tasks.get(task_id, {}).get("info", {})
        future: Future | None = self._tasks.get(task_id, {}).get("future", None)
        if not (future and (future.exception() or future.cancelled())):
            state = TaskState.COMPLETED
            logger.success("Task Completed", task_id=task_id, task=task_info)
        else:
            exc = (
                future.exception()
                if future.exception()
                else Exception("Task was cancelled")
            )
            state = TaskState.FAILED
            logger.opt(exception=exc).error(
                "Task failed", task_id=task_id, task=task_info, exception=exc
            )
        task_info["state"] = state
        self.save_task(task_id, task_info)

    def save_task(self, task_id: str, task_info: TaskInfo):
        with self._lock:
            logger.debug("Saving task", task_id=task_id, task=task_info)
            with open(self._tasks_store_path, "r+") as tasks_file:
                current: dict[str, TaskInfo] = json.loads(tasks_file.read() or "{}")
                current[task_id] = task_info
                tasks_file.truncate(0)
                tasks_file.seek(0)
                json.dump(current, tasks_file)
                os.fsync(tasks_file.fileno())

    def run_task(self, task: TaskName, *args, **kwargs) -> str:
        logger.debug("Running task", task=task.value, args=args, kwargs=kwargs)
        if self._shutting_down:
            raise TaskManagerShuttingDown()
        task_id = self.hash_task_info(task, *args, **kwargs)
        current = self.get_task(task_id) or {}
        retry_count = current.get("retry_count", -1)
        if current.get("state", None):
            return task_id
        info: TaskInfo = {
            "kwargs": kwargs,
            "task": task.value,
            "args": list(args),
            "retry_count": retry_count,
            "state": TaskState.PENDING,
        }
        self.save_task(task_id, info)
        future = self._executor.submit(task_mapping[task], *args, **kwargs)
        info["state"] = TaskState.RUNNING
        self.save_task(task_id, info)
        future.add_done_callback(lambda _: self.done_callback(task_id))
        self._tasks[task_id] = {"future": future, "info": info}
        return task_id

    def shutdown(self, timeout: int):
        logger.info("Shutting down Task Manager", timeout=timeout)
        self._shutting_down = True
        start_time = time.time()
        to_kill = {}
        while time.time() - start_time < timeout:
            if not self._tasks:
                break
            to_kill = {k: v for k, v in self._tasks.items() if v["future"].running()}
        if len(to_kill):
            for task_id, data in to_kill.items():
                info = data["info"]
                info["state"] = TaskState.FAILED
                self.save_task(task_id, info)
        self._executor.shutdown(wait=False, cancel_futures=True)

    def migrate_tasks_file_path(self):
        src = Path(
            f"{config.csi_driver.storage_pools[config.csi_driver.default_pool].path}/tasks.json"
        )
        dst = self._tasks_store_path
        if src.exists():
            shutil.move(src, dst)
