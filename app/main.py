# -*- coding: utf-8 -*-
"""易好短剧 · PySide6 版 入口。

运行:python app/main.py(Python 3.10+)
"""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .agents.prompts import seed_prompt_files
from .core import db
from .core.i18n import set_language
from .core.theme import apply_theme, load_bundled_fonts


def _apply_drama_font(app) -> None:
    """字体策略对齐原版 drama(body 栈:SF Pro → PingFang SC → Microsoft YaHei):
    1. assets/fonts/ 打包字体(本仓库内置 msyh.ttc,跨环境一致);
    2. macOS 回落 PingFang SC;Windows 回落 Microsoft YaHei UI。"""
    from PySide6.QtGui import QFont
    families = load_bundled_fonts(app)
    if families:
        app.setFont(QFont(families[0], 10))
        return
    if sys.platform == "darwin":
        f = QFont("PingFang SC", 10)
    else:
        f = QFont("Microsoft YaHei UI", 10)
        f.setStyleHint(QFont.SansSerif)
    f.setPointSize(10)
    app.setFont(f)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PySide6Drama")

    db.init_db()
    seed_prompt_files()
    from .ai.registry import seed_tts_default, seed_faceswap_default
    seed_tts_default()
    seed_faceswap_default()

    lang = db.get_setting("ui_language", "zh")
    set_language(lang)
    _apply_drama_font(app)
    apply_theme(app, db.get_setting("theme", "light"))

    from .ui.main_window import MainWindow
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
