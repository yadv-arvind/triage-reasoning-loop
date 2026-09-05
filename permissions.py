"""permissions.py — the permission gate layer of the harness.

Module 1 (Harness Engineering - Layer 3: Permissions):

The permission gate ensures the agent can PROPOSE but never EXECUTE irreversible actions.

Core principle:
  Agent → (calls tool) → Permission Gate → (queues for human review) → Human Approval → Action

In this demo:
  - Agent calls: draft_reply("T-101", "Dear customer...")
  - Permission Gate: Appends to REVIEW_QUEUE
  - Never Sends: draft_reply NEVER sends to customer
  - Human Decides: A human must approve before anything reaches the customer

This is what makes the agent safe. It can suggest, but never act without permission.
"""

# The permission gate: a queue for human review
REVIEW_QUEUE = []


def queue_draft_for_review(ticket_id: str, draft_text: str) -> dict:
    """Queue a draft reply for human review.

    This is the permission gate made concrete. The agent proposes, this gate holds it.
    A human must explicitly approve before the draft reaches the customer.

    Args:
        ticket_id: The ticket being replied to
        draft_text: The proposed draft reply

    Returns:
        dict: Status of the queue operation
    """
    review_item = {
        "ticket_id": ticket_id,
        "draft": draft_text,
        "status": "pending_review",
        "approved": False,
    }

    REVIEW_QUEUE.append(review_item)

    return {
        "status": "queued",
        "message": f"Draft for {ticket_id} queued for human review",
        "queue_position": len(REVIEW_QUEUE),
    }


def get_review_queue() -> list:
    """Get all drafts waiting for human review.

    Returns:
        list: All items in the review queue
    """
    return REVIEW_QUEUE


def approve_draft(ticket_id: str) -> dict:
    """Approve a draft for sending to the customer.

    In a real system, this would send the email. Here, it marks approved.

    Args:
        ticket_id: The ticket whose draft to approve

    Returns:
        dict: Result of the approval
    """
    for item in REVIEW_QUEUE:
        if item["ticket_id"] == ticket_id:
            item["approved"] = True
            item["status"] = "approved"
            return {"status": "approved", "message": f"Draft for {ticket_id} approved"}

    return {"status": "error", "message": f"No draft found for {ticket_id}"}


def reject_draft(ticket_id: str) -> dict:
    """Reject a draft and remove it from the queue.

    Args:
        ticket_id: The ticket whose draft to reject

    Returns:
        dict: Result of the rejection
    """
    for i, item in enumerate(REVIEW_QUEUE):
        if item["ticket_id"] == ticket_id:
            REVIEW_QUEUE.pop(i)
            return {"status": "rejected", "message": f"Draft for {ticket_id} rejected"}

    return {"status": "error", "message": f"No draft found for {ticket_id}"}


def clear_queue() -> None:
    """Clear the review queue (for testing)."""
    global REVIEW_QUEUE
    REVIEW_QUEUE = []
