# Evently architecture

## Mobile application

```text
frontend/
├── app/                 # Expo Router route entry points
│   ├── (auth)/
│   ├── (tabs)/
│   ├── admin/
│   ├── organizer/
│   ├── event/
│   ├── booking/
│   └── ticket/
├── components/          # Shared visual components
├── constants/           # Theme and seed data
├── context/             # Persisted application state
├── features/            # Feature-domain modules
├── hooks/               # Reusable hooks
├── lib/                 # Formatting and infrastructure helpers
├── providers/           # Top-level application providers
├── services/            # REST API boundary
└── types/               # Shared TypeScript types
```

## Backend API

```text
backend/
├── uploads/             # Organizer media uploads
└── src/
    ├── app.js           # Express assembly only
    ├── server.js        # Database connection and HTTP start only
    ├── config/          # Environment and database configuration
    ├── controllers/     # Request handlers by feature
    ├── models/          # One MongoDB model per file
    ├── routes/          # One Express route area per file
    ├── middleware/      # Authentication, errors, rate limiting
    ├── services/        # Assistant and external-service logic
    ├── utils/           # IDs and reusable errors
    ├── validators/      # Request validation
    ├── sockets/         # Socket.IO integration point
    └── jobs/            # Background maintenance jobs
```

The remaining integrations—Razorpay, Socket.IO, Expo push notifications, and PDF generation—belong in `services/`, `sockets/`, and `jobs/` and must be configured with their own credentials before production use.
