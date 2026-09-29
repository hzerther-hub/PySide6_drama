# PySide6 重写「易好短剧」实施计划

> 目标:用 **PySide6(Python + Qt6)** 桌面单机应用,100% 复刻「易好短剧」(Yihao Drama)全部功能。
> 依据:`docs/易好短剧-工具分析.md`(黑盒实测)+ `E:\xiaoshuo` 源码(TypeScript 全栈)分析。
> 所属仓库:https://github.com/hzerther-hub/PySide6_drama
> 规则:**一项一项完成;每完成一项在本文档勾选并写过程记录;每个阶段做一次 git 提交。**

---

## 0. 对原版的功能盘点(100% 覆盖清单)

| # | 原版功能 | 重写实现方式 |
|---|----------|--------------|
| F1 | 项目启动台:统计/筛选(全部·待开始·进行中·已完成)/搜索/排序/删除 | `ProjectsPage` |
| F2 | 新建项目:4 种创作目标(写小说/生成短剧/生成漫画/宣传营销) | `NewProjectDialog` |
| F3 | 14 种视觉风格(创作 8 + 通用 6)、画面比例、面孔文化、宣传平台×6、输出格式×6 | 常量表 + 种子数据 |
| F4 | 项目页:剧集列表(状态/进度/分辨率/增删)+ 项目级素材库(角色/场景/道具,跨集复用) | `ProjectPage` |
| F5 | 阶段① 原始内容:粘贴原文/目标字数/文风/AI 生成小说/批量写本章及后续 | `EpisodePage` step1 |
| F6 | 阶段② AI 改写:格式化剧本(`## S01|内外景·地点|时间`),重新改写 | script_rewriter Agent |
| F7 | 阶段③ 视漫制作:角色/场景/道具提取去重、最终提示词、出图、重绘、上传、换脸、漫画资产 | extractor + prompt_generator + 图片客户端 |
| F8 | 阶段④ 分镜:镜头级拆解、批量补齐提示词、批量视频、任务统计(生成中/完成/失败)、单镜重绘 | storyboard_breaker + 视频客户端 |
| F9 | 阶段⑤ 漫画:漫画格(画面/台词/构图/旁白≤50字)、批量出图、拼接长图 | comic_board + Pillow 拼接 |
| F10 | 阶段⑥ 拼接导出:镜头勾选、FFmpeg 拼接(+旁白混音)、成片列表/播放/删除/标记完成 | ffmpeg 子进程 |
| F11 | 设置·AI 服务:易好快捷配置 / 文本·图片·视频·配音四类多供应商(OpenAI兼容/Gemini/火山/Agnes/MiniMax/阿里Wan/qwen/本地换脸)、连通测试、启停 | `SettingsDialog` + `ai/` 客户端 |
| F12 | 设置·通用:**界面语言 15 种 + AI 内容语言 15 种(补全,原版仅 4 种)**、主题浅/深 | `core/i18n.py`(15 语言) |
| F13 | 设置·风格预设:启用/排序/编辑 | style_presets 表 |
| F14 | 设置·Agent 配置:10 个 Agent System Prompt 在线编辑/重置/语言变体 | workspace/prompts 机制 |
| F15 | 设置·存储位置 / 关于更新(版本、检查更新) | 存储统计 + 更新检查 |
| F16 | 任务面板:统一任务队列(sys_task),状态流转 processing→completed/failed | `core/taskmgr.py` |
| F17 | TTS 旁白配音(火山豆包 seed-tts,含语速自适应) | `ai/tts_client.py` |
| F18 | 换脸(本地 InsightFace 服务 127.0.0.1:5678,health/单张/落库) | `ai/face_swap.py` |
| F19 | 小说线:策划(总纲/世界观/合约/卷/章)、逐章生成、六维审校、按指令改写、导出整本 | novel_* Agents |
| F20 | 宣传线:按平台+格式生成文案 | promo_writer |
| F21 | 多语言内容:Agent 输出语言跟随设置(15 种) | prompt 语言变体 + 显式语言指令 |
| F22 | 数据:SQLite 单文件(20 张表)、媒体文件本地存储、上传图片/视频 | `core/db.py` |
| F23 | **无损视频合并工具(并入 golanse/easymerger 逻辑)**:ffprobe 参数一致性检测(分辨率/编码/帧率/Profile/采样率)→ 三通道(全一致 `-c copy` 秒合;视频一致音频不同→智能直通只统一音频;少数异类→一键对齐多数派后无损合并)+ 容错回退(诊断码流→换中间容器→重编码)+ 批量文件夹队列 | `pipeline/merge.py` + `ui/merger_tool_page.py` |
| F24 | **同款复刻(并入 liangdabiao/video-clone-lite 逻辑)**:新建项目第 5 种创作目标「同款复刻」——上传参考视频+产品照片(+可选出镜照片)→ AI 看懂原片输出分镜表 → 生成新主角/产品资产 → 逐镜重拍(首帧图→图生视频)→ 按原片节奏无损拼接成片;中间产物逐镜保存,单镜可重做 | `pipeline/video_clone.py` + 新建对话框/工作台分支 |

## 1. 技术选型

- Python 3.10+ / PySide6 6.6+(LGPL)
- 数据:sqlite3(标准库,WAL)
- HTTP:`requests`
- 图像处理:Pillow(缩略图/漫画拼接)
- 视频:ffmpeg/ffprobe 子进程(优先 PATH,可设置覆盖)
- 后台任务:QThreadPool + QRunnable,状态落 sys_task 表
- 结构:单包 `app/`,入口 `app/main.py`

## 2. 里程碑(逐项执行,勾选制)

### M1 计划与工程初始化
- [x] P1.1 编写本计划文档 PLAN.md
- [x] P1.2 git init + 关联 remote `https://github.com/hzerther-hub/PySide6_drama`
- [x] P1.3 requirements.txt / .gitignore / README.md

### M2 核心骨架
- [x] P2.1 `core/config.py`:数据目录/DB 路径/媒体目录/ffmpeg 定位
- [x] P2.2 `core/db.py`:23 张表 DDL(对齐原 schema)+ 种子(风格预设 20 条完整复刻/示例项目/默认 Agent 提示词落盘)
- [x] P2.3 `core/i18n.py`:**15 种语言**翻译表 + 语言注册 + tr() 切换(zh 兜底)
- [x] P2.4 `core/theme.py`:浅色/深色 QSS + drama 字体栈
- [x] P2.5 `core/taskmgr.py`:统一任务管理(创建/轮询/状态回写/完成回调)

### M3 AI 服务层
- [x] P3.1 `ai/registry.py`:四类服务配置 CRUD + 默认选择 + 连通测试
- [x] P3.2 `ai/text_client.py`:OpenAI 兼容 chat(含 Gemini 原生兼容)
- [x] P3.3 `ai/image_client.py`:openai / gemini / volcengine / agnes / qwen-image 适配(提交+轮询+落盘)
- [x] P3.4 `ai/video_client.py`:volcengine(Seedance) / minimax / aliyun(Wan) / agnes(提交+轮询+下载)
- [x] P3.5 `ai/tts_client.py`:火山豆包 seed-tts(双路径 fallback)+ 语速自适应
- [x] P3.6 `ai/face_swap.py`:本地换脸服务客户端(health/swap one)

### M4 Agent 层(10 个,提示词对齐原版 DEFAULT_PROMPTS)
- [x] P4.1 `agents/prompts.py`:10 Agent 默认 System Prompt(zh)+ **15 语言变体机制**(按设置语言加载/注入输出语言指令)
- [x] P4.2 `agents/runner.py`:Agent 执行器(system+user→文本模型→工具式 JSON 结果解析)

### M5 流水线
- [x] P5.1 `pipeline/rewriter.py`:原文→格式化剧本
- [x] P5.2 `pipeline/extractor.py`:角色/场景/道具提取+与已有资产去重
- [x] P5.3 `pipeline/storyboard.py`:剧本→分镜(镜号/景别/运镜/台词/时长/video_prompt)
- [x] P5.4 `pipeline/prompts_gen.py`:角色三视图/场景三层构图/道具单品图提示词
- [x] P5.5 `pipeline/comic.py`:漫画格拆解+旁白
- [x] P5.6 `pipeline/novel.py`:策划/逐章写作/六维审校/片段改写/导出整本
- [x] P5.7 `pipeline/promo.py`:平台宣传文案
- [x] P5.8 `pipeline/merge.py`:FFmpeg 拼接(分辨率统一/无音轨补静音/旁白混音)
- [x] P5.9 `pipeline/stitch.py`:漫画长条图拼接(Pillow)
- [x] P5.10 `pipeline/video_clone.py`:同款复刻(video-clone-lite 四步:看懂原片→备料→逐镜重拍→拼接)

### M5b 无损合并增强(easymerger 逻辑)
- [x] P5.11 `pipeline/merge.py` 增强:ffprobe 参数检测(分辨率/编码/帧率/Profile/采样率)+ 三通道决策(无损/智能直通/对齐异类)+ 失败回退链
- [x] P6.9 `ui/merger_tool_page.py`:独立工具页(导入文件夹/检测结论/一键对齐异类/合并输出)

### M6 UI
- [x] P6.1 `ui/main_window.py`:顶栏(Logo/导航/主题/语言/设置)+ QStackedWidget + 状态栏 + 复刻工作台
- [x] P6.2 `ui/projects_page.py`:启动台(统计/筛选/搜索/卡片/更多菜单)
- [x] P6.3 `ui/new_project_dialog.py`:新建(5 目标/风格/比例/面孔文化/平台/格式/复刻素材)
- [x] P6.4 `ui/project_page.py`:剧集列表+素材库
- [x] P6.5 `ui/episode_page.py`:六阶段工作台(侧栏步骤导航+顶栏模型选择)
- [x] P6.6 `ui/settings_dialog.py`:六分区设置(**语言 15 种补全**/AI 服务/风格预设/Agent 配置/存储/关于)
- [x] P6.7 `ui/task_panel.py`:任务列表面板
- [x] P6.8 `ui/widgets.py`:卡片/标签/头像/图片预览等通用组件

### M7 收尾
- [x] P7.1 种子示例项目(《归乡的井》剧本数据,开箱即有内容)
- [x] P7.2 运行冒烟:启动/新建项目/各页切换/设置语言 15 种切换(视觉验收 13 张截图,修复资产页空白/空态/字体三问题)
- [x] P7.3 截图存 docs/screenshots-pyside6/(13 张,打包 msyh.ttc 字体后中文渲染正常)
- [x] P7.4 README(中/英/日/韩四语言,含 15 语言支持说明)+ 过程记录 PROGRESS.md
- [ ] P7.5 git 提交推送

## 3. 与原版的有意差异(界面可调整授权范围内)

1. Web 多页路由 → 桌面单窗口 + 左侧导航(布局调整,信息架构不变);
2. 「使用引导」(driver.js 遮罩)→ 简化为各页顶部提示条;
3. 「关于更新」自动换包 → 版本展示 + 检查 GitHub Releases(桌面重写不做自更新);
4. **AI 内容语言从 4 种补全到 15 种**(用户要求):非内置 prompt 变体的语言,通过在 System Prompt 显式注入"必须以 X 语言输出"实现;
5. Docker/Watchtower 部署 → 不适用(纯桌面)。

---

## 过程记录(逐项追加,最新在上)

### 2026-09-29
- P1.1 ✅ 建立 PLAN.md,完成功能盘点 F1–F22 与里程碑 M1–M7。

### 2026-09-29 过程追加
- P5.10 同款复刻(video-clone-lite):新建项目第 5 目标「🎞 同款复刻」,四步流水线落地,分镜表/素材/首帧/视频存 metadata.clone,单镜可重做。
- P6.9 合并工具页:导入→ffprobe 检测(异类标红)→一键对齐→auto_merge。
- P7.2 视觉验收:13 张截图评审,修复资产页 QTabWidget+QScrollArea 嵌套塌陷、导出/合并空态提示。
- P7.3 字体(用户指示"用 drama 中的字体文件"):drama 源码无内置字体,CSS 栈 = SF Pro→PingFang SC→Microsoft YaHei;PySide6 版按同栈实现并打包 msyh.ttc(app/assets/fonts/)跨环境加载,中文渲染复验通过。
- P7.4 README 中/英/日/韩四语言,每份含 15 语言支持说明(用户要求)。
