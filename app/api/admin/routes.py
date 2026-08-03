import os
import json
import asyncio
import logging
from pathlib import Path
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db, SessionLocal
from app.db.models import SupportTicket, User
from fastapi.templating import Jinja2Templates
from fastapi import Form
from app.services.email_service import send_support_reply
from app.core.tasks import send_support_reply_task, process_support_email
from app.auth.dependencies import require_admin

templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
@router.get("/")
def admin_dashboard(
    request: Request,
    status: str = "all",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    query = db.query(SupportTicket)

    if status == "pending":
        query = query.filter(
            SupportTicket.processing_status == "pending"
        )

    elif status == "failed":
        query = query.filter(
            SupportTicket.processing_status == "failed"
        )

    tickets = query.order_by(
        SupportTicket.created_at.desc()
    ).all()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "tickets": tickets,
            "status": status,
            "current_user": current_user
        }
    )

logger = logging.getLogger(__name__)

@router.get("/{ticket_id}")
def view_ticket(request: Request, ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        logger.error(f"Ticket not found: {ticket_id}")
        raise HTTPException(status_code=404, detail="Ticket not found")

    return templates.TemplateResponse(
        "ticket_detail.html",
        {
            "request": request,
            "ticket": ticket,
            "current_user": current_user
        }
    )

@router.post("/{ticket_id}/action")
def ticket_action(
    ticket_id: int,
    action: str = Form(...),
    response: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):

    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if action == "send":
        if not response:
            raise HTTPException(status_code=400, detail="Response required")
        
        # Queue the sending to the high_priority queue
        send_support_reply_task.apply_async(
            args=[ticket.sender, ticket.subject, response],
            queue="high_priority"
        )

        ticket.processing_status = "sent"
        ticket.final_response = response

    elif action == "reject":
        ticket.processing_status = "rejected"

    db.commit()

    return RedirectResponse(url="/dashboard", status_code=303)

@router.post("/{ticket_id}/retry")
def retry_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    ticket = (
        db.query(SupportTicket)
        .filter(SupportTicket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(404)

    try:
        process_support_email.apply_async(
            args=[{
                "ticket_id": ticket.id,
                "email_id": ticket.email_id,
                "error_reason": ticket.error_reason
            }],
            queue="ai_processing"
        )
        ticket.processing_status = "pending"
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Retry dispatch failed: {e}")
        raise HTTPException(status_code=503, detail="Task queue unavailable")

    return RedirectResponse(url=f"/dashboard/{ticket_id}", status_code=303)

@router.get("/{ticket_id}/stream")
async def ticket_stream(
    ticket_id: int,
    current_user: User = Depends(require_admin)
):
    async def event_generator():
        db = SessionLocal()
        try:
            ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
            if not ticket:
                return

            while True:
                data = {
                    "processing_status": ticket.processing_status,
                    "ai_draft": ticket.ai_draft or "",
                    "error_reason": ticket.error_reason or "",
                }
                yield f"event: status_update\ndata: {json.dumps(data)}\n\n"

                if ticket.processing_status in ("draft_generated", "failed", "sent", "rejected"):
                    yield f"event: done\ndata: {json.dumps({'status': ticket.processing_status})}\n\n"
                    break

                await asyncio.sleep(15)
                db.refresh(ticket)
        finally:
            db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )