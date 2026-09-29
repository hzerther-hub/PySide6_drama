# -*- coding: utf-8 -*-
"""视频合并模块 —— 并入 golanse/easymerger 核心逻辑:

  能用无损合并就绝不用转码。

通道策略:
  A) 全部参数一致          → concat demuxer + `-c copy`(秒合,零损失)
  B) 视频参数一致、音频不一致 → 智能直通:视频流 copy,仅统一音频(aac 48k 立体声)
  C) 少数视频异类           → 一键对齐异类:只转码那几个到多数派参数,再走 A

参数检测(ffprobe):分辨率/编码/Profile/等级/帧率/像素格式/音频编码/音频Profile/采样率/声道。
容错回退:直通失败 → 换中间容器(.ts/.mov) → 重编码救回。
同时提供剧集拼接入口(镜头视频 + 旁白 MP3 amix 混音,对齐原版 ffmpeg-merge)。
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from ..core import config, db

VIDEO_KEYS = ["width", "height", "vcodec", "vprofile", "fps", "pix_fmt"]
AUDIO_KEYS = ["acodec", "aprofile", "sample_rate", "channels"]
ALL_KEYS = VIDEO_KEYS + AUDIO_KEYS


def _ffmpeg() -> str:
    ff = config.find_ffmpeg()
    if not ff:
        raise RuntimeError("未找到 ffmpeg,请安装或设置 FFMPEG_BIN 环境变量。")
    return ff


def _ffprobe() -> str:
    fp = config.find_ffprobe()
    if not fp:
        raise RuntimeError("未找到 ffprobe,请安装或设置 FFPROBE_BIN 环境变量。")
    return fp


def probe(path: str | Path) -> dict:
    """ffprobe 提取统一参数指纹。失败抛 RuntimeError。"""
    out = subprocess.run(
        [_ffprobe(), "-v", "error", "-print_format", "json",
         "-show_streams", "-show_format", str(path)],
        capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"ffprobe 失败: {out.stderr[:200]}")
    data = json.loads(out.stdout or "{}")
    v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
    fps = "0"
    if v.get("avg_frame_rate") and v["avg_frame_rate"] != "0/0":
        num, _, den = v["avg_frame_rate"].partition("/")
        try:
            rate = int(num) / int(den or 1)
            fps = str(int(round(rate))) if abs(rate - round(rate)) < 0.05 else f"{rate:.3f}"
        except Exception:  # noqa: BLE001
            fps = v.get("r_frame_rate", "0")
    return {
        "path": str(path), "name": Path(path).name,
        "width": v.get("width"), "height": v.get("height"),
        "vcodec": v.get("codec_name"), "vprofile": v.get("profile"),
        "fps": fps, "pix_fmt": v.get("pix_fmt"),
        "acodec": a.get("codec_name"), "aprofile": a.get("profile"),
        "sample_rate": str(a.get("sample_rate") or ""), "channels": a.get("channels"),
        "duration": float(data.get("format", {}).get("duration") or 0) or None,
        "has_audio": bool(a),
    }


@dataclass
class AnalyzeResult:
    files: list[dict] = field(default_factory=list)
    majority: dict = field(default_factory=dict)   # 多数派参数
    diffs: list[str] = field(default_factory=list)  # 不一致的参数名
    outliers: list[str] = field(default_factory=list)  # 异类文件路径
    video_consistent: bool = True
    audio_consistent: bool = True

    @property
    def can_lossless(self) -> bool:
        return not self.diffs

    @property
    def can_smart_passthrough(self) -> bool:
        return self.video_consistent and not self.audio_consistent

    @property
    def need_align(self) -> bool:
        return not self.video_consistent

    def summary(self) -> str:
        if self.can_lossless:
            return "全部参数一致,可无损合并(-c copy)"
        if self.can_smart_passthrough:
            return f"视频参数一致,音频差异({','.join(k for k in self.diffs if k in AUDIO_KEYS)}) → 智能直通"
        return f"视频参数差异({','.join(k for k in self.diffs if k in VIDEO_KEYS)}),异类 {len(self.outliers)} 个 → 先一键对齐"


def _mode(values: list) -> object:
    return max(set(values), key=values.count) if values else None


def analyze(paths: list[str | Path]) -> AnalyzeResult:
    files = [probe(p) for p in paths]
    if len(files) < 2:
        raise RuntimeError("至少需要 2 个视频文件")
    res = AnalyzeResult(files=files)
    for key in ALL_KEYS:
        vals = [f[key] for f in files]
        maj = _mode(vals)
        res.majority[key] = maj
        if any(v != maj for v in vals):
            res.diffs.append(key)
    res.video_consistent = not any(k in res.diffs for k in VIDEO_KEYS)
    res.audio_consistent = not any(k in res.diffs for k in AUDIO_KEYS)
    res.outliers = [f["path"] for f in files
                    if any(f[k] != res.majority[k] for k in VIDEO_KEYS)]
    return res


def _run(cmd: list[str], timeout: int = 3600) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg 失败: {proc.stderr[-400:]}")
    return proc


def lossless_merge(files: list[str], out: str | Path, stop_check=None) -> Path:
    """通道 A:concat demuxer + -c copy。失败自动走 _rescue。"""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for p in files:
            f.write(f"file '{Path(p).as_posix()}'\n")
        listfile = f.name
    try:
        try:
            _run([_ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i", listfile,
                  "-c", "copy", str(out)])
            return out
        except Exception:  # noqa: BLE001
            return _rescue(files, out)
    finally:
        os.unlink(listfile)


def _rescue(files: list[str], out: Path) -> Path:
    """容错回退:换中间容器(.ts)再 copy;仍失败则整批重编码。"""
    tmp = Path(tempfile.mkdtemp(prefix="merger_"))
    try:
        ts_files = []
        for i, p in enumerate(files):
            seg = tmp / f"{i:04d}.ts"
            _run([_ffmpeg(), "-y", "-i", p, "-c", "copy", "-bsf:v", "h264_mp4toannexb",
                  "-f", "mpegts", str(seg)])
            ts_files.append(str(seg))
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            for p in ts_files:
                f.write(f"file '{p}'\n")
            lst = f.name
        try:
            _run([_ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i", lst,
                  "-c", "copy", "-bsf:a", "aac_adtstoasc", str(out)])
            return out
        finally:
            os.unlink(lst)
    except Exception:  # noqa: BLE001
        return _reencode_merge(files, out)
    finally:
        for p in tmp.glob("*"):
            p.unlink(missing_ok=True)
        tmp.rmdir()


def smart_passthrough_merge(files: list[str], out: str | Path, stop_check=None) -> Path:
    """通道 B:视频流 copy,仅统一音频(48k 立体声 AAC)。"""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="passthrough_"))
    try:
        segs = []
        for i, p in enumerate(files):
            seg = tmp / f"{i:04d}.mp4"
            _run([_ffmpeg(), "-y", "-i", p,
                  "-map", "0:v:0", "-map", "0:a?",
                  "-c:v", "copy",
                  "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                  "-af", "apad", "-shortest",
                  str(seg)])
            segs.append(str(seg))
        return lossless_merge(segs, out)
    finally:
        for p in tmp.glob("*"):
            p.unlink(missing_ok=True)
        tmp.rmdir()


def _reencode_merge(files: list[str], out: Path, w: int = 1280, h: int = 720) -> Path:
    """通道 D(兜底):全部统一转码后 concat。"""
    tmp = Path(tempfile.mkdtemp(prefix="reencode_"))
    try:
        segs = []
        for i, p in enumerate(files):
            seg = tmp / f"{i:04d}.mp4"
            _run([_ffmpeg(), "-y", "-i", p,
                  "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30",
                  "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                  "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                  str(seg)])
            segs.append(str(seg))
        return lossless_merge(segs, out)
    finally:
        for p in tmp.glob("*"):
            p.unlink(missing_ok=True)
        tmp.rmdir()


def align_one(src: str, target: dict, out_dir: Path | None = None) -> Path:
    """一键对齐单个异类文件到多数派参数(仅视频转码,音频统一 aac)。返回新文件。"""
    out_dir = out_dir or (config.STATIC_DIR / "aligned")
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / f"aligned_{Path(src).stem}_{uuid.uuid4().hex[:6]}.mp4"
    vf = (f"scale={target['width']}:{target['height']}:force_original_aspect_ratio=decrease,"
          f"pad={target['width']}:{target['height']}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={target['fps']}")
    _run([_ffmpeg(), "-y", "-i", src, "-vf", vf,
          "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
          "-pix_fmt", str(target.get("pix_fmt") or "yuv420p"),
          "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", str(dst)])
    # 对齐后校验
    check = probe(dst)
    for k in VIDEO_KEYS:
        if str(check[k]) != str(target[k]):
            raise RuntimeError(f"对齐校验失败:{k} {check[k]} != {target[k]}")
    return dst


def align_outliers(result: AnalyzeResult, progress=None, stop_check=None) -> list[str]:
    """把所有异类对齐到多数派;返回新的文件序列(原顺序)。"""
    aligned: dict[str, str] = {}
    outliers = set(result.outliers)
    done = 0
    for f in result.files:
        if stop_check and stop_check():
            raise RuntimeError("用户停止")
        if f["path"] in outliers:
            aligned[f["path"]] = str(align_one(f["path"], result.majority))
            done += 1
            if progress:
                progress(done, len(outliers), f["name"])
    return [aligned.get(f["path"], f["path"]) for f in result.files]


def auto_merge(files: list[str], out: str | Path, progress=None, stop_check=None) -> tuple[Path, str]:
    """全自动:检测 → 选通道 → 合并。返回 (输出路径, 通道说明)。"""
    result = analyze(files)
    if progress:
        progress(0, 1, result.summary())
    if result.can_lossless:
        return lossless_merge(files, out, stop_check), "无损合并(-c copy)"
    if result.can_smart_passthrough:
        return smart_passthrough_merge(files, out, stop_check), "智能直通(视频 copy,音频统一)"
    files2 = align_outliers(result, progress, stop_check)
    return lossless_merge(files2, out, stop_check), f"已对齐 {len(result.outliers)} 个异类后无损合并"


# ── 剧集拼接入口(镜头视频 + 旁白混音,对齐原版 ffmpeg-merge) ──

def episode_shot_files(episode_id: int, only_ids: list[int] | None = None) -> list[Path]:
    rows = db.q("SELECT * FROM storyboards WHERE episode_id=? ORDER BY storyboard_number", (episode_id,))
    files = []
    for r in rows:
        if only_ids and r["id"] not in only_ids:
            continue
        url = r["video_url"] or r["composed_video_url"]
        if not url:
            continue
        p = config.media_url_to_path(url)
        if p.exists():
            files.append(p)
    if not files:
        raise RuntimeError("没有已生成的镜头视频(先在「分镜」批量生成视频)")
    return files


def merge_episode(episode_id: int, only_ids: list[int] | None = None,
                  progress=None, stop_check=None) -> Path:
    """拼接所选镜头;有旁白 MP3 时 amix 混音;分辨率统一到多数派。落 video_merges + episodes.video_url。"""
    shots = episode_shot_files(episode_id, only_ids)
    out = config.STATIC_DIR / "merged" / f"{episode_id}_{uuid.uuid4().hex[:8]}.mp4"
    ts = db.now()
    merge_id = db.ex(
        "INSERT INTO video_merges(episode_id,provider,model,scenes,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
        (episode_id, "ffmpeg", "lossless-auto", json.dumps([str(p) for p in shots], ensure_ascii=False),
         "processing", ts, ts))
    try:
        # 旁白音轨:逐镜头对应
        narrations = []
        rows = db.q("SELECT * FROM storyboards WHERE episode_id=? ORDER BY storyboard_number", (episode_id,))
        id_set = set(only_ids) if only_ids else {r["id"] for r in rows}
        shot_urls = [str(p) for p in shots]
        for r in rows:
            if r["id"] not in id_set:
                continue
            url = r["video_url"] or r["composed_video_url"]
            if url and str(config.media_url_to_path(url)) in shot_urls and r["narration_audio_url"]:
                np_ = config.media_url_to_path(r["narration_audio_url"])
                narrations.append(np_ if np_.exists() else None)
            elif url and str(config.media_url_to_path(url)) in shot_urls:
                narrations.append(None)

        has_narr = any(narrations)
        if has_narr and len(narrations) == len(shots):
            merged = _merge_with_narration(shots, narrations, out, stop_check)
            channel = "无损合并 + 旁白混音"
        else:
            path, channel = auto_merge([str(p) for p in shots], out, progress, stop_check)
            merged = path
        dur = probe(merged).get("duration") or 0
        db.ex("UPDATE video_merges SET merged_url=?, status='completed', duration=?, updated_at=? WHERE id=?",
              (config.path_to_media_url(merged), dur, db.now(), merge_id))
        db.ex("UPDATE episodes SET video_url=?, updated_at=? WHERE id=?",
              (config.path_to_media_url(merged), db.now(), episode_id))
        if progress:
            progress(1, 1, str(merged))
        return merged
    except Exception as e:  # noqa: BLE001
        db.ex("UPDATE video_merges SET status='failed', error_msg=?, updated_at=? WHERE id=?",
              (str(e)[:500], db.now(), merge_id))
        raise


def _merge_with_narration(shots: list[Path], narrations: list[Path | None],
                          out: Path, stop_check=None) -> Path:
    """视频统一参数 + 每镜头旁白 MP3 叠加 amix(filter_complex,对齐原版)。"""
    inputs: list[str] = []
    for s, n in zip(shots, narrations):
        inputs += ["-i", str(s)]
        inputs += ["-i", str(n)] if n else []
    parts, vlabels, alabels = [], [], []
    vi = 0
    for idx, (s, n) in enumerate(zip(shots, narrations)):
        v = f"[{vi}:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v{idx}];"
        parts.append(v)
        vlabels.append(f"[v{idx}]")
        vi += 1
        if n:
            parts.append(f"[{vi}:a]aformat=sample_rates=48000:channel_layouts=stereo[a{idx}];")
            alabels.append(f"[a{idx}]")
            vi += 1
        else:
            parts.append(f"anullsrc=r=48000:cl=stereo,atrim=0:2,asetpts=PTS-STARTPTS[a{idx}x];")
            alabels.append(f"[a{idx}x]")
    vconcat = "".join(vlabels) + f"concat=n={len(shots)}:v=1:a=0[vout];"
    amix = "".join(alabels) + f"amix=inputs={len(shots)}:normalize=0[aout]"
    fc = "".join(parts) + vconcat + amix
    _run([_ffmpeg(), "-y", *inputs, "-filter_complex", fc,
          "-map", "[vout]", "-map", "[aout]",
          "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
          "-c:a", "aac", "-b:a", "192k", str(out)])
    return out
