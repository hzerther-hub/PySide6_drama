# -*- coding: utf-8 -*-
"""设置对话框:AI 服务 / 通用(15 语言+主题)/ 风格预设 / Agent 配置 / 存储 / 关于更新。"""
from __future__ import annotations

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                               QFileDialog, QFormLayout, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem,
                               QMessageBox, QPlainTextEdit, QPushButton,
                               QStackedWidget, QTabWidget, QVBoxLayout, QWidget)

from ..agents import prompts
from ..ai import registry
from ..ai.image_client import test_config as img_test
from ..ai.text_client import test_config as text_test
from ..ai.tts_client import test_config as tts_test
from ..ai.video_client import test_config as video_test
from ..core import config, db
from ..core.i18n import LANGS, tr
from . import widgets as W

TESTERS = {"text": text_test, "image": img_test, "video": video_test, "tts": tts_test}
SVC_LABEL = {"text": "text_svc", "image": "image_svc", "video": "video_svc", "tts": "tts_svc"}


class SettingsDialog(QDialog):
    def __init__(self, parent=None, on_language_changed=None, on_theme_changed=None):
        super().__init__(parent)
        self.setWindowTitle(tr("settings"))
        self.resize(880, 620)
        self._on_lang = on_language_changed
        self._on_theme = on_theme_changed
        root = QHBoxLayout(self)
        self.tabs_nav = QListWidget()
        self.tabs_nav.setFixedWidth(150)
        for key, icon in [("ai_services", "🔌"), ("general", "⚙️"), ("style_presets", "🎨"),
                          ("agent_config", "🤖"), ("storage", "💾"), ("about_update", "ℹ️")]:
            item = QListWidgetItem(f"{icon}  {tr(key)}")
            self.tabs_nav.addItem(item)
        root.addWidget(self.tabs_nav)
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)
        self.pages = [self._page_ai(), self._page_general(), self._page_styles(),
                      self._page_agents(), self._page_storage(), self._page_about()]
        for p in self.pages:
            self.stack.addWidget(p)
        self.tabs_nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.tabs_nav.setCurrentRow(0)

    # ── AI 服务 ──
    def _page_ai(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)
        quick = W.make_card()
        q_lay = QVBoxLayout(quick)
        q_lay.setContentsMargins(14, 12, 14, 12)
        q_lay.addWidget(W.h2(tr("quick_config") + " · 推荐"))
        q_lay.addWidget(W.muted(tr("quick_hint")))
        row = QHBoxLayout()
        self.yihao_key = QLineEdit()
        self.yihao_key.setPlaceholderText("Yihao API Key")
        apply_btn = W.primary_btn(tr("write_config"))
        apply_btn.clicked.connect(self._apply_yihao)
        row.addWidget(self.yihao_key, 1)
        row.addWidget(apply_btn)
        q_lay.addLayout(row)
        lay.addWidget(quick)

        self.svc_tabs = QTabWidget()
        for st in registry.SERVICE_TYPES:
            tab = QWidget()
            t_lay = QVBoxLayout(tab)
            desc = {"text": "svc_text_desc", "image": "svc_image_desc",
                    "video": "svc_video_desc", "tts": "svc_tts_desc"}[st]
            bar = QHBoxLayout()
            bar.addWidget(W.muted(tr(desc)))
            bar.addStretch(1)
            add = QPushButton("＋ " + tr("add"))
            add.clicked.connect(lambda _=False, s=st: self._add_service(s))
            bar.addWidget(add)
            t_lay.addLayout(bar)
            listw = QListWidget()
            listw.setObjectName(f"svc_{st}")
            t_lay.addWidget(listw)
            self.svc_tabs.addTab(tab, tr(SVC_LABEL[st]))
            self._fill_services(st)
        lay.addWidget(self.svc_tabs, 1)
        return w

    def _fill_services(self, st: str):
        listw = self.findChild(QListWidget, f"svc_{st}")
        if not listw:
            return
        listw.clear()
        for r in registry.list_configs(st):
            status = tr("configured") if r["api_key"] else "no key"
            default = " · 默认" if r["is_default"] else ""
            active = "" if r["is_active"] else " · " + tr("stopped")
            item = QListWidgetItem(f"[{r['provider']}] {r['model']}  ·  {status}{default}{active}")
            item.setData(Qt.UserRole, dict(r))
            listw.addItem(item)
        listw.itemDoubleClicked.connect(lambda item: self._edit_service(item))

    def _apply_yihao(self):
        key = self.yihao_key.text().strip()
        if not key:
            return
        created = registry.apply_yihao_key(key)
        for st in registry.SERVICE_TYPES:
            self._fill_services(st)
        QMessageBox.information(self, tr("write_config"), "\n".join(created))

    def _add_service(self, st: str):
        from PySide6.QtWidgets import QInputDialog
        presets = registry.PROVIDER_PRESETS.get(st, [])
        names = [p["name"] for p in presets]
        name, ok = QInputDialog.getItem(self, tr("add"), tr("provider"), names, 0, False)
        if not ok:
            return
        preset = next(p for p in presets if p["name"] == name)
        model, ok2 = QInputDialog.getItem(self, tr("model"), tr("model"), preset["models"], 0, True)
        if not ok2:
            return
        dlg = _ServiceDialog(st, preset, model, self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.data()
            registry.add_config(st, data["provider"], data["base_url"], data["model"],
                                data["api_key"], data["is_default"])
            self._fill_services(st)

    def _edit_service(self, item: QListWidgetItem):
        cfg = item.data(Qt.UserRole)
        st = cfg["service_type"]
        dlg = _ServiceDialog(st, {"provider": cfg["provider"], "base_url": cfg["base_url"]},
                             cfg["model"], self, existing=dict(cfg))
        if dlg.exec() == QDialog.Accepted:
            data = dlg.data()
            registry.update_config(cfg["id"], provider=data["provider"], base_url=data["base_url"],
                                    model=data["model"], api_key=data["api_key"],
                                    is_default=data["is_default"], is_active=data["is_active"])
            self._fill_services(st)

    # ── 通用(语言 15 种 + 主题) ──
    def _page_general(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(14)
        box = W.make_card()
        f = QFormLayout(box)
        f.setContentsMargins(14, 14, 14, 14)
        self.lang_combo = QComboBox()
        for code, name in LANGS:
            self.lang_combo.addItem(f"{name} ({code})", code)
        cur = db.get_setting("content_language", "zh")
        i = self.lang_combo.findData(cur)
        self.lang_combo.setCurrentIndex(i if i >= 0 else 0)
        f.addRow(tr("ui_language"), self.lang_combo)
        f.addRow("", W.muted(tr("language_note") + "  ·  UI × 15 / AI × 15"))
        self.lang_combo.currentIndexChanged.connect(self._change_lang)
        theme_box = QWidget()
        trow = QHBoxLayout(theme_box)
        trow.setContentsMargins(0, 0, 0, 0)
        self.theme_combo = QComboBox()
        for key, label in [("light", tr("light")), ("dark", tr("dark")), ("system", tr("follow_system"))]:
            self.theme_combo.addItem(label, key)
        cur_t = db.get_setting("theme", "light")
        j = self.theme_combo.findData(cur_t)
        self.theme_combo.setCurrentIndex(j if j >= 0 else 0)
        self.theme_combo.currentIndexChanged.connect(self._change_theme)
        trow.addWidget(self.theme_combo)
        trow.addStretch(1)
        f.addRow(tr("theme"), theme_box)
        lay.addWidget(box)
        lay.addStretch(1)
        return w

    def _change_lang(self):
        lang = self.lang_combo.currentData()
        db.set_setting("content_language", lang)
        db.set_setting("ui_language", lang)
        from ..core.i18n import set_language
        set_language(lang)
        if self._on_lang:
            self._on_lang(lang)

    def _change_theme(self):
        mode = self.theme_combo.currentData()
        db.set_setting("theme", mode)
        if self._on_theme:
            self._on_theme(mode)

    # ── 风格预设 ──
    def _page_styles(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)
        self.style_list = QListWidget()
        for r in db.q("SELECT * FROM style_presets ORDER BY sort_order"):
            active = "✅" if r["is_active"] else "⛔"
            item = QListWidgetItem(f"{active}  {r['name']}  ·  {r['description'] or ''}")
            item.setData(Qt.UserRole, dict(r))
            self.style_list.addItem(item)
        self.style_list.itemDoubleClicked.connect(self._edit_style)
        lay.addWidget(W.muted("双击编辑风格 · 电影质感提示词前缀"))
        lay.addWidget(self.style_list)
        return w

    def _edit_style(self, item: QListWidgetItem):
        row = item.data(Qt.UserRole)
        dlg = _StyleDialog(dict(row), self)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.data()
            db.ex("UPDATE style_presets SET name=?, prompt=?, description=?, is_active=? WHERE id=?",
                  (d["name"], d["prompt"], d["description"], d["is_active"], row["id"]))
            self.style_list.clear()
            self.pages[2] = self._page_styles()
            # 简化:重建当前页
            self._refresh_styles()

    def _refresh_styles(self):
        self.style_list.clear()
        for r in db.q("SELECT * FROM style_presets ORDER BY sort_order"):
            active = "✅" if r["is_active"] else "⛔"
            item = QListWidgetItem(f"{active}  {r['name']}  ·  {r['description'] or ''}")
            item.setData(Qt.UserRole, dict(r))
            self.style_list.addItem(item)

    # ── Agent 配置 ──
    def _page_agents(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)
        self.agent_list = QListWidget()
        self.agent_list.setFixedWidth(220)
        for a in prompts.AGENT_META:
            QListWidgetItem(f"{a['icon']}  {a['name']}", self.agent_list)
        lay.addWidget(self.agent_list)
        right = QVBoxLayout()
        self.agent_meta_lab = W.muted("")
        right.addWidget(self.agent_meta_lab)
        self.agent_lang = QComboBox()
        for code, name in LANGS:
            self.agent_lang.addItem(name, code)
        self.agent_lang.setCurrentIndex(0)
        self.agent_lang.currentIndexChanged.connect(self._load_agent_prompt)
        right.addWidget(QLabel(tr("edit_lang_follow")))
        right.addWidget(self.agent_lang)
        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setMinimumHeight(340)
        right.addWidget(self.prompt_edit, 1)
        btns = QHBoxLayout()
        save = W.primary_btn(tr("save"))
        save.clicked.connect(self._save_agent_prompt)
        reset = QPushButton(tr("restore_default"))
        reset.clicked.connect(self._reset_agent_prompt)
        btns.addWidget(save)
        btns.addWidget(reset)
        btns.addStretch(1)
        right.addLayout(btns)
        lay.addLayout(right, 1)
        self.agent_list.currentRowChanged.connect(lambda _i: self._load_agent_prompt())
        self.agent_list.setCurrentRow(0)
        self._load_agent_prompt()
        return w

    def _current_agent(self) -> str:
        row = self.agent_list.currentRow()
        if 0 <= row < len(prompts.AGENT_META):
            return prompts.AGENT_META[row]["type"]
        return ""

    def _load_agent_prompt(self):
        agent = self._current_agent()
        lang = self.agent_lang.currentData()
        if not agent:
            return
        path = prompts.prompt_file(agent, lang)
        text = path.read_text(encoding="utf-8") if path.exists() else prompts.DEFAULT_PROMPTS.get(agent, "")
        self.prompt_edit.setPlainText(text)
        self.agent_meta_lab.setText(tr("prompt_saved").format(agent) + (f".{lang}" if lang != "zh" else ""))

    def _save_agent_prompt(self):
        agent = self._current_agent()
        if agent:
            prompts.save_prompt(agent, self.agent_lang.currentData(), self.prompt_edit.toPlainText())

    def _reset_agent_prompt(self):
        agent = self._current_agent()
        if agent:
            prompts.reset_prompt(agent, self.agent_lang.currentData())
            self._load_agent_prompt()

    # ── 存储 ──
    def _page_storage(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)
        db_size = config.DB_PATH.stat().st_size if config.DB_PATH.exists() else 0
        static_size = sum(f.stat().st_size for f in config.STATIC_DIR.rglob("*") if f.is_file())
        box = W.make_card()
        f = QFormLayout(box)
        f.setContentsMargins(14, 14, 14, 14)
        f.addRow("SQLite", QLabel(f"{config.DB_PATH}  ({db_size/1048576:.1f} MB)"))
        f.addRow(tr("storage"), QLabel(f"{config.STATIC_DIR}  ({static_size/1048576:.1f} MB)"))
        open_btn = QPushButton("打开数据目录")
        open_btn.clicked.connect(lambda: __import__("os").startfile(str(config.DATA_DIR)))  # noqa
        f.addRow("", open_btn)
        lay.addWidget(box)
        lay.addStretch(1)
        return w

    # ── 关于 ──
    def _page_about(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.addWidget(W.h2(f"易好短剧 PySide6 版 · {tr('version')} {config.APP_VERSION}"))
        lay.addWidget(W.muted("按「易好短剧」(Yihao Drama)功能 100% 复刻的 PySide6 桌面实现。"))
        lay.addWidget(W.muted(f"语言 / Languages: {len(LANGS)}(中文/EN/日本語/한국어/Français/Deutsch/Italiano/Português/Español/Tiếng Việt/Türkçe/العربية/हिन्दी/Bahasa Indonesia/ภาษาไทย)"))
        lay.addWidget(W.muted("核心:10 Agents · 20 风格预设 · 无损合并(easymerger) · 同款复刻(video-clone-lite) · FFmpeg 拼接+旁白混音"))
        check = QPushButton(tr("check_update"))
        check.clicked.connect(self._check_update)
        lay.addWidget(check)
        self.update_lab = QLabel("")
        lay.addWidget(self.update_lab)
        lay.addStretch(1)
        return w

    def _check_update(self):
        import requests
        try:
            resp = requests.get("https://api.github.com/repos/hzerther-hub/PySide6_drama/releases/latest", timeout=10)
            if resp.status_code == 200:
                tag = resp.json().get("tag_name", "?")
                self.update_lab.setText(f"GitHub latest: {tag} · {tr('version')} {config.APP_VERSION}")
            else:
                self.update_lab.setText(f"GitHub HTTP {resp.status_code}")
        except Exception as e:  # noqa: BLE001
            self.update_lab.setText(f"{e}"[:120])


class _ServiceDialog(QDialog):
    def __init__(self, st: str, preset: dict, model: str, parent=None, existing: dict | None = None):
        super().__init__(parent)
        self._st = st
        self.setWindowTitle(f"{tr(SVC_LABEL[st])} · {preset.get('provider','')}")
        self.resize(460, 240)
        self._preset = preset
        lay = QVBoxLayout(self)
        f = QFormLayout()
        self.provider = QLineEdit(preset.get("provider", ""))
        self.base_url = QLineEdit(preset.get("base_url", ""))
        self.model_edit = QLineEdit(model)
        self.api_key = QLineEdit(existing.get("api_key", "") if existing else "")
        self.api_key.setEchoMode(QLineEdit.Password)
        self.default_cb = QCheckBox(tr("enabled") + " / " + "默认")
        self.active_cb = QCheckBox(tr("enabled"))
        self.active_cb.setChecked(bool(existing["is_active"]) if existing else True)
        f.addRow(tr("provider"), self.provider)
        f.addRow(tr("base_url"), self.base_url)
        f.addRow(tr("model"), self.model_edit)
        f.addRow(tr("api_key"), self.api_key)
        f.addRow("", self.default_cb)
        f.addRow("", self.active_cb)
        lay.addLayout(f)
        test_btn = QPushButton(tr("test"))
        test_btn.clicked.connect(self._test)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        row = QHBoxLayout()
        row.addWidget(test_btn)
        row.addStretch(1)
        row.addWidget(btns)
        lay.addLayout(row)
        self.test_lab = QLabel("")
        lay.addWidget(self.test_lab)

    def _test(self):
        cfg = self.data()
        ok, msg = TESTERS[cfg["service_type"]](cfg)
        self.test_lab.setText(("✅ " if ok else "❌ ") + msg[:160])

    def data(self) -> dict:
        return {"service_type": self._st,
                "provider": self.provider.text().strip(),
                "base_url": self.base_url.text().strip(),
                "model": self.model_edit.text().strip(),
                "api_key": self.api_key.text().strip(),
                "is_default": self.default_cb.isChecked(),
                "is_active": self.active_cb.isChecked()}


class _StyleDialog(QDialog):
    def __init__(self, row: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(row["name"])
        self.resize(560, 420)
        lay = QVBoxLayout(self)
        f = QFormLayout()
        self.name = QLineEdit(row["name"])
        self.desc = QLineEdit(row.get("description") or "")
        self.active = QCheckBox(tr("enabled"))
        self.active.setChecked(bool(row["is_active"]))
        f.addRow(tr("visual_style"), self.name)
        f.addRow("描述", self.desc)
        f.addRow("", self.active)
        lay.addLayout(f)
        self.prompt = QPlainTextEdit(row["prompt"])
        lay.addWidget(self.prompt, 1)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def data(self) -> dict:
        return {"name": self.name.text().strip(), "prompt": self.prompt.toPlainText(),
                "description": self.desc.text().strip(), "is_active": 1 if self.active.isChecked() else 0}
