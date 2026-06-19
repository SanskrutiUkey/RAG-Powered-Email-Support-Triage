from unittest.mock import Mock, patch

from app.services.rag_service import (
    retrieve_relevant_docs,
    retrieve_keyword_docs,
    hybrid_retrieval,
)


def test_retrieve_relevant_docs_returns_rows():
    fake_db = Mock()

    fake_db.execute.return_value.fetchall.return_value = [
        ("doc1",),
        ("doc2",),
    ]

    result = retrieve_relevant_docs(
        fake_db,
        [0.1, 0.2]
    )

    assert result == [
        ("doc1",),
        ("doc2",),
    ]


def test_retrieve_keyword_docs_returns_rows():
    fake_db = Mock()

    fake_db.execute.return_value.fetchall.return_value = [
        ("doc3",),
        ("doc4",),
    ]

    result = retrieve_keyword_docs(
        fake_db,
        "python"
    )

    assert result == [
        ("doc3",),
        ("doc4",),
    ]


@patch("app.services.rag_service.retrieve_relevant_docs")
@patch("app.services.rag_service.retrieve_keyword_docs")
@patch("app.services.rag_service.SessionLocal")
def test_hybrid_retrieval_deduplicates_docs(
    mock_session,
    mock_keyword,
    mock_vector,
):
    fake_db = Mock()

    mock_session.return_value = fake_db

    mock_vector.return_value = [
        ("A",),
        ("B",),
    ]

    mock_keyword.return_value = [
        ("B",),
        ("C",),
    ]

    result = hybrid_retrieval(
        embedding=[1, 2],
        query="python",
    )

    assert set(result) == {
        "A",
        "B",
        "C",
    }

    fake_db.close.assert_called_once()


@patch("app.services.rag_service.retrieve_relevant_docs")
@patch("app.services.rag_service.SessionLocal")
def test_hybrid_retrieval_closes_db_on_exception(
    mock_session,
    mock_vector,
):
    import pytest

    fake_db = Mock()

    mock_session.return_value = fake_db
    mock_vector.side_effect = Exception("boom")

    with pytest.raises(Exception):
        hybrid_retrieval(
            embedding=[1, 2],
            query="python",
        )

    fake_db.close.assert_called_once()