"""graph_memory.py — knowledge-graph memory. Stores RELATIONSHIPS, enabling multi-hop.

Module 3 (Knowledge Graphs): Flat vector RAG finds tickets with similar TEXT.
It cannot tell you that two differently-worded tickets share the same root cause.
A graph can, because the relationship is stored explicitly.

This example uses NetworkX (simple, pure Python). In production you'd use Neo4j
or another graph database, but the conceptual logic is identical.
"""
import networkx as nx

# The graph: nodes are entities (tickets, customers, products, known issues)
# Edges are relationships (FROM, ABOUT, CAUSED_BY)
G = nx.DiGraph()


def seed_graph():
    """Build the demo graph: tickets -> customers, products, known-issues.

    The key insight: three tickets describe the same issue differently.
    A graph links all three to the same known-issue node (KI-7).
    One hop from any ticket reveals the others.
    """
    edges = [
        # T-101: customer, product, root cause
        ("T-101", "Acme Corp", "FROM"),
        ("T-101", "Billing API", "ABOUT"),
        ("T-101", "KI-7", "CAUSED_BY"),
        # T-102: same root cause, different words
        ("T-102", "Beta LLC", "FROM"),
        ("T-102", "Billing API", "ABOUT"),
        ("T-102", "KI-7", "CAUSED_BY"),
        # T-103: different product but also has KI-7 as a secondary issue
        # (simulating a cascading effect)
        ("T-103", "Gamma Inc", "FROM"),
        ("T-103", "Reporting", "ABOUT"),
        ("T-103", "KI-7", "CAUSED_BY"),
    ]
    for src, dst, rel in edges:
        G.add_edge(src, dst, rel=rel)


def query_graph(ticket_id: str) -> str:
    """Multi-hop: find this ticket's known issue(s), then EVERY other ticket with the
    same root cause. This is the reasoning flat retrieval cannot do.

    A single query reveals:
    - What is the root cause of this ticket?
    - What other tickets share the same root cause?
    This is multi-hop reasoning: ticket → issue → [other tickets].
    """
    if ticket_id not in G:
        return f"{ticket_id} not in knowledge graph."

    # One hop: find known issues caused by this ticket
    issues = [n for n in G.successors(ticket_id) if n.startswith("KI-")]
    if not issues:
        return f"{ticket_id} has no linked known issue."

    lines = []
    for ki in issues:
        # Another hop: find all other tickets caused by this issue
        others = [n for n in G.predecessors(ki) if n.startswith("T-") and n != ticket_id]
        if others:
            lines.append(
                f"{ticket_id} is caused by known issue {ki}, "
                f"which also affects tickets: {', '.join(others)}."
            )
        else:
            lines.append(f"{ticket_id} is caused by known issue {ki} (isolated).")
    return " ".join(lines)


# Initialize the graph when this module loads
seed_graph()


if __name__ == "__main__":
    # Demonstrate multi-hop on T-101: it finds the two other tickets (T-102, T-103)
    # that share the same root cause.
    print("Multi-hop query from T-101:")
    print(query_graph("T-101"))
    print()

    print("Multi-hop query from T-102:")
    print(query_graph("T-102"))
    print()

    print("Multi-hop query from T-103:")
    print(query_graph("T-103"))
