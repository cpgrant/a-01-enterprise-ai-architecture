
"""Semantic search over AI-A01 enterprise policies."""

import os

import psycopg
from dotenv import load_dotenv

from knowledge.embed_documents import generate_embedding

load_dotenv("infra/.env")


def search_policies(query: str, limit: int = 3) -> list[dict]:
    """Retrieve policy documents ranked by cosine similarity."""

    if not query.strip():
        raise ValueError("Search query cannot be empty")

    if not 1 <= limit <= 10:
        raise ValueError("Limit must be between 1 and 10")

    embedding = generate_embedding(query)
    vector_literal = "[" + ",".join(map(str, embedding)) + "]"

    with psycopg.connect(
        host="127.0.0.1",
        port=5433,
        dbname="ai_a01",
        user="ai_a01",
        password=os.environ["POSTGRES_PASSWORD"],
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    document_id,
                    title,
                    content,
                    1 - (embedding <=> %s::vector) AS similarity
                FROM knowledge_documents
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (vector_literal, vector_literal, limit),
            )

            rows = cur.fetchall()

    return [
        {
            "document_id": row[0],
            "title": row[1],
            "content": row[2],
            "similarity": float(row[3]),
        }
        for row in rows
    ]


if __name__ == "__main__":
    questions = [
        "What should we do when a supplier delivery is delayed?",
        "How should critical customers be prioritized?",
        "What recovery options are available for supply chain disruptions?",
    ]

    for question in questions:
        print(f"\nQUESTION: {question}")

        for result in search_policies(question):
            print(
                f"  {result['similarity']:.4f}  "
                f"Document {result['document_id']}: "
                f"{result['title']}"
            )
