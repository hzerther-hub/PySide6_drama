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


# ── 垃圾分镜清理(对齐原版 StoryboardSplit junk-removed) ──
JUNK_DESC_MIN = 50
JUNK_IMAGE_MIN = 30
JUNK_VIDEO_MIN = 60


def clean_junk_storyboards(episode_id: int) -> int:
    """清理拆分中断留下的空壳分镜。

    模型偶发先写「占位清理A/B…」占位行再填充,中途截断就留下
    description<50 且 image_prompt<30 且 video_prompt<60 的空壳行(实测一次 6 行)。
    以**产物长度**判定,不匹配标题关键词。级联清 storyboard_characters/props。
    """
    removed = 0
    for sb in db.q("SELECT * FROM storyboards WHERE episode_id=?", (episode_id,)):
        desc = (sb["content"] or "").strip()
        img = (sb["image_prompt"] or "").strip()
        vid = (sb["video_prompt"] or "").strip()
        if len(desc) < JUNK_DESC_MIN and len(img) < JUNK_IMAGE_MIN and len(vid) < JUNK_VIDEO_MIN:
            db.ex("DELETE FROM storyboard_characters WHERE storyboard_id=?", (sb["id"],))
            db.ex("DELETE FROM storyboard_props WHERE storyboard_id=?", (sb["id"],))
            db.ex("DELETE FROM storyboards WHERE id=?", (sb["id"],))
            removed += 1
    return removed


def split_storyboards_bg(episode_id: int, aspect: str = "9:16", config_id: int | None = None,
                         lang: str | None = None):
    """后台分镜拆解(对齐原版 POST /storyboards/split-async)。

    拆解是 5-10 分钟的多步 Agent 调用,同步等待会被代理掐断;这里丢进任务队列,
    由 TaskManager 线程执行,UI 轮询 sys_task 状态。
    """
    ep = db.q1("SELECT * FROM episodes WHERE id=?", (episode_id,))
    if not ep:
        raise RuntimeError("章节不存在")
    if not (ep["script_content"] or "").strip():
        raise RuntimeError("本集还没有剧本,请先完成「AI 改写」")
    # 防重入:同集已有拆分任务在跑
    running = db.q1("""SELECT id FROM sys_task WHERE episode_id=? AND type='storyboard_split'
                       AND status='processing'""", (episode_id,))
    if running:
        raise RuntimeError("本集拆分已在进行中,请等它完成或在任务面板查看进度")

    from ..core import taskmgr as TM
    from ..core.taskmgr import TASKMGR

    def job(tid: int):
        TM.set_stage(tid, "splitting")
        try:
            n = split_storyboards(episode_id, aspect, config_id=config_id, lang=lang)
            removed = clean_junk_storyboards(episode_id)
            n = db.q1("SELECT COUNT(*) c FROM storyboards WHERE episode_id=?", (episode_id,))["c"]
            if n == 0:
                raise RuntimeError("拆分结束但没有写入任何分镜,请重试")
            msg = f"拆出 {n} 个分镜"
            if removed:
                msg += f"(已清理 {removed} 个残缺行)"
            TM.finish_task(tid, "completed", result_url=str(n), local_path=msg)
            return n
        except Exception as e:  # noqa: BLE001
            TM.finish_task(tid, "failed", error=str(e)[:500])
            raise

    return TASKMGR.submit("storyboard_split", job, episode_id=episode_id,
                          drama_id=ep["drama_id"])
