# -*- coding: utf-8 -*-
"""图片生成客户端:openai / gemini / volcengine / agnes / qwen-image 适配(提交+轮询+落盘)。"""
from __future__ import annotations

import base64
import time
import uuid
from pathlib import Path

import requests
from PIL import Image

from ..core import config
from . import registry
from .text_client import AIError


def _download(url: str, out: Path, headers: dict | None = None) -> Path:
    resp = requests.get(url, headers=headers or {}, timeout=180)
    if resp.status_code != 200:
        raise AIError(f"下载生成图片失败 HTTP {resp.status_code}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(resp.content)
    return out


def _b64_save(b64: str, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(b64))
    return out


def _ref_data_url(path: str | Path) -> str | None:
    """参考图本地路径 → 压缩 data URL(≤768px JPEG q68,对齐原版压缩口径);失败返回 None。"""
    try:
        import io
        p = Path(path)
        if not p.exists():
            return None
        with Image.open(p) as im:
            im = im.convert("RGB")
            im.thumbnail((768, 768))
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=68)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:  # noqa: BLE001
        return None


_NEG_UNSUPPORTED = ("negative_prompt is not supported",
                    "negative prompt is not supported",
                    "unsupported parameter: negative_prompt")


def _strip_negative(body: dict) -> bool:
    """从请求体剥离 negative_prompt(顶层 / extra_body / 深层扫描),返回是否剥掉了。"""
    removed = False
    if body.pop("negative_prompt", None) is not None:
        removed = True
    eb = body.get("extra_body")
    if isinstance(eb, dict) and eb.pop("negative_prompt", None) is not None:
        removed = True
    for v in list(body.values()):                      # 深层扫描(网关可能包一层)
        if isinstance(v, dict):
            if v.pop("negative_prompt", None) is not None:
                removed = True
    return removed


def _neg_unsupported(resp) -> bool:
    """上游是否以「不支持 negative_prompt」为由拒绝了请求。"""
    try:
        text = resp.text[:500].lower()
    except Exception:  # noqa: BLE001
        return False
    return any(m in text for m in _NEG_UNSUPPORTED)


def _post_with_negative(url: str, body: dict, headers: dict, *, timeout: int,
                        prefix: str, **post_kw):
    """提交请求;上游不支持 negative_prompt 时**剥离后自动重试一次**。

    对齐原版 generation.ts 的「negative_prompt is not supported → 去掉重试」:
    平台质量守卫仍会下发负面词,但模型不吃这个字段时不能因此整次失败。
    """
    resp = requests.post(url, json=body, headers=headers, timeout=timeout, **post_kw)
    if resp.status_code >= 400 and _neg_unsupported(resp):
        if _strip_negative(body):
            resp = requests.post(url, json=body, headers=headers, timeout=timeout, **post_kw)
            if resp.status_code < 400:
                return resp
            text = resp.text[:400]
            raise AIError(f"{prefix} HTTP {resp.status_code}(已去掉负面词仍失败): {text}")
        text = resp.text[:400]
        raise AIError(f"{prefix} HTTP {resp.status_code}: {text}")
    return resp


def generate_image(prompt: str, out_name: str | None = None,
                   config_id: int | None = None, size: str | None = None,
                   reference_images: list[str] | None = None,
                   people: int = 1, skip_guard: bool = False) -> tuple[Path, str]:
    """生图:返回 (本地路径, provider)。reference_images 为本地路径列表(图生图参考)。

    仅 agnes 注入(extra_body.image[],≤6 张压缩 data URI);其余 provider 忽略。

    **平台级质量守卫**:prompt 统一追加画面质量要求(幂等),negative_prompt 统一下发禁用词。
    people = 画面应有的人物数(漫画格=绑定角色数),>1 时守卫措辞切到「恰好 N 人」,
    否则双人格子会收到「只许一个人」的自相矛盾指令、模型可能随机删掉第二个角色。
    """
    from .prompt_guards import apply_image_quality_guard, build_image_negative_guard
    prompt = prompt if skip_guard else apply_image_quality_guard(prompt, people)
    negative = build_image_negative_guard(people) if not skip_guard else None
    cfg = registry.check_ready("image", config_id)  # 未配置/缺 Key 直接拦下
    provider = cfg["provider"]
    out_name = out_name or f"{uuid.uuid4().hex}.png"
    out = config.STATIC_DIR / "images" / out_name
    headers = {"Content-Type": "application/json"}
    if cfg.get("api_key"):
        headers["Authorization"] = f"Bearer {cfg['api_key']}"

    if provider in ("openai", "gemini", "qwen-image"):
        # OpenAI 兼容 images/generations
        url = cfg["base_url"].rstrip("/") + "/images/generations"
        body: dict = {"model": cfg["model"], "prompt": prompt, "n": 1}
        if size:
            body["size"] = size
        if negative:
            body["negative_prompt"] = negative
        resp = _post_with_negative(url, body, headers, timeout=300, prefix="生图失败")
        if resp.status_code != 200:
            raise AIError(f"生图失败 HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()["data"][0]
        if data.get("b64_json"):
            _b64_save(data["b64_json"], out)
        else:
            _download(data["url"], out)
        return out, provider

    if provider == "volcengine":
        # 火山方舟 Seedream:images/generations 兼容(支持 b64 返回)
        url = cfg["base_url"].rstrip("/") + "/images/generations"
        body = {"model": cfg["model"], "prompt": prompt, "response_format": "url",
                "size": size or "2K", "watermark": False}
        if negative:
            body["negative_prompt"] = negative
        resp = _post_with_negative(url, body, headers, timeout=300, prefix="生图失败")
        if resp.status_code != 200:
            raise AIError(f"生图失败 HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()["data"][0]
        if data.get("b64_json"):
            _b64_save(data["b64_json"], out)
        else:
            _download(data["url"], out)
        return out, provider

    if provider == "agnes":
        # Agnes:提交任务 → 轮询 → 下载
        submit = cfg["base_url"].rstrip("/") + "/v1/images/generations"
        body = {"model": cfg["model"], "prompt": prompt, "n": 1}
        if size:
            body["size"] = size
        if negative:
            body["negative_prompt"] = negative
        # 图生图参考(对齐原版 agnes-image adapter:extra_body.image[] data URI,≤6 张)
        refs = [r for r in (_ref_data_url(x) for x in (reference_images or [])[:6]) if r]
        if refs:
            body["extra_body"] = {"image": refs}
        resp = _post_with_negative(submit, body, headers, timeout=120, prefix="Agnes 提交失败")
        if resp.status_code not in (200, 201):
            raise AIError(f"Agnes 提交失败 HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        # 兼容同步返回与异步任务两种形态
        if isinstance(data.get("data"), list) and data["data"] and (data["data"][0].get("url") or data["data"][0].get("b64_json")):
            item = data["data"][0]
            if item.get("b64_json"):
                _b64_save(item["b64_json"], out)
            else:
                _download(item["url"], out)
            return out, provider
        task_id = data.get("id") or data.get("task_id") or data.get("data", {}).get("task_id")
        if not task_id:
            raise AIError(f"Agnes 响应缺少任务 id: {str(data)[:300]}")
        for _ in range(120):  # 5s × 120 上限 10 分钟(对齐原版)
            time.sleep(5)
            st = requests.get(f"{cfg['base_url'].rstrip('/')}/v1/images/generations/{task_id}",
                              headers=headers, timeout=30)
            payload = st.json()
            status = str(payload.get("status") or payload.get("data", {}).get("status", "")).lower()
            if status in ("succeeded", "success", "completed"):
                item = (payload.get("data") or {}).get("images") or payload.get("images") or [{}]
                url_i = item[0].get("url") or item[0].get("image_url")
                if url_i:
                    _download(url_i, out)
                    return out, provider
                b64 = item[0].get("b64_json")
                if b64:
                    _b64_save(b64, out)
                    return out, provider
                raise AIError(f"Agnes 任务完成但无图片: {str(payload)[:300]}")
            if status in ("failed", "error", "cancelled"):
                raise AIError(f"Agnes 生图任务失败: {str(payload)[:300]}")
        raise AIError("Agnes 生图任务轮询超时(10 分钟)")

    raise AIError(f"不支持的图片 provider: {provider}")


def test_config(cfg: dict) -> tuple[bool, str]:
    try:
        out, _ = generate_image("a red apple on white background, product photo",
                                out_name=f"_test_{uuid.uuid4().hex[:8]}.png")
        out.unlink(missing_ok=True)
        return True, "OK"
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:300]
