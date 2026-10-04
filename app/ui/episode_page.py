# -*- coding: utf-8 -*-
"""集制作工作台:六阶段流水线(原始内容 → AI 改写 → 视漫制作 → 分镜 → 漫画 → 拼接导出)。

顶栏:文本/图片/视频模型 + 分辨率 + 任务入口(对齐原版 episode.vue)。
侧栏:剧本 / 制作(资产·分镜·漫画) / 导出 三段步骤导航 + 进度。
"""
from __future__ import annotations

import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QHBoxLayout,
                               QSizePolicy,
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
from .toast import err, info, ok, warn

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
        self.status_lab = QLabel("")
        self.status_lab.setObjectName("muted")
        top.addWidget(self.status_lab)
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
        self._sb_split_running = False
        self._sb_split_task = 0

    # ── 数据加载 ──
    def load(self, drama_id: int, episode_id: int):
        self.drama_id, self.episode_id = drama_id, episode_id
        d = db.q1("SELECT * FROM dramas WHERE id=?", (drama_id,))
        ep = db.q1("SELECT * FROM episodes WHERE id=?", (episode_id,))
        self._drama, self._ep = d, ep
        self.title.setText(f"{d['title']} · {tr('episode_n').format(ep['episode_number'])}")
        # 应用项目级内容语言(对齐原版 a6a47dc):进入不同项目时切换产出语言
        from ..core.config import resolve_content_language
        from ..core.i18n import set_language
        self._drama_lang = resolve_content_language(drama_id)
        set_language(self._drama_lang)
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
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(tr("configured"), None)
            for r in registry.list_configs(stype):
                combo.addItem(f"{r['remark'] or r['provider']}/{r['model']}", r["id"])
            # 恢复上次选择(全局记忆)
            saved = db.get_setting(f"yihao.model.{stype}")
            if saved:
                i = combo.findData(int(saved))
                if i >= 0:
                    combo.setCurrentIndex(i)
            combo.blockSignals(False)
            combo.currentIndexChanged.connect(lambda _i, c=combo, s=stype: self._remember_model(c, s))
        # 集级锁定(创建集后首次生成即锁定图片/视频配置,对齐原版)
        ep = getattr(self, "_ep", None)
        if ep:
            for combo, col in ((self.image_model, "image_config_id"), (self.video_model, "video_config_id")):
                locked = ep[col]
                if locked:
                    i = combo.findData(locked)
                    if i >= 0:
                        combo.blockSignals(True)
                        combo.setCurrentIndex(i)
                        combo.setItemText(i, "🔒 " + combo.itemText(i))
                        combo.blockSignals(False)
        self.video_model.currentIndexChanged.connect(self._sync_res_tiers)
        self._sync_res_tiers()
        saved_res = db.get_setting("yihao.resolution")
        if saved_res:
            i = self.res_combo.findText(saved_res)
            if i >= 0:
                self.res_combo.setCurrentIndex(i)
        self.res_combo.currentTextChanged.connect(lambda t: db.set_setting("yihao.resolution", t))

    def _remember_model(self, combo, stype: str):
        cid = combo.currentData()
        if cid:
            db.set_setting(f"yihao.model.{stype}", str(cid))
        # 集级锁定回写
        ep = getattr(self, "_ep", None)
        if ep:
            col = {"image": "image_config_id", "video": "video_config_id"}.get(stype)
            if col:
                db.ex(f"UPDATE episodes SET {col}=?, updated_at=? WHERE id=?",
                      (cid, db.now(), self.episode_id))
                self._ep = db.q1("SELECT * FROM episodes WHERE id=?", (self.episode_id,))

    def _sync_res_tiers(self):
        """分辨率档位随视频厂商联动(对齐原版 RESOLUTION_TIERS)。"""
        from ..ai.video_client import RESOLUTION_TIERS
        cid = self.video_model.currentData()
        provider = None
        if cid:
            row = db.q1("SELECT provider FROM ai_service_configs WHERE id=?", (cid,))
            provider = row["provider"] if row else None
        tiers = RESOLUTION_TIERS.get(provider or "", ["480p", "720p", "1080p"])
        cur = self.res_combo.currentText()
        self.res_combo.blockSignals(True)
        self.res_combo.clear()
        for t in tiers:
            self.res_combo.addItem(t)
        if cur in tiers:
            self.res_combo.setCurrentText(cur)
        self.res_combo.blockSignals(False)


    def _set_busy(self, on: bool, label: str = ""):
        """D 类:全局忙碌态(按钮禁用 + 状态栏提示),避免重复点击。"""
        self._busy = on
        self.status_lab.setText(("⏳ " + label) if on else "")

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
    # 主编辑区需要撑满剩余高度(自身内部滚动),其余阶段由外层滚动区承载
    FILL_PANELS = ("raw", "rewrite")

    def _build_panel(self, key: str) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 8, 8, 8)
        getattr(self, f"_panel_{key}")(lay)
        if key not in self.FILL_PANELS:
            lay.addStretch(1)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
            scroll.setWidget(w)
            return scroll
        # 撑满型:直接返回,文本框自身内部滚动
        return w

    def _panel_raw(self, lay):
        self.raw_edit = QPlainTextEdit()
        self.raw_edit.setPlaceholderText(tr("paste_hint"))
        self.raw_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        from .ai_edit_dialog import install_ai_edit_shortcut
        install_ai_edit_shortcut(self.raw_edit, self._open_ai_edit)
        ai_btn = QPushButton("✨ AI 修改 (Ctrl+L)")
        ai_btn.setToolTip("选中若干行改写选中内容;不选则在光标位置插入")
        ai_btn.clicked.connect(lambda: self._open_ai_edit(self.raw_edit))
        self.raw_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        bar = QHBoxLayout()
        self.words_spin = QSpinBox()
        self.words_spin.setRange(0, 200000)
        self.words_spin.setSpecialValueText("∞")
        self.style_edit = QLineEdit()
        self.style_edit.setPlaceholderText(tr("style_label"))
        save_btn = QPushButton(tr("save"))
        save_btn.clicked.connect(self._save_raw)
        self.novel_btn = W.primary_btn(tr("ai_novel"))
        self.novel_btn.clicked.connect(self._ai_novel)
        novel_btn = self.novel_btn
        self.batch_btn = QPushButton(tr("batch_write"))
        self.batch_btn.clicked.connect(self._batch_novel)
        batch_btn = self.batch_btn
        bar.addWidget(QLabel(tr("target_words")))
        bar.addWidget(self.words_spin)
        bar.addWidget(QLabel(tr("style_label")))
        bar.addWidget(self.style_edit, 1)
        bar.addWidget(ai_btn)
        bar.addWidget(novel_btn)
        bar.addWidget(batch_btn)
        bar.addWidget(save_btn)
        lay.addLayout(bar)
        # 小说线第二行:策划 / 审校 / 按指令改稿 / 封面
        bar2 = QHBoxLayout()
        plan_btn = QPushButton("§ 策划与设定")
        plan_btn.clicked.connect(self._open_plan)
        review_btn = QPushButton("◇ AI 六维审校")
        review_btn.clicked.connect(self._review_chapter)
        self.edit_instr = QLineEdit()
        self.edit_instr.setPlaceholderText("按指令改稿:如「把开头改得更抓人」「加强母亲戏份」")
        edit_btn = QPushButton("✏ 改稿")
        edit_btn.clicked.connect(self._edit_chapter)
        bar2.addWidget(plan_btn)
        self.review_btn = review_btn
        review_btn.setToolTip("六维审校(连贯性/人设/设定/物件/文风/节奏)·点击查看问题明细")
        self.summary_btn = QPushButton("≡ 全书审校清单")
        self.summary_btn.clicked.connect(self._open_review_summary)
        read_btn = QPushButton("🔊 朗读本章")
        read_btn.clicked.connect(self._read_aloud)
        bar2.addWidget(review_btn)
        bar2.addWidget(self.summary_btn)
        bar2.addWidget(read_btn)
        bar2.addWidget(self.edit_instr, 1)
        bar2.addWidget(edit_btn)
        lay.addLayout(bar2)
        lay.addWidget(self.raw_edit, 1)

    def _reload_raw(self):
        ep = self._ep
        self.raw_edit.setPlainText(ep["content"] or "")
        self.words_spin.setValue(ep["target_words"] or 0)
        self.style_edit.setText(db.get_setting("novel_style", "爽感快节奏网文:短句为主,情绪外露,段落简短,冲突直给,爽点前置"))
        if hasattr(self, "novel_btn"):
            self._update_novel_gate()


    def _open_ai_edit(self, editor):
        """Ctrl+L:选中→改写选中;未选中→光标处插入;可勾选整章处理。"""
        from .ai_edit_dialog import AiEditDialog
        text = editor.toPlainText()
        if not text.strip():
            return
        sel = editor.textCursor()
        start, end = sel.selectionStart(), sel.selectionEnd()
        mode = "selection" if end > start else "insert"
        col = "content" if editor is self.raw_edit else "script_content"
        def apply(new_text: str, s: int, e: int):
            editor.setPlainText(new_text)
            if col == "content":
                db.ex("UPDATE episodes SET content=?, updated_at=? WHERE id=?",
                      (new_text, db.now(), self.episode_id))
                self._ep = db.q1("SELECT * FROM episodes WHERE id=?", (self.episode_id,))
            else:
                self._save_script()
        AiEditDialog(self, editor, mode, start, end, apply, episode_id=self.episode_id).exec()

    def _save_raw(self):
        db.ex("UPDATE episodes SET content=?, target_words=?, updated_at=? WHERE id=?",
              (self.raw_edit.toPlainText(), self.words_spin.value(), db.now(), self.episode_id))
        self._ep = db.q1("SELECT * FROM episodes WHERE id=?", (self.episode_id,))
        QMessageBox.information(self, tr("save"), "OK")

    def _novel_redline_hint(self) -> str:
        """写作红线提示:缺哪几步(对齐原版 batchMissingSteps);齐全返回空串。"""
        try:
            from ..pipeline import novel as novel_pipe
            if self._drama.get("work_type") != "novel":
                return ""
            missing = novel_pipe.missing_steps_text(self.drama_id)
            return f"请先完成步骤 {missing} 的设定" if missing else ""
        except Exception:  # noqa: BLE001
            return ""

    def _update_novel_gate(self):
        """设定未齐时禁用「AI 生成小说/批量写」并在工具条提示(对齐原版前端守卫)。"""
        hint = self._novel_redline_hint()
        if hasattr(self, "novel_btn"):
            self.novel_btn.setEnabled(not hint)
            self.novel_btn.setToolTip(hint or "AI 生成本章")
        if hasattr(self, "batch_btn"):
            self.batch_btn.setEnabled(not hint)
            self.batch_btn.setToolTip(hint or "批量写本章及后续")

    def _ai_novel(self):
        from ..pipeline import novel as novel_pipe
        hint = self._novel_redline_hint()
        if hint:
            warn(hint)
            return
        def job(tid):
            if not db.q1("SELECT novel_outline FROM dramas WHERE id=?", (self.drama_id,))["novel_outline"]:
                idea = self.raw_edit.toPlainText().strip()[:6000] or self._drama["title"]
                novel_pipe.plan_novel(self.drama_id, idea, config_id=self.text_model.currentData())
            return novel_pipe.write_chapter_with_review(self.episode_id, config_id=self.text_model.currentData())
        def done(tid, result, error):
            if error:
                err("AI")
            else:
                self._reload_raw()
                r = (result or {})
                msg = "本章已生成" + (";审校发现问题并已自动修复一轮 ✅" if r.get("fixed") else "")
                QMessageBox.information(self, tr("ai_novel"), msg)
        self._save_raw_silent()
        TASKMGR.submit("novel", job, done, episode_id=self.episode_id, drama_id=self.drama_id)

    def _batch_novel(self):
        """批量写本章及后续(对齐原版未提交批次的语义重定义 + 进度条 + 阶段)。"""
        from ..core.preflight import ensure_ready
        if not ensure_ready("text", self._cfg_for("text")):
            return
        self._save_raw_silent()
        all_eps = [dict(r) for r in db.q(
            "SELECT * FROM episodes WHERE drama_id=? AND episode_number>=? ORDER BY episode_number",
            (self.drama_id, self._ep["episode_number"]))]
        cur = self._ep
        # 情形一:本章未写完(空 或 低于目标 80%)→ 确认后只重写本章
        body_len = len((cur["content"] or "").strip())
        target = cur["target_words"] or 3000
        if body_len < int(target * 0.8):
            if QMessageBox.question(
                    self, tr("batch_write"),
                    f"第 {cur['episode_number']} 章"
                    + (f"现有 {body_len} 字,未达目标 {target} 字" if body_len else f"尚未写作(目标 {target} 字)")
                    + ",将重新生成。已有内容会被覆盖且无法撤销。确定继续?",
                    QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                self._run_batch([cur["id"]], force=True)
            return
        # 情形二:本章已完成 → 取后续中「无正文」的前 10 章
        pending = [e for e in all_eps if e["episode_number"] > cur["episode_number"]
                   and len((e["content"] or "").strip()) < 200]
        if not pending:
            warn("后续章节都已有正文,没有待写内容")
            return
        self._run_batch([e["id"] for e in pending[:10]], force=False)

    def _run_batch(self, episode_ids: list[int], force: bool):
        """执行批量写章:三段式进度条 + 阶段显示 + 完成后提示。"""
        from ..pipeline import novel as novel_pipe
        self._batch_ids = list(episode_ids)
        self._batch_done = 0
        self._batch_ok = 0
        self._batch_failed = 0
        self._batch_stage = ""
        self._batch_dialog = _BatchProgressDialog(self, len(episode_ids), self)
        self._batch_dialog.show()
        self._batch_start_ts = 0
        def job(tid):
            from ..core import taskmgr as TM
            self._batch_start_ts = 1
            def on_progress(done, total, num):
                self._batch_done = done
                from PySide6.QtCore import QMetaObject, Qt as _Qt
                def _ui():
                    if self._batch_dialog:
                        self._batch_dialog.update_progress(done, total)
                QMetaObject.invokeMethod(self, "_noop", _Qt.QueuedConnection)
            return novel_pipe.batch_write_chapters(
                self.drama_id, episode_ids, force=force,
                config_id=self.text_model.currentData(),
                lang=getattr(self, "_drama_lang", None),
                on_progress=on_progress)
        def done(tid, result, error):
            r = result or {}
            if error:
                r.setdefault("failed", len(episode_ids))
            self._batch_ok = r.get("ok", 0)
            self._batch_failed = r.get("failed", 0)
            if self._batch_dialog:
                self._batch_dialog.finish(self._batch_ok, self._batch_failed)
            if r.get("ok"):
                ok(f"批量完成:{r['ok']} 章成功"
                   + (f",{r['failed']} 章失败" if r.get("failed") else ""))
            self._reload_raw()
        TASKMGR.submit("novel_batch", job, done, drama_id=self.drama_id, episode_id=self.episode_id)

    def _rewrite_done_chapters(self):
        """重写已完成章节(force=True 显式放行覆盖)。"""
        eps = [dict(r) for r in db.q(
            "SELECT * FROM episodes WHERE drama_id=? ORDER BY episode_number", (self.drama_id,))
            if len((r["content"] or "").strip()) >= 200]
        if not eps:
            return
        if QMessageBox.question(
                self, tr("batch_write"),
                f"将重新生成这 {len(eps)} 章,已有正文会被覆盖且无法撤销。确定继续?",
                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        self._run_batch([e["id"] for e in eps], force=True)

    def _chapter_running_stage(self, ep_id: int) -> str:
        """该集当前生成阶段(来自 sys_task.params.stage)。"""
        from ..core import taskmgr as TM
        row = db.q1("""SELECT id FROM sys_task WHERE episode_id=? AND status='processing'
                      ORDER BY id DESC LIMIT 1""", (ep_id,))
        return TM.get_stage(row["id"]) if row else ""

    def _review_issues(self) -> list:
        rj = db.jload(self._ep["review_json"], {}) or {}
        issues = rj.get("issues") or []
        for dim, v in (rj.get("dimensions") or {}).items():
            if isinstance(v, dict) and not v.get("pass", True):
                for s in (v.get("issues") or []):
                    issues.append(f"[{dim}] {s}")
        return issues

    def _show_review_detail(self):
        from .batch_dialogs import ReviewPanelDialog
        issues = self._review_issues()
        if not issues:
            info("本章没有未处理的审校问题")
            return
        ReviewPanelDialog(self, issues, self._ep["episode_number"], self._ep["title"] or "").exec()

    def _open_review_summary(self):
        from ..pipeline import novel as N
        from .batch_dialogs import ReviewSummaryDialog
        data = N.review_summary(self.drama_id)
        ReviewSummaryDialog(self, data, on_goto=self._goto_episode_by_id).exec()

    def _goto_episode_by_id(self, episode_id: int):
        ep = db.q1("SELECT drama_id, episode_number FROM episodes WHERE id=?", (episode_id,))
        if ep and ep["drama_id"] == self.drama_id:
            self.load(self.drama_id, episode_id)
            self._goto_step("raw")

    def _read_aloud(self):
        from ..core.preflight import ensure_ready
        if not ensure_ready("tts", None):
            return
        from ..pipeline import novel as N
        def job(tid):
            return N.read_aloud(self.episode_id)
        def done(tid, result, error):
            if error:
                err(error); return
            import os
            from ..core import config
            p = config.media_url_to_path(result["audio_url"])
            if p.exists():
                os.startfile(str(p))
            ok(f"已合成朗读音频({result['chunks']} 段)")
        TASKMGR.submit("tts", job, done, episode_id=self.episode_id)

    def _open_plan(self):
        from .novel_dialogs import NovelPlanDialog
        self._save_raw_silent()
        NovelPlanDialog(self, self.drama_id).exec()

    def _review_chapter(self):
        self._save_raw_silent()
        from .novel_dialogs import ReviewDialog
        from ..pipeline import novel as novel_pipe
        def job(tid):
            return novel_pipe.review_chapter(self.episode_id, config_id=self.text_model.currentData())
        def done(tid, result, error):
            if error:
                err("AI")
            else:
                ReviewDialog(self, result or {}, self._ep["episode_number"]).exec()
        TASKMGR.submit("review", job, done, episode_id=self.episode_id)

    def _edit_chapter(self):
        instr = self.edit_instr.text().strip()
        if not instr:
            self.edit_instr.setFocus()
            return
        self._save_raw_silent()
        from ..pipeline import novel as novel_pipe
        def job(tid):
            return novel_pipe.edit_chapter(self.episode_id, instr, config_id=self.text_model.currentData())
        def done(tid, result, error):
            if error:
                err("AI")
            else:
                self._reload_raw()
                self.edit_instr.clear()
        TASKMGR.submit("novel_edit", job, done, episode_id=self.episode_id)

    def _save_raw_silent(self):
        db.ex("UPDATE episodes SET content=?, target_words=?, updated_at=? WHERE id=?",
              (self.raw_edit.toPlainText(), self.words_spin.value(), db.now(), self.episode_id))
        db.set_setting("novel_style", self.style_edit.text().strip())
        self._ep = db.q1("SELECT * FROM episodes WHERE id=?", (self.episode_id,))

    # ── 阶段② AI 改写 ──
    def _panel_rewrite(self, lay):
        self.script_edit = QPlainTextEdit()
        self.script_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        from .ai_edit_dialog import install_ai_edit_shortcut
        install_ai_edit_shortcut(self.script_edit, self._open_ai_edit)
        ai_btn2 = QPushButton("✨ AI 修改 (Ctrl+L)")
        ai_btn2.setToolTip("选中若干行改写选中内容;不选则在光标位置插入")
        ai_btn2.clicked.connect(lambda: self._open_ai_edit(self.script_edit))
        bar = QHBoxLayout()
        rewrite_btn = W.primary_btn(tr("rewrite"))
        rewrite_btn.clicked.connect(self._rewrite)
        bar.addWidget(ai_btn2)
        save_btn = QPushButton(tr("save"))
        save_btn.clicked.connect(self._save_script)
        bar.addWidget(rewrite_btn)
        bar.addWidget(save_btn)
        bar.addStretch(1)
        lay.addLayout(bar)
        lay.addWidget(self.script_edit, 1)

    def _reload_rewrite(self):
        self.script_edit.setPlainText(self._ep["script_content"] or "")

    def _rewrite(self):
        self._save_raw_silent()
        def job(tid):
            return rewriter.rewrite_script(self.episode_id, self.style_edit.text().strip(),
                                           config_id=self.text_model.currentData(), lang=self._drama_lang)
        def done(tid, result, error):
            if error:
                err("AI")
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
        self.asset_empty = QLabel("—" + tr("extract") + "—")
        self.asset_empty.setObjectName("muted")
        self.asset_empty.setAlignment(Qt.AlignCenter)
        self.asset_list = QVBoxLayout()
        # 漫画资产 tab(真实页:角色/场景/道具 漫画风格镜像图)
        self.asset_tabs = QTabWidget()
        normal_tab = QWidget()
        n_lay = QVBoxLayout(normal_tab)
        n_lay.setContentsMargins(0, 6, 0, 6)
        n_lay.addWidget(self.asset_stat)
        n_lay.addWidget(self.asset_empty)
        n_lay.addLayout(self.asset_list)
        n_lay.addStretch(1)
        n_scroll = QScrollArea()
        n_scroll.setWidgetResizable(True)
        n_scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        n_holder = QWidget()
        n_holder.setLayout(n_lay)
        n_scroll.setWidget(n_holder)
        self.asset_tabs.addTab(n_scroll, tr("normal_assets"))
        comic_tab = QWidget()
        c_lay = QVBoxLayout(comic_tab)
        c_bar = QHBoxLayout()
        c_bar.addWidget(W.muted("漫画风格镜像资产(与常规资产行独立,用于条漫出图)"))
        c_bar.addStretch(1)
        c_batch = W.primary_btn("◑ " + tr("batch_image"))
        c_batch.clicked.connect(self._batch_comic_assets)
        c_bar.addWidget(c_batch)
        c_lay.addLayout(c_bar)
        self.comic_asset_list = QVBoxLayout()
        c_lay.addLayout(self.comic_asset_list)
        c_lay.addStretch(1)
        c_scroll = QScrollArea()
        c_scroll.setWidgetResizable(True)
        c_scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        c_holder = QWidget()
        c_holder.setLayout(c_lay)
        c_scroll.setWidget(c_holder)
        self.asset_tabs.addTab(c_scroll, tr("comic_assets"))
        lay.addWidget(self.asset_tabs, 1)

    def _gen_comic_asset(self, kind: str, row_id: int):
        from ..pipeline import comic as comic_pipe
        def job(tid):
            return comic_pipe.comic_asset_image(self.drama_id, kind, row_id,
                                                config_id=self.image_model.currentData())
        def done(tid, result, error):
            if error:
                err("AI")
            self._reload_comic_assets()
        TASKMGR.submit("image", job, done, drama_id=self.drama_id)

    def _batch_comic_assets(self):
        for kind, table in (("character", "characters"), ("scene", "scenes"), ("prop", "props")):
            for r in db.q(f"SELECT id FROM {table} WHERE drama_id=? AND comic_image_url IS NULL", (self.drama_id,)):
                self._gen_comic_asset(kind, r["id"])

    def _reload_comic_assets(self):
        if not getattr(self, "comic_asset_list", None):
            return
        while self.comic_asset_list.count():
            item = self.comic_asset_list.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for kind, table, label in (("character", "characters", tr("chars")),
                                   ("scene", "scenes", tr("scenes")),
                                   ("prop", "props", tr("props"))):
            for r in db.q(f"SELECT * FROM {table} WHERE drama_id=? ORDER BY id", (self.drama_id,)):
                box = W.make_card()
                lay = QHBoxLayout(box)
                lay.setContentsMargins(10, 6, 10, 6)
                img = QLabel()
                img.setPixmap(W.pixmap_from_media(r["comic_image_url"], 72))
                img.setFixedWidth(80)
                lay.addWidget(img)
                name = W.h2(r["name"])
                lay.addWidget(name)
                lay.addWidget(W.tag(label))
                if r["comic_image_url"]:
                    lay.addWidget(W.tag(tr("generated")))
                lay.addStretch(1)
                btn = QPushButton(tr("redraw"))
                btn.clicked.connect(lambda _=False, k=kind, i=r["id"]: self._gen_comic_asset(k, i))
                lay.addWidget(btn)
                self.comic_asset_list.addWidget(box)

    def _extract(self, scope: str):
        def job(tid):
            return extract_pipe.extract_assets(self.episode_id, config_id=self.text_model.currentData(), lang=self._drama_lang)
        def done(tid, result, error):
            if error:
                err("AI")
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
            var = QPushButton("◑ 变体")
            var.setToolTip("造型变体(多套服装造型)")
            var.clicked.connect(lambda _=False, r=row: self._open_variants(r["id"]))
            btns.addWidget(var)
        for b in (gen_prompt, redraw, upload):
            btns.addWidget(b)
        lay.addLayout(btns)
        return box

    def _open_variants(self, character_id: int):
        from .variants_dialog import VariantsDialog
        c = db.q1("SELECT * FROM characters WHERE id=?", (character_id,))
        if c:
            VariantsDialog(self, dict(c)).exec()
            self._reload_assets()

    def _gen_prompt(self, row_id: int, kind: str):
        fn = {"character": prompts_gen.character_prompt, "scene": prompts_gen.scene_prompt,
              "prop": prompts_gen.prop_prompt}[kind]
        def job(tid):
            return fn(row_id, config_id=self.text_model.currentData())
        def done(tid, result, error):
            if error:
                err("AI")
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
        def done(tid, result, error):
            if error:
                err("AI")
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
        """资产·角色卡换脸:打开对话框(当前形象 → 选源脸 → 预览 → 应用替换)。"""
        c = db.q1("SELECT * FROM characters WHERE id=?", (character_id,))
        if not c:
            return
        if not c["image_url"]:
            QMessageBox.information(self, tr("face_swap"), "该角色还没有形象图,请先「重绘」生成或「上传」")
            return
        from .character_face_swap_dialog import CharacterFaceSwapDialog
        dlg = CharacterFaceSwapDialog(self, dict(c), self.face_model.currentData(),
                                      self.face_model.currentText())
        if dlg.exec() == CharacterFaceSwapDialog.Accepted:
            self._reload_assets()

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
        self.repair_btn = W.primary_btn("⟳ 自动补全 0")
        self.repair_btn.setToolTip("修复拆分中断留下的残缺分镜:补出图提示词 + 绑定角色/场景/道具参考素材")
        self.repair_btn.setVisible(False)
        self.repair_btn.clicked.connect(self._repair_storyboards)
        bar.addWidget(self.repair_btn)
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
        self._load_incomplete()
        self._refresh_status()

    def _sb_row(self, r: dict) -> QWidget:
        box = W.make_card()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(12, 8, 12, 8)
        head = QHBoxLayout()
        num = QLabel(f"#{r['storyboard_number']:02d}")
        num.setObjectName("h2")
        head.addWidget(num)
        status = (tr("done") if (r["video_url"] or r["composed_video_url"]) else
                  (tr("in_progress") if r.get("status") == "processing" else tr("pending")))
        head.addWidget(W.tag(status))
        head.addWidget(W.tag(f"{int(r['duration'] or 0)}s"))
        if r["first_frame_image"]:
            head.addWidget(W.tag("首帧✓"))
        head.addStretch(1)
        ff_btn = QPushButton("▣ 首帧")
        ff_btn.setToolTip("生成本镜头首帧图")
        ff_btn.clicked.connect(lambda _=False, i=r["id"]: self._gen_first_frame(i))
        i2v_btn = QPushButton("▷ 图生")
        i2v_btn.setToolTip("用首帧图生成视频(图生视频,注入 @角色 参考图)")
        i2v_btn.clicked.connect(lambda _=False, i=r["id"]: self._compose_i2v(i))
        sub_btn = QPushButton("T 字幕")
        sub_btn.setToolTip("把旁白/台词烧录为字幕版本")
        sub_btn.clicked.connect(lambda _=False, i=r["id"]: self._burn_sub(i))
        tts_btn = QPushButton("♪")
        tts_btn.setToolTip(tr("narration"))
        tts_btn.clicked.connect(lambda _=False, i=r["id"]: self._one_tts(i))
        redo = QPushButton(tr("redraw"))
        redo.clicked.connect(lambda _=False, i=r["id"]: self._one_video(i))
        play = QPushButton("▶")
        play.setToolTip("播放")
        play.setEnabled(bool(r["video_url"] or r["composed_video_url"]))
        play.clicked.connect(lambda _=False, u=r["video_url"] or r["composed_video_url"]: self._play_video(u))
        dl_btn = QPushButton("↓")
        dl_btn.setToolTip("下载该镜头视频")
        dl_btn.setEnabled(bool(r["video_url"] or r["composed_video_url"]))
        dl_btn.clicked.connect(lambda _=False, rr=r: self._download_sb(rr))
        for b in (ff_btn, i2v_btn, sub_btn, tts_btn, redo, play, dl_btn):
            head.addWidget(b)
        lay.addLayout(head)
        content = QLabel(r["content"] or "")
        content.setWordWrap(True)
        lay.addWidget(content)
        vp = QLineEdit(r["video_prompt"] or "")
        vp.setPlaceholderText("视频提示词(可逐镜微调,@角色 自动注入参考图)")
        vp.editingFinished.connect(lambda li=r["id"], t=vp: db.ex(
            "UPDATE storyboards SET video_prompt=? WHERE id=?", (t.text(), li)))
        lay.addWidget(vp)
        narr = QLineEdit(r["narration"] or "")
        narr.setPlaceholderText(tr("narration_hint"))
        narr.editingFinished.connect(lambda li=r["id"], t=narr: db.ex(
            "UPDATE storyboards SET narration=? WHERE id=?", (t.text(), li)))
        lay.addWidget(narr)
        return box

    def _download_sb(self, sb: dict):
        from ..core import download as dl_mod
        try:
            p = dl_mod.download_storyboard_video(sb)
            ok(f"已下载:{p.name}")
        except Exception as e:  # noqa: BLE001
            err(str(e))

    def _gen_first_frame(self, sb_id: int):
        from ..pipeline import shot_tools
        def job(tid):
            return shot_tools.generate_first_frame(self.episode_id, sb_id,
                                                   config_id=self.image_model.currentData())
        def done(tid, result, error):
            if error:
                err("▣")
            self._reload_storyboard()
        TASKMGR.submit("image", job, done, episode_id=self.episode_id, storyboard_id=sb_id)

    def _compose_i2v(self, sb_id: int):
        from ..pipeline import shot_tools
        db.ex("UPDATE storyboards SET status='processing' WHERE id=?", (sb_id,))
        res = self.res_combo.currentText()
        def job(tid):
            return shot_tools.compose_from_image(self.episode_id, sb_id, res,
                                                 config_id=self.video_model.currentData())
        def done(tid, result, error):
            if error:
                db.ex("UPDATE storyboards SET status='failed' WHERE id=?", (sb_id,))
                err("▷")
            self._reload_storyboard()
        TASKMGR.submit("video", job, done, episode_id=self.episode_id, storyboard_id=sb_id)

    def _burn_sub(self, sb_id: int):
        from ..pipeline import shot_tools
        def job(tid):
            return shot_tools.burn_subtitle(sb_id)
        def done(tid, result, error):
            if error:
                err("T")
            self._reload_storyboard()
        TASKMGR.submit("video", job, done, episode_id=self.episode_id, storyboard_id=sb_id)

    def _load_incomplete(self):
        """检测残缺分镜;有才显示补全按钮(无残缺自动消失不占位)。"""
        if not getattr(self, "repair_btn", None) or not self.episode_id:
            return
        try:
            from ..pipeline import storyboard_repair as R
            self._incomplete = R.list_incomplete(self.episode_id)
        except Exception:  # noqa: BLE001
            self._incomplete = []
        n = len(self._incomplete or [])
        self.repair_btn.setVisible(n > 0)
        if n:
            self.repair_btn.setText(f"⟳ 自动补全 {n}")

    def _repair_storyboards(self):
        from ..core.taskmgr import TASKMGR
        ids = [x["id"] for x in (self._incomplete or [])]
        if not ids:
            return
        self.repair_btn.setEnabled(False)
        self.repair_btn.setText("⟳ 补全中 0/0")
        def job(tid):
            from ..pipeline import storyboard_repair as R
            return R.repair_storyboards(self.episode_id, ids,
                                        config_id=self.text_model.currentData(),
                                        lang=getattr(self, "_drama_lang", None))
        def done(tid, result, error):
            self.repair_btn.setEnabled(True)
            if error:
                err(e_)
                return
            r = result or {}
            if r.get("failed"):
                warn(f"补全完成,{r['failed']} 个失败可重试")
            else:
                ok(f"补全完成,共修复 {r.get('completed', 0)} 个分镜")
            self._reload_storyboard()
        TASKMGR.submit("sb_repair", job, done, episode_id=self.episode_id)

    def _split_sb(self):
        """重新拆分分镜(改后台任务 + 轮询,对齐原版 split-async)。"""
        from ..core.preflight import ensure_ready
        if not ensure_ready("text", self._cfg_for("text")):
            return
        if self._sb_split_running:
            return
        try:
            tid = sb_pipe.split_storyboards_bg(
                self.episode_id, self._drama["aspect_ratio"],
                config_id=self.text_model.currentData(),
                lang=getattr(self, "_drama_lang", None))
        except Exception as e:  # noqa: BLE001
            err(str(e)[:200]); return
        self._sb_split_running = True
        self._sb_split_task = tid
        info("分镜拆解已开始(后台运行,约 5-10 分钟)")
        self._poll_sb_split(tid, 0)

    def _poll_sb_split(self, tid: int, attempt: int):
        """每 6 秒轮询拆分任务(对齐原版 6000ms)。"""
        from PySide6.QtCore import QTimer
        if attempt > 200:            # 约 20 分钟兜底
            self._sb_split_running = False
            warn("分镜拆分超时,请到任务面板查看"); return
        def tick():
            row = db.q1("SELECT status, local_path, error_msg FROM sys_task WHERE id=?", (tid,))
            st = row["status"] if row else "failed"
            if st == "processing":
                QTimer.singleShot(6000, lambda: self._poll_sb_split(tid, attempt + 1))
                return
            self._sb_split_running = False
            if st == "completed":
                self._reload_storyboard()
                ok(row["local_path"] or "分镜拆分完成")
            else:
                err(row["error_msg"] or "分镜拆分失败")
        QTimer.singleShot(6000, tick)

    def _batch_vp(self):
        def job(tid):
            return sb_pipe.gen_video_prompts(self.episode_id, config_id=self.text_model.currentData(), lang=self._drama_lang)
        def done(tid, result, error):
            if error:
                err("AI")
            else:
                QMessageBox.information(self, tr("batch_prompts"), f"OK: {result}")
        TASKMGR.submit("prompt", job, done, episode_id=self.episode_id)

    def _one_video(self, sb_id: int):
        self._gen_video_job(sb_id)

    def _batch_video(self):
        rows = db.q("SELECT id FROM storyboards WHERE episode_id=? AND video_url IS NULL AND composed_video_url IS NULL",
                    (self.episode_id,))
        if not rows:
            QMessageBox.information(self, tr("batch_video"), "全部镜头已有视频")
            return
        # 批量生成前确认:镜头数 / 总时长 / 模型 / 分辨率(对齐原版)
        total = db.q1("SELECT COALESCE(SUM(duration),0) s FROM storyboards WHERE episode_id=? AND video_url IS NULL AND composed_video_url IS NULL",
                      (self.episode_id,))["s"]
        model_txt = self.video_model.currentText()
        stats = TASKMGR.ep_video_stats(self.episode_id)
        ret = QMessageBox.question(
            self, tr("batch_video"),
            f"即将生成 {len(rows)} 个镜头(约 {int(total)}s)\n模型:{model_txt}\n分辨率:{self.res_combo.currentText()}\n"
            f"当前任务:{tr('done')} {stats['completed']} · {tr('failed')} {stats['failed']}\n\n确认开始?",
            QMessageBox.Yes | QMessageBox.No)
        if ret != QMessageBox.Yes:
            return
        for r in rows:
            self._gen_video_job(r["id"])

    def _gen_video_job(self, sb_id: int):
        res = self.res_combo.currentText()
        def job(tid):
            from ..pipeline import shot_tools
            sb = db.q1("SELECT * FROM storyboards WHERE id=?", (sb_id,))
            db.ex("UPDATE storyboards SET status='processing' WHERE id=?", (sb_id,))
            prompt = shot_tools.resolve_prompt(dict(sb))
            ref_list = shot_tools.collect_reference_images(self.episode_id, sb_id)
            path, _p = video_client.generate_video(
                prompt[:1500], resolution=res, duration=int(sb["duration"] or 8),
                first_frame=sb["first_frame_image"], reference_images=ref_list,
                config_id=self.video_model.currentData())
            db.ex("UPDATE storyboards SET video_url=?, status='completed', updated_at=? WHERE id=?",
                  (config.path_to_media_url(path), db.now(), sb_id))
            return str(path)
        def done(tid, result, error):
            if error:
                db.ex("UPDATE storyboards SET status='failed' WHERE id=?", (sb_id,))
                err(tr("batch_video"))
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
        def done(tid, result, error):
            if error:
                err("♪")
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
            return comic_pipe.split_panels(self.episode_id, config_id=self.text_model.currentData(), lang=self._drama_lang)
        def done(tid, result, error):
            if error:
                err("AI")
            self._reload_comic()
        TASKMGR.submit("comic", job, done, episode_id=self.episode_id)

    def _one_panel_image(self, panel_id: int):
        def job(tid):
            fp = comic_pipe.panel_image_prompt(panel_id, self.drama_id, config_id=self.text_model.currentData())
            out, _p = image_client.generate_image(fp, config_id=self.image_model.currentData())
            db.ex("UPDATE comic_panels SET image_url=?, updated_at=? WHERE id=?",
                  (config.path_to_media_url(out), db.now(), panel_id))
            return str(out)
        def done(tid, result, error):
            if error:
                err("AI")
            self._reload_comic()
        TASKMGR.submit("image", job, done, episode_id=self.episode_id)

    def _batch_comic(self):
        rows = db.q("SELECT id FROM comic_panels WHERE episode_id=? AND image_url IS NULL", (self.episode_id,))
        for r in rows:
            self._one_panel_image(r["id"])

    def _stitch(self):
        def job(tid):
            return stitch_pipe.stitch_panels(self.episode_id)
        def done(tid, result, error):
            if error:
                err(tr("stitch_long"))
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
            dl.clicked.connect(lambda _=False, mm=m: self._download_merge(mm))
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
        def done(tid, result, error):
            if error:
                err(tr("export_stage"))
            else:
                import os
                os.startfile(str(result))  # noqa
            self._reload_export()
        TASKMGR.submit("merge", job, done, episode_id=self.episode_id)

    def _mark_done(self):
        db.ex("UPDATE episodes SET status='completed', updated_at=? WHERE id=?", (db.now(), self.episode_id))
        QMessageBox.information(self, tr("mark_done"), "OK")

    def _download_merge(self, merge: dict):
        from ..core import download as dl_mod
        try:
            p = dl_mod.download_merge(merge)
            ok(f"已下载:{p.name}")
        except Exception as e:  # noqa: BLE001
            err(str(e))

    def _open_file(self, url: str | None):
        if url:
            import os
            p = config.media_url_to_path(url)
            if p.exists():
                os.startfile(str(p))  # noqa


def QInputDialog_getInt(parent, title, label, value=1, lo=1, hi=99):
    from PySide6.QtWidgets import QInputDialog
    return QInputDialog.getInt(parent, title, label, value, lo, hi)
