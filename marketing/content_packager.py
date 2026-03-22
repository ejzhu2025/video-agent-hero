"""marketing/content_packager.py — generate 3-platform content packages from a video."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

import anthropic
from dotenv import load_dotenv

load_dotenv()

_PLATFORM_PROMPTS = {
    "tiktok": {
        "lang": "English",
        "tone": "punchy, trendy, Gen-Z friendly. Use short sentences. Strong hook in the first line.",
        "hashtag_count": 5,
        "title_max": 80,
        "body_max": 150,
    },
    "instagram": {
        "lang": "English",
        "tone": "aspirational, aesthetic, lifestyle-forward. Slightly longer sentences. Emotive.",
        "hashtag_count": 10,
        "title_max": 100,
        "body_max": 220,
    },
    "xiaohongshu": {
        "lang": "Chinese (Simplified)",
        "tone": "relatable, warm, lifestyle-focused. Like a friend recommending a product. Use Chinese internet slang naturally.",
        "hashtag_count": 6,
        "title_max": 30,
        "body_max": 200,
    },
}

_COPY_PROMPT = """You are an expert social media copywriter specializing in {platform} ads for the US market.

Brand: {brand_name}
Product: {product_name}
Category: {category}
Target audience: {target_audience}
Emotional hook: {emotional_hook}
Key features: {key_features}
Platform: {platform}
Language: {lang}
Tone: {tone}

Write a complete {platform} post. Output ONLY valid JSON, no markdown:
{{
  "title": "<{title_max} chars max — the first line / caption hook>",
  "body": "<{body_max} chars max — supporting copy>",
  "cta": "<call-to-action, 1 sentence>",
  "hashtags": [<exactly {hashtag_count} hashtags as strings without # prefix>]
}}"""


def _extract_cover(video_path: str, output_path: str, timestamp: float = 1.5) -> bool:
    """Extract a cover frame from the video at `timestamp` seconds."""
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-ss", str(timestamp),
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "2",
                output_path,
            ],
            capture_output=True,
            check=True,
        )
        return True
    except Exception as e:
        print(f"[packager] Cover extraction failed: {e}")
        return False


def _resize_cover(src: str, dst: str, width: int, height: int) -> bool:
    """Resize and crop cover to target dimensions."""
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", src,
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}",
                dst,
            ],
            capture_output=True,
            check=True,
        )
        return True
    except Exception as e:
        print(f"[packager] Resize failed: {e}")
        return False


def _generate_copy(brand_info: dict[str, Any], platform: str) -> dict[str, str]:
    """Call Claude to generate platform-specific copy."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {
            "title": f"Discover {brand_info.get('brand_name', 'this brand')}",
            "body": brand_info.get("brief", ""),
            "cta": "Shop now",
            "hashtags": [],
        }

    cfg = _PLATFORM_PROMPTS[platform]
    prompt = _COPY_PROMPT.format(
        platform=platform.title(),
        brand_name=brand_info.get("brand_name", ""),
        product_name=brand_info.get("product_name", ""),
        category=brand_info.get("product_category", ""),
        target_audience=brand_info.get("target_audience", ""),
        emotional_hook=brand_info.get("emotional_hook", ""),
        key_features=", ".join(brand_info.get("key_features", [])),
        lang=cfg["lang"],
        tone=cfg["tone"],
        title_max=cfg["title_max"],
        body_max=cfg["body_max"],
        hashtag_count=cfg["hashtag_count"],
    )

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    import json
    try:
        return json.loads(text)
    except Exception:
        return {
            "title": f"Discover {brand_info.get('brand_name', '')}",
            "body": text[:200],
            "cta": "Shop now",
            "hashtags": [],
        }


def _format_copy_file(copy: dict, platform: str) -> str:
    """Format copy dict into a clean text file."""
    hashtags = " ".join(f"#{h}" for h in copy.get("hashtags", []))
    return (
        f"TITLE\n{copy.get('title', '')}\n\n"
        f"BODY\n{copy.get('body', '')}\n\n"
        f"CTA\n{copy.get('cta', '')}\n\n"
        f"HASHTAGS\n{hashtags}\n"
    )


def build_content_package(
    video_path: str,
    brand_info: dict[str, Any],
    output_dir: Path,
    platforms: list[str] | None = None,
) -> dict[str, Any]:
    """Build the full content package for all platforms.

    Returns a dict with paths to all generated files.
    """
    if platforms is None:
        platforms = ["tiktok", "instagram", "xiaohongshu"]

    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy video
    import shutil
    video_dst = output_dir / "video.mp4"
    shutil.copy2(video_path, video_dst)

    # Extract base cover (9:16 @ 1.5s)
    base_cover = str(output_dir / "_cover_base.jpg")
    _extract_cover(video_path, base_cover)

    result: dict[str, Any] = {"video": str(video_dst), "covers": {}, "copy": {}}

    # Platform cover dimensions
    cover_sizes = {
        "tiktok": (1080, 1920),        # 9:16
        "instagram": (1080, 1920),     # 9:16 Reels
        "xiaohongshu": (1080, 1440),   # 3:4
    }

    for platform in platforms:
        w, h = cover_sizes.get(platform, (1080, 1920))
        cover_path = str(output_dir / f"cover_{platform}.jpg")
        if Path(base_cover).exists():
            _resize_cover(base_cover, cover_path, w, h)
        result["covers"][platform] = cover_path

        # Generate copy
        print(f"[packager] Generating {platform} copy...")
        copy = _generate_copy(brand_info, platform)
        copy_path = output_dir / f"{platform}.txt"
        copy_path.write_text(_format_copy_file(copy, platform), encoding="utf-8")
        result["copy"][platform] = {"path": str(copy_path), "data": copy}

    # Clean up base cover
    Path(base_cover).unlink(missing_ok=True)

    return result
