# -*- coding: utf-8 -*-
"""文本模型客户端:OpenAI 兼容 chat completions(覆盖 OpenAI/MiniMax/DeepSeek/Gemini-OpenAI 端点)。"""
from __future__ import annotations

import requests

from . import registry


class AIError(RuntimeError):
    pass


def chat(prompt: str, system: str | None = None, config_id: int | None = None,
         temperature: float = 0.7, max_tokens: int = 8192,
         json_mode: bool = False, timeout: int = 300) -> str:
    cfg = registry.check_ready("text", config_id)  # 未配置/缺 Key 直接拦下,不发空请求
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if cfg.get("api_key"):
        headers["Authorization"] = f"Bearer {cfg['api_key']}"
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    body: dict = {"model": cfg["model"], "messages": msgs,
                  "temperature": temperature, "max_tokens": max_tokens}
    # 配置级 Temperature(对齐原版:留空跟随服务默认;填写则强制覆盖,应对强制温度模型)
    cfg_temp = cfg.get("temperature")
    if cfg_temp is not None and cfg_temp != "":
        try:
            body["temperature"] = float(cfg_temp)
        except (TypeError, ValueError):
            pass
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    resp = requests.post(url, json=body, headers=headers, timeout=timeout)
    if resp.status_code != 200:
        raise AIError(f"文本模型请求失败 HTTP {resp.status_code}: {resp.text[:400]}")
    data = resp.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise AIError(f"文本模型响应格式异常: {data}") from e
    # 兼容部分中转站返回 reasoning + content 结构
    if isinstance(content, list):
        content = "".join(p.get("text", "") for p in content if isinstance(p, dict))
    return content or ""


def test_config(cfg: dict) -> tuple[bool, str]:
    try:
        url = cfg["base_url"].rstrip("/") + "/chat/completions"
        headers = {"Content-Type": "application/json"}
        if cfg.get("api_key"):
            headers["Authorization"] = f"Bearer {cfg['api_key']}"
        resp = requests.post(url, json={
            "model": cfg["model"], "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 8, "temperature": 0,
        }, headers=headers, timeout=30)
        if resp.status_code == 200:
            return True, "OK"
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:  # noqa: BLE001
        return False, str(e)
