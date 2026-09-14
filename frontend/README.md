# Frontend — AI API Security Agent

React dashboard for the FastAPI-backed AI API Security Agent.

## Stack

- Vite + React + TypeScript
- React Router
- Axios
- Tailwind CSS v4
- Lucide React
- Vitest + Testing Library

## Setup

```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```

Default API base URL:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Ensure the backend is running and `CORS_ORIGINS` includes `http://localhost:5173`.

## Scripts

- `npm run dev` — local development server
- `npm run build` — production build
- `npm test` — unit/component tests

## Notes

- JWT access tokens are stored in `localStorage` (demo/portfolio use)
- Gemini calls always go through the FastAPI backend
- Risk scores and findings are never recalculated in the browser
