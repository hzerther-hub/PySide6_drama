# 小云雀 API 接入文档摘录

> 来源：飞书文档《小云雀 API 体验指南》（2026-09-23 更新，v1.0.6）
> 原文链接：https://bytedance.larkoffice.com/docx/CQOYdJNLioLz6fxRzKXcCsKLnJh
> 摘录方式：2026-09-29 登录后按目录锚点逐段提取正文（所有端点路径均已从文档 curl 示例原文确认）。
> 官方入口：小云雀 Web 官网顶部 【CLI/API】 - 【API】

## 定位

小云雀 API 是面向工作流/Agent 的工具包，用你自己的小云雀账号（Access Key）在任意环境发起生成任务。**计费走小云雀积分**（与 Web/CLI 同一账户体系，可用「积分余额查询」接口核对），即会员折扣价同样适用。

## 更新日志

| 版本 | 日期 | 内容 |
|---|---|---|
| v1.0.6 | 2026-09-21 | 新增 MiniMax-H3 / MiniMax-H3-Max / wan3.0 / happyhorse-1.1 模型 |
| v1.0.5 | 2026-09-07 | 新增积分余额查询 API |
| v1.0.4 | 2026-07-31 | 新增 Seedance_2.5 模型 |
| v1.0.3 | 2026-06-29 | 新增沉浸式短片 API |
| v1.0.2 | 2026-06-23 | 响应出参区分视频结果和图片结果 |
| v1.0.1 | 2026-06-22 | 新增 Seedance 2.0 mini 模型 |
| v1.0.0 | 2026-06-15 | 营销视频 API 的生成与结果轮询 |

## 认证（Access Key）

申请：登录小云雀 Web 官网 → 顶部【CLI/API】-【API】→ 新建秘钥 → 复制。**与 CLI 共用**。

所有接口共用请求头：

| 字段 | 值 |
|---|---|
| Authorization | `Bearer <Access Key>` |
| Content-Type | `application/json`（文件上传为 multipart/form-data） |
| Accept | `application/json` |

## 接口清单（路径均已从 curl 示例原文确认）

### 1. 文件上传

```bash
curl -X POST 'https://xyq.jianying.com/api/biz/v1/skill/upload_file' \
  -H 'Authorization: Bearer <Access Key>' \
  -H 'Accept: application/json' \
  -F 'file=@./example.png;type=image/png'
```

- multipart/form-data，**单次仅支持一个文件**；认证在请求头，不进 multipart body；name 固定为 `file`
- 响应：`ret/errmsg/svr_time/log_id` + `data.pippit_asset_id`（资产 ID，提交任务时引用）

### 2. 生成营销视频

```bash
curl -X POST 'https://xyq.jianying.com/api/biz/v1/agent/submit_marketing_run' \
  -H 'Authorization: Bearer <Access Key>' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -d '{
    "message": "基于上传的商品图生成一条适合社媒投放的品牌种草短视频，突出轻薄、防水和通勤场景",
    "asset_ids": ["asset_123"],
    "general_agent_settings": {
      "ratio": 3,
      "duration_start": 15,
      "duration_end": 20,
      "show_subtitle": true,
      "video_model": "seedance2.0_fast_vision",
      "video_resolution": "720p"
    }
  }'
```

请求体：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| message | string | 是 | 自然语言创作指令，不能为空 |
| asset_ids | array\<string\> | 否 | 素材 ID（文件上传返回的 pippit_asset_id） |
| general_agent_settings | object | 是 | 通用生成设置；未传时按默认策略 |
| thread_id | string | 否 | 复用会话；不传则服务端生成 `marketing_<uuid>` |

`general_agent_settings` 字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| ratio | int32 | 画幅：2=16:9，3=9:16，4=4:3，5=3:4，6=1:1 |
| video_model | string | 见下方模型列表 |
| duration_start / duration_end | int32 | 期望时长上下限（秒）；精确时长传同一数值 |
| show_subtitle | bool | 是否展示字幕 |
| video_resolution | string | 480p / 720p / 1080p（**1080p 仅支持 seedance2.0_vision**） |
| images | []object | 参考图列表 `[{"pippit_asset_id": "..."}]` |

响应：`ret=0` 成功；`data.run.run_id` / `data.run.thread_id` / `data.run.state` / `data.web_thread_link`（网页端会话链接，pippit.com 域）。

### 3. 生成沉浸式短片（短剧向）

端点：`POST https://xyq.jianying.com/api/biz/v1/agent/submit_run`（文档正文以 `submit_run` 指代，与 submit_marketing_run 同前缀）

请求体：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| message | string | 是 | 沉浸式短片生成指令，不能为空 |
| asset_ids | array\<string\> | 否 | 素材 ID 列表 |
| video_part_tool_param | object | 是 | 沉浸式短片参数（见下表） |
| thread_id | string | 否 | 复用会话 |
| **agent_name** | string | 是 | **固定传入 `pippit_video_part_agent`** |

`video_part_tool_param` 字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| ratio | string | 否 | 画幅枚举：`16:9` / `9:16` / `4:3` / `3:4` / `1:1`（注意：此处是字符串，营销接口是 int 枚举） |
| prompt | string | 是 | 生成指令，与 message 保持一致 |
| model | string | 是 | 见下方模型列表 |
| generate_type | int64 | 否 | 首尾帧模式传入 1 |
| duration_sec | int32 | 是 | 期望视频时长（秒） |
| resolution | string | 否 | 480p / 720p / 1080p（1080p 仅 seedance2.0_vision） |
| images | []object | 否 | 参考图片 `[{"pippit_asset_id": "..."}]` |
| videos | []object | 否 | 参考视频列表 |

### 可用模型列表（video_model / model 字段）

**VIP 模型**：`seedance2.0_fast_vision`、`seedance2.0_vision`、`Seedance_2.0_mini`、`Seedance_2.5`、`MiniMax-H3`、`MiniMax-H3-Max`、`wan3.0`、`happyhorse-1.1`
**非 VIP 模型**：`Seedance_2.0_mini_lite`

### 4. 结果查询（轮询）

```bash
curl -X POST 'https://xyq.jianying.com/api/biz/v1/agent/query_generate_video_result' \
  -H 'Authorization: Bearer <Access Key>' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -d '{ "thread_id": "...", "run_id": "..." }'
```

- 请求体：`thread_id` + `run_id`（均取自提交响应 `data.run.*`）
- `run_state`：1=已创建，2=处理中，3=成功，4=失败，5=已取消
- 成功时 `video_urls` 返回可下载视频链接（区分视频/图片结果）；未完成为空继续轮询；失败/取消返回 `fail_reason`

### 5. 查询积分余额

```bash
curl -X POST 'https://xyq.jianying.com/api/biz/v1/skill/get_credit_balance' \
  -H 'Authorization: Bearer <Access Key>' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -d '{}'
```

- 请求体为空 JSON；仅查询，不增减积分
- 响应：`data.total_remain_amount`（string，int64；零余额返回 `"0"`）

## FAQ

仅一条：是否有传参说明 / 错误码说明 → 另见文档《小云雀API传参&错误码说明》（站内链接）。

## 与 pydrama 的关系

- 对接模式与现有 `app/ai/video_client.py` 的「提交 + 轮询 + 下载」完全同构（submit → thread_id/run_id → poll run_state → video_urls），加一个 provider 成本低。
- 这是 **Agent 编排型 API**（输入自然语言指令，小云雀负责分镜/编排），不是裸 Seedance 文生视频接口；裸模型直出走 CLI（`pippit-tool-cli` 模型直出）。
- 计费走小云雀积分 → 会员折扣价适用（会员价 Seedance 720P 约 0.28~0.38 元/秒 vs 火山 API 约 0.6~1 元/秒，见价格对比分析）。
- **沉浸式短片 API（submit_run + video_part_tool_param + agent_name=pippit_video_part_agent）与短剧流水线最相关**：支持指定模型（含 Seedance_2.5）、时长、分辨率、参考图/视频、首尾帧模式。
- 积分余额接口可直接用于成本监控与用量告警。
- 商用条款、并发/频控未见说明，生产接入前需与小云雀确认（xiaoyunque@bytedance.com）。
