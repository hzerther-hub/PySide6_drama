# -*- coding: utf-8 -*-
"""阶段③:从剧本提取角色/场景/道具并去重(extractor Agent),写库+关联本集。"""
from __future__ import annotations

import json

from ..agents import runner
from ..core import db

ROLE_MAP = {"lead": "lead", "supporting": "supporting", "extra": "extra",
            "主角": "lead", "配角": "supporting", "龙套": "extra"}


def extract_assets(episode_id: int, config_id: int | None = None, lang: str | None = None) -> dict:
    """提取并入库;返回统计。与项目已有资产按名字去重(同名更新描述,否则新增)。"""
    ep = db.q1("SELECT * FROM episodes WHERE id=?", (episode_id,))
    if not ep:
        raise RuntimeError("剧集不存在")
    drama_id = ep["drama_id"]
    script = ep["script_content"] or ep["content"] or ""
    if not script.strip():
        raise RuntimeError("请先完成剧本(原始内容 / AI 改写)")

    existing = {
        "characters": [r["name"] for r in db.q("SELECT name FROM characters WHERE drama_id=?", (drama_id,))],
        "scenes": [r["name"] for r in db.q("SELECT name FROM scenes WHERE drama_id=?", (drama_id,))],
        "props": [r["name"] for r in db.q("SELECT name FROM props WHERE drama_id=?", (drama_id,))],
    }
    prompt = f"""剧本(第 {ep['episode_number']} 集):
{script[:12000]}

项目已有资产(不要重复提取):
角色: {', '.join(existing['characters']) or '无'}
场景: {', '.join(existing['scenes']) or '无'}
道具: {', '.join(existing['props']) or '无'}"""
    data = runner.run_agent_json("extractor", prompt, lang=lang, config_id=config_id)
    ts = db.now()
    stat = {"characters": 0, "scenes": 0, "props": 0}

    for c in data.get("characters", []) or []:
        name = (c.get("name") or "").strip()
        if not name or name in existing["characters"]:
            continue
        cid = db.ex(
            "INSERT INTO characters(drama_id,name,role_type,appearance,styling,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
            (drama_id, name, ROLE_MAP.get(c.get("role_type", "supporting"), "supporting"),
             c.get("appearance", ""), c.get("styling", ""), ts, ts))
        db.ex("INSERT OR IGNORE INTO episode_characters(episode_id,character_id) VALUES(?,?)", (episode_id, cid))
        stat["characters"] += 1

    for s in data.get("scenes", []) or []:
        name = (s.get("name") or "").strip()
        if not name or name in existing["scenes"]:
            continue
        sid = db.ex(
            "INSERT INTO scenes(drama_id,episode_id,name,location,time,prompt,lighting,setting_tags,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?)",
            (drama_id, episode_id, name, s.get("location", ""), s.get("time", ""),
             s.get("prompt", ""), s.get("lighting", ""),
             json.dumps(s.get("setting_tags", []), ensure_ascii=False), ts, ts))
        db.ex("INSERT OR IGNORE INTO episode_scenes(episode_id,scene_id) VALUES(?,?)", (episode_id, sid))
        stat["scenes"] += 1

    for p in data.get("props", []) or []:
        name = (p.get("name") or "").strip()
        if not name or name in existing["props"]:
            continue
        pid = db.ex(
            "INSERT INTO props(drama_id,name,type,description,created_at,updated_at) VALUES(?,?,?,?,?,?)",
            (drama_id, name, p.get("type", "prop"), p.get("description", ""), ts, ts))
        db.ex("INSERT OR IGNORE INTO episode_props(episode_id,prop_id) VALUES(?,?)", (episode_id, pid))
        stat["props"] += 1

    db.touch("episodes", episode_id)
    return stat
