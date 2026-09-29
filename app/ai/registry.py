# -*- coding: utf-8 -*-
"""AI 服务配置注册表:四类服务(text/image/video/tts)多供应商 CRUD + 默认项 + 连通测试。"""
from __future__ import annotations

from ..core import db

SERVICE_TYPES = ["text", "image", "video", "tts"]

# 手动模板预设(对齐原版 ai_service_providers 种子:provider / base_url / model)
PROVIDER_PRESETS: dict[str, list[dict]] = {
    "text": [
        {"provider": "openai", "name": "OpenAI 兼容", "base_url": "https://api.openai.com/v1",
         "models": ["gpt-4o", "gpt-4o-mini", "deepseek-chat"]},
        {"provider": "minimax", "name": "MiniMax 官方", "base_url": "https://api.minimaxi.com/v1",
         "models": ["MiniMax-M3", "MiniMax-M2.5", "MiniMax-M2"]},
        {"provider": "gemini", "name": "Gemini", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
         "models": ["gemini-2.5-flash", "gemini-2.5-pro"]},
    ],
    "image": [
        {"provider": "agnes", "name": "Agnes 官方", "base_url": "https://apihub.agnes-ai.com",
         "models": ["agnes-image-2.5-flash", "agnes-image-2.5", "agnes-image-2.1-flash"]},
        {"provider": "openai", "name": "OpenAI Images", "base_url": "https://api.openai.com/v1",
         "models": ["gpt-image-1"]},
        {"provider": "gemini", "name": "Gemini Image", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
         "models": ["gemini-2.5-flash-image"]},
        {"provider": "volcengine", "name": "火山方舟 Seedream", "base_url": "https://ark.cn-beijing.volces.com/api/v3",
         "models": ["doubao-seedream-4-0"]},
        {"provider": "qwen-image", "name": "阿里 qwen-image", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
         "models": ["qwen-image"]},
        {"provider": "local-faceswap", "name": "本地 InsightFace 人脸融合", "base_url": "http://127.0.0.1:5678",
         "models": ["inswapper_128"]},
    ],
    "video": [
        {"provider": "volcengine", "name": "火山方舟 Seedance", "base_url": "https://ark.cn-beijing.volces.com/api/v3",
         "models": ["doubao-seedance-2-0", "doubao-seedance-2-0-fast", "doubao-seedance-2-0-mini"]},
        {"provider": "minimax", "name": "MiniMax", "base_url": "https://api.minimaxi.com/v1",
         "models": ["MiniMax-H3"]},
        {"provider": "aliyun", "name": "阿里云百炼 Wan", "base_url": "https://dashscope.aliyuncs.com",
         "models": ["wan3.0-video", "wan3.0-video-prime"]},
        {"provider": "agnes", "name": "Agnes 官方", "base_url": "https://apihub.agnes-ai.com",
         "models": ["agnes-video-2.5-flash", "agnes-video-2.5"]},
    ],
    "tts": [
        {"provider": "volcengine", "name": "豆包语音(火山引擎)", "base_url": "https://openspeech.bytedance.com",
         "models": ["BV001_streaming", "seed-tts-2.0"]},
    ],
}

# 各 provider 的可选模型候选(新建时展示;对齐原版设置页展示)
MODEL_CHOICES: dict[str, list[str]] = {
    "minimax": ["MiniMax-M3", "MiniMax-M2.5", "MiniMax-M2.7", "MiniMax-M2.1", "MiniMax-H3"],
    "agnes": ["agnes-image-2.5-flash", "agnes-image-2.5", "agnes-image-2.1-flash", "agnes-video-2.5-flash", "agnes-video-2.5"],
    "volcengine": ["doubao-seedance-2-0", "doubao-seedance-2-0-fast", "doubao-seedance-2-0-mini", "doubao-seedream-4-0"],
    "aliyun": ["wan3.0-video", "wan3.0-video-prime"],
}


def list_configs(service_type: str | None = None) -> list:
    if service_type:
        return db.q("SELECT * FROM ai_service_configs WHERE service_type=? ORDER BY is_default DESC, priority DESC, id",
                    (service_type,))
    return db.q("SELECT * FROM ai_service_configs ORDER BY service_type, is_default DESC, id")


def add_config(service_type: str, provider: str, base_url: str, model: str,
               api_key: str = "", is_default: bool = False, remark: str = "") -> int:
    ts = db.now()
    if is_default:
        db.ex("UPDATE ai_service_configs SET is_default=0 WHERE service_type=?", (service_type,))
    return db.ex(
        "INSERT INTO ai_service_configs(service_type,provider,base_url,api_key,model,is_default,is_active,remark,created_at,updated_at)"
        " VALUES(?,?,?,?,?,?,1,?,?,?)",
        (service_type, provider, base_url, api_key, model, 1 if is_default else 0, remark, ts, ts))


def update_config(cid: int, **fields) -> None:
    sets, vals = [], []
    for k in ("provider", "base_url", "api_key", "model", "remark"):
        if k in fields and fields[k] is not None:
            sets.append(f"{k}=?"); vals.append(fields[k])
    if fields.get("is_default"):
        row = db.q1("SELECT service_type FROM ai_service_configs WHERE id=?", (cid,))
        if row:
            db.ex("UPDATE ai_service_configs SET is_default=0 WHERE service_type=?", (row["service_type"],))
        sets.append("is_default=1")
    if "is_active" in fields:
        sets.append("is_active=?"); vals.append(1 if fields["is_active"] else 0)
    if sets:
        vals += [db.now(), cid]
        db.ex(f"UPDATE ai_service_configs SET {','.join(sets)}, updated_at=? WHERE id=?", tuple(vals))


def delete_config(cid: int) -> None:
    db.ex("DELETE FROM ai_service_configs WHERE id=?", (cid,))


def default_config(service_type: str, config_id: int | None = None) -> dict | None:
    if config_id:
        row = db.q1("SELECT * FROM ai_service_configs WHERE id=? AND service_type=? AND is_active=1", (config_id, service_type))
        if row:
            return dict(row)
    row = db.q1("SELECT * FROM ai_service_configs WHERE service_type=? AND is_active=1 ORDER BY is_default DESC, priority DESC, id LIMIT 1",
                (service_type,))
    return dict(row) if row else None


def apply_yihao_key(api_key: str) -> list[str]:
    """易好快捷配置:一个 Key 写入文本/图片/视频三条推荐配置(对齐原版)。"""
    created: list[str] = []
    presets = [
        ("text", "minimax", "https://api.minimaxi.com/v1", "MiniMax-M3"),
        ("image", "agnes", "https://apihub.agnes-ai.com", "agnes-image-2.5-flash"),
        ("video", "agnes", "https://apihub.agnes-ai.com", "agnes-video-2.5-flash"),
    ]
    for st, provider, url, model in presets:
        row = db.q1("SELECT id FROM ai_service_configs WHERE service_type=? AND provider=?", (st, provider))
        if row:
            update_config(row["id"], api_key=api_key, model=model, base_url=url)
        else:
            add_config(st, provider, url, model, api_key=api_key, is_default=True)
        created.append(f"{st}:{provider}/{model}")
    return created


def seed_tts_default() -> None:
    if not (q_tts := db.q1("SELECT id FROM ai_service_configs WHERE service_type='tts'")):
        add_config("tts", "volcengine", "https://openspeech.bytedance.com", "BV001_streaming", remark="默认豆包语音")
