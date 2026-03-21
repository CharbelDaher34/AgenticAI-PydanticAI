"""
FastAPI server that bridges PydanticAIClient streaming traces → WebSocket.
Run with:  uv run server.py
"""

import json
import sys
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
    PydanticAIClient,
    ThinkingStart,
    ThinkingDelta,
    ThinkingEnd,
    TextDelta,
    ToolCallTrace,
    ToolResultTrace,
    FinalOutput,
)

app = FastAPI(title="PydanticAI Trace Visualizer")

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse((Path(__file__).parent / "static" / "index.html").read_text())


@app.websocket("/ws/trace")
async def trace_websocket(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            raw = await ws.receive_text()
            cfg: dict[str, Any] = json.loads(raw)

            provider         = cfg.get("provider", "openai")
            model_name       = cfg.get("model_name", "gpt-4o")
            system_prompt    = cfg.get("system_prompt", "You are a helpful assistant.")
            enable_thinking  = cfg.get("enable_thinking", False)
            thinking_budget  = int(cfg.get("thinking_budget") or 8000)
            user_prompt      = cfg.get("user_prompt", "Hello!")
            temperature      = cfg.get("temperature") or None
            max_tokens       = cfg.get("max_tokens") or None
            tools_cfg        = cfg.get("tools", [])

            client = PydanticAIClient(
                provider=provider,
                model_name=model_name,
                system_prompt=system_prompt,
                enable_thinking=enable_thinking,
                thinking_budget=thinking_budget,
                temperature=temperature,
                max_tokens=max_tokens,
                keep_history=False,
            )

            # Register user-supplied tools
            for t in tools_cfg:
                try:
                    ns: dict = {}
                    exec(t["code"], ns)
                    fn = ns[t["name"]]
                    client.add_tool(fn, name=t["name"])
                except Exception as e:
                    await ws.send_text(json.dumps({
                        "type": "error",
                        "content": f"Tool '{t.get('name')}' failed to load: {e}",
                    }))

            # Stream trace events → JSON messages
            async for event in client.stream(user_prompt):

                if isinstance(event, ThinkingStart):
                    await ws.send_text(json.dumps({
                        "type": "thinking_start",
                        "part_index": event.part_index,
                    }))

                elif isinstance(event, ThinkingDelta):
                    await ws.send_text(json.dumps({
                        "type": "thinking_delta",
                        "content": event.content,
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
                        "content": event.content,
                    }))

                elif isinstance(event, FinalOutput):
                    await ws.send_text(json.dumps({
                        "type": "final_output",
                        "content": event.content,
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
