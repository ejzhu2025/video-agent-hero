"""One-off script: re-render S3 of d8007625 via Gemini T2I → fal I2V → replace clip."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from pathlib import Path

PROJECT_ID = "d8007625"
SHOT_ID    = "S3"
DESC = (
    "Athlete's feet, clad in Nike Metcon 10 training shoes, plant firmly on the ground, "
    "teal accent color #00B894, preparing for a heavy lift, focused gaze, "
    "gym floor background, dramatic side lighting."
)
DURATION   = 1.0
QUALITY    = "hd"

work_dir      = Path("data/projects") / PROJECT_ID / "clips"
product_img   = Path("data/projects") / PROJECT_ID / "product.png"
scene_img     = work_dir / f"{SHOT_ID}_scene.png"
raw_i2v       = work_dir / f"{SHOT_ID}_raw.mp4"
clip_out      = work_dir / f"{SHOT_ID}.mp4"

print(f"[rerender] product image: {product_img} (exists={product_img.exists()})")

# ── Step 1: Gemini T2I — generate scene with product reference ────────────
from render.gemini_t2i import generate_scene_frame
from agent.nodes.planner_llm import get_gemini_client

print("[rerender] Step 1: Gemini T2I generating scene frame…")
gclient = get_gemini_client()
if not gclient:
    sys.exit("ERROR: No Gemini client — check GOOGLE_API_KEY")

generate_scene_frame(
    str(product_img),
    DESC,
    str(scene_img),
    gclient,
    style_tone=["dynamic", "athletic", "cinematic"],
)
print(f"[rerender] Scene frame saved: {scene_img}")

# ── Step 2: fal I2V — animate the scene frame ─────────────────────────────
from render.fal_i2v import generate_clip_from_image, build_shot_motion_prompt

print("[rerender] Step 2: fal I2V animating scene frame…")
motion = build_shot_motion_prompt("lifestyle", DESC, brief="Nike Metcon 10 workout shoes")
generate_clip_from_image(str(scene_img), motion, str(raw_i2v), quality=QUALITY)
print(f"[rerender] Raw I2V clip: {raw_i2v}")

# ── Step 3: Trim & scale ──────────────────────────────────────────────────
from render.ffmpeg_composer import FFmpegComposer

print("[rerender] Step 3: Trim & scale…")
FFmpegComposer().trim_and_scale_clip(str(raw_i2v), str(clip_out), duration=DURATION)
print(f"[rerender] ✓ {clip_out}")

# ── Step 4: Re-concatenate all clips ─────────────────────────────────────
import sqlite3, json

print("[rerender] Step 4: Re-concatenating all clips…")
db = sqlite3.connect("data/vah.db")
row = db.execute(
    "SELECT latest_plan_json FROM projects WHERE project_id=?", (PROJECT_ID,)
).fetchone()
plan = json.loads(row[0])
shot_list = plan["shot_list"]

clip_paths = [str(work_dir / f"{s['shot_id']}.mp4") for s in shot_list]
out_dir = Path("data/projects") / PROJECT_ID
branded = str(out_dir / "branded.mp4")
FFmpegComposer().concat_clips(clip_paths, branded, crossfade=0.0)
import shutil
shutil.copy(branded, str(out_dir / "with_subs.mp4"))
print(f"[rerender] ✓ Final video: {branded}")
print("[rerender] Done — re-export from the app to get a new download link.")
