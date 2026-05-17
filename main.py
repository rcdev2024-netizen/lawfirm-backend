import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes import auth, appointments, cases, documents, messages, notifications, invoices, dashboard

load_dotenv()

app = FastAPI(
    title="Law Firm Portal API",
    description="""
## Law Firm Portal API

Powers the full Law Firm portal — client, attorney, and admin dashboards.

### Features
- **Authentication** – Register, login, JWT-based session management
- **Appointments** – Book, view, update appointments
- **Cases** – Full case lifecycle management
- **Documents** – Document storage and retrieval
- **Messages** – Internal messaging between clients and attorneys
- **Notifications** – Real-time notification feed
- **Invoices** – Billing and invoice management
- **Dashboard** – Aggregated stats per user role

### Authentication
Most endpoints require a Bearer JWT token. Obtain via `/api/auth/login`.
Include as: `Authorization: Bearer <token>`
    """,
    version="2.0.0",
    contact={
        "name": "Atty Rochelle Cortez-Naz Law Firm",
        "email": "attyrochellecortez.naz@gmail.com"
    },
    license_info={"name": "Private"}
)

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


@app.on_event("startup")
def on_startup():
    print("Law Firm Portal API v2 started.")
    print("Swagger UI: http://localhost:8000/docs")


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Law Firm Portal API is running",
        "version": "2.0.0",
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
        "version": "2.0.0",
        "supabase": db_status
    }
