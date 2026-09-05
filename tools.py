"""tools.py — the harness's tools (its 'hands').

Module 1 (Harness Engineering - Layer 1: Tools):

The concrete layer that gives the agent the ability to do things.
Tools are the agent's HANDS — read tickets, search, find patterns, propose replies.

Note: The permission gate (Layer 3) is in permissions.py
"""
from langchain_core.tools import tool
from permissions import queue_draft_for_review

# In a real system these hit your DB / ticketing API. Hardcoded here for the demo.
TICKETS = {
    "T-101": {
        "customer": "Acme Corp",
        "product": "Billing API",
        "text": "Getting 500 errors on the invoice endpoint since yesterday.",
    },
    "T-102": {
        "customer": "Beta LLC",
        "product": "Billing API",
        "text": "Invoice API intermittently returns 500.",
    },
    "T-103": {
        "customer": "Gamma Inc",
        "product": "Reporting",
        "text": "Export to CSV button does nothing. Nothing shows up in logs either.",
    },
}


@tool
def read_ticket(ticket_id: str) -> str:
    """Read a support ticket by its ID. Returns customer, product, and the message.

    This is the agent's first step: gather the raw facts about the ticket.
    """
    t = TICKETS.get(ticket_id)
    if not t:
        return f"No ticket found with id {ticket_id}."
    return (
        f"Ticket {ticket_id} from {t['customer']} "
        f"about {t['product']}: {t['text']}"
    )


@tool
def draft_reply(ticket_id: str, text: str) -> str:
    """Draft a reply to a ticket. The draft is placed in a human REVIEW QUEUE, not sent.

    Use this once you have a good reply ready for a human to approve.
    This is the permission gate made concrete: the agent can propose, but only a
    human can actually send anything to the customer.

    The actual permission gate logic is in permissions.py (Layer 3).
    """
    result = queue_draft_for_review(ticket_id, text)
    return f"Draft queued for human review on {ticket_id}. It was NOT sent."
