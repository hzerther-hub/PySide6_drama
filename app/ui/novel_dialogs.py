# -*- coding: utf-8 -*-
"""小说线 UI:策划与设定面板 / 六维审校结果。"""
from __future__ import annotations

import json

from PySide6.QtWidgets import (QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPlainTextEdit, QPushButton, QTabWidget,
                               QVBoxLayout, QWidget)

from ..core import config, db
from ..core.i18n import tr
from ..core.taskmgr import TASKMGR
from . import widgets as W
from .braille import WaitingButton
from .toast import err, ok


class NovelPlanDialog(QDialog):
    """策划与设定:总纲/世界观/合约/卷战略 可查看编辑保存 + 章节计划 + AI 封面。"""

    def __init__(self, parent, drama_id: int):
        super().__init__(parent)
        self.drama_id = drama_id
        d = db.q1("SELECT * FROM dramas WHERE id=?", (drama_id,))
        self.setWindowTitle("§ 小说策划与设定")
        self.resize(760, 620)
        root = QVBoxLayout(self)
        head = QHBoxLayout()
        head.addWidget(W.h2(f"§ {d['title']}"))
        head.addStretch(1)
        cover_btn = QPushButton("◑ AI 生成封面")
        cover_btn.clicked.connect(self._gen_cover)
        head.addWidget(cover_btn)
        root.addLayout(head)

        meta0 = db.jload(d["metadata"], {}) or {}
        meta_row = QHBoxLayout()
        self.intro_edit = QLineEdit(meta0.get("intro", ""))
        self.intro_edit.setPlaceholderText("项目简介(AI 起草会读取)")
        self.genre_edit = QLineEdit(meta0.get("genre", ""))
        self.genre_edit.setPlaceholderText("题材")
        meta_row.addWidget(QLabel("简介"))
        meta_row.addWidget(self.intro_edit, 2)
        meta_row.addWidget(QLabel("题材"))
        meta_row.addWidget(self.genre_edit, 1)
        root.addLayout(meta_row)

        self.cover_lab = QLabel()
        self.cover_lab.setFixedHeight(120)
        self.cover_lab.setAlignment(Qt.AlignCenter)
        self.cover_lab.setPixmap(W.pixmap_from_media(d["thumbnail"], 220, 116))
        root.addWidget(self.cover_lab)

        # 每个设定板块:AI 起草 + 保存(对齐原版 draftNovelSection/saveWizardSection)
        self.edits: dict[str, QPlainTextEdit] = {}
        self.tabs = QTabWidget()
        self._draft_btns: dict[str, WaitingButton] = {}
        for key, name in (("outline", "总纲"), ("world", "世界观"),
                          ("contract", "故事合约"), ("volume", "分卷战略")):
            page = QWidget()
            lay = QVBoxLayout(page)
            lay.setContentsMargins(0, 8, 0, 0)
            row = QHBoxLayout()
            edit = QPlainTextEdit(d[f"novel_{key}"] or "")
            edit.setMinimumHeight(260)
            self.edits[key] = edit
            btn = WaitingButton("✨ AI 起草")
            btn.clicked.connect(lambda _=False, k=key, n=name: self._draft_section(k, n))
            self._draft_btns[key] = btn
            save_btn = QPushButton("保存")
            save_btn.clicked.connect(lambda _=False, k=key: self._save_section(k))
            row.addWidget(btn)
            row.addWidget(save_btn)
            row.addStretch(1)
            row.addWidget(W.muted("AI 起草会覆盖当前内容,先保存项目设定(题材/简介)以便 Agent 读取"))
            lay.addLayout(row)
            lay.addWidget(edit, 1)
            self.tabs.addTab(page, name)
        ch = QPlainTextEdit()
        ch.setReadOnly(True)
        chapters = db.jload(d["novel_chapters"], [])
        lines = [f"第{c.get('number','?')}章 {c.get('title','')} — 目标:{c.get('goal','')} | 事件:{c.get('events','')} | 钩子:{c.get('cliffhanger','')}"
                 for c in chapters]
        ch.setPlainText("\n".join(lines) or "(尚未生成章节计划,可通过「批量写本章及后续」前先运行策划)")
        self.tabs.addTab(ch, "章节计划")
        meta = db.jload(d["novel_meta"], {})
        mc = QPlainTextEdit(json.dumps(meta.get("main_characters", []), ensure_ascii=False, indent=1))
        mc.setReadOnly(True)
        self.tabs.addTab(mc, "主要角色")
        root.addWidget(self.tabs, 1)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        save = W.primary_btn(tr("save"))
        save.clicked.connect(self._save)
        close = QPushButton(tr("close"))
        close.clicked.connect(self.accept)
        bottom.addWidget(close)
        bottom.addWidget(save)
        root.addLayout(bottom)


    # ── AI 起草(对齐原版 draftNovelSection)──
    SECTION_CN = {"outline": "总纲", "world": "世界观", "contract": "故事合约", "volume": "分卷战略"}
    SECTION_MAP = {"outline": ("novel_outline", "outline"),
                   "world": ("novel_world", "world"),
                   "contract": ("novel_contract", "contract"),
                   "volume": ("novel_volume", "volume")}

    def _draft_section(self, key: str, name: str):
        """调用 novel_planner Agent 起草该板块(已落库项目设定供其读取)。"""
        from ..core.preflight import ensure_ready
        if not ensure_ready("text", None):
            return
        self._save_project_meta()          # 先落库,Agent 通过 read_novel_context 读题材/简介
        d = db.q1("SELECT * FROM dramas WHERE id=?", (self.drama_id,))
        chapters = db.jload(d["novel_chapters"], []) or []
        intended = len(chapters) or int(d["total_episodes"] or 0)
        ch_part = f",计划共 {intended} 章" if intended else ""
        field, section = self.SECTION_MAP[key]
        hint = ""
        if key == "world":
            hint = "。保存时必须同时传 structured:era/location/power_system/factions[{name,desc}]/note"
        elif key == "contract":
            hint = "。保存时必须同时传 structured:pov/tones[]/rules[]/word_range:[min,max]/note"
        btn = self._draft_btns[key]
        btn.busy("起草中")
        msg = f"请起草本书的{name}(section={section}{ch_part}),完成后调用 save_novel_settings 保存{hint}。"

        def job(tid):
            from ..agents import runner
            return runner.run_agent("novel_planner", msg)

        def done(tid, result, error):
            btn.idle()
            if error:
                err(error)
                return
            self._reload_tabs()
            ok(f"{name}已生成")

        TASKMGR.submit("prompt", job, done, drama_id=self.drama_id)

    def _save_section(self, key: str):
        field, _ = self.SECTION_MAP[key]
        db.ex(f"UPDATE dramas SET {field}=?, updated_at=? WHERE id=?",
              (self.edits[key].toPlainText(), db.now(), self.drama_id))
        ok(f"{self.SECTION_CN[key]}已保存")

    def _save_project_meta(self):
        """保存简介/题材(供 Agent read_novel_context 读取)。"""
        d = db.q1("SELECT metadata FROM dramas WHERE id=?", (self.drama_id,))
        meta = db.jload(d["metadata"], {}) if d else {}
        if self.intro_edit is not None:
            meta["intro"] = self.intro_edit.text().strip()
        if self.genre_edit is not None:
            meta["genre"] = self.genre_edit.text().strip()
        db.ex("UPDATE dramas SET metadata=?, updated_at=? WHERE id=?",
              (json.dumps(meta, ensure_ascii=False), db.now(), self.drama_id))

    def _reload_tabs(self):
        """AI 起草后从库重载各板块。"""
        d = db.q1("SELECT * FROM dramas WHERE id=?", (self.drama_id,))
        for key, (field, _) in self.SECTION_MAP.items():
            self.edits[key].setPlainText(d[field] or "")

    def _save(self):
        from ..pipeline import novel as novel_pipe
        self._save_project_meta()
        novel_pipe.save_plan(self.drama_id,
                             self.edits["outline"].toPlainText(), self.edits["world"].toPlainText(),
                             self.edits["contract"].toPlainText(), self.edits["volume"].toPlainText())
        self.accept()

    def _gen_cover(self):
        from ..pipeline import novel as novel_pipe
        def job(tid):
            return novel_pipe.generate_cover(self.drama_id)
        def done(tid, result, error):
            if error:
                err("AI")
            else:
                self.cover_lab.setPixmap(W.pixmap_from_media(result, 220, 116))
        TASKMGR.submit("image", job, done, drama_id=self.drama_id)


from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QMessageBox  # noqa: E402


class ReviewDialog(QDialog):
    """六维审校结果:连贯性/人设/设定/物件状态/文风/节奏,pass/fail + 问题清单。"""

    DIM_CN = {"coherence": "连贯性", "character": "人设", "setting": "设定",
              "props": "物件状态", "style": "文风", "pacing": "节奏"}

    def __init__(self, parent, review: dict, episode_number: int = 0):
        super().__init__(parent)
        self.setWindowTitle("◇ 六维审校结果")
        self.resize(640, 520)
        root = QVBoxLayout(self)
        overall = review.get("overall", "")
        head = QHBoxLayout()
        head.addWidget(W.h2(f"◇ 第 {episode_number} 章审校 · " + ("✅ 通过" if overall == "pass" else "⚠️ 需修复")))
        head.addStretch(1)
        root.addLayout(head)
        if review.get("summary"):
            root.addWidget(W.muted(str(review["summary"])))
        dims = review.get("dimensions") or {}
        for key in ("coherence", "character", "setting", "props", "style", "pacing"):
            v = dims.get(key) or {}
            ok = bool(v.get("pass", True))
            issues = v.get("issues") or []
            text = f"{'✅' if ok else '❌'} {self.DIM_CN.get(key, key)}"
            if issues:
                text += "：" + "；".join(str(i) for i in issues[:4])
            lab = QLabel(text)
            lab.setWordWrap(True)
            root.addWidget(lab)
        root.addSpacing(8)
        close = W.primary_btn(tr("close"))
        close.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(close)
        root.addLayout(row)

# 写作红线:NOVEL_REQUIRED_STEPS 全部完成才能生成小说(对齐原版 5933)
NOVEL_REQUIRED_STEPS = [1, 2, 3, 4, 5, 7]
STEP_NAMES = {1: "项目设定", 2: "总纲", 3: "世界观", 4: "故事合约",
              5: "角色设定", 6: "卷战略", 7: "章节计划"}


def wizard_step_done(drama_id: int, step: int) -> bool:
    """步骤完成判定(对齐原版 wizardStepDone)。

    ★ 步骤 3/4 读**已落库的** novel_meta,而非向导内存草稿 —— 刷新页面后未开向导也能正确判定。
    """
    d = db.q1("SELECT * FROM dramas WHERE id=?", (drama_id,))
    if not d:
        return False
    meta = db.jload(d["novel_meta"], {}) or {}
    if step == 1:                        # 项目设定 = 标题 + 简介
        m = db.jload(d["metadata"], {}) or {}
        return bool((d["title"] or "").strip() and (m.get("intro") or "").strip())
    if step == 2:
        return bool((d["novel_outline"] or "").strip())
    if step == 3:                        # 世界观 = era + location
        w = meta.get("world") or {}
        return bool(str(w.get("era") or "").strip() and str(w.get("location") or "").strip())
    if step == 4:                        # 故事合约 = pov + rules + tones
        c = meta.get("contract") or {}
        rules = c.get("rules") or []
        tones = c.get("tones") or []
        rules_ok = any(str(r or "").strip() for r in rules)
        return bool(c.get("pov") and rules_ok and len(tones) > 0)
    if step == 5:                        # 角色设定
        return bool(db.q1("SELECT id FROM characters WHERE drama_id=? LIMIT 1", (drama_id,)))
    if step == 6:
        return bool((d["novel_volume"] or "").strip())
    if step == 7:                        # 章节计划
        return len(db.jload(d["novel_chapters"], []) or []) > 0
    return False


def missing_steps(drama_id: int) -> list[int]:
    return [s for s in NOVEL_REQUIRED_STEPS if not wizard_step_done(drama_id, s)]


def gate_message(drama_id: int) -> str:
    """闸门提示:缺哪几步(对齐原版 batchMissingSteps)。"""
    miss = missing_steps(drama_id)
    if not miss:
        return ""
    return "、".join(f"{s}({STEP_NAMES.get(s,'')})" for s in miss)
