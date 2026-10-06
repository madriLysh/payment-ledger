from os import getenv

class Config:

    DATABASE_URL: str = getenv("DATABASE_URL", "postgresql+psycopg://localhost:5432/payment_ledger")
    DB_POOL_SIZE: int = int(getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_TIMEOUT: int = int(getenv("DB_POOL_TIMEOUT", "30"))
    DB_ECHO: bool = getenv("DB_ECHO", "false").lower() == "true"
    EXPIRED_URLS_BATCH_SIZE: int = int(getenv("EXPIRED_URLS_BATCH_SIZE", "1000"))