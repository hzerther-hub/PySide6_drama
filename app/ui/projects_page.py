# -*- coding: utf-8 -*-
"""项目启动台:统计/筛选/搜索/排序/项目卡(状态标记+更多菜单)/新建/删除。"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from PySide6.QtCore import QDateTime, Qt, Signal
from PySide6.QtWidgets import (QComboBox, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMenu, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from ..core import db
from ..core.i18n import tr
from . import widgets as W
from .toast import err, ok

WT_LABEL = {"novel": "📖 " + tr("wt_novel"), "drama": "🎬 " + tr("wt_drama"),
            "comic": "📚 " + tr("wt_comic"), "promotion": "📣 " + tr("wt_promotion"),
            "video_clone": "🎞 " + tr("wt_clone")}

STATUS_META = {
    "pending": ("待开始", "#86909c"),
    "active": ("进行中", "#4b6ef5"),
    "completed": ("已完成", "#16a34a"),
}


def _fmt_ago(ts: str) -> str:
    """相对时间(对齐原版:刚刚 / N分钟前 / N小时前 / M/D)。"""
    if not ts:
        return "-"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        secs = (datetime.now(timezone.utc) - dt).total_seconds()
    except Exception:  # noqa: BLE001
        return ts[:16]
    if secs < 60:
        return "刚刚"
    if secs < 3600:
        return f"{int(secs // 60)} 分钟前"
    if secs < 86400:
        return f"{int(secs // 3600)} 小时前"
    if secs < 86400 * 7:
        return f"{int(secs // 86400)} 天前"
    return f"{dt.month}/{dt.day}"


class ProjectCard(QFrame):
    open_requested = Signal(int)
    delete_requested = Signal(int, str)
    status_changed = Signal(int, str)

    def __init__(self, drama: dict):
        super().__init__()
        self.setObjectName("card")
        self.drama_id = drama["id"]
        self._title = drama["title"]
        self.setFixedHeight(196)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 10)
        lay.setSpacing(8)

        # 顶部:封面首字母 + 画幅角标 + 状态徽标 + 更多
        top = QHBoxLayout()
        cover = W.avatar(drama["title"], 46)
        top.addWidget(cover)
        ratio = W.tag(drama["aspect_ratio"])
        top.addWidget(ratio)
        top.addStretch(1)
        self.status_btn = QPushButton("●")
        self.status_btn.setFixedWidth(56)
        self.status_btn.setCursor(Qt.PointingHandCursor)
        self._apply_status_style(drama.get("status") or "pending")
        self.status_btn.clicked.connect(self._status_menu)
        top.addWidget(self.status_btn)
        more = QPushButton("···")
        more.setFixedWidth(34)
        more.setCursor(Qt.PointingHandCursor)
        more.clicked.connect(self._menu)
        top.addWidget(more)
        lay.addLayout(top)

        title = W.h2(drama["title"])
        title.setWordWrap(False)
        lay.addWidget(title)

        chips = QHBoxLayout()
        chips.setSpacing(6)
        chips.addWidget(W.tag(WT_LABEL.get(drama["work_type"], drama["work_type"])))
        style = db.q1("SELECT name FROM style_presets WHERE value=?", (drama["style"],))
        if style and drama["work_type"] != "novel":
            chips.addWidget(W.tag(style["name"]))
        chips.addStretch(1)
        lay.addLayout(chips)

        nc = db.q1("SELECT COUNT(*) c FROM characters WHERE drama_id=?", (drama["id"],))["c"]
        ns = db.q1("SELECT COUNT(*) c FROM scenes WHERE drama_id=?", (drama["id"],))["c"]
        ne = db.q1("SELECT COUNT(*) c FROM episodes WHERE drama_id=?", (drama["id"],))["c"]
        row = QHBoxLayout()
        row.addWidget(QLabel(f"{nc} 角色 · {ns} 场景 · {ne} 集"))
        row.addStretch(1)
        ago = QLabel(_fmt_ago(drama["updated_at"]))
        ago.setObjectName("muted")
        row.addWidget(ago)
        lay.addLayout(row)

    def _apply_status_style(self, status: str):
        label, color = STATUS_META.get(status, STATUS_META["pending"])
        self.status_btn.setText(label)
        self.status_btn.setStyleSheet(
            f"QPushButton{{color:{color};border:1px solid {color}44;border-radius:10px;"
            f"background:transparent;font-size:11px;padding:2px 6px;}}")

    def _status_menu(self):
        m = QMenu(self)
        for key, (label, color) in STATUS_META.items():
            act = m.addAction(f"●  {label}")
            act.setIcon(_dot_icon(color))
            act.triggered.connect(lambda _=False, k=key: self.status_changed.emit(self.drama_id, k))
        m.exec()

    def _menu(self):
        m = QMenu(self)
        a1 = m.addAction(tr("open_project"))
        a2 = m.addAction(tr("delete_project"))
        act = m.exec()
        if act == a1:
            self.open_requested.emit(self.drama_id)
        elif act == a2:
            self.delete_requested.emit(self.drama_id, self._title)


def _dot_icon(color: str):
    from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
    pm = QPixmap(12, 12)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.NoPen)
    p.drawEllipse(2, 2, 8, 8)
    p.end()
    return QIcon(pm)


class ProjectsPage(QWidget):
    open_drama = Signal(int)

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        root.addWidget(W.h1(tr("projects")))
        root.addWidget(W.muted(tr("tagline")))

        self.stat = W.StatBar([("0", tr("stat_projects").format(0)),
                               ("0", tr("stat_running").format(0)),
                               ("0", tr("stat_styles").format(0))])
        root.addWidget(self.stat)

        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("search"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.reload)
        self.filter = QComboBox()
        for key in ("filter_all", "filter_pending", "filter_running", "filter_done"):
            self.filter.addItem(tr(key), key.split("filter_")[1])
        self.filter.currentIndexChanged.connect(self.reload)
        self.sort = QComboBox()
        self.sort.addItem("🕘 " + tr("sort_recent"), "recent")
        self.sort.addItem("🔤 按标题", "title")
        self.sort.currentIndexChanged.connect(self.reload)
        new_btn = W.primary_btn("＋ " + tr("new_project"))
        new_btn.clicked.connect(self._new_project)
        bar.addWidget(self.search, 1)
        bar.addWidget(self.filter)
        bar.addWidget(self.sort)
        bar.addWidget(new_btn)
        root.addLayout(bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        self.holder = QWidget()
        self.grid = QGridLayout(self.holder)
        self.grid.setContentsMargins(0, 8, 0, 8)
        self.grid.setSpacing(14)
        self.scroll.setWidget(self.holder)
        root.addWidget(self.scroll, 1)
        self._new_cb = None
        self.reload()

    def set_new_callback(self, cb) -> None:
        self._new_cb = cb

    def _new_project(self):
        if self._new_cb:
            self._new_cb()

    def reload(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        flt = self.filter.currentData() or "all"
        kw = self.search.text().strip()
        rows = [dict(r) for r in db.q("SELECT * FROM dramas")]
        shown = []
        for d in rows:
            if kw and kw not in d["title"]:
                continue
            if flt != "all" and d.get("status", "pending") != flt:
                continue
            shown.append(d)
        if self.sort.currentData() == "title":
            shown.sort(key=lambda x: x["title"])
        else:
            shown.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
        cols = 3
        for i, d in enumerate(shown):
            card = ProjectCard(d)
            card.open_requested.connect(self.open_drama.emit)
            card.delete_requested.connect(self._delete)
            card.status_changed.connect(self._set_status)
            self.grid.addWidget(card, i // cols, i % cols)
        if not shown:
            empty = QLabel("还没有项目" if not rows else "没有符合条件的项目")
            empty.setObjectName("muted")
            empty.setAlignment(Qt.AlignCenter)
            self.grid.addWidget(empty, 0, 0)
        running = sum(1 for d in rows if d.get("status") == "active")
        self.stat.setItemValue(0, tr("stat_projects").format(len(rows)))
        self.stat.setItemValue(1, tr("stat_running").format(running))
        self.stat.setItemValue(2, tr("stat_styles").format(len(db.q("SELECT id FROM style_presets WHERE is_active=1"))))

    def _set_status(self, drama_id: int, status: str):
        db.ex("UPDATE dramas SET status=?, updated_at=? WHERE id=?", (status, db.now(), drama_id))
        ok(f"已标记为「{STATUS_META[status][0]}」")
        self.reload()

    def _delete(self, drama_id: int, _title: str):
        from PySide6.QtWidgets import QMessageBox
        d = db.q1("SELECT title FROM dramas WHERE id=?", (drama_id,))
        if not d:
            return
        if QMessageBox.question(self, tr("delete_project"),
                                tr("confirm_delete_project", d["title"])) != QMessageBox.Yes:
            return
        for t in ("episode_characters", "episode_scenes", "episode_props"):
            db.ex(f"DELETE FROM {t} WHERE episode_id IN (SELECT id FROM episodes WHERE drama_id=?)", (drama_id,))
        for t in ("storyboard_characters", "storyboard_props"):
            db.ex(f"DELETE FROM {t} WHERE storyboard_id IN (SELECT id FROM storyboards WHERE episode_id IN (SELECT id FROM episodes WHERE drama_id=?))", (drama_id,))
        db.ex("DELETE FROM storyboards WHERE episode_id IN (SELECT id FROM episodes WHERE drama_id=?)", (drama_id,))
        db.ex("DELETE FROM comic_panel_characters WHERE panel_id IN (SELECT id FROM comic_panels WHERE episode_id IN (SELECT id FROM episodes WHERE drama_id=?))", (drama_id,))
        db.ex("DELETE FROM comic_panels WHERE episode_id IN (SELECT id FROM episodes WHERE drama_id=?)", (drama_id,))
        db.ex("DELETE FROM video_merges WHERE episode_id IN (SELECT id FROM episodes WHERE drama_id=?)", (drama_id,))
        db.ex("DELETE FROM episodes WHERE drama_id=?", (drama_id,))
        db.ex("DELETE FROM characters WHERE drama_id=?", (drama_id,))
        db.ex("DELETE FROM scenes WHERE drama_id=?", (drama_id,))
        db.ex("DELETE FROM props WHERE drama_id=?", (drama_id,))
        db.ex("DELETE FROM dramas WHERE id=?", (drama_id,))
        self.reload()
