# Invoice Extractor

GST invoice extraction service: upload a bill, extract structured data, validate it, review and export.

## Backend setup
1. Install PostgreSQL and create database `invoice_db` with user `invoice`.
2. `cd backend`, create and activate a venv, then `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and fill in values.
4. `alembic upgrade head`
5. `uvicorn app.main:app --reload`, then open http://localhost:8000/docs
6. Run tests with `pytest -v`

## Deployment (Vercel + Render + Neon)

The frontend is a Vite SPA, the API is FastAPI, and PostgreSQL is required. The repository includes a Vercel rewrite for client-side routes and a Render Blueprint for the Docker-based API.

1. Create a PostgreSQL database on Neon. Copy its connection string and use the `postgresql+psycopg://` SQLAlchemy scheme (Neon may provide `postgresql://`); keep the SSL parameters.
2. In Render, create a Blueprint from this repository and apply `render.yaml`. Set `DATABASE_URL` to the Neon connection string and `CORS_ORIGINS` to the exact Vercel site origin, such as `https://your-app.vercel.app` (no trailing slash). Render generates `SECRET_KEY`. The Blueprint runs Alembic migrations before deploy and mounts persistent storage at `/app/uploads`.
3. In Vercel, import the same repository and set the project root to `frontend`. Set `VITE_API_URL` to the Render API origin, such as `https://invoice-extractor-api.onrender.com` (no trailing slash), then deploy.
4. After deployment, open the Render API's `/health` endpoint, then test account creation, login, invoice upload, OCR, and viewing the uploaded file.
5. If you use custom domains, update both `CORS_ORIGINS` in Render and `VITE_API_URL` in Vercel to the production origins, then redeploy the frontend.

The Render upload disk preserves invoice files across deploys, but it is tied to one Render service instance. Keep the service at one instance unless file storage is moved to shared object storage. Configure any optional LLM environment variables in Render if extraction is intended to use an LLM.

Never commit `.env` files or production credentials. Generate a fresh `SECRET_KEY` and rotate any database credential that has been exposed.