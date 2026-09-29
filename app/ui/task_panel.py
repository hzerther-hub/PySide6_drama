# -*- coding: utf-8 -*-
"""任务面板:统一任务队列(sys_task)列表与状态。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QHeaderView, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from ..core.i18n import tr
from ..core.taskmgr import TASKMGR


class TaskPanel(QDialog):
    def __init__(self, episode_id: int | None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("tasks"))
        self.resize(680, 420)
        self.episode_id = episode_id
        lay = QVBoxLayout(self)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", tr("params"), "model", "status", "time"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        lay.addWidget(self.table)
        TASKMGR.updated.connect(self.reload)
        self.reload()

    def reload(self):
        rows = TASKMGR.list_tasks(self.episode_id, limit=100)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            vals = [str(r["id"]), r["type"], f"{r['provider'] or ''}/{r['model'] or ''}",
                    r["status"], (r["updated_at"] or "")[:19].replace("T", " ")]
            for j, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if j == 3:
                    item.setForeground(Qt.darkGreen if v == "completed" else (Qt.red if v == "failed" else Qt.gray))
                self.table.setItem(i, j, item)
