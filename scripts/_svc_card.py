class ServiceCard(QFrame):
    """一条 AI 服务配置卡片:徽章 + 名称/Key 标 + 模型 chips + 开关 + 测试/编辑/删除。

    对齐原版 settings.vue 的 config card(provider logo badge、名称、「有 Key/无 Key」标、
    「已停用」标、点击 model chip 设默认、逐行 Test、启用开关、编辑、删除)。
    """

    def __init__(self, cfg: dict, parent, on_toggle=None, on_test=None,
                 on_edit=None, on_delete=None, on_set_default_model=None):
        super().__init__()
        self.cfg = cfg
        self.setObjectName("svcCard")
        self.setEnabled(True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        head = QHBoxLayout()
        head.setSpacing(8)
        # 供应商标识徽章(取首字母,原版是 provider logo)
        badge = QLabel((cfg.get("remark") or cfg.get("provider") or "?")[:1].upper())
        badge.setFixedSize(28, 28)
        badge.setAlignment(Qt.AlignCenter)
        badge.setObjectName("svcBadge")
        badge.setStyleSheet(
            f"background:{_provider_tint(cfg.get('provider'))}; color:#fff;"
            "border-radius:7px; font-weight:800;")
        head.addWidget(badge)
        name = QLabel(cfg.get("remark") or cfg.get("provider") or "")
        f = name.font()
        f.setBold(True)
        name.setFont(f)
        name.setToolTip(f"{cfg.get('provider')}  ·  {cfg.get('base_url')}")
        head.addWidget(name)
        head.addWidget(W.tag(tr("configured") if cfg.get("api_key") else tr("no_key")))
        if cfg.get("is_default"):
            head.addWidget(self._tag_orange(tr("default")))
        if not cfg.get("is_active"):
            off = W.tag(tr("stopped"))
            off.setStyleSheet("background:#fdecec;color:#dc2626;border-radius:4px;padding:2px 8px;")
            head.addWidget(off)
        head.addStretch(1)
        head.addWidget(W.tag(f"P{cfg.get('priority') or 0}"))
        # 启用开关
        self.toggle = QCheckBox("")
        self.toggle.setChecked(bool(cfg.get("is_active")))
        self.toggle.setToolTip(tr("toggle_enabled"))
        self.toggle.toggled.connect(lambda on: on_toggle(cfg, on) if on_toggle else None)
        head.addWidget(self.toggle)
        lay.addLayout(head)

        # 模型 chips:点一下即设为该配置的默认模型
        models = _cfg_models(cfg)
        if models:
            chips = _FlowLayout()
            for i, m in enumerate(models):
                is_default = (i == 0)
                chip = QPushButton(("★ " if is_default else "") + m)
                chip.setToolTip(tr("click_set_default_model") if not is_default
                                else tr("is_default_model"))
                chip.setStyleSheet(
                    "QPushButton{border-radius:12px;padding:3px 10px;font-size:12px;"
                    + ("QPushButton{background:#f97316;color:white;font-weight:700;border:none;}"
                       if is_default else
                       "QPushButton{background:rgba(128,128,128,35);color:inherit;}"))
                if not is_default and on_set_default_model:
                    chip.setCursor(Qt.PointingHandCursor)
                    chip.clicked.connect(
                        lambda _=False, mm=m: on_set_default_model(cfg, mm))
                chips.add(chip)
            lay.addLayout(chips)
        else:
            lay.addWidget(W.muted(tr("no_models_yet")))

        base = QLabel(cfg.get("base_url") or "")
        base.setObjectName("muted")
        base.setToolTip(base.text())
        lay.addWidget(base)

        # 动作行
        actions = QHBoxLayout()
        actions.setSpacing(6)
        self.test_btn = WaitingButton(tr("test"))
        self.test_btn.setFixedHeight(26)
        self.test_btn.clicked.connect(lambda: on_test(cfg) if on_test else None)
        actions.addWidget(self.test_btn)
        actions.addStretch(1)
        edit = QPushButton("✎ " + tr("edit"))
        edit.setFixedHeight(26)
        edit.clicked.connect(lambda: on_edit(cfg) if on_edit else None)
        actions.addWidget(edit)
        delete = QPushButton("🗑 " + tr("delete"))
        delete.setObjectName("danger")
        delete.setFixedHeight(26)
        delete.clicked.connect(lambda: on_delete(cfg) if on_delete else None)
        actions.addWidget(delete)
        lay.addLayout(actions)

    @staticmethod
    def _tag_orange(text: str) -> QLabel:
        t = W.tag(text)
        t.setStyleSheet("background:#fdf0e6;color:#ea580c;border-radius:4px;padding:2px 8px;")
        return t


def _provider_tint(provider: str | None) -> str:
    """按 provider 给徽章一个稳定颜色(同 provider 同色)。"""
    palette = {"openai": "#10a37f", "gemini": "#4285f4", "volcengine": "#f97316",
               "agnes": "#8b5cf6", "minimax": "#ef4444", "aliyun": "#0ea5e9",
               "qwen-image": "#6366f1", "xiaoyunque": "#ec4899",
               "local-faceswap": "#64748b", "remote-faceswap": "#64748b", "jev": "#14b8a6"}
    return palette.get(provider or "", "#64748b")


def _cfg_models(cfg: dict) -> list[str]:
    """配置上的模型列表:优先 models 数组,否则回落到单个 model。"""
    raw = cfg.get("models")
    if raw:
        try:
            models = json.loads(raw) if isinstance(raw, str) else list(raw)
        except (TypeError, ValueError):
            models = []
        if isinstance(models, list):
            models = [str(m) for m in models if m]
            if models:
                return models
    m = (cfg.get("model") or "").strip()
    return [m] if m else []