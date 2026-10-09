# -*- coding: utf-8 -*-
"""浅色 / 深色 QSS 主题。

字体策略对齐原版 drama(frontend/app/assets/studio.css):
  body/display: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif
  mono:         ui-monospace, 'SF Mono', Menlo, 'Fira Code', Consolas, monospace
Windows 上实际回落到 Microsoft YaHei;macOS 回落 PingFang SC。
"""
from __future__ import annotations

FONT_STACK = "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', 'Hiragino Sans GB', 'Heiti SC', sans-serif"
MONO_STACK = "ui-monospace, 'SF Mono', 'SFMono-Regular', Menlo, 'Fira Code', Consolas, monospace"

_QSS_BODY = None  # 字体栈直接内联进两套 QSS

# 制作流水线侧栏(对齐原版 episode.vue 的 .sidebar / .pipe-section / .pipe-item /
# .sidebar-progress)。用 objectName 承载,亮暗两套各一份,避免组件里写死颜色。
SIDEBAR_QSS_LIGHT = """
QWidget#sidebar { background: #f7f8fa; border-right: 1px solid #e4e7ec; }
QLabel#pipeSection { color: #4e5969; font-size: 11px; font-weight: 700; letter-spacing: 1px; padding: 10px 4px 2px 4px; }
QLabel#pipeTag { background: #eef1fe; color: #4b6ef5; border-radius: 4px; padding: 1px 6px; font-size: 11px; font-weight: 600; }
QLabel#pipeState { color: #c0c6cf; font-size: 12px; }
QLabel#pipeState[done="1"] { color: #4b6ef5; }
QPushButton#pipeItem { background: transparent; border: none; border-radius: 6px; padding: 6px 8px; text-align: left; color: #1f2329; }
QPushButton#pipeItem:hover { background: #eef1fe; color: #4b6ef5; }
QPushButton#pipeItem:checked { background: #eef1fe; color: #4b6ef5; font-weight: 700; }
QPushButton#pipeItem:disabled { background: transparent; color: #c0c6cf; }
QPushButton#pipeToggle { background: transparent; border: none; color: #86909c; padding: 5px 8px; text-align: left; }
QPushButton#pipeToggle:hover { color: #4b6ef5; }
QPushButton#pipeSeg { background: #e4e7ec; border: none; border-radius: 3px; height: 6px; }
QPushButton#pipeSeg:hover { background: #c0c6cf; }
QPushButton#pipeSeg[state="done"] { background: #4b6ef5; }
QPushButton#pipeSeg[state="current"] { background: #aab8f8; }
QLabel#pipeProgLabel { color: #86909c; font-size: 11px; }
QLabel#pipeProgLabel[on="1"] { color: #4b6ef5; font-weight: 700; }
QLabel#pipeProgLabel[done="1"] { color: #4e5969; }
"""

SIDEBAR_QSS_DARK = """
QWidget#sidebar { background: #1a1c20; border-right: 1px solid #2c2e35; }
QLabel#pipeSection { color: #8b909a; font-size: 11px; font-weight: 700; letter-spacing: 1px; padding: 10px 4px 2px 4px; }
QLabel#pipeTag { background: #2b3252; color: #8ba0ff; border-radius: 4px; padding: 1px 6px; font-size: 11px; font-weight: 600; }
QLabel#pipeState { color: #5a5d66; font-size: 12px; }
QLabel#pipeState[done="1"] { color: #6b87f8; }
QPushButton#pipeItem { background: transparent; border: none; border-radius: 6px; padding: 6px 8px; text-align: left; color: #e8eaed; }
QPushButton#pipeItem:hover { background: #26282e; color: #8ba0ff; }
QPushButton#pipeItem:checked { background: #2b3252; color: #8ba0ff; font-weight: 700; }
QPushButton#pipeItem:disabled { background: transparent; color: #5a5d66; }
QPushButton#pipeToggle { background: transparent; border: none; color: #8b909a; padding: 5px 8px; text-align: left; }
QPushButton#pipeToggle:hover { color: #8ba0ff; }
QPushButton#pipeSeg { background: #31343d; border: none; border-radius: 3px; height: 6px; }
QPushButton#pipeSeg:hover { background: #454953; }
QPushButton#pipeSeg[state="done"] { background: #4b6ef5; }
QPushButton#pipeSeg[state="current"] { background: #3d4570; }
QLabel#pipeProgLabel { color: #5a5d66; font-size: 11px; }
QLabel#pipeProgLabel[on="1"] { color: #8ba0ff; font-weight: 700; }
QLabel#pipeProgLabel[done="1"] { color: #8b909a; }
"""


def load_bundled_fonts(app) -> list[str]:
    """注册 assets/fonts/ 下的打包字体(分发用);原版 drama 不内置字体,返回已注册 family。"""
    from pathlib import Path
    from PySide6.QtGui import QFontDatabase
    fonts_dir = Path(__file__).resolve().parent.parent / "assets" / "fonts"
    families: list[str] = []
    if fonts_dir.exists():
        for f in sorted(fonts_dir.glob("*")):
            if f.suffix.lower() in (".ttf", ".otf", ".ttc"):
                fid = QFontDatabase.addApplicationFont(str(f))
                fams = QFontDatabase.applicationFontFamilies(fid)
                families += fams
    return families


LIGHT_QSS = """
* { font-family: """ + FONT_STACK + """; font-size: 13px; }
QMainWindow, QDialog { background: #f5f6f8; }
QWidget#card { background: #ffffff; border: 1px solid #e4e7ec; border-radius: 10px; }
QLabel#h1 { font-size: 22px; font-weight: 700; color: #1f2329; }
QLabel#h2 { font-size: 16px; font-weight: 700; color: #1f2329; }
QLabel#muted { color: #86909c; font-size: 12px; }
QLabel#tag { background: #f2f3f5; border-radius: 4px; padding: 2px 8px; color: #4e5969; font-size: 12px; }
QPushButton { background: #ffffff; border: 1px solid #d5d9e0; border-radius: 6px; padding: 6px 14px; color: #1f2329; }
QPushButton:hover { border-color: #4b6ef5; color: #4b6ef5; }
QPushButton:disabled { color: #c0c6cf; border-color: #e4e7ec; }
QPushButton#primary { background: #4b6ef5; border: none; color: white; font-weight: 600; }
QPushButton#primary:hover { background: #3d5ce0; }
QPushButton#primary:disabled { background: #c2c9f5; color: #f0f1f5; }
QPushButton#danger { color: #e5484d; border-color: #f1b8ba; }
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {
  background: #ffffff; border: 1px solid #d5d9e0; border-radius: 6px; padding: 5px 8px; color: #1f2329; selection-background-color: #4b6ef5;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus { border-color: #4b6ef5; }
QComboBox QAbstractItemView { background: #ffffff; border: 1px solid #e4e7ec; selection-background-color: #eef1fe; selection-color: #1f2329; }
QListWidget, QTreeWidget, QTableWidget { background: #ffffff; border: 1px solid #e4e7ec; border-radius: 8px; }
QListWidget::item { padding: 6px 8px; border-radius: 6px; }
QListWidget::item:selected { background: #eef1fe; color: #1f2329; }
QTreeWidget::item, QTableWidget::item { padding: 4px; }
QHeaderView::section { background: #f7f8fa; border: none; border-bottom: 1px solid #e4e7ec; padding: 6px; font-weight: 600; }
QTabWidget::pane { border: 1px solid #e4e7ec; border-radius: 8px; top: -1px; }
QTabBar::tab { padding: 7px 16px; color: #4e5969; border: none; }
QTabBar::tab:selected { color: #4b6ef5; border-bottom: 2px solid #4b6ef5; }
QProgressBar { border: 1px solid #e4e7ec; border-radius: 5px; text-align: center; height: 16px; background: #ffffff; }
QProgressBar::chunk { background: #4b6ef5; border-radius: 4px; }
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: #d5d9e0; border-radius: 5px; min-height: 30px; }
QScrollBar::horizontal { background: transparent; height: 10px; }
QScrollBar::handle:horizontal { background: #d5d9e0; border-radius: 5px; min-width: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QMenu { background: #ffffff; border: 1px solid #e4e7ec; border-radius: 8px; padding: 4px; }
QMenu::item { padding: 6px 22px; border-radius: 6px; }
QMenu::item:selected { background: #eef1fe; }
QStatusBar { background: #f5f6f8; color: #86909c; }
QSplitter::handle { background: #e4e7ec; }
QToolTip { background: #ffffff; color: #1f2329; border: 1px solid #d5d9e0; padding: 4px; }
QCheckBox::indicator, QRadioButton::indicator { width: 16px; height: 16px; }
""" + SIDEBAR_QSS_LIGHT

DARK_QSS = """
* { font-family: """ + FONT_STACK + """; font-size: 13px; color: #e8eaed; }
QMainWindow, QDialog { background: #17181c; }
QWidget#card { background: #202126; border: 1px solid #2c2e35; border-radius: 10px; }
QLabel#h1 { font-size: 22px; font-weight: 700; color: #f2f3f5; }
QLabel#h2 { font-size: 16px; font-weight: 700; color: #f2f3f5; }
QLabel#muted { color: #8b909a; font-size: 12px; }
QLabel#tag { background: #2a2c33; border-radius: 4px; padding: 2px 8px; color: #b8bcc4; font-size: 12px; }
QPushButton { background: #26282e; border: 1px solid #3a3d46; border-radius: 6px; padding: 6px 14px; color: #e8eaed; }
QPushButton:hover { border-color: #6b87f8; color: #8ba0ff; }
QPushButton:disabled { color: #5a5d66; border-color: #2c2e35; }
QPushButton#primary { background: #4b6ef5; border: none; color: white; font-weight: 600; }
QPushButton#primary:hover { background: #5c7cf8; }
QPushButton#primary:disabled { background: #31343d; color: #6a6d76; }
QPushButton#danger { color: #ff7a7e; border-color: #5d3a3c; }
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {
  background: #1d1f24; border: 1px solid #3a3d46; border-radius: 6px; padding: 5px 8px; color: #e8eaed; selection-background-color: #4b6ef5;
}
QComboBox QAbstractItemView { background: #202126; border: 1px solid #3a3d46; selection-background-color: #33364a; }
QListWidget, QTreeWidget, QTableWidget { background: #202126; border: 1px solid #2c2e35; border-radius: 8px; }
QListWidget::item { padding: 6px 8px; border-radius: 6px; }
QListWidget::item:selected { background: #33364a; color: #f2f3f5; }
QHeaderView::section { background: #1d1f24; border: none; border-bottom: 1px solid #2c2e35; padding: 6px; font-weight: 600; }
QTabWidget::pane { border: 1px solid #2c2e35; border-radius: 8px; top: -1px; }
QTabBar::tab { padding: 7px 16px; color: #9aa0aa; border: none; }
QTabBar::tab:selected { color: #8ba0ff; border-bottom: 2px solid #4b6ef5; }
QProgressBar { border: 1px solid #2c2e35; border-radius: 5px; text-align: center; height: 16px; background: #1d1f24; color: #e8eaed; }
QProgressBar::chunk { background: #4b6ef5; border-radius: 4px; }
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: #3a3d46; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:horizontal { background: #3a3d46; border-radius: 5px; min-width: 30px; }
QMenu { background: #202126; border: 1px solid #3a3d46; border-radius: 8px; padding: 4px; }
QMenu::item { padding: 6px 22px; border-radius: 6px; }
QMenu::item:selected { background: #33364a; }
QStatusBar { background: #17181c; color: #8b909a; }
QToolTip { background: #26282e; color: #e8eaed; border: 1px solid #3a3d46; padding: 4px; }
""" + SIDEBAR_QSS_DARK


def apply_theme(app, mode: str = "light") -> None:
    from PySide6.QtWidgets import QApplication  # noqa: F401
    app.setStyleSheet(DARK_QSS if mode == "dark" else LIGHT_QSS)
