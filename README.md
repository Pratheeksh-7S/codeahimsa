# CodeAhimsa

A campus coding-practice tutor for beginners that refuses to hand over the answer.
Amazon Bedrock does the tutoring; **Strands Decider 2B** checks every reply before the student sees it,
and blocks replies that would spoil the exercise. Pattern: **#guardrails** · #strands-decider-2b

▶️ **Demo video (2:54):** https://youtu.be/l1YLZODMKss

## Results
Decider 2B vs. a Bedrock LLM judge on 16 labeled replies: both 16/16, Decider at zero Bedrock tokens. See [`docs/results.md`](docs/results.md) (`python scripts/evaluate.py`).

## Reusable decision pattern
See [`patterns/socratic_guardrail/`](patterns/socratic_guardrail/README.md).

## Run it
```bash
python -m venv .venv && .venv\Scripts\activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# terminal 1
strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --port 8099
# terminal 2 (needs AWS credentials with Bedrock access, e.g. AWS_BEARER_TOKEN_BEDROCK)
streamlit run app.py      # web chat
python chat.py            # or terminal chat
```
Defaults: model `apac.amazon.nova-lite-v1:0` in `ap-southeast-2`. Override with
`CODEAHIMSA_MODEL_ID` and `AWS_REGION`.

## See the guardrail work
A well-prompted tutor rarely spoils the answer, so there is a demo switch that swaps in an
"eager" prompt (a plain helpful assistant that hands over full code):

| Command | What happens |
|---|---|
| `python chat.py --eager --no-guard` | Full ready-to-paste solution reaches the student |
| `python chat.py --eager` | Decider 2B scores the draft (e.g. spoils 0.88), blocks it, and the student gets a hint |

In the web app, the same switches are toggles in the sidebar, and each blocked draft can be expanded.

## License
Apache-2.0
