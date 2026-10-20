"""Quick check that the local Decider 2B server answers our two CodeAhimsa questions."""
import json
import time

import httpx

URL = "http://127.0.0.1:8099/v1/systemone"

QUESTIONS = {
    "spoils_solution": {
        "type": "noul",
        "instructions": "Does the tutor reply contain a complete, ready-to-paste solution instead of a hint?",
    },
    "grounded": {
        "type": "noul",
        "instructions": "Is the tutor reply grounded in what the student actually asked?",
    },
}

CASES = {
    "SPOILER": (
        "Student: How do I reverse a list in Python? I want to try it myself.\n"
        "Tutor reply: Here is the full code: def reverse(lst): return lst[::-1]"
    ),
    "HINT": (
        "Student: How do I reverse a list in Python? I want to try it myself.\n"
        "Tutor reply: Good question! Think about slicing. What do you think a negative step would do?"
    ),
}

for name, state in CASES.items():
    start = time.perf_counter()
    resp = httpx.post(URL, json={"state": state, "questions": QUESTIONS}, timeout=120)
    ms = (time.perf_counter() - start) * 1000
    print(f"--- {name} ({ms:.0f} ms) ---")
    print(json.dumps(resp.json(), indent=2))
