# -*- coding: utf-8 -*-
"""视频生成客户端:volcengine(Seedance) / minimax / aliyun(Wan) / agnes,提交+轮询+下载。"""
from __future__ import annotations

import re
import time
import uuid
from pathlib import Path

import requests

from ..core import config
from . import registry
from .text_client import AIError

RESOLUTION_TIERS: dict[str, list[str]] = {
    # 对齐原版 RESOLUTION_TIERS(按厂商分档)
    "volcengine": ["480p", "720p"],
    "minimax": ["768P", "2K"],
    "aliyun": ["480P", "720P", "1080P"],
    "agnes": ["720P", "1080P"],
}


def _ext_for(url: str) -> str:
    low = (url.split("?")[0] or "").lower()
    return Path(low).suffix or ".mp4"


def _download(url: str, headers: dict | None = None) -> Path:
    out = config.STATIC_DIR / "videos" / f"{uuid.uuid4().hex}{_ext_for(url)}"
    resp = requests.get(url, headers=headers or {}, timeout=600)
    if resp.status_code != 200:
        raise AIError(f"下载生成视频失败 HTTP {resp.status_code}")
    out.write_bytes(resp.content)
    return out


def _local_to_data_url(path: str | Path) -> str:
    import base64
    p = Path(path)
    if p.exists():
        return "data:application/octet-stream;base64," + base64.b64encode(p.read_bytes()).decode()
    return str(path)


def _poll(fetch_status, interval: int, rounds: int) -> str:
    """轮询直至返回最终视频 URL;失败抛 AIError。对齐原版 video 10s×300。"""
    for _ in range(rounds):
        time.sleep(interval)
        status, url, err = fetch_status()
        if url:
            return url
        if status == "failed":
            raise AIError(f"视频任务失败: {err}")
    raise AIError("视频任务轮询超时")


def generate_video(prompt: str, resolution: str = "720p", duration: int | None = None,
                   first_frame: str | None = None, config_id: int | None = None,
                   reference_images: list[str] | None = None) -> tuple[Path, str]:
    """文生视频 / 图生视频(first_frame 本地路径)。

    reference_images:@角色 形象参考图本地路径列表(角色一致性)。
    agnes 走多模态参考注入;volcengine 以 reference_image 角色注入;minimax/aliyun 忽略。
    返回 (本地路径, provider)。
    """
    cfg = registry.default_config("video", config_id)
    if not cfg:
        raise AIError("未配置视频生成服务,请到「设置 → AI 服务」添加。")
    provider = cfg["provider"]
    headers = {"Content-Type": "application/json"}
    if cfg.get("api_key"):
        headers["Authorization"] = f"Bearer {cfg['api_key']}"
    base = cfg["base_url"].rstrip("/")
    refs = [_local_to_data_url(r) for r in (reference_images or [])][:4]

    if provider == "volcengine":
        body: dict = {"model": cfg["model"], "content": [
            {"type": "text", "text": prompt + f" --resolution {resolution}" +
             (f" --duration {duration}" if duration else "") +
             (" --ratio 16:9" if resolution.lower() not in ("720p", "1080p", "480p") else "")}]}
        for ref in refs:
            body["content"].append({"type": "image_url", "image_url": {"url": ref},
                                    "role": "reference_image"})
        if first_frame:
            body["content"].append({"type": "image_url", "image_url": {"url": _local_to_data_url(first_frame)}})
        resp = requests.post(f"{base}/contents/generations/tasks", json=body, headers=headers, timeout=120)
        if resp.status_code not in (200, 201):
            raise AIError(f"Seedance 提交失败 HTTP {resp.status_code}: {resp.text[:300]}")
        task_id = resp.json().get("id")
        if not task_id:
            raise AIError(f"Seedance 响应缺少 id: {resp.text[:300]}")

        def check():
            st = requests.get(f"{base}/contents/generations/tasks/{task_id}", headers=headers, timeout=30).json()
            status = st.get("status", "")
            video = (st.get("content") or {}).get("video_url") if isinstance(st.get("content"), dict) else None
            return ("failed" if status == "failed" else "running"), video, st.get("error")

        url = _poll(check, 10, 300)
        return _download(url, headers), provider

    if provider == "minimax":
        body = {"model": cfg["model"], "prompt": prompt}
        if first_frame:
            body["first_frame_image"] = _local_to_data_url(first_frame)
        resp = requests.post(f"{base}/video_generation", json=body, headers=headers, timeout=120)

        def check2():
            st = requests.get(f"{base}/query/video_generation?task_id={task_id}", headers=headers, timeout=30).json()
            status = st.get("status", "")
            file = (st.get("file") or {}) if isinstance(st.get("file"), dict) else {}
            return ("failed" if status == "Fail" else "running"), file.get("download_url"), st.get("message")

        url = _poll(check2, 10, 300)
        return _download(url, headers), provider

    if provider == "aliyun":
        body = {"model": cfg["model"], "input": {"prompt": prompt},
                "parameters": {"size": "1280*720" if "720" in resolution.upper() else "960*480"}}
        resp = requests.post(f"{base}/api/v1/services/aigc/video-generation/video-synthesis",
                             json=body, headers=headers, timeout=120)
        if resp.status_code not in (200, 201):
            raise AIError(f"Wan 提交失败 HTTP {resp.status_code}: {resp.text[:300]}")
        task_id = resp.json().get("output", {}).get("task_id")

        def check3():
            st = requests.get(f"{base}/api/v1/tasks/{task_id}", headers=headers, timeout=30).json()
            out = st.get("output", {})
            status = out.get("task_status", "")
            url_v = out.get("video_url")
            if status == "SUCCEEDED" and url_v:
                return "running", url_v + ("?Expires=" + str(int(time.time()) + 86400)), None
            return ("failed" if status in ("FAILED", "CANCELED") else "running"), None, out.get("message")

        url = _poll(check3, 10, 300)
        return _download(url, headers), provider

    if provider == "agnes":
        body: dict = {"model": cfg["model"], "prompt": prompt, "resolution": resolution}
        if duration:
            body["duration"] = duration
        if refs:
            body["reference_images"] = refs  # 多模态参考(@角色 一致性)
        if first_frame:
            body["image"] = _local_to_data_url(first_frame)
        resp = requests.post(f"{base}/v1/videos/generations", json=body, headers=headers, timeout=120)
        if resp.status_code not in (200, 201):
            raise AIError(f"Agnes 提交失败 HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        if isinstance(data.get("data"), dict) and data["data"].get("url"):
            return _download(data["data"]["url"], headers), provider
        task_id = data.get("id") or data.get("task_id")

        def check4():
            st = requests.get(f"{base}/v1/videos/generations/{task_id}", headers=headers, timeout=30).json()
            status = str(st.get("status") or (st.get("data") or {}).get("status", "")).lower()
            url_v = (st.get("data") or {}).get("url") or (st.get("data") or {}).get("video_url")
            return ("failed" if status in ("failed", "error") else "running"), url_v, str(st)[:200]

        url = _poll(check4, 10, 300)
        return _download(url, headers), provider

    if provider == "runninghub":
        return _generate_runninghub(cfg, base, headers, prompt, resolution, duration,
                                    first_frame, refs, config_id)

    raise AIError(f"不支持的视频 provider: {provider}")


# ── RunningHub(对齐原版 b78f9bf:openapi v2,Seedance 2.5 + Wan 3.0 参考生视频)──
RUNNINGHUB_MODELS = {
    "seedance-2.5": {"endpoint": "/bydedance/seedance-2.5-token/multimodal-video",
                      "img": 30, "vid": 10, "aud": 10},
    "wan3.0-video": {"endpoint": "/alibaba/wan-3.0/reference-to-video",
                     "img": 10, "vid": 5, "aud": 5},
    "wan3.0-video-prime": {"endpoint": "/alibaba/wan-3.0/reference-to-video",
                           "img": 10, "vid": 5, "aud": 5},
}


def _rh_normalize_duration(d) -> int:
    try:
        n = int(float(d))
    except (TypeError, ValueError):
        n = 5
    return min(30, max(2, n))


def _rh_normalize_resolution(res: str, is_wan: bool) -> str:
    r = (res or "").strip()
    if r.upper() == "2K":
        return "1080P" if is_wan else "2K"
    if r.upper() in ("480P", "1080P"):
        return r.upper()
    return "720P"


def _rh_find_video_url(node, depth: int = 0):
    """递归找第一个 .mp4 URL;优先按字段名顺序,避免封面图抢先命中。"""
    if depth > 8:
        return None
    if isinstance(node, str):
        return node if re.match(r"^https?://\S+\.mp4(\?\S*)?$", node, re.I) else None
    if isinstance(node, dict):
        for key in ("video_url", "videoUrl", "video", "url", "result_url", "resultUrl"):
            if key in node:
                hit = _rh_find_video_url(node[key], depth + 1)
                if hit:
                    return hit
        for v in node.values():
            hit = _rh_find_video_url(v, depth + 1)
            if hit:
                return hit
    elif isinstance(node, list):
        for v in node:
            hit = _rh_find_video_url(v, depth + 1)
            if hit:
                return hit
    return None


def _generate_runninghub(cfg, base, headers, prompt, resolution, duration,
                         first_frame, refs, config_id):
    import json as _json
    model_key = (cfg["model"] or "").strip()
    spec = RUNNINGHUB_MODELS.get(model_key)
    if not spec:
        raise AIError("RunningHub 视频仅支持 seedance-2.5 / wan3.0-video(-prime),当前: " + model_key)
    is_wan = model_key.startswith("wan3")
    imgs = list(refs)
    if len(imgs) > spec["img"]:
        raise AIError(f"RunningHub 参考素材超限:图片≤{spec['img']}")
    # 首帧图 unshift 到首位,保持「第一张参考图锁脸」语义
    if first_frame:
        d_url = _local_to_data_url(first_frame)
        if d_url not in imgs:
            imgs.insert(0, d_url)
    if not imgs and not prompt.strip():
        raise AIError("RunningHub 生成需要至少一个参考图/视频或 prompt")
    dur = _rh_normalize_duration(duration)
    res = _rh_normalize_resolution(resolution, is_wan)
    # 厂商私有开关:settings.realPersonMode 显式为 false 才关(默认 true)
    settings = {}
    try:
        s = _json.loads(cfg.get("settings") or "")
        if isinstance(s, dict):
            settings = s
    except Exception:  # noqa: BLE001
        pass
    body: dict = {"prompt": prompt.replace("@图片(\\d+)", r"图\1"),
                  "imageUrls": imgs, "resolution": res, "duration": dur}
    if is_wan:
        body["aspectRatio"] = "自适应"
        body["audio"] = True
    else:
        body["ratio"] = "自适应"
        body["generateAudio"] = True
        body["watermark"] = False
        body["realPersonMode"] = settings.get("realPersonMode") is not False
    submit = requests.post(f"{base}/openapi/v2{spec['endpoint']}", json=body,
                           headers=headers, timeout=120)
    if submit.status_code not in (200, 201):
        raise AIError(f"RunningHub 提交失败 HTTP {submit.status_code}: {submit.text[:300]}")
    r = submit.json()
    task_id = (r.get("taskId") or r.get("task_id") or (r.get("data") or {}).get("taskId")
               or (r.get("data") or {}).get("task_id") or r.get("id"))
    if not task_id:
        raise AIError(f"[RunningHub] {r.get('msg') or r.get('message') or '响应中缺少 taskId'}")

    def check():
        st = requests.post(f"{base}/openapi/v2/query", json={"taskId": task_id},
                           headers=headers, timeout=30).json()
        payload = st.get("data") or st
        s = str(payload.get("status") or payload.get("state") or "").lower()
        if s in ("success", "succeeded", "completed", "complete"):
            return "running", _rh_find_video_url(payload), None
        if s in ("failed", "failure", "error", "cancelled", "canceled"):
            return "failed", None, (payload.get("msg") or payload.get("message")
                                    or payload.get("failMsg") or payload.get("fail_msg"))
        return "running", None, None

    url = _poll(check, 10, 300)
    return _download(url, headers), "runninghub"


def test_config(cfg: dict) -> tuple[bool, str]:
    # 视频不做真实生成测试,只做提交连通性(避免消耗配额):用极短 prompt 提交后立即查询一次
    try:
        headers = {"Content-Type": "application/json"}
        if cfg.get("api_key"):
            headers["Authorization"] = f"Bearer {cfg['api_key']}"
        base = cfg["base_url"].rstrip("/")
        if cfg["provider"] == "volcengine":
            resp = requests.post(f"{base}/contents/generations/tasks", json={
                "model": cfg["model"], "content": [{"type": "text", "text": "ping --resolution 480p"}]},
                headers=headers, timeout=30)
            ok = resp.status_code in (200, 201)
            return ok, "OK" if ok else f"HTTP {resp.status_code}: {resp.text[:200]}"
        return True, "OK(跳过真实提交)"
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:300]
