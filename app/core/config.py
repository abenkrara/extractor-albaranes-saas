"""
Módulo de Configuración Global del Sistema.
Carga y valida las variables de entorno usando Pydantic Settings.
"""

from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuraciones de la aplicación cargadas desde el archivo .env o variables de entorno."""

    # Proveedor de Inteligencia Artificial ("openai" o "groq")
    LLM_PROVIDER: Literal["openai", "groq"] = "groq"

    # Credenciales de OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Credenciales de Groq (openai/gpt-oss-120b u openai/gpt-oss-20b)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    # Configuración de red y servidores
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8008
    FRONTEND_PORT: int = 8505
    BACKEND_URL: str = "http://localhost:8008"

    # Configuración de límites de carga
    MAX_FILE_SIZE_MB: int = 20
    MAX_PAGES_TO_PROCESS: int = 15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Instancia singleton para importar en toda la app
settings = Settings()

