# -*- coding: utf-8 -*-
"""阶段③配套:角色/场景/道具最终出图提示词(prompt_generator Agent)。"""
from __future__ import annotations

from ..agents import runner
from ..core import db


def _style_prefix(drama_id: int) -> str:
    return db.style_prompt(db.drama_style(drama_id))


def character_prompt(character_id: int, config_id: int | None = None, lang: str | None = None) -> str:
    c = db.q1("SELECT * FROM characters WHERE id=?", (character_id,))
    if not c:
        raise RuntimeError("角色不存在")
    prompt = f"""目标类型:character(角色三视图参考图)
视觉风格前缀: {_style_prefix(c['drama_id'])}

角色: {c['name']}({'主角' if c['role_type']=='lead' else '配角' if c['role_type']=='supporting' else '龙套'})
样貌: {c['appearance'] or '未提供'}
妆造: {c['styling'] or '未提供'}"""
    data = runner.run_agent_json("prompt_generator", prompt, lang=lang, config_id=config_id)
    fp = (data or {}).get("final_prompt", "")
    if not fp:
        raise RuntimeError("提示词生成失败")
    db.ex("UPDATE characters SET final_prompt=?, final_prompt_style=?, updated_at=? WHERE id=?",
          (fp, db.drama_style(c["drama_id"]), db.now(), character_id))
    return fp


def scene_prompt(scene_id: int, config_id: int | None = None, lang: str | None = None) -> str:
    s = db.q1("SELECT * FROM scenes WHERE id=?", (scene_id,))
    if not s:
        raise RuntimeError("场景不存在")
    prompt = f"""目标类型:scene(场景空镜建立图)
视觉风格前缀: {_style_prefix(s['drama_id'])}

场景: {s['name']}
位置: {s['location'] or ''}
时间: {s['time'] or ''}
环境: {s['prompt'] or ''}
光照: {s['lighting'] or ''}"""
    data = runner.run_agent_json("prompt_generator", prompt, lang=lang, config_id=config_id)
    fp = (data or {}).get("final_prompt", "")
    if not fp:
        raise RuntimeError("提示词生成失败")
    db.ex("UPDATE scenes SET final_prompt=?, updated_at=? WHERE id=?", (fp, db.now(), scene_id))
    return fp


def prop_prompt(prop_id: int, config_id: int | None = None, lang: str | None = None) -> str:
    p = db.q1("SELECT * FROM props WHERE id=?", (prop_id,))
    if not p:
        raise RuntimeError("道具不存在")
    prompt = f"""目标类型:prop(道具单品产品图)
视觉风格前缀: {_style_prefix(p['drama_id'])}

道具: {p['name']}({p['type'] or 'prop'})
描述: {p['description'] or ''}"""
    data = runner.run_agent_json("prompt_generator", prompt, lang=lang, config_id=config_id)
    fp = (data or {}).get("final_prompt", "")
    if not fp:
        raise RuntimeError("提示词生成失败")
    db.ex("UPDATE props SET final_prompt=?, updated_at=? WHERE id=?", (fp, db.now(), prop_id))
    return fp
