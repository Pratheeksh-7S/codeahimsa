"""Terminal chat with CodeAhimsa. Start the Decider server first (see README)."""

import sys

from codeahimsa.tutor import Tutor


def main() -> None:
    # --eager: plain "helpful assistant" prompt that gives full code (demo)
    # --no-guard: turn the Decider guardrail off (to compare with/without)
    eager = "--eager" in sys.argv
    guarded = "--no-guard" not in sys.argv
    tutor = Tutor(eager=eager, guarded=guarded)
    print(f"[mode: {'eager' if eager else 'socratic'} prompt, guardrail {'ON' if guarded else 'OFF'}]")
    print("CodeAhimsa: Hi! What are you working on? (type 'quit' to exit)\n")
    while True:
        student = input("You: ").strip()
        if student.lower() in {"quit", "exit"}:
            break
        if not student:
            continue
        out = tutor.ask(student)
        for d in out["decisions"]:
            if d["verdict"].startswith("guide"):
                draft = d["proposed_reply"].replace("\n", " ")
                print(f"  [BLOCKED draft: {draft[:150]}...]")
            print(f"  [Decider: spoils={d['spoils_solution']:.2f} grounded={d['grounded']:.2f} "
                  f"{d['latency_ms']:.0f}ms -> {d['verdict']}]")
        print(f"\nCodeAhimsa: {out['reply']}\n")


if __name__ == "__main__":
    main()
