import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from routes import auth, appointments, cases, documents, messages, notifications, invoices, dashboard, roles, audit_logs, reports
from routes.clients import router as clients_router
from routes.attorneys import router as attorneys_router

load_dotenv()

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI(
    title="Law Firm Portal API",
    description="""
## Law Firm Portal API

Powers the full Law Firm portal â€” client, attorney, and admin dashboards.

### Features
- **Authentication** â€“ Register, login, JWT-based session management
- **Appointments** â€“ Book, view, update appointments (online/onsite)
- **Cases** â€“ Full case lifecycle management
- **Clients** â€“ Client management with approval workflow
- **Attorneys** â€“ Attorney management
- **Documents** â€“ Document storage and retrieval
- **Messages** â€“ Internal messaging between clients and attorneys
- **Notifications** â€“ Real-time notification feed
- **Invoices** â€“ Billing and invoice management
- **Dashboard** â€“ Aggregated stats, today's schedule, case overview
- **Audit Logs** â€“ User activity tracking

### Authentication
Most endpoints require a Bearer JWT token. Obtain via `/api/auth/login`.
Include as: `Authorization: Bearer <token>`
    """,
    version="2.2.0",
    contact={
        "name": "Atty Rochelle Cortez-Naz Law Firm",
        "email": "attyrochellecortez.naz@gmail.com"
    },
    license_info={"name": "Private"}
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(appointments.router)
app.include_router(cases.router)
app.include_router(documents.router)
app.include_router(messages.router)
app.include_router(notifications.router)
app.include_router(invoices.router)
app.include_router(dashboard.router)
app.include_router(roles.router)
app.include_router(clients_router)
app.include_router(attorneys_router)
app.include_router(audit_logs.router)
app.include_router(reports.router)


@app.on_event("startup")
def on_startup():
    print("Law Firm Portal API v2.2 started.")
    print("Swagger UI: http://localhost:8000/docs")


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Law Firm Portal API is running",
        "version": "2.2.0",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
def health():
    from database import get_supabase
    try:
        get_supabase().table("users").select("id").limit(1).execute()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "version": "2.2.0",
        "supabase": db_status
    }

