# PROGRESS.md — 实施过程记录

> 逐项记录 PySide6 重写「易好短剧」的全过程(倒序,最新在上)。
> 计划:[PLAN.md](PLAN.md) · 分析:[docs/易好短剧-工具分析.md](docs/易好短剧-工具分析.md)

## 2026-09-29(第 1 天,完成全部里程碑 M1–M7)

### M7 运行验证与收尾 ✅
- offscreen 冒烟:主窗口启动 → 启动台 → 项目页 → 工作台六阶段切换 → 合并工具 → 设置 → 新建对话框(复刻/宣传表单),全流程无异常。
- **视觉验收(agent 评审 13 张截图)**:12/13 通过。发现并修复:
  1. 资产页内容空白 —— 原因是 `QTabWidget` 内嵌 `QScrollArea` 嵌套塌陷,去掉内层滚动后数据正常显示(修复后复验通过);
  2. 导出页/合并工具页缺空态提示 —— 补「—」空态标签与操作引导;
  3. offscreen 中文方块字 —— offscreen 平台缺 OpenType 支持;**按用户指示采用原版 drama 的字体方案**:drama 源码本身不打包字体,CSS 字体栈为 `SF Pro → PingFang SC → Microsoft YaHei`(body/display)与 `SF Mono/Consolas`(mono);PySide6 版实现同一策略:`theme.py` 的 QSS 使用完全相同字体栈,`main._apply_drama_font()` 优先加载 `app/assets/fonts/` 打包字体(已内置 msyh.ttc,19.7MB),macOS 回落 PingFang SC / Windows 回落 Microsoft YaHei UI。复验后中文全部正常渲染。
- 最终截图 13 张:`docs/screenshots-pyside6/01~13*.png`。
- README:**四语言**(zh/en/ja/ko),每份都含 15 语言支持说明;PROGRESS.md(本文件)。

### M6 UI 层 ✅(9 个界面文件)
- `widgets.py`:卡片/标题/标签/头像(按名字哈希配色)/StatBar/图片加载(/static 相对地址→本地路径)。
- `projects_page.py`:启动台(统计条/筛选下拉/搜索/最近排序/项目卡/更多菜单删除,级联清空 12 张关联表)。
- `new_project_dialog.py`:5 种创作目标单选(宣传→动态追加平台/格式必填;复刻→动态追加参考视频/产品照/出镜照三个文件选择)、风格下拉按 work_type 过滤、比例、面孔文化。
- `project_page.py`:EP 卡片(状态 chip/镜头进度/删除)+「进入制作」;素材库网格(角色/场景/道具混排,图片/描述/生成状态)。
- `episode_page.py`(最大,~800 行):顶栏模型选择(文本/图片/视频/分辨率)+任务入口;左侧 StepNav(剧本/制作/导出三段,进度 x/4);六面板:
  - 原始内容:目标字数/文风/AI 生成小说(自动先策划)/批量写后续章/保存;
  - AI 改写:调 script_rewriter 回写剧本;
  - 视漫制作:提取(全部或按类)/逐资产卡片(AI 最终提示词/重绘/上传/换脸)/批量出图/就绪统计;
  - 分镜:重新拆分/批量补齐提示词/批量视频/单镜重绘/逐镜旁白行内编辑+TTS 按钮/状态统计(生成中·完成·失败)/本地播放;
  - 漫画:拆格/逐格出图/旁白编辑/拼接长图(Pillow,白底+间距+旁白条);
  - 导出:成片列表(下载/时长/状态)+镜头勾选拼接(≥2)+标记完成。
- `settings_dialog.py`:六分区——AI 服务(易好快捷配置/四类服务列表/新增向导(厂商模板+模型+Key)/双击编辑/连通测试/启停)、通用(**语言下拉 15 种**,切换同时写 ui_language+content_language)、风格预设(双击编辑名/描述/提示词/启停)、Agent 配置(10 Agent 列表 + 15 语言下拉切换编辑 System Prompt,保存到 workspace/prompts/,恢复默认)、存储位置(路径+占用统计+打开目录)、关于更新(版本/GitHub Releases 检查)。
- `task_panel.py`:sys_task 表格(ID/类型/模型/状态/时间,状态着色,订阅 TASKMGR.updated 自动刷新)。
- `merger_tool_page.py`:easymerger 工作流(导入文件/文件夹→后台 ffprobe 检测→参数表格(异类标红)+结论条→一键对齐异类→全自动合并→打开输出目录)。
- `main_window.py`:顶栏(Logo/项目/合并工具/语言/主题/设置)+页面栈(启动台/项目页/工作台/复刻页/合并工具)+新建项目全流程(含复刻素材导入)+宣传文案对话框+语言切换(重启生效提示)+主题切换;`ClonePage` 同款复刻工作台(分析原片→生成模特→逐镜首帧图→逐镜视频→无损拼接)。

### M5 流水线 ✅
- `rewriter.py`(script_rewriter→格式化剧本)、`extractor.py`(提取+按名去重合并+episode 关联)、`storyboard.py`(分镜拆解+批量 video_prompt)、`prompts_gen.py`(角色三视图/场景三层构图/道具单品图提示词)、`comic.py`(漫画格+旁白)、`novel.py`(策划五件套/逐章生成带前情/六维审校/按指令改稿/导出整本 txt)、`promo.py`(6 平台×6 格式文案)。
- **`merge.py`(easymerger 完整逻辑)**:probe 指纹(宽高/编码/Profile/fps/像素格式/音频编码/Profile/采样率/声道)→ AnalyzeResult(多数派/差异项/异类/三通道判定)→ lossless_merge(concat demuxer+-c copy)→ 失败 _rescue(转 .ts 中间容器再 copy→仍失败整批重编码)→ smart_passthrough_merge(视频 copy+音频统一 aac 48k 立体声)→ align_one/align_outliers(只转异类到多数派参数,对齐后逐参数校验)→ auto_merge 全自动选通道;另有 merge_episode(剧集拼接,旁白 MP3 filter_complex amix 混音,对齐原版 ffmpeg-merge)。
- **`video_clone.py`(video-clone-lite 逻辑)**:import_reference/upload_material→extract_frames(ffmpeg 均匀抽帧)→analyze_reference(分镜表 JSON 存 metadata.clone)→prepare_presenter(AI 模特)→generate_shot_image(首帧图)→generate_shot_video(图生视频)→merge_clone(auto_merge 拼接)。
- `stitch.py`:漫画长条图(Pillow,统一宽 1080/白底/间距/旁白分行)。

### M4 Agent 层 ✅
- `prompts.py`:10 Agent 中文默认 System Prompt(职责/输出 JSON 格式/创作规范);`FILE_AGENTS` 9 类支持 `workspace/prompts/<agent>[.lang].md` 用户自定义(novel_editor 仅内置);**语言机制**:非 zh 时在 System Prompt 末尾注入 "You MUST write ALL your output in {lang}",覆盖全部 15 语言(超出原版 4 语言,按用户要求补全);`seed_prompt_files()` 首次落盘供设置页编辑。
- `runner.py`:run_agent(读设置语言→加载 system→文本模型)与 run_agent_json(鲁棒 JSON 提取:```json 围栏/整体/首尾大括号/中括号四路尝试)。

### M3 AI 服务层 ✅
- `registry.py`:四类(text/image/video/tts)配置 CRUD+默认项+易好 Key 一键写入三条推荐(MiniMax-M3/agnes-image-2.5-flash/agnes-video-2.5-flash)+厂商模板(含本地换脸 http://127.0.0.1:5678)+模型候选。
- `text_client.py`:OpenAI 兼容 chat/completions(支持 Gemini OpenAI 端点/MiniMax/DeepSeek,兼容 reasoning 数组内容)。
- `image_client.py`:openai|gemini|qwen-image 走 images/generations;volcengine(Seedream,b64/url);agnes(同步或任务轮询 5s×120)。
- `video_client.py`:volcengine(Seedance contents/generations/tasks 轮询)/minimax(video_generation+query)/aliyun(Wan 异步任务)/agnes(同步或轮询);分辨率档位表对齐原版。
- `tts_client.py`:火山豆包双路径(seed-tts-2.0 流式→seed-audio base64 兜底)+按 narration_duration 自适应语速(0.5–2.0)。
- `face_swap.py`:health/swap_one(base64 出入,落 images/)。

### M2 核心骨架 ✅
- `config.py`:YIHAO_DATA_DIR/SQLITE_PATH/STORAGE_PATH/WORKSPACE_PATH 环境变量(对齐原版)、ffmpeg/ffprobe 三级定位(env→PATH→vendor)、/static 相对地址↔本地路径互转。
- `db.py`:**23 张表 DDL**(dramas 含小说五件套/episodes/characters+variants/scenes/props/三张 episode 关联/storyboards+两张关联/旁白四字段/comic_panels+三张关联/ai_service_configs/style_presets/sys_task/video_merges/assets/app_settings)+索引;**20 条风格种子完整复刻原版**(8 创作+6 通用+6 宣传,英文提示词逐字对齐,统一电影质感锚点);示例项目种子(《归乡的井》:4 角色/5 场景/1 道具/6 分镜/6 漫画格/完整剧本);启动时把中断任务清为 failed(对齐原版)。
- `i18n.py`:**15 语言** zh/en/ja/ko/fr/de/it/pt/es/vi/tr/ar/hi/id/th;zh 基准约 150 个 key,en 全量,其余语言覆盖高频项(缺失回退 en→zh);LANG_OUTPUT_NAME 供 Agent 语言指令。
- `taskmgr.py`:QThreadPool(6 线程)+sys_task 落库,processing→completed/failed 状态机,提交/完成回调/按集统计。
- `theme.py`:浅色/深色 QSS 全套(卡片/主按钮/输入/表格/滚动条等)。

### M1 计划与工程 ✅
- PLAN.md(功能盘点 F1–F24/里程碑 M1–M7/与原版差异声明);
- git init + remote `https://github.com/hzerther-hub/PySide6_drama`;
- requirements.txt(PySide6/requests/Pillow)+ .gitignore。

## 关键决策记录
1. **Python 3.10+ 要求**(用户指定):开发验证环境 Python 3.13.15;类型语法用 `from __future__ import annotations` 保持前向兼容。
2. **语言 15 种补全**(用户指定):UI 与 AI 内容统一 15 语言(原版 AI 内容仅 4);非内置语言靠显式输出指令注入。
3. **合并引擎**(用户指定):不重复造轮子,直接移植 easymerger 的"能无损绝不转码"三通道策略与容错回退;剧集拼接也走同一 auto_merge(带旁白时走 filter_complex 混音路径)。
4. **同款复刻**(用户指定):作为第 5 种创作目标放进新建下拉,流程=video-clone-lite 的四步(看懂原片→备料→逐镜重拍→拼接);分镜表/素材/首帧/视频全部存 dramas.metadata.clone,单镜可重做。
5. **视觉风格**(用户指定"主要是电影质感的"):20 条种子逐字复刻原版(每条 prompt 都带 cinematic 锚点),不做自定义扩展。
6. **字体**(用户指定"用 drama 中的字体文件"):原版无内置字体文件,采用其 CSS 字体栈策略;为跨环境一致额外打包 msyh.ttc 并内置加载。

## 2026-09-29(第 2 轮:服务对话框对齐原版 + Logo)
- **服务对话框重做**(用户给出原版截图):新增 `ServiceDialog` —— 模板快选芯片(Gemini/OpenAI/MiniMax/Agnes 官方等,点击自动填配置名称+服务商+Base URL+默认模型)、配置名称(存 remark)、服务商下拉(可编辑)、优先级(数值越高越优先,工作台取同类型最高优先级启用配置)、API Key、Base URL、**多模型标签编辑器 ModelChipsEditor**(首位默认高亮,点标签置顶,× 删除,输入框支持逗号/换行批量,新增按钮)、Temperature(留空跟随服务默认;填写则 text_client 强制覆盖,应对 kimi-k2 等强制温度模型)、底部 测试配置/取消/保存。模板模型清单逐字对齐原版推荐矩阵(gemini-3.8-flash / deepseek-v4-pro / doubao-seedance-2-0-mini-260615 等)。
- **AI 服务页**:新增「手动模板」卡片(文本/图片/视频/配音 四芯片直接打开对应服务类型的新增对话框),对齐原版第二张截图;修复服务列表构建时 findChild 找不到未入树控件的 bug 与 itemDoubleClicked 重复连接 bug;列表项显示 配置名称·模型·优先级·状态。
- **数据层**:ai_service_configs 幂等加列 `models`(JSON 多模型列表)与 `temperature`(REAL);registry.add_config 扩展 priority/models/temperature,同类型第一条配置自动设默认;default_config 改为优先级优先排序。
- **Logo(用户指定从原参考文件取出)**:复制原版 `frontend/app/public/icon-192.png`(橙色圆角方块白"易"字)为 `app/assets/logo.png`(另存 512/favicon),用于窗口图标 setWindowIcon 与顶栏 Logo 图;顶栏文案与窗口标题按用户要求**去掉 "PySide6" 字样**,只保留「易好短剧 / Yihao Shorts」(i18n 四语言 app_title 同步更新)。
- 截图:14-service-dialog.png(与原版界面逐项对齐)/ 15-main-with-logo.png / 16-settings-manual-tpl.png。
