"""Terminal chat with CodeAhimsa. Start the Decider server first (see README)."""

from codeahimsa.tutor import Tutor


def main() -> None:
    tutor = Tutor()
    print("CodeAhimsa: Hi! What are you working on? (type 'quit' to exit)\n")
    while True:
        student = input("You: ").strip()
        if student.lower() in {"quit", "exit"}:
            break
        if not student:
            continue
        out = tutor.ask(student)
        d = out["decision"] or {}
        if out["rewrites"]:
            print(f"  [guardrail blocked {out['rewrites']} spoiler draft(s)]")
        if d:
            print(f"  [Decider: spoils={d['spoils_solution']:.2f} grounded={d['grounded']:.2f} "
                  f"{d['latency_ms']:.0f}ms -> {d['verdict']}]")
        print(f"\nCodeAhimsa: {out['reply']}\n")


if __name__ == "__main__":
    main()
