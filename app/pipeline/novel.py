# -*- coding: utf-8 -*-
"""小说线:策划(novel_planner)→ 逐章生成(novel_writer)→ 六维审校(novel_reviewer)→ 改稿(novel_editor)。"""
from __future__ import annotations

import json

from ..agents import runner
from ..core import db


def plan_novel(drama_id: int, idea: str, config_id: int | None = None) -> dict:
    """开书策划:总纲/世界观/合约/卷战略/章节清单/主要角色,写入 dramas。"""
    prompt = f"新书创意:\n{idea[:6000]}\n\n请给出完整开书规划。"
    data = runner.run_agent_json("novel_planner", prompt, config_id=config_id)
    chapters = data.get("chapters", [])
    db.ex("""UPDATE dramas SET novel_outline=?, novel_world=?, novel_contract=?, novel_volume=?,
             novel_chapters=?, novel_meta=?, updated_at=? WHERE id=?""",
          (data.get("outline", ""), data.get("world", ""), data.get("contract", ""),
           json.dumps(data.get("volume", ""), ensure_ascii=False),
           json.dumps(chapters, ensure_ascii=False),
           json.dumps({"main_characters": data.get("main_characters", [])}, ensure_ascii=False),
           db.now(), drama_id))
    # 主要角色直接入资产库
    ts = db.now()
    for c in data.get("main_characters", []) or []:
        name = (c.get("name") or "").strip()
        if not name:
            continue
        if db.q1("SELECT id FROM characters WHERE drama_id=? AND name=?", (drama_id, name)):
            continue
        db.ex("INSERT INTO characters(drama_id,name,role_type,appearance,styling,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
              (drama_id, name, "lead" if c.get("role") in ("主角", "lead") else "supporting",
               c.get("appearance", ""), c.get("styling", ""), ts, ts))
    return data


def write_chapter(episode_id: int, config_id: int | None = None) -> str:
    """按章节计划写当前章正文(自动带前情+设定),写回 episodes.content。"""
    ep = db.q1("SELECT * FROM episodes WHERE id=?", (episode_id,))
    if not ep:
        raise RuntimeError("剧集(章)不存在")
    d = db.q1("SELECT * FROM dramas WHERE id=?", (ep["drama_id"],))
    chapters = db.jload(d["novel_chapters"], [])
    plan = next((c for c in chapters if int(c.get("number", 0)) == ep["episode_number"]), {})
    prev = db.q("SELECT episode_number, content FROM episodes WHERE drama_id=? AND episode_number<? ORDER BY episode_number DESC LIMIT 1",
                (ep["drama_id"], ep["episode_number"]))
    prev_summary = (prev[0]["content"] or "")[-800:] if prev else "(本章为第一章)"
    prompt = f"""小说设定:
总纲: {(d['novel_outline'] or '')[:600]}
世界观: {(d['novel_world'] or '')[:600]}
故事合约: {(d['novel_contract'] or '')[:400]}
本章计划: 第{ep['episode_number']}章 {plan.get('title','')} — 目标:{plan.get('goal','')} 事件:{plan.get('events','')} 钩子:{plan.get('cliffhanger','')}
文风: {db.get_setting('novel_style','爽感快节奏网文:短句为主,情绪外露,段落简短,冲突直给,爽点前置')}
目标字数: {ep['target_words'] or 2500}
上一章结尾(衔接用): {prev_summary}

请输出本章正文。"""
    content = runner.run_agent("novel_writer", prompt, config_id=config_id)
    db.ex("UPDATE episodes SET content=?, updated_at=? WHERE id=?", (content, db.now(), episode_id))
    return content


def write_chapter_with_review(episode_id: int, config_id: int | None = None) -> dict:
    """写章 → 六维审校 → 有问题带清单重写一轮(对齐原版 batch 修复循环)。"""
    content = write_chapter(episode_id, config_id=config_id)
    try:
        review = review_chapter(episode_id, config_id=config_id)
    except Exception:  # noqa: BLE001
        return {"content": content, "review": None, "fixed": False}
    if isinstance(review, dict) and review.get("overall") == "fix":
        issues = []
        for dim, v in (review.get("dimensions") or {}).items():
            if isinstance(v, dict) and not v.get("pass", True):
                issues.append(f"[{dim}] " + "; ".join(v.get("issues", [])[:3]))
        if issues:
            fix_prompt = "审校发现以下问题,请修复后输出完整修订正文:\n" + "\n".join(issues[:8]) \
                         + f"\n\n原正文:\n{content[:14000]}"
            fixed = runner.run_agent("novel_editor", fix_prompt, config_id=config_id)
            db.ex("UPDATE episodes SET content=?, updated_at=? WHERE id=?", (fixed, db.now(), episode_id))
            return {"content": fixed, "review": review, "fixed": True}
    return {"content": content, "review": review, "fixed": False}


def generate_cover(drama_id: int, config_id: int | None = None) -> str:
    from ..ai import image_client
    d = db.q1("SELECT * FROM dramas WHERE id=?", (drama_id,))
    if not d:
        raise RuntimeError("项目不存在")
    style = db.style_prompt(d["style"] or "3d")
    prompt = (f"{style}, 小说封面插图, 竖版海报构图, 核心场景与主角形象, "
              f"主题: {(d['novel_outline'] or d['title'])[:200]}, 电影质感, 无文字")
    out, _p = image_client.generate_image(prompt, out_name=f"cover_{drama_id}.png", config_id=config_id)
    url = config.path_to_media_url(out)
    db.ex("UPDATE dramas SET thumbnail=?, updated_at=? WHERE id=?", (url, db.now(), drama_id))
    return url


def save_plan(drama_id: int, outline: str, world: str, contract: str, volume: str) -> None:
    """策划面板手动保存四件套(章节清单经 novel_planner 重新生成)。"""
    db.ex("""UPDATE dramas SET novel_outline=?, novel_world=?, novel_contract=?, novel_volume=?, updated_at=? WHERE id=?""",
          (outline, world, contract, volume, db.now(), drama_id))


def review_chapter(episode_id: int, config_id: int | None = None) -> dict:
    """六维审校,结果存 episodes.review_json。"""
    ep = db.q1("SELECT * FROM episodes WHERE id=?", (episode_id,))
    if not ep or not (ep["content"] or "").strip():
        raise RuntimeError("本章还没有正文")
    prompt = f"第 {ep['episode_number']} 章正文:\n{(ep['content'] or '')[:15000]}"
    data = runner.run_agent_json("novel_reviewer", prompt, config_id=config_id)
    db.ex("UPDATE episodes SET review_json=?, updated_at=? WHERE id=?",
          (json.dumps(data, ensure_ascii=False), db.now(), episode_id))
    return data


def edit_chapter(episode_id: int, instruction: str, config_id: int | None = None) -> str:
    """按指令改写本章正文。"""
    ep = db.q1("SELECT * FROM episodes WHERE id=?", (episode_id,))
    if not ep or not (ep["content"] or "").strip():
        raise RuntimeError("本章还没有正文")
    prompt = f"修改指令: {instruction}\n\n正文:\n{ep['content'][:15000]}"
    content = runner.run_agent("novel_editor", prompt, config_id=config_id)
    db.ex("UPDATE episodes SET content=?, updated_at=? WHERE id=?", (content, db.now(), episode_id))
    return content


def export_book(drama_id: int, out_dir: str) -> str:
    """导出整本书目录结构(书名/第N章 标题.txt);返回根目录。"""
    from pathlib import Path
    d = db.q1("SELECT * FROM dramas WHERE id=?", (drama_id,))
    if not d:
        raise RuntimeError("项目不存在")
    root = Path(out_dir) / (d["title"].replace("/", "_")[:60])
    root.mkdir(parents=True, exist_ok=True)
    (root / "设定.md").write_text(
        f"# {d['title']}\n\n## 总纲\n{d['novel_outline'] or ''}\n\n## 世界观\n{d['novel_world'] or ''}\n\n## 故事合约\n{d['novel_contract'] or ''}\n",
        encoding="utf-8")
    chapters = db.jload(d["novel_chapters"], [])
    titles = {int(c.get("number", 0)): c.get("title", "") for c in chapters}
    for ep in db.q("SELECT * FROM episodes WHERE drama_id=? ORDER BY episode_number", (drama_id,)):
        title = titles.get(ep["episode_number"], ep["title"] or "")
        name = f"第{ep['episode_number']}章 {title}".strip().replace("/", "_")[:70]
        (root / f"{name}.txt").write_text(ep["content"] or "", encoding="utf-8")
    return str(root)
