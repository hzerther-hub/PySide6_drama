# -*- coding: utf-8 -*-
"""阶段⑤:剧本 → 漫画格(comic_board Agent)+ 旁白补齐 + 长条图拼接。"""
from __future__ import annotations

from ..agents import runner
from ..core import db


def split_panels(episode_id: int, config_id: int | None = None, lang: str | None = None) -> int:
    """整集重新生成漫画分镜格;返回格数。"""
    ep = db.q1("SELECT * FROM episodes WHERE id=?", (episode_id,))
    if not ep:
        raise RuntimeError("剧集不存在")
    script = ep["script_content"] or ep["content"] or ""
    if not script.strip():
        raise RuntimeError("请先完成剧本")
    prompt = f"剧本(第 {ep['episode_number']} 集):\n{script[:14000]}"
    data = runner.run_agent_json("comic_board", prompt, lang=lang, config_id=config_id)
    panels = data.get("panels") or (data if isinstance(data, list) else [])
    if not panels:
        raise RuntimeError("漫画分镜结果为空")
    ts = db.now()
    db.ex("DELETE FROM comic_panels WHERE episode_id=?", (episode_id,))
    for i, p in enumerate(panels, start=1):
        db.ex(
            "INSERT INTO comic_panels(episode_id,panel_number,description,dialogue,composition,narration,image_prompt,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?,?)",
            (episode_id, int(p.get("number") or i), p.get("description", ""), p.get("dialogue", "无"),
             p.get("composition", ""), p.get("narration", ""), "", ts, ts))
    db.touch("episodes", episode_id)
    return len(panels)


def panel_image_prompt(panel_id: int, drama_id: int, config_id: int | None = None) -> str:
    """单格出图提示词:画面+构图+对白气泡说明,注入项目风格前缀。"""
    p = db.q1("SELECT * FROM comic_panels WHERE id=?", (panel_id,))
    if not p:
        raise RuntimeError("漫画格不存在")
    style = db.style_prompt(db.drama_style(drama_id))
    prompt = f"""目标类型:comic_panel(条漫单格画面,画幅竖版)
视觉风格前缀: {style}

画面: {p['description']}
构图: {p['composition']}
台词(画面内以对话气泡呈现): {p['dialogue']}"""
    data = runner.run_agent_json("prompt_generator", prompt, config_id=config_id)
    fp = (data or {}).get("final_prompt", "")
    if fp:
        db.ex("UPDATE comic_panels SET image_prompt=?, updated_at=? WHERE id=?", (fp, db.now(), panel_id))
    return fp


def comic_asset_image(drama_id: int, kind: str, row_id: int, config_id: int | None = None) -> str:
    """资产行的漫画风格镜像图(角色/场景/道具),写 comic_image_url;返回 URL。"""
    from ..ai import image_client
    table = {"character": "characters", "scene": "scenes", "prop": "props"}[kind]
    row = db.q1(f"SELECT * FROM {table} WHERE id=?", (row_id,))
    if not row:
        raise RuntimeError("资产不存在")
    d = db.q1("SELECT comic_style, style FROM dramas WHERE id=?", (drama_id,))
    style = db.style_prompt(d["comic_style"] or d["style"] or "3d")
    if kind == "character":
        spec = f"角色三视图参考图(左正脸特写+正/侧/背三张全身), 角色: {row['name']}, 样貌: {row['appearance'] or ''}, 服装: {row['styling'] or ''}"
    elif kind == "scene":
        spec = f"场景空镜建立图(三层构图,无人物), 场景: {row['name']}, 环境: {row['prompt'] or ''}, 光照: {row['lighting'] or ''}"
    else:
        spec = f"道具单品图(纯白背景), 道具: {row['name']}, 描述: {row['description'] or ''}"
    prompt = f"{style}, {spec}, 电影质感"
    out, _p = image_client.generate_image(prompt, config_id=config_id)
    url = config.path_to_media_url(out)
    db.ex(f"UPDATE {table} SET comic_image_url=?, updated_at=? WHERE id=?", (url, db.now(), row_id))
    return url
