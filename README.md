# CodeAhimsa

A campus coding-practice tutor for beginners that refuses to hand over the answer.
Amazon Bedrock does the tutoring; **Strands Decider 2B** checks every reply before the student sees it,
and blocks replies that would spoil the exercise. Pattern: **#guardrails** · #strands-decider-2b

## Reusable decision pattern
See [`patterns/socratic_guardrail/`](patterns/socratic_guardrail/README.md).

## Run it
```bash
python -m venv .venv && .venv\Scripts\activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# terminal 1
strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --port 8099
# terminal 2 (needs AWS credentials with Bedrock access)
python chat.py
```
Defaults: model `apac.amazon.nova-lite-v1:0` in `ap-southeast-2`. Override with
`CODEAHIMSA_MODEL_ID` and `AWS_REGION`.

## License
Apache-2.0
