from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.routers import auth

app = FastAPI(title="Invoice Extractor API")

app.include_router(auth.router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    return {"status": "ok"}