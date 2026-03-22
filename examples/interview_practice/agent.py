"""
Standalone AI Interview Practice — adaptive questions via pydantic-graph + WebSocket.

Run from repo root::

    uv run uvicorn examples.interview_practice.agent:app --host 0.0.0.0 --port 8765 --reload
"""
from __future__ import annotations

import json
import logging
import secrets
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Union

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from common.pydantic_ai_client import PydanticAIClient

# ───────── Logging ────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("interview")

# ───────── Pydantic schemas ──────────────────────────────────────────────────


class InterviewConfig(BaseModel):
    job_description: str
    goal: str = "general"
    difficulty: str = "medium"
    num_questions: int = Field(default=5, ge=1, le=20)


class TailoredQuestion(BaseModel):
    question: str
    ideal_answer: str
    tags: list[str]
    difficulty: str


@dataclass
class ConversationEntry:
    speaker: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    message_type: str | None = None


class InterviewTurn(BaseModel):
    question: str
    ideal_answer: str
    candidate_answer: str
    followup_question: str | None = None
    followup_answer: str | None = None
    followup_reason: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)
    response_time_seconds: float
    followup_response_time_seconds: float | None = None
    paste_count: int = 0
    tab_switch_count: int = 0
    copy_count: int = 0
    conversation_history: list[dict] = Field(default_factory=list)


class ResponseType(str, Enum):
    answer = "answer"
    clarification = "clarification"
    unrelated = "unrelated"


class ClassificationOutput(BaseModel):
    classification: ResponseType
    explanation: str


class FollowUpDecision(BaseModel):
    needs_followup: bool
    followup_question: str | None = None
    reason: str


class Evaluation(BaseModel):
    technical_score: int
    communication_score: int
    feedback: str
    strengths: list[str]
    improvements: list[str]


class FinalReport(BaseModel):
    session_id: str
    turns: list[InterviewTurn]
    evaluations: list[Evaluation]
    overall_score: float
    technical_score: float
    communication_score: float
    duration: str


# ───────── Agent clients (all OpenAI) ─────────────────────────────────────────

question_gen_client = PydanticAIClient(
    provider="openai",
    model_name="gpt-4o-mini",
    system_prompt=(
        "You are a senior technical interviewer who crafts targeted interview questions.\n\n"
        "RULES:\n"
        "- Generate exactly ONE question per request.\n"
        "- Adapt the question to the job description, interview goal, and requested difficulty.\n"
        "- If prior Q&A history is provided, adjust: avoid repeating topics already covered, "
        "probe weak areas the candidate exposed, and escalate or simplify difficulty based on their performance.\n"
        "- For 'adaptive' difficulty: start at the requested baseline, increase after strong answers "
        "(score >= 75), decrease after weak answers (score < 50).\n"
        "- Tags should reflect the main topics the question covers.\n"
        "- The ideal_answer should be concise (3-5 sentences) but comprehensive enough for evaluation.\n"
        "- NEVER repeat a question that was already asked."
    ),
    output_type=TailoredQuestion,
    keep_history=False,
)

evaluation_client = PydanticAIClient(
    provider="openai",
    model_name="gpt-4o-mini",
    system_prompt=(
        "You are an expert interview evaluator.\n\n"
        "Return JSON with fields:\n"
        "- technical_score: 0-100\n"
        "- communication_score: 0-100\n"
        "- feedback: 2-3 sentence summary\n"
        "- strengths: list of strengths\n"
        "- improvements: list of areas to improve"
    ),
    output_type=Evaluation,
    keep_history=False,
)

follow_up_client = PydanticAIClient(
    provider="openai",
    model_name="gpt-4o-mini",
    system_prompt=(
        "You decide whether a follow-up question is needed.\n"
        "Set needs_followup=true ONLY when the answer is vague or missing critical detail.\n"
        "If uncertain, default to needs_followup=false.\n"
        "Follow-up must be ONE short question (max 25 words).\n"
        "Return JSON: needs_followup, followup_question (null if false), reason (max 15 words)."
    ),
    output_type=FollowUpDecision,
    keep_history=False,
)

classification_client = PydanticAIClient(
    provider="openai",
    model_name="gpt-4o-mini",
    system_prompt=(
        "Classify a candidate response as:\n"
        "- 'answer': attempting to answer (even if incomplete)\n"
        "- 'clarification': asking for help understanding the question\n"
        "- 'unrelated': off-topic or inappropriate\n"
        "If the user says they don't know, classify as 'answer'.\n"
        "Return JSON: classification, explanation."
    ),
    output_type=ClassificationOutput,
    keep_history=False,
)


# ───────── Helpers ────────────────────────────────────────────────────────────

def _build_history_summary(state: InterviewState) -> str:
    """Summarise prior turns + scores for the question generator."""
    if not state.turns:
        return "No prior questions yet."
    lines: list[str] = []
    for idx, (aq, t, ev) in enumerate(zip(state.asked_questions, state.turns, state.evaluations), 1):
        overall = (ev.technical_score + ev.communication_score) / 2
        lines.append(
            f"Q{idx} [{', '.join(aq.tags)}] (difficulty: {aq.difficulty}) — "
            f"tech {ev.technical_score}, comm {ev.communication_score}, overall {overall:.0f}\n"
            f"  Question: {t.question[:120]}\n"
            f"  Candidate said: {t.candidate_answer[:120]}"
        )
    return "\n".join(lines)


def _resolve_difficulty(config: InterviewConfig, evaluations: list[Evaluation]) -> str:
    """For 'adaptive' difficulty, compute the effective level from recent scores."""
    if config.difficulty != "adaptive" or not evaluations:
        return config.difficulty if config.difficulty != "adaptive" else "medium"
    last_overall = (evaluations[-1].technical_score + evaluations[-1].communication_score) / 2
    if last_overall >= 75:
        return "hard"
    elif last_overall < 50:
        return "easy"
    return "medium"


# ───────── Interview state ────────────────────────────────────────────────────

@dataclass
class InterviewState:
    session_id: str
    config: InterviewConfig
    ws: WebSocket | None = None

    turns: list[InterviewTurn] = field(default_factory=list)
    evaluations: list[Evaluation] = field(default_factory=list)
    asked_questions: list[TailoredQuestion] = field(default_factory=list)
    i: int = 0
    start_time: datetime = field(default_factory=datetime.now)

    _current_question: TailoredQuestion | None = None
    _answer: str | None = None
    _t_question: datetime | None = None
    _classification: ClassificationOutput | None = None
    _followup_decision: FollowUpDecision | None = None
    _is_followup: bool = False
    _current_turn: InterviewTurn | None = None
    _paste_count: int = 0
    _tab_switch_count: int = 0
    _copy_count: int = 0
    _current_conversation: list[ConversationEntry] = field(default_factory=list)

    def add_conversation_entry(self, speaker: str, message: str, message_type: str | None = None) -> None:
        self._current_conversation.append(
            ConversationEntry(speaker=speaker, message=message, message_type=message_type)
        )

    def get_conversation_context(self) -> str:
        if not self._current_conversation:
            return "No conversation history yet.\n"
        lines = ["=== CONVERSATION HISTORY FOR THIS TURN ==="]
        for e in self._current_conversation:
            label = "AI Interviewer" if e.speaker == "interviewer" else "Candidate"
            lines.append(f"{label} ({e.message_type or 'message'}): {e.message}")
        return "\n".join(lines) + "\n\n"

    def reset_conversation_for_new_turn(self) -> None:
        self._current_conversation = []


# ───────── Graph nodes ────────────────────────────────────────────────────────

@dataclass
class AskQuestion(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> "AwaitResponse":
        st = ctx.state
        effective_difficulty = _resolve_difficulty(st.config, st.evaluations)
        history_summary = _build_history_summary(st)

        gen_prompt = (
            f"=== JOB DESCRIPTION ===\n{st.config.job_description}\n\n"
            f"=== INTERVIEW SETTINGS ===\n"
            f"Goal: {st.config.goal}\n"
            f"Target difficulty for this question: {effective_difficulty}\n"
            f"Question number: {st.i + 1} of {st.config.num_questions}\n\n"
            f"=== PRIOR Q&A HISTORY ===\n{history_summary}\n\n"
            "Generate the next interview question."
        )
        res = await question_gen_client.run(gen_prompt)
        q: TailoredQuestion = res.output
        st._current_question = q
        st.asked_questions.append(q)

        st._t_question = datetime.now()
        st.reset_conversation_for_new_turn()
        st.add_conversation_entry("interviewer", q.question, "question")

        logger.info("Q%d/%d [%s]: %s", st.i + 1, st.config.num_questions, q.difficulty, q.question[:80])
        await st.ws.send_json({
            "question": q.question,
            "question_number": st.i + 1,
            "difficulty": q.difficulty,
        })
        return AwaitResponse()


@dataclass
class AwaitResponse(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> "ClassifyResponse":
        msg = await ctx.state.ws.receive_text()
        try:
            data = json.loads(msg)
            answer = data["answer"]
            ctx.state._paste_count = int(data.get("paste_count", 0))
            ctx.state._tab_switch_count = int(data.get("tab_switch_count", 0))
            ctx.state._copy_count = int(data.get("copy_count", 0))
        except Exception:
            answer = msg
            ctx.state._paste_count = ctx.state._tab_switch_count = ctx.state._copy_count = 0
        ctx.state._answer = answer
        ctx.state.add_conversation_entry("candidate", answer, "response")
        return ClassifyResponse()


@dataclass
class ClassifyResponse(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> Union["SendClarification", "SendWarning", "CheckFollowUp"]:
        q = ctx.state._current_question
        prompt = (
            f"Question: {q.question}\nDifficulty: {q.difficulty}\nTopics: {', '.join(q.tags)}\n\n"
            f"{ctx.state.get_conversation_context()}"
            "Classify the candidate's latest response."
        )
        res = await classification_client.run(prompt)
        ctx.state._classification = res.output
        logger.info("Classification: %s", res.output.classification)
        if res.output.classification == ResponseType.answer:
            return CheckFollowUp()
        elif res.output.classification == ResponseType.clarification:
            return SendClarification()
        return SendWarning()


@dataclass
class SendClarification(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> AwaitResponse:
        text = ctx.state._classification.explanation
        ctx.state.add_conversation_entry("interviewer", text, "clarification")
        await ctx.state.ws.send_json({"clarification": text})
        return AwaitResponse()


@dataclass
class SendWarning(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> AwaitResponse:
        text = ctx.state._classification.explanation
        ctx.state.add_conversation_entry("interviewer", text, "warning")
        await ctx.state.ws.send_json({"warning": text})
        return AwaitResponse()


@dataclass
class CheckFollowUp(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> Union["AskFollowUp", "EvaluateAnswer"]:
        if ctx.state._is_followup:
            return EvaluateAnswer()
        q = ctx.state._current_question
        if not ctx.state._current_turn:
            ctx.state._current_turn = InterviewTurn(
                question=q.question,
                ideal_answer=q.ideal_answer,
                candidate_answer=ctx.state._answer,
                response_time_seconds=(datetime.now() - ctx.state._t_question).total_seconds(),
                paste_count=ctx.state._paste_count,
                tab_switch_count=ctx.state._tab_switch_count,
                copy_count=ctx.state._copy_count,
            )
        prompt = (
            f"Question: {q.question}\nIdeal: {q.ideal_answer}\n\n"
            f"{ctx.state.get_conversation_context()}"
            "Decide if a follow-up is needed."
        )
        res = await follow_up_client.run(prompt)
        ctx.state._followup_decision = res.output
        if res.output.needs_followup and res.output.followup_question:
            ctx.state._current_turn.followup_question = res.output.followup_question
            ctx.state._current_turn.followup_reason = res.output.reason
            return AskFollowUp()
        return EvaluateAnswer()


@dataclass
class AskFollowUp(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> AwaitResponse:
        ctx.state._t_question = datetime.now()
        ctx.state._is_followup = True
        fq = ctx.state._followup_decision.followup_question
        ctx.state.add_conversation_entry("interviewer", fq, "followup")
        await ctx.state.ws.send_json({"followup_question": fq, "reason": ctx.state._followup_decision.reason})
        return AwaitResponse()


@dataclass
class EvaluateAnswer(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> "NextQuestion":
        q = ctx.state._current_question
        if ctx.state._is_followup and ctx.state._current_turn:
            ctx.state._current_turn.followup_answer = ctx.state._answer
            ctx.state._current_turn.followup_response_time_seconds = (
                datetime.now() - ctx.state._t_question
            ).total_seconds()
            ctx.state._is_followup = False

        if not ctx.state._current_turn:
            ctx.state._current_turn = InterviewTurn(
                question=q.question,
                ideal_answer=q.ideal_answer,
                candidate_answer=ctx.state._answer,
                response_time_seconds=(datetime.now() - ctx.state._t_question).total_seconds(),
                paste_count=ctx.state._paste_count,
                tab_switch_count=ctx.state._tab_switch_count,
                copy_count=ctx.state._copy_count,
            )

        t = ctx.state._current_turn
        t.conversation_history = [
            {"speaker": e.speaker, "message": e.message, "message_type": e.message_type, "timestamp": e.timestamp.isoformat()}
            for e in ctx.state._current_conversation
        ]

        prompt = (
            f"Question: {t.question}\nIdeal: {t.ideal_answer}\n\n"
            f"{ctx.state.get_conversation_context()}"
            "Evaluate the candidate's complete interaction."
        )
        ev = await evaluation_client.run(prompt)
        ctx.state.turns.append(t)
        ctx.state.evaluations.append(ev.output)
        ctx.state._current_turn = None

        overall_local = (ev.output.technical_score + ev.output.communication_score) / 2
        payload = ev.output.model_dump()
        payload["overall"] = overall_local
        await ctx.state.ws.send_json({"evaluation": payload})
        return NextQuestion()


@dataclass
class NextQuestion(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> Union[AskQuestion, "EndInterview"]:
        ctx.state.i += 1
        if ctx.state.i < ctx.state.config.num_questions:
            return AskQuestion()
        return EndInterview()


@dataclass
class EndInterview(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> End[InterviewState]:
        evs = ctx.state.evaluations
        if evs:
            tech = sum(e.technical_score for e in evs) / len(evs)
            comm = sum(e.communication_score for e in evs) / len(evs)
            overall = (tech + comm) / 2
        else:
            overall = tech = comm = 0.0
        duration = datetime.now() - ctx.state.start_time

        report = FinalReport(
            session_id=ctx.state.session_id,
            turns=ctx.state.turns,
            evaluations=ctx.state.evaluations,
            overall_score=overall,
            technical_score=tech,
            communication_score=comm,
            duration=str(duration),
        )
        await ctx.state.ws.send_json({"summary": report.model_dump(mode="json")})
        await ctx.state.ws.close()
        logger.info("Interview %s finished — score %.1f", ctx.state.session_id, overall)
        return End(ctx.state)


live_interview_graph = Graph(
    nodes=[
        AskQuestion, AwaitResponse, ClassifyResponse,
        SendClarification, SendWarning,
        EvaluateAnswer, CheckFollowUp,
        AskFollowUp, NextQuestion, EndInterview,
    ]
)


# ───────── FastAPI app ────────────────────────────────────────────────────────

app = FastAPI(title="AI Interview Practice")

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

pending_sessions: dict[str, InterviewConfig] = {}


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse((static_dir / "index.html").read_text())


@app.post("/api/start")
async def start_interview(config: InterviewConfig):
    session_id = secrets.token_urlsafe(12)
    pending_sessions[session_id] = config
    logger.info("Session %s created — %d questions, difficulty=%s, goal=%s",
                session_id, config.num_questions, config.difficulty, config.goal)
    return {"session_id": session_id}


@app.websocket("/ws/interview/{session_id}")
async def ws_interview(websocket: WebSocket, session_id: str):
    config = pending_sessions.pop(session_id, None)
    if config is None:
        await websocket.close(code=4404)
        return

    await websocket.accept()
    logger.info("WebSocket connected for session %s", session_id)

    state = InterviewState(
        session_id=session_id,
        config=config,
        ws=websocket,
    )

    await websocket.send_json({
        "feedback": (
            f"Welcome! Starting a {config.difficulty} interview with {config.num_questions} questions. "
            f"Goal: {config.goal.replace('-', ' ')}. Generating your first question…"
        ),
    })

    try:
        await live_interview_graph.run(AskQuestion(), state=state)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for session %s", session_id)
    except Exception as e:
        logger.error("Interview error (%s): %s", session_id, e, exc_info=True)
        try:
            await websocket.close(code=1011)
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("examples.interview_practice.agent:app", host="0.0.0.0", port=8765, reload=False)
