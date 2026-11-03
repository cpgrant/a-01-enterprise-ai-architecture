
"""Generate and store embeddings for enterprise policy documents."""

import os

import httpx
import psycopg
from dotenv import load_dotenv

load_dotenv("infra/.env")

MODEL = "embeddinggemma-2:270m"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5433,
    "dbname": "ai_a01",
    "user": "ai_a01",
    "password": os.environ["POSTGRES_PASSWORD"],
}


def generate_embedding(text: str) -> list[float]:
    """Generate a 768-dimensional embedding using local Ollama."""

    response = httpx.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": MODEL, "input": text},
        timeout=120,
    )
    response.raise_for_status()

    embedding = response.json()["embeddings"][0]

    if len(embedding) != 768:
        raise ValueError(
            f"Expected 768 dimensions, received {len(embedding)}"
        )

    return embedding


def main():
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT document_id, title, content "
                "FROM knowledge_documents ORDER BY document_id"
            )
            documents = cur.fetchall()

            for document_id, title, content in documents:
                text = f"{title}\n{content}"
                embedding = generate_embedding(text)

                # pgvector accepts its text vector representation.
                vector_literal = "[" + ",".join(map(str, embedding)) + "]"

                cur.execute(
                    """
                    UPDATE knowledge_documents
                    SET embedding = %s::vector
                    WHERE document_id = %s
                    """,
                    (vector_literal, document_id),
                )

                print(
                    f"Embedded document {document_id}: "
                    f"{title} ({len(embedding)} dimensions)"
                )

        conn.commit()

    print("PASS: Enterprise policy embeddings stored")


if __name__ == "__main__":
    main()
