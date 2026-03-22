"""
FastAPI server that bridges PydanticAIClient streaming traces → WebSocket.
Run with:  uv run server.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# ── Import trace types + client ───────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from test import (
    DEFAULT_AGENT_SYSTEM_BASE,
    PydanticAIClient,
    ThinkingStart,
    ThinkingDelta,
    ThinkingEnd,
    TextDelta,
    ToolCallTrace,
    ToolResultTrace,
)

app = FastAPI(title="PydanticAI Trace Visualizer")

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def build_system_prompt(user_extra: str) -> str:
    merged = DEFAULT_AGENT_SYSTEM_BASE.strip()
    extra = (user_extra or "").strip()
    if extra:
        merged = f"{merged}\n\n--- Additional instructions ---\n{extra}"
    if "Today's date:" not in merged:
        merged += f"\n\nToday's date: {datetime.now().strftime('%A, %B %d, %Y')}."
    return merged


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse((Path(__file__).parent / "static" / "index.html").read_text())


@app.websocket("/ws/trace")
async def trace_websocket(ws: WebSocket):
    await ws.accept()
    session_client: PydanticAIClient | None = None
    try:
        while True:
            raw = await ws.receive_text()
            cfg: dict[str, Any] = json.loads(raw)

            if cfg.get("reset_session"):
                session_client = None
                await ws.send_text(json.dumps({"type": "session_reset"}))
                continue

            user_prompt = (cfg.get("user_prompt") or "").strip()
            if not user_prompt:
                continue

            provider = cfg.get("provider", "openai")
            model_name = cfg.get("model_name", "gpt-4o")
            user_extra = (cfg.get("system_prompt") or "").strip()
            system_prompt = build_system_prompt(user_extra)
            enable_thinking = cfg.get("enable_thinking", False)
            thinking_budget = int(cfg.get("thinking_budget") or 8000)
            temperature_raw = cfg.get("temperature")
            if temperature_raw is not None and temperature_raw != "":
                temperature = float(temperature_raw)
            else:
                temperature = None
            max_tokens_raw = cfg.get("max_tokens")
            max_tokens = int(max_tokens_raw) if max_tokens_raw not in (None, "") else None
            tools_cfg = cfg.get("tools", [])
            # Must be JSON boolean true — avoid truthiness of non-empty strings, etc.
            continue_session = cfg.get("continue_session") is True

            if not continue_session:
                session_client = None

            if session_client is None:
                session_client = PydanticAIClient(
                    provider=provider,
                    model_name=model_name,
                    system_prompt=system_prompt,
                    enable_thinking=enable_thinking,
                    thinking_budget=thinking_budget,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    keep_history=True,
                )
                for t in tools_cfg:
                    try:
                        ns: dict = {}
                        exec(t["code"], ns)
                        fn = ns[t["name"]]
                        session_client.add_tool(fn, name=t["name"])
                    except Exception as e:
                        await ws.send_text(json.dumps({
                            "type": "error",
                            "content": f"Tool '{t.get('name')}' failed to load: {e}",
                        }))

            async for event in session_client.stream(user_prompt):

                if isinstance(event, ThinkingStart):
                    await ws.send_text(json.dumps({
                        "type": "thinking_start",
                        "part_index": event.part_index,
                    }))

                elif isinstance(event, ThinkingDelta):
                    await ws.send_text(json.dumps({
                        "type": "thinking_delta",
                        "content": event.content if event.content is not None else "",
                        "part_index": event.part_index,
                    }))

                elif isinstance(event, ThinkingEnd):
                    await ws.send_text(json.dumps({
                        "type": "thinking_end",
                        "part_index": event.part_index,
                    }))

                elif isinstance(event, ToolCallTrace):
                    await ws.send_text(json.dumps({
                        "type": "tool_call",
                        "tool_name": event.tool_name,
                        "args": str(event.args),
                        "tool_call_id": event.tool_call_id,
                    }))

                elif isinstance(event, ToolResultTrace):
                    await ws.send_text(json.dumps({
                        "type": "tool_result",
                        "tool_call_id": event.tool_call_id,
                        "content": str(event.content),
                    }))

                elif isinstance(event, TextDelta):
                    await ws.send_text(json.dumps({
                        "type": "text_delta",
                        "content": event.content if event.content is not None else "",
                    }))

            await ws.send_text(json.dumps({"type": "done"}))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await ws.send_text(json.dumps({"type": "error", "content": str(e)}))
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8765, reload=True)
