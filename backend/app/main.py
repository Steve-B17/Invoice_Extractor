from fastapi import FastAPI

app = FastAPI(title="Invoice Extractor API")


@app.get("/health")
def health():
    return {"status": "ok"}