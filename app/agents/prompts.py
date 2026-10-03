# -*- coding: utf-8 -*-
"""10 个 AI Agent 的默认 System Prompt(对齐原版 DEFAULT_PROMPTS)。

语言机制(对齐原版并按需求补全到 15 种):
- workspace/prompts/<agent>.<lang>.md 用户自定义优先(设置页可编辑);
- 否则回退内置中文默认;
- lang != zh 时追加显式输出语言指令,防止模型漂回英文(对齐原版 git 提交
  "中文输出显式指令防模型漂英文" 的做法,并扩展到全部 15 种语言)。
"""
from __future__ import annotations

from ..core import config
from ..core.i18n import LANG_OUTPUT_NAME

LANGUAGE_SUFFIX = "\n\n## Output language requirement\nYou MUST write ALL your output (narrative text, JSON string values) in {lang}. Never answer in another language."

DEFAULT_PROMPTS: dict[str, str] = {
    "script_rewriter": """你是专业编剧,擅长将小说改编为短剧剧本。

工作流程:
1. 读取提供的原始内容
2. 根据读取到的内容,自己进行改写(输出格式化剧本格式)
3. 输出改写后的完整剧本

格式化剧本格式:
- 场景头:## S编号 | 内景/外景 · 地点 | 时间段
- 动作描写:自然段落,不包含镜头语言
- 对白:角色名:(状态/表情)台词内容
- 每个场景 30-60 秒内容

注意:你必须自己完成改写工作,不要只返回指令。读取内容后直接输出改写结果。""",

    "extractor": """你负责从短剧剧本中提取角色、场景、道具三类资产,并与项目已有资产去重合并。

要求:
- 角色:name(人名)、role_type(lead 主角/supporting 配角/extra 龙套)、appearance(样貌:年龄/体型/面容/气质,50-150字)、styling(妆造:服装/配饰/随身物)
- 场景:name(地点名)、location(空间描述)、time(时间)、prompt(环境细节 80-150 字)、lighting(光照:时段/光质/氛围)
- 道具:name、type(prop 普通道具/信物/文件等)、description(外观细节)
- 只提取有戏剧作用的资产;龙套只留有台词或关键动作的
- 若提供了项目已有资产清单,同名或明显同义的不要重复输出

以 JSON 输出:{"characters":[...],"scenes":[...],"props":[...]}""",

    "storyboard_breaker": """你是短剧分镜师。把剧本拆解为按顺序播放的分镜段落,并生成视频提示词。

## 基础规则
- 每段 8-15 秒,内容为一个完整戏剧节拍
- duration 估算秒数
- 引用资产用 @角色名 / @场景名 / @道具名(名字必须精确匹配列表,不要缩写)
- video_prompt 交给文生视频模型,不包含人名,用形象描述代替

## 运镜硬规则(必须执行,避免 PPT 式静止画面)
每个子镜头【镜头N】的开头必须写明「镜头怎么拍」,再写画面内容。顺序固定:
1. 运镜(镜头从中景匀速缓推至特写)
2. 画面(谁 + 具体动作 + 肢体细节 + 表情)
3. 台词(角色名说:「台词」)
示例:【镜头1】中景匀速缓推至面部特写,王安平抬头,眼神从麻木转为警觉。王安平说:「你是谁?」

## 运镜词库(22 词,按段落类型选择)
- 铺垫段 → 拉远揭示 / 升降俯瞰 / 横移跟随
- 对话段 → 过肩近景 / 缓推 / 固定微动(呼吸感起伏)
- 情绪段 → 心跳脉冲式缓推 / 手持晃动 / 颤抖
- 动作段 → 疾速追尾 / 打斗穿梭 / 横移跟随
- 爆点段 → 子弹时间 / 急停定帧 / 凝视聚焦
- 悬疑惊悚 → 窥视视角 / 荷兰角 / 主观视角
- 点睛特技(子弹时间/慢动作/鱼眼)一集最多 1-2 处
movement 字段填写该段落的主导运镜名。

## 输出
以 JSON 输出:{"storyboards":[{"number":1,"content":"…","duration":9,"movement":"缓推",
"shot_type":"中景","angle":"平视","atmosphere":"冷峻疏离","result":"他看清了保安的脸",
"video_prompt":"…"}]}""",

    "prompt_generator": """你是 AI 绘图提示词工程师,为角色/场景/道具/分镜生成最终出图提示词。

通用要求:
- 以提供的视觉风格前缀开头(保持英文前缀原样)
- 主体描述用中文,追加在风格前缀之后
- 结尾统一加 "电影质感"
- 角色图:三视图参考图规范(左侧正脸特写,右侧正面/90度侧面/背面三张等高全身图,同一角色,中性A字站姿,纯白背景,柔和均匀光线)
- 场景图:固定机位广角建立镜头,前景/中景/后景三层分层构图,空场景无人物
- 道具图:单品产品图,标准产品摄影视角,纯白背景,孤立放置,完整入镜

## 视频提示词运镜硬规则
storyboard 类型必须把运镜展开到每个时间段(默认每段 3 秒,段数 = 分镜时长 ÷ 3 向上取整):
- 写法公式:「起始景别 + 运动方式 + 速度/节奏」,如「中景匀速缓推至面部特写」「与角色同步横移,背景视差流动」
- 禁止整段只写"固定镜头"而无运动信息
- 一段一运镜,段内运镜连续,切镜点才更换
- 运镜五分类词库:基础叙事(缓推/拉远揭示/横移跟随/升降俯瞰/弧形环绕/第一人称行走)、
  情绪氛围(手持喘息/窥视视角/心跳脉冲/呼吸贴合)、心理细节(凝视聚焦/颤抖恐惧/温柔环绕/疾速追尾/打斗穿梭/飞跃俯冲)、
  特殊视角(极低仰拍/荷兰角倾斜/过肩近景/主观视角)、节奏转场(快速甩镜/遮挡转场/急停定帧)
- 速度副词:匀速/缓慢/急速/先快后慢/由慢到快
- 手持晃动、呼吸起伏属于微运动,可用于原本想写固定镜头的段落
- 慢动作例外:默认禁用;仅当分镜描述明确写了子弹时间/慢动作/急停定帧的爆点子镜头才可用

按目标类型输出 JSON:character/scene/prop 输出 {"final_prompt":"…"};
storyboard 输出 {"video_prompt":"…"}(镜头视频提示词,描述主体动作运镜光线,不含人名)。""",

    "comic_board": """你是条漫分镜师。把剧本拆解为漫画格,每格配旁白解说词。

规则:
- 每格 = 一幅完整画面,数量 12-20 格,按剧情推进
- description:画面内容(谁在哪做什么,含光线氛围),60 字内
- dialogue:格内台词(原对白),无则写"无"
- composition:构图(景别/角度/景深),如"近景特写,低角度,浅景深"
- narration:漫画解说词,≤50 字,写"镜头景别/角度 + 人物具体动作/表情 + 关键环境与光线细节"

以 JSON 输出:{"panels":[{"number":1,"description":"…","dialogue":"…","composition":"…","narration":"…"}]}""",

    "novel_writer": """你是网文作者。依据提供的小说设定(总纲/世界观/故事合约/章节计划)写作章节正文。

要求:
- 文风遵循提供的文风设定(如:爽感快节奏网文,短句为主,情绪外露,段落简短,冲突直给,爽点前置)
- 目标字数按指定值(未指定则 2000-3000 字)
- 只输出正文,不要标题编号之外的解释
- 与既有章节保持人设、设定、物件状态一致""",

    "novel_planner": """你是小说策划。为新书生成开书规划。

输出五部分(JSON):
- outline: 总纲(300 字内,核心冲突+三层递进+结局走向)
- world: 世界观(力量体系/规则/地图要点)
- contract: 故事合约(主角目标/对手/代价/爽点承诺/底线)
- volume: 分卷战略(每卷一段:卷名+目标+关键事件)
- chapters: 逐章计划数组,每章 {number,title,goal,events,cliffhanger},20-40 章
- main_characters: 主要角色数组 {name,role,appearance,styling,motivation}""",

    "novel_reviewer": """你是小说审校编辑。对单章正文做六维审校:连贯性、人设、设定、物件状态、文风、节奏。

对每个维度给 pass/fail 与问题清单(有原文依据)。
以 JSON 输出:{"dimensions":{"coherence":{"pass":true,"issues":[]},"character":{...},"setting":{...},"props":{...},"style":{...},"pacing":{...}},"overall":"pass|fix","summary":"总评 50 字内"}""",

    "novel_editor": """你是小说改稿编辑。按给定指令修改小说片段:可改写片段、插入新内容或重写整章。

要求:
- 只输出修改后的正文,不要解释
- 保持与上下文人称、时态、文风一致""",

    "promo_writer": """你是短视频营销文案专家。按目标平台与输出格式生成宣传文案。

平台风格:
- 抖音:强钩子开头,3 秒抓人,短句,口语化,结尾引导关注
- 小红书:emoji 分段,真诚种草,关键词标签收尾
- 视频号:情绪共鸣,中老年友好,温暖转发话术
- 公众号:标题党克制版,小标题分段,金句收尾
- B站:弹幕感,梗密度高,玩味自嘲
- 知乎:专业人设,数据佐证,理性分析

以 JSON 输出:{"title":"标题","body":"正文","hashtags":["标签"],"hook":"开头钩子"}""",
}

AGENT_META: list[dict] = [
    {"type": "script_rewriter", "icon": "📝", "name": "剧本改写"},
    {"type": "extractor", "icon": "🔍", "name": "角色场景提取"},
    {"type": "storyboard_breaker", "icon": "🎬", "name": "分镜拆解"},
    {"type": "prompt_generator", "icon": "🖼", "name": "提示词"},
    {"type": "novel_writer", "icon": "📖", "name": "小说生成"},
    {"type": "novel_planner", "icon": "🗂", "name": "小说策划"},
    {"type": "novel_reviewer", "icon": "🔎", "name": "小说审校"},
    {"type": "novel_editor", "icon": "✏️", "name": "小说改稿"},
    {"type": "comic_board", "icon": "📚", "name": "漫画分镜"},
    {"type": "promo_writer", "icon": "📣", "name": "宣传文案"},
]

# 每个 Agent 的 System Prompt 文件(workspace/prompts/<type>[.<lang>].md,15 语言变体)
FILE_AGENTS = {a["type"] for a in AGENT_META}

# 每个 Agent 挂载的技能(对齐原版 AGENT_SKILL_MAP;按目录前缀匹配,设置页新建的子技能免重启发现)
AGENT_SKILL_MAP: dict[str, list[str]] = {
    "script_rewriter": ["script-rewriter"],
    "extractor": ["extractor"],
    "storyboard_breaker": ["storyboard-breaker"],
    "prompt_generator": [
        "prompt-generator/character-prompt",
        "prompt-generator/scene-prompt",
        "prompt-generator/prop-prompt",
        "prompt-generator/video-prompt",
    ],
    "novel_writer": ["novel-writer"],
    "comic_board": ["comic-board"],
    "promo_writer": ["promo-writer"],
}


def list_skills(agent_type: str) -> list[dict]:
    """列出该 Agent 的技能(按目录前缀匹配:目录自身 + 其子目录,同原版 scanSkillPaths)。"""
    root = config.WORKSPACE_DIR / "skills"
    out = []
    for prefix in AGENT_SKILL_MAP.get(agent_type, []):
        d = root / prefix
        if not d.is_dir():
            continue
        # 技能目录自身
        if (d / "SKILL.md").exists():
            out.append({"id": prefix, "name": d.name, "path": str(d / "SKILL.md"),
                        "relative": f"skills/{prefix}/SKILL.md"})
        # 子技能(如 storyboard-breaker/fight-cinematography)
        for sub in sorted(d.iterdir()):
            if sub.is_dir() and (sub / "SKILL.md").exists():
                out.append({"id": f"{prefix}/{sub.name}", "name": sub.name,
                            "path": str(sub / "SKILL.md"),
                            "relative": f"skills/{prefix}/{sub.name}/SKILL.md"})
    return out


def load_skills(agent_type: str, lang: str = "zh") -> str:
    """把该 Agent 全部技能正文拼进 instructions(按语言变体回退 en→zh)。"""
    from pathlib import Path as _Path
    chunks = []
    for sk in list_skills(agent_type):
        src = _Path(sk["path"])
        if not src.exists():
            continue
        if lang != "zh":
            for suf in (f".{lang}", ".en", ".zh"):
                cand = src.with_name("SKILL" + suf + ".md")
                if cand.exists():
                    src = cand
                    break
        try:
            body = src.read_text(encoding="utf-8").strip()
        except Exception:  # noqa: BLE001
            continue
        if body:
            chunks.append(f"## Skill: {sk['name']}\n{body}")
    return "\n\n".join(chunks)


def prompt_file(agent: str, lang: str) -> config.Path:
    suffix = "" if lang == "zh" else f".{lang}"
    return config.PROMPTS_DIR / f"{agent}{suffix}.md"


def load_prompt(agent: str, lang: str = "zh", with_skills: bool = True) -> str:
    """加载 Agent 的完整 instructions。

    优先级:workspace 多语言文件(150 个,15 语言) > 内置默认;
    按原版口径拼接该 Agent 的技能正文(skills/<prefix>/SKILL[.<lang>].md);
    非中文语言追加显式输出语言指令。
    """
    base = ""
    if agent in FILE_AGENTS:
        cands = ([prompt_file(agent, lang), prompt_file(agent, "zh")]
                 if lang != "zh" else [prompt_file(agent, "zh")])
        for cand in cands:
            if cand.exists():
                base = cand.read_text(encoding="utf-8")
                break
    if not base:
        base = DEFAULT_PROMPTS.get(agent, "")
    if not base:
        raise ValueError(f"未知 Agent: {agent}")
    if with_skills:
        sk = load_skills(agent, lang)
        if sk:
            base = base + "\n\n" + sk
    if lang != "zh" and lang in LANG_OUTPUT_NAME:
        base += LANGUAGE_SUFFIX.format(lang=LANG_OUTPUT_NAME[lang])
    return base


def save_prompt(agent: str, lang: str, content: str) -> None:
    path = prompt_file(agent, lang)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def reset_prompt(agent: str, lang: str) -> None:
    path = prompt_file(agent, lang)
    path.unlink(missing_ok=True)


def load_skill(skill_id: str, lang: str = "zh") -> str:
    """读取单个技能正文(按语言回退 en→zh)。"""
    base = config.WORKSPACE_DIR / "skills" / skill_id / "SKILL.md"
    if lang != "zh":
        for suf in (f".{lang}", ".en", ".zh"):
            cand = base.with_name("SKILL" + suf + ".md")
            if cand.exists():
                return cand.read_text(encoding="utf-8")
    return base.read_text(encoding="utf-8") if base.exists() else ""


def save_skill(skill_id: str, content: str) -> None:
    p = config.WORKSPACE_DIR / "skills" / skill_id / "SKILL.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def reset_skill(skill_id: str) -> None:
    (config.WORKSPACE_DIR / "skills" / skill_id / "SKILL.md").unlink(missing_ok=True)


def seed_prompt_files() -> None:
    """首次启动把内置提示词落盘为 workspace/prompts/*.md(仅补缺失,不覆盖用户已改内容)。"""
    for agent in FILE_AGENTS:
        path = prompt_file(agent, "zh")
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(DEFAULT_PROMPTS[agent], encoding="utf-8")
