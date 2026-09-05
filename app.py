"""app.py — a minimal watchable UI for the demo. Run: streamlit run app.py

Module 4 (Integration & Demo): All three concepts in one flow.
Shows the ticket, the connected context from the knowledge graph, the loop's
attempts, and the final queued draft. Requires ANTHROPIC_API_KEY set.

Set LANGSMITH_TRACING=true and LANGSMITH_API_KEY=... for the trace (no code change).
"""
import os
import streamlit as st
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

from tools import TICKETS, REVIEW_QUEUE, read_ticket, draft_reply
from graph_memory import query_graph
from verify import verify_draft

# Load environment variables from .env file
load_dotenv()

# Page config
st.set_page_config(
    page_title="Support Triage Agent",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Support Triage Agent")
st.markdown(
    """
Harness + Loop + Graph Demo

This agent shows all three concepts in action:
1. **Harness** — reads a ticket, accesses tools
2. **Graph** — finds connected tickets sharing the same root cause
3. **Loop** — drafts a reply, verifies it, retries if needed
"""
)

# Sidebar: ticket selection
st.sidebar.header("Select a Ticket")
ticket_id = st.sidebar.selectbox("Ticket", list(TICKETS.keys()))

# Initialize session state to avoid re-running on every interaction
if "triage_result" not in st.session_state:
    st.session_state.triage_result = None


# Main demo flow
if st.button("Triage This Ticket", type="primary", use_container_width=True):
    st.session_state.triage_result = None  # Clear previous result

    # Get ticket info
    t = TICKETS[ticket_id]
    product = t["product"]

    # Step 1: Harness reads the ticket
    with st.status("Step 1: Harness reads the ticket", expanded=True):
        ticket_text = read_ticket.invoke({"ticket_id": ticket_id})
        st.write(ticket_text)

    # Step 2: Knowledge graph — find connected context
    with st.status("Step 2: Knowledge graph — find related tickets", expanded=True):
        context = query_graph(ticket_id)
        st.info(context)

    # Step 3: Loop — draft, verify, revise
    with st.status("Step 3: Loop — draft → verify → revise", expanded=True):
        model = ChatAnthropic(
            model="claude-opus-4-1",
            temperature=0,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

        attempts = 0
        draft = ""
        status = ""
        reason = None

        while attempts < 4:
            attempts += 1

            # Build the prompt
            prompt = (
                f"You are a support agent triaging a ticket.\n\n"
                f"Ticket ID: {ticket_id}\n"
                f"Customer: {t['customer']}\n"
                f"Product: {product}\n"
                f"Issue: {t['text']}\n\n"
                f"Context (related tickets): {context}\n\n"
                f"Draft a helpful, professional support reply that:\n"
                f"- Acknowledges the customer's issue\n"
                f"- Mentions the product by name\n"
                f"- Explains what's happening (or what we're doing)\n"
                f"- Is between 50-150 words\n"
                f"- Makes no over-promises\n\n"
            )

            if attempts > 1:
                prompt += f"Your previous draft failed because: {reason}. Please fix it and try again.\n\n"

            prompt += "Reply:"

            # Call the model
            draft = model.invoke(prompt).content.strip()

            # Verify the draft
            passed, reason = verify_draft(draft, product)

            if passed:
                status = "queued"
                st.write(f"✅ Attempt {attempts}: **PASS** ({reason})")
                st.write(f"Draft:\n> {draft}")
                break
            else:
                st.write(f"❌ Attempt {attempts}: **FAIL** — {reason}")
                st.write(f"> {draft[:100]}...")

        if attempts >= 4 and status != "queued":
            status = "escalated"
            st.write(
                f"⚠️ **Escalated after {attempts} attempts** — "
                f"couldn't generate a passing draft. Needs human review."
            )

    # Step 4: Permission gate
    with st.status("Step 4: Permission gate — queue for human review", expanded=True):
        if status == "queued":
            # Queue the draft (never sends)
            draft_reply.invoke({"ticket_id": ticket_id, "text": draft})
            st.success(
                f"✅ Draft queued for human review (NOT automatically sent)\n\n"
                f"**Ticket:** {ticket_id}\n\n"
                f"**Draft:**\n\n{draft}"
            )
            st.session_state.triage_result = {
                "status": "queued",
                "ticket_id": ticket_id,
                "draft": draft,
                "attempts": attempts,
            }
        else:
            st.warning(
                f"⚠️ Escalated to human support\n\n"
                f"After {attempts} attempts, the agent could not produce a "
                f"satisfactory draft. A human support lead should review this ticket."
            )
            st.session_state.triage_result = {
                "status": "escalated",
                "ticket_id": ticket_id,
                "attempts": attempts,
            }

    st.divider()

# Show review queue (human approval layer)
st.sidebar.header("📋 Review Queue")
if REVIEW_QUEUE:
    for item in REVIEW_QUEUE:
        st.sidebar.write(f"**{item['ticket_id']}**")
        st.sidebar.caption(f"Waiting for approval...")
else:
    st.sidebar.caption("Queue is empty")

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🤖 **Harness** — reads tickets via tools")
with col2:
    st.caption("🔗 **Graph** — finds related issues")
with col3:
    st.caption("♻️ **Loop** — verify & revise until pass or escalate")

st.caption("All drafts are queued for human review. **Nothing is auto-sent to customers.**")
