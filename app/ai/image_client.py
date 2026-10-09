# -*- coding: utf-8 -*-
"""图片生成客户端:openai / gemini / volcengine / agnes / qwen-image 适配(提交+轮询+落盘)。"""
from __future__ import annotations

import base64
import time
import uuid
from pathlib import Path

import requests
from PIL import Image

from ..core import config
from . import registry
from .text_client import AIError


def _download(url: str, out: Path, headers: dict | None = None) -> Path:
    resp = requests.get(url, headers=headers or {}, timeout=180)
    if resp.status_code != 200:
        raise AIError(f"下载生成图片失败 HTTP {resp.status_code}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(resp.content)
    return out


def _b64_save(b64: str, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(b64))
    return out


def _ref_data_url(path: str | Path) -> str | None:
    """参考图本地路径 → 压缩 data URL(≤768px JPEG q68,对齐原版压缩口径);失败返回 None。"""
    try:
        import io
        p = Path(path)
        if not p.exists():
            return None
        with Image.open(p) as im:
            im = im.convert("RGB")
            im.thumbnail((768, 768))
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=68)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:  # noqa: BLE001
        return None


def generate_image(prompt: str, out_name: str | None = None,
                   config_id: int | None = None, size: str | None = None,
                   reference_images: list[str] | None = None) -> tuple[Path, str]:
    """生图:返回 (本地路径, provider)。reference_images 为本地路径列表(图生图参考)。

    仅 agnes 注入(extra_body.image[],≤6 张压缩 data URI);其余 provider 忽略。
    """
    cfg = registry.check_ready("image", config_id)  # 未配置/缺 Key 直接拦下
    provider = cfg["provider"]
    out_name = out_name or f"{uuid.uuid4().hex}.png"
    out = config.STATIC_DIR / "images" / out_name
    headers = {"Content-Type": "application/json"}
    if cfg.get("api_key"):
        headers["Authorization"] = f"Bearer {cfg['api_key']}"

    if provider in ("openai", "gemini", "qwen-image"):
        # OpenAI 兼容 images/generations
        url = cfg["base_url"].rstrip("/") + "/images/generations"
        body: dict = {"model": cfg["model"], "prompt": prompt, "n": 1}
        if size:
            body["size"] = size
        resp = requests.post(url, json=body, headers=headers, timeout=300)
        if resp.status_code != 200:
            raise AIError(f"生图失败 HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()["data"][0]
        if data.get("b64_json"):
            _b64_save(data["b64_json"], out)
        else:
            _download(data["url"], out)
        return out, provider

    if provider == "volcengine":
        # 火山方舟 Seedream:images/generations 兼容(支持 b64 返回)
        url = cfg["base_url"].rstrip("/") + "/images/generations"
        body = {"model": cfg["model"], "prompt": prompt, "response_format": "url",
                "size": size or "2K", "watermark": False}
        resp = requests.post(url, json=body, headers=headers, timeout=300)
        if resp.status_code != 200:
            raise AIError(f"生图失败 HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()["data"][0]
        if data.get("b64_json"):
            _b64_save(data["b64_json"], out)
        else:
            _download(data["url"], out)
        return out, provider

    if provider == "agnes":
        # Agnes:提交任务 → 轮询 → 下载
        submit = cfg["base_url"].rstrip("/") + "/v1/images/generations"
        body = {"model": cfg["model"], "prompt": prompt, "n": 1}
        if size:
            body["size"] = size
        # 图生图参考(对齐原版 agnes-image adapter:extra_body.image[] data URI,≤6 张)
        refs = [r for r in (_ref_data_url(x) for x in (reference_images or [])[:6]) if r]
        if refs:
            body["extra_body"] = {"image": refs}
        resp = requests.post(submit, json=body, headers=headers, timeout=120)
        if resp.status_code not in (200, 201):
            raise AIError(f"Agnes 提交失败 HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        # 兼容同步返回与异步任务两种形态
        if isinstance(data.get("data"), list) and data["data"] and (data["data"][0].get("url") or data["data"][0].get("b64_json")):
            item = data["data"][0]
            if item.get("b64_json"):
                _b64_save(item["b64_json"], out)
            else:
                _download(item["url"], out)
            return out, provider
        task_id = data.get("id") or data.get("task_id") or data.get("data", {}).get("task_id")
        if not task_id:
            raise AIError(f"Agnes 响应缺少任务 id: {str(data)[:300]}")
        for _ in range(120):  # 5s × 120 上限 10 分钟(对齐原版)
            time.sleep(5)
            st = requests.get(f"{cfg['base_url'].rstrip('/')}/v1/images/generations/{task_id}",
                              headers=headers, timeout=30)
            payload = st.json()
            status = str(payload.get("status") or payload.get("data", {}).get("status", "")).lower()
            if status in ("succeeded", "success", "completed"):
                item = (payload.get("data") or {}).get("images") or payload.get("images") or [{}]
                url_i = item[0].get("url") or item[0].get("image_url")
                if url_i:
                    _download(url_i, out)
                    return out, provider
                b64 = item[0].get("b64_json")
                if b64:
                    _b64_save(b64, out)
                    return out, provider
                raise AIError(f"Agnes 任务完成但无图片: {str(payload)[:300]}")
            if status in ("failed", "error", "cancelled"):
                raise AIError(f"Agnes 生图任务失败: {str(payload)[:300]}")
        raise AIError("Agnes 生图任务轮询超时(10 分钟)")

    raise AIError(f"不支持的图片 provider: {provider}")


def test_config(cfg: dict) -> tuple[bool, str]:
    try:
        out, _ = generate_image("a red apple on white background, product photo",
                                out_name=f"_test_{uuid.uuid4().hex[:8]}.png")
        out.unlink(missing_ok=True)
        return True, "OK"
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:300]
