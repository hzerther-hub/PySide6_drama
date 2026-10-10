# -*- coding: utf-8 -*-
"""流式生成:后台线程逐块收文本,推给界面实时显示。

用 QThread + 信号(Qt 队列连接,自动跨线程投递到 GUI 线程),不用手工加锁。
流式端点不支持时由 `text_stream.chat_stream` 内部回落成一次性返回,调用方无感。
"""
from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

from ..ai import text_stream

# 思考过程用灰色斜体,正式输出正常字色 —— 一眼能分清「想的过程」和「最终结果」
REASONING_COLOR = QColor("#8b909a")
CONTENT_COLOR = QColor("#1f2329")
DARK_REASONING = QColor("#8b909a")


class StreamWorker(QThread):
    """跑一次流式生成。delta 逐块发,finished 带完整文本,failed 带错误。"""

    delta = Signal(str, str)      # (kind, text);kind ∈ reasoning / content
    finished = Signal(str)         # 仅正式内容
    failed = Signal(str)

    def __init__(self, prompt: str, *, system: str | None = None,
                 config_id: int | None = None, temperature: float = 0.7,
                 max_tokens: int = 8192, json_mode: bool = False,
                 parent: QObject | None = None):
        super().__init__(parent)
        self._prompt = prompt
        self._system = system
        self._config_id = config_id
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._json_mode = json_mode
        self._content: list[str] = []
        self._reasoning: list[str] = []
        self.cancelled = False

    @property
    def content(self) -> str:
        """**只有正式输出**——思考过程不参与落库。"""
        return "".join(self._content)

    @property
    def reasoning(self) -> str:
        return "".join(self._reasoning)

    def cancel(self) -> None:
        """请求停止(下一个数据块到达时生效)。"""
        self.cancelled = True

    def run(self) -> None:                       # noqa: D102  (QThread 入口)
        try:
            for kind, chunk in text_stream.chat_stream(
                    self._prompt, system=self._system, config_id=self._config_id,
                    temperature=self._temperature, max_tokens=self._max_tokens,
                    json_mode=self._json_mode):
                if self.cancelled:
                    break
                if kind == "reasoning":
                    self._reasoning.append(chunk)
                else:
                    self._content.append(chunk)
                self.delta.emit(kind, chunk)
            self.finished.emit(self.content)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


def _formats(dark: bool) -> tuple[QTextCharFormat, QTextCharFormat]:
    """(思考格式, 正文格式)。"""
    think = QTextCharFormat()
    think.setForeground(DARK_REASONING if dark else REASONING_COLOR)
    f = QFont()
    f.setItalic(True)
    think.setFont(f)
    body = QTextCharFormat()
    body.setForeground(QColor("#e8eaed") if dark else CONTENT_COLOR)
    body.setFont(QFont())                    # 取消斜体
    return think, body


def stream_into(editor: QPlainTextEdit | QTextEdit, prompt: str, *,
                system: str | None = None, config_id: int | None = None,
                temperature: float = 0.7, max_tokens: int = 8192,
                json_mode: bool = False,
                on_finished=None, on_failed=None,
                owner: QWidget | None = None) -> StreamWorker:
    """把一次流式生成实时写进 `editor`,并保持自动滚到底。

    **思考过程会显示(灰色斜体),但 on_finished 只拿到正式内容** ——
    落库时不会把「用户要求…必须先调用工具…」这类思考混进正文。
    返回 worker(调用方负责在销毁时 cancel+wait,以免线程仍在往已释放的控件投递)。
    """
    editable_before = editor.isReadOnly()
    editor.setReadOnly(True)
    editor.setPlainText("")
    dark = is_dark(editor)

    def _append(kind: str, chunk: str) -> None:
        think_fmt, body_fmt = _formats(dark)
        cur = editor.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        cur.setCharFormat(think_fmt if kind == "reasoning" else body_fmt)
        cur.insertText(chunk)
        editor.setTextCursor(cur)
        bar = editor.verticalScrollBar()
        bar.setValue(bar.maximum())          # 跟随输出滚动

    worker = StreamWorker(prompt, system=system, config_id=config_id,
                          temperature=temperature, max_tokens=max_tokens,
                          json_mode=json_mode, parent=owner)

    def _done(text: str) -> None:
        editor.setReadOnly(editable_before)
        if on_finished:
            on_finished(text)

    def _failed(msg: str) -> None:
        editor.setReadOnly(editable_before)
        if on_failed:
            on_failed(msg)

    worker.delta.connect(_append)
    worker.finished.connect(_done)
    worker.failed.connect(_failed)
    worker.start()
    return worker


def is_dark(widget: QWidget) -> bool:
    """按调色板亮度粗判当前是亮色还是暗色主题(决定思考文字的颜色)。"""
    return widget.palette().color(widget.palette().ColorRole.Window).lightnessF() < 0.5
