from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.routers import auth, invoices

app = FastAPI(title="Invoice Extractor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://invoice-extractor-one-blue.vercel.app/", "http://localhost:5173"],
    allow_credentials=True,   # the token travels in an Authorization header, not a cookie
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],   # lets the frontend read the CSV file name
)

app.include_router(auth.router)
app.include_router(invoices.router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    return {"status": "ok"}