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
    ocr_psm: int = 4
    max_pdf_pages: int = 3

    # LLM (any OpenAI-compatible chat completions endpoint)
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None
    llm_json_mode: bool = True
    llm_timeout_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()