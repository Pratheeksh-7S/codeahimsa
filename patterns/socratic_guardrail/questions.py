"""The typed questions handed to Decider 2B, and how the state string is built."""

# Two yes/no ("noul") questions. Decider returns the probability of "yes" for each.
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

# Policy thresholds. Tuned on our own test prompts; see docs/results.md.
SPOIL_BLOCK = 0.60  # spoils_solution >= this  -> send back as a hint
GROUNDED_MIN = 0.30  # grounded < this          -> send back to stay on topic


def build_state(student_message: str, proposed_reply: str) -> str:
    """The state Decider reads: what the student said, and what the tutor is about to send."""
    return f"Student: {student_message}\nTutor reply: {proposed_reply}"
