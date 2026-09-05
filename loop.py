"""loop.py — the bounded, evidence-gated loop with real stop conditions.

Module 2 (Loop Engineering): This is pure Python so you can SEE the loop logic
clearly. In the full agent it lives inside your LangGraph flow, but the control
logic is exactly this.

The anatomy: trigger (what starts it) → action (what it does) → evidence check
(did it work?) → stop condition (when to quit).

Four stop conditions:
  1. Success — the evidence check passes, exit cleanly
  2. Max iterations — hard cap (e.g. 4 tries) then escalate
  3. No-progress — same failure twice means it's stuck, escalate
  4. Escalate-to-human — graceful exit when it can't win
"""
from verify import verify_draft


def triage_loop(make_draft, product, max_attempts=4):
    """draft -> verify -> retry on fail -> STOP on pass / cap / no-progress.

    Args:
        make_draft: a callable that takes attempt number and returns a draft string
        product: the product name (used in verification)
        max_attempts: hard cap on loop iterations

    Returns:
        {"status": "queued", "draft": ..., "attempts": ...} on pass
        {"status": "escalated", "why": ..., "attempts": ...} on failure
    """
    attempts = 0
    last_reason = None
    no_progress = 0

    while True:
        attempts += 1

        # THE ACTION: call the model to generate a draft
        draft = make_draft(attempt=attempts)

        # THE EVIDENCE CHECK: grade the draft deterministically
        passed, reason = verify_draft(draft, product)
        print(f"  attempt {attempts}: {'PASS' if passed else 'FAIL'} ({reason})")

        # STOP CONDITION 1: success
        if passed:
            return {"status": "queued", "draft": draft, "attempts": attempts}

        # Track no-progress: same failure twice in a row = stuck
        no_progress = no_progress + 1 if reason == last_reason else 0
        last_reason = reason

        # STOP CONDITION 2: stuck on same error (no progress)
        if no_progress >= 2:
            return {
                "status": "escalated",
                "why": "no progress",
                "attempts": attempts,
            }

        # STOP CONDITION 3: hard cap on iterations
        if attempts >= max_attempts:
            return {
                "status": "escalated",
                "why": "hit max attempts",
                "attempts": attempts,
            }
        # Loop continues to the next attempt


if __name__ == "__main__":
    print("Test 1: Succeeds after a fix")
    result1 = triage_loop(
        lambda attempt: "short" if attempt == 1 else
        "Hi Acme, we are fixing the Billing API 500 errors now.",
        "Billing API"
    )
    print(result1)
    print()

    print("Test 2: Impossible task -> escalates, never hangs")
    result2 = triage_loop(
        lambda attempt: "x",  # always fails — too short
        "Billing API"
    )
    print(result2)
