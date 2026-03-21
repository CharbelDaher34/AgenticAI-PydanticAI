/* ─── PydanticAI Trace Visualizer — App Logic ─── */

// ── State ──────────────────────────────────────────────────────────────────
let ws = null;
let isRunning = false;
const tools = [
    {
        name: 'multiply',
        code: `def multiply(a: int, b: int) -> int:
    """Multiply two integers."""
    return a * b`
    },
    {
        name: 'divide',
        code: `def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    return a / b`
    },
    {
        name: 'add',
        code: `def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b`
    },
    {
        name: 'subtract',
        code: `def subtract(a: int, b: int) -> int:
    """Subtract two integers."""
    return a - b`
    },
];
let tokenCount = 0;
let eventIndex = 0; // global counter for timeline ordering

// ── DOM refs ───────────────────────────────────────────────────────────────
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');
const runBtn = document.getElementById('runBtn');
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
document.getElementById('enable_thinking').addEventListener('change', function () {
    document.getElementById('thinkingBudgetGroup').style.display = this.checked ? '' : 'none';
});

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

// ── Clear ──────────────────────────────────────────────────────────────────
clearBtn.addEventListener('click', () => {
    traceFeed.innerHTML = '';
    traceFeed.appendChild(emptyState);
    emptyState.style.display = 'flex';
    tokenCount = 0;
    eventIndex = 0;
    tokenCountEl.textContent = '0 tokens';
    setStatus('idle', 'Idle');
});

// ── Run ────────────────────────────────────────────────────────────────────
runBtn.addEventListener('click', startRun);

function startRun() {
    if (isRunning) return;

    const provider = document.getElementById('provider').value;
    const model_name = document.getElementById('model_name').value.trim();
    const system_prompt = document.getElementById('system_prompt').value.trim();
    const enable_thinking = document.getElementById('enable_thinking').checked;
    const thinking_budget = parseInt(document.getElementById('thinking_budget').value) || 8000;
    const user_prompt = document.getElementById('user_prompt').value.trim();
    const tempRaw = parseFloat(tempSlider.value);
    const temperature = (tempVal.textContent === '—') ? null : tempRaw;
    const max_tokens_raw = parseInt(document.getElementById('max_tokens').value);
    const max_tokens = isNaN(max_tokens_raw) ? null : max_tokens_raw;

    if (!user_prompt) { shake(runBtn); return; }

    setStatus('running', 'Running…');
    isRunning = true;
    runBtn.disabled = true;
    eventIndex = 0;

    emptyState.style.display = 'none';

    // Run header
    const header = createRunHeader(user_prompt, provider, model_name);
    traceFeed.appendChild(header);

    // Timeline wrapper
    const timeline = document.createElement('div');
    timeline.className = 'timeline';
    traceFeed.appendChild(timeline);
    scrollFeed();

    let activeThinkingCards = {}; // keyed by part_index
    let activeTextCard = null;

    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    ws = new WebSocket(`${proto}://${location.host}/ws/trace`);

    ws.onopen = () => {
        ws.send(JSON.stringify({ provider, model_name, system_prompt, enable_thinking, thinking_budget, user_prompt, temperature, max_tokens, tools }));
    };

    ws.onmessage = (ev) => {
        let msg;
        try { msg = JSON.parse(ev.data); } catch { return; }

        switch (msg.type) {
            case 'thinking_start':
                // Open a new thinking card for this part_index
                if (!activeThinkingCards) activeThinkingCards = {};
                if (!activeThinkingCards[msg.part_index]) {
                    const tc = createThinkingCard();
                    activeThinkingCards[msg.part_index] = tc;
                    timeline.appendChild(tc);
                }
                scrollFeed();
                break;

            case 'thinking_delta':
                if (!activeThinkingCards) activeThinkingCards = {};
                if (!activeThinkingCards[msg.part_index]) {
                    // Defensive: card wasn't opened yet
                    const tc = createThinkingCard();
                    activeThinkingCards[msg.part_index] = tc;
                    timeline.appendChild(tc);
                }
                appendThinking(activeThinkingCards[msg.part_index], msg.content);
                scrollFeed();
                addTokens(msg.content.length / 4);
                break;

            case 'thinking_end':
                if (activeThinkingCards && activeThinkingCards[msg.part_index]) {
                    sealThinking(activeThinkingCards[msg.part_index]);
                    delete activeThinkingCards[msg.part_index];
                }
                break;

            case 'tool_call':
                sealAllThinking(activeThinkingCards); activeThinkingCards = {};
                sealText(activeTextCard); activeTextCard = null;
                timeline.appendChild(createToolCallCard(msg));
                scrollFeed();
                break;

            case 'tool_result':
                timeline.appendChild(createToolResultCard(msg));
                scrollFeed();
                break;

            case 'text_delta':
                sealAllThinking(activeThinkingCards); activeThinkingCards = {};
                if (!activeTextCard) {
                    activeTextCard = createTextCard();
                    timeline.appendChild(activeTextCard);
                }
                appendText(activeTextCard, msg.content);
                scrollFeed();
                addTokens(msg.content.length / 4);
                break;

            case 'final_output':
                sealAllThinking(activeThinkingCards); activeThinkingCards = {};
                sealText(activeTextCard); activeTextCard = null;
                timeline.appendChild(createFinalCard(msg.content));
                scrollFeed();
                break;

            case 'error':
                sealText(activeTextCard); activeTextCard = null;
                timeline.appendChild(createErrorCard(msg.content));
                scrollFeed();
                break;

            case 'done':
                sealAllThinking(activeThinkingCards); activeThinkingCards = {};
                sealText(activeTextCard); activeTextCard = null;
                header.querySelector('.run-status').innerHTML = doneStatus();
                setStatus('done', 'Done');
                finishRun();
                break;
        }
    };

    ws.onerror = () => {
        timeline.appendChild(createErrorCard('WebSocket error — is the server running?'));
        scrollFeed();
        setStatus('error', 'Error');
        finishRun();
    };

    ws.onclose = () => { if (isRunning) finishRun(); };
}

function finishRun() {
    isRunning = false;
    runBtn.disabled = false;
    if (ws) { try { ws.close(); } catch { } ws = null; }
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

// ── Run header banner ──────────────────────────────────────────────────────
function createRunHeader(prompt, provider, model) {
    const el = document.createElement('div');
    el.className = 'run-header';
    el.innerHTML = `
    <div class="run-header-left">
      <div class="run-spinner"></div>
      <div class="run-info">
        <div class="run-label">Agent run</div>
        <div class="run-prompt">${escHtml(prompt)}</div>
      </div>
    </div>
    <div class="run-header-right">
      <span class="run-model-badge">${escHtml(provider)} · ${escHtml(model)}</span>
      <div class="run-status">
        <span class="run-status-dot"></span>
        <span>Running</span>
      </div>
    </div>`;
    return el;
}

function doneStatus() {
    return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--emerald)" stroke-width="2.5" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg> <span style="color:var(--emerald)">Completed</span>`;
}

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
    card._raw += delta;
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

// ── Final Output card ──────────────────────────────────────────────────────
function createFinalCard(content) {
    eventIndex++;
    const wordCount = content.split(/\s+/).filter(Boolean).length;

    const card = document.createElement('div');
    card.className = 'tc tc-final';
    card.dataset.expanded = 'true';
    card.innerHTML = `
    <div class="tc-line tc-line-last"></div>
    <div class="tc-dot tc-dot-final">
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
      </svg>
    </div>
    <div class="tc-body">
      <div class="tc-header" role="button" tabindex="0">
        <div class="tc-header-left">
          <span class="tc-badge tc-badge-final">Final Output</span>
          <span class="tc-time">${nowStr()}</span>
        </div>
        <div class="tc-header-right">
          <span class="tc-stats">${wordCount} words</span>
          <svg class="tc-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
      </div>
      <div class="tc-content">
        <div class="tc-final-body ${typeof marked !== 'undefined' ? 'tc-md' : ''}">${typeof marked !== 'undefined' ? marked.parse(content) : escHtml(content)
        }</div>
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
    'groq':                'llama-3.3-70b-versatile',
    'xai':                 'grok-3',
    'openrouter':          'anthropic/claude-3.5-sonnet',
    'bedrock-anthropic':   'anthropic.claude-3-5-sonnet-20241022-v2:0',
    'bedrock-openai':      'amazon.nova-pro-v1:0',
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
