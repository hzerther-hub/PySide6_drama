# -*- coding: utf-8 -*-
"""换脸工具页(对齐原版 /tools/face-swap):

健康检查 → 导入目标图(可多张)+ 源脸照片 → 参数(全部脸/增强)→ 逐张换脸
→ 结果预览 → 「存为角色形象」落库 characters.image_url。
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QFrame,
                               QHBoxLayout, QLabel, QMessageBox, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from ..ai import face_swap
from ..core import config, db
from ..core.i18n import tr
from ..core.taskmgr import TASKMGR
from . import widgets as W


class _ImageCard(QFrame):
    """目标图卡片:缩略图 + 文件名 + 换脸后状态。"""
    def __init__(self, path: str, on_remove):
        super().__init__()
        self.setObjectName("card")
        self.path = path
        self.result_path: str | None = None
        self.setFixedSize(168, 190)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        self.img = QLabel()
        self.img.setFixedSize(150, 110)
        self.img.setAlignment(Qt.AlignCenter)
        self.img.setPixmap(W.pixmap_from_media(path, 150, 110))
        lay.addWidget(self.img)
        name = QLabel(Path(path).name[:22])
        name.setObjectName("muted")
        lay.addWidget(name)
        self.status = QLabel("待处理")
        self.status.setObjectName("muted")
        lay.addWidget(self.status)
        rm = QPushButton("× " + tr("delete"))
        rm.setStyleSheet("QPushButton{border:none;color:#e5484d;}")
        rm.clicked.connect(lambda: on_remove(self))
        lay.addWidget(rm)

    def set_result(self, path: str):
        self.result_path = path
        self.status.setText("✅ 已换脸")
        self.img.setPixmap(W.pixmap_from_media(path, 150, 110))


class FaceSwapPage(QWidget):
    def __init__(self):
        super().__init__()
        self.targets: list[_ImageCard] = []
        self.source_path: str | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(12)

        head = QHBoxLayout()
        head.addWidget(W.h1("🎭 " + tr("face_swap")))
        head.addStretch(1)
        self.health_lab = QLabel("…")
        self.health_lab.setObjectName("muted")
        head.addWidget(self.health_lab)
        recheck = QPushButton(tr("refresh"))
        recheck.clicked.connect(self._check_health)
        head.addWidget(recheck)
        root.addLayout(head)
        root.addWidget(W.muted("本地 InsightFace 换脸:源脸照片 → 替换目标图中的人脸。需先启动换脸服务(127.0.0.1:5678,见原版 face-swap-service)。"))

        bar = QHBoxLayout()
        add_btn = QPushButton("🖼 " + tr("import_files") + "(目标图)")
        add_btn.setObjectName("primary")
        add_btn.clicked.connect(self._add_targets)
        self.source_btn = QPushButton("👤 选择源脸照片")
        self.source_btn.clicked.connect(self._pick_source)
        self.all_faces = QCheckBox("替换图中所有脸")
        self.enhance = QCheckBox("人脸增强")
        go = W.primary_btn("▶ " + tr("face_swap"))
        go.clicked.connect(self._run)
        bar.addWidget(add_btn)
        bar.addWidget(self.source_btn)
        bar.addWidget(self.all_faces)
        bar.addWidget(self.enhance)
        bar.addStretch(1)
        bar.addWidget(go)
        root.addLayout(bar)

        apply_bar = QHBoxLayout()
        apply_bar.addWidget(QLabel(tr("chars") + ":"))
        self.char_combo = QComboBox()
        self.char_combo.setMinimumWidth(220)
        apply_bar.addWidget(self.char_combo)
        apply_btn = QPushButton("⬇ 存为角色形象")
        apply_btn.clicked.connect(self._apply_to_character)
        apply_bar.addWidget(apply_btn)
        apply_bar.addStretch(1)
        root.addLayout(apply_bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        self.holder = QWidget()
        self.grid_lay = QHBoxLayout(self.holder)
        self.grid_lay.setContentsMargins(0, 4, 0, 4)
        self.grid_lay.setSpacing(12)
        self.grid_lay.addStretch(1)
        self.scroll.setWidget(self.holder)
        root.addWidget(self.scroll, 1)
        self._check_health()

    def _check_health(self):
        ok, msg = face_swap.health()
        self.health_lab.setText(("✅ " if ok else "❌ ") + msg)
        # 角色下拉
        self.char_combo.clear()
        for r in db.q("SELECT id,name FROM characters ORDER BY drama_id, id"):
            self.char_combo.addItem(r["name"], r["id"])

    def _add_targets(self):
        ps, _ = QFileDialog.getOpenFileNames(self, tr("import_files"), "", "Images (*.png *.jpg *.jpeg *.webp)")
        for p in ps:
            card = _ImageCard(p, self._remove_card)
            self.targets.append(card)
            self.grid_lay.insertWidget(self.grid_lay.count() - 1, card)

    def _remove_card(self, card: _ImageCard):
        self.targets.remove(card)
        card.deleteLater()

    def _pick_source(self):
        p, _ = QFileDialog.getOpenFileName(self, "选择源脸照片", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if p:
            self.source_path = p
            self.source_btn.setText("👤 " + Path(p).name[:18])

    def _run(self):
        if not self.targets:
            QMessageBox.information(self, tr("face_swap"), tr("import_files"))
            return
        if not self.source_path:
            QMessageBox.information(self, tr("face_swap"), "请选择源脸照片")
            return
        ok, msg = face_swap.health()
        if not ok:
            QMessageBox.warning(self, tr("face_swap"), msg)
            return
        all_faces = self.all_faces.isChecked()
        enhance = self.enhance.isChecked()
        cards = list(self.targets)

        def job(tid):
            outs = []
            for c in cards:
                out = face_swap.swap_one(c.path, self.source_path,
                                         swap_all_faces=all_faces, face_enhance=enhance)
                outs.append((c, str(out)))
            return outs
        def done(tid, result, err):
            if err:
                QMessageBox.warning(self, tr("face_swap"), str(err)[:400])
            for card, out in (result or []):
                card.set_result(out)
        TASKMGR.submit("face_swap", job, done)

    def _apply_to_character(self):
        cid = self.char_combo.currentData()
        if not cid:
            return
        with_result = [c for c in self.targets if c.result_path]
        if not with_result:
            QMessageBox.information(self, tr("face_swap"), "没有换脸结果可应用")
            return
        from ..core import db as _db
        _db.ex("UPDATE characters SET image_url=?, updated_at=? WHERE id=?",
               (config.path_to_media_url(with_result[0].result_path), _db.now(), cid))
        QMessageBox.information(self, tr("face_swap"),
                                f"已应用到「{self.char_combo.currentText()}」(共 {len(with_result)} 张结果,取第一张)")
