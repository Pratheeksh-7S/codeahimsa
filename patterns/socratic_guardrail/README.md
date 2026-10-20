# Reusable Decider 2B pattern: Socratic guardrail (#guardrails)

Stops an agent from handing over a finished answer when it should be teaching.
Works for any Strands agent that talks to its user through a reply tool.

## The decision
Two yes/no (`noul`) questions, asked of Strands Decider 2B before the reply tool runs:

| name | question | action |
|---|---|---|
| `spoils_solution` | Does the tutor reply contain a complete, ready-to-paste solution instead of a hint? | `>= 0.60` → `Guide` the model to rewrite as a hint |
| `grounded` | Is the tutor reply grounded in what the student actually asked? | `< 0.45` → `Guide` the model back on topic |

State string: `"Student: <last student message>\nTutor reply: <proposed reply>"`.
"The model classifies, the code decides": thresholds live in `questions.py`.

## Use it in your agent
```python
from strands import Agent, tool
from patterns.socratic_guardrail import SocraticGuardrail

@tool
def send_to_student(message: str) -> str:
    """Send your reply to the student."""
    ...

agent = Agent(tools=[send_to_student], interventions=[SocraticGuardrail()])
```
1. Run Decider locally: `strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --port 8099`
   (or set `STRANDS_DECIDER_URL`).
2. Tell your agent (system prompt) to reply only through the reply tool.
3. Call `guardrail.new_turn()` before each user message to reset the rewrite budget (default 2).

Every decision is appended to `decisions.jsonl` (scores, latency, verdict) so you can measure it.
