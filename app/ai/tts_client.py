# -*- coding: utf-8 -*-
"""TTS 旁白配音:火山引擎豆包语音(seed-tts 异步轮询 → seed-audio 同步 base64 双路径 fallback)。"""
from __future__ import annotations

import base64
import json
import time
import uuid
from pathlib import Path

import requests

from ..core import config
from . import registry
from .text_client import AIError


def _out_path() -> Path:
    return config.STATIC_DIR / "narration" / f"{uuid.uuid4().hex}.mp3"


def synthesize(text: str, voice: str = "BV001_streaming",
               target_duration: float | None = None, config_id: int | None = None) -> Path:
    """合成旁白 MP3。target_duration(秒)时自适应语速(对齐原版 narration_duration 逻辑)。"""
    cfg = registry.default_config("tts", config_id)
    if not cfg:
        raise AIError("未配置配音(TTS)服务,请到「设置 → AI 服务 → 配音」添加。")
    if not cfg.get("api_key"):
        raise AIError("配音服务缺少 API Key(火山引擎访问令牌)。")
    base = cfg["base_url"].rstrip("/")
    key = cfg["api_key"]
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer; {key}"}
    speed_ratio = 1.0
    if target_duration and target_duration > 0:
        est = max(len(text) / 4.5, 1.0)  # 粗略估算自然语速时长
        speed_ratio = round(min(max(est / target_duration, 0.5), 2.0), 2)

    out = _out_path()
    # 路径一:seed-tts-2.0 提交+轮询
    try:
        body = {
            "model": cfg["model"].startswith("seed-tts") and cfg["model"] or "seed-tts-2.0",
            "text": text,
            "voice": {"type": "voice_type", "voice_type": voice.replace("_streaming", "")},
            "audio_params": {"format": "mp3", "speed_ratio": speed_ratio},
        }
        resp = requests.post(f"{base}/api/v3/tts/unidirectional", json=body, headers=headers, stream=True, timeout=120)
        if resp.status_code == 200:
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            if out.stat().st_size > 512:
                return out
        # 尝试异步任务形态
        resp2 = requests.post(f"{base}/api/v3/tts/proxy/tts", json={
            "app": {"appid": "yihao", "token": key, "cluster": "volcano_tts"},
            "user": {"uid": "pyside6"},
            "audio": {"voice_type": voice, "encoding": "mp3", "speed_ratio": speed_ratio},
            "request": {"text": text, "operation": "QUERY"},
        }, headers={"Content-Type": "application/json", "Authorization": f"Bearer; {key}"}, timeout=120)
        if resp2.status_code == 200:
            data = resp2.json()
            b64 = data.get("data")
            if b64:
                out.write_bytes(base64.b64decode(b64))
                return out
            raise AIError(f"TTS 响应无音频: {json.dumps(data)[:300]}")
    except requests.RequestException as e:
        # 落到路径二
        err1 = str(e)
    # 路径二:seed-audio-1.0 同步(兜底)
    resp3 = requests.post(f"{base}/api/v1/tts", json={
        "text": text, "voice_type": voice, "speed_ratio": speed_ratio, "encoding": "mp3",
    }, headers={"Content-Type": "application/json", "Authorization": f"Bearer; {key}"}, timeout=120)
    if resp3.status_code == 200:
        try:
            b64 = resp3.json()["data"]
            out.write_bytes(base64.b64decode(b64))
            return out
        except Exception:  # noqa: BLE001
            pass
    raise AIError(f"TTS 合成失败: HTTP {resp3.status_code} {resp3.text[:200]}")


def test_config(cfg: dict) -> tuple[bool, str]:
    try:
        p = synthesize("测试", config_id=cfg["id"])
        p.unlink(missing_ok=True)
        return True, "OK"
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:300]
