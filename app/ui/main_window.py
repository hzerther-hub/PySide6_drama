# -*- coding: utf-8 -*-
"""主窗口:顶栏(Logo/导航/主题/语言)+ QStackedWidget(启动台/项目页/工作台/复刻页/合并工具)。"""
from __future__ import annotations

import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QMainWindow,
                               QMessageBox, QPushButton, QStackedWidget,
                               QVBoxLayout, QWidget)

from ..core import config, db
from ..core.i18n import LANGS, set_language, tr
from ..core.taskmgr import TASKMGR
from ..core.theme import apply_theme
from .episode_page import EpisodePage
from .new_project_dialog import NewProjectDialog
from .project_page import ProjectPage
from .projects_page import ProjectsPage
from .settings_dialog import SettingsDialog
from . import widgets as W


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_title"))
        self.resize(1360, 860)
        from PySide6.QtGui import QIcon
        _logo = config.ROOT_DIR / "app" / "assets" / "logo.png"
        if _logo.exists():
            self.setWindowIcon(QIcon(str(_logo)))
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 顶栏
        top = QWidget()
        top.setStyleSheet("background:#202126;border-bottom:1px solid #2c2e35;")
        tlay = QHBoxLayout(top)
        tlay.setContentsMargins(20, 10, 20, 10)
        from PySide6.QtGui import QPixmap
        _logo_path = config.ROOT_DIR / "app" / "assets" / "logo.png"
        logo_lab = QLabel()
        if _logo_path.exists():
            pm = QPixmap(str(_logo_path)).scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lab.setPixmap(pm)
        else:
            logo_lab.setText("易")
        logo_lab.setStyleSheet("background:transparent;border:none;")
        logo = QLabel("易好短剧")
        logo.setStyleSheet("color:#f2f3f5;font-weight:700;font-size:16px;background:transparent;border:none;")
        tlay.addWidget(logo_lab)
        tlay.addSpacing(4)
        tlay.addWidget(logo)
        tlay.addStretch(1)
        self.nav_btns: dict[str, QPushButton] = {}
        self._nav_defs = [("projects", "▦", "nav_projects")]
        for key, icon, label_key in self._nav_defs:
            b = QPushButton(f"{icon} {tr(label_key)}")
            b.setStyleSheet("color:#c8ccd4;background:transparent;border:none;padding:6px 10px;")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, k=key: self._goto(k))
            self.nav_btns[key] = b
            tlay.addWidget(b)
        theme_btn = QPushButton("◐ " + tr("theme"))
        theme_btn.setStyleSheet("color:#c8ccd4;background:transparent;border:none;padding:6px 10px;")
        theme_btn.clicked.connect(self._toggle_theme)
        settings_btn = QPushButton("⚙️ " + tr("nav_settings"))
        settings_btn.setStyleSheet("color:#c8ccd4;background:transparent;border:none;padding:6px 10px;")
        settings_btn.clicked.connect(self._open_settings)
        lang_btn = QPushButton("◎ " + tr("lang_short"))
        lang_btn.setStyleSheet("color:#c8ccd4;background:transparent;border:none;padding:6px 10px;")
        lang_btn.clicked.connect(self._switch_language)
        tlay.addWidget(theme_btn)
        tlay.addWidget(settings_btn)
        tlay.addWidget(lang_btn)
        root.addWidget(top)

        # AI 服务未就绪横幅(缺 text/image/video 任一即显示,点此去设置)
        self.banner = QLabel()
        self.banner.setContentsMargins(20, 8, 20, 8)
        self.banner.setStyleSheet(
            "background:#fff7e6;color:#ad6800;border-bottom:1px solid #ffd591;"
            "font-weight:600;padding:6px 12px;")
        self.banner.setCursor(Qt.PointingHandCursor)
        self.banner.mousePressEvent = lambda _e: self._open_settings()
        self.banner.setVisible(False)
        root.addWidget(self.banner)
        self._refresh_ai_banner()

        # 页面栈
        self.stack = QStackedWidget()
        self.projects_page = ProjectsPage()
        self.project_page = ProjectPage()
        self.episode_page = EpisodePage()
        self.clone_page = ClonePage()
        for p in (self.projects_page, self.project_page, self.episode_page, self.clone_page):
            self.stack.addWidget(p)
        root.addWidget(self.stack, 1)

        # 状态栏
        self.status = self.statusBar()

        # 全局 toast(D 类)
        from .toast import ToastManager
        ToastManager.attach(central)

        # 信号
        self.projects_page.set_new_callback(self._new_project)
        self.projects_page.open_drama.connect(self._open_drama)
        self.project_page.set_callbacks(self._back_to_projects, self._enter_episode, self._promo_dialog)
        self.episode_page.back_requested.connect(self._back_to_project)
        self.clone_page.back_requested.connect(self._back_to_projects)
        TASKMGR.updated.connect(lambda: self.status.showMessage(
            f"{tr('tasks')}: {TASKMGR.active_count()} {tr('in_progress')}"))

    def retranslate(self):
        """语言切换后即时刷新顶栏与标题(页面内容重启后完全生效)。"""
        self.setWindowTitle(tr("app_title"))
        for key, icon, label_key in self._nav_defs:
            self.nav_btns[key].setText(f"{icon} {tr(label_key)}")

    def _refresh_ai_banner(self):
        """AI 服务就绪横幅:缺失时明确列出缺哪几类,点击直达设置。"""
        try:
            from ..ai import registry
            miss = registry.missing_services()
        except Exception:  # noqa: BLE001
            return
        if miss:
            names = "、".join(registry.SVC_CN_LABEL.get(m, m) for m in miss)
            self.banner.setText(f"⚠ AI 服务未配置完整(缺:{names}) — 依赖模型的操作会无法执行,点击此处去「设置 → AI 服务」补全")
            self.banner.setVisible(True)
        else:
            self.banner.setVisible(False)

    def _goto(self, key: str):
        self.stack.setCurrentWidget(self.projects_page)
        self.projects_page.reload()

    def _new_project(self):
        dlg = NewProjectDialog(self)
        if dlg.exec() != NewProjectDialog.Accepted:
            return
        data = dlg.result_data()
        ts = db.now()
        drama_id = db.ex(
            "INSERT INTO dramas(title,style,aspect_ratio,work_type,ethnicity,metadata,status,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?, 'pending', ?, ?)",
            (data["title"], data["style"], data["aspect_ratio"], data["work_type"],
             data["ethnicity"], data["metadata"], ts, ts))
        ep_id = db.ex(
            "INSERT INTO episodes(drama_id,episode_number,title,status,resolution,created_at,updated_at)"
            " VALUES(?,1,?,'pending','720p',?,?)",
            (drama_id, tr("episode_n").format(1), ts, ts))
        # 同款复刻:导入参考视频与素材
        if data["work_type"] == "video_clone":
            from ..pipeline import video_clone
            meta = db.jload(data["metadata"], {})
            src = meta.get("clone", {})
            if src.get("reference_src"):
                video_clone.import_reference(drama_id, src["reference_src"])
            if src.get("product_src"):
                video_clone.upload_material(drama_id, "product", src["product_src"])
            if src.get("presenter_src"):
                video_clone.upload_material(drama_id, "presenter", src["presenter_src"])
        self.projects_page.reload()
        self._open_drama(drama_id)

    def _open_drama(self, drama_id: int):
        d = db.q1("SELECT * FROM dramas WHERE id=?", (drama_id,))
        if not d:
            return
        if d["work_type"] == "video_clone":
            self.clone_page.load(drama_id)
            self.stack.setCurrentWidget(self.clone_page)
        else:
            self.project_page.load(drama_id)
            self.stack.setCurrentWidget(self.project_page)

    def _back_to_projects(self):
        self.projects_page.reload()
        self.stack.setCurrentWidget(self.projects_page)

    def _back_to_project(self):
        self.project_page.load(self.episode_page.drama_id)
        self.stack.setCurrentWidget(self.project_page)

    def _enter_episode(self, drama_id: int, episode_id: int):
        self.episode_page.load(drama_id, episode_id)
        self.stack.setCurrentWidget(self.episode_page)

    def _promo_dialog(self, drama_id: int):
        # 宣传文案已内置到项目页(A5),这里保留兼容入口
        pass

    def _switch_language(self):
        from PySide6.QtWidgets import QDialog, QDialogButtonBox, QListWidget, QListWidgetItem
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("ui_language"))
        dlg.resize(300, 420)
        lay = QVBoxLayout(dlg)
        lw = QListWidget()
        cur = db.get_setting("ui_language", "zh")
        for code, name in LANGS:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, code)
            if code == cur:
                item.setSelected(True)
            lw.addItem(item)
        lay.addWidget(lw)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        if dlg.exec() == QDialog.Accepted and lw.currentItem():
            lang = lw.currentItem().data(Qt.UserRole)
            db.set_setting("ui_language", lang)
            db.set_setting("content_language", lang)
            QMessageBox.information(self, tr("ui_language"), "✅ 请重启应用生效 / Please restart the app.")

    def _toggle_theme(self):
        cur = db.get_setting("theme", "light")
        new = "dark" if cur != "dark" else "light"
        db.set_setting("theme", new)
        from PySide6.QtWidgets import QApplication
        apply_theme(QApplication.instance(), new)

    def _open_settings(self):
        dlg = SettingsDialog(self, on_language_changed=self._on_language_changed,
                             on_theme_changed=self._apply_theme_cb)
        dlg.exec()
        self._refresh_ai_banner()

    def _on_language_changed(self, lang: str):
        self.retranslate()

    def _apply_theme_cb(self, mode: str):
        from PySide6.QtWidgets import QApplication
        apply_theme(QApplication.instance(), "dark" if mode == "dark" else
                    ("dark" if mode == "system" and self._system_dark() else "light"))

    @staticmethod
    def _system_dark() -> bool:
        try:
            import darkdetect  # type: ignore
            return darkdetect.isDark()
        except Exception:  # noqa: BLE001
            return False


def QApplication_instance():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance()


class ClonePage(QWidget):
    """同款复刻工作台:参考视频分析 → 素材 → 逐镜重拍 → 拼接。"""
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self.drama_id = 0
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(12)
        head = QHBoxLayout()
        back = QPushButton("← " + tr("back"))
        back.clicked.connect(self.back_requested.emit)
        self.title = W.h1("")
        head.addWidget(back)
        head.addWidget(self.title)
        head.addStretch(1)
        root.addLayout(head)
        self.intro = W.muted(tr("wt_clone_desc"))
        root.addWidget(self.intro)

        bar = QHBoxLayout()
        analyze_btn = W.primary_btn("1️⃣ " + tr("detect") + " · AI " + tr("storyboard"))
        analyze_btn.clicked.connect(self._analyze)
        presenter_btn = QPushButton("2️⃣ AI " + "生成出镜模特")
        presenter_btn.clicked.connect(self._presenter)
        merge_btn = W.primary_btn("4️⃣ " + tr("merge_now"))
        merge_btn.clicked.connect(self._merge)
        bar.addWidget(analyze_btn)
        bar.addWidget(presenter_btn)
        bar.addWidget(merge_btn)
        bar.addStretch(1)
        root.addLayout(bar)
        self.board_list = QVBoxLayout()
        root.addLayout(self.board_list)
        root.addStretch(1)

    def load(self, drama_id: int):
        self.drama_id = drama_id
        d = db.q1("SELECT * FROM dramas WHERE id=?", (drama_id,))
        self.title.setText(f"▷ {d['title']}")
        self.reload()

    def reload(self):
        while self.board_list.count():
            item = self.board_list.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        from ..pipeline import video_clone
        boards = video_clone._clone_storyboards(self.drama_id)
        for b in boards:
            box = W.make_card()
            lay = QHBoxLayout(box)
            lay.setContentsMargins(12, 8, 12, 8)
            info = QVBoxLayout()
            head = QHBoxLayout()
            head.addWidget(W.h2(f"#{int(b.get('number', 0)):02d}"))
            head.addWidget(W.tag(f"{b.get('start','?')}-{b.get('end','?')}s"))
            if b.get("video"):
                head.addWidget(W.tag(tr("done")))
            head.addStretch(1)
            info.addLayout(head)
            desc = QLabel(f"{b.get('shot','')} · {b.get('action','')}  {('产品:' + b.get('product_use','')) if b.get('product_use') else ''}")
            desc.setWordWrap(True)
            info.addWidget(desc)
            if b.get("line"):
                line = QLabel("💬 " + b["line"])
                line.setObjectName("muted")
                info.addWidget(line)
            lay.addLayout(info, 1)
            btns = QVBoxLayout()
            img_btn = QPushButton("3️⃣ " + tr("redraw") + " · 首帧图")
            img_btn.clicked.connect(lambda _=False, n=int(b.get("number", 0)): self._shot_image(n))
            vid_btn = W.primary_btn("▷ " + tr("batch_video"))
            vid_btn.clicked.connect(lambda _=False, n=int(b.get("number", 0)): self._shot_video(n))
            btns.addWidget(img_btn)
            btns.addWidget(vid_btn)
            lay.addLayout(btns)
            self.board_list.addWidget(box)

    def _analyze(self):
        from ..pipeline import video_clone
        def job(tid):
            return video_clone.analyze_reference(self.drama_id)
        def done(tid, result, error):
            if error:
                err("AI")
            self.reload()
        TASKMGR.submit("clone_analyze", job, done, drama_id=self.drama_id)

    def _presenter(self):
        from ..pipeline import video_clone
        d = db.q1("SELECT style FROM dramas WHERE id=?", (self.drama_id,))
        def job(tid):
            return video_clone.prepare_presenter(self.drama_id, d["style"])
        def done(tid, result, error):
            if error:
                err("AI")
        TASKMGR.submit("clone_presenter", job, done, drama_id=self.drama_id)

    def _shot_image(self, n: int):
        from ..pipeline import video_clone
        d = db.q1("SELECT style FROM dramas WHERE id=?", (self.drama_id,))
        def job(tid):
            return str(video_clone.generate_shot_image(self.drama_id, n, d["style"]))
        def done(tid, result, error):
            if error:
                err("AI")
            self.reload()
        TASKMGR.submit("clone_image", job, done, drama_id=self.drama_id)

    def _shot_video(self, n: int):
        from ..pipeline import video_clone
        def job(tid):
            return str(video_clone.generate_shot_video(self.drama_id, n, "720p"))
        def done(tid, result, error):
            if error:
                err("AI")
            self.reload()
        TASKMGR.submit("clone_video", job, done, drama_id=self.drama_id)

    def _merge(self):
        from ..pipeline import video_clone
        def job(tid):
            return str(video_clone.merge_clone(self.drama_id))
        def done(tid, result, error):
            if error:
                err(tr("merge_now"))
            else:
                import os
                os.startfile(result)  # noqa
        TASKMGR.submit("clone_merge", job, done, drama_id=self.drama_id)
