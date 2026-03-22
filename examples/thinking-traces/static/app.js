/* ─── PydanticAI Trace Visualizer — App Logic ─── */

// ── State ──────────────────────────────────────────────────────────────────
let ws = null;
let isRunning = false;
const tools = [
    {
        name: 'search_web',
        code: `import asyncio

from ddgs import DDGS


async def search_web(query: str) -> str:
    """Search the web via DuckDuckGo text search (titles, href, body)."""
    await asyncio.sleep(2.0)

    def ddg_text_fetch():
        search_query = query.strip()
        with DDGS() as ddgs:
            rows = ddgs.text(
                search_query,
                region="wt-wt",
                safesearch="moderate",
                max_results=2,
            )
        return list(rows) if rows else []

    try:
        results = await asyncio.to_thread(ddg_text_fetch)
    except Exception as exc:
        return f"Search failed: {type(exc).__name__}: {exc}"
    if not results:
        return "No results found; try different keywords."
    lines = []
    for idx, row in enumerate(results):
        title = str(row.get("title", ""))
        href = str(row.get("href", ""))
        body = str(row.get("body", ""))
        lines.append(f"Result {idx + 1}: {title}")
        lines.append(f"  URL: {href}")
        lines.append(f"  Body: {body}")
    return chr(10).join(lines)[:6000]`
    },
    {
        name: 'execute_python',
        code: `import asyncio
import io
import textwrap


async def execute_python(code: str) -> str:
    """Run Python in a restricted environment (math + builtins; use print() for output)."""
    await asyncio.sleep(2.0)
    output_buf = io.StringIO()

    def safe_print(*args, **kwargs):
        kwargs.pop("file", None)
        print(*args, file=output_buf, **kwargs)

    safe_builtins = {
        "abs": abs,
        "all": all,
        "any": any,
        "bool": bool,
        "chr": chr,
        "dict": dict,
        "enumerate": enumerate,
        "filter": filter,
        "float": float,
        "format": format,
        "int": int,
        "len": len,
        "list": list,
        "map": map,
        "max": max,
        "min": min,
        "pow": pow,
        "print": safe_print,
        "range": range,
        "repr": repr,
        "reversed": reversed,
        "round": round,
        "set": set,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "zip": zip,
        "True": True,
        "False": False,
        "None": None,
    }
    import math

    namespace = {"__builtins__": safe_builtins, "math": math}
    try:
        exec(textwrap.dedent(code), namespace, namespace)
    except Exception as exc:
        return f"Error: {type(exc).__name__}: {exc}"
    text_out = output_buf.getvalue().strip()
    if text_out:
        return text_out[:8000]
    return "(no printed output; use print(...) to show results)"`
    },
    {
        name: 'evaluate_math',
        code: `import ast
import asyncio
import operator as operator_mod


_MATH_BINOPS = {
    ast.Add: operator_mod.add,
    ast.Sub: operator_mod.sub,
    ast.Mult: operator_mod.mul,
    ast.Div: operator_mod.truediv,
    ast.FloorDiv: operator_mod.floordiv,
    ast.Mod: operator_mod.mod,
    ast.Pow: operator_mod.pow,
}
_MATH_UNARY = {
    ast.UAdd: operator_mod.pos,
    ast.USub: operator_mod.neg,
}


def _eval_math_ast(node):
    if isinstance(node, ast.Expression):
        return _eval_math_ast(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ValueError("only numeric constants are allowed")
        return node.value
    if isinstance(node, ast.UnaryOp):
        op_t = type(node.op)
        if op_t not in _MATH_UNARY:
            raise ValueError("unsupported unary operator")
        return _MATH_UNARY[op_t](_eval_math_ast(node.operand))
    if isinstance(node, ast.BinOp):
        op_t = type(node.op)
        if op_t not in _MATH_BINOPS:
            raise ValueError("unsupported binary operator")
        return _MATH_BINOPS[op_t](_eval_math_ast(node.left), _eval_math_ast(node.right))
    raise ValueError("unsupported expression (use numbers and + - * / // % ** only)")


async def evaluate_math(expression: str) -> str:
    """Evaluate a single arithmetic expression (numbers, + - * / // % **, parentheses)."""
    await asyncio.sleep(1.5)
    expr = expression.strip()
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        return f"Syntax error: {exc}"
    try:
        value = _eval_math_ast(tree)
        return repr(value)
    except Exception as exc:
        return f"Error: {type(exc).__name__}: {exc}"`
    },
];
let tokenCount = 0;
let eventIndex = 0;
let conversation_active = false;
let active_turn_ctx = null;

// ── DOM refs ───────────────────────────────────────────────────────────────
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');
const sendBtn = document.getElementById('sendBtn');
const chatInput = document.getElementById('chat_input');
const clearBtn = document.getElementById('clearBtn');
const traceFeed = document.getElementById('traceFeed');
const emptyState = document.getElementById('emptyState');
const statusDot = document.getElementById('statusDot');
const statusLabel = document.getElementById('statusLabel');
const tokenCountEl = document.getElementById('tokenCount');
const tempSlider = document.getElementById('temperature');
const tempVal = document.getElementById('tempVal');
const addToolBtn = document.getElementById('addTool');
const toolsList = document.getElementById('toolsList');
const toolModal = document.getElementById('toolModal');
const closeModal = document.getElementById('closeModal');
const cancelTool = document.getElementById('cancelTool');
const saveTool = document.getElementById('saveTool');
const toolNameInput = document.getElementById('toolName');
const toolCodeInput = document.getElementById('toolCode');

// ── Sidebar toggle ─────────────────────────────────────────────────────────
sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('collapsed'));
mobileSidebarToggle.addEventListener('click', () => sidebar.classList.toggle('open'));

// ── Temperature slider ─────────────────────────────────────────────────────
tempSlider.addEventListener('input', () => {
    tempVal.textContent = parseFloat(tempSlider.value).toFixed(2);
});
tempVal.textContent = '—';
tempSlider.value = 1;

// Render default tools on page load
renderToolChips();

// ── Thinking budget visibility ──────────────────────────────────────────────
function sync_thinking_budget_visibility() {
    const en = document.getElementById('enable_thinking');
    const grp = document.getElementById('thinkingBudgetGroup');
    if (grp) grp.style.display = en && en.checked ? '' : 'none';
}
document.getElementById('enable_thinking').addEventListener('change', sync_thinking_budget_visibility);
sync_thinking_budget_visibility();

// ── Tools modal ────────────────────────────────────────────────────────────
addToolBtn.addEventListener('click', openToolModal);
closeModal.addEventListener('click', closeToolModal);
cancelTool.addEventListener('click', closeToolModal);
toolModal.addEventListener('click', (e) => { if (e.target === toolModal) closeToolModal(); });

saveTool.addEventListener('click', () => {
    const name = toolNameInput.value.trim();
    const code = toolCodeInput.value.trim();
    if (!name || !code) { shake(saveTool); return; }
    tools.push({ name, code });
    renderToolChips();
    closeToolModal();
});

function openToolModal() {
    toolNameInput.value = '';
    toolCodeInput.value = `def my_tool(x: int) -> int:\n    """Description of what this tool does."""\n    return x * 2`;
    toolModal.style.display = 'flex';
    setTimeout(() => toolNameInput.focus(), 50);
}
function closeToolModal() { toolModal.style.display = 'none'; }

toolNameInput.addEventListener('input', () => {
    const name = toolNameInput.value.trim() || 'my_tool';
    toolCodeInput.value = `def ${name}(x: int) -> int:\n    """Description of what this tool does."""\n    return x * 2`;
});

function renderToolChips() {
    toolsList.innerHTML = '';
    tools.forEach((t, i) => {
        const chip = document.createElement('div');
        chip.className = 'tool-chip';
        chip.innerHTML = `
      <span>fn <strong>${t.name}</strong>()</span>
      <button class="tool-chip-remove" title="Remove tool" data-idx="${i}">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>`;
        chip.querySelector('.tool-chip-remove').addEventListener('click', () => {
            tools.splice(i, 1);
            renderToolChips();
        });
        toolsList.appendChild(chip);
    });
}

function shake(el) {
    el.style.animation = 'none';
    el.offsetHeight;
    el.style.animation = 'shake 0.4s ease';
    setTimeout(() => el.style.animation = '', 400);
}

// ── Clear conversation ─────────────────────────────────────────────────────
clearBtn.addEventListener('click', clearConversation);

function clearConversation() {
    conversation_active = false;
    active_turn_ctx = null;
    if (ws) {
        try { ws.close(); } catch { /* ignore */ }
        ws = null;
    }
    traceFeed.innerHTML = '';
    traceFeed.appendChild(emptyState);
    emptyState.style.display = 'flex';
    tokenCount = 0;
    eventIndex = 0;
    tokenCountEl.textContent = '0 tokens';
    setStatus('idle', 'Idle');
    if (chatInput) chatInput.focus();
}

function buildChatPayload(user_text) {
    const max_raw = parseInt(document.getElementById('max_tokens').value, 10);
    return {
        provider: document.getElementById('provider').value,
        model_name: document.getElementById('model_name').value.trim(),
        system_prompt: document.getElementById('system_prompt').value.trim(),
        enable_thinking: document.getElementById('enable_thinking').checked,
        thinking_budget: parseInt(document.getElementById('thinking_budget').value, 10) || 8000,
        user_prompt: user_text,
        temperature: (tempVal.textContent === '—') ? null : parseFloat(tempSlider.value),
        max_tokens: Number.isNaN(max_raw) ? null : max_raw,
        tools,
        continue_session: conversation_active,
    };
}

function appendUserBubble(text) {
    const row = document.createElement('div');
    row.className = 'chat-turn chat-turn-user';
    row.innerHTML = `<div class="chat-bubble chat-bubble-user"><div class="chat-bubble-text">${escHtml(text)}</div></div>`;
    traceFeed.appendChild(row);
    scrollFeed();
}

function createAssistantTurn() {
    const wrap = document.createElement('div');
    wrap.className = 'chat-turn chat-turn-assistant';
    wrap.innerHTML = `
    <details class="chat-traces">
      <summary class="chat-traces-summary">
        <span class="chat-traces-chevron" aria-hidden="true">▸</span>
        <span>Trace</span>
        <span class="chat-traces-count" data-trace-count>0 steps</span>
      </summary>
      <div class="timeline chat-traces-timeline"></div>
    </details>
    <div class="chat-answer">
      <div class="chat-answer-label">Assistant</div>
      <div class="chat-answer-body streaming"></div>
    </div>`;
    traceFeed.appendChild(wrap);
    const details_el = wrap.querySelector('.chat-traces');
    details_el.open = false;
    details_el.addEventListener('toggle', () => {
        const ch = wrap.querySelector('.chat-traces-chevron');
        if (ch) ch.textContent = details_el.open ? '▾' : '▸';
    });
    return {
        wrap,
        timeline: wrap.querySelector('.chat-traces-timeline'),
        answerEl: wrap.querySelector('.chat-answer-body'),
        countEl: wrap.querySelector('[data-trace-count]'),
        thinkingCards: {},
        answerRaw: '',
        traceCount: 0,
    };
}

function bumpTraceCount(ctx) {
    ctx.traceCount += 1;
    if (ctx.countEl) ctx.countEl.textContent = `${ctx.traceCount} steps`;
}

/** WebSocket JSON may send null deltas; JS (x + null) becomes the string "null". */
function wsStringChunk(value) {
    if (value == null) return '';
    return typeof value === 'string' ? value : String(value);
}

function finalizeAssistantAnswer(ctx) {
    if (!ctx || !ctx.answerEl) return;
    let raw = wsStringChunk(ctx.answerRaw);
    if (typeof marked !== 'undefined' && raw) {
        ctx.answerEl.classList.remove('streaming');
        ctx.answerEl.classList.add('tc-md');
        ctx.answerEl.innerHTML = marked.parse(raw);
    } else if (raw) {
        ctx.answerEl.textContent = raw;
    } else {
        ctx.answerEl.classList.remove('streaming');
        ctx.answerEl.textContent = '—';
    }
}

function ensureWebSocket() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    ws = new WebSocket(`${proto}://${location.host}/ws/trace`);
    ws.onmessage = handleWsMessage;
    ws.onerror = () => {
        if (!active_turn_ctx) return;
        active_turn_ctx.timeline.appendChild(createErrorCard('WebSocket error — is the server running?'));
        scrollFeed();
        setStatus('error', 'Error');
        conversation_active = false;
        finishRun();
    };
    ws.onclose = () => {
        ws = null;
        if (isRunning) {
            setStatus('idle', 'Idle');
            finishRun();
        }
    };
}

function handleWsMessage(ev) {
    let msg;
    try { msg = JSON.parse(ev.data); } catch { return; }

    if (msg.type === 'session_reset') return;

    const ctx = active_turn_ctx;
    const timeline = ctx ? ctx.timeline : null;

    switch (msg.type) {
        case 'thinking_start':
            if (!ctx) break;
            if (!ctx.thinkingCards[msg.part_index]) {
                const tc = createThinkingCard();
                ctx.thinkingCards[msg.part_index] = tc;
                timeline.appendChild(tc);
                bumpTraceCount(ctx);
            }
            scrollFeed();
            break;

        case 'thinking_delta':
            if (!ctx) break;
            if (!ctx.thinkingCards[msg.part_index]) {
                const tc = createThinkingCard();
                ctx.thinkingCards[msg.part_index] = tc;
                timeline.appendChild(tc);
                bumpTraceCount(ctx);
            }
            appendThinking(ctx.thinkingCards[msg.part_index], msg.content);
            scrollFeed();
            addTokens(wsStringChunk(msg.content).length / 4);
            break;

        case 'thinking_end':
            if (ctx && ctx.thinkingCards[msg.part_index]) {
                sealThinking(ctx.thinkingCards[msg.part_index]);
                delete ctx.thinkingCards[msg.part_index];
            }
            break;

        case 'tool_call':
            if (!ctx) break;
            sealAllThinking(ctx.thinkingCards);
            ctx.thinkingCards = {};
            timeline.appendChild(createToolCallCard(msg));
            bumpTraceCount(ctx);
            scrollFeed();
            break;

        case 'tool_result':
            if (!ctx) break;
            timeline.appendChild(createToolResultCard(msg));
            bumpTraceCount(ctx);
            scrollFeed();
            break;

        case 'text_delta':
            if (!ctx) break;
            sealAllThinking(ctx.thinkingCards);
            ctx.thinkingCards = {};
            {
                const piece = wsStringChunk(msg.content);
                ctx.answerRaw = (ctx.answerRaw || '') + piece;
                ctx.answerEl.textContent = ctx.answerRaw;
                addTokens(piece.length / 4);
            }
            scrollFeed();
            break;

        case 'error':
            if (ctx && timeline) timeline.appendChild(createErrorCard(wsStringChunk(msg.content)));
            scrollFeed();
            setStatus('error', 'Error');
            conversation_active = false;
            active_turn_ctx = null;
            finishRun();
            break;

        case 'done':
            if (ctx) {
                sealAllThinking(ctx.thinkingCards);
                ctx.thinkingCards = {};
                finalizeAssistantAnswer(ctx);
                active_turn_ctx = null;
            }
            setStatus('done', 'Done');
            conversation_active = true;
            finishRun();
            break;
    }
}

function sendChatMessage() {
    if (isRunning) return;
    const user_text = (chatInput && chatInput.value || '').trim();
    if (!user_text) { shake(sendBtn); return; }

    emptyState.style.display = 'none';
    appendUserBubble(user_text);
    chatInput.value = '';

    active_turn_ctx = createAssistantTurn();

    setStatus('running', 'Running…');
    isRunning = true;
    sendBtn.disabled = true;

    const payload = buildChatPayload(user_text);
    ensureWebSocket();

    const send_payload = () => {
        try {
            ws.send(JSON.stringify(payload));
        } catch {
            if (active_turn_ctx && active_turn_ctx.timeline) {
                active_turn_ctx.timeline.appendChild(createErrorCard('Could not send message.'));
            }
            conversation_active = false;
            setStatus('error', 'Error');
            finishRun();
        }
    };

    if (ws.readyState === WebSocket.OPEN) send_payload();
    else ws.addEventListener('open', send_payload, { once: true });
}

function finishRun() {
    isRunning = false;
    sendBtn.disabled = false;
}

sendBtn.addEventListener('click', sendChatMessage);
if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });
}

// ── Status ─────────────────────────────────────────────────────────────────
function setStatus(type, label) {
    statusDot.className = `status-dot ${type}`;
    statusLabel.textContent = label;
}

function addTokens(delta) {
    tokenCount += delta;
    tokenCountEl.textContent = `~${Math.round(tokenCount).toLocaleString()} tokens`;
}

function scrollFeed() {
    requestAnimationFrame(() => { traceFeed.scrollTop = traceFeed.scrollHeight; });
}

function nowStr() {
    return new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// ═══════════════════════════════════════════════════════════════════════════
// ── Card Builders ──────────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════

// ── Thinking card ──────────────────────────────────────────────────────────
function createThinkingCard() {
    eventIndex++;
    const idx = eventIndex;
    const card = document.createElement('div');
    card.className = 'tc tc-thinking';
    card.dataset.expanded = 'true';
    card.innerHTML = `
    <div class="tc-line"></div>
    <div class="tc-dot tc-dot-thinking">
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
        <circle cx="12" cy="12" r="3"/>
        <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>
      </svg>
    </div>
    <div class="tc-body">
      <div class="tc-header" role="button" tabindex="0">
        <div class="tc-header-left">
          <span class="tc-badge tc-badge-thinking">Thinking</span>
          <span class="tc-thinking-snip" id="think-snip-${idx}"></span>
          <span class="tc-time">${nowStr()}</span>
        </div>
        <div class="tc-header-right">
          <span class="tc-stats" id="think-stats-${idx}">0 chars</span>
          <svg class="tc-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
      </div>
      <div class="tc-content tc-content-thinking">
        <div class="tc-thinking-text" id="think-text-${idx}"></div>
        <span class="streaming-cursor" style="background:var(--purple)"></span>
      </div>
    </div>`;

    card._raw = '';
    card._statsEl = card.querySelector(`#think-stats-${idx}`);
    card._snipEl = card.querySelector(`#think-snip-${idx}`);
    card._textEl = card.querySelector(`#think-text-${idx}`);
    card._cursorEl = card.querySelector('.streaming-cursor');

    setupCollapse(card);
    return card;
}

function appendThinking(card, delta) {
    card._raw += wsStringChunk(delta);
    card._textEl.textContent = card._raw;
    // Always keep a short snippet visible in the collapsed header
    card._snipEl.textContent = card._raw.slice(0, 90) + (card._raw.length > 90 ? '…' : '');
    card._statsEl.textContent = `${card._raw.length.toLocaleString()} chars`;
}

function sealThinking(card) {
    if (!card) return;
    card._cursorEl?.remove();
    if (card._snipEl) {
        card._snipEl.textContent = card._raw.slice(0, 90) + (card._raw.length > 90 ? '…' : '');
    }
}

function sealAllThinking(cardsMap) {
    if (!cardsMap) return;
    Object.values(cardsMap).forEach(sealThinking);
}

// ── Streaming text card ────────────────────────────────────────────────────
function createTextCard() {
    eventIndex++;
    const card = document.createElement('div');
    card.className = 'tc tc-text';
    card.dataset.expanded = 'true';
    card.innerHTML = `
    <div class="tc-line"></div>
    <div class="tc-dot tc-dot-text">
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    </div>
    <div class="tc-body">
      <div class="tc-header" role="button" tabindex="0">
        <div class="tc-header-left">
          <span class="tc-badge tc-badge-text">Response</span>
          <span class="tc-time">${nowStr()}</span>
        </div>
        <div class="tc-header-right">
          <span class="tc-stats" id="text-stats-${eventIndex}">Streaming…</span>
          <svg class="tc-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
      </div>
      <div class="tc-content">
        <div class="tc-text-body" id="text-body-${eventIndex}"></div>
        <span class="streaming-cursor"></span>
      </div>
    </div>`;

    card._raw = '';
    card._bodyEl = card.querySelector(`#text-body-${eventIndex}`);
    card._statsEl = card.querySelector(`#text-stats-${eventIndex}`);
    card._cursorEl = card.querySelector('.streaming-cursor');

    setupCollapse(card);
    return card;
}

function appendText(card, delta) {
    card._raw += delta;
    card._bodyEl.textContent = card._raw;
    const words = card._raw.split(/\s+/).filter(Boolean).length;
    card._statsEl.textContent = `${words} words`;
}

function sealText(card) {
    if (!card) return;
    card._cursorEl?.remove();
    if (card._raw && typeof marked !== 'undefined') {
        card._bodyEl.className = 'tc-text-body tc-md';
        card._bodyEl.innerHTML = marked.parse(card._raw);
    }
    const words = card._raw.split(/\s+/).filter(Boolean).length;
    card._statsEl.textContent = `${words} words`;
}

// ── Tool Call card ─────────────────────────────────────────────────────────
function createToolCallCard(msg) {
    eventIndex++;
    const prettyArgs = formatJson(msg.args);
    const shortId = msg.tool_call_id.slice(-8);

    const card = document.createElement('div');
    card.className = 'tc tc-tool-call';
    card.dataset.expanded = 'true';
    card.innerHTML = `
    <div class="tc-line"></div>
    <div class="tc-dot tc-dot-tool-call">
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3-3a1 1 0 0 0-1.4-1.4l-1.6 1.6-1.6-1.6a1 1 0 0 0-1.4 0z"/>
        <path d="M5 20L3 22M5 16l3-3 4-4 3 3-4 4-3 3z"/>
      </svg>
    </div>
    <div class="tc-body">
      <div class="tc-header" role="button" tabindex="0">
        <div class="tc-header-left">
          <span class="tc-badge tc-badge-tool-call">Tool Call</span>
          <span class="tc-fn-name">${escHtml(msg.tool_name)}</span>
          <span class="tc-time">${nowStr()}</span>
        </div>
        <div class="tc-header-right">
          <span class="tc-id-pill">#${escHtml(shortId)}</span>
          <svg class="tc-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
      </div>
      <div class="tc-content">
        <div class="tc-tool-row">
          <div class="tc-tool-section">
            <div class="tc-section-label">Function</div>
            <div class="tc-fn-pill">${escHtml(msg.tool_name)}</div>
          </div>
          <div class="tc-tool-section tc-tool-section-grow">
            <div class="tc-section-label">Arguments</div>
            <pre class="tc-code tc-code-amber">${escHtml(prettyArgs)}</pre>
          </div>
        </div>
        <div class="tc-call-id">
          <span class="tc-section-label">Call ID</span>
          <code class="tc-id-code">${escHtml(msg.tool_call_id)}</code>
        </div>
      </div>
    </div>`;

    setupCollapse(card);
    return card;
}

// ── Tool Result card ───────────────────────────────────────────────────────
function createToolResultCard(msg) {
    eventIndex++;
    const prettyResult = formatJson(msg.content);
    const shortId = msg.tool_call_id.slice(-8);

    const card = document.createElement('div');
    card.className = 'tc tc-tool-result';
    card.dataset.expanded = 'true';
    card.innerHTML = `
    <div class="tc-line"></div>
    <div class="tc-dot tc-dot-tool-result">
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
    </div>
    <div class="tc-body">
      <div class="tc-header" role="button" tabindex="0">
        <div class="tc-header-left">
          <span class="tc-badge tc-badge-tool-result">Tool Result</span>
          <span class="tc-result-preview">${escHtml(prettyResult.slice(0, 60))}${prettyResult.length > 60 ? '…' : ''}</span>
          <span class="tc-time">${nowStr()}</span>
        </div>
        <div class="tc-header-right">
          <span class="tc-id-pill">#${escHtml(shortId)}</span>
          <svg class="tc-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
      </div>
      <div class="tc-content">
        <div class="tc-result-section">
          <div class="tc-section-label">Return value</div>
          <pre class="tc-code tc-code-emerald">${escHtml(prettyResult)}</pre>
        </div>
        <div class="tc-call-id">
          <span class="tc-section-label">Call ID</span>
          <code class="tc-id-code">${escHtml(msg.tool_call_id)}</code>
        </div>
      </div>
    </div>`;

    setupCollapse(card);
    return card;
}

// ── Error card ─────────────────────────────────────────────────────────────
function createErrorCard(message) {
    eventIndex++;
    const card = document.createElement('div');
    card.className = 'tc tc-error';
    card.dataset.expanded = 'true';
    card.innerHTML = `
    <div class="tc-line"></div>
    <div class="tc-dot tc-dot-error">
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
    </div>
    <div class="tc-body">
      <div class="tc-header" role="button" tabindex="0">
        <div class="tc-header-left">
          <span class="tc-badge tc-badge-error">Error</span>
          <span class="tc-time">${nowStr()}</span>
        </div>
        <div class="tc-header-right">
          <svg class="tc-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
      </div>
      <div class="tc-content">
        <div class="tc-error-msg">${escHtml(message)}</div>
      </div>
    </div>`;

    setupCollapse(card);
    return card;
}

// ═══════════════════════════════════════════════════════════════════════════
// ── Collapse / Expand ──────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════
function setupCollapse(card) {
    const header = card.querySelector('.tc-header');
    const content = card.querySelector('.tc-content');
    if (!header || !content) return;

    header.addEventListener('click', () => toggleCard(card, content));
    header.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleCard(card, content); }
    });
}

function toggleCard(card, content) {
    const isExpanded = card.dataset.expanded === 'true';
    if (isExpanded) {
        // Collapse
        content.style.maxHeight = content.scrollHeight + 'px';
        content.style.overflow = 'hidden';
        requestAnimationFrame(() => {
            content.style.transition = 'max-height 0.3s cubic-bezier(0.4,0,0.2,1), opacity 0.25s ease';
            content.style.maxHeight = '0';
            content.style.opacity = '0';
        });
        card.dataset.expanded = 'false';
        card.classList.add('tc-collapsed');
    } else {
        // Expand
        content.style.transition = 'max-height 0.35s cubic-bezier(0.4,0,0.2,1), opacity 0.25s ease';
        content.style.maxHeight = content.scrollHeight + 'px';
        content.style.opacity = '1';
        content.addEventListener('transitionend', () => {
            if (card.dataset.expanded === 'true') content.style.maxHeight = 'none';
        }, { once: true });
        card.dataset.expanded = 'true';
        card.classList.remove('tc-collapsed');
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// ── Helpers ────────────────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════
function escHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function formatJson(val) {
    try {
        if (typeof val === 'string') {
            const parsed = JSON.parse(val);
            return JSON.stringify(parsed, null, 2);
        }
        return JSON.stringify(val, null, 2);
    } catch {
        return String(val);
    }
}

// ── Provider → default model ───────────────────────────────────────────────
const providerDefaults = {
    'openai':              'gpt-4o',
    'openai-responses':    'o4-mini',
    'anthropic':           'claude-sonnet-4-5',
    'anthropic-adaptive':  'claude-opus-4-6',
    'google':              'gemini-2.0-flash',
    'xai':                 'grok-3',
};
document.getElementById('provider').addEventListener('change', (e) => {
    document.getElementById('model_name').value = providerDefaults[e.target.value] || '';
});

// ── Shake animation ────────────────────────────────────────────────────────
const shakeStyle = document.createElement('style');
shakeStyle.textContent = `
@keyframes shake {
  0%,100%{transform:translateX(0)}
  20%{transform:translateX(-6px)}
  40%{transform:translateX(6px)}
  60%{transform:translateX(-4px)}
  80%{transform:translateX(4px)}
}`;
document.head.appendChild(shakeStyle);
