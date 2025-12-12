# backend/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.db import create_db_and_tables, get_session
from backend.schemas import ChatRequest, ChatResponse, TicketCreate, TicketUpdate, TicketOut
from backend.groq_client import ask_groq
from backend.auth import admin_login, verify_token, oauth2_scheme
from backend.email_utils import send_email
from backend.sms_utils import send_sms
from backend.models import Ticket, Message
from sqlmodel import Session, select
from typing import List

app = FastAPI(title="John Customer Support Agent - Backend")

# CORS
origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # Optionally persist message to ticket if ticket_id provided
    try:
        reply = ask_groq(req.message, history=req.history, system_prompt=req.system_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # if ticket provided, save both messages
    if req.ticket_id:
        with Session(get_session().__self__.bind) as session:
            # insert message records
            m_user = Message(ticket_id=req.ticket_id, role="user", content=req.message)
            m_assist = Message(ticket_id=req.ticket_id, role="assistant", content=reply)
            session.add(m_user)
            session.add(m_assist)
            session.commit()
    return ChatResponse(reply=reply)

# Tickets
@app.post("/tickets", response_model=TicketOut)
def create_ticket(payload: TicketCreate):
    t = Ticket(title=payload.title, description=payload.description)
    with Session(get_session().__self__.bind) as session:
        session.add(t)
        session.commit()
        session.refresh(t)
        return TicketOut(
            id=t.id, title=t.title, description=t.description,
            status=t.status, created_at=str(t.created_at), updated_at=str(t.updated_at)
        )

@app.get("/tickets", response_model=List[TicketOut])
def list_tickets(limit: int = 50, session: Session = Depends(get_session)):
    with Session(get_session().__self__.bind) as s:
        q = s.exec(select(Ticket).order_by(Ticket.created_at.desc()).limit(limit))
        tickets = q.all()
        return [
            TicketOut(id=t.id, title=t.title, description=t.description,
                      status=t.status, created_at=str(t.created_at), updated_at=str(t.updated_at))
            for t in tickets
        ]

@app.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int):
    with Session(get_session().__self__.bind) as s:
        t = s.get(Ticket, ticket_id)
        if not t:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return TicketOut(id=t.id, title=t.title, description=t.description, status=t.status, created_at=str(t.created_at), updated_at=str(t.updated_at))

@app.patch("/tickets/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, payload: TicketUpdate):
    with Session(get_session().__self__.bind) as s:
        t = s.get(Ticket, ticket_id)
        if not t:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if payload.title is not None:
            t.title = payload.title
        if payload.description is not None:
            t.description = payload.description
        if payload.status is not None:
            t.status = payload.status
        import datetime
        t.updated_at = datetime.datetime.utcnow()
        s.add(t)
        s.commit()
        s.refresh(t)
        return TicketOut(id=t.id, title=t.title, description=t.description, status=t.status, created_at=str(t.created_at), updated_at=str(t.updated_at))

# Admin token endpoint
from fastapi.security import OAuth2PasswordRequestForm
@app.post("/admin/token")
def admin_token(form_data: OAuth2PasswordRequestForm = Depends()):
    return admin_login(form_data)

# Protected admin-only email & sms sending
@app.post("/admin/email")
def admin_send_email(to: str, subject: str, body: str, token: str = Depends(oauth2_scheme)):
    username = verify_token(token)  # validate
    try:
        send_email(to, subject, body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "sent"}

@app.post("/admin/sms")
def admin_send_sms(to: str, body: str, token: str = Depends(oauth2_scheme)):
    username = verify_token(token)
    try:
        sid = send_sms(to, body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"sid": sid}

