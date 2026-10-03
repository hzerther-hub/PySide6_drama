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
from .toast import err, ok
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
        head.addWidget(QLabel(tr("faceswap_svc") + ":"))
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(200)
        self.model_combo.currentIndexChanged.connect(lambda _i: self._check_health())
        head.addWidget(self.model_combo)
        self.health_lab = QLabel("…")
        self.health_lab.setObjectName("muted")
        head.addWidget(self.health_lab)
        recheck = QPushButton(tr("refresh"))
        recheck.clicked.connect(self._check_health)
        head.addWidget(recheck)
        root.addLayout(head)
        root.addWidget(W.muted("通用图片换脸工具:源脸照片 → 替换目标图中的人脸(本地 127.0.0.1:5678 或远程,在右侧下拉选择)。角色形象换脸请到「项目 → 进入制作 → 视漫制作」的角色卡片。"))

        bar = QHBoxLayout()
        add_btn = QPushButton("▣ " + tr("import_files") + "(目标图)")
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
        self.reload_models()

    def _check_health(self):
        cfg_id = self.model_combo.currentData()
        ok, msg = face_swap.health(config_id=cfg_id)
        self.health_lab.setText(("✅ " if ok else "❌ ") + msg)

    def reload_models(self):
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        rows = db.q("SELECT * FROM ai_service_configs WHERE service_type='faceswap' AND is_active=1 ORDER BY priority DESC, id")
        for r in rows:
            self.model_combo.addItem(f"{r['remark'] or r['provider']} · {r['base_url']}", r["id"])
        self.model_combo.blockSignals(False)
        self._check_health()

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
        cfg_id = self.model_combo.currentData()
        ok, msg = face_swap.health(config_id=cfg_id)
        if not ok:
            QMessageBox.warning(self, tr("face_swap"), msg)
            return
        all_faces = self.all_faces.isChecked()
        enhance = self.enhance.isChecked()
        cards = list(self.targets)

        def job(tid):
            outs = []
            for c in cards:
                out = face_swap.swap_one(c.path, self.source_path, swap_all_faces=all_faces,
                                         face_enhance=enhance, config_id=cfg_id)
                outs.append((c, str(out)))
            return outs
        def done(tid, result, error):
            if err:
                err(tr("face_swap"))
            for card, out in (result or []):
                card.set_result(out)
        TASKMGR.submit("face_swap", job, done)
