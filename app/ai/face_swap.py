# -*- coding: utf-8 -*-
"""本地 InsightFace 换脸服务客户端(127.0.0.1:5678)。

对齐原版 face-swap-service/app.py 接口:
  POST /swap  body: {source_url, template_url, source_index, template_index,
                     swap_all_faces, face_enhance, save_local_path}
              resp: {ok, image_base64, saved_path, elapsed_ms, source_face_count, template_face_count}
  GET  /health → {status, model, providers, data_root}
source = 脸来源照片;template = 被换脸的目标图。
"""
from __future__ import annotations

import base64
import mimetypes
import uuid
from pathlib import Path

import requests

from ..core import config

DEFAULT_BASE = "http://127.0.0.1:5678"


def _to_data_url(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        return str(path)  # 允许直接传 URL / /static 相对地址
    mime = mimetypes.guess_type(str(p))[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def _resolve_base(config_id: int | None = None, base: str | None = None) -> str:
    """换脸服务地址优先级:显式 base > 指定配置 > faceswap 类默认配置 > 本地默认。"""
    if base:
        return base.rstrip("/")
    from . import registry
    cfg = registry.default_config("faceswap", config_id)
    if cfg and cfg.get("base_url"):
        return str(cfg["base_url"]).rstrip("/")
    return DEFAULT_BASE


def health(base: str | None = None, config_id: int | None = None) -> tuple[bool, str]:
    _base = _resolve_base(config_id, base)
    try:
        resp = requests.get(f"{_base}/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            # 新版返回 {local:{ok}, remote:{ok}};旧版扁平 {ok}(对齐原版 09e76b8 修复)
            ok_flag = data.get("local", {}).get("ok") if isinstance(data.get("local"), dict) else None
            if ok_flag is None:
                ok_flag = data.get("ok", False)
            model = (data.get("model") or (data.get("local") or {}).get("model") or "")
            return bool(ok_flag), f"{data.get('status', 'ok')} · {model}"
        return False, resp.text[:200]
    except Exception as e:  # noqa: BLE001
        return False, f"服务不可达({_base}):{e}"


def swap_one(template_path: str | Path, source_path: str | Path,
             swap_all_faces: bool = True, face_enhance: bool = False,
             source_index: int = 0, base: str | None = None,
             config_id: int | None = None) -> Path:
    """单图换脸:template=被换图,source=脸来源。返回输出图片路径。

    config_id/base 可指向本地(127.0.0.1:5678)或远程换脸服务,接口协议一致。
    """
    _base = _resolve_base(config_id, base)
    # 输出格式按模板扩展名判定(对齐原版:png 保留透明通道,否则 jpg)
    out_fmt = "png" if str(template_path).lower().endswith(".png") else "jpg"
    payload = {
        "source_url": _to_data_url(source_path),
        "template_url": _to_data_url(template_path),
        "source_index": source_index,
        "template_index": 0,
        "swap_all_faces": swap_all_faces,
        "face_enhance": face_enhance,
        "output_format": out_fmt,
    }
    resp = requests.post(f"{_base}/swap", json=payload, timeout=300)
    if resp.status_code != 200:
        raise RuntimeError(f"换脸服务返回 HTTP {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    if not data.get("ok") or not data.get("image_base64"):
        raise RuntimeError(f"换脸失败: {str(data)[:200]}")
    out = config.STATIC_DIR / "images" / f"faceswap_{uuid.uuid4().hex[:12]}.png"
    out.write_bytes(base64.b64decode(data["image_base64"]))
    return out


def test_config(cfg: dict) -> tuple[bool, str]:
    return health(cfg.get("base_url"))
