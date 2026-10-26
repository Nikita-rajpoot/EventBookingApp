# TaeVerse FastAPI backend

This is the FastAPI migration of the Express API. It retains the `/api` route contract, so the Expo frontend can keep the same base URL.

```powershell
cd backend/fastapi
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload --port 4000
```

Configure `MONGODB_URI`, `JWT_SECRET`, and optionally `TICKETMASTER_API_KEY` in `.env`. Swagger is available at `http://localhost:4000/docs`.

The Express service remains in `backend/src` until the FastAPI service has been verified with your database.
