---
title: Video Agent Hero
emoji: 🎬
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
---

# Video Agent Hero 🎬

An **agentic short-form video generator** with a chat-driven two-phase pipeline:
**Plan → Review → Generate → Modify**

Powered by **LangGraph** + **Claude** + **fal.ai Wan 2.2**.

🌐 **Live demo**: [ejzhu2026-video-agent-hero.hf.space](https://ejzhu2026-video-agent-hero.hf.space)

---

## Features

- **Chat-driven UI** — describe your video, then refine via conversation
- **Two-phase pipeline** — see and edit the storyboard before generating
- **Turbo → HD upgrade** — quick 480p preview first, then upgrade to 720p
- **Smart partial re-render** — AI classifies feedback as global (full replan) or local (re-render only affected shots), saving time and cost
- **Real-time agent steps** — watch each pipeline node run with live elapsed timers
- **Brand kit** — consistent logo, colors, fonts, subtitles across all videos
- **Memory** — past projects stored in ChromaDB for semantic retrieval

---

## Architecture

```
POST /plan                POST /execute             POST /modify
     │                         │                         │
     ▼                         ▼                         ▼
intent_parser          executor_pipeline         change_classifier
memory_loader          caption_agent              ├─ local → partial_executor
clarification_planner  layout_branding            └─ global → planner_llm
planner_llm ◄──────    quality_gate
plan_checker (loop)    qc_diagnose
     │                 render_export
     ▼                 result_summarizer
  Plan JSON            memory_writer → END
  saved to DB
```

**LangGraph** orchestrates 4 compiled graphs:

| Graph | Entry → Exit | Used by |
|-------|-------------|---------|
| `build_plan_only_graph` | `intent_parser` → `plan_checker` → END | `/plan` |
| `build_execute_only_graph` | `executor_pipeline` → `memory_writer` → END | `/execute` |
| `build_partial_rerender_graph` | `change_classifier` → … → `memory_writer` → END | `/modify` |
| `build_replan_graph` | `planner_llm` → … → `memory_writer` → END | `/feedback` |

---

## Pipeline Nodes

| Node | Role | External Call |
|------|------|--------------|
| `intent_parser` | Extracts platform / duration / tone hints from brief | — |
| `memory_loader` | Loads brand kit (SQLite) + similar projects (ChromaDB) | SQLite, ChromaDB |
| `clarification_planner` | Detects missing fields, generates questions | — |
| `planner_llm` | Generates 4-shot Plan JSON; includes existing plan on replan | **Claude claude-sonnet-4-6** |
| `plan_checker` | Validates duration, shots, script; auto-fixes; loops ≤3× | — |
| `executor_pipeline` | Renders each shot via T2V (parallel, 6 workers) | **fal.ai wan/v2.2-a14b** |
| `caption_agent` | Maps script lines to shot durations → caption segments | — |
| `layout_branding` | Concat clips + burn subtitles + add logo watermark | FFmpeg |
| `quality_gate` | Probes resolution, duration, bitrate, frame content | FFmpeg (ffprobe) |
| `qc_diagnose` | Root-cause analysis; routes to retry / user action / proceed | Claude (fallback) |
| `render_export` | Final H.264 CRF23 + AAC 128k encode | FFmpeg |
| `result_summarizer` | Builds human-readable summary | — |
| `memory_writer` | Persists plan + output path + vector embedding | SQLite, ChromaDB |
| `change_classifier` | Classifies feedback as global/local; identifies shot indices | **Claude Haiku** |
| `partial_executor` | Re-renders only affected shots; reuses disk clips for the rest | **fal.ai wan/v2.2-a14b** |

---

## State (AgentState)

All nodes share a single `TypedDict` that flows through the graph:

```python
{
  # Identity
  "project_id": "a1b2c3d4",
  "brief": "Summer promo for Tong Sui Coconut Watermelon",
  "brand_id": "tong_sui",

  # Plan (output of planner_llm)
  "plan": {
    "platform": "tiktok", "duration_sec": 10,
    "style_tone": ["fresh", "playful"],
    "script": { "hook": "...", "body": [...], "cta": "..." },
    "storyboard": [{ "scene": 1, "desc": "...", "duration": 2.5 }, ...],
    "shot_list":  [{ "shot_id": "S1", "text_overlay": "...", "duration": 2.5 }, ...],
    "_quality": "turbo"          # written after execute
  },

  # Execution
  "scene_clips": [{ "shot_id": "S1", "clip_path": "...", "duration": 2.5 }],
  "branded_clip_path": "data/projects/.../branded.mp4",
  "output_path": "data/exports/a1b2c3d4_9x16_....mp4",

  # Quality
  "quality": "turbo",            # "turbo" | "hd"
  "quality_result": { "passed": true, "issues": [] },

  # Partial re-render
  "change_type": "local",
  "affected_shot_indices": [1],
  "shot_updates": { "1": { "desc": "...", "text_overlay": "..." } },

  # Control
  "needs_replan": false,
  "plan_version": 1,
  "messages": [...]
}
```

---

## Video Quality Tiers

| Tier | Model | Frames | Resolution | Use case |
|------|-------|--------|-----------|---------|
| **Turbo** | `fal-ai/wan/v2.2-a14b/text-to-video` | 33 @ 16fps | 480p | Fast preview (~2s clips) |
| **HD** | `fal-ai/wan/v2.2-a14b/text-to-video` | 81 @ 16fps | 720p | Final delivery (~5s clips) |

---

## UI Flow

```
idle ──[Send brief]──► planning ──[done]──► plan_ready
                                                │
                                    Edit storyboard cards
                                                │
                                    [▶ Approve & Generate]
                                                │
                                           executing ──[done]──► done
                                                                   │
                                              ⚡ Turbo preview shown
                                              [✦ Upgrade to HD] button
                                                                   │
                                              [chat: "modify..."] ─┘
                                                     smart re-render
```

Chat bar states:

| State | Input placeholder | Action |
|-------|------------------|--------|
| `idle` / `error` | Describe your video... | Create project + plan |
| `plan_ready` | Ask to change the plan... | Replan with feedback |
| `done` | Modify this video... | Smart partial/global re-render |

---

## Project Structure

```
video-agent-hero/
├── web/server.py              # FastAPI + SSE streaming + inline HTML/JS frontend
├── agent/
│   ├── graph.py               # 4 LangGraph compiled graphs
│   ├── state.py               # AgentState TypedDict
│   ├── deps.py                # DB + VectorStore singletons
│   └── nodes/                 # 15 node functions (one file each)
├── render/
│   ├── fal_t2v.py             # fal.ai T2V wrapper (turbo/hd quality tiers)
│   ├── ffmpeg_composer.py     # concat, subtitles, watermark, trim/scale
│   ├── caption_renderer.py    # SRT/ASS subtitle file writer
│   └── frame_generator.py     # PIL placeholder frames (no-key fallback)
├── memory/
│   ├── db.py                  # SQLite (projects, brand_kits, user_prefs, feedback)
│   ├── vector_store.py        # ChromaDB semantic search
│   └── schemas.py             # Pydantic v2 models
├── cli/main.py                # Typer CLI (vah init/new/run/feedback/demo)
├── assets/                    # Brand assets (auto-generated on startup)
├── data/                      # Runtime data — gitignored
│   ├── vah.db                 # SQLite
│   ├── chroma/                # ChromaDB
│   ├── projects/{id}/clips/   # Per-shot MP4s (reused on partial re-render)
│   └── exports/               # Final deliverable MP4s
├── Dockerfile                 # HuggingFace Spaces deployment
└── requirements.txt
```

---

## Quick Start (Local)

### Prerequisites

```bash
brew install ffmpeg        # macOS
# sudo apt install ffmpeg  # Ubuntu
python3.11 -m venv .venv && source .venv/bin/activate
```

### Install & Run

```bash
git clone https://github.com/ejzhu2025/video-agent-hero
cd video-agent-hero
pip install -r requirements.txt
uvicorn web.server:app --host 0.0.0.0 --port 7860 --reload
# Open http://localhost:7860
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | For AI planning | Claude claude-sonnet-4-6 planner + Haiku classifier |
| `FAL_KEY` | For video generation | fal.ai Wan 2.2 T2V |
| `VAH_DATA_DIR` | Optional | Data directory (default: `./data`) |

Without keys: mock planner + PIL placeholder frames (useful for UI development).

---

## CLI Reference

```bash
pip install -e .   # installs `vah` command

vah init           # seed DB with Tong Sui brand kit
vah new --brief "..." [--brand X] [--user Y]
vah run --project ID [--yes]
vah feedback --project ID --text "..."
vah list
vah demo           # full end-to-end Tong Sui demo
```

---

## Output Spec

| Property | Value |
|----------|-------|
| Resolution | 1080 × 1920 (9:16 vertical) |
| Codec | H.264 (libx264), CRF 23 |
| Frame rate | 30 fps |
| Audio | AAC 128kbps |
| Captions | Burned-in SRT, branded box style |
| Logo | Watermark in configurable safe area |

---

## HuggingFace Spaces Deployment

Set these as **Space Secrets** (Settings → Repository secrets):
- `ANTHROPIC_API_KEY`
- `FAL_KEY`

Data is stored in `/data` (Docker volume). The app auto-seeds the brand kit on startup.
