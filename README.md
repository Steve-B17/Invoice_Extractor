# Invoice Extractor

GST invoice extraction service: upload a bill, extract structured data, validate it, review and export.

## Backend setup
1. Install PostgreSQL and create database `invoice_db` with user `invoice`.
2. `cd backend`, create and activate a venv, then `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and fill in values.
4. `alembic upgrade head`
5. `uvicorn app.main:app --reload`, then open http://localhost:8000/docs
6. Run tests with `pytest -v`