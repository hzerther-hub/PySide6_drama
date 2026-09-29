# -*- coding: utf-8 -*-
"""项目启动台:统计/筛选/搜索/排序/项目卡片/新建/删除。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QComboBox, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMenu, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from ..core import db
from ..core.i18n import tr
from . import widgets as W

WT_LABEL = {"novel": "📖 " + tr("wt_novel"), "drama": "🎬 " + tr("wt_drama"),
            "comic": "📚 " + tr("wt_comic"), "promotion": "📣 " + tr("wt_promotion"),
            "video_clone": "🎞 " + tr("wt_clone")}


def _fmt_ago(ts: str) -> str:
    return (ts or "")[:16].replace("T", " ")


class ProjectCard(QFrame):
    open_requested = Signal(int)
    delete_requested = Signal(int, str)

    def __init__(self, drama: dict):
        super().__init__()
        self.setObjectName("card")
        self.drama_id = drama["id"]
        self.setFixedHeight(168)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 14, 12, 14)
        lay.setSpacing(14)

        col = QVBoxLayout()
        col.setSpacing(6)
        top = QHBoxLayout()
        top.addWidget(W.avatar(drama["title"]))
        title_box = QVBoxLayout()
        t = W.h2(drama["title"])
        t.setWordWrap(False)
        title_box.addWidget(t)
        chips = QHBoxLayout()
        chips.setSpacing(6)
        chips.addWidget(W.tag(WT_LABEL.get(drama["work_type"], drama["work_type"])))
        style = db.q1("SELECT name FROM style_presets WHERE value=?", (drama["style"],))
        chips.addWidget(W.tag(style["name"] if style else drama["style"]))
        chips.addWidget(W.tag(drama["aspect_ratio"]))
        chips.addStretch(1)
        title_box.addLayout(chips)
        col.addLayout(top)
        col.addLayout(chips_wrap(col, drama))
        lay.addLayout(col, 1)

        more = QPushButton("···")
        more.setFixedWidth(36)
        more.setCursor(Qt.PointingHandCursor)
        more.clicked.connect(self._menu)
        lay.addWidget(more, 0, Qt.AlignTop)
        self._title = drama["title"]

    def _menu(self):
        m = QMenu(self)
        a1 = m.addAction(tr("open_project"))
        a2 = m.addAction(tr("delete_project"))
        act = m.exec()
        if act == a1:
            self.open_requested.emit(self.drama_id)
        elif act == a2:
            self.delete_requested.emit(self.drama_id, self._title)


def chips_wrap(_col, drama: dict) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(6)
    nc = db.q1("SELECT COUNT(*) c FROM characters WHERE drama_id=?", (drama["id"],))["c"]
    ns = db.q1("SELECT COUNT(*) c FROM scenes WHERE drama_id=?", (drama["id"],))["c"]
    ne = db.q1("SELECT COUNT(*) c FROM episodes WHERE drama_id=?", (drama["id"],))["c"]
    row.addWidget(QLabel(tr("characters_n", nc)))
    row.addWidget(QLabel("·"))
    row.addWidget(QLabel(tr("scenes_n", ns)))
    row.addWidget(QLabel("·"))
    row.addWidget(QLabel(tr("episodes_n", ne)))
    row.addStretch(1)
    ago = QLabel(_fmt_ago(drama["updated_at"]))
    ago.setObjectName("muted")
    row.addWidget(ago)
    return row


class ProjectsPage(QWidget):
    open_drama = Signal(int)

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        root.addWidget(W.h1(tr("projects")))
        root.addWidget(W.muted(tr("tagline")))

        self.stat = W.StatBar([("0", tr("stat_projects").format(0)), ("0", tr("stat_running").format(0)), ("0", tr("stat_styles").format(0))])
        root.addWidget(self.stat)

        # 工具行
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("search"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.reload)
        self.filter = QComboBox()
        for key in ("filter_all", "filter_pending", "filter_running", "filter_done"):
            self.filter.addItem(tr(key), key.split("filter_")[1])
        self.filter.currentIndexChanged.connect(self.reload)
        self.sort = QPushButton(tr("sort_recent"))
        self.sort.clicked.connect(self.reload)
        new_btn = W.primary_btn("＋ " + tr("new_project"))
        new_btn.clicked.connect(self._new_project)
        bar.addWidget(self.search, 1)
        bar.addWidget(self.filter)
        bar.addWidget(self.sort)
        bar.addWidget(new_btn)
        root.addLayout(bar)

        # 卡片滚动区
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        self.holder = QWidget()
        self.grid = QGridLayout(self.holder)
        self.grid.setContentsMargins(0, 8, 0, 8)
        self.grid.setSpacing(14)
        self.scroll.setWidget(self.holder)
        root.addWidget(self.scroll, 1)
        self._new_cb = None  # 由主窗口注入:打开新建对话框
        self.reload()

    def set_new_callback(self, cb) -> None:
        self._new_cb = cb

    def _new_project(self):
        if self._new_cb:
            self._new_cb()

    def reload(self):
        # 清空
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        flt = self.filter.currentData() or "all"
        kw = self.search.text().strip()
        rows = db.q("SELECT * FROM dramas ORDER BY updated_at DESC")
        shown = []
        for d in rows:
            if kw and kw not in d["title"]:
                continue
            if flt != "all":
                has_video = db.q1(
                    "SELECT id FROM episodes WHERE drama_id=? AND video_url IS NOT NULL LIMIT 1", (d["id"],))
                if flt == "done" and not has_video:
                    continue
                if flt == "running" and has_video:
                    continue
                if flt == "pending":
                    n = db.q1("SELECT COUNT(*) c FROM episodes WHERE drama_id=? AND (script_content IS NOT NULL AND script_content!='' OR content IS NOT NULL AND content!='')", (d["id"],))["c"]
                    if n:
                        continue
            shown.append(d)
        cols = 3
        for i, d in enumerate(shown):
            card = ProjectCard(dict(d))
            card.open_requested.connect(self.open_drama.emit)
            card.delete_requested.connect(self._delete)
            self.grid.addWidget(card, i // cols, i % cols)
        if not shown:
            empty = QLabel(tr("search") + " · 0")
            empty.setObjectName("muted")
            empty.setAlignment(Qt.AlignCenter)
            self.grid.addWidget(empty, 0, 0)
        # 统计
        running = 0
        for d in rows:
            if db.q1("SELECT id FROM episodes WHERE drama_id=? AND video_url IS NULL AND script_content!='' LIMIT 1", (d["id"],)):
                running += 1
        self.stat.setItemValue(0, tr("stat_projects").format(len(rows)))
        self.stat.setItemValue(1, tr("stat_running").format(running))
        self.stat.setItemValue(2, tr("stat_styles").format(len(db.q("SELECT id FROM style_presets WHERE is_active=1"))))

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
