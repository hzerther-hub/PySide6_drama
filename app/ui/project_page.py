# -*- coding: utf-8 -*-
"""项目页:剧集列表(增删/进入制作)+ 项目级素材库(角色/场景/道具)。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QComboBox, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMenu, QMessageBox,
                               QPushButton, QScrollArea, QTabWidget,
                               QVBoxLayout, QWidget)

from ..core import db
from ..core.i18n import tr
from . import widgets as W


class EpisodeCard(QFrame):
    enter = Signal(int)

    def __init__(self, ep: dict, resolution: str = "720p"):
        super().__init__()
        self.setObjectName("card")
        self.episode_id = ep["id"]
        self.setFixedHeight(150)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 12, 12)
        lay.setSpacing(6)
        top = QHBoxLayout()
        num = QLabel(f"EP{ep['episode_number']:02d}")
        num.setObjectName("muted")
        top.addWidget(num)
        top.addWidget(W.h2(tr("episode_n").format(ep["episode_number"])))
        top.addStretch(1)
        chips = QHBoxLayout()
        chips.setSpacing(6)
        if ep["script_content"]:
            chips.addWidget(W.tag(tr("script_entered")))
        if ep["video_url"]:
            chips.addWidget(W.tag(tr("merged_tag")))
        else:
            chips.addWidget(W.tag(tr("pending")))
        chips.addWidget(W.tag(ep["resolution"] or resolution))
        top.addLayout(chips)
        lay.addLayout(top)
        mid = QHBoxLayout()
        n_done = db.q1("SELECT COUNT(*) c FROM storyboards WHERE episode_id=? AND video_url IS NOT NULL", (ep["id"],))["c"]
        n_all = db.q1("SELECT COUNT(*) c FROM storyboards WHERE episode_id=?", (ep["id"],))["c"]
        st = QLabel(f"{n_done}/{n_all} · {ep['updated_at'][:10]}")
        st.setObjectName("muted")
        mid.addWidget(st)
        mid.addStretch(1)
        enter = W.primary_btn(tr("enter_production"))
        enter.setFixedHeight(30)
        enter.clicked.connect(lambda: self.enter.emit(self.episode_id))
        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(30, 30)
        del_btn.setToolTip(tr("delete_episode"))
        del_btn.clicked.connect(lambda: self._del(ep["id"], ep["episode_number"]))
        mid.addWidget(del_btn)
        mid.addWidget(enter)
        lay.addLayout(mid)

    def _del(self, eid: int, num: int):
        if QMessageBox.question(self, tr("delete_episode"), f"{tr('episode_n').format(num)} → {tr('delete')}?") == QMessageBox.Yes:
            for t in ("storyboard_characters", "storyboard_props"):
                db.ex(f"DELETE FROM {t} WHERE storyboard_id IN (SELECT id FROM storyboards WHERE episode_id=?)", (eid,))
            db.ex("DELETE FROM storyboards WHERE episode_id=?", (eid,))
            db.ex("DELETE FROM comic_panel_characters WHERE panel_id IN (SELECT id FROM comic_panels WHERE episode_id=?)", (eid,))
            db.ex("DELETE FROM comic_panels WHERE episode_id=?", (eid,))
            db.ex("DELETE FROM episode_characters WHERE episode_id=?", (eid,))
            db.ex("DELETE FROM episode_scenes WHERE episode_id=?", (eid,))
            db.ex("DELETE FROM episode_props WHERE episode_id=?", (eid,))
            db.ex("DELETE FROM video_merges WHERE episode_id=?", (eid,))
            db.ex("DELETE FROM episodes WHERE id=?", (eid,))
            from ..core.taskmgr import TASKMGR
            TASKMGR.updated.emit()


class AssetCard(QFrame):
    """素材库卡片:图片 + 名称 + 描述 + 操作提示。"""
    def __init__(self, kind: str, row: dict):
        super().__init__()
        self.setObjectName("card")
        self.setFixedHeight(210)
        self.setFixedWidth(220)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)
        img = QLabel()
        img.setFixedHeight(96)
        img.setAlignment(Qt.AlignCenter)
        url = row["image_url"] or row["comic_image_url"]
        img.setPixmap(W.pixmap_from_media(url, 200, 96))
        lay.addWidget(img)
        name = W.h2(row["name"])
        lay.addWidget(name)
        role = {"lead": tr("lead"), "supporting": tr("supporting"), "extra": tr("extra")}.get(row.get("role_type"), row.get("type") or kind)
        lay.addWidget(W.tag(url and tr("generated") or role))
        desc = QLabel((row.get("appearance") or row.get("prompt") or row.get("description") or "")[:60] + "…")
        desc.setObjectName("muted")
        desc.setWordWrap(True)
        lay.addWidget(desc)


class ProjectPage(QWidget):
    enter_episode = Signal(int, int)  # drama_id, episode_id

    def __init__(self):
        super().__init__()
        self.drama_id = 0
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(12)

        head = QHBoxLayout()
        back = QPushButton("← " + tr("back"))
        back.clicked.connect(self._go_back)
        self.title = W.h1("")
        head.addWidget(back)
        head.addWidget(self.title)
        head.addStretch(1)
        self.promo_btn = QPushButton("📣 " + tr("promo_copy"))
        self.promo_btn.clicked.connect(self._promo)
        head.addWidget(self.promo_btn)
        root.addLayout(head)

        self.sub = W.muted("")
        root.addWidget(self.sub)

        self.tabs = QTabWidget()
        # 剧集列表
        ep_holder = QWidget()
        self.ep_lay = QVBoxLayout(ep_holder)
        self.ep_lay.setContentsMargins(0, 10, 0, 10)
        self.ep_lay.setSpacing(12)
        ep_scroll = QScrollArea()
        ep_scroll.setWidgetResizable(True)
        ep_scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        ep_scroll.setWidget(ep_holder)
        self.tabs.addTab(ep_scroll, tr("episodes"))
        # 素材库
        lib_holder = QWidget()
        lib_root = QVBoxLayout(lib_holder)
        lib_bar = QHBoxLayout()
        self.lib_filter = QComboBox()
        for key, label in [("all", tr("filter_all")), ("chars", tr("chars")), ("scenes", tr("scenes")), ("props", tr("props"))]:
            self.lib_filter.addItem(label, key)
        self.lib_filter.currentIndexChanged.connect(self.reload)
        lib_bar.addWidget(self.lib_filter)
        lib_bar.addStretch(1)
        lib_root.addLayout(lib_bar)
        self.lib_scroll = QScrollArea()
        self.lib_scroll.setWidgetResizable(True)
        self.lib_scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        self.lib_grid_holder = QWidget()
        self.lib_grid = QGridLayout(self.lib_grid_holder)
        self.lib_grid.setSpacing(12)
        self.lib_scroll.setWidget(self.lib_grid_holder)
        lib_root.addWidget(self.lib_scroll, 1)
        self.tabs.addTab(lib_holder, tr("asset_library"))
        root.addWidget(self.tabs, 1)

        self._back_cb = None
        self._enter_cb = None

    def set_callbacks(self, back_cb, enter_cb, promo_cb=None):
        self._back_cb = back_cb
        self._enter_cb = enter_cb
        self._promo_cb = promo_cb

    def _go_back(self):
        if self._back_cb:
            self._back_cb()

    def _promo(self):
        if getattr(self, "_promo_cb", None):
            self._promo_cb(self.drama_id)

    def load(self, drama_id: int):
        self.drama_id = drama_id
        d = db.q1("SELECT * FROM dramas WHERE id=?", (drama_id,))
        if not d:
            return
        self.title.setText(d["title"])
        nc = db.q1("SELECT COUNT(*) c FROM characters WHERE drama_id=?", (drama_id,))["c"]
        ns = db.q1("SELECT COUNT(*) c FROM scenes WHERE drama_id=?", (drama_id,))["c"]
        ne = db.q1("SELECT COUNT(*) c FROM episodes WHERE drama_id=?", (drama_id,))["c"]
        self.sub.setText(f"{tr('characters_n', nc)} · {tr('scenes_n', ns)} · {tr('episodes_n', ne)}")
        self.promo_btn.setVisible(True)
        self.reload()

    def reload(self):
        while self.ep_lay.count():
            item = self.ep_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        rows = db.q("SELECT * FROM episodes WHERE drama_id=? ORDER BY episode_number", (self.drama_id,))
        for ep in rows:
            card = EpisodeCard(dict(ep))
            card.enter.connect(self._on_enter)
            self.ep_lay.addWidget(card)
        add = QPushButton("＋ " + tr("add_episode"))
        add.clicked.connect(self._add_episode)
        self.ep_lay.addWidget(add)
        self.ep_lay.addStretch(1)
        # 素材库
        while self.lib_grid.count():
            item = self.lib_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        chars = db.q("SELECT * FROM characters WHERE drama_id=? ORDER BY id", (self.drama_id,))
        scenes = db.q("SELECT * FROM scenes WHERE drama_id=? ORDER BY id", (self.drama_id,))
        props = db.q("SELECT * FROM props WHERE drama_id=? ORDER BY id", (self.drama_id,))
        items = ([("chars", dict(r)) for r in chars] + [("scenes", dict(r)) for r in scenes]
                 + [("props", dict(r)) for r in props])
        cols = max(1, self.lib_grid_holder.width() // 240 or 4)
        for i, (kind, row) in enumerate(items):
            self.lib_grid.addWidget(AssetCard(kind, row), i // cols, i % cols)

    def _add_episode(self):
        n = (db.q1("SELECT MAX(episode_number) m FROM episodes WHERE drama_id=?", (self.drama_id,))["m"] or 0) + 1
        ts = db.now()
        eid = db.ex("INSERT INTO episodes(drama_id,episode_number,title,status,resolution,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                    (self.drama_id, n, tr("episode_n").format(n), "pending", "720p", ts, ts))
        self.reload()

    def _on_enter(self, episode_id: int):
        if self._enter_cb:
            self._enter_cb(self.drama_id, episode_id)
