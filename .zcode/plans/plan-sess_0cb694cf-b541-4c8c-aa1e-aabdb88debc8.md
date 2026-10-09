# 计划:功能与界面对齐参考项目(第 32 轮)

方向已确认:**先修 bug → 后端契约与重试 → i18n 15 语言全覆盖 → 界面复刻(设置卡片 + 换脸向导)**,六批次,每批独立可验证、可提交。

---

## 批次 0:修 4 个真 bug + 补缺失迁移(必须最先做)

批次 3/4 会重写 `face_swap_page.py` 和设置页,先把这些文件里的缺陷清掉,避免在坏地基上盖楼。

| 文件 | 问题 | 修法 |
|---|---|---|
| `app/ui/face_swap_page.py:167` | `if err:` 判的是**从 toast 导入的函数**(恒为真),换脸成功也弹错误 | 改 `if error:`,提示里用 `error` |
| `app/ui/face_swap_page.py:114,151`<br>`app/ui/character_face_swap_dialog.py:195` | `ok, msg = face_swap.health(...)` 把 toast 的 `ok` **覆盖掉** | 局部改名 `healthy, msg`,不动导入 |
| `app/ui/character_face_swap_dialog.py:258` | `str(e_)` 引用**未定义名**,批量失败分支直接 `NameError` | 改 `str(error)` |
| `app/ui/character_face_swap_dialog.py:166,171,182` | `tr("redraw")` 当对话框标题,该键**不存在** | 换成真实键 |
| `app/ui/character_face_swap_dialog.py:108-109` | `size_tip` 声明后**从未赋值**,分辨率告警是死的 | 用 `QPixmap.width()/height()` 实现 ≥512 警告 / <256 硬失败 |
| `app/core/db.py` 迁移段 | `character_variants` 缺 `sort_order`、`comic_image_url`;`tags` 声明了但**没有写入方** | 迁移加两列;`variants_dialog` 保存时写 `tags` + `sort_order`,排序改 `ORDER BY sort_order, id` |
| `app/ui/settings_dialog.py:541,559,562` | 3 处 QMessageBox 标题/正文是**裸中文** | 收进 `ui_strings` 词典 |

验收:构造一次成功换脸 + 一次批量失败,确认不再误报 / 不再崩;`PRAGMA table_info(character_variants)` 含新列。

---

## 批次 1:视频请求契约校验 + 错误分类 + retry_at 跟随

只动 `app/ai/video_client.py`,不碰生成主链路以外的地方。

1. **`normalize_video_request()`** —— 兼容两种入参形态:本仓现有扁平参数,与官方 Wan 3.0 的 `input.media[] / parameters{}`。`WAN_MEDIA_TYPES` 七种 type;`official_media` 每项 type+非空 url;`first_frame/last_frame/file/link` 各至多 1 项。
2. **`validate_video_request()`** —— 上限表(与参考逐条对齐):
   - aliyun:图片 ≤10 / 视频 ≤5 / 音频 ≤5;`last_frame` 必须配 `first_frame`;`file` 与 `link` 互斥;`first/last` 不得与 reference_* / file / link 混用;`media` 合计 ≤20
   - 通用:图片 ≤9 / 视频 ≤3 / 音频 ≤3;有音频则至少要有 1 个图或视频
   - 全局:prompt 为空且无任何素材 → 拒绝
3. **`is_fallbackable_error()`** —— 4xx(缺 key / 参数错 / 模型下线)判**永久错误直接失败**;429 / 503 / queue_full / gateway 类才判可恢复。这一层决定「要不要继续等」,是回退决策的输入。
4. **`parse_retry_at()` + 跟随** —— 解析上游 `Please try again after <datetime>` 时间戳,睡到那一刻,**最多跟随 2 次、每次 ≤24h、额外 +5s 余量**,绕过短预算。
5. **`resolve_fallback_config()`** —— **env 开关控制、默认关闭**。参考项目已被用户策略关成单点(不再悄悄切模型掩盖真问题),这里保持同一策略,需要时用 `YIHAO_VIDEO_FALLBACK=1` 打开。

接入点:`generate_video()` 分发前先 normalize + validate;提交重试循环里按错误分类决定「续等 / 长预算 / 快速失败」。

验收:用构造请求逐条断言错误文案(超限 / 混用 / 互斥 / 空 prompt 各一条);`is_fallbackable_error` 对 400 与 429 各断言一次。

---

## 批次 2:i18n 15 语言全覆盖

真实待办是 **~280 条**,不是之前估的 550 —— 另外 ~300 条是**发给 AI 模型的提示词,不该翻译**(与参考项目一致:模型指令留在提示词文件里按语言提供,不在 UI 层翻)。

拆分为:
- **150 条**用户可见标签 / 按钮 / 占位符 / 对话框文案
- **9 条** tooltip
- **120 条** `err()` / `ok()` / QMessageBox 错误提示

做法:
1. 往 `app/core/ui_strings.py` 的 `S` 词典补约 280 个键,每条 15 个值。词典已有自检(必须恰好 15 个非空串),沿用。
2. 逐文件替换调用点:`episode_page.py`(91)→ `novel_dialogs.py`(70)→ `settings_dialog.py`(52)→ `asset_dialogs.py`(49)→ `book_import_dialog.py`(46)→ `ai_edit_dialog.py`(38)→ `batch_dialogs.py`(34)→ `character_face_swap_dialog.py`(32)→ 其余。
3. **明确排除**:`ai_edit_dialog.py` 的连贯性硬规则、`novel.py` 的写作提示词等模型指令字符串,一律原样保留。

验收:15 种语言 × 亮/暗 × 2 项目 × 6 步骤冒烟,无异常;人工抽查 zh/en/ja/ko 四种下的同一页文案。

---

## 批次 3:设置页 AI 配置列表 → 卡片行

现状:`_fill_services()` 第 130 行用一个 f-string 把整条配置拼成一行文本塞进 `QListWidget`,无开关、无删除、无逐行测试,只能双击编辑。

改为每配置一张卡片行:
- 供应商标识徽章 + 名称 + 「有 Key / 无 Key」标 + 「已停用」标
- **启用/停用开关**(走 `registry.update_config(is_active=...)`)
- **模型 chips**:复用已有的 `ModelChipsEditor`(`settings_dialog.py:629`)与 `_FlowLayout`(`:568`),★ 标当前默认模型
- **逐行测试**:复用 `TESTERS` 字典,含新增的 `jev`
- 编辑 / 删除(删除走批次 5 的确认对话框)

改动集中在 `_page_ai` 的 8 处 + `_fill_services`,数据层 `registry` 不动。

验收:加一条配置 → 改优先级 → 关停 → 逐行测试 → 删除,全程不重启。

---

## 批次 4:换脸工具页 → 三段式向导

`face_swap_page.py` 现在 207 行,结构是「头部 + 一排操作按钮 + 单行不换行的卡片滚动条」,连 ①②③ 的分段都没有。`character_face_swap_dialog.py` 里已有可搬的:三栏布局、引擎下拉(faceswap + image 合并)、风格下拉、从其他角色选源脸、批量、全部下载、应用/还原。

重写为:
- **① 源人脸**:上传 / 剪贴板粘贴 / URL 粘贴 / 从其他角色形象选;预览缩略图;**分辨率告警**(<512 警告、<256 硬失败)
- **② 角色模板图**:角色选择器 → 载入该角色基础形象 + 全部造型变体的缩略网格(逐张保持原比例);从库拿,不再是任意文件
- **③ 结果**:独立结果区 + 逐图 ok/失败角标 + 进度条
- 引擎下拉(faceswap + image 合并,未配置时给本地服务占位项)、风格下拉、自由提示词
- 逐图重绘、灯箱(复用 `ImageViewerDialog`)、全部下载、全部应用到角色、恢复原貌
- 上次选择记忆(provider / 风格 / 提示词 / 角色),避免按优先级排序把用户静默切到风格化模型
- `QHBoxLayout` → `QGridLayout`,按视口宽度重排列数

`character_face_swap_dialog.py`(角色路线的弹窗)**保持不动**,那条路径继续可用。

验收:选角色 → 批量换脸 → 逐张重绘 → 应用 → 还原,全链路走通;两种主题截图。

---

## 批次 5:确认对话框抽象 + 收尾

- 新增 `ConfirmDialog`(图标变体 / loading 态 / Enter=确认 Esc=取消),替换全仓 **14 处** `QMessageBox.question` / `warning`(7 + 7)
- 进度条驱动下载进度(设置页「关于」页那个 `QProgressBar` 现在一直是 indeterminate)
- PROGRESS.md 补第 32 轮,截图(亮/暗),提交推送

---

## 风险与依赖

- **批次 3/4 是本轮最大的重写**,各自独立成一个提交,出问题可单独回滚;批次 0 先把这两块的坏代码清掉正是为此。
- **i18n 的主要风险是翻译质量**:用词典自检 + 四语人工抽查兜底,不在同一次改动里同时动界面结构。
- **批次 1 不改生成语义**,只在入口加校验与错误分类;契约校验失败会在请求发出前就给出明确原因,比现在让上游拒更好。
- 回退链按 env 默认关闭,与参考项目当前策略一致 —— 需要跨 provider 兜底时开 `YIHAO_VIDEO_FALLBACK=1`。