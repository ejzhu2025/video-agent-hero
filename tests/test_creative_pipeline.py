"""Tests for the Director→Storyboard→Critic→PromptCompiler creative pipeline."""
import json
import pytest

from agent.nodes.creative_pipeline import (
    run_director,
    run_storyboard,
    run_critic,
    run_compiler,
    _apply_patch,
    _build_cross_shot_sequence,
    _mock_concept,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

MINIMAL_STATE = {
    "brief": "Summer promo for Tong Sui Coconut Watermelon Refresh",
    "brand_kit": {
        "brand_id": "tong_sui",
        "name": "Tong Sui",
        "colors": {"primary": "#00B894"},
        "intro_outro": {"outro_cta": "Order now"},
    },
    "clarification_answers": {
        "platform": "tiktok",
        "duration_sec": 15,
        "language": "en",
        "style_tone": ["fresh", "summer"],
    },
}

SAMPLE_PLAN = {
    "project_id": "test123",
    "brief": "Summer promo",
    "platform": "tiktok",
    "duration_sec": 5.5,
    "language": "en",
    "style_tone": ["fresh"],
    "script": {"hook": "Cool off this summer", "body": ["100% natural"], "cta": "Order now"},
    "storyboard": [
        {
            "scene": 1,
            "desc": "Macro shot of coconut slices with teal water droplets, locked-off push-in, harsh overhead light",
            "duration": 1.5,
            "asset_hint": "macro",
            "narrative_beat": "hook",
            "transition_in": "opening — establish color palette and camera style",
        },
        {
            "scene": 2,
            "desc": "Product cup with teal liquid, slow push-in continues, condensation droplets glisten",
            "duration": 1.0,
            "asset_hint": "product",
            "narrative_beat": "reveal",
            "transition_in": "match cut — echo teal from S1, camera continues push-in",
        },
        {
            "scene": 3,
            "desc": "Abstract deep teal and warm straw bokeh background, minimal elegance",
            "duration": 1.0,
            "asset_hint": "text",
            "narrative_beat": "payoff",
            "transition_in": "fade through teal — color continuity from S2",
        },
    ],
    "shot_list": [
        {"shot_id": "S1", "type": "macro", "asset": "generate", "text_overlay": "Cool off this summer", "duration": 1.5},
        {"shot_id": "S2", "type": "product", "asset": "generate", "text_overlay": "", "duration": 1.0},
        {"shot_id": "S3", "type": "text", "asset": "generate", "text_overlay": "Order now", "duration": 1.0},
    ],
    "render_targets": ["9:16"],
}

CONCEPT = {
    "id": "C1",
    "hook_angle": "sensory immersion",
    "visual_style": "macro textures + golden hour lifestyle",
    "key_message": "Experience summer in every sip",
    "mood": "fresh and energetic",
    "scene_count": 4,
    "visual_signature": {
        "camera_style": "locked-off macro with slow push-in — NO handheld mixing",
        "color_palette": "#00B894 deep teal, #FFE082 warm straw, #FFFFFF clean white",
        "lighting": "harsh overhead midday sun with sharp drop shadows",
        "visual_motif": "condensation water droplets on cup exterior",
    },
}


# ── Mock LLM helpers ──────────────────────────────────────────────────────────

def make_llm(response: dict | list):
    """Return a LLMCall that always returns the given JSON object."""
    def call(system: str, user: str) -> str:
        return json.dumps(response)
    return call

def failing_llm(system: str, user: str) -> str:
    raise RuntimeError("LLM unavailable")


# ── Director tests ────────────────────────────────────────────────────────────

class TestDirector:
    def test_returns_best_concept(self):
        response = {
            "concepts": [
                {"id": "C1", "hook_angle": "sensory", "visual_style": "macro", "key_message": "A", "mood": "fresh", "scene_count": 4},
                {"id": "C2", "hook_angle": "surprise", "visual_style": "lifestyle", "key_message": "B", "mood": "playful", "scene_count": 3},
                {"id": "C3", "hook_angle": "emotion", "visual_style": "cinematic", "key_message": "C", "mood": "luxurious", "scene_count": 5},
            ],
            "best_index": 1,
        }
        concept = run_director(MINIMAL_STATE, make_llm(response))
        assert concept["id"] == "C2"
        assert concept["hook_angle"] == "surprise"

    def test_falls_back_to_mock_on_error(self):
        concept = run_director(MINIMAL_STATE, failing_llm)
        assert "hook_angle" in concept
        assert "visual_style" in concept
        assert "scene_count" in concept

    def test_mock_concept_has_required_fields(self):
        concept = _mock_concept(MINIMAL_STATE)
        for field in ("id", "hook_angle", "visual_style", "key_message", "mood", "scene_count"):
            assert field in concept

    def test_mock_concept_detects_food_brief(self):
        state = {**MINIMAL_STATE, "brief": "New coconut watermelon drink launch"}
        concept = _mock_concept(state)
        assert "macro" in concept["visual_style"].lower() or "lifestyle" in concept["visual_style"].lower()

    def test_mock_concept_has_visual_signature(self):
        concept = _mock_concept(MINIMAL_STATE)
        assert "visual_signature" in concept
        vs = concept["visual_signature"]
        for field in ("camera_style", "color_palette", "lighting", "visual_motif"):
            assert field in vs, f"visual_signature missing field: {field}"
        assert "#" in vs["color_palette"], "color_palette should contain hex codes"

    def test_director_llm_returns_visual_signature(self):
        response = {
            "concepts": [
                {
                    "id": "C1",
                    "hook_angle": "sensory",
                    "visual_style": "macro",
                    "key_message": "Cool",
                    "mood": "fresh",
                    "scene_count": 4,
                    "visual_signature": {
                        "camera_style": "locked-off macro",
                        "color_palette": "#00B894 teal, #FFE082 straw",
                        "lighting": "overhead sun",
                        "visual_motif": "water droplets",
                    },
                }
            ],
            "best_index": 0,
        }
        concept = run_director(MINIMAL_STATE, make_llm(response))
        assert "visual_signature" in concept
        assert concept["visual_signature"]["camera_style"] == "locked-off macro"


# ── Storyboard tests ──────────────────────────────────────────────────────────

class TestStoryboard:
    def test_returns_plan_with_shot_list(self):
        plan = run_storyboard(MINIMAL_STATE, CONCEPT, "proj001", make_llm(SAMPLE_PLAN))
        assert "shot_list" in plan
        assert "storyboard" in plan
        assert plan["project_id"] == "proj001"

    def test_falls_back_to_mock_on_error(self):
        plan = run_storyboard(MINIMAL_STATE, CONCEPT, "proj001", failing_llm)
        assert "shot_list" in plan
        assert len(plan["shot_list"]) > 0

    def test_plan_has_required_top_level_keys(self):
        plan = run_storyboard(MINIMAL_STATE, CONCEPT, "proj001", make_llm(SAMPLE_PLAN))
        for key in ("platform", "duration_sec", "language", "script", "storyboard", "shot_list", "render_targets"):
            assert key in plan, f"Missing key: {key}"

    def test_storyboard_scenes_have_narrative_beat_and_transition_in(self):
        plan = run_storyboard(MINIMAL_STATE, CONCEPT, "proj001", make_llm(SAMPLE_PLAN))
        for scene in plan.get("storyboard", []):
            assert "narrative_beat" in scene, f"Scene {scene.get('scene')} missing narrative_beat"
            assert "transition_in" in scene, f"Scene {scene.get('scene')} missing transition_in"

    def test_storyboard_user_prompt_contains_visual_signature(self):
        """Verify visual_signature fields are passed in the user prompt to LLM."""
        captured = {}
        def capture_llm(system: str, user: str) -> str:
            captured["user"] = user
            return json.dumps(SAMPLE_PLAN)

        run_storyboard(MINIMAL_STATE, CONCEPT, "proj001", capture_llm)
        user_msg = captured["user"]
        assert "locked-off macro" in user_msg, "camera_style not in storyboard prompt"
        assert "#00B894" in user_msg, "color_palette not in storyboard prompt"
        assert "water droplets" in user_msg, "visual_motif not in storyboard prompt"


# ── Critic tests ──────────────────────────────────────────────────────────────

class TestCritic:
    def test_applies_replace_patch(self):
        import copy
        plan = copy.deepcopy(SAMPLE_PLAN)
        # Scene 1 has a bad desc
        plan["storyboard"][0]["desc"] = "branded cup on white background, studio lighting"

        patch = [{"op": "replace", "path": "/storyboard/0/desc", "value": "product cup on white background, studio lighting"}]
        patched = run_critic(plan, make_llm(patch))
        assert "branded" not in patched["storyboard"][0]["desc"]
        assert "product cup" in patched["storyboard"][0]["desc"]

    def test_empty_patch_leaves_plan_unchanged(self):
        import copy
        plan = copy.deepcopy(SAMPLE_PLAN)
        patched = run_critic(plan, make_llm([]))
        assert patched["storyboard"] == plan["storyboard"]

    def test_falls_back_gracefully_on_error(self):
        import copy
        plan = copy.deepcopy(SAMPLE_PLAN)
        result = run_critic(plan, failing_llm)
        assert result["storyboard"] == plan["storyboard"]  # unchanged

    def test_apply_patch_replace(self):
        obj = {"storyboard": [{"desc": "old desc"}, {"desc": "scene 2"}]}
        patch = [{"op": "replace", "path": "/storyboard/0/desc", "value": "new desc"}]
        result = _apply_patch(obj, patch)
        assert result["storyboard"][0]["desc"] == "new desc"
        assert result["storyboard"][1]["desc"] == "scene 2"  # unchanged

    def test_apply_patch_remove_key(self):
        obj = {"a": 1, "b": 2}
        patch = [{"op": "remove", "path": "/b"}]
        result = _apply_patch(obj, patch)
        assert "b" not in result
        assert result["a"] == 1

    def test_apply_patch_bad_path_is_ignored(self):
        obj = {"storyboard": []}
        patch = [{"op": "replace", "path": "/storyboard/99/desc", "value": "x"}]
        result = _apply_patch(obj, patch)  # should not raise
        assert result["storyboard"] == []


# ── Compiler tests ────────────────────────────────────────────────────────────

class TestCompiler:
    def test_returns_dict_of_prompts(self):
        # New format: each value is {positive, negative}
        prompts_response = {
            "S1": {"positive": "Macro shot of coconut. Style: fresh.", "negative": "blurry, text"},
            "S2": {"positive": "Lifestyle shot.", "negative": "blurry"},
            "S3": {"positive": "", "negative": ""},
        }
        prompts = run_compiler(SAMPLE_PLAN, CONCEPT, MINIMAL_STATE, make_llm(prompts_response))
        assert isinstance(prompts, dict)
        assert "S1" in prompts
        assert "Macro" in prompts["S1"]["positive"]

    def test_text_shots_have_empty_prompt(self):
        prompts_response = {
            "S1": {"positive": "prompt", "negative": "blurry"},
            "S2": {"positive": "prompt", "negative": "blurry"},
            "S3": {"positive": "", "negative": ""},
        }
        prompts = run_compiler(SAMPLE_PLAN, CONCEPT, MINIMAL_STATE, make_llm(prompts_response))
        assert prompts.get("S3", {}).get("positive", "") == ""

    def test_falls_back_to_empty_on_error(self):
        prompts = run_compiler(SAMPLE_PLAN, CONCEPT, MINIMAL_STATE, failing_llm)
        assert prompts == {}

    def test_compiler_user_prompt_contains_visual_signature(self):
        """Compiler user prompt must embed color_palette, camera_style, and visual_motif."""
        captured = {}
        def capture_llm(system: str, user: str) -> str:
            captured["user"] = user
            return json.dumps({"S1": "test prompt", "S2": "prompt", "S3": ""})

        run_compiler(SAMPLE_PLAN, CONCEPT, MINIMAL_STATE, capture_llm)
        user_msg = captured["user"]
        # Hex codes are pre-translated to color names; check the translated name
        assert "fresh teal" in user_msg, "translated color name not in compiler prompt"
        assert "locked-off macro" in user_msg, "camera_style not in compiler prompt"
        assert "water droplets" in user_msg, "visual_motif not in compiler prompt"

    def test_compiler_user_prompt_contains_cross_shot_context(self):
        """Shots after the first must have prev_desc populated."""
        captured = {}
        def capture_llm(system: str, user: str) -> str:
            captured["user"] = user
            return json.dumps({"S1": "p1", "S2": "p2", "S3": ""})

        run_compiler(SAMPLE_PLAN, CONCEPT, MINIMAL_STATE, capture_llm)
        user_msg = captured["user"]
        assert "prev_desc" in user_msg, "prev_desc cross-shot field not in compiler prompt"
        assert "prev_beat" in user_msg, "prev_beat cross-shot field not in compiler prompt"
        assert "transition_in" in user_msg, "transition_in not in compiler prompt"


class TestBuildCrossShotSequence:
    def test_first_shot_has_null_prev(self):
        shots = _build_cross_shot_sequence(SAMPLE_PLAN)
        assert shots[0]["prev_desc"] is None
        assert shots[0]["prev_beat"] is None

    def test_second_shot_has_prev_from_first_scene(self):
        shots = _build_cross_shot_sequence(SAMPLE_PLAN)
        assert shots[1]["prev_desc"] == SAMPLE_PLAN["storyboard"][0]["desc"]
        assert shots[1]["prev_beat"] == SAMPLE_PLAN["storyboard"][0]["narrative_beat"]

    def test_all_shots_have_narrative_beat_and_transition_in(self):
        shots = _build_cross_shot_sequence(SAMPLE_PLAN)
        for shot in shots:
            assert "narrative_beat" in shot
            assert "transition_in" in shot

    def test_shot_count_matches_shot_list(self):
        shots = _build_cross_shot_sequence(SAMPLE_PLAN)
        assert len(shots) == len(SAMPLE_PLAN["shot_list"])


# ── Integration: full pipeline mock ──────────────────────────────────────────

class TestCreativePipelineIntegration:
    def test_full_pipeline_mock_mode(self):
        """Run the complete pipeline end-to-end with mocked LLM."""
        from agent.nodes.creative_pipeline import run_creative_pipeline

        director_response = {
            "concepts": [
                {
                    "id": "C1",
                    "hook_angle": "sensory",
                    "visual_style": "macro",
                    "key_message": "Cool off",
                    "mood": "fresh",
                    "scene_count": 3,
                    "visual_signature": {
                        "camera_style": "locked-off macro",
                        "color_palette": "#00B894 teal, #FFE082 straw",
                        "lighting": "overhead sun",
                        "visual_motif": "water droplets",
                    },
                }
            ],
            "best_index": 0,
        }
        compiler_response = {"S1": "Macro coconut shot, fresh summer.", "S2": "", "S3": ""}

        call_idx = [0]
        responses = [director_response, SAMPLE_PLAN, [], compiler_response]  # director, storyboard, critic, compiler

        def sequenced_llm(system: str, user: str) -> str:
            resp = responses[min(call_idx[0], len(responses) - 1)]
            call_idx[0] += 1
            return json.dumps(resp)

        concept, plan, prompts = run_creative_pipeline(MINIMAL_STATE, "test001", sequenced_llm)
        assert "hook_angle" in concept
        assert "shot_list" in plan
        assert isinstance(prompts, dict)

    def test_full_pipeline_fallback_mode(self):
        """All LLM calls fail → mocks kick in, pipeline still produces valid output."""
        from agent.nodes.creative_pipeline import run_creative_pipeline

        concept, plan, prompts = run_creative_pipeline(MINIMAL_STATE, "test002", failing_llm)
        assert "hook_angle" in concept
        assert "shot_list" in plan
        assert len(plan["shot_list"]) > 0
        assert isinstance(prompts, dict)  # empty {} is fine
