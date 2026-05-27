import os
import logging
from pathlib import Path
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import SupportTicket
from fastapi.templating import Jinja2Templates
from fastapi import Form
from app.services.email_service import send_support_reply

templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix="/admin", tags=["admin"])
@router.get("/dashboard")
def admin_dashboard(
    request: Request,
    status: str = "all",
    db: Session = Depends(get_db)
):
    
    query = db.query(SupportTicket)

    if status == "processed":
        query = query.filter(
            SupportTicket.processing_status == "draft_generated"
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
    db: Session = Depends(get_db)
):

    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if action == "send":
        if not response:
            raise HTTPException(status_code=400, detail="Response required")
        
        send_support_reply(
            ticket.sender,
            ticket.subject,
            response
        )

        ticket.processing_status = "sent"
        ticket.final_response = response

    elif action == "reject":
        ticket.processing_status = "rejected"

    db.commit()

    return RedirectResponse(url="/dashboard", status_code=303)