"""agent.py — assembles the harness: model + tools + memory.

Module 1 (Harness Engineering): This is the core "Agent = Model + Harness" assembly.

The four layers:
  1. MODEL — the brain (Claude)
  2. TOOLS — the hands (read_ticket, draft_reply, query_graph)
  3. MEMORY — the notebook (SqliteSaver for persistence across runs)
  4. PERMISSIONS — the gate (draft_reply can only propose, not send)
"""
import os
import sys
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver

# Load environment variables from .env file
load_dotenv()

# Import tools from Module 1
from tools import read_ticket, draft_reply

# Import the knowledge graph tool from Module 3
from graph_memory import query_graph

# Make query_graph a callable tool for the agent
from langchain_core.tools import tool


@tool
def find_connected_tickets(ticket_id: str) -> str:
    """Find other tickets connected to this one via the knowledge graph.

    Calls query_graph to do multi-hop reasoning: find the known issue(s),
    then find all other tickets with the same root cause.
    """
    return query_graph(ticket_id)


def build_agent():
    """Build the complete harness.

    Returns:
        An agent (LangGraph StateGraph) that can be invoked with a message.
    """

    # Layer 1: The MODEL — the brain we rent
    # Using Claude Opus for power on this demo
    model = ChatAnthropic(
        model="claude-opus-4-1",  # Use current Claude model
        temperature=0,  # Deterministic outputs (no creativity in support replies)
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    # Layer 2: The TOOLS — the agent's hands
    tools = [
        read_ticket,  # Read a support ticket
        find_connected_tickets,  # Query the knowledge graph
        draft_reply,  # Draft a reply (goes to review queue, never sent)
    ]

    # Layer 3: The MEMORY — persistence (survive a restart)
    # SqliteSaver stores state in a file so the agent's memory persists.
    # For a first run, you can use InMemorySaver (zero setup, lost on restart).
    checkpoint_db = os.getenv("CHECKPOINT_DB", "triage_memory.sqlite")
    saver = SqliteSaver.from_conn_string(f"sqlite:///{checkpoint_db}")

    # Layer 4: The PERMISSIONS — the boundary (in the system prompt)
    SYSTEM_PROMPT = (
        "You are a support-ticket triage agent. Your job:\n"
        "1. Read the ticket using read_ticket.\n"
        "2. Find connected tickets using find_connected_tickets.\n"
        "3. Draft a helpful reply that acknowledges the customer and explains the situation.\n"
        "4. Use draft_reply to queue the reply for human review.\n\n"
        "CRITICAL: You can ONLY propose drafts via draft_reply — you cannot send anything.\n"
        "A human reviews and approves every draft before it reaches the customer.\n"
        "Never make over-promises or guarantees. Mention the product by name."
    )

    # Create the agent using LangGraph's create_react_agent
    # (ReAct = Reasoning + Acting, the foundation of agentic loops)
    agent = create_react_agent(
        model=model,
        tools=tools,
        state_modifier=SYSTEM_PROMPT,  # Sets the boundary in the system prompt
        checkpointer=saver,  # Persistence layer
    )

    return agent


if __name__ == "__main__":
    # Test: build the agent and run a simple triage
    print("Building agent...")
    agent = build_agent()

    # Run the agent on a ticket
    ticket_id = "T-101"
    print(f"\nTriaging ticket {ticket_id}...")

    # Invoke the agent with a persistent thread ID (so state survives across invocations)
    config = {"configurable": {"thread_id": ticket_id}}

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Please triage ticket {ticket_id} and draft a reply.",
                }
            ]
        },
        config,
    )

    # The agent's final message
    print("\nAgent completed. Final message:")
    print(result["messages"][-1].content)

    # Show what landed in the review queue
    from tools import REVIEW_QUEUE

    print("\n--- REVIEW QUEUE (drafts waiting for human approval) ---")
    for item in REVIEW_QUEUE:
        print(f"Ticket: {item['ticket_id']}")
        print(f"Draft: {item['draft']}")
        print()
