# -*- coding: utf-8 -*-
"""设置对话框:AI 服务 / 通用(15 语言+主题)/ 风格预设 / Agent 配置 / 存储 / 关于更新。"""
from __future__ import annotations

import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                               QFileDialog, QFormLayout, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem,
                               QMessageBox, QPlainTextEdit, QPushButton, QSpinBox,
                               QStackedWidget, QTabWidget, QVBoxLayout, QWidget)

from ..agents import prompts
from ..ai import face_swap as fs_mod
from ..ai import registry
from ..ai.registry import SVC_CN
from ..ai.image_client import test_config as img_test
from ..ai.text_client import test_config as text_test
from ..ai.tts_client import test_config as tts_test
from ..ai.video_client import test_config as video_test
from ..core import config, db
from ..core.i18n import LANGS, tr
from . import widgets as W

TESTERS = {"text": text_test, "image": img_test, "video": video_test,
           "tts": tts_test, "faceswap": fs_mod.test_config}
SVC_LABEL = {"text": "text_svc", "image": "image_svc", "video": "video_svc",
             "tts": "tts_svc", "faceswap": "faceswap_svc"}
SVC_DESC = {"text": "svc_text_desc", "image": "svc_image_desc",
            "video": "svc_video_desc", "tts": "svc_tts_desc",
            "faceswap": "本地或远程 InsightFace 换脸服务(角色形象换脸/换脸工具页)"}


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

        # 手动模板(对齐原版:选服务类型直接填推荐 provider/base URL/model)
        manual = W.make_card()
        m_lay = QVBoxLayout(manual)
        m_lay.setContentsMargins(14, 12, 14, 12)
        m_lay.addWidget(W.h2("手动模板"))
        m_lay.addWidget(W.muted("选择服务类型后,直接用模板填充推荐的 `provider / base URL / model`。"))
        chips = QHBoxLayout()
        for st in registry.SERVICE_TYPES:
            b = QPushButton(tr(SVC_LABEL[st]))
            b.setStyleSheet("QPushButton{border-radius:14px;padding:5px 18px;background:rgba(128,128,128,30);font-weight:600;}")
            b.clicked.connect(lambda _=False, s=st: self._add_service(s))
            chips.addWidget(b)
        chips.addStretch(1)
        m_lay.addLayout(chips)
        lay.addWidget(manual)

        self.svc_tabs = QTabWidget()
        self._svc_lists: dict[str, QListWidget] = {}
        for st in registry.SERVICE_TYPES:
            tab = QWidget()
            t_lay = QVBoxLayout(tab)
            desc = SVC_DESC[st]
            bar = QHBoxLayout()
            bar.addWidget(W.muted(tr(desc)))
            bar.addStretch(1)
            add = QPushButton("＋ " + tr("add"))
            add.clicked.connect(lambda _=False, s=st: self._add_service(s))
            bar.addWidget(add)
            t_lay.addLayout(bar)
            listw = QListWidget()
            self._svc_lists[st] = listw
            listw.itemDoubleClicked.connect(self._edit_service)
            t_lay.addWidget(listw)
            self.svc_tabs.addTab(tab, tr(SVC_LABEL[st]))
            self._fill_services(st)
        lay.addWidget(self.svc_tabs, 1)
        return w

    def _fill_services(self, st: str):
        listw = self._svc_lists.get(st)
        if not listw:
            return
        listw.clear()
        for r in registry.list_configs(st):
            status = tr("configured") if r["api_key"] else "no key"
            default = " · 默认" if r["is_default"] else ""
            active = "" if r["is_active"] else " · " + tr("stopped")
            name = r["remark"] or r["provider"]
            item = QListWidgetItem(f"{name}  ·  {r['model']}  ·  P{r['priority'] or 0}  ·  {status}{default}{active}")
            item.setData(Qt.UserRole, dict(r))
            listw.addItem(item)

    def _apply_yihao(self):
        key = self.yihao_key.text().strip()
        if not key:
            return
        created = registry.apply_yihao_key(key)
        for st in registry.SERVICE_TYPES:
            self._fill_services(st)
        QMessageBox.information(self, tr("write_config"), "\n".join(created))

    def _add_service(self, st: str):
        dlg = ServiceDialog(st, self)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.data()
            registry.add_config(st, d["provider"], d["base_url"], d["model"],
                                api_key=d["api_key"], remark=d["name"],
                                priority=d["priority"], models=d["models"],
                                temperature=d["temperature"])
            self._fill_services(st)

    def _edit_service(self, item: QListWidgetItem):
        cfg = dict(item.data(Qt.UserRole))
        st = cfg["service_type"]
        dlg = ServiceDialog(st, self, existing=cfg)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.data()
            registry.update_config(cfg["id"], provider=d["provider"], base_url=d["base_url"],
                                    model=d["model"], api_key=d["api_key"],
                                    remark=d["name"], priority=d["priority"],
                                    models=d["models"], temperature=d["temperature"])
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
        lay.addWidget(W.h2(f"易好短剧 · {tr('version')} {config.APP_VERSION}"))
        lay.addWidget(W.muted("「易好短剧」(Yihao Drama) 的 PySide6 桌面实现,功能对齐原版。"))
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


class _FlowLayout(QWidget):
    """简易流式布局(模板芯片/模型标签换行用)。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(8)

    def add(self, w: QWidget):
        self._lay.addWidget(w)

    def clear(self):
        while self._lay.count():
            item = self._lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


def _muted(text: str) -> QLabel:
    return W.muted(text)


class ModelChipsEditor(QWidget):
    """多模型标签编辑器(对齐原版):首位为默认模型;点标签置顶;× 删除;输入框支持逗号/换行批量。"""
    changed = Signal()

    def __init__(self, models=None):
        super().__init__()
        self.models = [m for m in (models or []) if m]
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        self.flow = _FlowLayout()
        lay.addWidget(self.flow)
        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("输入模型名,回车添加(支持逗号/换行批量粘贴)")
        self.input.returnPressed.connect(self._add_from_input)
        add_btn = QPushButton("新增")
        add_btn.clicked.connect(self._add_from_input)
        row.addWidget(self.input, 1)
        row.addWidget(add_btn)
        lay.addLayout(row)
        lay.addWidget(_muted("首位为默认模型;点击标签可置顶,输入框支持逗号/换行批量粘贴"))
        self._render()

    def _render(self):
        self.flow.clear()
        for i, m in enumerate(list(self.models)):
            chip = QPushButton(m + ("  默认" if i == 0 else ""))
            chip.setToolTip("点击置顶设为默认")
            chip.setStyleSheet(
                "QPushButton{border-radius:12px; padding:3px 10px; font-size:12px;}"
                + ("QPushButton{background:#4b6ef5;color:white;font-weight:700;border:none;}"
                   if i == 0 else "QPushButton{background:rgba(128,128,128,35);}"))
            chip.clicked.connect(lambda _=False, idx=i: self._promote(idx))
            self.flow.add(chip)
            x = QPushButton("×")
            x.setFixedSize(22, 22)
            x.setStyleSheet("QPushButton{border:none;background:transparent;color:#888;font-weight:700;}")
            x.clicked.connect(lambda _=False, idx=i: self._remove(idx))
            self.flow.add(x)

    def _promote(self, idx: int):
        if idx <= 0:
            return
        self.models.insert(0, self.models.pop(idx))
        self._render()
        self.changed.emit()

    def _remove(self, idx: int):
        self.models.pop(idx)
        self._render()
        self.changed.emit()

    def _add_from_input(self):
        import re as _re
        for part in _re.split(r"[,\n;，；]", self.input.text()):
            p = part.strip()
            if p and p not in self.models:
                self.models.append(p)
        self.input.clear()
        self._render()
        self.changed.emit()

    def set_models(self, models):
        self.models = [m for m in (models or []) if m]
        self._render()
        self.changed.emit()


class ServiceDialog(QDialog):
    """添加/编辑 AI 服务(对齐原版「添加文本服务」界面):

    模板快选 → 配置名称/服务商/优先级/API Key/Base URL/多模型标签/Temperature → 测试配置/保存。
    """

    def __init__(self, st: str, parent=None, existing=None):
        super().__init__(parent)
        import json as _json
        self._st = st
        self._existing = existing
        cn = SVC_CN[st]
        self.setWindowTitle(("编辑" if existing else "添加") + cn + "服务")
        self.resize(560, 760)
        root = QVBoxLayout(self)
        root.setSpacing(10)

        head = QHBoxLayout()
        head.addWidget(W.h2(("编辑" if existing else "添加") + cn + "服务"))
        head.addStretch(1)
        head.addWidget(W.tag(cn))
        root.addLayout(head)
        root.addWidget(_muted("推荐先选择模板,系统会自动填入更合理的 `Base URL` 与默认模型。"))

        self.tpl_flow = _FlowLayout()
        for p in registry.PROVIDER_PRESETS.get(st, []):
            b = QPushButton(p["name"])
            b.setStyleSheet("QPushButton{border-radius:14px;padding:5px 14px;background:rgba(128,128,128,30);font-weight:600;}")
            b.clicked.connect(lambda _=False, pr=p: self._apply_template(pr))
            self.tpl_flow.add(b)
        root.addWidget(self.tpl_flow)

        form = QFormLayout()
        form.setSpacing(8)
        self.name_edit = QLineEdit()
        form.addRow("配置名称", self.name_edit)
        self.provider_combo = QComboBox()
        self.provider_combo.setEditable(True)
        seen = []
        for p in registry.PROVIDER_PRESETS.get(st, []):
            if p["provider"] not in seen:
                seen.append(p["provider"])
        self.provider_combo.addItems(seen)
        form.addRow("服务商", self.provider_combo)
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(-99, 99)
        self.priority_spin.setValue(0)
        form.addRow("优先级", self.priority_spin)
        form.addRow("", _muted("数值越高越优先。工作台默认使用同类型里优先级最高的启用配置。"))
        self.api_key = QLineEdit()
        self.api_key.setPlaceholderText("sk-...")
        self.api_key.setEchoMode(QLineEdit.Password)
        form.addRow("API Key", self.api_key)
        self.base_url = QLineEdit()
        form.addRow("Base URL", self.base_url)
        self.models_editor = ModelChipsEditor()
        form.addRow("模型", self.models_editor)
        self.temperature = QLineEdit()
        self.temperature.setPlaceholderText("如 0.6")
        form.addRow("Temperature (留空跟随服务默认)", self.temperature)
        form.addRow("", _muted("部分模型强制固定温度(如 kimi-k2 只允许 0.6),遇 invalid temperature 错误时在此填入对应值"))
        root.addLayout(form)
        root.addStretch(1)

        bottom = QHBoxLayout()
        test_btn = QPushButton("测试配置")
        test_btn.setStyleSheet("QPushButton{color:#e0794b;border:none;font-weight:700;}")
        test_btn.clicked.connect(self._test)
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        save = W.primary_btn("保存")
        save.clicked.connect(self._save)
        bottom.addWidget(test_btn)
        bottom.addStretch(1)
        bottom.addWidget(cancel)
        bottom.addWidget(save)
        root.addLayout(bottom)
        self.test_lab = QLabel("")
        self.test_lab.setWordWrap(True)
        root.addWidget(self.test_lab)

        if existing:
            self._prefill(_json)

    def _apply_template(self, p: dict):
        self.name_edit.setText(f"{p['name']}-{SVC_CN[self._st]}")
        i = self.provider_combo.findText(p["provider"])
        if i >= 0:
            self.provider_combo.setCurrentIndex(i)
        else:
            self.provider_combo.setCurrentText(p["provider"])
        self.base_url.setText(p["base_url"])
        self.models_editor.set_models(list(p["models"]))

    def _prefill(self, _json):
        e = self._existing
        self.name_edit.setText(e.get("remark") or "")
        i = self.provider_combo.findText(e["provider"])
        self.provider_combo.setCurrentIndex(i if i >= 0 else 0)
        if i < 0:
            self.provider_combo.setCurrentText(e["provider"])
        self.priority_spin.setValue(int(e.get("priority") or 0))
        self.api_key.setText(e.get("api_key") or "")
        self.base_url.setText(e.get("base_url") or "")
        models = _json.loads(e["models"]) if e.get("models") else [e["model"]]
        self.models_editor.set_models(models)
        if e.get("temperature") is not None:
            self.temperature.setText(str(e["temperature"]))

    def _collect(self) -> dict:
        temp_raw = self.temperature.text().strip()
        temperature = None
        if temp_raw:
            try:
                temperature = float(temp_raw)
            except ValueError:
                pass
        models = self.models_editor.models or [""]
        return {"service_type": self._st,
                "name": self.name_edit.text().strip(),
                "provider": self.provider_combo.currentText().strip(),
                "base_url": self.base_url.text().strip(),
                "api_key": self.api_key.text().strip(),
                "priority": self.priority_spin.value(),
                "models": models,
                "model": models[0],
                "temperature": temperature}

    def _test(self):
        cfg = self._collect()
        ok, msg = TESTERS[cfg["service_type"]](
            {"service_type": cfg["service_type"], "provider": cfg["provider"],
             "base_url": cfg["base_url"], "api_key": cfg["api_key"], "model": cfg["model"]})
        self.test_lab.setText(("✅ " if ok else "❌ ") + msg[:200])

    def _save(self):
        data = self._collect()
        if not data["model"] or not data["base_url"]:
            self.test_lab.setText("❌ Base URL 与至少一个模型必填")
            return
        self.accept()

    def data(self) -> dict:
        return self._collect()


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
