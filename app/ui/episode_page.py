# -*- coding: utf-8 -*-
"""集制作工作台:六阶段流水线(原始内容 → AI 改写 → 视漫制作 → 分镜 → 漫画 → 拼接导出)。

顶栏:文本/图片/视频模型 + 分辨率 + 任务入口(对齐原版 episode.vue)。
侧栏:剧本 / 制作(资产·分镜·漫画) / 导出 三段步骤导航 + 进度。
"""
from __future__ import annotations

import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QHBoxLayout,
                               QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
                               QPushButton, QScrollArea, QSpinBox, QSplitter,
                               QTabWidget, QVBoxLayout, QWidget)

from ..ai import face_swap, image_client, registry, tts_client, video_client
from ..agents import runner
from ..core import config, db
from ..core.i18n import tr
from ..core.taskmgr import TASKMGR
from ..pipeline import comic as comic_pipe
from ..pipeline import extractor as extract_pipe
from ..pipeline import merge as merge_pipe
from ..pipeline import prompts_gen
from ..pipeline import rewriter
from ..pipeline import storyboard as sb_pipe
from ..pipeline import stitch as stitch_pipe
from . import widgets as W

STEPS = ["raw", "rewrite", "assets", "storyboard", "comic", "export"]
STEP_LABELS = {"raw": "raw_content", "rewrite": "ai_rewrite", "assets": "production",
               "storyboard": "storyboard", "comic": "comic", "export": "export_stage"}


class StepNav(QWidget):
    step_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(180)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 20, 8, 20)
        lay.setSpacing(4)
        self._btns: dict[str, QPushButton] = {}
        for group, keys in (("step_script", ["raw", "rewrite"]),
                            ("step_production", ["assets", "storyboard", "comic"]),
                            ("step_export", ["export"])):
            lay.addWidget(W.muted(tr(group)))
            for k in keys:
                b = QPushButton("  " + tr(STEP_LABELS[k]))
                b.setStyleSheet("text-align:left; border:none; background:transparent;")
                b.setCursor(Qt.PointingHandCursor)
                b.clicked.connect(lambda _=False, kk=k: self.step_changed.emit(kk))
                self._btns[k] = b
                lay.addWidget(b)
            lay.addSpacing(8)
        lay.addStretch(1)
        self.progress = QLabel("1/4")
        self.progress.setObjectName("muted")
        lay.addWidget(self.progress)

    def set_active(self, key: str):
        for k, b in self._btns.items():
            b.setStyleSheet(
                "text-align:left; border:none; background:transparent; color:#4b6ef5; font-weight:700;"
                if k == key else "text-align:left; border:none; background:transparent;")


class EpisodePage(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self.drama_id = 0
        self.episode_id = 0
        self._step = "raw"
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 14, 20, 14)
        root.setSpacing(10)

        # 顶栏
        top = QHBoxLayout()
        back = QPushButton("← " + tr("back"))
        back.clicked.connect(self.back_requested.emit)
        top.addWidget(back)
        self.title = W.h2("")
        top.addWidget(self.title)
        top.addStretch(1)
        top.addWidget(QLabel(tr("text_svc") + ":"))
        self.text_model = QComboBox()
        top.addWidget(self.text_model)
        top.addWidget(QLabel(tr("image_svc") + ":"))
        self.image_model = QComboBox()
        top.addWidget(self.image_model)
        top.addWidget(QLabel(tr("video_svc") + ":"))
        self.video_model = QComboBox()
        top.addWidget(self.video_model)
        top.addWidget(QLabel(tr("faceswap_svc") + ":"))
        self.face_model = QComboBox()
        top.addWidget(self.face_model)
        top.addWidget(QLabel(tr("resolution") + ":"))
        self.res_combo = QComboBox()
        for r in ("480p", "720p", "1080p"):
            self.res_combo.addItem(r)
        self.res_combo.setCurrentIndex(1)
        top.addWidget(self.res_combo)
        self.task_btn = QPushButton(tr("tasks"))
        self.task_btn.clicked.connect(self._open_tasks)
        top.addWidget(self.task_btn)
        root.addLayout(top)
        self.subtitle = W.muted("")
        root.addWidget(self.subtitle)

        # 主体:侧栏 + 内容栈
        body = QSplitter(Qt.Horizontal)
        self.nav = StepNav()
        self.nav.step_changed.connect(self._goto_step)
        body.addWidget(self.nav)

        self.stack_holder = QWidget()
        self.stack_lay = QVBoxLayout(self.stack_holder)
        self.stack_lay.setContentsMargins(0, 0, 0, 0)
        self.panels: dict[str, QWidget] = {}
        for k in STEPS:
            p = self._build_panel(k)
            self.panels[k] = p
            self.stack_lay.addWidget(p)
        body.addWidget(self.stack_holder)
        body.setStretchFactor(1, 1)
        root.addWidget(body, 1)
        TASKMGR.updated.connect(self._refresh_status)
        self._loading = False

    # ── 数据加载 ──
    def load(self, drama_id: int, episode_id: int):
        self.drama_id, self.episode_id = drama_id, episode_id
        d = db.q1("SELECT * FROM dramas WHERE id=?", (drama_id,))
        ep = db.q1("SELECT * FROM episodes WHERE id=?", (episode_id,))
        self._drama, self._ep = d, ep
        self.title.setText(f"{d['title']} · {tr('episode_n').format(ep['episode_number'])}")
        nc = db.q1("SELECT COUNT(*) c FROM episode_characters WHERE episode_id=?", (episode_id,))["c"]
        nb = db.q1("SELECT COUNT(*) c FROM storyboards WHERE episode_id=?", (episode_id,))["c"]
        self.subtitle.setText(f"{tr('characters_n', nc)} · {tr('segments', nb)}")
        self.res_combo.setCurrentText(ep["resolution"] or "720p")
        # 小说项目隐藏制作/导出;宣传项目隐藏漫画
        work = d["work_type"]
        for k in ("assets", "storyboard", "export"):
            self.panels[k].setVisible(work != "novel")
        self.panels["comic"].setVisible(work not in ("novel", "promotion", "video_clone"))
        self._reload_models()
        self._reload_raw()
        self._reload_assets()
        self._reload_storyboard()
        self._reload_comic()
        self._reload_export()
        self._goto_step("raw")

    def _reload_models(self):
        for combo, stype in ((self.text_model, "text"), (self.image_model, "image"),
                             (self.video_model, "video"), (self.face_model, "faceswap")):
            combo.clear()
            combo.addItem(tr("configured"), None)
            for r in registry.list_configs(stype):
                combo.addItem(f"{r['remark'] or r['provider']}/{r['model']}", r["id"])
        ep = getattr(self, "_ep", None)
        if ep:
            for combo, field in ((self.text_model, "image_config_id"),):
                pass  # 集锁定模型后续扩展;默认走全局默认项

    def _goto_step(self, key: str):
        self._step = key
        self.nav.set_active(key)
        for k, p in self.panels.items():
            p.setVisible(k == key)
        stage = {"raw": "1/4", "rewrite": "1/4", "assets": "2/4", "storyboard": "3/4",
                 "comic": "3/4", "export": "4/4"}[key]
        self.nav.progress.setText(stage)

    def _open_tasks(self):
        from .task_panel import TaskPanel
        TaskPanel(self.episode_id, self).exec()

    def _refresh_status(self):
        if self._loading or not self.episode_id:
            return
        self._loading = True
        try:
            nb = db.q1("SELECT COUNT(*) c FROM storyboards WHERE episode_id=?", (self.episode_id,))["c"]
            nc = db.q1("SELECT COUNT(*) c FROM episode_characters WHERE episode_id=?", (self.episode_id,))["c"]
            self.subtitle.setText(f"{tr('characters_n', nc)} · {tr('segments', nb)}")
            stats = TASKMGR.ep_video_stats(self.episode_id)
            self.sb_stat.setText(f"{tr('in_progress')} {stats['processing']} · {tr('done')} {stats['completed']} · {tr('failed')} {stats['failed']}")
            active = TASKMGR.active_count()
            self.task_btn.setText(f"{tr('tasks')}" + (f" · {active}" if active else ""))
        finally:
            self._loading = False

    # ── 阶段① 原始内容 ──
    def _build_panel(self, key: str) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 8, 8, 8)
        getattr(self, f"_panel_{key}")(lay)
        lay.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        scroll.setWidget(w)
        return scroll

    def _panel_raw(self, lay):
        self.raw_edit = QPlainTextEdit()
        self.raw_edit.setPlaceholderText(tr("paste_hint"))
        self.raw_edit.setMinimumHeight(360)
        bar = QHBoxLayout()
        self.words_spin = QSpinBox()
        self.words_spin.setRange(0, 200000)
        self.words_spin.setSpecialValueText("∞")
        self.style_edit = QLineEdit()
        self.style_edit.setPlaceholderText(tr("style_label"))
        save_btn = QPushButton(tr("save"))
        save_btn.clicked.connect(self._save_raw)
        novel_btn = W.primary_btn(tr("ai_novel"))
        novel_btn.clicked.connect(self._ai_novel)
        batch_btn = QPushButton(tr("batch_write"))
        batch_btn.clicked.connect(self._batch_novel)
        bar.addWidget(QLabel(tr("target_words")))
        bar.addWidget(self.words_spin)
        bar.addWidget(QLabel(tr("style_label")))
        bar.addWidget(self.style_edit, 1)
        bar.addWidget(novel_btn)
        bar.addWidget(batch_btn)
        bar.addWidget(save_btn)
        lay.addLayout(bar)
        lay.addWidget(self.raw_edit)

    def _reload_raw(self):
        ep = self._ep
        self.raw_edit.setPlainText(ep["content"] or "")
        self.words_spin.setValue(ep["target_words"] or 0)
        self.style_edit.setText(db.get_setting("novel_style", "爽感快节奏网文:短句为主,情绪外露,段落简短,冲突直给,爽点前置"))

    def _save_raw(self):
        db.ex("UPDATE episodes SET content=?, target_words=?, updated_at=? WHERE id=?",
              (self.raw_edit.toPlainText(), self.words_spin.value(), db.now(), self.episode_id))
        self._ep = db.q1("SELECT * FROM episodes WHERE id=?", (self.episode_id,))
        QMessageBox.information(self, tr("save"), "OK")

    def _ai_novel(self):
        from ..pipeline import novel as novel_pipe
        def job(tid):
            if not db.q1("SELECT novel_outline FROM dramas WHERE id=?", (self.drama_id,))["novel_outline"]:
                idea = self.raw_edit.toPlainText().strip()[:6000] or self._drama["title"]
                novel_pipe.plan_novel(self.drama_id, idea, config_id=self.text_model.currentData())
            return novel_pipe.write_chapter(self.episode_id, config_id=self.text_model.currentData())
        def done(tid, result, err):
            self._reload_raw() if not err else QMessageBox.warning(self, "AI", str(err)[:400])
        self._save_raw_silent()
        TASKMGR.submit("novel", job, done, episode_id=self.episode_id, drama_id=self.drama_id)

    def _batch_novel(self):
        self._save_raw_silent()
        n = db.q1("SELECT MAX(episode_number) m FROM episodes WHERE drama_id=?", (self.drama_id,))["m"] or 0
        want, ok = QInputDialog_getInt(self, tr("batch_write"), "N =", 3, 1, 20)
        if not ok:
            return
        from ..pipeline import novel as novel_pipe
        ts = db.now()
        ids = []
        for i in range(want):
            n += 1
            ids.append(db.ex("INSERT INTO episodes(drama_id,episode_number,title,status,resolution,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                             (self.drama_id, n, tr("episode_n").format(n), "pending", "720p", ts, ts)))
        def job(tid):
            outs = []
            for eid in ids:
                outs.append(novel_pipe.write_chapter(eid, config_id=self.text_model.currentData()))
            return outs
        def done(tid, result, err):
            if err:
                QMessageBox.warning(self, "AI", str(err)[:400])
        TASKMGR.submit("novel_batch", job, done, episode_id=self.episode_id, drama_id=self.drama_id)

    def _save_raw_silent(self):
        db.ex("UPDATE episodes SET content=?, target_words=?, updated_at=? WHERE id=?",
              (self.raw_edit.toPlainText(), self.words_spin.value(), db.now(), self.episode_id))
        db.set_setting("novel_style", self.style_edit.text().strip())
        self._ep = db.q1("SELECT * FROM episodes WHERE id=?", (self.episode_id,))

    # ── 阶段② AI 改写 ──
    def _panel_rewrite(self, lay):
        self.script_edit = QPlainTextEdit()
        self.script_edit.setMinimumHeight(360)
        bar = QHBoxLayout()
        rewrite_btn = W.primary_btn(tr("rewrite"))
        rewrite_btn.clicked.connect(self._rewrite)
        save_btn = QPushButton(tr("save"))
        save_btn.clicked.connect(self._save_script)
        bar.addWidget(rewrite_btn)
        bar.addWidget(save_btn)
        bar.addStretch(1)
        lay.addLayout(bar)
        lay.addWidget(self.script_edit)

    def _reload_rewrite(self):
        self.script_edit.setPlainText(self._ep["script_content"] or "")

    def _rewrite(self):
        self._save_raw_silent()
        def job(tid):
            return rewriter.rewrite_script(self.episode_id, self.style_edit.text().strip(),
                                           config_id=self.text_model.currentData())
        def done(tid, result, err):
            if err:
                QMessageBox.warning(self, "AI", str(err)[:400])
            else:
                self._ep = db.q1("SELECT * FROM episodes WHERE id=?", (self.episode_id,))
                self.script_edit.setPlainText(result or "")
        TASKMGR.submit("script", job, done, episode_id=self.episode_id, drama_id=self.drama_id)

    def _save_script(self):
        db.ex("UPDATE episodes SET script_content=?, updated_at=? WHERE id=?",
              (self.script_edit.toPlainText(), db.now(), self.episode_id))
        self._ep = db.q1("SELECT * FROM episodes WHERE id=?", (self.episode_id,))

    # ── 阶段③ 视漫制作(资产) ──
    def _panel_assets(self, lay):
        bar = QHBoxLayout()
        re_chars = QPushButton(tr("re_extract_chars"))
        re_chars.clicked.connect(lambda: self._extract("characters"))
        re_scenes = QPushButton(tr("re_extract_scenes"))
        re_scenes.clicked.connect(lambda: self._extract("scenes"))
        re_props = QPushButton(tr("re_extract_props"))
        re_props.clicked.connect(lambda: self._extract("props"))
        extract_all = W.primary_btn(tr("extract"))
        extract_all.clicked.connect(lambda: self._extract("all"))
        b_chars = QPushButton(tr("batch_chars"))
        b_chars.clicked.connect(lambda: self._batch_images("characters"))
        b_scenes = QPushButton(tr("batch_scenes"))
        b_scenes.clicked.connect(lambda: self._batch_images("scenes"))
        b_props = QPushButton(tr("batch_props"))
        b_props.clicked.connect(lambda: self._batch_images("props"))
        for b in (re_chars, re_scenes, re_props, extract_all, b_chars, b_scenes, b_props):
            bar.addWidget(b)
        bar.addStretch(1)
        lay.addLayout(bar)
        self.asset_stat = QLabel("")
        self.asset_stat.setObjectName("muted")
        lay.addWidget(self.asset_stat)
        self.asset_empty = QLabel("—" + tr("extract") + "—")
        self.asset_empty.setObjectName("muted")
        self.asset_empty.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.asset_empty)
        self.asset_list = QVBoxLayout()
        lay.addLayout(self.asset_list)

    def _extract(self, scope: str):
        def job(tid):
            return extract_pipe.extract_assets(self.episode_id, config_id=self.text_model.currentData())
        def done(tid, result, err):
            if err:
                QMessageBox.warning(self, "AI", str(err)[:400])
            else:
                self._reload_assets()
        TASKMGR.submit("extract", job, done, episode_id=self.episode_id, drama_id=self.drama_id)

    def _reload_assets(self):
        if not getattr(self, "asset_list", None):
            return
        while self.asset_list.count():
            item = self.asset_list.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        rows: list[dict] = []
        for r in db.q("SELECT * FROM characters WHERE drama_id=? ORDER BY id", (self.drama_id,)):
            rows.append({**dict(r), "kind": "1"})
        for r in db.q("SELECT * FROM scenes WHERE drama_id=? ORDER BY id", (self.drama_id,)):
            rows.append({**dict(r), "kind": "2"})
        for r in db.q("SELECT * FROM props WHERE drama_id=? ORDER BY id", (self.drama_id,)):
            rows.append({**dict(r), "kind": "3"})
        total = ready = 0
        for r in rows:
            total += 1
            if r["image_url"]:
                ready += 1
            self.asset_list.addWidget(self._asset_row(r))
        self.asset_empty.setVisible(total == 0)
        self.asset_stat.setText(tr("ready_n").format(ready, total))

    def _asset_row(self, row: dict) -> QWidget:
        box = W.make_card()
        lay = QHBoxLayout(box)
        lay.setContentsMargins(10, 8, 10, 8)
        info = QVBoxLayout()
        head = QHBoxLayout()
        name = W.h2(row["name"])
        head.addWidget(name)
        kind_label = {"1": tr("chars"), "2": tr("scenes"), "3": tr("props")}.get(str(row["kind"]), "")
        head.addWidget(W.tag(kind_label))
        if row.get("role_type"):
            head.addWidget(W.tag({"lead": tr("lead"), "supporting": tr("supporting"), "extra": tr("extra")}.get(row["role_type"], "")))
        if row["image_url"]:
            head.addWidget(W.tag(tr("generated")))
        head.addStretch(1)
        info.addLayout(head)
        desc = (row.get("appearance") or row.get("prompt") or row.get("description") or "")
        lab = QLabel((desc or "")[:100] + ("…" if len(desc or "") > 100 else ""))
        lab.setObjectName("muted")
        lab.setWordWrap(True)
        info.addWidget(lab)
        if row["final_prompt"]:
            fp = QLabel(tr("final_prompt") + ": " + row["final_prompt"][:80] + "…")
            fp.setObjectName("muted")
            info.addWidget(fp)
        lay.addLayout(info, 1)
        img = QLabel()
        img.setPixmap(W.pixmap_from_media(row["image_url"], 96))
        lay.addWidget(img)
        btns = QVBoxLayout()
        kid = {"1": ("characters", "character"), "2": ("scenes", "scene"), "3": ("props", "prop")}[str(row["kind"])]
        gen_prompt = QPushButton("AI " + tr("final_prompt"))
        gen_prompt.clicked.connect(lambda _=False, r=row, k=kid[1]: self._gen_prompt(r["id"], k))
        redraw = QPushButton(tr("redraw"))
        redraw.clicked.connect(lambda _=False, r=row, t=kid[0]: self._gen_image(r["id"], t))
        upload = QPushButton(tr("upload"))
        upload.clicked.connect(lambda _=False, r=row, t=kid[0]: self._upload_image(r["id"], t))
        if str(row["kind"]) == "1":
            swap = QPushButton(tr("face_swap"))
            swap.clicked.connect(lambda _=False, r=row: self._face_swap(r["id"]))
            btns.addWidget(swap)
        for b in (gen_prompt, redraw, upload):
            btns.addWidget(b)
        lay.addLayout(btns)
        return box

    def _gen_prompt(self, row_id: int, kind: str):
        fn = {"character": prompts_gen.character_prompt, "scene": prompts_gen.scene_prompt,
              "prop": prompts_gen.prop_prompt}[kind]
        def job(tid):
            return fn(row_id, config_id=self.text_model.currentData())
        def done(tid, result, err):
            if err:
                QMessageBox.warning(self, "AI", str(err)[:400])
            self._reload_assets()
        TASKMGR.submit("prompt", job, done, drama_id=self.drama_id, character_id=row_id if kind == "character" else None)

    def _gen_image(self, row_id: int, table: str):
        col = {"characters": "final_prompt", "scenes": "final_prompt", "props": "final_prompt"}[table]

        def job(tid):
            row = db.q1(f"SELECT * FROM {table} WHERE id=?", (row_id,))
            fp = row["final_prompt"]
            if not fp:
                kind = {"characters": "character", "scenes": "scene", "props": "prop"}[table]
                fp = {"character": prompts_gen.character_prompt, "scene": prompts_gen.scene_prompt,
                      "prop": prompts_gen.prop_prompt}[kind](row_id, config_id=self.text_model.currentData())
            out, _provider = image_client.generate_image(fp, config_id=self.image_model.currentData())
            url = config.path_to_media_url(out)
            db.ex(f"UPDATE {table} SET image_url=?, updated_at=? WHERE id=?", (url, db.now(), row_id))
            return url
        def done(tid, result, err):
            if err:
                QMessageBox.warning(self, "AI", str(err)[:400])
            self._reload_assets()
        TASKMGR.submit("image", job, done, drama_id=self.drama_id)

    def _batch_images(self, table: str):
        rows = db.q(f"SELECT id FROM {table} WHERE drama_id=? AND image_url IS NULL", (self.drama_id,))
        for r in rows:
            self._gen_image(r["id"], table)

    def _upload_image(self, row_id: int, table: str):
        p, _ = QFileDialog.getOpenFileName(self, tr("upload"), "", "Images (*.png *.jpg *.jpeg *.webp)")
        if not p:
            return
        import shutil
        dst = config.STATIC_DIR / "uploads" / f"up_{row_id}_{config.uuid.uuid4().hex[:6]}{p[p.rfind('.'):][:8]}"
        shutil.copy(p, dst)
        db.ex(f"UPDATE {table} SET image_url=?, updated_at=? WHERE id=?",
              (config.path_to_media_url(dst), db.now(), row_id))
        self._reload_assets()

    def _face_swap(self, character_id: int):
        cfg_id = self.face_model.currentData()
        ok, msg = face_swap.health(config_id=cfg_id)
        if not ok:
            QMessageBox.warning(self, tr("face_swap"), f"换脸服务不可达:{msg}")
            return
        c = db.q1("SELECT * FROM characters WHERE id=?", (character_id,))
        if not c["image_url"]:
            QMessageBox.information(self, tr("face_swap"), "请先生成或上传角色形象图")
            return
        # 用项目内另一角色/或上传脸源:这里弹出选择脸源图片
        p, _ = QFileDialog.getOpenFileName(self, tr("face_swap"), "", "Images (*.png *.jpg *.jpeg)")
        if not p:
            return
        def job(tid):
            target = config.media_url_to_path(c["image_url"])
            out = face_swap.swap_one(target, p, config_id=cfg_id)
            db.ex("UPDATE characters SET image_url=?, updated_at=? WHERE id=?",
                  (config.path_to_media_url(out), db.now(), character_id))
            return str(out)
        def done(tid, result, err):
            if err:
                QMessageBox.warning(self, tr("face_swap"), str(err)[:400])
            self._reload_assets()
        TASKMGR.submit("image", job, done, drama_id=self.drama_id)

    # ── 阶段④ 分镜 ──
    def _panel_storyboard(self, lay):
        bar = QHBoxLayout()
        split_btn = W.primary_btn(tr("re_split"))
        split_btn.clicked.connect(self._split_sb)
        prompts_btn = QPushButton(tr("batch_prompts"))
        prompts_btn.clicked.connect(self._batch_vp)
        video_btn = W.primary_btn(tr("batch_video"))
        video_btn.clicked.connect(self._batch_video)
        bar.addWidget(split_btn)
        bar.addWidget(prompts_btn)
        bar.addWidget(video_btn)
        bar.addStretch(1)
        self.sb_stat = QLabel("")
        self.sb_stat.setObjectName("muted")
        bar.addWidget(self.sb_stat)
        lay.addLayout(bar)
        self.sb_meta = QLabel("")
        self.sb_meta.setObjectName("muted")
        lay.addWidget(self.sb_meta)
        self.sb_list = QVBoxLayout()
        lay.addLayout(self.sb_list)

    def _reload_storyboard(self):
        if not getattr(self, "sb_list", None):
            return
        while self.sb_list.count():
            item = self.sb_list.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        rows = db.q("SELECT * FROM storyboards WHERE episode_id=? ORDER BY storyboard_number", (self.episode_id,))
        total = sum(r["duration"] or 0 for r in rows)
        self.sb_meta.setText(tr("segments", len(rows)) + f" · {tr('total_dur', int(total))}")
        for r in rows:
            self.sb_list.addWidget(self._sb_row(dict(r)))
        self._refresh_status()

    def _sb_row(self, r: dict) -> QWidget:
        box = W.make_card()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(12, 8, 12, 8)
        head = QHBoxLayout()
        num = QLabel(f"#{r['storyboard_number']:02d}")
        num.setObjectName("h2")
        head.addWidget(num)
        status = (tr("done") if r["video_url"] else
                  (tr("in_progress") if r.get("status") == "processing" else tr("pending")))
        head.addWidget(W.tag(status))
        head.addWidget(W.tag(f"{int(r['duration'] or 0)}s"))
        head.addStretch(1)
        redo = QPushButton(tr("redraw"))
        redo.clicked.connect(lambda _=False, i=r["id"]: self._one_video(i))
        tts_btn = QPushButton("🔊")
        tts_btn.setToolTip(tr("narration"))
        tts_btn.clicked.connect(lambda _=False, i=r["id"]: self._one_tts(i))
        play = QPushButton("▶")
        play.setToolTip("播放")
        play.setEnabled(bool(r["video_url"]))
        play.clicked.connect(lambda _=False, u=r["video_url"]: self._play_video(u))
        head.addWidget(tts_btn)
        head.addWidget(redo)
        head.addWidget(play)
        lay.addLayout(head)
        content = QLabel(r["content"] or "")
        content.setWordWrap(True)
        lay.addWidget(content)
        narr = QLineEdit(r["narration"] or "")
        narr.setPlaceholderText(tr("narration_hint"))
        narr.editingFinished.connect(lambda li=r["id"], t=narr: db.ex(
            "UPDATE storyboards SET narration=? WHERE id=?", (t.text(), li)))
        lay.addWidget(narr)
        return box

    def _split_sb(self):
        def job(tid):
            return sb_pipe.split_storyboards(self.episode_id, self._drama["aspect_ratio"],
                                             config_id=self.text_model.currentData())
        def done(tid, result, err):
            if err:
                QMessageBox.warning(self, "AI", str(err)[:400])
            self._reload_storyboard()
        TASKMGR.submit("storyboard", job, done, episode_id=self.episode_id, drama_id=self.drama_id)

    def _batch_vp(self):
        def job(tid):
            return sb_pipe.gen_video_prompts(self.episode_id, config_id=self.text_model.currentData())
        def done(tid, result, err):
            if err:
                QMessageBox.warning(self, "AI", str(err)[:400])
            else:
                QMessageBox.information(self, tr("batch_prompts"), f"OK: {result}")
        TASKMGR.submit("prompt", job, done, episode_id=self.episode_id)

    def _one_video(self, sb_id: int):
        self._gen_video_job(sb_id)

    def _batch_video(self):
        rows = db.q("SELECT id FROM storyboards WHERE episode_id=? AND video_url IS NULL", (self.episode_id,))
        if not rows:
            QMessageBox.information(self, tr("batch_video"), "全部镜头已有视频")
            return
        for r in rows:
            self._gen_video_job(r["id"])

    def _gen_video_job(self, sb_id: int):
        res = self.res_combo.currentText()
        def job(tid):
            sb = db.q1("SELECT * FROM storyboards WHERE id=?", (sb_id,))
            db.ex("UPDATE storyboards SET status='processing' WHERE id=?", (sb_id,))
            prompt = sb["video_prompt"] or sb["content"]
            path, _p = video_client.generate_video(
                prompt[:1500], resolution=res, duration=int(sb["duration"] or 8),
                first_frame=sb["first_frame_image"], config_id=self.video_model.currentData())
            db.ex("UPDATE storyboards SET video_url=?, status='completed', updated_at=? WHERE id=?",
                  (config.path_to_media_url(path), db.now(), sb_id))
            return str(path)
        def done(tid, result, err):
            if err:
                db.ex("UPDATE storyboards SET status='failed' WHERE id=?", (sb_id,))
                QMessageBox.warning(self, tr("batch_video"), str(err)[:400])
            self._reload_storyboard()
        TASKMGR.submit("video", job, done, episode_id=self.episode_id, storyboard_id=sb_id)

    def _one_tts(self, sb_id: int):
        def job(tid):
            sb = db.q1("SELECT * FROM storyboards WHERE id=?", (sb_id,))
            text = (sb["narration"] or "").strip() or (sb["content"] or "")[:120]
            if not text:
                raise RuntimeError("无旁白文本")
            p = tts_client.synthesize(text, target_duration=sb["duration"], config_id=None)
            db.ex("UPDATE storyboards SET narration_audio_url=?, updated_at=? WHERE id=?",
                  (config.path_to_media_url(p), db.now(), sb_id))
            return str(p)
        def done(tid, result, err):
            if err:
                QMessageBox.warning(self, "🔊", str(err)[:400])
        TASKMGR.submit("tts", job, done, episode_id=self.episode_id, storyboard_id=sb_id)

    def _play_video(self, url: str | None):
        if not url:
            return
        import os
        import subprocess
        p = config.media_url_to_path(url)
        if p.exists():
            os.startfile(str(p))  # noqa  Windows 默认播放器

    # ── 阶段⑤ 漫画 ──
    def _panel_comic(self, lay):
        bar = QHBoxLayout()
        re_panel = W.primary_btn(tr("re_split"))
        re_panel.clicked.connect(self._split_panels)
        batch_img = W.primary_btn(tr("batch_image"))
        batch_img.clicked.connect(self._batch_comic)
        stitch_btn = QPushButton(tr("stitch_long"))
        stitch_btn.clicked.connect(self._stitch)
        bar.addWidget(re_panel)
        bar.addWidget(batch_img)
        bar.addWidget(stitch_btn)
        bar.addStretch(1)
        self.comic_stat = QLabel("")
        self.comic_stat.setObjectName("muted")
        bar.addWidget(self.comic_stat)
        lay.addLayout(bar)
        self.comic_list = QVBoxLayout()
        lay.addLayout(self.comic_list)

    def _reload_comic(self):
        if not getattr(self, "comic_list", None):
            return
        while self.comic_list.count():
            item = self.comic_list.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        rows = db.q("SELECT * FROM comic_panels WHERE episode_id=? ORDER BY panel_number", (self.episode_id,))
        done_n = sum(1 for r in rows if r["image_url"])
        self.comic_stat.setText(tr("panels_n", len(rows)) + " · " + tr("images_done", done_n, len(rows)))
        for r in rows:
            box = W.make_card()
            lay = QHBoxLayout(box)
            lay.setContentsMargins(10, 8, 10, 8)
            img = QLabel()
            img.setPixmap(W.pixmap_from_media(r["image_url"], 110))
            img.setFixedWidth(120)
            lay.addWidget(img)
            info = QVBoxLayout()
            head = QHBoxLayout()
            head.addWidget(W.h2(f"#{r['panel_number']:02d}"))
            if r["image_url"]:
                head.addWidget(W.tag(tr("generated")))
            head.addStretch(1)
            redo = QPushButton(tr("redraw"))
            redo.clicked.connect(lambda _=False, i=r["id"]: self._one_panel_image(i))
            head.addWidget(redo)
            info.addLayout(head)
            d = QLabel(r["description"] or "")
            d.setWordWrap(True)
            info.addWidget(d)
            narr = QLineEdit(r["narration"] or "")
            narr.setPlaceholderText(tr("narration_hint"))
            narr.editingFinished.connect(lambda li=r["id"], t=narr: db.ex(
                "UPDATE comic_panels SET narration=? WHERE id=?", (t.text(), li)))
            info.addWidget(narr)
            lay.addLayout(info, 1)
            self.comic_list.addWidget(box)

    def _split_panels(self):
        def job(tid):
            return comic_pipe.split_panels(self.episode_id, config_id=self.text_model.currentData())
        def done(tid, result, err):
            if err:
                QMessageBox.warning(self, "AI", str(err)[:400])
            self._reload_comic()
        TASKMGR.submit("comic", job, done, episode_id=self.episode_id)

    def _one_panel_image(self, panel_id: int):
        def job(tid):
            fp = comic_pipe.panel_image_prompt(panel_id, self.drama_id, config_id=self.text_model.currentData())
            out, _p = image_client.generate_image(fp, config_id=self.image_model.currentData())
            db.ex("UPDATE comic_panels SET image_url=?, updated_at=? WHERE id=?",
                  (config.path_to_media_url(out), db.now(), panel_id))
            return str(out)
        def done(tid, result, err):
            if err:
                QMessageBox.warning(self, "AI", str(err)[:400])
            self._reload_comic()
        TASKMGR.submit("image", job, done, episode_id=self.episode_id)

    def _batch_comic(self):
        rows = db.q("SELECT id FROM comic_panels WHERE episode_id=? AND image_url IS NULL", (self.episode_id,))
        for r in rows:
            self._one_panel_image(r["id"])

    def _stitch(self):
        def job(tid):
            return stitch_pipe.stitch_panels(self.episode_id)
        def done(tid, result, err):
            if err:
                QMessageBox.warning(self, tr("stitch_long"), str(err)[:400])
            else:
                import os
                os.startfile(result)  # noqa
        TASKMGR.submit("stitch", job, done, episode_id=self.episode_id)

    # ── 阶段⑥ 拼接导出 ──
    def _panel_export(self, lay):
        top = QHBoxLayout()
        mark = W.primary_btn(tr("mark_done"))
        mark.clicked.connect(self._mark_done)
        refresh = QPushButton(tr("refresh"))
        refresh.clicked.connect(self._reload_export)
        top.addWidget(mark)
        top.addWidget(refresh)
        top.addStretch(1)
        lay.addLayout(top)
        self.merge_list = QVBoxLayout()
        lay.addWidget(W.h2(tr("merge_list")))
        self.merge_empty = QLabel("—")
        self.merge_empty.setObjectName("muted")
        lay.addWidget(self.merge_empty)
        lay.addLayout(self.merge_list)
        lay.addWidget(W.h2(tr("shot_materials")))
        bar = QHBoxLayout()
        clear = QPushButton(tr("clear_selection"))
        clear.clicked.connect(self._clear_sel)
        self.merge_btn = W.primary_btn(tr("merge_selected", 0))
        self.merge_btn.clicked.connect(self._merge)
        bar.addWidget(clear)
        bar.addWidget(self.merge_btn)
        bar.addStretch(1)
        lay.addLayout(bar)
        self.shot_checks: dict[int, QCheckBox] = {}
        self.shot_list = QVBoxLayout()
        lay.addLayout(self.shot_list)

    def _reload_export(self):
        if not getattr(self, "merge_list", None):
            return
        while self.merge_list.count():
            item = self.merge_list.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for m in db.q("SELECT * FROM video_merges WHERE episode_id=? ORDER BY id DESC LIMIT 8", (self.episode_id,)):
            box = W.make_card()
            lay = QHBoxLayout(box)
            lay.setContentsMargins(10, 6, 10, 6)
            lay.addWidget(QLabel(f"{(m['created_at'] or '')[:16].replace('T',' ')} · {int(m['duration'] or 0)}s · {m['status']}"))
            lay.addStretch(1)
            dl = QPushButton(tr("download"))
            dl.clicked.connect(lambda _=False, u=m["merged_url"]: self._open_file(u))
            lay.addWidget(dl)
            self.merge_list.addWidget(box)
        self.merge_empty.setVisible(db.q1("SELECT id FROM video_merges WHERE episode_id=? LIMIT 1", (self.episode_id,)) is None)
        while self.shot_list.count():
            item = self.shot_list.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.shot_checks.clear()
        for r in db.q("SELECT * FROM storyboards WHERE episode_id=? ORDER BY storyboard_number", (self.episode_id,)):
            if not (r["video_url"] or r["composed_video_url"]):
                continue
            cb = QCheckBox(f"#{r['storyboard_number']:02d} · {int(r['duration'] or 0)}s · {(r['content'] or '')[:46]}…")
            cb.setChecked(True)
            cb.stateChanged.connect(self._update_sel)
            self.shot_checks[r["id"]] = cb
            self.shot_list.addWidget(cb)
        self._update_sel()

    def _update_sel(self):
        n = sum(1 for cb in self.shot_checks.values() if cb.isChecked())
        self.merge_btn.setText(tr("merge_selected", n))

    def _clear_sel(self):
        for cb in self.shot_checks.values():
            cb.setChecked(False)

    def _merge(self):
        ids = [i for i, cb in self.shot_checks.items() if cb.isChecked()]
        if len(ids) < 2:
            QMessageBox.information(self, tr("export_stage"), "≥2")
            return
        def job(tid):
            return merge_pipe.merge_episode(self.episode_id, ids)
        def done(tid, result, err):
            if err:
                QMessageBox.warning(self, tr("export_stage"), str(err)[:400])
            else:
                import os
                os.startfile(str(result))  # noqa
            self._reload_export()
        TASKMGR.submit("merge", job, done, episode_id=self.episode_id)

    def _mark_done(self):
        db.ex("UPDATE episodes SET status='completed', updated_at=? WHERE id=?", (db.now(), self.episode_id))
        QMessageBox.information(self, tr("mark_done"), "OK")

    def _open_file(self, url: str | None):
        if url:
            import os
            p = config.media_url_to_path(url)
            if p.exists():
                os.startfile(str(p))  # noqa


def QInputDialog_getInt(parent, title, label, value=1, lo=1, hi=99):
    from PySide6.QtWidgets import QInputDialog
    return QInputDialog.getInt(parent, title, label, value, lo, hi)
