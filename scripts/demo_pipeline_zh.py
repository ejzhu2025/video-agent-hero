"""演示3个Brief → Director → Storyboard的完整流程（中文输出）。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from agent.nodes.creative_pipeline import run_director, run_storyboard, _mock_concept
from agent.nodes.planner_llm import _build_llm_call

# ── 3个测试Brief ─────────────────────────────────────────────────────────────

EXAMPLES = [
    {
        "name": "例子1：饮品品牌",
        "state": {
            "brief": "推广一款新上市的抹茶拿铁，目标用户是18-25岁都市白领，主打'慢下来享受生活'的氛围感",
            "brand_kit": {
                "name": "茶时光",
                "brand_id": "cha_shiguang",
                "colors": {"primary": "#4A7C59"},
                "intro_outro": {"outro_cta": "扫码下单"},
            },
            "clarification_answers": {
                "platform": "reels",
                "duration_sec": 15,
                "language": "zh",
                "style_tone": ["温柔", "氛围感", "慢生活"],
            },
        },
    },
    {
        "name": "例子2：健身App",
        "state": {
            "brief": "为健身App做一条30秒广告，展示用户从沙发懒汉变成健身达人的蜕变，激励年轻人行动起来",
            "brand_kit": {
                "name": "燃起来",
                "brand_id": "burn_up",
                "colors": {"primary": "#FF4500"},
                "intro_outro": {"outro_cta": "免费下载"},
            },
            "clarification_answers": {
                "platform": "tiktok",
                "duration_sec": 30,
                "language": "zh",
                "style_tone": ["热血", "励志", "动感"],
            },
        },
    },
    {
        "name": "例子3：高端护肤品",
        "state": {
            "brief": "推广一款含有黄金成分的抗衰精华液，目标是30+成熟女性，强调奢华质感和科技感",
            "brand_kit": {
                "name": "黄金肌",
                "brand_id": "gold_skin",
                "colors": {"primary": "#C9A84C"},
                "intro_outro": {"outro_cta": "立即体验"},
            },
            "clarification_answers": {
                "platform": "reels",
                "duration_sec": 20,
                "language": "zh",
                "style_tone": ["奢华", "精致", "科技感"],
            },
        },
    },
]

# ── 辅助翻译函数（调用LLM翻译JSON内容）────────────────────────────────────────

def translate_to_chinese(llm_call, text: str) -> str:
    system = "你是专业翻译。将以下英文内容翻译成中文，保持原意，输出纯文本，不要加任何解释。"
    try:
        return llm_call(system, text)
    except Exception:
        return text

def translate_field(llm_call, value):
    """递归翻译dict/list/str中的英文字段。"""
    if isinstance(value, str) and value:
        return translate_to_chinese(llm_call, value)
    elif isinstance(value, list):
        return [translate_field(llm_call, v) for v in value]
    elif isinstance(value, dict):
        return {k: translate_field(llm_call, v) for k, v in value.items()}
    return value

# ── 格式化输出 ────────────────────────────────────────────────────────────────

def format_concept(concept: dict) -> str:
    vs = concept.get("visual_signature", {})
    lines = [
        f"  选中概念: {concept.get('id', '?')}",
        f"  开场策略: {concept.get('hook_angle', '')}",
        f"  视觉风格: {concept.get('visual_style', '')}",
        f"  核心信息: {concept.get('key_message', '')}",
        f"  情绪基调: {concept.get('mood', '')}",
        f"  建议场景数: {concept.get('scene_count', '?')}",
        f"  ── 视觉规范 ──",
        f"  运镜风格: {vs.get('camera_style', '')}",
        f"  色彩方案: {vs.get('color_palette', '')}",
        f"  灯光: {vs.get('lighting', '')}",
        f"  视觉母题: {vs.get('visual_motif', '')}",
    ]
    return "\n".join(lines)


def format_storyboard(plan: dict) -> str:
    script = plan.get("script", {})
    lines = [
        f"  平台: {plan.get('platform', '')} | 时长: {plan.get('duration_sec', '')}s | 语言: {plan.get('language', '')}",
        f"  风格: {', '.join(plan.get('style_tone', []))}",
        f"",
        f"  📝 脚本",
        f"    钩子: {script.get('hook', '')}",
    ]
    for i, line in enumerate(script.get("body", []), 1):
        lines.append(f"    正文{i}: {line}")
    lines.append(f"    CTA: {script.get('cta', '')}")
    lines.append("")
    lines.append("  🎬 分镜")
    for scene in plan.get("storyboard", []):
        beat = scene.get("narrative_beat", "")
        trans = scene.get("transition_in", "")
        lines.append(
            f"    S{scene['scene']} [{beat}] {scene['duration']}s"
            f"\n       画面: {scene['desc']}"
            f"\n       衔接: {trans}"
        )
    lines.append("")
    lines.append("  🎯 镜头列表")
    for shot in plan.get("shot_list", []):
        lines.append(
            f"    {shot['shot_id']} | 类型:{shot['type']} | {shot['duration']}s"
            f" | 字幕:「{shot.get('text_overlay', '')}」"
        )
    return "\n".join(lines)


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main():
    llm_call = _build_llm_call()

    for i, example in enumerate(EXAMPLES, 1):
        print(f"\n{'='*60}")
        print(f"  {example['name']}")
        print(f"{'='*60}")
        state = example["state"]
        print(f"\n📋 Brief: {state['brief']}\n")

        # Step 1: Director
        print("── STEP 1: 创意导演 ──────────────────────────────")
        concept = run_director(state, llm_call)
        print(format_concept(concept))

        # Step 2: Storyboard
        print("\n── STEP 2: 分镜故事板 ────────────────────────────")
        import uuid
        project_id = f"demo_{i:02d}"
        plan = run_storyboard(state, concept, project_id, llm_call)
        print(format_storyboard(plan))

        # no interactive pause needed

    print(f"\n{'='*60}")
    print("  全部演示完成")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
