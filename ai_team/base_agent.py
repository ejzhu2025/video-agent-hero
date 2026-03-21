"""Base agent — agentic loop using Anthropic SDK tool use."""
from __future__ import annotations

import os
import sys
from typing import Any

import time
import anthropic

from .tools import TOOL_DEFS, TOOL_MAP, execute_tool

_FALLBACK_MODELS = ["claude-opus-4-6", "claude-sonnet-4-6"]


def run_agent(
    system_prompt: str,
    task: str,
    allowed_tools: list[str] | None = None,
    model: str = "claude-opus-4-6",
    max_turns: int = 20,
    verbose: bool = True,
) -> str:
    """
    Run an agentic loop: Claude calls tools until it reaches end_turn.
    Returns the final text response.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Filter tools to allowed set
    tools = [t for t in TOOL_DEFS if allowed_tools is None or t["name"] in (allowed_tools or [])]

    messages: list[dict] = [{"role": "user", "content": task}]

    for turn in range(max_turns):
        if verbose:
            print(f"  [turn {turn+1}] calling {model}...", file=sys.stderr)

        response = _call_with_retry(client, model, system_prompt, tools, messages, verbose)

        # Append assistant response
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Extract final text
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        if response.stop_reason != "tool_use":
            break

        # Execute tool calls
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            if verbose:
                print(f"  [tool] {block.name}({_summarize(block.input)})", file=sys.stderr)
            result = execute_tool(block.name, block.input)
            if verbose and len(result) < 300:
                print(f"  [result] {result[:200]}", file=sys.stderr)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })

        messages.append({"role": "user", "content": tool_results})

    # Fallback: return last text block
    for block in reversed(messages[-1]["content"] if isinstance(messages[-1]["content"], list) else []):
        if isinstance(block, dict) and block.get("type") == "text":
            return block["text"]
    return "(no response)"


def _call_with_retry(client, model, system_prompt, tools, messages, verbose):
    """Call API with exponential backoff + model fallback on overload."""
    candidates = [model] + [m for m in _FALLBACK_MODELS if m != model]
    # Try each model up to 2 times
    queue = [m for m in candidates for _ in range(2)]
    last_err = None
    for attempt, m in enumerate(queue):
        try:
            with client.messages.stream(
                model=m,
                max_tokens=8096,
                system=system_prompt,
                tools=tools,
                messages=messages,
            ) as stream:
                return stream.get_final_message()
        except Exception as e:
            last_err = e
            err_str = str(e)
            is_overload = "overloaded" in err_str.lower() or "529" in err_str or "429" in err_str
            if is_overload:
                wait = min(15 * (attempt + 1), 60)
                if verbose:
                    print(f"  [retry] {m} overloaded, trying next in {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
    raise last_err or RuntimeError("All models overloaded after retries")


def _summarize(inp: dict) -> str:
    parts = []
    for k, v in inp.items():
        sv = str(v)
        parts.append(f"{k}={sv[:40]!r}" if len(sv) > 40 else f"{k}={sv!r}")
    return ", ".join(parts)
