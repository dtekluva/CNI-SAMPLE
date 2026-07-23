# CNI Group Governance Portal

Multi-entity board governance portal. See [`../PRD_Group_Governance_Portal.md`](../PRD_Group_Governance_Portal.md), [`../DECISIONS.md`](../DECISIONS.md), and the Northstar design system in [`../design-system/`](../design-system/).

## Stack (DECISIONS D-A1)
- **Backend:** Django 5 + Django REST Framework (Python) — `backend/`
- **DB:** PostgreSQL 16 (SQLite fallback for fast unit tests)
- **Frontend:** React + Vite + TypeScript — `frontend/`, using the Northstar tokens/components
- **Tests (the build-loop's definition-of-done):** pytest (backend), Vitest + Testing Library (frontend), Playwright (e2e, to be added)
- **Dev services:** Postgres + Redis via `docker-compose.yml`

## Quick start
```bash
# 1. dev services (needs Docker)
make up

# 2. backend
cp .env.example backend/.env
make backend-install
make migrate
make backend-test        # green = API stack wired
make backend-run         # http://127.0.0.1:8000/api/health/

# 3. frontend (new shell)
make frontend-install
make frontend-test       # green
npm --prefix frontend run dev   # http://127.0.0.1:5173 (proxies /api → :8000)
```

## Layout
```
backend/     Django project (config/) + apps/ (core/ = health + baseline)
frontend/    Vite React app; src/styles/ mirrors the design-system CSS
docker-compose.yml   postgres + redis
```

## Status
Phase 0 scaffold: health endpoint + first green tests on both ends, security-first Django baseline (MFA middleware, least-privilege DRF default, env-driven secrets). Next: data model (entities/hierarchy), auth/RBAC, then the Phase-1 backlog.
