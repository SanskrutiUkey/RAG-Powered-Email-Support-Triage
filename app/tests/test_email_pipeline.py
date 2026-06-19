from unittest.mock import MagicMock, patch

from app.core.tasks import process_support_email
from app.db.models import SupportTicket
from app.db.session import SessionLocal

# Ticket → Embedding → Retrieval → AI Draft → Status Update
@patch("app.core.tasks.retrieve_relevant_docs")
@patch("app.core.tasks.client")
def test_email_processing_pipeline(
    mock_client,
    mock_retrieve_docs,
):
    # Embedding response
    embedding = MagicMock()
    embedding.embedding = [0.1] * 768

    mock_client.embeddings.create.return_value.data = [
        embedding
    ]

    # Retrieval response
    mock_retrieve_docs.return_value = [
        "Refund policy document"
    ]

    # LLM response
    choice = MagicMock()
    choice.message.content = "Mock AI reply"

    mock_client.chat.completions.create.return_value.choices = [
        choice
    ]

    db = SessionLocal()

    ticket = SupportTicket(
        email_id="test-123",
        sender="user@test.com",
        subject="Refund",
        text_body="I need a refund",
        raw_payload={},
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    process_support_email.run(
        {"ticket_id": ticket.id}
    )

    db.expire_all()

    updated_ticket = (
        db.query(SupportTicket)
        .filter(SupportTicket.id == ticket.id)
        .one()
    )

    # Pipeline assertions
    mock_client.embeddings.create.assert_called_once()
    mock_retrieve_docs.assert_called_once()
    mock_client.chat.completions.create.assert_called_once()

    # DB assertions
    assert (updated_ticket.processing_status == "draft_generated")

    assert (updated_ticket.ai_draft == "Mock AI reply")