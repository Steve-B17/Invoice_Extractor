# Invoice Extractor

Turn photos or PDFs of Indian GST bills (including bills with Tamil text) into validated, reviewable, structured data ready for export (CSV). The system combines image preprocessing, OCR (Tesseract), LLM-assisted extraction into a fixed schema, and deterministic validators to ensure arithmetic and GST checks; a human review step finalizes correctness before export.

---

## Table of contents

- [Overview](#overview)
- [Tech stack](#tech-stack)
- [How it works](#how-it-works)
- [Repository layout](#repository-layout)
- [Quick start (local)](#quick-start-local)
- [Docker / Compose](#docker--compose)
- [Deployment (Render + Vercel + Neon)](#deployment-render--vercel--neon)
- [Environment variables](#environment-variables)
- [Testing & evaluation](#testing--evaluation)
- [Operational notes & security](#operational-notes--security)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License & contact](#license--contact)

---

## Overview

This repository implements a full-stack pipeline for extracting structured invoice data from images or PDFs. The design emphasizes reliability: extracted values are validated with deterministic checks (GSTIN checksum, tax arithmetic, totals, date sanity). Fields that fail validation are highlighted for human review.

Primary users:
- Accounts-payable teams and small businesses needing accurate invoice capture from phone photos or PDFs.

---

## Tech stack

- Languages: Python (backend), JavaScript/React (frontend)
- Backend: FastAPI, Uvicorn, SQLAlchemy 2, Alembic
- OCR / imaging: Tesseract (eng + tam), OpenCV, PyMuPDF
- Frontend: React (Vite), Tailwind CSS, TanStack Query, React Hook Form
- Database: PostgreSQL (Neon recommended)
- DevOps: Docker, docker-compose, Render (API), Vercel (frontend)

---

## How it works

1. The user uploads a photo or PDF via the React SPA.
2. The backend preprocesses images (crop, resize, deskew, shadow removal) to improve OCR.
3. OCR is performed with Tesseract (English + Tamil) or the PDF text layer is read with PyMuPDF.
4. An LLM maps the OCR/text into a fixed JSON invoice schema.
5. Deterministic validators (GSTIN checksum, line-item arithmetic, tax totals, dates) check the extracted fields. Any issues are flagged with an explanation.
6. The review UI presents the original image next to editable fields; a human verifies and saves the record.
7. Verified data can be exported as CSV (UTF-8, Excel-ready).

---

## Repository layout

```
README.md
docker-compose.yml            # local container orchestration
render.yaml                   # Render blueprint for API service
frontend/                     # React (Vite) SPA
  package.json
  src/                        # UI, routes, review screens
  public/
backend/                      # FastAPI app and supporting files
  Dockerfile
  .env.example
  requirements.txt
  alembic/
  app/
    main.py                   # FastAPI app instantiation (routers & CORS)
    core/                     # configuration
    routers/                  # auth, invoices endpoints
    services/                 # OCR, extraction, validators
    models/                   # SQLAlchemy models
    schemas/                  # Pydantic schemas
  scripts/                    # evaluation & stress-test scripts
  tests/                      # pytest suite
eval/                         # evaluation datasets and scripts
```

---

## Quick start (local)

Prerequisites:
- Python 3.10+
- Node.js (LTS)
- Tesseract installed with `eng` and `tam` language packs
- PostgreSQL (or a managed Postgres instance)

Backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env        # set DATABASE_URL, SECRET_KEY, CORS_ORIGINS, and LLM credentials if used
alembic upgrade head
uvicorn app.main:app --reload
# API docs: http://localhost:8000/docs
```

Frontend (separate terminal):

```bash
cd frontend
npm install
cp .env.example .env        # set VITE_API_URL to backend origin
npm run dev
# Frontend dev URL: typically http://localhost:5173
```

---

## Docker / Compose

Run both services with Docker Compose from the repository root:

```bash
docker compose up --build
# API typically on :8000, frontend on :8080 (check docker-compose.yml for exact ports)
```

---

## Deployment (Render + Vercel + Neon)

1. Create a PostgreSQL database on Neon and copy its connection string.
2. In Render, create a service and apply `render.yaml`. Set `DATABASE_URL` to the Neon connection string and `CORS_ORIGINS` to the frontend origin.
3. In Vercel, import the repo and set the project root to `frontend`. Set `VITE_API_URL` to the Render API origin.
4. After deployment, verify the API `/health` endpoint and end-to-end flows (signup/login, upload, OCR, review, export).

Notes: uploaded files are stored on the API instance disk by default. For durability and multi-instance scaling, configure S3-compatible object storage and update upload handling.

---

## Environment variables

Set these in `backend/.env` (copy from `.env.example`):

- DATABASE_URL — SQLAlchemy-style DB URL (e.g. `postgresql+psycopg://user:pass@host/dbname`)
- SECRET_KEY — application secret
- CORS_ORIGINS — comma-separated frontend origin(s) (e.g. `http://localhost:5173,https://your-frontend.vercel.app`)
- LLM_BASE_URL, LLM_API_KEY, LLM_MODEL — set if using an external LLM provider

Frontend `.env` variables:
- VITE_API_URL — backend origin used by the SPA

---

## Testing & evaluation

Backend tests:

```bash
cd backend
python -m pytest -q
```

Frontend tests:

```bash
cd frontend
npm test
```

Evaluation scripts (end-to-end and validator stress tests):

```bash
cd backend
python -m scripts.evaluate
python -m scripts.validator_stress
```

---

## Operational notes & security

- Never commit `.env` or production credentials. Rotate credentials if exposed.
- Uploaded files stored on the API host are ephemeral across deploys/restarts. Use object storage for production.
- Tokens are stored in `localStorage` by default; consider httpOnly cookies for stronger protection against XSS.
- For scale and reliability, move OCR/LLM work to background workers with a job queue and retries.

---

## Troubleshooting

- Slow first request on free hosting: the backend may be asleep; the first request can take up to a minute.
- OCR issues: ensure Tesseract `eng` and `tam` language packs are installed and validate preprocessing parameters.
- Validation flags: inspect OCR output and LLM-provided JSON when arithmetic or decimal issues appear.
- DB connection errors: confirm `DATABASE_URL` uses the correct SQLAlchemy scheme and credentials.

---

## Contributing

- Add backend logic under `backend/app/services`, API endpoints under `backend/app/routers`, and Pydantic schema changes under `backend/app/schemas`.
- Add Alembic migrations for DB schema changes.
- Run tests locally before opening PRs; CI will run both backend and frontend tests.

---

## License & contact

If this repository does not include a LICENSE file, add one before using the code broadly. Common choices: MIT or Apache-2.0.

For questions, open an issue or check the commit history and frontend documentation.

---

This README has been proofread and updated to remove obvious errors and placeholders. Replace demo links and badges with your production URLs if desired.
