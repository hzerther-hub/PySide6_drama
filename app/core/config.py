# -*- coding: utf-8 -*-
"""路径与环境配置:数据目录 / SQLite / 媒体目录 / ffmpeg 定位。"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

APP_NAME = "PySide6Drama"
APP_VERSION = "1.0.0"


def _base_dir() -> Path:
    # 仓库根(app/ 的上一级);打包后以 exe 所在目录为根
    here = Path(__file__).resolve().parent
    root = here.parent.parent
    return root if root.exists() else Path.cwd()


ROOT_DIR = _base_dir()
DATA_DIR = Path(os.environ.get("YIHAO_DATA_DIR") or (ROOT_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = Path(os.environ.get("SQLITE_PATH") or (DATA_DIR / "yihao.sqlite3"))
STATIC_DIR = Path(os.environ.get("STORAGE_PATH") or (DATA_DIR / "static"))
STATIC_DIR.mkdir(parents=True, exist_ok=True)
for sub in ("images", "videos", "narration", "merged", "comics", "uploads", "covers"):
    (STATIC_DIR / sub).mkdir(parents=True, exist_ok=True)

# Agent 可编辑提示词工作区(对齐原版 workspace/prompts)
WORKSPACE_DIR = Path(os.environ.get("WORKSPACE_PATH") or (ROOT_DIR / "workspace"))
PROMPTS_DIR = WORKSPACE_DIR / "prompts"
PROMPTS_DIR.mkdir(parents=True, exist_ok=True)


def find_ffmpeg() -> str | None:
    """定位 ffmpeg:环境变量 FFMPEG_BIN > PATH > vendor 目录。"""
    env = os.environ.get("FFMPEG_BIN")
    if env and Path(env).exists():
        return env
    found = shutil.which("ffmpeg")
    if found:
        return found
    vendor = ROOT_DIR / "vendor" / "ffmpeg" / "bin" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    return str(vendor) if vendor.exists() else None


def find_ffprobe() -> str | None:
    env = os.environ.get("FFPROBE_BIN")
    if env and Path(env).exists():
        return env
    found = shutil.which("ffprobe")
    if found:
        return found
    vendor = ROOT_DIR / "vendor" / "ffmpeg" / "bin" / ("ffprobe.exe" if os.name == "nt" else "ffprobe")
    return str(vendor) if vendor.exists() else None


def media_url_to_path(url: str) -> Path:
    """把存储的 /static/xxx 相对地址转为本地绝对路径。"""
    rel = url.replace("\\", "/")
    if rel.startswith("/static/"):
        rel = rel[len("/static/"):]
    elif rel.startswith("static/"):
        rel = rel[len("static/"):]
    return (STATIC_DIR / rel).resolve()


def path_to_media_url(path: str | Path) -> str:
    p = Path(path).resolve()
    try:
        rel = p.relative_to(STATIC_DIR)
    except ValueError:
        return str(p)
    return "/static/" + rel.as_posix()
