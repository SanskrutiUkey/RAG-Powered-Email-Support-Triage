from unittest.mock import Mock, patch

from app.services.reranking_service import rerank_docs


@patch("app.services.rag_service.model")
def test_rerank_docs_builds_query_doc_pairs(mock_model):
    docs = ["doc1", "doc2"]

    rerank_docs(
        query="python",
        docs=docs,
    )

    mock_model.predict.assert_called_once_with([
        ["python", "doc1"],
        ["python", "doc2"],
    ])


@patch("app.services.rag_service.model")
def test_rerank_docs_sorts_by_score(mock_model):
    docs = ["A", "B", "C"]

    mock_model.predict.return_value = [
        0.4,
        0.9,
        0.2,
    ]
    result = rerank_docs(
        query="python",
        docs=docs,
    )
    assert result == [
        "B",
        "A",
        "C",
    ]


@patch("app.services.rag_service.model")
def test_rerank_docs_returns_top_k(mock_model):
    docs = ["A", "B", "C"]

    mock_model.predict.return_value = [
        0.4,
        0.9,
        0.2,
    ]
    result = rerank_docs(
        query="python",
        docs=docs,
        top_k=2,
    )
    assert result == [
        "B",
        "A",
    ]

@patch("app.services.rag_service.model")
def test_rerank_docs_returns_only_docs(mock_model):
    docs = ["A"]

    mock_model.predict.return_value = [0.99]

    result = rerank_docs(
        query="python",
        docs=docs,
    )

    assert result == ["A"]