# -*- coding: utf-8 -*-
"""小说线 UI:策划与设定面板 / 六维审校结果。"""
from __future__ import annotations

import json

from PySide6.QtWidgets import (QDialog, QFormLayout, QHBoxLayout, QLabel,
                               QPlainTextEdit, QPushButton, QTabWidget,
                               QVBoxLayout, QWidget)

from ..core import config, db
from ..core.i18n import tr
from ..core.taskmgr import TASKMGR
from . import widgets as W


class NovelPlanDialog(QDialog):
    """策划与设定:总纲/世界观/合约/卷战略 可查看编辑保存 + 章节计划 + AI 封面。"""

    def __init__(self, parent, drama_id: int):
        super().__init__(parent)
        self.drama_id = drama_id
        d = db.q1("SELECT * FROM dramas WHERE id=?", (drama_id,))
        self.setWindowTitle("📖 小说策划与设定")
        self.resize(760, 620)
        root = QVBoxLayout(self)
        head = QHBoxLayout()
        head.addWidget(W.h2(f"📖 {d['title']}"))
        head.addStretch(1)
        cover_btn = QPushButton("🎨 AI 生成封面")
        cover_btn.clicked.connect(self._gen_cover)
        head.addWidget(cover_btn)
        root.addLayout(head)

        self.cover_lab = QLabel()
        self.cover_lab.setFixedHeight(120)
        self.cover_lab.setAlignment(Qt.AlignCenter)
        self.cover_lab.setPixmap(W.pixmap_from_media(d["thumbnail"], 220, 116))
        root.addWidget(self.cover_lab)

        self.tabs = QTabWidget()
        self.outline = QPlainTextEdit(d["novel_outline"] or "")
        self.world = QPlainTextEdit(d["novel_world"] or "")
        self.contract = QPlainTextEdit(d["novel_contract"] or "")
        self.volume = QPlainTextEdit(d["novel_volume"] or "")
        for w, name in ((self.outline, "总纲"), (self.world, "世界观"),
                        (self.contract, "故事合约"), (self.volume, "分卷战略")):
            self.tabs.addTab(w, name)
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

    def _save(self):
        from ..pipeline import novel as novel_pipe
        novel_pipe.save_plan(self.drama_id, self.outline.toPlainText(), self.world.toPlainText(),
                             self.contract.toPlainText(), self.volume.toPlainText())
        self.accept()

    def _gen_cover(self):
        from ..pipeline import novel as novel_pipe
        def job(tid):
            return novel_pipe.generate_cover(self.drama_id)
        def done(tid, result, err):
            if err:
                QMessageBox.warning(self, "AI", str(err)[:300])
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
        self.setWindowTitle("🔎 六维审校结果")
        self.resize(640, 520)
        root = QVBoxLayout(self)
        overall = review.get("overall", "")
        head = QHBoxLayout()
        head.addWidget(W.h2(f"🔎 第 {episode_number} 章审校 · " + ("✅ 通过" if overall == "pass" else "⚠️ 需修复")))
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
