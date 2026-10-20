"""SocraticGuardrail: a Strands InterventionHandler that stops a tutor from spoiling the answer.

The agent must talk to the learner through a reply tool (default name: "send_to_student").
Before that tool runs, Decider 2B scores the proposed message. The model classifies,
this code decides: Proceed, or Guide the model back to rewrite the reply as a hint.
"""

import json
import logging
from pathlib import Path

from strands.interventions import Guide, InterventionHandler, Proceed, Transform

from .client import DeciderClient
from .questions import GROUNDED_MIN, QUESTIONS, SPOIL_BLOCK, build_state

log = logging.getLogger(__name__)

SPOIL_FEEDBACK = (
    "Blocked by the Socratic guardrail: that reply gives away a complete solution. "
    "Rewrite it as a hint. Do not include working code for the whole task. Point at the "
    "concept, show at most one small unrelated example, and end with a guiding question. "
    "Then call send_to_student again."
)
OFF_TOPIC_FEEDBACK = (
    "Blocked by the Socratic guardrail: that reply does not address what the student asked. "
    "Re-read the student's last message and answer that, as a hint. Then call send_to_student again."
)

# Sent instead of the model's draft when it keeps spoiling after max_rewrites (fail closed).
FALLBACK_REPLY = (
    "I can't hand you the finished solution, but let's get there together. "
    "What have you tried so far, and which part feels stuck?"
)


def _text_of(message: dict) -> str:
    return " ".join(block.get("text", "") for block in message.get("content", []) if "text" in block)


def _last_student_message(agent) -> str:
    """Latest user turn that contains real text (skips tool-result turns)."""
    for message in reversed(getattr(agent, "messages", []) or []):
        if message.get("role") == "user":
            text = _text_of(message).strip()
            if text:
                return text
    return ""


class SocraticGuardrail(InterventionHandler):
    name = "socratic-guardrail"

    def __init__(
        self,
        reply_tool: str = "send_to_student",
        decider: DeciderClient | None = None,
        max_rewrites: int = 2,
        log_path: str | None = "decisions.jsonl",
    ):
        super().__init__()
        self.reply_tool = reply_tool
        self.decider = decider or DeciderClient()
        self.max_rewrites = max_rewrites
        self.log_path = Path(log_path) if log_path else None
        self.rewrites = 0
        self.last_decision: dict | None = None
        self.decisions: list[dict] = []  # every check made during the current turn

    def new_turn(self) -> None:
        """Call once per student message so the rewrite budget resets."""
        self.rewrites = 0
        self.last_decision = None
        self.decisions = []

    def before_tool_call(self, event, **kwargs):
        tool_use = event.tool_use
        if tool_use.get("name") != self.reply_tool:
            return Proceed()

        proposed = str(tool_use.get("input", {}).get("message", ""))
        student = _last_student_message(event.agent)
        answers, latency_ms = self.decider.ask(build_state(student, proposed), QUESTIONS)
        spoil = answers["spoils_solution"]["noul"]
        grounded = answers["grounded"]["noul"]

        if spoil >= SPOIL_BLOCK:
            verdict, feedback = "guide_hint", SPOIL_FEEDBACK
        elif grounded < GROUNDED_MIN:
            verdict, feedback = "guide_on_topic", OFF_TOPIC_FEEDBACK
        else:
            verdict, feedback = "proceed", None

        out_of_retries = feedback is not None and self.rewrites >= self.max_rewrites
        if out_of_retries:
            # Out of retries: never deliver the spoiler, send a safe Socratic fallback instead.
            verdict, feedback = "fallback", None

        self.last_decision = {
            "student": student,
            "proposed_reply": proposed,
            "spoils_solution": spoil,
            "grounded": grounded,
            "latency_ms": round(latency_ms, 1),
            "verdict": verdict,
            "rewrite": self.rewrites,
        }
        self.decisions.append(self.last_decision)
        self._log(self.last_decision)

        if feedback:
            self.rewrites += 1
            return Guide(feedback=feedback)
        if out_of_retries:
            return Transform(
                apply=lambda e: e.tool_use["input"].__setitem__("message", FALLBACK_REPLY),
                reason="replaced spoiler with fallback hint",
            )
        return Proceed()

    def _log(self, record: dict) -> None:
        log.info("guardrail %s spoil=%.2f grounded=%.2f %.0fms",
                 record["verdict"], record["spoils_solution"], record["grounded"], record["latency_ms"])
        if self.log_path:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
