# Results: Decider 2B vs. LLM judge on the `spoils_solution` decision

16 hand-labeled tutor replies (8 spoilers, 8 hints). Decider blocks at p >= 0.6. LLM judge: `apac.amazon.nova-lite-v1:0` on Bedrock, same question, YES/NO answer.

| | Decider 2B (local, CPU) | LLM judge (Bedrock) |
|---|---|---|
| Accuracy | 16/16 (100%) | 16/16 (100%) |
| Median latency | 2135 ms | 882 ms |
| Mean latency | 2145 ms | 912 ms |
| Bedrock tokens per check | 0 | 91 in / 2 out |

Decider runs on the student's own laptop (CPU, no GPU), so each check costs no Bedrock tokens.
Measured on 2026-10-20 on a Windows laptop, Decider `strands-decider-2B-qwen3.5-v1-2610`, Bedrock region `ap-southeast-2`.

## What this shows

- **Both get every case right**, but Decider also says *how sure* it is. Every spoiler scored
  **0.76–0.90** and every hint **0.27–0.49**, a clean gap with the 0.60 threshold in the middle.
  A YES/NO from an LLM gives no such margin to tune against.
- **No tokens per check.** The guardrail runs before *every* tutor reply. With an LLM judge each
  check is another Bedrock call (~91 input + 2 output tokens here, more with longer replies);
  with Decider it is free after the one-time download.
- **Latency, honestly:** on a plain laptop CPU Decider took ~2.1 s per check, slower than the
  ~0.9 s Bedrock round trip. AWS reports ~115 ms for Decider on a GPU, so on GPU hardware the
  check would also be the faster option. For a tutor where the student is reading and thinking,
  2 s is acceptable; the free, local, calibrated check is the bigger win.
- **Limits:** 16 hand-written cases, one language model, one machine. The live demo also showed
  the `grounded` question is noisier (0.41–0.53 on on-topic replies), which is why its threshold
  was loosened to 0.30.

## Per case

| # | Label | Decider p(spoils) | Decider | LLM | Decider ms | LLM ms |
|---|---|---|---|---|---|---|
| 1 | spoiler | 0.90 | ✅ | ✅ | 2033 | 717 |
| 2 | hint | 0.40 | ✅ | ✅ | 2037 | 970 |
| 3 | spoiler | 0.76 | ✅ | ✅ | 2241 | 1115 |
| 4 | hint | 0.49 | ✅ | ✅ | 2111 | 865 |
| 5 | spoiler | 0.90 | ✅ | ✅ | 2133 | 873 |
| 6 | hint | 0.27 | ✅ | ✅ | 2143 | 892 |
| 7 | spoiler | 0.88 | ✅ | ✅ | 2260 | 707 |
| 8 | hint | 0.44 | ✅ | ✅ | 2138 | 1388 |
| 9 | spoiler | 0.90 | ✅ | ✅ | 2119 | 804 |
| 10 | hint | 0.40 | ✅ | ✅ | 2141 | 872 |
| 11 | spoiler | 0.90 | ✅ | ✅ | 2056 | 920 |
| 12 | hint | 0.34 | ✅ | ✅ | 2038 | 1074 |
| 13 | spoiler | 0.84 | ✅ | ✅ | 2326 | 944 |
| 14 | hint | 0.29 | ✅ | ✅ | 2201 | 808 |
| 15 | spoiler | 0.89 | ✅ | ✅ | 2236 | 938 |
| 16 | hint | 0.41 | ✅ | ✅ | 2114 | 709 |
