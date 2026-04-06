from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "API Auditoria"
    debug: bool = False

    # MySQL
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = ""
    mysql_password: str = ""
    mysql_database: str = ""

    # OpenRouter / LLM
    openrouter_api_key: str = ""
    default_model: str = "anthropic/claude-sonnet-4-5-20250514"
    fallback_model: str = "anthropic/claude-sonnet-4-20250514"

    model_config = {"env_file": ".env", "extra": "ignore"}


def get_settings() -> Settings:
    return Settings()
