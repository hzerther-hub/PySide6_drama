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

## 2026-09-29(第 3 轮:换脸工具页)
- **独立换脸工具页**(对齐原版 /tools/face-swap,用户要求"换脸的也要加入"):顶栏新增 🎭 换脸 导航;页面含服务健康检查(实测本机 5678 InsightFace 服务在线,显示 `ok · inswapper_128`)、导入目标图(多张卡片)、选择源脸照片、"替换图中所有脸"/"人脸增强"参数、逐张换脸(任务队列)、结果回填卡片预览、下拉选角色「存为角色形象」落库。
- **face_swap 客户端按原版 API 重写**:原 face-swap-service 真实接口为 `{source_url, template_url, source_index, swap_all_faces, face_enhance, save_local_path}`(source=脸来源,template=被换图),响应 `image_base64`;旧客户端字段名错误已修正(data URL 编码上传)。
- 附:工作台资产页的每角色「换脸」按钮沿用同一客户端,自动受益。
- 截图:17-face-swap-page.png。

## 2026-09-29(第 4 轮:换脸模型类型 + 导航中文化)
- **换脸成为第五类 AI 服务模型**(用户要求"模型那里加入换脸模型,可本地可远程"):registry.SERVICE_TYPES 增 `faceswap`,预设模板「本地 InsightFace (CPU) @127.0.0.1:5678」与「远程换脸服务(自填地址)」,首启自动种子本地配置;设置页第五个"换脸"标签(与文本/图片/视频/配音同待遇,连通测试=health)。
- **face_swap 客户端配置化**:`_resolve_base` 按显式 base > 指定 config_id > faceswap 默认配置 > 本地默认 解析服务地址,本地/远程协议一致。
- **两处换脸模型选择器**:工作台顶栏(文本/图片/视频/换脸/分辨率)与换脸工具页头部(显示 配置名 · Base URL,切换即重新健康检查);角色换脸与工具页换脸均按所选配置调用。
- **导航中文化 + 即时多语言**(用户要求"merger 改为中文,多语言时同步切换"):顶栏改用 i18n key(nav_projects/nav_merger/nav_faceswap),默认中文「项目/合并工具/换脸」;新增 MainWindow.retranslate(),设置切换语言后顶栏与标题**立即**跟随(整页内容重启后完全生效)。
- 截图:18-faceswap-model-selector.png / 19-nav-english.png(英文即时切换)/ 20-episode-face-model.png / 21-settings-faceswap-tab.png。

## 2026-09-29(第 5 轮:换脸归位资产角色卡 + 移除独立工具导航)
- **换脸移到资产·角色卡片**(用户澄清"换脸不是在这里,是要在资产里的角色那里"):新组件 `CharacterFaceSwapDialog` —— 三栏(当前形象 / 源脸照片(上传或从其他角色形象选) / 换脸预览)+ 参数(所有脸/增强)+ 顶部使用工作台所选换脸模型 + 「应用替换形象」确认后才写回 characters.image_url(取消不动)。工作台"视漫制作"每张角色卡的「换脸」按钮改为打开此对话框。
- **独立换脸工具页移除角色部分并从导航下线**:顶栏不再有"换脸"入口(nav 仅剩 项目);`face_swap_page.py` 保留为纯图片对图片通用工具(未注册导航)。
- **合并工具从导航移除**(用户:"merger 不应在这里,应出现在生成视频的拼接中,根本不要说用什么拼接"):顶栏只剩「项目」;无损合并/智能直通/对齐异类能力作为 `pipeline/merge.py` 的内部实现,只在「拼接导出 → 拼接所选」与「同款复刻拼接」中生效,UI 不出现任何技术名词。
- 截图:22-clean-nav.png / 23-assets-characters.png / 24-character-faceswap-dialog.png / 25-export-stage.png。

## 2026-09-29(第 6 轮:补齐 14 项差距,对齐原版 100%)
### 小说线(5/5)
1. **六维审校 UI**:原始内容面板新增「🔎 AI 六维审校」→ `ReviewDialog` 按维度显示 ✅/❌ + 问题清单 + 总评(写 review_json)。
2. **按指令改稿 UI**:指令输入框 + 「✏ 改稿」→ novel.edit_chapter。
3. **审校→修复循环**:`novel.write_chapter_with_review` 写章后自动审校,overall=fix 时带问题清单重写一轮;单章生成与批量续写均走此路径,完成后报告修复章数。
4. **策划与设定面板**:`NovelPlanDialog` 四标签(总纲/世界观/合约/分卷)可编辑保存 + 章节计划/主要角色只读展示。
5. **AI 封面**:NovelPlanDialog 内生成,写 dramas.thumbnail 并即时预览。
### 短剧线(9/9)
6. **@角色参考图注入视频**:shot_tools.collect_reference_images 从分镜文本解析 @角色名 → 形象图(去重≤4);video_client volcengine 以 reference_image 角色注入、agnes 多模态参考;文生与图生路径均生效。
7. **首帧图生成**:分镜行「🖼 首帧」→ shot_tools.generate_first_frame(风格前缀+video_prompt),标「首帧✓」。
8. **图生视频**:「🎬 图生」→ 无首帧自动先建,再图生视频(带参考图)。
9. **字幕烧录**:「T 字幕」→ 旁白/台词 srt → ffmpeg subtitles 滤镜 → composed_video_url。
10. **video_prompt 逐镜编辑**:分镜卡新增提示词行内编辑框。
11. **批量视频前确认**:镜头数/总时长/模型/分辨率/当前任务统计确认后才发。
12. **分辨率随厂商联动**:RESOLUTION_TIERS(volcengine 480p/720p、minimax 768P/2K、aliyun 至 1080P、agnes 720P/1080P)。
13. **模型选择记忆 + 集级锁定**:全局记忆四类选择与分辨率;集首次选用图片/视频配置后 🔒 锁定并回写 episodes.image/video_config_id,换选即更新锁定。
14. **角色造型变体**:角色卡「🎨 变体」→ VariantsDialog(新增标签+造型描述 → AI 提示词 → 变体出图 → 用作角色形象,默认标记)。**漫画资产真实页**:常规/漫画双 tab,漫画风格镜像图(comic_image_url)逐个生成与批量出图;漫画格「重新出图」即恢复原图(局部擦除标注交互后续按需加)。
- 截图 26~30。诚实备注:漫画"局部重绘(擦除区域)"需要交互式标注画布,本轮以整格重新出图替代。

## 2026-09-29(第 7 轮:补齐 A 类管理闭环 + D 类全局体验)
### A 类(项目/剧集/素材页管理)
1. **项目卡状态标记**:每卡右上可点状态徽标(待开始/进行中/已完成,彩色圆点图标),菜单切换写库;统计条"进行中"随之变化。
2. **排序真实可用**:最近更新 ↔ 按标题(原来按钮点了没反应);筛选改为直接按项目状态过滤。
3. **相对时间**:刚刚 / N 分钟前 / N 小时前 / N 天前 / M/D(替代原始时间戳);卡片重排为 封面+画幅角标+状态+更多。
4. **项目设置弹窗**(新 `asset_dialogs.ProjectSettingsDialog`):标题/简介/题材/画幅/视觉风格/面孔文化,保存入库。
5. **素材库全面可交互**:卡片点击打开 `AssetDetailDialog`(左预览可点击放大 ImageViewer + 右编辑:角色名/定位/样貌/妆造,场景地点/时间/描述/光影/标签,道具名/类型/外貌)+ 最终提示词面板(AI 生成/重新生成/复制/手动编辑)+ 造型变体入口 + footer(删除/上传/生成形象/保存/关闭);新增「＋角色/＋场景/＋道具」手工添加;空态提示。
6. **剧集卡**:标题**内联改名**(点击即可改)、状态菜单(带选中态圆点)、分辨率下拉(480p/720p/1080p)、新增 `NewEpisodeDialog`(标题+分辨率+说明)。
7. **宣传文案对话框**(内嵌项目页):平台+格式+补充说明 → 生成 → 标题/正文只读框 + 复制全文(替代原来只能看弹窗)。
### D 类(全局体验)
8. **全局 Toast**(`ui/toast.py`):右上角浮层 info/success/warning/error 四级,堆叠最多 5 条,自动消失,不阻塞,跟随窗口 resize 重排;**错误友好化 `map_error`** 对齐原版八类优先级短路(网络/超时/鉴权/限频/invalid temperature/内容审核/5xx/API error 提取/原文兜底)。
9. 全量替换 20+ 处 `QMessageBox.warning(str(err))` → toast;保留确认类(question)弹窗。
10. **Loading 基座**(`ui/loading.py`):`Spinner`(纯 QPaint 旋转)+ `BusyButton`(内嵌 spinner/禁用态);TaskManager 增加 `busy_changed` 信号,工作台顶栏 `status_lab` 显示忙碌提示。
### 顺带修复
- theme.py 重复 `apply_theme` 定义清理;settings_dialog 死代码(`self.pages[2]=...`)删除;两处 QFormLayout 双重父布局警告修复。
- 截图 31~37(含 toast 三色演示与错误友好化验证)。

## 2026-09-29(第 8 轮:文本框撑满 + Ctrl+L AI 智能修改)
- **文本框撑满**(用户截图标注):原始内容 / AI 改写两个主编辑区由固定 360px 改为 Expanding 策略并占满剩余高度(去掉外层 QScrollArea 包裹,自身内部滚动),实测 1120×600 铺满工作区;新增 `FILL_PANELS` 区分撑满型与滚动型面板。
- **Ctrl+L AI 修改**(对齐原版 episode.vue 的 @keydown.ctrl.l + aiEdit):
  - 三种模式——**选中若干行→改写选中片段**、**不选→在光标位置插入**、勾选「整章处理」→输出整章;对话框显示模式标签与选中片段预览(超 400 字截断)。
  - 提示词拼接与输出规则逐条对齐原版 RULES(只输出结果文本/不重复原文/保持未涉及部分原样)。
  - 回填逻辑:selection=前缀+新片段+后缀;insert=按原版规则补空行;chapter=整章替换;并落库 + toast 提示。
  - 快捷键 Ctrl+L 与 Cmd+L 双注册;两个编辑框工具条各加「✨ AI 修改 (Ctrl+L)」按钮。
- **连贯性上下文**(用户要求:改写/插入须带前情,不能生成不合理文字):`_context_parts()` 在每次改写前自动拼接——作品设定(总纲/世界观/故事合约)、文风要求、本章计划(标题/目标/事件/钩子)、**前三章摘要(每章结尾 600 字,按章号倒序)**,并追加 4 条连贯性硬规则(不得与设定/前情冲突、不得写前文未发生的事、人称时序称谓文风一致、不输出无关内容)。
- 截图 40(撑满+Ctrl+L 按钮)/ 41(AI 修改对话框)。

## 2026-09-29(第 9 轮:顶栏语言按钮)
- 语言按钮移到最右(顺序:项目 → 主题模式 → 设置 → 🌐 语言),文案由「界面与 AI 内容语言」精简为「语言」;新增 i18n key `lang_short` 并补齐 15 语言(语言/Language/言語/언어/Langue/Sprache/Lingua/Idioma/Idioma/Ngôn ngữ/Dil/اللغة/भाषा/Bahasa/ภาษา)。
- 截图 42(中文)/ 43(英文即时切换)。

## 2026-09-29(第 10 轮:项目卡整卡可点)
- 用户反馈"点示例卡片没反应":原实现只有「···」菜单里的"打开项目"入口,整卡不可点(与原版 card click 行为不一致)。现 ProjectCard 整卡可点(指针光标 + tooltip + mousePressEvent 打开项目),点在右上状态徽标/更多按钮时不误触发(按钮 pressed 置位标记拦截)。
- 截图 44(QTest 模拟点击卡片验证跳转项目页)。

## 2026-09-29(第 11 轮:修复 emoji 空白按钮)
- 用户截图反馈剧集卡上有一个空白按钮:该处应为「🗑 删除本集」,但 **🗑 等彩色 emoji 在微软雅黑(msyh.ttc)中无字形**,Qt 渲染为空白方块。
- 用 QRawFont.supportsCharacter 实测全项目符号:15 个彩色 emoji(📖🎬📚📣🎞📁🌓🌐🖼🔊🔎🎨🔄📋🗑)缺字形;几何/箭头符号(▶✏➕⚡✕●○⋯·—⏳✅❌↻)均正常。
- 全项目 46 处 emoji 替换为可靠 Unicode 符号(§▷▤◈▦◐◎▣♪◇◑↻✕),删除按钮改为红色文字「删除」双保险。
- 截图 45~47(启动台/剧集列表/工作台)。

## 2026-09-29(第 12 轮:同步原版 xiaoshuo 新增功能,8 项 100% 复刻)
> 依据 `git diff dc86ba8..HEAD`(原版 2026-09-29 ~ 10-01 共 20+ 提交)逐项复刻。
### P0
1. **参考图序号统一(正确性 bug 修复,原版 67adf7a)**:新增 `pipeline/refs.py` 作为单一真相源 `build_shot_reference_list()`——权威顺序 **角色→场景→道具**(角色排首位:后端缺 first_frame 时会用 [0] 兜底锁脸),按 imageUrl 去重,截断上限 Wan 3.0 为 10 张 / 其他 9 张。`get_shot_reference_images()` 与 `get_shot_reference_index_map()` 均由它派生,保证 `@图片N ≡ reference_image_urls[N-1]`;`resolve_video_prompt_refs()` 把 `@名字` 替换为 `@图片N名字`(名字按长度降序匹配避免前缀误命中)。`shot_tools.collect_reference_images` 由「正则猜 @名字」改为按 storyboard_id 走该真源。
2. **项目设置新增字段(原版 72736af)**:创意描述 textarea + 「不需要创意描述」复选框 + 集数(1-999);已有第 1 集时创意描述与复选框**锁定**;集数=1 或已达总数时「添加一集」按钮隐藏并提示。
3. **小说章节自动起名(原版 a41c224 + 8f3213d)**:`gen_chapter_title()`——上下文=总纲 400 字 + 前三章摘要(各 200 字)+ 本章节选 2000 字,输出清洗三级(取首行→去「第N集」前缀→去引号/井号→截断 20 字),写回 `episodes.title` 与正文首行 `# <name>`;写章路径 `_save_with_title()` 自动识别首行章节名并写回;UI 在缺章节名时显示「✎ 章节名」按钮。
### P1
4. **资产下载(原版 72736af)**:新增 `core/download.py`,文件名规则对齐原版(资产名[_变体].png / 第NN镜[_标题].mp4 / <项目名>_第N集.mp4),非法字符清洗、扩展名推断、400MB 上限、重名自动加序号;UI 接入素材详情弹窗「↓ 下载原图」、分镜行「↓」、导出页成片「下载」。
5. **RunningHub 视频适配器(原版 b78f9bf)**:openapi v2 协议,模型 `seedance-2.5`(realPersonMode 默认 true,显式 false 才关)/ `wan3.0-video(-prime)`;首帧图 unshift 首位保锁脸;归一化(duration 2-30、resolution 2K→wan 收敛 1080P、adaptive→自适应);`@图片N`→`图N` 提示词转换;容忍性响应解析(5 处 taskId 兜底 + 8 层递归找 mp4,优先按字段名顺序避免封面图抢先);注册进 settings 预设与易好快捷配置。
### P2
6. **运镜全链路(原版 ca55b49)**:纯提示词层——storyboard_breaker 注入 22 词运镜库 + 按段落类型选择(铺垫/对话/情绪/动作/爆点/悬疑)+ 子镜头 description 写法硬规则(运镜写在【镜头N】开头,再写画面、再写台词);prompt_generator 注入 video_prompt 运镜硬规则(每 3 秒段必须含「起始景别+运动方式+速度」,禁止纯静止镜头)+ 运镜五分类词库 + 速度副词 + 慢动作例外。
7. **换脸面板升级**:批量换脸(基础形象+全部变体,单张失败不中断)、批量下载结果、恢复原貌(首次载入快照)。
8. **默认视频模型优先级(原版 e653b75+b78f9bf)**:易好快捷配置改为 MiniMax 98 > Wan 3.0 97 > Seedance 96 > RunningHub 95(Seedance 垫底);内容语言选择器由 4 语言下拉改为 **15 语种 5 列网格**(对齐原版 lang-picker-grid)。
- DB 迁移:storyboards +title/location/time/result/atmosphere/sound_effect/description/subtitle_url/setting_tags/reference_images/deleted_at;dramas +creative_description/skip_creative/total_episodes;ai_service_configs +settings。
- 截图 48~51。

## 2026-09-29(第 13 轮:同步原版 73b3339)
- **「章节名」按钮搬到项目页剧集卡**(原版 73b3339):从工作台原始内容工具栏移除,改到项目页剧集卡标题下方——缺章节名(标题为空或仅「第N集」占位)且有正文时显示虚线胶囊「✎ 章节名」,已有名字的集不显示;点击后原地写回并 toast 提示,卡片自动刷新(按钮消失)。
- **正文标题行反向提取**(不调模型):新增 `extract_title_from_content()` 支持两种写法——markdown 标题 `# 归乡的井` 与 `第1集 县医院的消毒水味`;清洗书名号/引号/尾部标点;超过 30 字视为正文不当作标题(实测:两种写法均正确提取,超长行与普通正文行均返回空)。
- `gen_chapter_title()` 改为**优先反向提取**(返回 source='content',省一次模型调用),提取不到才走 AI(返回 source='ai');仅在标题为占位时才提取,避免覆盖用户已改好的名字;UI 按来源给出「已提取章节名:」/「章节名已写入:」两种提示。
- 截图 52(剧集卡章节名按钮:EP01 已有名字不显示 / EP99 缺名显示)。

## 2026-09-29(第 14 轮:同步原版最新 4 提交,基线推进到 a6a47dc)
> 原版从 73b3339 推进到 a6a47dc,新增 4 项,全部复刻。
### 1. 残缺分镜自动补全(daa17d0)
- 新增 `pipeline/storyboard_repair.py`:**判定**——`image_prompt` 为空 → 缺 image_prompt;`storyboard_characters` 零行且 description 含 `@角色名`(正则 `/@([^\s@，。；：、!！?？)）]{1,20})/g` + 剥括号注释,如 `@王德厚（王父）`→`王德厚`)→ 缺 character_links;**修复**——逐个调 prompt_generator 补 image_prompt + character_ids + prop_ids + scene_id;**成败以落库为准**(不信 agent 自述):要求 image_prompt 非空且关联行数 > 0 才算完成。
- UI:分镜页「⟳ 自动补全 N」按钮,**仅残缺时显示**(无残缺自动消失不占位),运行时禁用并显示进度;完成 toast 区分全成功/有失败两种。
### 2. 写作红线 1/2/3/4/5/7 + 章节名沿用 + 上一章衔接(101759d)
- **写作红线**:`NOVEL_REQUIRED_STEPS = [1,2,3,4,5,7]`(6 卷战略为节拍层保持可选),`check_novel_redlines()` 逐条判定——1 标题+简介 / 2 总纲 / 3 世界观(era+location,读**落库的** novel_meta 而非向导内存草稿)/ 4 故事合约(pov+rules 非空+tones 非空)/ 5 角色表有行 / 7 章节规划非空;`assert_novel_ready()` 后端兜底拒绝,`missing_steps_text()` 给出「1(项目设定)、2(总纲)…」。
- UI 前置守卫:设定未齐时禁用「AI 生成小说 / 批量写」并 toast + tooltip 提示缺哪几步;短剧/漫画项目不受红线约束。
- **章节名沿用清单**:`write_chapter` 提示词改为「章节名优先沿用【本章计划】里的标题(原样使用,不要改写);无计划标题时再自行起名」——保证重新生成后章节名稳定不漂移。
- **上一章衔接修复**:`prev` 查询加 `content IS NOT NULL AND content != ''` 过滤(原版 bug:`lt` 过滤后按升序取第一行拿到的是**第 1 集**,重写第 5 章时衔接第 1 章结尾导致跨章断裂)。
### 3. 换脸健康检查(09e76b8)
- `face_swap.health()` 改为读 `data.local.ok` 并以 `data.ok` 兜底(新版本地/远程嵌套 `{local:{ok},remote:{ok}}`,旧版扁平 `{ok}`),修「本地服务正常但下拉永远显示未启动」的前端字段路径 bug。
### 4. 项目级内容语言(a6a47dc)
- 新增 `dramas.language TEXT DEFAULT 'auto'`('auto'=跟随全局,其他=固定该语言);`config.resolve_content_language(drama_id)` 三段式优先级:显式传入 > 项目覆盖 > 全局设置。
- **全链路贯通**:rewriter / extractor / storyboard / prompts_gen / comic / novel 六类 pipeline 的 agent 调用全部新增 `lang` 参数;工作台 `EpisodePage.load()` 进入项目时按项目语言 `set_language()`,并把 `_drama_lang` 传给所有 UI 调用点。
- UI:项目设置弹窗新增「内容语言」下拉(跟随全局 + 15 语种),新建项目对话框同步。
- 截图 53(分镜页「⟳ 自动补全 6」按钮)。

## 2026-09-29(第 15 轮:同步原版 26c7d00 + 0114f24,基线推进到 0114f24)
> 对齐源仍为 E:\xiaoshuo(gitee huobao),原版从 a6a47dc 推进到 0114f24。
### 1. 供应商模板胶囊 → 与「服务商」合并为单一下拉(26c7d00)
- 原版解决「上方一排模板胶囊 + 下方供应商下拉,两处都在选供应商,容易困惑」。现**移除顶部胶囊行**,合并为一个「服务商」下拉:选项显示模板 label(如「Agnes 官方」「MiniMax 官方」),选中即自动填入 Base URL + 默认模型 + 配置名称(原胶囊行为);末尾附「自定义…」,选中时展开原始服务商标识输入框(隐藏式,不占默认行)。
- 新建时默认选中首个模板并主动填充一次(下拉首项不触发 currentIndexChanged);编辑已有配置时命中模板则选中对应项,否则落到自定义并回填原 provider。
- 顺带修一个旧 bug:`_FlowLayout` 原本是伪流式(内部 QHBoxLayout 不换行),模型标签一多就**文字重叠**;改为基于 move/resizeEvent 的真流式布局,标签按可用宽度自动换行(实测 4 个标签分两行渲染,重叠消失)。
### 2. 小说设定闸门消息压缩(0114f24)
- `assert_novel_ready()` 消息由「小说设定未完成(缺步骤 X),请先在「策划与设定」补齐后再生成」压缩为 **「小说设定未完成，请先补齐步骤 1、2、3」**(24 字,原版约束 40 字内),只报步骤号,名称由 UI 侧翻译补全,避免长文本在错误提示里被截断。
- 截图 54/55(合并后的服务商下拉 + 真流式模型标签)。

## 2026-09-29(第 16 轮:Agent 配置补齐 Skills + 15 语言全量同步)
> 用户指出「生成小说/短剧的配置是否完成?注意是多语言的」——核查发现**未完成**:原版是 10 提示词 × 15 语言 = 150 文件 + 11 技能 × 15 语言 = 165 文件,而本版只有中文内置提示词,**Skills 一个都没有**,设置页也无 Skills 面板。
### 配置文件全量同步(315 个)
- `workspace/prompts/` 150 个:`<agent>.md` + `.en/.ja/.ko/.fr/.de/.it/.pt/.es/.vi/.tr/.ar/.hi/.id/.th` × 10 个 agent
- `workspace/skills/` 165 个:11 个技能 × 15 语言
  - comic-board / extractor / novel-writer / promo-writer / script-rewriter / storyboard-breaker
  - prompt-generator 下 4 个子技能:character / scene / prop / video-prompt
  - storyboard-breaker 下子技能:fight-cinematography
### 技能加载器(`agents/prompts.py`)
- `AGENT_SKILL_MAP` 按目录前缀挂载(对齐原版),`list_skills()` 同时识别**技能目录自身**与**子目录**(如 fight-cinematography)
- `load_skills()` 把技能正文以 `## Skill: <name>` 段落拼进 instructions,语言回退链 `<lang> → en → zh`
- `load_prompt(..., with_skills=True)` 统一组装:多语言文件 → 技能正文 → 非中文时追加显式输出语言指令
- 新增 `load_skill / save_skill / reset_skill` 供设置页编辑
- 实测:15 种语言提示词全部有内容(均 > 500 字符),`th` 语言 storyboard_breaker 含 2 个技能共 20740 字符
### 设置页 Agent 配置(对齐原版截图)
- 左侧列表加**技能数量徽标**(剧本改写 [1]、分镜拆解 [2]、提示词 [4] …)
- 右侧改**双标签:System Prompt / Skills**
  - System Prompt:路径提示 `workspace/prompts/<agent>[.<lang>].md` + 编辑器 + 保存/恢复默认
  - Skills:左技能列表 + 右正文编辑器(显示 `skills/<id>/SKILL[.<lang>].md` 路径)+ 保存/恢复默认
- 顶部语言下拉切换时,两个标签的内容与路径同时按语言切换
- 截图 57/58/59(System Prompt 标签 / Skills 标签 / 日语技能路径)。

## 2026-09-29(第 17 轮:AI 服务缺失拦截 + 自动更新)
### A. AI 服务未就绪直接提示(用户要求:不能"不声不响的没有结果")
**问题实测**:
1. 配置存在但 **API Key 为空**时,客户端仍会真的发请求 → 拿到 401 才报错,白跑一次网络;
2. 完全未配置时只在后台任务失败后弹 toast,用户看不到、也不知道去哪配;
3. `map_error` 无「未就绪」分支,原文直传。
**修复(三层防护)**:
1. `ai/registry.py` 新增 `check_ready()` / `readiness()` / `missing_services()` / `NotConfigured`:
   覆盖**未配置 / 全部停用 / 缺 API Key / 缺模型名 / 缺 Base URL** 五种情况,每种给出明确原因;
   `local-faceswap` 等本地 provider 豁免 Key 检查。
2. **四个 AI 客户端入口改为 `check_ready()`**:text/image/video/tts 在发请求前校验,
   缺配置时抛 `NotConfigured` 而**不发空请求**(实测:空 Key 的图片生成在网络调用前即被拦下)。
3. **`TASKMGR.submit()` 统一拦截**(18 类任务 → 所需服务映射):未就绪时弹模态提示
   (「✗ 图片服务未就绪 — 配置「agnes」缺少 API Key / 影响:角色形象·场景·道具·漫画格·封面 / 请到「设置 → AI 服务」补全」),
   **不创建 sys_task 记录**(不留下"跑了没结果"的空任务),并回调通知 UI。
4. **主窗口全局横幅**:缺 text/image/video 任一即显示橙色横幅「⚠ AI 服务未配置完整(缺:文本、图片、视频) — 依赖模型的操作会无法执行,点击此处去「设置 → AI 服务」补全」,点击直达设置,保存后自动复查刷新。
5. `toast.map_error` 增加「未就绪/未配置」最高优先级分支。
**顺带修一个潜伏崩溃**:37 处 `def done(tid, result, err)` 的参数 `err` 遮蔽了模块级 toast 函数 `err`,
一旦走进错误分支就 `TypeError: 'RuntimeError' object is not callable`。统一重命名为 `error`。
### B. 自动更新
- 新增 `core/updater.py`:GitHub Releases 检查(语义化版本比较,`v1.2.10 > v1.0.0`)、
  zip 下载(流式+进度)、解压、单层目录下钻、**备份后覆盖**(只覆盖源码/配置类文件,不动二进制与
  data/workspace)、重启拉起;支持 `PYDRAMA_UPDATE_FEED` 覆盖更新源。
- 「关于更新」分区重做:当前版本 + **启动时自动检查更新**开关(默认开)+ 检查更新按钮 +
  发现新版本时显示 Release notes + 「立即下载并更新」+ 进度条,完成后询问重启。
- 启动后 3 秒静默检查,有新版以 toast 提示(可在设置关闭)。
- 截图 60(AI 缺失横幅)/ 61(拦截弹窗)/ 62(关于更新)。

## 2026-09-29(第 18 轮:全面 bug 排查 + 版本升至 1.1.0)
### 排查结果
- **语法**:全量 `py_compile` 发现并修复 `ui/merger_tool_page.py:182` 缩进错误
  (批量插入 toast import 时误插到函数体外,导致整个模块无法导入 —— 该页是「无损合并工具」入口)。
- **导入**:pkgutil 遍历 app.* 全部模块,导入失败 0。
- **运行时冒烟**:启动台 / 项目页 / 工作台六阶段(raw·rewrite·assets·storyboard·comic·export)/
  设置六分区(AI服务·通用·风格预设·Agent配置·存储·关于更新)/ 5 种语言切换 —— **0 错误**。
- **数据一致性**:孤儿分镜、孤儿角色关联、指向不存在集的场景、空内容分镜、僵死 processing 任务 —— **全部为 0**。
- **静态分析**:lambda 闭包、索引越界、可疑未定义名逐项核查,均为误报
  (lambda 均用默认参数绑定循环变量 `lambda _=False, i=r["id"]:`,`updater` 的 `entries[0]` 有 `len==1` 保护)。
- **逻辑验证**:参考图单一真相源(角色优先·序号映射·@图片N替换)、ref 上限(Wan 10 / 其他 9)、
  章节名清洗边界(空串/超 30 字/两种写法/尾部标点)—— 全部符合预期。
### 版本
- `APP_VERSION` 1.0.0 → **1.1.0**(功能已显著超过初版,便于自动更新区分)。

## 2026-09-29(第 19 轮:同步原版未提交批次 49 文件 +3269 行)
> 原版有一批**未提交**的本地改动(工作区脏),主题是「长篇小说(999 章量级)生产链路的可靠性 + 可观测性」。全部复刻。
### 配置文件
- 重新同步 prompts(150)与 skills(165),新增 **fight-cinematography**(高速打斗运镜手册:10 条机位公式 + 4 种速度注解,15 语言)与 **novel_editor**(第 10 个 Agent,15 语言)。
### P0 可靠性
1. **LLM 挂起超时**:`AI_LLM_TIMEOUT_MS`(默认 300s)作用于文本请求 —— 服务商"接受连接但永不响应"不再让任务永远卡 processing。
2. **任务阶段可见性**:`sys_task.params.stage` 写入 writing→reviewing→repairing/splitting,新增 `taskmgr.set_stage/get_stage`。
3. **写后校验**:`write_chapter_with_review` 以 `episodes.content` 为准,`<200` 字符即抛错(防"界面显示完成但章节空着"),上层可重试。
4. **分镜拆解改后台任务**:`split_storyboards_bg()` 走任务队列 + **防重入**(同集已有 processing 任务则拒绝)+ **垃圾分镜清理**(description<50 且 image_prompt<30 且 video_prompt<60 的空壳行,级联清关联表)+ 假完成校验(0 分镜抛错);UI 6 秒轮询,按钮显示"后台运行 5-10 分钟"。
5. **批量建集**:`bulk_create_episodes(titles/count 1-999, target_words, resolution)`,start_num 取已有最大集号+1。
6. **防误覆盖**:`batch_write_chapters(force=)` 默认**已有正文的章节整批拒绝**并提示"重写请点「重写已完成章节」";UI 侧 `批量写本章及后续` 语义重定义(本章未写完→确认重写本章;已完成→取后续无正文的前 10 章),并新增 `重写已完成章节(force=True)` 按钮。
### P1 可观测性
7. **伏笔台账**:LCS≥5 去重(实测"苏晓晴对李安全变化的怀疑"vs"…越来越深"命中 12 字合并;"感情线"vs"持续关注"正确保留)、`OPEN_LEDGER_CAP=40` stale 封顶、`backfill_ledger_chapters` 前 4 字回填埋设章号、按埋设章号倒序注入最近 8 条、`toggle_ledger` 可交互勾选(乐观更新+失败回滚)。
8. **审校明细 + 全书审校清单**:`ReviewPanelDialog`(逐条勾选,仅本地标记)、`ReviewSummaryDialog`(逐章列出问题,可跳转)。
9. **整章朗读**:`read_aloud()` 按句切 600 字硬切超长句,逐块 TTS 后拼 MP3(帧自包含可连续播放)。
10. **任务收尾按产出归位**:`settle_interrupted_tasks()` 启动时把 processing 任务按"产出是否已落"判 completed/failed(不再一律 failed)。
11. `storyboard_count` 随剧集卡一次 groupBy 带出,消除 N+1。
### P2 UI
12. **三段式进度条**(成功绿/失败红/进行中)+ 图例(百分比/进行中/成功/失败)+ 每章阶段显示。
13. **剧集卡制作阶段条**:按产物判定(正文<200→剧本<100→资产/分镜→分镜→成片),五段绿/蓝/灰;**字数进度** `X / Y 字`,低于 80% 标琥珀色,否则"未写"。
14. 分镜拆解接后台任务 + 轮询。
### 验证
- 冒烟:启动台/项目页/工作台六阶段/批量进度面板/审校明细/全书清单/伏笔台账/审校摘要/垃圾清理/批量建集越界 —— **0 错误**。
- 逻辑单测:阶段判定 5 态全对、LCS 去重 4 例全对、朗读分块(12/600/103)、中断任务收尾(1 completed/2 failed)、垃圾清理 4 条。
- 截图 63(阶段条+字数)/ 64(小说工具条)/ 65(批量进度)。
