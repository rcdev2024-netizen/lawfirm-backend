# Atty Rochelle Law Office — FastAPI Backend

## Setup & Run Locally

### Step 1 — Run the database migration (ONE TIME ONLY)
1. Go to your Supabase dashboard → **SQL Editor**
2. Click **New Query**
3. Paste the contents of `migration.sql`
4. Click **Run**

That creates the `users` and `appointments` tables.

---

### Step 2 — Create and activate virtual environment

```powershell
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Mac / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Start the server
```bash
uvicorn main:app --reload --port 8000
```

### Step 5 — Open Swagger docs
- http://localhost:8000/docs
- http://localhost:8000/redoc

---

## .env (already filled in)
```
SUPABASE_URL=https://iouwkzcflpulmavindyb.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
SECRET_KEY=your-jwt-secret
CORS_ORIGINS=http://localhost:4200
```

> No database connection string needed — the backend connects via HTTPS using the Supabase client.

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/auth/register | No | Register |
| POST | /api/auth/login | No | Login → JWT |
| GET | /api/auth/me | Yes | Current user |
| POST | /api/appointments | Optional | Book appointment |
| GET | /api/appointments | Yes | All appointments |
| GET | /api/appointments/my | Yes | My appointments |
| PATCH | /api/appointments/{id}/status | Yes | Update status |
| DELETE | /api/appointments/{id} | Yes | Delete |
