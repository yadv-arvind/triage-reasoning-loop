"""verify.py — the deterministic verification gate the loop uses to grade a draft.

Module 2 (Loop Engineering): The quality check that determines if the agent's
draft is good enough to send to a human. This is DETERMINISTIC (concrete rules,
not an LLM judging itself), which is why loops are trustworthy.

The loop runs: draft -> verify -> (if no pass) revise and retry -> stop on pass/fail.
"""


def verify_draft(draft: str, product: str) -> tuple[bool, str]:
    """Grade a draft. Returns (passed, reason). Deterministic — no LLM judging itself.

    Concrete rules make loops reliable. These rules are NOT opinions; they are
    measurable checks that the draft meets the minimum standard.
    """
    if not draft or len(draft.strip()) < 20:
        return False, "too short"

    if product.lower() not in draft.lower():
        return False, "does not mention the product"

    if len(draft) > 1000:
        return False, "too long"

    # Banned over-promises: things a support team should never auto-send.
    banned = ["guarantee", "definitely won't happen again", "100% fixed"]
    if any(b in draft.lower() for b in banned):
        return False, "contains a banned over-promise"

    return True, "ok"
