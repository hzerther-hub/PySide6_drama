# -*- coding: utf-8 -*-
"""镜头级工具:首帧图生成 / 字幕烧录 / @角色参考图收集。

字幕/合成通过 ffmpeg 子进程完成(不向用户暴露技术细节)。
"""
from __future__ import annotations

import re
import subprocess
import uuid
from pathlib import Path

from ..ai import image_client, video_client
from ..core import config, db


def _ffmpeg() -> str:
    ff = config.find_ffmpeg()
    if not ff:
        raise RuntimeError("未找到 ffmpeg")
    return ff


def collect_reference_images(episode_id: int, text: str, limit: int = 4) -> list[str]:
    """从分镜文本中收集 @角色名 引用的角色形象图本地路径(去重,限 limit 张)。"""
    names = set(re.findall(r"@([\u4e00-\u9fa5A-Za-z0-9_·]+)", text or ""))
    if not names:
        return []
    refs: list[str] = []
    rows = db.q(
        f"SELECT c.name, c.image_url FROM characters c "
        f"JOIN episode_characters ec ON ec.character_id=c.id WHERE ec.episode_id=?", (episode_id,))
    for r in rows:
        if r["name"] in names and r["image_url"]:
            p = config.media_url_to_path(r["image_url"])
            if p.exists():
                refs.append(str(p))
        if len(refs) >= limit:
            break
    return refs


def generate_first_frame(episode_id: int, storyboard_id: int, config_id: int | None = None) -> str:
    """按分镜内容生成首帧图,写 storyboards.first_frame_image;返回 /static URL。"""
    sb = db.q1("SELECT * FROM storyboards WHERE id=?", (storyboard_id,))
    if not sb:
        raise RuntimeError("分镜不存在")
    ep = db.q1("SELECT drama_id FROM episodes WHERE id=?", (episode_id,))
    style = db.style_prompt(db.drama_style(ep["drama_id"]))
    prompt = f"{style}, {sb['video_prompt'] or sb['content'][:300]}, 电影质感"
    out, _p = image_client.generate_image(prompt, out_name=f"ff_{storyboard_id}.png", config_id=config_id)
    url = config.path_to_media_url(out)
    db.ex("UPDATE storyboards SET first_frame_image=?, updated_at=? WHERE id=?", (url, db.now(), storyboard_id))
    return url


def _extract_dialogue(text: str) -> str:
    lines = re.findall(r"「([^」]+)」|「([^」]+)」", text or "")
    merged = " / ".join(a or b for a, b in lines)[:220]
    return merged or (text or "")[:120]


def burn_subtitle(storyboard_id: int) -> str:
    """把旁白/台词作为字幕烧录进镜头视频,写 composed_video_url;返回 URL。"""
    sb = db.q1("SELECT * FROM storyboards WHERE id=?", (storyboard_id,))
    if not sb:
        raise RuntimeError("分镜不存在")
    src_url = sb["video_url"] or sb["composed_video_url"]
    if not src_url:
        raise RuntimeError("该镜头还没有视频")
    src = config.media_url_to_path(src_url)
    if not src.exists():
        raise RuntimeError("镜头视频文件不存在")
    sub_text = (sb["narration"] or "").strip() or _extract_dialogue(sb["content"])
    if not sub_text:
        raise RuntimeError("没有可用于字幕的文本(旁白/台词)")
    srt = config.STATIC_DIR / "videos" / f"srt_{uuid.uuid4().hex[:8]}.srt"
    srt.write_text(f"1\n00:00:00,200 --> 00:00:08,000\n{sub_text}\n", encoding="utf-8")
    out = config.STATIC_DIR / "videos" / f"sub_{uuid.uuid4().hex[:10]}.mp4"
    try:
        proc = subprocess.run(
            [_ffmpeg(), "-y", "-i", str(src),
             "-vf", f"subtitles={srt.as_posix()}:force_style='FontSize=14,Outline=1,MarginV=24'",
             "-c:a", "copy", str(out)],
            capture_output=True, text=True, timeout=600)
        if proc.returncode != 0:
            raise RuntimeError(f"字幕烧录失败: {proc.stderr[-300:]}")
    finally:
        srt.unlink(missing_ok=True)
    url = config.path_to_media_url(out)
    db.ex("UPDATE storyboards SET composed_video_url=?, updated_at=? WHERE id=?", (url, db.now(), storyboard_id))
    return url


def compose_from_image(episode_id: int, storyboard_id: int, resolution: str = "720p",
                       config_id: int | None = None) -> str:
    """图生视频:用首帧图生成镜头视频(无首帧则先生成),写 video_url。"""
    sb = db.q1("SELECT * FROM storyboards WHERE id=?", (storyboard_id,))
    if not sb:
        raise RuntimeError("分镜不存在")
    first = sb["first_frame_image"]
    if not first:
        generate_first_frame(episode_id, storyboard_id, config_id=config_id)
        sb = db.q1("SELECT * FROM storyboards WHERE id=?", (storyboard_id,))
        first = sb["first_frame_image"]
    refs = collect_reference_images(episode_id, sb["content"] or "")
    path, _provider = video_client.generate_video(
        (sb["video_prompt"] or sb["content"])[:1500], resolution=resolution,
        duration=int(sb["duration"] or 8),
        first_frame=config.media_url_to_path(first), reference_images=refs,
        config_id=config_id)
    db.ex("UPDATE storyboards SET video_url=?, status='completed', updated_at=? WHERE id=?",
          (config.path_to_media_url(path), db.now(), storyboard_id))
    return config.path_to_media_url(path)
