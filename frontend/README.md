# Atty Rochelle Cortez-Naz Law Office — Full Stack Project

## Project Structure
```
/
├── src/                    # Angular Frontend (v17)
│   ├── app/
│   │   ├── components/
│   │   │   ├── navbar/     # Navbar with Login button
│   │   │   ├── hero/
│   │   │   ├── about/
│   │   │   ├── practice-areas/
│   │   │   ├── faqs/
│   │   │   ├── blog/
│   │   │   ├── contact/    # Appointment booking (connected to API)
│   │   │   ├── footer/
│   │   │   └── login/      # Login & Register page
│   │   ├── services/
│   │   │   ├── auth.service.ts
│   │   │   └── appointment.service.ts
│   │   └── environments/
│   │       ├── environment.ts       # Dev: localhost:8000
│   │       └── environment.prod.ts  # Prod: update with your API URL
└── backend/                # FastAPI Python Backend
    ├── main.py
    ├── database.py
    ├── models.py
    ├── schemas.py
    ├── auth.py
    ├── routes/
    │   ├── auth.py
    │   └── appointments.py
    ├── requirements.txt
    └── .env
```

---

## Running Locally

### Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate       # Mac/Linux
# OR: venv\Scripts\activate    # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend (Angular)
```bash
npm install
npm start
```
- App: http://localhost:4200

---

## API Endpoints

| Method | Endpoint | Auth |
|--------|----------|------|
| POST | /api/auth/register | No |
| POST | /api/auth/login | No |
| GET | /api/auth/me | Yes |
| POST | /api/appointments | Optional |
| GET | /api/appointments | Yes |
| GET | /api/appointments/my | Yes |
| PATCH | /api/appointments/{id}/status | Yes |
| DELETE | /api/appointments/{id} | Yes |
