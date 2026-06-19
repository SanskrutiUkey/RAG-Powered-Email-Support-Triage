import os
import logging
from pathlib import Path
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
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
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    query = db.query(SupportTicket)

    if status == "processed":
        query = query.filter(
            SupportTicket.processing_status == "draft_generated"
        )

    elif status == "failed":
        query = query.filter(
            SupportTicket.processing_status == "failed"
        )

    if current_user.role == "admin":
        tickets = query.order_by(
            SupportTicket.created_at.desc()
        ).all()

    else:
        tickets = (query.filter(SupportTicket.assigned_to == current_user.id).
                   order_by(SupportTicket.created_at.desc()).all()
    )
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "tickets": tickets,
            "status": status
        }
    )

logger = logging.getLogger(__name__)

@router.get("/{ticket_id}")
def view_ticket(request: Request, ticket_id: int, db: Session = Depends(get_db)):

    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        logger.error(f"Ticket not found: {ticket_id}")
        raise HTTPException(status_code=404, detail="Ticket not found")

    return templates.TemplateResponse(
        "ticket_detail.html",
        {
            "request": request,
            "ticket": ticket
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

    if (current_user.role != "admin"  and ticket.assigned_to != current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )
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
    db: Session = Depends(get_db)
):

    ticket = (
        db.query(SupportTicket)
        .filter(SupportTicket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(404)

    process_support_email.delay( 
        {
            "ticket_id": ticket.id,
            "email_id": ticket.email_id
        }
    )
    ticket.processing_status = "pending"
    ticket.error_reason = None

    db.commit()

    return {"message": "Retry queued"}