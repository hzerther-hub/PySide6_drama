# -*- coding: utf-8 -*-
"""项目页:剧集列表(改名/状态/分辨率/增删/进入制作)+ 素材库(筛选/详情编辑/添加)。"""
from __future__ import annotations

import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QComboBox, QDialog, QFormLayout, QFrame,
                               QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QMenu, QMessageBox, QPushButton, QScrollArea,
                               QTabWidget, QVBoxLayout, QWidget)

from ..core import db
from ..core.i18n import tr
from . import widgets as W
from .toast import err, ok
from .cover_dialog import CoverPanel, EpisodeCoverButton

EP_STAGES = ["novel", "script", "assets", "storyboard", "video"]
EP_STAGE_CN = {"novel": "正文", "script": "剧本", "assets": "资产",
               "storyboard": "分镜", "video": "成片"}


def ep_stage_index(ep: dict) -> int:
    """按产物判定制作阶段(不依赖手工状态字段,对齐原版 detail.vue)。"""
    if len((ep.get("content") or "").strip()) < 200:
        return 0
    if len((ep.get("script_content") or "").strip()) < 100:
        return 1
    n = int(ep.get("storyboard_count") or 0)
    if n <= 0:
        return 2
    if not (ep.get("video_url") or ""):
        return 3
    return 4


STATUS_META = {
    "pending": ("待开始", "#86909c"),
    "active": ("进行中", "#4b6ef5"),
    "completed": ("已完成", "#16a34a"),
}


def _chapter_name_missing(ep: dict) -> bool:
    """标题为空或只有「第N集」占位 = 缺章节名(对齐原版 chapterNameMissing)。"""
    import re
    t = (ep.get("title") or "").strip()
    return (not t) or bool(re.match(r"^第\d+集\s*$", t))


class EpisodeCard(QFrame):
    enter = Signal(int)
    _reload_needed = Signal()

    def __init__(self, ep: dict, on_changed=None):
        super().__init__()
        self._on_changed = on_changed
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
        # 内联改名
        self.title_edit = QLineEdit(ep["title"] or tr("episode_n").format(ep["episode_number"]))
        f = self.title_edit.font()
        from PySide6.QtGui import QFont
        f2 = QFont(f)
        f2.setBold(True)
        f2.setPointSize(11)
        self.title_edit.setFont(f2)
        self.title_edit.setStyleSheet("border:none;background:transparent;")
        self.title_edit.setToolTip("点击可直接改名")
        self.title_edit.editingFinished.connect(self._rename)
        self.title_edit.returnPressed.connect(self._rename)
        top.addWidget(self.title_edit, 1)
        self.title_done: list = []  # 防止重复挂载
        # 状态菜单
        self.status_btn = QPushButton()
        self.status_btn.setFixedWidth(64)
        self.status_btn.setCursor(Qt.PointingHandCursor)
        self._apply_status(ep.get("status") or "pending")
        self.status_btn.clicked.connect(self._status_menu)
        top.addWidget(self.status_btn)
        lay.addLayout(top)
        # 缺章节名且有正文时,标题下方显示「章节名」按钮(对齐原版 73b3339)
        if _chapter_name_missing(dict(ep)) and (ep.get("content") or "").strip():
            name_row = QHBoxLayout()
            self.name_btn = QPushButton("✎ 章节名")
            self.name_btn.setToolTip("正文已有标题行就直接取,否则 AI 参考前文摘要与总纲自动起名")
            self.name_btn.setStyleSheet(
                "QPushButton{border:1px dashed #4b6ef5;color:#4b6ef5;border-radius:10px;"
                "padding:2px 10px;font-size:11px;background:transparent;}")
            self.name_btn.clicked.connect(lambda: self._gen_chapter_title(ep["id"]))
            name_row.addWidget(self.name_btn)
            name_row.addStretch(1)
            lay.addLayout(name_row)
        mid = QHBoxLayout()
        chips = QHBoxLayout()
        chips.setSpacing(6)
        if ep["script_content"]:
            chips.addWidget(W.tag(tr("script_entered")))
        if ep["video_url"]:
            chips.addWidget(W.tag(tr("merged_tag")))
        mid.addLayout(chips)
        # 制作阶段条(按产物判定)
        idx = ep_stage_index(ep)
        seg_row = QHBoxLayout()
        seg_row.setSpacing(3)
        for i, st in enumerate(EP_STAGES):
            seg = QLabel(EP_STAGE_CN[st])
            if i < idx:
                seg.setStyleSheet("background:#d9f2e3;color:#16a34a;border-radius:3px;padding:1px 5px;font-size:10px;")
            elif i == idx:
                seg.setStyleSheet("background:#4b6ef5;color:#fff;border-radius:3px;padding:1px 5px;font-size:10px;font-weight:700;")
            else:
                seg.setStyleSheet("background:#f0f1f4;color:#c0c6cf;border-radius:3px;padding:1px 5px;font-size:10px;")
            seg_row.addWidget(seg)
        seg_row.addStretch(1)
        mid.addLayout(seg_row)
        # 字数进度
        wc = len((ep.get("content") or "").strip())
        tw = ep.get("target_words") or 0
        if wc:
            warn_cls = wc < int(tw * 0.8) if tw else False
            wl = QLabel(f"{wc} / {tw} 字" if tw else f"{wc} 字")
            wl.setObjectName("muted")
            if warn_cls:
                wl.setStyleSheet("color:#d97706;font-weight:600;")
            mid.addWidget(wl)
        else:
            wl = QLabel("未写")
            wl.setObjectName("muted")
            mid.addWidget(wl)
        mid.addStretch(1)
        # 分辨率菜单
        self.res_btn = QPushButton(ep["resolution"] or "720p")
        self.res_btn.setFixedWidth(66)
        self.res_btn.setCursor(Qt.PointingHandCursor)
        self.res_btn.clicked.connect(self._res_menu)
        mid.addWidget(self.res_btn)
        n_done = db.q1("SELECT COUNT(*) c FROM storyboards WHERE episode_id=? AND video_url IS NOT NULL", (ep["id"],))["c"]
        n_all = db.q1("SELECT COUNT(*) c FROM storyboards WHERE episode_id=?", (ep["id"],))["c"]
        st = QLabel(f"{n_done}/{n_all}")
        st.setObjectName("muted")
        mid.addWidget(st)
        mid.addStretch(1)
        self.cover_btn = EpisodeCoverButton(ep, on_done=self._on_changed)
        self.cover_btn.setFixedHeight(30)
        mid.addWidget(self.cover_btn)
        del_btn = W.danger_btn(tr("delete"))
        del_btn.setFixedHeight(30)
        del_btn.setMinimumWidth(56)
        del_btn.setToolTip(tr("delete_episode"))
        del_btn.clicked.connect(self._del)
        mid.addWidget(del_btn)
        enter = W.primary_btn(tr("enter_production"))
        enter.setFixedHeight(30)
        enter.clicked.connect(lambda: self.enter.emit(self.episode_id))
        mid.addWidget(enter)
        lay.addLayout(mid)

    def _gen_chapter_title(self, episode_id: int):
        """一键章节名:优先从正文首行提取,提取不到才调 AI。"""
        from ..core.taskmgr import TASKMGR
        def job(tid):
            from ..pipeline import novel as novel_pipe
            return novel_pipe.gen_chapter_title(episode_id)
        def done(tid, result, error):
            if error:
                err(e_)
                return
            name, src = result
            ok(("已提取章节名:" if src == "content" else "章节名已写入:") + str(name))
            self._reload_needed.emit()
        TASKMGR.submit("novel_title", job, done, episode_id=episode_id)

    def _rename(self):
        from PySide6.QtWidgets import QApplication
        title = self.title_edit.text().strip()
        if title:
            db.ex("UPDATE episodes SET title=?, updated_at=? WHERE id=?", (title, db.now(), self.episode_id))
            QApplication.clipboard()  # noop keep
        self.title_edit.clearFocus()

    def _apply_status(self, status: str):
        label, color = STATUS_META.get(status, STATUS_META["pending"])
        self.status_btn.setText(label)
        self.status_btn.setStyleSheet(
            f"QPushButton{{color:{color};border:1px solid {color}44;border-radius:10px;"
            f"background:transparent;font-size:11px;}}")

    def _status_menu(self):
        m = QMenu(self)
        cur = db.q1("SELECT status FROM episodes WHERE id=?", (self.episode_id,))
        for key, (label, _c) in STATUS_META.items():
            act = m.addAction(("● " if cur and cur["status"] == key else "○ ") + label)
            act.triggered.connect(lambda _=False, k=key: self._set_status(k))
        m.exec()

    def _set_status(self, status: str):
        db.ex("UPDATE episodes SET status=?, updated_at=? WHERE id=?", (status, db.now(), self.episode_id))
        self._apply_status(status)
        ok(f"已标记为「{STATUS_META[status][0]}」")

    def _res_menu(self):
        m = QMenu(self)
        for res in ("480p", "720p", "1080p"):
            m.addAction(res).triggered.connect(lambda _=False, r=res: self._set_res(r))
        m.exec()

    def _set_res(self, res: str):
        db.ex("UPDATE episodes SET resolution=?, updated_at=? WHERE id=?", (res, db.now(), self.episode_id))
        self.res_btn.setText(res)

    def _del(self, eid=None, num=None):
        eid = eid or self.episode_id
        ep = db.q1("SELECT episode_number FROM episodes WHERE id=?", (eid,))
        if QMessageBox.question(self, tr("delete_episode"), f"{tr('episode_n').format(ep['episode_number'])} → {tr('delete')}?") == QMessageBox.Yes:
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


class NewEpisodeDialog(QDialog):
    """新建一集:标题 + 分辨率 + 锁定说明。"""

    def __init__(self, parent, number: int):
        super().__init__(parent)
        self.setWindowTitle(tr("add_episode"))
        self.resize(400, 240)
        f = QFormLayout()
        outer = QVBoxLayout(self)
        self.title = QLineEdit(tr("episode_n").format(number))
        self.title.setPlaceholderText("例如:第 2 集 · 归乡")
        f.addRow("标题", self.title)
        self.res = QComboBox()
        for r in ("480p", "720p", "1080p"):
            self.res.addItem(r)
        self.res.setCurrentText("720p")
        f.addRow("分辨率", self.res)
        f.addRow("", W.muted("创建后可在剧集卡上随时修改标题、状态与分辨率。"))
        outer.addLayout(f)
        row = QHBoxLayout()
        cancel = QPushButton(tr("cancel"))
        cancel.clicked.connect(self.reject)
        save = W.primary_btn(tr("add_episode"))
        save.clicked.connect(self.accept)
        row.addStretch(1)
        row.addWidget(cancel)
        row.addWidget(save)
        outer.addLayout(row)

    def data(self):
        return {"title": self.title.text().strip() or tr("episode_n").format(0), "resolution": self.res.currentText()}


class AddAssetDialog(QDialog):
    """＋ 添加资产:角色/场景/道具。"""

    def __init__(self, parent, drama_id: int, kind: str):
        super().__init__(parent)
        self.drama_id, self.kind = drama_id, kind
        label = {"character": "角色", "scene": "场景", "prop": "道具"}[kind]
        self.setWindowTitle(f"＋ 添加{label}")
        self.resize(440, 340)
        f = QFormLayout()
        outer = QVBoxLayout(self)
        outer.addLayout(f)
        self.name = QLineEdit()
        f.addRow("名称", self.name)
        self.role = QComboBox()
        for v, l in (("lead", tr("lead")), ("supporting", tr("supporting")), ("extra", tr("extra"))):
            self.role.addItem(l, v)
        self.desc = QLineEdit()
        self.time = QLineEdit()
        if kind == "character":
            f.addRow("角色定位", self.role)
            f.addRow(tr("appearance"), self.desc)
            f.addRow(tr("styling"), self.time)
        elif kind == "scene":
            f.addRow("地点", self.desc)
            f.addRow("时间", self.time)
        else:
            f.addRow("外貌", self.desc)
        row = QHBoxLayout()
        cancel = QPushButton(tr("cancel"))
        cancel.clicked.connect(self.reject)
        save = W.primary_btn(tr("add"))
        save.clicked.connect(self.accept)
        row.addStretch(1)
        row.addWidget(cancel)
        row.addWidget(save)
        outer.addLayout(row)

    def save(self):
        ts = db.now()
        name = self.name.text().strip()
        if not name:
            return
        if self.kind == "character":
            db.ex("INSERT INTO characters(drama_id,name,role_type,appearance,styling,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                  (self.drama_id, name, self.role.currentData(), self.desc.text().strip(), self.time.text().strip(), ts, ts))
        elif self.kind == "scene":
            db.ex("INSERT INTO scenes(drama_id,name,location,time,prompt,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                  (self.drama_id, name, self.desc.text().strip(), self.time.text().strip(), "", ts, ts))
        else:
            db.ex("INSERT INTO props(drama_id,name,type,description,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                  (self.drama_id, name, "prop", self.desc.text().strip(), ts, ts))


class AssetCard(QFrame):
    """素材卡:点击打开详情编辑。"""
    def __init__(self, kind: str, row: dict, on_open):
        super().__init__()
        self.setObjectName("card")
        self.setFixedSize(210, 210)
        self.setCursor(Qt.PointingHandCursor)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)
        img = QLabel()
        img.setFixedHeight(96)
        img.setAlignment(Qt.AlignCenter)
        img.setPixmap(W.pixmap_from_media(row["image_url"] or row.get("comic_image_url"), 190, 96))
        lay.addWidget(img)
        name = W.h2(row["name"])
        lay.addWidget(name)
        role = {"lead": tr("lead"), "supporting": tr("supporting"), "extra": tr("extra")}.get(row.get("role_type"), row.get("type") or "")
        chips = QHBoxLayout()
        chips.addWidget(W.tag(role))
        if row["image_url"] or row.get("comic_image_url"):
            chips.addWidget(W.tag(tr("generated")))
        chips.addStretch(1)
        lay.addLayout(chips)
        desc = QLabel((row.get("appearance") or row.get("prompt") or row.get("description") or "")[:50] + "…")
        desc.setObjectName("muted")
        desc.setWordWrap(True)
        lay.addWidget(desc)

    def mousePressEvent(self, e):
        import functools
        # 由外部连接点击
        if getattr(self, "_on_click", None):
            self._on_click()
        super().mousePressEvent(e)


class PromoDialog(QDialog):
    """宣传文案:平台 + 格式 + 补充说明 → 生成 → 结果可复制。"""

    def __init__(self, parent, drama_id: int):
        super().__init__(parent)
        self.drama_id = drama_id
        from ..pipeline import promo as promo_pipe
        self.setWindowTitle(tr("promo_copy"))
        self.resize(560, 520)
        root = QVBoxLayout(self)
        root.addWidget(W.h2(tr("promo_copy")))
        f = QFormLayout()
        self.platform = QComboBox()
        for v, n in promo_pipe.PLATFORMS:
            self.platform.addItem(n, v)
        f.addRow(tr("target_platform"), self.platform)
        self.fmt = QComboBox()
        for v, n in promo_pipe.FORMATS:
            self.fmt.addItem(n, v)
        f.addRow(tr("output_format"), self.fmt)
        self.extra = QLineEdit()
        self.extra.setPlaceholderText("补充说明(可选),如 突出性价比")
        f.addRow("补充", self.extra)
        root.addLayout(f)
        self.gen_btn = W.primary_btn("✨ 生成文案")
        self.gen_btn.clicked.connect(self._gen)
        root.addWidget(self.gen_btn)
        self.result = QLineEdit()
        self.result.setReadOnly(True)
        root.addWidget(W.muted("标题"))
        root.addWidget(self.result)
        self.body = QLineEdit()
        self.body.setReadOnly(True)
        root.addWidget(W.muted("正文"))
        root.addWidget(self.body)
        copy_btn = QPushButton("▤ 复制全文")
        copy_btn.clicked.connect(self._copy)
        row = QHBoxLayout()
        row.addWidget(copy_btn)
        row.addStretch(1)
        close = QPushButton(tr("close"))
        close.clicked.connect(self.accept)
        row.addWidget(close)
        root.addLayout(row)

    def _gen(self):
        from ..core.taskmgr import TASKMGR
        pv, fv = self.platform.currentData(), self.fmt.currentData()
        extra = self.extra.text().strip()
        from ..pipeline import promo as promo_pipe
        def job(tid):
            return promo_pipe.generate_promo(self.drama_id, pv, fv, extra=extra)
        def done(tid, result, e):
            if e:
                err(e)
                return
            self.result.setText(result.get("title", ""))
            self.body.setText(result.get("body", ""))
        TASKMGR.submit("promo", job, done, drama_id=self.drama_id)

    def _copy(self):
        from PySide6.QtWidgets import QApplication
        text = f"{self.result.text()}\n\n{self.body.text()}"
        QApplication.clipboard().setText(text)
        ok("已复制到剪贴板")


class ProjectPage(QWidget):
    enter_episode = Signal(int, int)

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
        self.settings_btn = QPushButton("⚙ " + tr("project_settings"))
        self.settings_btn.clicked.connect(self._open_settings)
        head.addWidget(self.settings_btn)
        self.promo_btn = QPushButton("◈ " + tr("promo_copy"))
        self.promo_btn.clicked.connect(self._promo)
        head.addWidget(self.promo_btn)
        root.addLayout(head)

        self.sub = W.muted("")
        root.addWidget(self.sub)

        # 项目封面区在 load() 中按 drama_id 构建
        self.cover_holder = QWidget()
        self.cover_holder.setLayout(QVBoxLayout())
        root.addWidget(self.cover_holder)

        self.tabs = QTabWidget()
        ep_holder = QWidget()
        self.ep_lay = QVBoxLayout(ep_holder)
        self.ep_lay.setContentsMargins(0, 10, 0, 10)
        self.ep_lay.setSpacing(12)
        ep_scroll = QScrollArea()
        ep_scroll.setWidgetResizable(True)
        ep_scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        ep_scroll.setWidget(ep_holder)
        self.tabs.addTab(ep_scroll, tr("episodes"))
        lib_holder = QWidget()
        lib_root = QVBoxLayout(lib_holder)
        lib_bar = QHBoxLayout()
        self.lib_filter = QComboBox()
        for key, label in [("all", tr("filter_all")), ("chars", tr("chars")), ("scenes", tr("scenes")), ("props", tr("props"))]:
            self.lib_filter.addItem(label, key)
        self.lib_filter.currentIndexChanged.connect(self.reload)
        lib_bar.addWidget(self.lib_filter)
        self.add_char = QPushButton("＋ 角色")
        self.add_char.clicked.connect(lambda: self._add_asset("character"))
        self.add_scene = QPushButton("＋ 场景")
        self.add_scene.clicked.connect(lambda: self._add_asset("scene"))
        self.add_prop = QPushButton("＋ 道具")
        self.add_prop.clicked.connect(lambda: self._add_asset("prop"))
        for b in (self.add_char, self.add_scene, self.add_prop):
            lib_bar.addWidget(b)
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
        self._promo_cb = None

    def set_callbacks(self, back_cb, enter_cb, promo_cb=None):
        self._back_cb = back_cb
        self._enter_cb = enter_cb
        self._promo_cb = promo_cb

    def _go_back(self):
        if self._back_cb:
            self._back_cb()

    def _promo(self):
        PromoDialog(self, self.drama_id).exec()

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
        # 项目封面区(3:4 竖版 + 提示词 + 生成 + 放大预览)
        ch = self.cover_holder.layout()
        while ch.count():
            item = ch.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        ch.addWidget(CoverPanel(drama_id, on_changed=self.reload))
        self.reload()

    def _open_settings(self):
        from .asset_dialogs import ProjectSettingsDialog
        if ProjectSettingsDialog(self, self.drama_id).exec() == QDialog.Accepted:
            self.load(self.drama_id)
            ok("项目设置已保存")

    def can_add_episode(self) -> bool:
        """集数限制(对齐原版 canAddEpisode):未配置→不限制;集数=1→单集完结;已达总数→禁止。"""
        d = db.q1("SELECT total_episodes FROM dramas WHERE id=?", (self.drama_id,))
        target = (d["total_episodes"] if d else None)
        if not target or int(target) <= 0:
            return True
        current = db.q1("SELECT COUNT(*) c FROM episodes WHERE drama_id=?", (self.drama_id,))["c"]
        if int(target) == 1:
            return False
        return current < int(target)

    def reload(self):
        while self.ep_lay.count():
            item = self.ep_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        rows = db.q("SELECT * FROM episodes WHERE drama_id=? ORDER BY episode_number", (self.drama_id,))
        counts = {r["episode_id"]: r["c"] for r in db.q(
            "SELECT episode_id, COUNT(*) c FROM storyboards GROUP BY episode_id")}
        for ep in rows:
            d = dict(ep)
            d["storyboard_count"] = counts.get(ep["id"], 0)
            card = EpisodeCard(d, on_changed=self.reload)
            card.enter.connect(self._on_enter)
            card._reload_needed.connect(self.reload)
            self.ep_lay.addWidget(card)
        if self.can_add_episode():
            add = QPushButton("＋ " + tr("add_episode"))
            add.clicked.connect(self._add_episode)
            self.ep_lay.addWidget(add)
        else:
            hint = W.muted("项目已设单集完结(集数=1)或已达计划总集数;如需继续添加,请在「项目设置」里调整")
            self.ep_lay.addWidget(hint)
        self.ep_lay.addStretch(1)
        while self.lib_grid.count():
            item = self.lib_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        f = self.lib_filter.currentData() or "all"
        items = []
        if f in ("all", "chars"):
            items += [("character", dict(r)) for r in db.q("SELECT * FROM characters WHERE drama_id=? ORDER BY id", (self.drama_id,))]
        if f in ("all", "scenes"):
            items += [("scene", dict(r)) for r in db.q("SELECT * FROM scenes WHERE drama_id=? ORDER BY id", (self.drama_id,))]
        if f in ("all", "props"):
            items += [("prop", dict(r)) for r in db.q("SELECT * FROM props WHERE drama_id=? ORDER BY id", (self.drama_id,))]
        cols = max(1, self.lib_grid_holder.width() // 230 or 4)
        for i, (kind, row) in enumerate(items):
            card = AssetCard(kind, row, None)
            card._on_click = lambda k=kind, r=row: self._open_asset(k, r)
            self.lib_grid.addWidget(card, i // cols, i % cols)
        if not items:
            empty = QLabel("暂无素材")
            empty.setObjectName("muted")
            empty.setAlignment(Qt.AlignCenter)
            self.lib_grid.addWidget(empty, 0, 0)

    def _open_asset(self, kind: str, row: dict):
        from .asset_dialogs import AssetDetailDialog
        AssetDetailDialog(self, kind, row, on_changed=self.reload).exec()
        self.reload()

    def _add_asset(self, kind: str):
        dlg = AddAssetDialog(self, self.drama_id, kind)
        if dlg.exec() == QDialog.Accepted:
            dlg.save()
            self.reload()
            ok("已添加")

    def _add_episode(self):
        n = (db.q1("SELECT MAX(episode_number) m FROM episodes WHERE drama_id=?", (self.drama_id,))["m"] or 0) + 1
        dlg = NewEpisodeDialog(self, n)
        if dlg.exec() != QDialog.Accepted:
            return
        data = dlg.data()
        ts = db.now()
        db.ex("INSERT INTO episodes(drama_id,episode_number,title,status,resolution,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
              (self.drama_id, n, data["title"], "pending", data["resolution"], ts, ts))
        self.reload()

    def _on_enter(self, episode_id: int):
        if self._enter_cb:
            self._enter_cb(self.drama_id, episode_id)
