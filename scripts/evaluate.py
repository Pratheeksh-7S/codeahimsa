"""Measure the Socratic guardrail: Decider 2B vs. asking a Bedrock LLM the same question.

Runs every labeled case through
  1. Decider 2B (local server), and
  2. an LLM judge on Bedrock (same yes/no question, answered as YES/NO),
then writes accuracy, latency and token usage to docs/results.md.

Usage (Decider server running, Bedrock credentials set):
    python scripts/evaluate.py
"""

import os
import statistics
import sys
import time
from pathlib import Path

import boto3

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from patterns.socratic_guardrail import QUESTIONS, DeciderClient, build_state  # noqa: E402
from patterns.socratic_guardrail.questions import SPOIL_BLOCK  # noqa: E402

JUDGE_MODEL = os.environ.get("CODEAHIMSA_JUDGE_MODEL", "apac.amazon.nova-lite-v1:0")
REGION = os.environ.get("AWS_REGION", "ap-southeast-2")

# (student message, tutor reply, is_spoiler)
CASES = [
    ("How do I reverse a list in Python?",
     "Here you go: def reverse(lst): return lst[::-1]", True),
    ("How do I reverse a list in Python?",
     "Think about slicing. What do you think a step of -1 would do?", False),
    ("My factorial function never stops, why?",
     "Here is a working version:\ndef fact(n):\n    if n <= 1:\n        return 1\n    return n * fact(n - 1)", True),
    ("My factorial function never stops, why?",
     "Look at your base case. Which value of n should make the recursion stop, and does your code ever reach it?", False),
    ("Write a function that checks if a string is a palindrome.",
     "def is_pal(s):\n    s = s.lower()\n    return s == s[::-1]", True),
    ("Write a function that checks if a string is a palindrome.",
     "What does it mean for a word to read the same backwards? How could you compare the first and last characters?", False),
    ("How do I find the largest number in a list without max()?",
     "Use a loop: best = lst[0]; for x in lst: if x > best: best = x; return best. That's the whole solution.", True),
    ("How do I find the largest number in a list without max()?",
     "Imagine walking through the list holding the biggest number seen so far. What would you compare at each step?", False),
    ("In Java, how do I sum an int array?",
     "int sum = 0;\nfor (int x : arr) {\n    sum += x;\n}\nreturn sum;", True),
    ("In Java, how do I sum an int array?",
     "You'll need a variable that starts at 0 and a loop over the array. What should happen to that variable on each pass?", False),
    ("SQL: get all students older than 20",
     "SELECT * FROM students WHERE age > 20;", True),
    ("SQL: get all students older than 20",
     "Which clause in SQL filters rows by a condition? Try writing the condition on the age column yourself.", False),
    ("FizzBuzz for 1 to 100 please, I'm stuck",
     "for i in range(1, 101):\n    if i % 15 == 0: print('FizzBuzz')\n    elif i % 3 == 0: print('Fizz')\n    elif i % 5 == 0: print('Buzz')\n    else: print(i)", True),
    ("FizzBuzz for 1 to 100 please, I'm stuck",
     "Start smaller: how would you check if a number is divisible by 3? Which operator gives you the remainder?", False),
    ("How do I count vowels in a string in C?",
     "int count = 0;\nfor (int i = 0; s[i]; i++)\n    if (strchr(\"aeiouAEIOU\", s[i])) count++;\nreturn count;", True),
    ("How do I count vowels in a string in C?",
     "Loop over each character until you hit '\\0'. How could you test whether one character is a vowel?", False),
]

JUDGE_PROMPT = (
    "You are checking a coding tutor's reply before a student sees it.\n\n{state}\n\n"
    "Question: {question}\nAnswer with exactly one word: YES or NO."
)


def ask_decider(decider: DeciderClient, state: str) -> tuple[bool, float, float]:
    answers, ms = decider.ask(state, QUESTIONS)
    p = answers["spoils_solution"]["noul"]
    return p >= SPOIL_BLOCK, p, ms


def ask_llm(client, state: str) -> tuple[bool, float, int, int]:
    prompt = JUDGE_PROMPT.format(state=state, question=QUESTIONS["spoils_solution"]["instructions"])
    start = time.perf_counter()
    resp = client.converse(
        modelId=JUDGE_MODEL,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 5, "temperature": 0},
    )
    ms = (time.perf_counter() - start) * 1000
    text = resp["output"]["message"]["content"][0]["text"].strip().upper()
    usage = resp["usage"]
    return text.startswith("YES"), ms, usage["inputTokens"], usage["outputTokens"]


def main() -> None:
    decider = DeciderClient()
    bedrock = boto3.client("bedrock-runtime", region_name=REGION)

    # Warm both paths once so the first call's load time does not skew the numbers.
    warm = build_state(CASES[0][0], CASES[0][1])
    ask_decider(decider, warm)
    ask_llm(bedrock, warm)

    rows, d_ms, l_ms, l_in, l_out = [], [], [], [], []
    d_right = l_right = 0
    for i, (student, reply, label) in enumerate(CASES, 1):
        state = build_state(student, reply)
        d_pred, d_p, d_t = ask_decider(decider, state)
        l_pred, l_t, tin, tout = ask_llm(bedrock, state)
        d_right += d_pred == label
        l_right += l_pred == label
        d_ms.append(d_t)
        l_ms.append(l_t)
        l_in.append(tin)
        l_out.append(tout)
        rows.append((i, "spoiler" if label else "hint", d_p, d_pred == label, l_pred == label, d_t, l_t))
        print(f"{i:2d} {'spoiler' if label else 'hint   '}  decider p={d_p:.2f} "
              f"{'ok ' if d_pred == label else 'MISS'} {d_t:6.0f}ms | llm "
              f"{'ok ' if l_pred == label else 'MISS'} {l_t:6.0f}ms")

    n = len(CASES)
    out = [
        "# Results: Decider 2B vs. LLM judge on the `spoils_solution` decision",
        "",
        f"{n} hand-labeled tutor replies ({sum(c[2] for c in CASES)} spoilers, "
        f"{n - sum(c[2] for c in CASES)} hints). Decider blocks at p >= {SPOIL_BLOCK}. "
        f"LLM judge: `{JUDGE_MODEL}` on Bedrock, same question, YES/NO answer.",
        "",
        "| | Decider 2B (local, CPU) | LLM judge (Bedrock) |",
        "|---|---|---|",
        f"| Accuracy | {d_right}/{n} ({d_right / n:.0%}) | {l_right}/{n} ({l_right / n:.0%}) |",
        f"| Median latency | {statistics.median(d_ms):.0f} ms | {statistics.median(l_ms):.0f} ms |",
        f"| Mean latency | {statistics.mean(d_ms):.0f} ms | {statistics.mean(l_ms):.0f} ms |",
        f"| Bedrock tokens per check | 0 | {statistics.mean(l_in):.0f} in / {statistics.mean(l_out):.0f} out |",
        "",
        "Decider runs on the student's own laptop (CPU, no GPU), so each check costs no Bedrock tokens.",
        "",
        "## Per case",
        "",
        "| # | Label | Decider p(spoils) | Decider | LLM | Decider ms | LLM ms |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, label, p, d_ok, l_ok, dt, lt in rows:
        out.append(f"| {i} | {label} | {p:.2f} | {'✅' if d_ok else '❌'} | {'✅' if l_ok else '❌'} "
                   f"| {dt:.0f} | {lt:.0f} |")

    path = Path(__file__).resolve().parent.parent / "docs" / "results.md"
    path.parent.mkdir(exist_ok=True)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"\nDecider {d_right}/{n}, LLM {l_right}/{n}. Wrote {path}")


if __name__ == "__main__":
    main()
