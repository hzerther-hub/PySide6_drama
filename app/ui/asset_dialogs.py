# -*- coding: utf-8 -*-
"""项目设置 + 素材详情编辑弹窗(对齐原版 detail.vue 的项目设置 / 素材详情对话框)。"""
from __future__ import annotations

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDialog, QFormLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
                               QPushButton, QScrollArea, QVBoxLayout, QWidget)

from ..core import config, db
from ..core.i18n import tr
from . import widgets as W

ASPECTS = [("16:9", "16:9 · 横屏"), ("9:16", "9:16 · 竖屏"), ("1:1", "1:1 · 方形"), ("adaptive", "自适应")]
ETHNICITIES = [("auto", "智能匹配"), ("east_asian", "东亚"), ("middle_eastern", "中东"),
               ("western", "西方"), ("south_asian", "南亚"), ("latin", "拉美"), ("african", "非洲"), ("mixed", "混合")]


def _muted(t: str) -> QLabel:
    return W.muted(t)


class ProjectSettingsDialog(QDialog):
    """项目设置:标题 / 简介 / 题材 / 画幅 / 视觉风格 / 面孔文化。"""

    def __init__(self, parent, drama_id: int):
        super().__init__(parent)
        self.drama_id = drama_id
        d = db.q1("SELECT * FROM dramas WHERE id=?", (drama_id,))
        self.setWindowTitle(tr("project_settings"))
        self.resize(480, 460)
        root = QVBoxLayout(self)
        root.addWidget(W.h2(tr("project_settings")))
        f = QFormLayout()
        self.title = QLineEdit(d["title"])
        f.addRow(tr("project_name"), self.title)
        meta = db.jload(d["metadata"], {})
        self.intro = QLineEdit(meta.get("intro", ""))
        self.intro.setPlaceholderText("一句话简介(可选)")
        f.addRow("简介", self.intro)
        self.genre = QLineEdit(meta.get("genre", ""))
        self.genre.setPlaceholderText("题材,如 都市情感 / 仙侠")
        f.addRow("题材", self.genre)
        self.aspect = QComboBox()
        for v, label in ASPECTS:
            self.aspect.addItem(label, v)
        i = self.aspect.findData(d["aspect_ratio"])
        self.aspect.setCurrentIndex(i if i >= 0 else 0)
        f.addRow(tr("aspect_ratio"), self.aspect)
        self.style = QComboBox()
        for r in db.q("SELECT value,name FROM style_presets WHERE is_active=1 ORDER BY sort_order"):
            self.style.addItem(r["name"], r["value"])
        i = self.style.findData(d["style"])
        self.style.setCurrentIndex(i if i >= 0 else 0)
        f.addRow(tr("visual_style"), self.style)
        self.ethnicity = QComboBox()
        for v, label in ETHNICITIES:
            self.ethnicity.addItem(label, v)
        i = self.ethnicity.findData(d["ethnicity"])
        self.ethnicity.setCurrentIndex(i if i >= 0 else 0)
        f.addRow(tr("ethnicity"), self.ethnicity)
        root.addLayout(f)
        root.addStretch(1)
        row = QHBoxLayout()
        cancel = QPushButton(tr("cancel"))
        cancel.clicked.connect(self.reject)
        save = W.primary_btn(tr("save"))
        save.clicked.connect(self._save)
        row.addStretch(1)
        row.addWidget(cancel)
        row.addWidget(save)
        root.addLayout(row)

    def _save(self):
        d = db.q1("SELECT metadata FROM dramas WHERE id=?", (self.drama_id,))
        meta = db.jload(d["metadata"], {}) if d else {}
        meta["intro"] = self.intro.text().strip()
        meta["genre"] = self.genre.text().strip()
        db.ex("UPDATE dramas SET title=?, aspect_ratio=?, style=?, ethnicity=?, metadata=?, updated_at=? WHERE id=?",
              (self.title.text().strip() or "未命名", self.aspect.currentData(),
               self.style.currentData(), self.ethnicity.currentData(),
               json.dumps(meta, ensure_ascii=False), db.now(), self.drama_id))
        self.accept()


class ImageViewerDialog(QDialog):
    """大图查看器(点击图片放大)。"""
    def __init__(self, parent, url: str | None, title: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title or "预览")
        self.resize(760, 620)
        root = QVBoxLayout(self)
        img = QLabel()
        img.setAlignment(Qt.AlignCenter)
        img.setPixmap(W.pixmap_from_media(url, 700, 540))
        root.addWidget(img, 1)
        close = W.primary_btn(tr("close"))
        close.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(close)
        root.addLayout(row)


class AssetDetailDialog(QDialog):
    """素材详情编辑(对齐原版):
    左预览(点击放大)+ 右编辑(角色名/角色定位/样貌/妆造 · 场景地点/时间/描述/光影/标签 · 道具名/类型/外貌)
    + 造型变体面板(角色)+ 最终提示词面板(生成/编辑/复制)+ footer(删除/关闭/上传/生成/保存)
    """

    KINDS = {"character": ("characters", tr("chars")), "scene": ("scenes", tr("scenes")), "prop": ("props", tr("props"))}

    def __init__(self, parent, kind: str, row: dict, on_changed=None):
        super().__init__(parent)
        self.kind = kind
        self.table = self.KINDS[kind][0]
        self.row = row
        self._on_changed = on_changed
        self.setWindowTitle(f"{self.KINDS[kind][1]} · {row['name']}")
        self.resize(860, 660)
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.addWidget(W.h2(f"{self.KINDS[kind][1]} · {row['name']}"))

        body = QHBoxLayout()
        # 左预览
        left = QVBoxLayout()
        self.img = QLabel()
        self.img.setAlignment(Qt.AlignCenter)
        self.img.setFixedSize(280, 280)
        self.img.setStyleSheet("border:1px solid rgba(128,128,128,60);border-radius:8px;")
        self.img.setPixmap(W.pixmap_from_media(row.get("image_url"), 276, 276))
        self.img.mousePressEvent = lambda _e: ImageViewerDialog(self, row.get("image_url"), row["name"]).exec()
        self.img.setToolTip("点击查看大图")
        left.addWidget(self.img)
        body.addLayout(left)
        # 右编辑
        right = QVBoxLayout()
        f = QFormLayout()
        if kind == "character":
            self.name = QLineEdit(row["name"])
            f.addRow(tr("project_name").replace(tr("project_name"), "名称"), self.name)
            self.role = QComboBox()
            for v, label in (("lead", tr("lead")), ("supporting", tr("supporting")), ("extra", tr("extra"))):
                self.role.addItem(label, v)
            i = self.role.findData(row.get("role_type") or "supporting")
            self.role.setCurrentIndex(i if i >= 0 else 1)
            f.addRow("角色定位", self.role)
            self.appearance = QPlainTextEdit(row.get("appearance") or "")
            f.addRow(tr("appearance"), self.appearance)
            self.styling = QPlainTextEdit(row.get("styling") or "")
            f.addRow(tr("styling"), self.styling)
        elif kind == "scene":
            self.name = QLineEdit(row["name"])
            f.addRow("名称", self.name)
            self.location = QLineEdit(row.get("location") or "")
            f.addRow("地点", self.location)
            self.time = QLineEdit(row.get("time") or "")
            f.addRow("时间", self.time)
            self.desc = QPlainTextEdit(row.get("prompt") or "")
            f.addRow("描述", self.desc)
            self.lighting = QPlainTextEdit(row.get("lighting") or "")
            f.addRow(tr("lighting"), self.lighting)
            tags = db.jload(row.get("setting_tags"), []) or []
            self.tags = QLineEdit(", ".join(tags))
            self.tags.setPlaceholderText("标签,逗号分隔(如 室内,夜)")
            f.addRow("标签", self.tags)
        else:
            self.name = QLineEdit(row["name"])
            f.addRow("名称", self.name)
            self.ptype = QComboBox()
            for v in ("prop", "信物", "文件", "关键道具"):
                self.ptype.addItem(v, v)
            i = self.ptype.findData(row.get("type") or "prop")
            self.ptype.setCurrentIndex(i if i >= 0 else 0)
            f.addRow("类型", self.ptype)
            self.desc = QPlainTextEdit(row.get("description") or "")
            f.addRow("外貌", self.desc)
        right.addLayout(f)
        right.addStretch(1)
        body.addLayout(right, 1)
        root.addLayout(body, 1)

        # 最终提示词
        fp_box = W.make_card()
        fp_lay = QVBoxLayout(fp_box)
        fp_lay.setContentsMargins(10, 8, 10, 8)
        fp_lay.addWidget(W.h2(tr("final_prompt")))
        self.fp = QPlainTextEdit(row.get("final_prompt") or "")
        self.fp.setMaximumHeight(90)
        self.fp.setPlaceholderText("可手动编辑;或点「AI 生成」自动产出")
        fp_lay.addWidget(self.fp)
        fp_btns = QHBoxLayout()
        gen_fp = QPushButton("✨ AI 生成")
        gen_fp.clicked.connect(self._gen_prompt)
        regen_fp = QPushButton("↻ 重新生成")
        regen_fp.clicked.connect(self._gen_prompt)
        copy_fp = QPushButton("▤ 复制")
        copy_fp.clicked.connect(self._copy_prompt)
        for b in (gen_fp, regen_fp, copy_fp):
            fp_btns.addWidget(b)
        fp_btns.addStretch(1)
        fp_lay.addLayout(fp_btns)
        root.addWidget(fp_box)

        # 角色变体
        if kind == "character":
            var_btn = QPushButton("◑ 造型变体")
            var_btn.clicked.connect(self._open_variants)
            root.addWidget(var_btn)

        # footer
        footer = QHBoxLayout()
        delete = W.danger_btn(tr("delete"))
        delete.clicked.connect(self._delete)
        footer.addWidget(delete)
        footer.addStretch(1)
        upload = QPushButton(tr("upload"))
        upload.clicked.connect(self._upload)
        gen_img = W.primary_btn("◑ 生成形象")
        gen_img.clicked.connect(self._gen_image)
        save = W.primary_btn(tr("save"))
        save.clicked.connect(self._save)
        close = QPushButton(tr("close"))
        close.clicked.connect(self.accept)
        for b in (upload, gen_img, save, close):
            footer.addWidget(b)
        root.addLayout(footer)

    def _collect(self) -> dict:
        d = {"name": self.name.text().strip() or self.row["name"]}
        if self.kind == "character":
            d.update(role_type=self.role.currentData(),
                     appearance=self.appearance.toPlainText(), styling=self.styling.toPlainText())
        elif self.kind == "scene":
            tags = [t.strip() for t in self.tags.text().split(",") if t.strip()]
            d.update(location=self.location.text().strip(), time=self.time.text().strip(),
                     prompt=self.desc.toPlainText(), lighting=self.lighting.toPlainText(),
                     setting_tags=json.dumps(tags, ensure_ascii=False))
        else:
            d.update(type=self.ptype.currentData(), description=self.desc.toPlainText())
        return d

    def _save(self):
        d = self._collect()
        sets = ",".join(f"{k}=?" for k in d)
        db.ex(f"UPDATE {self.table} SET {sets}, updated_at=? WHERE id=?", (*d.values(), db.now(), self.row["id"]))
        if self._on_changed:
            self._on_changed()
        self.accept()

    def _copy_prompt(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.fp.toPlainText())

    def _gen_prompt(self):
        from ..core.taskmgr import TASKMGR
        from .toast import err, ok
        d = db.q1(f"SELECT * FROM {self.table} WHERE id=?", (self.row["id"],))
        merged = {**dict(d), **self._collect()}
        from ..pipeline import prompts_gen
        fn = {"character": prompts_gen.character_prompt, "scene": prompts_gen.scene_prompt,
              "prop": prompts_gen.prop_prompt}[self.kind]
        def job(tid):
            return fn(self.row["id"])
        def done(tid, result, err_):
            if err_:
                err(err_)
            else:
                ok("提示词已生成")
                d2 = db.q1(f"SELECT final_prompt FROM {self.table} WHERE id=?", (self.row["id"],))
                self.fp.setPlainText(d2["final_prompt"] or "")
        TASKMGR.submit("prompt", job, done)

    def _gen_image(self):
        from ..core.taskmgr import TASKMGR
        from .toast import err
        from ..ai import image_client
        def job(tid):
            fp = self.fp.toPlainText() or self.row.get("final_prompt") or ""
            if not fp:
                raise RuntimeError("请先生成最终提示词")
            out, _p = image_client.generate_image(fp)
            url = config.path_to_media_url(out)
            db.ex(f"UPDATE {self.table} SET image_url=?, updated_at=? WHERE id=?", (url, db.now(), self.row["id"]))
            return url
        def done(tid, result, err_):
            if err_:
                err(err_)
            else:
                self.img.setPixmap(W.pixmap_from_media(result, 276, 276))
                if self._on_changed:
                    self._on_changed()
        TASKMGR.submit("image", job, done)

    def _upload(self):
        import shutil
        from PySide6.QtWidgets import QFileDialog
        p, _ = QFileDialog.getOpenFileName(self, tr("upload"), "", "Images (*.png *.jpg *.jpeg *.webp)")
        if not p:
            return
        dst = config.STATIC_DIR / "uploads" / f"up_{self.row['id']}_{config.uuid.uuid4().hex[:6]}{p[p.rfind('.'):][:8]}"
        shutil.copy(p, dst)
        url = config.path_to_media_url(dst)
        db.ex(f"UPDATE {self.table} SET image_url=?, updated_at=? WHERE id=?", (url, db.now(), self.row["id"]))
        self.img.setPixmap(W.pixmap_from_media(url, 276, 276))
        if self._on_changed:
            self._on_changed()

    def _delete(self):
        if QMessageBox.question(self, tr("delete"), f"确定删除「{self.row['name']}」?") != QMessageBox.Yes:
            return
        for t in ("episode_characters", "episode_scenes", "episode_props"):
            db.ex(f"DELETE FROM {t} WHERE {self.table[:-1]}_id=?", (self.row["id"],))
        db.ex(f"DELETE FROM {self.table} WHERE id=?", (self.row["id"],))
        if self._on_changed:
            self._on_changed()
        self.accept()

    def _open_variants(self):
        from .variants_dialog import VariantsDialog
        c = db.q1("SELECT * FROM characters WHERE id=?", (self.row["id"],))
        if c:
            VariantsDialog(self, dict(c)).exec()
            if self._on_changed:
                self._on_changed()
