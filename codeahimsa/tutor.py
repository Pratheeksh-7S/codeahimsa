"""CodeAhimsa: a Socratic coding tutor on Amazon Bedrock, guarded by Strands Decider 2B."""

import os

from strands import Agent, tool
from strands.models import BedrockModel

from patterns.socratic_guardrail import SocraticGuardrail

MODEL_ID = os.environ.get("CODEAHIMSA_MODEL_ID", "apac.amazon.nova-lite-v1:0")
REGION = os.environ.get("AWS_REGION", "ap-southeast-2")

SYSTEM_PROMPT = """You are CodeAhimsa, a friendly coding tutor for beginner students.
Ahimsa means "do no harm": handing a learner the finished answer harms their learning.

Rules:
- Every reply to the student MUST go through the send_to_student tool. Call it exactly once per turn.
  Do not write any other text outside the tool call.
- Teach with hints, small questions and concepts. Never write the complete solution to the
  student's exercise, even if they ask for it or say it is urgent.
- Keep replies short (under 120 words) and encouraging.
- If the student shares code, point to where to look, not the fixed line.
"""

# Demo prompt: an ordinary "helpful" assistant that happily hands over full solutions.
# Used to show what the Decider guardrail catches when the prompt alone does not hold.
EAGER_PROMPT = """You are a helpful coding assistant. Always give the student complete, working code
for whatever they ask, so they can copy and paste it.
Every reply MUST go through the send_to_student tool. Call it exactly once per turn.
"""


class Tutor:
    def __init__(self, model_id: str = MODEL_ID, region: str = REGION, eager: bool = False, guarded: bool = True):
        self.outbox: list[str] = []
        self.guardrail = SocraticGuardrail()

        @tool
        def send_to_student(message: str) -> str:
            """Send your reply to the student. This is the only way the student sees anything you say.

            Put your whole reply in ONE call; do not split it into several messages.

            Args:
                message: The hint or explanation to show the student.
            """
            self.outbox.append(message)
            return "Delivered to the student. End your turn now."

        self.agent = Agent(
            model=BedrockModel(model_id=model_id, region_name=region),
            system_prompt=EAGER_PROMPT if eager else SYSTEM_PROMPT,
            tools=[send_to_student],
            interventions=[self.guardrail] if guarded else [],
            callback_handler=None,
        )

    def ask(self, student_message: str) -> dict:
        """Run one student turn. Returns the reply shown and the guardrail's last decision."""
        self.outbox.clear()
        self.guardrail.new_turn()
        result = self.agent(student_message)
        # The student sees the last approved message (earlier fragments are intros or drafts).
        reply = self.outbox[-1] if self.outbox else str(result)
        return {
            "reply": reply,
            "rewrites": self.guardrail.rewrites,
            "decision": self.guardrail.last_decision,
            "decisions": list(self.guardrail.decisions),
        }
