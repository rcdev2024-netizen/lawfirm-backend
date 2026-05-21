import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from limiter import limiter
from routes import auth, appointments, cases, documents, messages, notifications, invoices, dashboard, roles, audit_logs, reports
from routes.clients import router as clients_router
from routes.attorneys import router as attorneys_router

load_dotenv()

ALLOWED_ORIGINS = [
    "https://lawfirm-frontend-nu.vercel.app",
    "https://lawfirm-frontend-git-main-rcdev2024-netizens-projects.vercel.app",
    "http://localhost:4200",
    "http://localhost:3000",
]

app = FastAPI(
    title="Law Firm Portal API",
    description="Law Firm Portal API — client, attorney, and admin dashboards.",
    version="2.2.0",
    contact={"name": "Atty Rochelle Cortez-Naz Law Firm", "email": "attyrochellecortez.naz@gmail.com"},
    license_info={"name": "Private"}
)

# CORS must be first — so OPTIONS preflight always gets correct headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter registered after CORS
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    origin = request.headers.get("origin", "")
    headers = {"Retry-After": "60"}
    if origin in ALLOWED_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "false"
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please slow down."},
        headers=headers,
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


@app.get("/", tags=["Health"])
def root():
    return {"message": "Law Firm Portal API is running", "version": "2.2.0", "docs": "/docs"}


@app.get("/health", tags=["Health"])
def health():
    from database import get_supabase
    try:
        get_supabase().table("users").select("id").limit(1).execute()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return {"status": "healthy" if db_status == "connected" else "degraded", "version": "2.2.0", "supabase": db_status}
