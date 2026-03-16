"""render/fal_transition.py — AI scene transitions via Kling v2.1 start+end frame."""
from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from pathlib import Path

import fal_client
import httpx

FAL_CALL_TIMEOUT = 300  # 5 minutes per transition
TRANSITION_KEEP_SECONDS = 1.5  # trim Kling's 5s clip to this length


def generate_transition_clip(
    frame_a_path: str,
    frame_b_path: str,
    output_path: str,
    keep_seconds: float = TRANSITION_KEEP_SECONDS,
) -> str:
    """Generate a smooth AI morph clip from frame_a → frame_b using Kling v2.1.

    Kling's `tail_image_url` produces a 5-second clip that starts looking like
    frame_a and ends looking like frame_b.  We keep only the first `keep_seconds`
    so the transition flows naturally out of the preceding clip (which already
    ends at frame_a).

    Returns output_path.
    """
    print(f"[fal_transition] uploading frames …", file=sys.stderr, flush=True)
    image_url = fal_client.upload_file(frame_a_path)
    tail_url = fal_client.upload_file(frame_b_path)

    def _run():
        return fal_client.run(
            "fal-ai/kling-video/v2.1/standard/image-to-video",
            arguments={
                "image_url": image_url,
                "tail_image_url": tail_url,
                "prompt": (
                    "smooth cinematic transition between two scenes, "
                    "seamless morphing, no text, no logos, no watermarks"
                ),
                "duration": "5",
                "aspect_ratio": "9:16",
            },
        )

    with ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(_run)
        try:
            result = future.result(timeout=FAL_CALL_TIMEOUT)
        except FuturesTimeoutError:
            raise TimeoutError(
                f"Kling transition timed out after {FAL_CALL_TIMEOUT}s"
            )

    if "video" in result:
        url = result["video"]["url"]
    elif "videos" in result and result["videos"]:
        url = result["videos"][0]["url"]
    else:
        raise ValueError(f"Unexpected Kling response keys: {list(result.keys())}")

    # Download full 5s clip
    raw_path = str(Path(output_path).with_suffix("")) + "_raw.mp4"
    with httpx.Client(timeout=180, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        Path(raw_path).write_bytes(resp.content)

    # Trim to keep_seconds (take from start — seamless handoff from preceding clip)
    from render.ffmpeg_composer import FFmpegComposer
    FFmpegComposer().trim_and_scale_clip(raw_path, output_path, duration=keep_seconds)
    print(
        f"[fal_transition] transition clip ready: {Path(output_path).name}",
        file=sys.stderr,
        flush=True,
    )
    return output_path
