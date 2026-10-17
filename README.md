# Invoice Extractor — Professional README

A production-minded service to turn Indian GST bills (photos or PDFs) into validated, reviewable, structured data for export (CSV). Designed for human-in-the-loop verification: the AI/LLM and OCR do the reading, deterministic validators enforce correctness and flag suspicious fields for a user to review.

Key uses
- Accounts payable teams who need accurate structured invoice data from camera photos and PDFs.
- Data-entry and reconciliation workflows that require arithmetic and GST validation guarantees before accepting extracted values.

Highlights
- Preprocessing for photos (crop, deskew, shadow removal) + Tesseract OCR (English + Tamil) and PDF text-layer handling.
- LLM-based extraction into a fixed JSON schema, followed by deterministic validators (GSTIN checksum, tax arithmetic, date sanity).
- Review UI with original bill side-by-side and flagged fields for human verification.
- FastAPI backend, React (Vite) frontend, PostgreSQL persistence; designed to run locally, in containers, or on Render + Vercel.

Table of contents
- What this is
- Stack
- Architecture / how it works
- Repo layout (annotated)
- Quick start — run locally
- Docker / containers
- Deployment (Render + Vercel + Neon)
- Tests & evaluation
- Operational notes & troubleshooting
- Contributing & contact

What this is
One-sentence: a full-stack pipeline that extracts, validates, and lets a person verify invoice fields read from photos or PDFs so downstream exports are reliable and auditable.

Stack
- Language(s): Python (backend), JavaScript / React (frontend)
- Frameworks / runtime:
  - Backend: FastAPI + Uvicorn
  - Frontend: React (Vite)
  - Database: PostgreSQL (Neon recommended)
- Notable libraries:
  - Backend: SQLAlchemy 2, Alembic, Pydantic, PyMuPDF, pytesseract, OpenCV
  - Frontend: Tailwind CSS, TanStack Query, React Hook Form
  - DevOps: Docker, GitHub Actions

Architecture / how it works
1. Browser (React SPA) — user authenticates with JWT and uploads an image/PDF.
2. API (FastAPI) — receives file, stores it, enqueues/executes preprocessing and OCR.
3. Preprocessing — crop to paper region, resize, deskew, remove shadows to improve OCR.
4. OCR — Tesseract (eng + tam) or PDF text extraction via PyMuPDF.
5. Extraction — an LLM is asked to map OCR/text to a fixed JSON invoice schema.
6. Validation — deterministic checks (GSTIN checksum, state code, line-item arithmetic, taxes, totals, date sanity). Invalid or uncertain fields are flagged and given a reason.
7. Review UI — user sees original image and editable fields, corrects flagged values, then verifies and exports CSV (UTF-8).
8. Persistence — validated data stored in PostgreSQL; uploaded files stored on the API host disk (or object storage if configured).

Annotated repository layout

```
.gitignore
docker-compose.yml            # local container orchestration
render.yaml                   # Render blueprint for API service
frontend/                     # React (Vite) SPA (project root for Vercel)
  package.json                # dev/build scripts (dev/build/test)
  src/                        # UI, routes, review screens, asset imports
  public/
  vercel.json                 # Vercel static config
backend/                      # FastAPI app, migrations, scripts, tests
  Dockerfile
  .env.example
  requirements.txt
  alembic/                    # DB migrations
  app/
    main.py                   # FastAPI app (includes routers, CORS)
    routers/                  # auth, invoices endpoints
    services/                 # extraction, ocr, validator logic
    models/                   # SQLAlchemy ORM models
    schemas/                  # Pydantic request/response models
  scripts/                    # evaluation, stress tests
  tests/                      # pytest tests
eval/                         # evaluation assets / scripts (results & experiments)
```

How it fits together
- The frontend talks to the backend via a single API origin (VITE_API_URL). The backend exposes interactive OpenAPI docs at /docs and a /health endpoint.
- Uploaded files are written to the API instance disk by default; for production, use an S3-compatible store for durability and multi-instance scaling.
- Validators run synchronously in the API process today; for scale, move background work to a job queue/worker with retries.

Quick start — run locally (shortest path)
Prerequisites:
- Python 3.10+ (or compatible), Node.js (LTS), Tesseract with `eng` and `tam` language packs, PostgreSQL.

Backend:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env                                    # set DATABASE_URL, SECRET_KEY, LLM credentials, etc.
alembic upgrade head
uvicorn app.main:app --reload
# API interactive docs: http://localhost:8000/docs
```

Frontend (separate terminal):
```bash
cd frontend
npm install
cp .env.example .env                                    # set VITE_API_URL to backend origin
npm run dev
# Frontend default URL shown by Vite, typically http://localhost:5173
```

Everything in containers:
```bash
# from repository root
docker compose up --build   # web on :8080, API on :8000 (see compose file for exact ports)
```

Environment variables (important)
- Backend (.env):
  - DATABASE_URL (SQLAlchemy-style URL e.g. postgresql+psycopg://user:pass@host/dbname)
  - SECRET_KEY (app secret)
  - CORS_ORIGINS (production frontend origin)
  - LLM_* or OPENAI_API_KEY (LLM provider credentials, per README)
  - Any Tesseract/PyMuPDF toggles if present
- Frontend (.env):
  - VITE_API_URL (API origin used by the SPA)

Deployment notes
- Recommended production stack in README: Neon (Postgres) + Render (API Docker service) + Vercel (frontend).
- Render blueprint (render.yaml) is included; set DATABASE_URL on the Render service to your Neon URL and set CORS_ORIGINS to the exact Vercel frontend origin.
- On Vercel, import the repo and set the project root to `frontend`; set VITE_API_URL to the Render API origin.
- Be careful with CORS origins and the allowed_origins list in backend/app/main.py (it currently allows a specific Vercel URL — replace with your production origin).

Security & operational considerations
- Never commit .env or production credentials. Generate a fresh SECRET_KEY for each environment.
- Uploaded files stored on the API instance disk are lost on instance restarts or scaling. Move to S3-compatible storage for durability and multi-instance setups.
- Tokens are currently stored in localStorage on the client; consider switching to httpOnly cookies for stronger XSS protection.
- Background work runs in-process. For reliability and retries, introduce a job queue (Redis + RQ/Celery or a managed job service).

Testing & evaluation
- Backend tests: run from backend/ with pytest:
```bash
cd backend
python -m pytest -q
```
- Frontend tests: `cd frontend && npm test` (configured in package.json).
- Evaluation scripts: backend/scripts includes `evaluate` and `validator_stress` modules to measure end-to-end accuracy and validator coverage. Run them inside the backend environment:
```bash
python -m scripts.evaluate
python -m scripts.validator_stress
```

API surface (observed)
- GET /health — returns {"status": "ok"}
- OpenAPI docs: /docs (FastAPI autogenerated)
- Uploads, auth, invoices routes exist under routers included in app.main (see backend/app/routers).

Troubleshooting tips
- First request slow on free hosting — the free backend may sleep; allow up to ~1 minute for the first wakeup.
- If OCR is poor: ensure Tesseract is installed with `eng` and `tam` data; validate pre-processing parameters (crop, resize).
- If validations flag many fields incorrectly, inspect the LLM extraction prompt/schema and the OCR text output for character errors (decimal points, similar-looking digits).
- Database connection errors: confirm DATABASE_URL uses SQLAlchemy-compatible scheme `postgresql+psycopg://` if required by the app.

Contributing
- Follow the existing structure: add backend logic under app/services, API surface in app/routers, and Pydantic contract changes in app/schemas with matching Alembic migrations.
- Run tests locally before opening PRs. The project uses GitHub Actions CI (see frontend README badges) to run backend and frontend tests.

License & contact
- See repository root for license (if present). If none, add a clear LICENSE file before wide use in production.
- For questions and context, refer to commit history and the frontend demo/illustrations in frontend/docs.

Appendix — Operational checklist before production
- Move file uploads to durable object storage (S3/compatible).
- Add a worker/queue for OCR/extraction with proper retries and observability.
- Rotate secrets and use environment-specific config (do not reuse dev secrets).
- Harden auth tokens (httpOnly cookie) and add rate limiting on upload endpoints.

---
This professional README is structured to be used as the repository root README.md. It consolidates the current project workflow, run & deployment instructions, and operational guidance based on the repository's backend and frontend layouts, Docker and Render configuration, and evaluation scripts.
