
"""Integration tests for AI-A01 semantic policy retrieval."""

import pytest

from knowledge.search import search_policies


@pytest.mark.parametrize(
    "question,expected_document_id",
    [
        (
            "What should we do when a supplier delivery is delayed?",
            1,
        ),
        (
            "How should critical customers be prioritized?",
            2,
        ),
        (
            "What recovery options are available for supply chain disruptions?",
            3,
        ),
    ],
)
def test_relevant_policy_ranked_first(question, expected_document_id):
    results = search_policies(question, limit=3)

    assert len(results) == 3
    assert results[0]["document_id"] == expected_document_id


def test_similarity_scores_are_ordered():
    results = search_policies(
        "Supplier delivery delay escalation",
        limit=3,
    )

    scores = [result["similarity"] for result in results]

    assert scores == sorted(scores, reverse=True)


def test_retrieval_limit():
    results = search_policies(
        "Customer priority and supplier delays",
        limit=2,
    )

    assert len(results) == 2


def test_empty_query_rejected():
    with pytest.raises(ValueError, match="empty"):
        search_policies("")


def test_invalid_limit_rejected():
    with pytest.raises(ValueError, match="Limit"):
        search_policies("Supplier delays", limit=0)
