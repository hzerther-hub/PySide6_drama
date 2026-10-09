# -*- coding: utf-8 -*-
"""阶段④:剧本 → 镜头级分镜(storyboard_breaker Agent)+ 批量视频提示词。"""
from __future__ import annotations

import json
import re

from ..agents import runner
from ..core import db


def split_storyboards(episode_id: int, aspect: str = "9:16", config_id: int | None = None,
                    lang: str | None = None) -> int:
    """整集重新拆分分镜;返回数量(对齐原版 save_storyboards:全量替换 + 资产绑定)。

    与原版对齐的关键点:
    - 落库 **全字段**(title/shot_type/angle/movement/location/time/description/result/
      atmosphere/image_prompt/video_prompt/bgm_prompt/sound_effect/scene_id/setting_tags/duration);
      setting_tags 为空时从场景继承 —— 缺这些字段时 `refs.build_shot_reference_list`
      拿不到绑定、reference injection 就是空的,生图只能每次现调 Agent。
    - 同步写 `storyboard_characters`(带 variant_id)与 `storyboard_props`;
    - 按 shot_number **幂等 upsert**(重拆不丢已生成的视频/首帧);
    - 重算 `episodes.duration = ceil(Σ分镜时长 / 60)`。
    """
    ep = db.q1("SELECT * FROM episodes WHERE id=?", (episode_id,))
    if not ep:
        raise RuntimeError("剧集不存在")
    script = ep["script_content"] or ""
    if not script.strip():
        raise RuntimeError("请先完成剧本改写")
    chars = db.q("SELECT id, name FROM characters WHERE drama_id=?", (ep["drama_id"],))
    scenes = db.q("SELECT id, name, setting_tags FROM scenes WHERE drama_id=?", (ep["drama_id"],))
    props = db.q("SELECT id, name FROM props WHERE drama_id=?", (ep["drama_id"],))
    assets = ", ".join(r["name"] for r in chars) or "无"
    prompt = f"""剧本(第 {ep['episode_number']} 集,画面比例 {aspect}):
{script[:14000]}

可用资产(@引用): {assets}"""
    prompt += ("\n\n请输出 JSON 对象:"
               '{"storyboards":[…]};每镜字段 '
               'number/title/content/shot_type/angle/movement/location/time/description/'
               'atmosphere/result/image_prompt/video_prompt/bgm_prompt/sound_effect/'
               'setting_tags(数组)/characters(角色名数组)/props(道具名数组)')
    data = runner.run_agent_json("storyboard_breaker", prompt, lang=lang, config_id=config_id)
    boards = _extract_boards(data)
    if not boards:
        raise RuntimeError("分镜结果为空")
    ts = db.now()
    name_to_id = {r["name"]: r["id"] for r in chars}
    scene_by_name = {r["name"]: dict(r) for r in scenes}
    prop_by_id = {r["id"]: r["name"] for r in props}
    prop_names = [r["name"] for r in props]
    _clear_episode_bindings(episode_id)
    total_dur = 0.0
    for i, b in enumerate(boards, start=1):
        num = int(b.get("number") or i)
        scene_id = _match_scene(b, scene_by_name)
        inherit = (scene_by_name.get(b.get("location") or "", {}) or {}).get("setting_tags")
        tags = b.get("setting_tags") or inherit
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.replace("、", ",").split(",") if t.strip()]
        dur = float(b.get("duration") or 10)
        total_dur += dur
        # 幂等 upsert:已存在的镜头保留生成物(视频/首帧/字幕),只更新描述类字段
        existing = db.q1("SELECT id FROM storyboards WHERE episode_id=? AND storyboard_number=?",
                         (episode_id, num))
        vals = (str(b.get("title") or b.get("content") or "")[:120],
                b.get("shot_type") or b.get("shot_size"), b.get("angle"), b.get("movement"),
                b.get("location"), b.get("time"), b.get("description"),
                b.get("result"), b.get("atmosphere"), b.get("image_prompt"),
                b.get("video_prompt"), b.get("bgm_prompt"), b.get("sound_effect"),
                scene_id, json.dumps(tags, ensure_ascii=False) if tags else None,
                b.get("content", ""), dur)
        if existing:
            db.ex("""UPDATE storyboards SET title=?, shot_type=?, angle=?, movement=?, location=?,
                      time=?, description=?, result=?, atmosphere=?, image_prompt=?, video_prompt=?,
                      bgm_prompt=?, sound_effect=?, scene_id=?, setting_tags=?, content=?, duration=?,
                      updated_at=? WHERE id=?""", vals + (ts, existing["id"]))
            sb_id = existing["id"]
        else:
            sb_id = db.ex(
                """INSERT INTO storyboards(episode_id,storyboard_number,title,shot_type,angle,
                   movement,location,time,description,result,atmosphere,image_prompt,video_prompt,
                   bgm_prompt,sound_effect,scene_id,setting_tags,content,duration,status,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'pending',?,?)""",
                (episode_id, num) + vals + (ts, ts))
        _bind_assets(sb_id, b, name_to_id, prop_by_id, prop_names, ts)
    db.ex("UPDATE episodes SET duration=?, updated_at=? WHERE id=?",
          (max(1, round(total_dur / 60)), ts, episode_id))
    db.touch("episodes", episode_id)
    return len(boards)


def _extract_boards(data) -> list:
    """兼容三种返回形态:{"storyboards":[…]} / {"boards":[…]} / 裸数组。"""
    if isinstance(data, list):
        return [b for b in data if isinstance(b, dict)]
    if isinstance(data, dict):
        for key in ("storyboards", "boards", "shots", "items"):
            v = data.get(key)
            if isinstance(v, list) and v:
                return [b for b in v if isinstance(b, dict)]
        # 兜底:形如 {"1": {...}, "2": {...}} 的字典
        vals = [v for v in data.values() if isinstance(v, dict)]
        if vals and all("content" in v or "video_prompt" in v for v in vals):
            return vals
    return []


def _clear_episode_bindings(episode_id: int) -> None:
    """重拆前清掉本集分镜的资产绑定(分镜本身由 upsert 处理,不删以免丢生成物)。"""
    db.ex("DELETE FROM storyboard_characters WHERE storyboard_id IN "
          "(SELECT id FROM storyboards WHERE episode_id=?)", (episode_id,))
    db.ex("DELETE FROM storyboard_props WHERE storyboard_id IN "
          "(SELECT id FROM storyboards WHERE episode_id=?)", (episode_id,))


def _match_scene(b: dict, scene_by_name: dict) -> int | None:
    """按 location / scene 字段匹配场景;匹配不到留空(原版同样允许 unbound)。"""
    for key in ("scene", "location"):
        v = (b.get(key) or "").strip()
        if v and v in scene_by_name:
            return scene_by_name[v]["id"]
    for name in scene_by_name:
        if name and name in (b.get("content") or ""):
            return scene_by_name[name]["id"]
    return None


def _bind_assets(sb_id: int, b: dict, name_to_id: dict, prop_by_id: dict,
                 prop_names: list, ts: str) -> None:
    """把本镜出现的 @角色 / @道具 绑定到分镜(对齐 syncStoryboardCharacters/Props)。

    兼容两种形态:`characters: ["叶尘"]` 与 `char_ids: [3]`(模型有时直接给 id)。
    """
    names = _refs_to_names(b, "characters", name_to_id, prop_by_id)
    for name, cid, vid in names:
        db.ex("INSERT OR IGNORE INTO storyboard_characters(storyboard_id,character_id,variant_id) "
              "VALUES(?,?,?)", (sb_id, cid, vid))
    for _name, pid, _vid in _refs_to_names(b, "props", prop_by_id, prop_by_id):
        db.ex("INSERT OR IGNORE INTO storyboard_props(storyboard_id,prop_id) VALUES(?,?)",
              (sb_id, pid))


def _refs_to_names(b: dict, key: str, id_by_name: dict, prop_by_id: dict) -> list:
    """把 characters/props 引用统一成 (名字, id, variant_id);兼容名字数组与 id 数组。"""
    out: list = []
    id_key = "char_ids" if key == "characters" else "prop_ids"
    for cid in b.get(id_key) or []:
        try:
            row = db.q1("SELECT id, name FROM characters WHERE id=?" if key == "characters"
                        else "SELECT id, name FROM props WHERE id=?", (int(cid),))
        except (TypeError, ValueError):
            row = None
        if row:
            out.append((row["name"], row["id"], None))
    for ref in b.get(key) or []:
        name = (ref.get("name") if isinstance(ref, dict) else str(ref)) or ""
        name = name.lstrip("@").strip()
        cid = id_by_name.get(name)
        if cid:
            vid = (ref.get("variant_id") if isinstance(ref, dict) else None)
            out.append((name, cid, vid))
    return out
    # 兜底:正文里出现的资产名也算绑定(Agent 漏给 characters 数组时)
    text = b.get("content") or ""
    for name, cid in name_to_id.items():
        if cid and name in text and "@" + name in text:
            db.ex("INSERT OR IGNORE INTO storyboard_characters(storyboard_id,character_id) "
                  "VALUES(?,?)", (sb_id, cid))
    for i, name in enumerate(prop_names):
        if name and "@" + name in text:
            db.ex("INSERT OR IGNORE INTO storyboard_props(storyboard_id,prop_id) VALUES(?,?)",
                  (sb_id, prop_by_id[name]))

def gen_video_prompts(episode_id: int, config_id: int | None = None, lang: str | None = None) -> int:
    """批量补齐缺失的每镜 video_prompt(prompt_generator Agent);返回处理数。

    对齐原版:只处理 `video_prompt` 为空的镜头(已有的不覆盖),按镜头号顺序逐条生成。
    """
    rows = db.q("""SELECT * FROM storyboards WHERE episode_id=?
                   AND (video_prompt IS NULL OR video_prompt='') ORDER BY storyboard_number""",
                (episode_id,))
    if not rows:
        rows = db.q("SELECT * FROM storyboards WHERE episode_id=? ORDER BY storyboard_number",
                    (episode_id,))
        if not rows:
            raise RuntimeError("请先「重新拆分」生成分镜")
    from .comic import _style_for
    drama_id = db.q1("SELECT drama_id FROM episodes WHERE id=?", (episode_id,))["drama_id"]
    style = _style_for(drama_id)
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
