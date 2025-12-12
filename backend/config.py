# backend/config.py
import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    # Groq / Model
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # DB
    DATABASE_URL: str = "postgresql+psycopg2://postgres:password@db:5432/john_agent"

    # Auth
    JWT_SECRET: str = "change-this-secret"
    JWT_ALGORITHM: str = "HS256"
    ADMIN_USER: str = "admin"
    ADMIN_PASS: str = "adminpass"

    # Email (SMTP)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""

    # Twilio
    TWILIO_SID: str = ""
    TWILIO_TOKEN: str = ""
    TWILIO_FROM: str = ""

    # CORS
    CORS_ORIGINS: str = "*"  # comma separated

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

