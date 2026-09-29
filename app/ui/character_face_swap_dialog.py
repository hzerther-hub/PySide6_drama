# -*- coding: utf-8 -*-
"""资产·角色卡换脸对话框:

角色当前形象 → 选源脸(上传照片 / 从其他角色形象选) → 参数 → 换脸预览
→ 「应用替换形象」写回 characters.image_url(取消则不动)。
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFileDialog,
                               QHBoxLayout, QLabel, QMessageBox,
                               QPushButton, QVBoxLayout)

from ..ai import face_swap
from ..core import config, db
from ..core.i18n import tr
from ..core.taskmgr import TASKMGR
from . import widgets as W


class CharacterFaceSwapDialog(QDialog):
    def __init__(self, parent, character: dict, face_cfg_id: int | None, face_cfg_label: str = ""):
        super().__init__(parent)
        self.character = character
        self.cfg_id = face_cfg_id
        self.source_path: str | None = None
        self.result_path: str | None = None
        self.setWindowTitle(f"{tr('face_swap')} · {character['name']}")
        self.resize(760, 560)
        root = QVBoxLayout(self)
        root.setSpacing(12)

        root.addWidget(W.h2(f"🎭 {tr('face_swap')} · {character['name']}"))
        root.addWidget(W.muted("为角色形象换脸:选择源脸照片(可上传或取自其他角色),换脸预览满意后替换角色形象。"
                              + (f"  换脸模型:{face_cfg_label}" if face_cfg_label else "")))

        cols = QHBoxLayout()
        # 当前形象
        cur_box = QVBoxLayout()
        cur_box.addWidget(QLabel(tr("appearance") + "(当前形象)"))
        self.cur_img = QLabel()
        self.cur_img.setFixedSize(240, 240)
        self.cur_img.setAlignment(Qt.AlignCenter)
        self.cur_img.setStyleSheet("border:1px solid rgba(128,128,128,50);border-radius:8px;")
        self.cur_img.setPixmap(W.pixmap_from_media(character["image_url"], 236, 236))
        cur_box.addWidget(self.cur_img)
        cols.addLayout(cur_box)
        # 源脸
        src_box = QVBoxLayout()
        src_box.addWidget(QLabel("源脸照片"))
        self.src_img = QLabel("未选择")
        self.src_img.setFixedSize(240, 240)
        self.src_img.setAlignment(Qt.AlignCenter)
        self.src_img.setStyleSheet("border:1px dashed rgba(128,128,128,80);border-radius:8px;color:#888;")
        src_box.addWidget(self.src_img)
        btns = QHBoxLayout()
        up = QPushButton("🖼 " + tr("upload"))
        up.clicked.connect(self._pick_source)
        other = QComboBox()
        other.addItem("从其他角色形象选…", None)
        for r in db.q("SELECT id,name,image_url FROM characters WHERE id!=? AND image_url IS NOT NULL",
                      (character["id"],)):
            other.addItem(r["name"], r["image_url"])
        other.currentIndexChanged.connect(self._use_other_character)
        btns.addWidget(up)
        btns.addWidget(other, 1)
        src_box.addLayout(btns)
        cols.addLayout(src_box)
        # 结果
        res_box = QVBoxLayout()
        res_box.addWidget(QLabel("换脸预览"))
        self.res_img = QLabel("—")
        self.res_img.setFixedSize(240, 240)
        self.res_img.setAlignment(Qt.AlignCenter)
        self.res_img.setStyleSheet("border:1px solid rgba(75,110,245,60);border-radius:8px;color:#888;")
        res_box.addWidget(self.res_img)
        cols.addLayout(res_box)
        root.addLayout(cols, 1)

        opt = QHBoxLayout()
        self.all_faces = QCheckBox("替换图中所有脸")
        self.enhance = QCheckBox("人脸增强")
        opt.addWidget(self.all_faces)
        opt.addWidget(self.enhance)
        opt.addStretch(1)
        self.go_btn = W.primary_btn("▶ " + tr("face_swap"))
        self.go_btn.clicked.connect(self._run)
        opt.addWidget(self.go_btn)
        root.addLayout(opt)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        cancel = QPushButton(tr("cancel"))
        cancel.clicked.connect(self.reject)
        self.apply_btn = W.primary_btn("✅ 应用替换形象")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._apply)
        bottom.addWidget(cancel)
        bottom.addWidget(self.apply_btn)
        root.addLayout(bottom)
        self.status = QLabel("")
        self.status.setObjectName("muted")
        root.addWidget(self.status)

    # ── 源脸 ──
    def _pick_source(self):
        p, _ = QFileDialog.getOpenFileName(self, tr("upload"), "", "Images (*.png *.jpg *.jpeg *.webp)")
        if p:
            self.source_path = p
            self.src_img.setPixmap(W.pixmap_from_media(p, 236, 236))
            self.src_img.setStyleSheet("border:1px solid rgba(128,128,128,50);border-radius:8px;")

    def _use_other_character(self, _idx: int):
        sender = self.sender()
        url = sender.currentData()
        if not url:
            return
        p = config.media_url_to_path(url)
        if p.exists():
            self.source_path = str(p)
            self.src_img.setPixmap(W.pixmap_from_media(url, 236, 236))
            self.src_img.setStyleSheet("border:1px solid rgba(128,128,128,50);border-radius:8px;")

    # ── 换脸 ──
    def _run(self):
        if not self.character["image_url"]:
            QMessageBox.information(self, tr("face_swap"), "该角色还没有形象图,请先生成或上传")
            return
        if not self.source_path:
            QMessageBox.information(self, tr("face_swap"), "请先选择源脸照片")
            return
        ok, msg = face_swap.health(config_id=self.cfg_id)
        if not ok:
            QMessageBox.warning(self, tr("face_swap"), msg)
            return
        self.go_btn.setEnabled(False)
        self.status.setText(tr("in_progress") + "…")
        template = str(config.media_url_to_path(self.character["image_url"]))
        src, all_faces, enhance, cfg_id = self.source_path, self.all_faces.isChecked(), self.enhance.isChecked(), self.cfg_id

        def job(tid):
            return str(face_swap.swap_one(template, src, swap_all_faces=all_faces,
                                          face_enhance=enhance, config_id=cfg_id))
        def done(tid, result, err):
            self.go_btn.setEnabled(True)
            if err:
                self.status.setText("❌ " + str(err)[:200])
                return
            self.result_path = result
            self.res_img.setPixmap(W.pixmap_from_media(result, 236, 236))
            self.res_img.setStyleSheet("border:1px solid rgba(128,128,128,50);border-radius:8px;")
            self.apply_btn.setEnabled(True)
            self.status.setText("✅ 完成,可预览后应用")
        TASKMGR.submit("face_swap", job, done)

    def _apply(self):
        if not self.result_path:
            return
        db.ex("UPDATE characters SET image_url=?, updated_at=? WHERE id=?",
              (config.path_to_media_url(self.result_path), db.now(), self.character["id"]))
        self.accept()
