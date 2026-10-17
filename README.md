<!--
  Polished README for Invoice_Extractor
  Replaces the existing README.md with styled Markdown, TOC links, clear sections, and improved code blocks.
-->

# Invoice Extractor

[![Docs](https://img.shields.io/badge/docs-OpenAPI-blue.svg)](#api)
[![Demo](https://img.shields.io/badge/demo-available-lightgrey.svg)](<<your Vercel link>>)

Turn photos or PDFs of Indian GST bills (including bills with Tamil text) into validated, reviewable, structured data ready for export (CSV). The pipeline combines image preprocessing, Tesseract OCR, LLM-assisted extraction into a fixed schema, and deterministic validators to guarantee arithmetic and GST checks; a human review step finalizes corrections.

---

## Table of contents

- [Why this project](#why-this-project)
- [Tech stack](#tech-stack)
- [Architecture overview](#architecture-overview)
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

## Why this project

OCR and LLMs make errors on photos and degraded scans. This project treats the AI as a reader, not a final authority: extracted values are validated by deterministic rules (GSTIN checksum, tax/total arithmetic, date sanity). Anything that doesn't add up is flagged for a human to review and correct before the data is exported.

Use cases:
- Accounts-payable teams converting paper/PDF invoices to structured records.
- Small businesses that need reliable invoice capture from phone photos.

---

## Tech stack

- Languages: **Python** (backend), **JavaScript / React (Vite)** (frontend)
- Backend: FastAPI, Uvicorn, SQLAlchemy 2, Alembic
- OCR / imaging: pytesseract (eng + tam), OpenCV (cv2), PyMuPDF
- Frontend: React (Vite), Tailwind CSS, TanStack Query, React Hook Form
- Database: PostgreSQL (Neon recommended)
- DevOps: Docker, docker-compose, Render (API), Vercel (frontend)

---

## Architecture overview

```mermaid
flowchart LR
  Browser[Browser (React)] -->|JWT| API[FastAPI API]
  API --> DB[(PostgreSQL)]
  API --> Preproc[Image preprocessing: crop, resize, deskew]
  Preproc --> OCR[Tesseract OCR or PDF text layer]
  OCR --> LLM[LLM extraction → fixed JSON schema]
  LLM --> Validators[Deterministic validators: GSTIN, arithmetic]
  Validators --> DB
  DB --> Browser
```

High-level flow:
1. Upload image or PDF from the browser.
2. API preprocesses images and runs OCR (Tesseract or PDF text).
3. An LLM maps text into a fixed invoice JSON schema.
4. Validators check GSTINs, tax arithmetic, totals, and dates. Flagged fields are annotated with reasons.
5. The review screen shows original image and editable fields. After verification the user exports CSV.

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
    routers/                  # auth.py, invoices.py
    services/                 # OCR, extraction, validators
    models/                   # SQLAlchemy models
    schemas/                  # Pydantic schemas
  scripts/                    # evaluation & stress-test scripts
  tests/                      # pytest suite
eval/                         # evaluation datasets and scripts
```

**How it fits together:** The frontend (configured with VITE_API_URL) calls the FastAPI backend for auth, uploads, and review endpoints. Uploaded files are stored on the API host by default (move to object storage for production). Validators are synchronous in-process today; for scale move them to background workers and a queue.

---

## Quick start (local)

Prerequisites: Python 3.10+, Node.js (LTS), Tesseract with `eng` and `tam` language packs, PostgreSQL.

Backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env        # set DATABASE_URL, SECRET_KEY, LLM credentials
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

Run everything with Docker Compose from the repository root:

```bash
docker compose up --build
# API on :8000, frontend on :8080 (check docker-compose.yml for exact ports)
```

---

## Deployment (Render + Vercel + Neon)

- Create a PostgreSQL database on Neon and copy its connection string. Ensure the SQLAlchemy scheme (postgresql+psycopg://) is used if required.
- In Render, create a service from this repository and apply `render.yaml`. Set `DATABASE_URL` to the Neon URL and `CORS_ORIGINS` to the Vercel frontend origin.
- In Vercel, import this repo and set the project root to `frontend`. Set `VITE_API_URL` to the Render API origin.
- After deployment, check API `/health` and test upload → OCR → review → export flows.

Notes: the Render disk preserves uploaded files only on that instance. Use S3-compatible storage to support multi-instance scaling and durable uploads.

---

## Environment variables (important)

Backend (.env):
- DATABASE_URL — SQLAlchemy-style DB URL (e.g. postgresql+psycopg://user:pass@host/dbname)
- SECRET_KEY — application secret
- CORS_ORIGINS — frontend origin(s)
- LLM / OpenAI credentials — provider-specific environment variables

Frontend (.env):
- VITE_API_URL — backend origin used by the SPA

---

## Testing & evaluation

- Backend tests:

```bash
cd backend
python -m pytest -q
```

- Frontend tests:

```bash
cd frontend
npm test
```

- Evaluation scripts (end-to-end and validator stress tests):

```bash
cd backend
python -m scripts.evaluate
python -m scripts.validator_stress
```

---

## Operational notes & security

- Do not commit `.env` or production credentials. Rotate secrets if exposed.
- Uploaded files are stored on the API instance disk by default and will be lost when the instance restarts; migrate to S3 or compatible object storage for production.
- Tokens are currently in `localStorage`; consider httpOnly cookies for stronger XSS protection.
- Move long-running or heavy workloads (OCR, LLM calls) to background workers with queues for scalability and reliability.

---

## Troubleshooting

- Slow first request in free hosting: the backend may sleep; first wake can take ~1 minute.
- OCR accuracy issues: ensure Tesseract `eng` and `tam` data are installed, and tune preprocessing (crop, resize, deskew).
- Validation errors: inspect the OCR text and LLM extraction; missing decimal points or misread digits are common causes.
- DB connection failures: confirm `DATABASE_URL` scheme and credentials.

---

## Contributing

- Add backend logic under `backend/app/services`, API endpoints under `backend/app/routers`, and Pydantic schema changes under `backend/app/schemas`.
- Add Alembic migrations for DB schema changes.
- Run tests locally before opening PRs.

---

## License & contact

If this repository does not include a LICENSE file, add one before using this code broadly. Recommended: MIT or Apache-2.0.

For questions, open an issue or check the commit history and frontend demo illustrations.

---

*This README was updated to improve clarity and styling. Replace placeholder demo links and badges with your production URLs and badges as appropriate.*
