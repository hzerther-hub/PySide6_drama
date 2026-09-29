# -*- coding: utf-8 -*-
"""Agent 执行器:组装 system + user,调用文本模型,解析 JSON 输出。"""
from __future__ import annotations

import json
import re

from ..ai import text_client
from ..core import db
from . import prompts


def extract_json(text: str) -> dict | list | None:
    """从模型输出中稳健提取 JSON(容忍 ```json 围栏与前后杂文)。"""
    if not text:
        return None
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    candidates = []
    if fence:
        candidates.append(fence.group(1).strip())
    # 直接整体
    candidates.append(text.strip())
    # 首个 { 到最后一个 }
    s, e = text.find("{"), text.rfind("}")
    if s >= 0 and e > s:
        candidates.append(text[s:e + 1])
    s2, e2 = text.find("["), text.rfind("]")
    if s2 >= 0 and e2 > s2:
        candidates.append(text[s2:e2 + 1])
    for cand in candidates:
        try:
            return json.loads(cand)
        except Exception:  # noqa: BLE001
            continue
    return None


def run_agent(agent_type: str, user_prompt: str, *, lang: str | None = None,
              json_output: bool = False, temperature: float = 0.7,
              config_id: int | None = None) -> str:
    if lang is None:
        lang = db.get_setting("content_language", "zh")
    system = prompts.load_prompt(agent_type, lang)
    return text_client.chat(
        user_prompt, system=system, temperature=temperature,
        json_mode=json_output, config_id=config_id)


def run_agent_json(agent_type: str, user_prompt: str, *, lang: str | None = None,
                   config_id: int | None = None) -> dict | list:
    """跑 Agent 并解析 JSON;解析失败时抛 RuntimeError(带原始输出片段)。"""
    raw = run_agent(agent_type, user_prompt, lang=lang, json_output=True,
                    temperature=0.4, config_id=config_id)
    data = extract_json(raw)
    if data is None:
        raise RuntimeError(f"{agent_type} 输出无法解析为 JSON:{raw[:300]}")
    return data
