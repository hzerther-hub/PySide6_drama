# -*- coding: utf-8 -*-
"""同款复刻(video-clone-lite 逻辑):看懂原片 → 备新料 → 逐镜重拍 → 按原片节奏拼接。

数据落在 dramas.metadata.clone:* 与 sys_task(type=clone_*)。
"""
from __future__ import annotations

import json
import subprocess
import uuid
from pathlib import Path

from ..agents import runner
from ..ai import image_client, text_client, video_client
from ..core import config, db


def _meta(drama_id: int) -> dict:
    d = db.q1("SELECT metadata FROM dramas WHERE id=?", (drama_id,))
    return db.jload(d["metadata"], {}) if d else {}


def _save_meta(drama_id: int, meta: dict) -> None:
    db.ex("UPDATE dramas SET metadata=?, updated_at=? WHERE id=?",
          (json.dumps(meta, ensure_ascii=False), db.now(), drama_id))


def import_reference(drama_id: int, video_path: str | Path) -> dict:
    """导入参考视频(拷入 data/static/uploads),记录元数据。"""
    src = Path(video_path)
    dst = config.STATIC_DIR / "uploads" / f"ref_{uuid.uuid4().hex[:10]}{src.suffix or '.mp4'}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
    meta = _meta(drama_id)
    meta["clone"] = {**meta.get("clone", {}), "reference": str(dst)}
    _save_meta(drama_id, meta)
    return {"path": str(dst), "size": dst.stat().st_size}


def upload_material(drama_id: int, kind: str, image_path: str | Path) -> str:
    """上传素材:kind = product(产品图,必须)/ presenter(出镜人照片,可选)。"""
    src = Path(image_path)
    dst = config.STATIC_DIR / "uploads" / f"{kind}_{uuid.uuid4().hex[:10]}{src.suffix or '.png'}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
    meta = _meta(drama_id)
    clone = meta.get("clone", {})
    clone[kind] = str(dst)
    meta["clone"] = clone
    _save_meta(drama_id, meta)
    return str(dst)


def extract_frames(video_path: str | Path, count: int = 8) -> list[Path]:
    """ffmpeg 均匀抽帧(供视觉模型理解原片)。"""
    ff = config.find_ffmpeg()
    if not ff:
        raise RuntimeError("未找到 ffmpeg")
    out_dir = config.STATIC_DIR / "uploads" / f"frames_{uuid.uuid4().hex[:8]}"
    out_dir.mkdir(parents=True, exist_ok=True)
    fps_expr = f"{count}/{_duration(video_path) or 15:.2f}"
    subprocess.run([ff, "-y", "-i", str(video_path), "-vf",
                    f"fps={fps_expr},scale=640:-2",
                    "-frames:v", str(count), str(out_dir / "f%02d.jpg")],
                   capture_output=True, timeout=180)
    frames = sorted(out_dir.glob("f*.jpg"))
    if not frames:
        raise RuntimeError("抽帧失败,请检查视频文件")
    return frames


def _duration(video_path: str | Path) -> float:
    fp = config.find_ffprobe()
    if not fp:
        return 0.0
    out = subprocess.run([fp, "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(video_path)], capture_output=True, text=True, timeout=30)
    try:
        return float(out.stdout.strip())
    except Exception:  # noqa: BLE001
        return 0.0


def _image_data_url(path: str | Path, mime: str = "image/jpeg") -> str:
    import base64
    return f"data:{mime};base64," + base64.b64encode(Path(path).read_bytes()).decode()


def read_product_desc(product_path: str | Path, config_id: int | None = None) -> str | None:
    """多模态读产品图,产出注入生成提示词的产品描述(供 clone.product_desc 落库)。

    独立于分镜分析的小调用:图与视频帧不混传,避免干扰分镜判断;失败返回 None。
    """
    p = Path(product_path)
    if not p.exists():
        return None
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    prompt = """这张图片是带货视频要推广的产品照片。请识别并输出一段用于文生图/文生视频提示词的产品描述:
- 产品类别与形态(如"圆柱形保温杯")
- 颜色与材质质感
- 1-3 个最有辨识度的外观细节
- 适合画面呈现的一句话使用场景
只输出 JSON:{"product_desc": "一句话中文描述(60字内),串起上述要点,不含品牌名"}"""
    raw = text_client.chat(prompt, temperature=0.3, max_tokens=512, json_mode=True,
                           config_id=config_id, image_urls=[_image_data_url(p, mime)])
    data = runner.extract_json(raw)
    if isinstance(data, dict):
        desc = str(data.get("product_desc") or "").strip()
        return desc or None
    return None


def analyze_reference(drama_id: int, extra_hint: str = "", config_id: int | None = None) -> list[dict]:
    """第 1 步:看懂原片。抽帧 + 时长 → 多模态文本模型(如 MiniMax-M3)看图输出分镜表 JSON。

    有产品图时顺带读图写 clone.product_desc(下步生镜图提示词用;失败不阻塞分镜分析)。
    分镜表每镜:{number, start, end, shot(景别), camera(运镜), action(动作概述),
    action_steps(连续动作时序数组), line(台词/字幕), product_use(产品如何出现), prompt(重拍视频提示词)}
    """
    meta = _meta(drama_id)
    clone = meta.get("clone", {})
    ref = clone.get("reference")
    if not ref:
        raise RuntimeError("请先导入参考视频")
    frames = extract_frames(ref, count=8)
    dur = _duration(ref)
    image_urls = [_image_data_url(f) for f in frames]
    frame_desc = "\n".join(
        f"第{i}帧(约 {dur * i / (len(frames) + 1):.1f} 秒处)"
        for i, _ in enumerate(frames, 1))
    prompt = f"""下面是一条待复刻的带货/种草类视频,已按时间均匀抽出 {len(frames)} 帧随消息附上(顺序对应):
总时长: {dur:.1f} 秒
{frame_desc}
{('补充说明: ' + extra_hint) if extra_hint else ''}

请逐帧仔细看图,推断该视频的完整分镜表(8 秒上下每镜,共 2-6 镜):
- 每帧识别:场景、人物与景别(远/全/中/近/特)、人物动作、出现的商品及其使用方式、画面字幕或口播要点
- 相邻两帧画面差异明显即发生了镜头切换,据此划分镜头边界与起止时间
每镜输出:
- number, start, end, shot(景别), camera(运镜:固定/推/拉/摇/移/跟/升降等,选一词)
- action(一句话动作概述), action_steps(连续动作时序数组,2-5 步,每步一句按时间先后排列的可见动作)
- line(推测台词/字幕), product_use(产品如何出现)
- prompt(给文生视频模型的重拍提示词:主体+动作+运镜+光线+氛围,不写人名)
以 JSON 输出:{{"storyboards":[...]}}"""
    data = runner.run_agent_json("storyboard_breaker", prompt, config_id=config_id,
                                 image_urls=image_urls)
    boards = data.get("storyboards") or (data if isinstance(data, list) else [])
    if not boards:
        raise RuntimeError("分镜表生成失败")
    clone["storyboards"] = boards
    product = clone.get("product")
    if product:
        try:
            desc = read_product_desc(product, config_id=config_id)
            if desc:
                clone["product_desc"] = desc
        except Exception:  # noqa: BLE001
            pass  # 可选步骤:读产品图失败不阻塞分镜分析
    meta["clone"] = clone
    _save_meta(drama_id, meta)
    return boards


def prepare_presenter(drama_id: int, style_value: str, config_id: int | None = None) -> str:
    """第 2 步(可选):无出镜照片时,AI 生成一位与目标市场匹配的模特形象图。"""
    meta = _meta(drama_id)
    clone = meta.get("clone", {})
    prompt_prefix = db.style_prompt(style_value)
    prompt = (f"{prompt_prefix}, 单人全身模特形象参考图,正面站姿,纯白背景,柔和影棚光, "
              "人物形象干净亲和,适合带货出镜, 电影质感")
    out, _ = image_client.generate_image(prompt, out_name=f"clone_presenter_{drama_id}.png", config_id=config_id)
    clone["presenter"] = str(out)
    meta["clone"] = clone
    _save_meta(drama_id, meta)
    return str(out)


def _clone_storyboards(drama_id: int) -> list[dict]:
    return _meta(drama_id).get("clone", {}).get("storyboards", [])


def _resolve_local(p) -> Path | None:
    """素材字段可能是本地绝对路径或 /static/ 媒体地址,统一转本地路径;不存在返回 None。"""
    s = str(p).replace("\\", "/")
    path = config.media_url_to_path(s) if s.startswith(("/static/", "static/")) else Path(p)
    return path if path.exists() else None


def _shot_video_prompt(b: dict) -> str:
    """重拍视频提示词:显式 prompt 字段优先作主体;缺失时按原版 videoPrompt 口径合成
    (景别+运镜+动作时序);有台词时追加口型同步标注。"""
    steps = [str(s).strip() for s in (b.get("action_steps") or []) if str(s).strip()]
    cam = str(b.get("camera") or "").strip()
    line = str(b.get("line") or "").strip()
    body = str(b.get("prompt") or "").strip()
    if not body:
        body = "，".join(filter(None, (str(b.get("shot") or ""), cam,
                                       "，".join(steps) or str(b.get("action") or ""))))
    elif steps:
        body = f"{body}，动作按 {'，'.join(steps)} 的时序推进"
    if line:
        body = f"{body}。台词（口型同步）：{line}"
    return body


def generate_shot_image(drama_id: int, board_number: int, style_value: str,
                        config_id: int | None = None) -> Path:
    """第 3 步 a:按分镜表生成该镜首帧图(注入产品/模特形象描述)。

    有产品图/模特形象图时作为参考图注入(agnes extra_body.image):人物锁脸、产品保外观,
    提示词附一致性约束;无图退回纯文生图。
    """
    boards = _clone_storyboards(drama_id)
    b = next((x for x in boards if int(x.get("number", 0)) == int(board_number)), None)
    if not b:
        raise RuntimeError(f"分镜 #{board_number} 不存在,请先分析参考视频")
    meta = _meta(drama_id)
    clone = meta.get("clone", {})
    style = db.style_prompt(style_value)
    product_desc = clone.get("product_desc") or "用户产品(见产品图)"
    presenter_desc = clone.get("presenter_desc") or "亲和力强的出镜人物(见模特形象)"
    # 参考图注入:模特形象在前(锁脸),产品图在后(保外观)
    refs = [p for p in (_resolve_local(clone.get(k)) for k in ("presenter", "product")) if p]
    consist = (", 人物长相与服装必须与参考图中的模特完全一致, 产品外观细节必须与参考图中的产品完全一致"
               if refs else "")
    # 静帧取动作时序串(姿态更具体),无时序退回动作概述
    steps = [str(s).strip() for s in (b.get("action_steps") or []) if str(s).strip()]
    action_txt = "，".join(steps) if steps else str(b.get("action") or "展示产品")
    prompt = (f"{style}, {b.get('shot','中景')}, {presenter_desc} 正在 {action_txt}, "
              f"画面突出 {product_desc}: {b.get('product_use','')}{consist}, "
              f"运镜与光线参考带货实拍视频,清晰锐利, 电影质感")
    out, _ = image_client.generate_image(prompt, out_name=f"clone_s{board_number}_{uuid.uuid4().hex[:6]}.png",
                                         config_id=config_id, reference_images=refs)
    # 记录首帧
    for x in boards:
        if int(x.get("number", 0)) == int(board_number):
            x["first_frame"] = str(out)
    clone["storyboards"] = boards
    meta["clone"] = clone
    _save_meta(drama_id, meta)
    return out


def generate_shot_video(drama_id: int, board_number: int, resolution: str = "720p",
                        config_id: int | None = None) -> Path:
    """第 3 步 b:图生视频(首帧=上一步生成的镜头图)。"""
    boards = _clone_storyboards(drama_id)
    b = next((x for x in boards if int(x.get("number", 0)) == int(board_number)), None)
    if not b:
        raise RuntimeError(f"分镜 #{board_number} 不存在")
    first = b.get("first_frame")
    if not first:
        raise RuntimeError(f"分镜 #{board_number} 还没有首帧图,请先生成镜头图")
    dur = max(4, min(12, int(float(b.get("end", 8)) - float(b.get("start", 0))) or 8))
    path, _ = video_client.generate_video(
        _shot_video_prompt(b), resolution=resolution,
        duration=dur, first_frame=first, config_id=config_id)
    for x in boards:
        if int(x.get("number", 0)) == int(board_number):
            x["video"] = str(path)
    meta = _meta(drama_id)
    clone = meta.get("clone", {})
    clone["storyboards"] = boards
    meta["clone"] = clone
    _save_meta(drama_id, meta)
    return path


def clone_done_videos(drama_id: int) -> list[Path]:
    return [Path(x["video"]) for x in _clone_storyboards(drama_id) if x.get("video")]


def merge_clone(drama_id: int, out: str | Path | None = None, progress=None) -> Path:
    """第 4 步:按原片节奏无损拼接成片(复用 easymerger auto_merge)。"""
    from . import merge as merge_mod
    files = [str(p) for p in clone_done_videos(drama_id) if p.exists()]
    if len(files) < 2:
        raise RuntimeError("至少完成 2 个镜头视频才能拼接")
    out = out or (config.STATIC_DIR / "merged" / f"clone_{drama_id}_{uuid.uuid4().hex[:8]}.mp4")
    path, _channel = merge_mod.auto_merge(files, out, progress=progress)
    return path
