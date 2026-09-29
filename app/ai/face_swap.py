# -*- coding: utf-8 -*-
"""本地 InsightFace 换脸服务客户端(127.0.0.1:5678,对齐原版 face-swap-service)。"""
from __future__ import annotations

import base64
import uuid
from pathlib import Path

import requests

from ..core import config

DEFAULT_BASE = "http://127.0.0.1:5678"


def health(base: str | None = None) -> tuple[bool, str]:
    base = (base or DEFAULT_BASE).rstrip("/")
    try:
        resp = requests.get(f"{base}/health", timeout=5)
        return resp.status_code == 200, resp.text[:200]
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def swap_one(target_path: str | Path, source_face_path: str | Path, base: str | None = None) -> Path:
    """单图换脸:target=要被换脸的图,source=脸来源。返回输出路径。"""
    base = (base or DEFAULT_BASE).rstrip("/")
    target = Path(target_path)
    source = Path(source_face_path)
    if not target.exists() or not source.exists():
        raise RuntimeError("换脸图片不存在")
    payload = {
        "target_image": base64.b64encode(target.read_bytes()).decode(),
        "source_image": base64.b64encode(source.read_bytes()).decode(),
    }
    resp = requests.post(f"{base}/swap", json=payload, timeout=180)
    if resp.status_code != 200:
        raise RuntimeError(f"换脸服务返回 HTTP {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    b64 = data.get("image") or data.get("result") or data.get("data")
    if not b64:
        raise RuntimeError(f"换脸服务响应无图片字段: {str(data)[:200]}")
    out = config.STATIC_DIR / "images" / f"faceswap_{uuid.uuid4().hex[:12]}.png"
    out.write_bytes(base64.b64decode(b64))
    return out
