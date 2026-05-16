import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes import auth, appointments

load_dotenv()

app = FastAPI(
    title="Atty Rochelle Law Office API",
    description="""
## Law Office Appointment & Auth API

This API powers the Atty Rochelle Cortez-Naz Law Office web application.

### Features
- **Authentication** – Register, login, and manage user sessions with JWT tokens.
- **Appointments** – Book, view, update, and cancel appointment requests.

### Authentication
Most endpoints require a Bearer JWT token. Obtain a token via `/api/auth/login`.
Include it in requests as: `Authorization: Bearer <token>`
    """,
    version="1.0.0",
    contact={
        "name": "Atty Rochelle Cortez-Naz Law Office",
        "email": "attyrochellecortez.naz@gmail.com"
    },
    license_info={"name": "Private"}
)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(appointments.router)


@app.on_event("startup")
def on_startup():
    print("✅  Atty Rochelle Law Office API started.")
    print("📄  Swagger UI: http://localhost:8000/docs")


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Atty Rochelle Law Office API is running",
        "docs": "/docs",
        "redoc": "/redoc"
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
        "version": "1.0.0",
        "supabase": db_status
    }
