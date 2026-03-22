// ── AI Interview Practice — frontend logic ──────────────────────────────────

(function () {
  "use strict";

  const setupScreen = document.getElementById("setup-screen");
  const interviewScreen = document.getElementById("interview-screen");
  const setupForm = document.getElementById("setup-form");
  const startBtn = document.getElementById("start-btn");
  const sessionMeta = document.getElementById("session-meta");
  const progressLabel = document.getElementById("progress-label");
  const chatEl = document.getElementById("chat");
  const typingIndicator = document.getElementById("typing-indicator");
  const answerInput = document.getElementById("answer-input");
  const sendBtn = document.getElementById("send-btn");

  let ws = null;
  let connected = false;
  let numQuestions = 5;
  let currentQ = 0;

  let pasteCount = 0;
  let tabSwitchCount = 0;
  let copyCount = 0;

  function escapeHtml(text) {
    if (text == null) return "";
    const div = document.createElement("div");
    div.textContent = String(text);
    return div.innerHTML;
  }

  const goalLabels = {
    general: "General practice",
    "deep-dive": "Deep dive (gaps)",
    breadth: "Breadth coverage",
    behavioral: "Behavioral & technical",
  };

  const difficultyLabels = {
    easy: "Easy",
    medium: "Medium",
    hard: "Hard",
    adaptive: "Adaptive",
  };

  setupForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    startBtn.disabled = true;
    startBtn.innerHTML =
      '<span class="btn-icon"><i class="fas fa-spinner fa-spin" aria-hidden="true"></i></span><span>Starting session…</span>';

    const goal_key = document.getElementById("goal").value;
    const diff_key = document.getElementById("difficulty").value;
    const config = {
      job_description: document.getElementById("job-desc").value.trim(),
      goal: goal_key,
      difficulty: diff_key,
      num_questions: parseInt(document.getElementById("num-questions").value, 10),
    };
    numQuestions = config.num_questions;

    try {
      const resp = await fetch("/api/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });
      if (!resp.ok) throw new Error(await resp.text());

      const data = await resp.json();
      openWebSocket(data.session_id, config, goal_key, diff_key);
    } catch (err) {
      alert("Failed to start interview: " + err.message);
      startBtn.disabled = false;
      startBtn.innerHTML =
        '<span class="btn-icon"><i class="fas fa-play" aria-hidden="true"></i></span><span>Begin interview</span>';
    }
  });

  function openWebSocket(sessionId, config, goal_key, diff_key) {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${proto}://${location.host}/ws/interview/${sessionId}`);

    ws.onopen = function () {
      connected = true;
      setupScreen.classList.add("hidden");
      interviewScreen.classList.remove("hidden");
      sessionMeta.textContent =
        difficultyLabels[diff_key] +
        " · " +
        (goalLabels[goal_key] || config.goal) +
        " · " +
        numQuestions +
        " question" +
        (numQuestions === 1 ? "" : "s");
      updateProgress(0);
      showTyping();
    };

    ws.onmessage = function (e) {
      hideTyping();
      handleMessage(JSON.parse(e.data));
    };

    ws.onclose = function () {
      connected = false;
      hideTyping();
      addMsg(
        "bot",
        '<span class="msg-label">System</span><p class="bubble-note">Session ended. Refresh the page to configure a new interview.</p>'
      );
      disableInput();
    };

    ws.onerror = function () {
      alert("Connection error. Please refresh and try again.");
    };
  }

  function handleMessage(m) {
    if (m.question) {
      currentQ = m.question_number || currentQ + 1;
      updateProgress(currentQ);
      const diff = m.difficulty
        ? '<span class="difficulty-badge">' + escapeHtml(m.difficulty) + "</span>"
        : "";
      addMsg(
        "bot",
        '<div class="msg-head"><span class="msg-label">Question ' +
          currentQ +
          "</span>" +
          diff +
          "</div>" +
          '<p class="msg-body">' +
          escapeHtml(m.question) +
          "</p>"
      );
      enableInput();
    } else if (m.followup_question) {
      addMsg(
        "bot",
        '<span class="msg-label">Follow-up</span>' +
          '<p class="msg-body">' +
          escapeHtml(m.followup_question) +
          "</p>" +
          '<span class="followup-reason"><strong>Context</strong> — ' +
          escapeHtml(m.reason) +
          "</span>"
      );
      enableInput();
    } else if (m.evaluation) {
      const ev = m.evaluation;
      const overall =
        ev.overall ?? (ev.technical_score + ev.communication_score) / 2;
      addMsg(
        "bot",
        '<div class="eval-card">' +
          '<div class="eval-card-header">' +
          '<span class="score-badge overall">Overall ' +
          overall.toFixed(0) +
          "</span>" +
          '<span class="score-badge tech">Technical ' +
          escapeHtml(ev.technical_score) +
          "</span>" +
          '<span class="score-badge comm">Communication ' +
          escapeHtml(ev.communication_score) +
          "</span>" +
          "</div>" +
          "<h4>Feedback</h4><p>" +
          escapeHtml(ev.feedback) +
          "</p>" +
          "<h4>Strengths</h4><ul>" +
          ev.strengths.map(function (s) {
            return "<li>" + escapeHtml(s) + "</li>";
          }).join("") +
          "</ul>" +
          "<h4>Areas to improve</h4><ul>" +
          ev.improvements.map(function (s) {
            return "<li>" + escapeHtml(s) + "</li>";
          }).join("") +
          "</ul></div>"
      );
      showTyping();
    } else if (m.clarification) {
      addMsg(
        "bot",
        '<span class="msg-label">Clarification</span><p class="msg-body">' +
          escapeHtml(m.clarification) +
          "</p>"
      );
      enableInput();
    } else if (m.warning) {
      addMsg(
        "bot",
        '<span class="msg-label">Guidance</span><p class="msg-body">' +
          escapeHtml(m.warning) +
          "</p>"
      );
      enableInput();
    } else if (m.feedback) {
      addMsg(
        "bot",
        '<span class="msg-label">Welcome</span><p class="msg-body">' +
          escapeHtml(m.feedback) +
          "</p>"
      );
      showTyping();
    } else if (m.summary) {
      renderSummary(m.summary);
      disableInput();
    }

    scrollToBottom();
  }

  function renderSummary(s) {
    const turns = s.turns || [];
    const turnsHtml = turns
      .map(function (t, i) {
        let block =
          '<div class="turn-card">' +
          '<div class="turn-card-q">Question ' +
          (i + 1) +
          "</div>" +
          '<div class="turn-card-a">' +
          escapeHtml(t.question) +
          "</div>" +
          '<div class="turn-meta">Your response · ' +
          t.response_time_seconds.toFixed(1) +
          "s</div>" +
          '<div class="turn-card-a turn-card-a--answer"><strong>Answer:</strong> ' +
          escapeHtml(t.candidate_answer) +
          "</div>";
        if (t.followup_question && t.followup_answer) {
          block +=
            '<div class="turn-followup"><strong>Follow-up:</strong> ' +
            escapeHtml(t.followup_question) +
            "<br><strong>Your reply:</strong> " +
            escapeHtml(t.followup_answer) +
            "</div>";
        }
        return block + "</div>";
      })
      .join("");

    addMsg(
      "bot",
      '<div class="final-report">' +
        "<h3>Session complete</h3>" +
        '<div class="report-stats">' +
        '<div class="stat-item"><span class="stat-value">' +
        s.overall_score.toFixed(1) +
        '</span><div class="stat-label">Overall</div></div>' +
        '<div class="stat-item"><span class="stat-value">' +
        s.technical_score.toFixed(1) +
        '</span><div class="stat-label">Technical</div></div>' +
        '<div class="stat-item"><span class="stat-value">' +
        s.communication_score.toFixed(1) +
        '</span><div class="stat-label">Communication</div></div>' +
        '<div class="stat-item"><span class="stat-value">' +
        turns.length +
        '</span><div class="stat-label">Questions</div></div>' +
        '<div class="stat-item"><span class="stat-value stat-value--text">' +
        escapeHtml(s.duration) +
        '</span><div class="stat-label">Duration</div></div>' +
        "</div>" +
        '<p class="report-section-title">Responses</p>' +
        '<div class="turn-list">' +
        turnsHtml +
        "</div></div>"
    );
  }

  function addMsg(type, html) {
    const div = document.createElement("div");
    div.className = "msg " + type;
    div.innerHTML = '<div class="bubble">' + html + "</div>";
    chatEl.appendChild(div);
    scrollToBottom();
  }

  function addUserMessage(text) {
    const div = document.createElement("div");
    div.className = "msg user";
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    const label = document.createElement("span");
    label.className = "msg-label";
    label.textContent = "You";
    const body = document.createElement("p");
    body.className = "msg-body";
    body.textContent = text;
    bubble.appendChild(label);
    bubble.appendChild(body);
    div.appendChild(bubble);
    chatEl.appendChild(div);
    scrollToBottom();
  }

  function scrollToBottom() {
    requestAnimationFrame(function () {
      chatEl.scrollTop = chatEl.scrollHeight;
    });
  }

  function showTyping() {
    typingIndicator.classList.add("is-active");
    typingIndicator.setAttribute("aria-hidden", "false");
    scrollToBottom();
  }

  function hideTyping() {
    typingIndicator.classList.remove("is-active");
    typingIndicator.setAttribute("aria-hidden", "true");
  }

  function enableInput() {
    answerInput.disabled = false;
    sendBtn.disabled = false;
    answerInput.focus();
  }

  function disableInput() {
    answerInput.disabled = true;
    sendBtn.disabled = true;
  }

  function updateProgress(q) {
    progressLabel.textContent = "Q " + q + " / " + numQuestions;
  }

  function sendAnswer() {
    const text = answerInput.value.trim();
    if (!text || !connected) return;

    addUserMessage(text);
    ws.send(
      JSON.stringify({
        answer: text,
        paste_count: pasteCount,
        tab_switch_count: tabSwitchCount,
        copy_count: copyCount,
      })
    );

    answerInput.value = "";
    answerInput.style.height = "auto";
    disableInput();
    showTyping();
    pasteCount = 0;
    tabSwitchCount = 0;
    copyCount = 0;
  }

  sendBtn.addEventListener("click", sendAnswer);

  answerInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendAnswer();
    }
  });

  answerInput.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 140) + "px";
  });

  answerInput.addEventListener("paste", function () {
    pasteCount++;
  });
  answerInput.addEventListener("copy", function () {
    copyCount++;
  });
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") tabSwitchCount++;
  });
})();
