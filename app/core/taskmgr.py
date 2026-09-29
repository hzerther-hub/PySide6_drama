# -*- coding: utf-8 -*-
"""统一后台任务管理:QThreadPool 执行,状态落 sys_task 表。

生命周期(对齐原版 generation.ts):
  processing → (polling) → completed / failed
"""
from __future__ import annotations

import traceback
from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from . import db


def create_task(task_type: str, **links) -> int:
    ts = db.now()
    cols = {"type": task_type, "status": "processing", "created_at": ts, "updated_at": ts}
    for k in ("drama_id", "episode_id", "storyboard_id", "scene_id", "character_id", "prop_id",
              "provider", "model", "task_id", "result_url", "local_path"):
        if links.get(k) is not None:
            cols[k] = str(links[k]) if not isinstance(links[k], (int, float)) else links[k]
    keys = ",".join(cols)
    marks = ",".join("?" * len(cols))
    return db.ex(f"INSERT INTO sys_task({keys}) VALUES({marks})", tuple(cols.values()))


def finish_task(task_id: int, status: str, error: str | None = None,
                result_url: str | None = None, local_path: str | None = None) -> None:
    db.ex("UPDATE sys_task SET status=?, error_msg=?, result_url=COALESCE(?,result_url), local_path=COALESCE(?,local_path), updated_at=? WHERE id=?",
          (status, error, result_url, local_path, db.now(), task_id))


def active_count() -> int:
    row = db.q1("SELECT COUNT(*) c FROM sys_task WHERE status='processing'")
    return row["c"] if row else 0


class TaskSignals(QObject):
    finished = Signal(int, str)       # task_id, status
    progress = Signal(int, int)       # task_id, percent
    message = Signal(str)


class _FnTask(QRunnable):
    def __init__(self, task_id: int, fn: Callable[..., object], signals: TaskSignals, done_cb: Callable | None):
        super().__init__()
        self.task_id, self.fn, self.signals, self.done_cb = task_id, fn, signals, done_cb
        self.setAutoDelete(True)

    def run(self):  # noqa: D102
        try:
            result = self.fn(self.task_id)
            finish_task(self.task_id, "completed")
            if self.done_cb:
                self.done_cb(self.task_id, result, None)
        except Exception:  # noqa: BLE001
            err = traceback.format_exc(limit=6)
            finish_task(self.task_id, "failed", err)
            if self.done_cb:
                self.done_cb(self.task_id, None, err)
        finally:
            self.signals.finished.emit(self.task_id, "done")


class TaskManager(QObject):
    """全局任务管理器:submit() 返回 sys_task id;UI 轮询或订阅信号。"""
    updated = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.pool = QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(6)
        self.signals = TaskSignals()
        self.signals.finished.connect(self.updated.emit)

    @staticmethod
    def active_count() -> int:
        return active_count()

    def submit(self, task_type: str, fn: Callable[..., object],
               done_cb: Callable | None = None, **links) -> int:
        tid = create_task(task_type, **links)
        self.pool.start(_FnTask(tid, fn, self.signals, done_cb))
        self.updated.emit()
        return tid

    # 轮询任务列表(任务面板 / 工作台用)
    @staticmethod
    def list_tasks(episode_id: int | None = None, limit: int = 100) -> list:
        if episode_id:
            return db.q("SELECT * FROM sys_task WHERE episode_id=? ORDER BY id DESC LIMIT ?",
                        (episode_id, limit))
        return db.q("SELECT * FROM sys_task ORDER BY id DESC LIMIT ?", (limit,))

    @staticmethod
    def ep_video_stats(episode_id: int) -> dict:
        rows = db.q(
            "SELECT status, COUNT(*) c FROM sys_task WHERE episode_id=? AND type='video' GROUP BY status",
            (episode_id,))
        stats = {r["status"]: r["c"] for r in rows}
        return {"processing": stats.get("processing", 0),
                "completed": stats.get("completed", 0),
                "failed": stats.get("failed", 0)}


TASKMGR = TaskManager()
