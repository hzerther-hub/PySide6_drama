# 🎬 易好短剧 · PySide6 版(Yihao Shorts Desktop)

**简体中文** | [English](#english) | [日本語](#日本語) | [한국어](#한국어)

基于 **PySide6(Python 3.10+)** 的 AI 短剧/小说/漫画一站式制作工具。功能 100% 对齐开源项目 [chatfire-AI/yihao-drama](https://github.com/chatfire-AI/yihao-drama)(Web 版),并集成了两个社区工具的核心能力:

- **[golanse/easymerger](https://github.com/golanse/easymerger)** — 无损视频合并(参数检测/智能直通/一键对齐异类)
- **[liangdabiao/video-clone-lite](https://github.com/liangdabiao/video-clone-lite)** — 同款复刻(爆款视频结构迁移到你的产品)

> 黑盒分析报告:[docs/易好短剧-工具分析.md](docs/易好短剧-工具分析.md) · 实施计划:[PLAN.md](PLAN.md) · 过程记录:[PROGRESS.md](PROGRESS.md)

---

## 🌐 语言支持(15 种)

**界面语言与 AI 内容语言是同一个开关,内置 15 种**(超过原版 Web 的"UI 15 种 + AI 内容 4 种"):

中文 / English / 日本語 / 한국어 / Français / Deutsch / Italiano / Português / Español / Tiếng Việt / Türkçe / العربية / हिन्दी / Bahasa Indonesia / ภาษาไทย

- 切换入口:顶栏「界面与 AI 内容语言」或「设置 → 通用」;
- 切换后界面文案与 AI 产出(剧本/资产提取/分镜/提示词/小说/文案)**同时**使用所选语言;
- 非 zh/en/ja/ko 的语言通过在 Agent System Prompt 末尾注入显式输出语言指令实现(防止模型漂回英文);
- 本地化文件:`app/core/i18n.py`(新增语言只需在 `LANGS` 加一行 + 补 `T[lang]` 字典)。

## ✨ 功能全景

| 模块 | 能力 |
|------|------|
| 项目启动台 | 统计/筛选(待开始·进行中·已完成)/搜索/删除(二次确认) |
| 新建项目(5 种创作目标) | 📖 写小说 · 🎬 生成短剧 · 📚 生成漫画 · 📣 宣传营销(平台×6/格式×6) · 🎞 同款复刻(新) |
| 视觉风格 | 20 条预设(短剧向 8 + 通用 6 + 宣传 6),完整复刻原版英文提示词,统一电影质感锚点 |
| 集工作台(六阶段) | 原始内容 → AI 改写 → 视漫制作 → 分镜 → 漫画 → 拼接导出 |
| AI Agent ×10 | 剧本改写/角色场景提取/分镜拆解/提示词/小说生成/策划/六维审校/改稿/漫画分镜/宣传文案,System Prompt 全开放可编辑(`workspace/prompts/*.md`) |
| AI 服务 | 文本/图片/视频/配音 四类多供应商(OpenAI 兼容、Gemini、火山 Seedance/Seedream、MiniMax、阿里 Wan、Agnes、qwen-image、本地 InsightFace 换脸),易好 Key 一键配置,连通测试 |
| 任务系统 | 统一任务队列(sys_task),processing → completed/failed,任务面板 |
| 无损合并工具页 | ffprobe 参数一致性检测(分辨率/编码/帧率/Profile/采样率)→ 三通道:全一致 `-c copy` 秒合 / 视频一致音频不同→智能直通 / 少数异类→一键对齐多数派;失败回退链(换中间容器→重编码) |
| 同款复刻 | 参考视频抽帧 → AI 出分镜表 → 产品/模特素材 → 逐镜首帧图+图生视频 → 按原片节奏无损拼接 |
| 小说线 | 开书策划(总纲/世界观/合约/卷/章节)→ 逐章生成 → 六维审校 → 按指令改稿 → 导出整本 |
| 数据 | SQLite 单文件(23 张表)+ 本体媒体存储,`data/` 目录即全部数据 |

## 🚀 快速开始

```bash
# 要求 Python 3.10+(开发验证于 3.13)
pip install -r requirements.txt

# 运行
python app/main.py
```

- 数据目录:`data/`(SQLite + 生成的图片/视频/成片)
- Agent 提示词:`workspace/prompts/*.md`(设置页可在线编辑)
- FFmpeg:自动从 PATH 查找;或设置环境变量 `FFMPEG_BIN` / `FFPROBE_BIN`;或放入 `vendor/ffmpeg/bin/`
- AI 服务:首次启动进入「设置 → AI 服务」,粘贴 Yihao API Key 一键写入三条推荐配置,或手动模板逐个添加

## 📁 结构

```
app/
  core/    config.py(路径/ffmpeg) db.py(23表+种子) i18n.py(15语言) taskmgr.py(任务队列) theme.py(QSS)
  ai/      registry.py(服务注册表) text_client.py image_client.py video_client.py tts_client.py face_swap.py
  agents/  prompts.py(10 Agent 提示词+15语言机制) runner.py(执行器)
  pipeline/ rewriter.py extractor.py storyboard.py prompts_gen.py comic.py novel.py promo.py
           merge.py(easymerger 逻辑) stitch.py(长图) video_clone.py(同款复刻)
  ui/      main_window.py projects_page.py new_project_dialog.py project_page.py
           episode_page.py(六阶段工作台) settings_dialog.py task_panel.py merger_tool_page.py widgets.py
assets/fonts/  打包字体(微软雅黑,对齐原版 drama 字体栈回落策略)
docs/          分析报告/计划/过程/截图
```

## 📄 许可

延续原版 CC BY-NC-SA 4.0。FFmpeg 以子进程调用,其 GPL/LGPL 许可不影响本项目。

---

<a name="english"></a>
# 🎬 Yihao Shorts (PySide6 Edition)

**A one-stop AI studio for short dramas, novels and comics**, rebuilt in PySide6 (Python 3.10+). Feature-complete rewrite of [chatfire-AI/yihao-drama](https://github.com/chatfire-AI/yihao-drama), plus core logic from [golanse/easymerger](https://github.com/golanse/easymerger) (lossless merging) and [liangdabiao/video-clone-lite](https://github.com/liangdabiao/video-clone-lite) (viral-video cloning).

## 🌐 Languages — 15 supported

**UI language and AI-content language share one switch**, available in 15 languages:

Chinese / English / 日本語 / 한국어 / Français / Deutsch / Italiano / Português / Español / Tiếng Việt / Türkçe / العربية / हिन्दी / Bahasa Indonesia / ภาษาไทย

Switching updates both the interface and all AI output (scripts, asset extraction, storyboards, prompts, novels, marketing copy). Languages outside zh/en/ja/ko are enforced via an explicit output-language directive appended to each agent's system prompt.

## Features

- **5 creative goals**: novel / short drama / comic / promotion (6 platforms × 6 formats) / video clone
- **6-stage studio**: raw text → AI rewrite → assets → storyboard → comic → merge & export
- **10 AI agents** with fully editable system prompts (`workspace/prompts/*.md`)
- **Multi-provider AI services**: text/image/video/TTS (OpenAI-compatible, Gemini, Volcengine Seedance/Seedream, MiniMax, Aliyun Wan, Agnes, qwen-image, local InsightFace face-swap)
- **Lossless merger tool**: ffprobe parameter consistency check (resolution/codec/fps/profile/sample-rate) → lossless concat (`-c copy`), smart passthrough (video copy + audio aligned), or align-outliers-then-merge; with fallback chain
- **Video clone**: analyze reference video → AI storyboard → your product/presenter → shot-by-shot re-generation → lossless merge
- **Novel pipeline**: planning → chapter writing → 6-dimension review → editing → full book export
- **20 style presets** faithful to the original (cinematic quality anchors), SQLite storage (23 tables)

## Quick start

```bash
pip install -r requirements.txt   # Python 3.10+
python app/main.py
```

Data lives in `data/`; configure AI providers in Settings → AI Services (or paste a Yihao API Key for one-click setup).

License: CC BY-NC-SA 4.0 (inherited from the original project).

---

<a name="日本語"></a>
# 🎬 易好短劇 PySide6 版(日本語)

**AI によるショートドラマ・小説・漫画のワンストップ制作ツール**(Python 3.10+ / PySide6)。オープンソース [chatfire-AI/yihao-drama](https://github.com/chatfire-AI/yihao-drama) の全機能を再実装し、[golanse/easymerger](https://github.com/golanse/easymerger)(ロスレス結合)と [liangdabiao/video-clone-lite](https://github.com/liangdabiao/video-clone-lite)(動画複製)の核心ロジックを統合しました。

## 🌐 対応言語 — 15 言語

**UI 言語と AI 出力言語は同じスイッチで**、15 言語に対応:

中国語 / English / 日本語 / 한국어 / Français / Deutsch / Italiano / Português / Español / Tiếng Việt / Türkçe / العربية / हिन्दी / Bahasa Indonesia / ภาษาไทย

切り替えると、画面表示と AI が生成するすべてのコンテンツ(脚本・アセット・絵コンテ・プロンプト・小説・宣伝文)が同じ言語で出力されます。

## 主な機能

- **5 つの創作目標**:小説 / ショートドラマ / 漫画 / プロモーション / 動画複製
- **6 段階ワークベンチ**:原文 → AI リライト → アセット → 絵コンテ → 漫画 → 結合・書き出し
- **10 種類の AI Agent**(System Prompt は全て編集可能)
- **マルチプロバイダ AI**(OpenAI 互換 / Gemini / 火山 Seedance / MiniMax / 阿里 Wan / Agnes / ローカル顔交換)
- **ロスレス結合ツール**:ffprobe によるパラメータ一致判定(解像度/コーデック/FPS/Profile)→ `-c copy` / スマートパススルー / 外れ値整列の 3 チャネル + 失敗時フォールバック
- **小説制作**:企画 → 逐章生成 → 6 観点レビュー → 加筆 → 全編書き出し

## クイックスタート

```bash
pip install -r requirements.txt   # Python 3.10+
python app/main.py
```

ライセンス:CC BY-NC-SA 4.0(原プロジェクトより継承)。

---

<a name="한국어"></a>
# 🎬 이하오 숏드라마 PySide6 판(한국어)

**AI로 만드는 숏드라마·소설·만화 올인원 제작 도구**(Python 3.10+ / PySide6). 오픈소스 [chatfire-AI/yihao-drama](https://github.com/chatfire-AI/yihao-drama)의 전체 기능을 재구현하고, [golanse/easymerger](https://github.com/golanse/easymerger)(무손실 병합)와 [liangdabiao/video-clone-lite](https://github.com/liangdabiao/video-clone-lite)(영상 복제)의 핵심 로직을 통합했습니다.

## 🌐 지원 언어 — 15 개

**UI 언어와 AI 출력 언어가 하나의 스위치로 동작**하며 15 개 언어를 지원합니다:

중국어 / English / 日本語 / 한국어 / Français / Deutsch / Italiano / Português / Español / Tiếng Việt / Türkçe / العربية / हिन्दी / Bahasa Indonesia / ภาษาไทย

전환하면 화면 문구와 AI가 생성하는 모든 콘텐츠(대본·에셋·스토리보드·프롬프트·소설·홍보 문구)가 같은 언어로 출력됩니다.

## 주요 기능

- **5 가지 창작 목표**: 소설 / 숏드라마 / 만화 / 홍보 마케팅 / 영상 복제
- **6 단계 워크벤치**: 원문 → AI 각색 → 에셋 → 스토리보드 → 만화 → 병합·내보내기
- **10 종 AI Agent**(System Prompt 전체 편집 가능)
- **멀티 프로바이더 AI**(OpenAI 호환 / Gemini / 버섹 Seedance / MiniMax / 알리 Wan / Agnes / 로컬 얼굴 교체)
- **무손실 병합 도구**: ffprobe 파라미터 일치 검사(해상도/코덱/FPS/Profile) → `-c copy` / 스마트 패스스루 / 이상치 정렬 3 채널 + 실패 폴백
- **소설 제작**: 기획 → 챕터 생성 → 6 항목 검토 → 수정 → 전체 내보내기

## 빠른 시작

```bash
pip install -r requirements.txt   # Python 3.10+
python app/main.py
```

라이선스: CC BY-NC-SA 4.0(원 프로젝트 승계).
