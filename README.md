# Evently — Event Booking App

See [ARCHITECTURE.md](ARCHITECTURE.md) for the complete mobile and backend module layout.

Production-minded Expo/React Native client and Express/MongoDB API for discovering, booking, and checking into events.

## Project layout

```
event-booking-app/
├── frontend/  # Expo React Native application
├── backend/   # Express + MongoDB REST API
└── README.md
```

## Run the mobile client

```bash
cd frontend
npm install
npx expo start
```

The client ships with local realistic seed data and a persisted demo session, so it works before the API is configured. Sign in with any valid-looking email; include `admin` in the address to expose the Admin Console in Profile.

## Run the API

```bash
cd backend
copy .env.example .env
npm install
npm run dev
```

Set `MONGODB_URI` and a secure `JWT_SECRET` in `backend/.env`. API routes cover auth, event CRUD, bookings/tickets, favorites, notifications, and protected admin stats/QR verification.

## Structure

- `app/` — Expo Router screens and routes
- `components/` — shared, reusable UI
- `context/` — auth, favorites, booking state and local demo persistence
- `constants/` — theme and seed events
- `backend/` — independent Express API with MongoDB models and JWT middleware

### Backend modules

The API is organized by responsibility: `src/routes/` contains named API route files, `src/controllers/` contains feature handlers, `src/models/` contains one model per file, `src/services/` contains reusable integrations, and `src/middleware/` contains authentication, errors, async handling, and rate limiting. `src/server.js` only connects MongoDB and starts the application.

### API map

`POST /api/auth/register`, `POST /api/auth/login`, `GET /api/events`, `POST /api/bookings`, `GET /api/bookings`, `GET /api/favorites`, `GET /api/notifications`, and `/api/admin/*` are available. Send `Authorization: Bearer <jwt>` to protected routes.
