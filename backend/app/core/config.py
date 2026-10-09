from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 30
    upload_dir: str = "uploads"
    max_upload_mb: int = 10

    # OCR
    tesseract_cmd: str | None = None
    ocr_language: str = "eng"
    ocr_psm: int = 6
    max_pdf_pages: int = 3

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()