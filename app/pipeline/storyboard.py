# -*- coding: utf-8 -*-
"""阶段④:剧本 → 镜头级分镜(storyboard_breaker Agent)+ 批量视频提示词。"""
from __future__ import annotations

import re

from ..agents import runner
from ..core import db


def split_storyboards(episode_id: int, aspect: str = "9:16", config_id: int | None = None,
                    lang: str | None = None) -> int:
    """整集重新拆分分镜;返回数量。删除旧分镜(有视频的保留? 对齐原版:重拆=全量替换)。"""
    ep = db.q1("SELECT * FROM episodes WHERE id=?", (episode_id,))
    if not ep:
        raise RuntimeError("剧集不存在")
    script = ep["script_content"] or ""
    if not script.strip():
        raise RuntimeError("请先完成剧本改写")
    chars = db.q("SELECT name FROM characters WHERE drama_id=?", (ep["drama_id"],))
    assets = ", ".join(r["name"] for r in chars) or "无"
    prompt = f"""剧本(第 {ep['episode_number']} 集,画面比例 {aspect}):
{script[:14000]}

可用资产(@引用): {assets}"""
    data = runner.run_agent_json("storyboard_breaker", prompt, lang=lang, config_id=config_id)
    boards = data.get("storyboards") or (data if isinstance(data, list) else [])
    if not boards:
        raise RuntimeError("分镜结果为空")
    ts = db.now()
    db.ex("DELETE FROM storyboards WHERE episode_id=?", (episode_id,))
    for i, b in enumerate(boards, start=1):
        db.ex(
            "INSERT INTO storyboards(episode_id,storyboard_number,content,duration,video_prompt,status,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (episode_id, int(b.get("number") or i), b.get("content", ""),
             float(b.get("duration") or 8), b.get("video_prompt", ""), "pending", ts, ts))
    db.touch("episodes", episode_id)
    return len(boards)


def gen_video_prompts(episode_id: int, config_id: int | None = None, lang: str | None = None) -> int:
    """批量补齐/重写每镜 video_prompt(prompt_generator Agent);返回处理数。"""
    rows = db.q("SELECT * FROM storyboards WHERE episode_id=? ORDER BY storyboard_number", (episode_id,))
    if not rows:
        raise RuntimeError("请先「重新拆分」生成分镜")
    style = db.style_prompt(db.drama_style(db.q1("SELECT drama_id FROM episodes WHERE id=?", (episode_id,))["drama_id"]))
    done = 0
    for r in rows:
        prompt = f"""目标类型:storyboard(镜头视频提示词)
视觉风格前缀: {style}

分镜 #{r['storyboard_number']}:
{r['content'][:1500]}"""
        try:
            data = runner.run_agent_json("prompt_generator", prompt, lang=lang, config_id=config_id)
            vp = data.get("video_prompt") if isinstance(data, dict) else None
            if vp:
                db.ex("UPDATE storyboards SET video_prompt=?, updated_at=? WHERE id=?", (vp, db.now(), r["id"]))
                done += 1
        except Exception:  # noqa: BLE001
            continue
    return done
