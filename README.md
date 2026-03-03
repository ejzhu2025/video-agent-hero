---
title: Video Agent Hero
emoji: 🎬
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
---

# video-agent-hero 🎬

An **Agentic Video Generator** — plan-first, interactive, memory-aware, brand-consistent.

Powered by LangGraph + Claude + fal.ai.

## Setup

Set these as HuggingFace Space Secrets:
- `ANTHROPIC_API_KEY` — for LLM planning (required for real AI generation)
- `FAL_KEY` — for fal.ai T2V video generation (required for real video clips)

Without keys the app runs with a mock planner and PIL placeholder frames.
