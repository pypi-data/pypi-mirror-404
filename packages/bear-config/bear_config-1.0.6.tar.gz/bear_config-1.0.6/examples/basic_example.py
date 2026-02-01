"""Basic example of using Bear Config with Pydantic models."""  # noqa: INP001

from collections.abc import Callable  # noqa: TC003

from pydantic import BaseModel

from bear_config.common import nullable_string_validator
from bear_config.manager import ConfigManager


class DatabaseConfig(BaseModel):
    """Configuration for an example database connection."""

    host: str = "localhost"
    port: int = 5432
    username: str = "app"
    password: str = "example"  # noqa: S105, just an example
    database: str = "myapp"


class LoggingConfig(BaseModel):
    """Configuration for an example logging setup."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str | None = None

    _validate_file: Callable[..., str | None] = nullable_string_validator("file")


class AppConfig(BaseModel):
    """Example application configuration model."""

    database: DatabaseConfig = DatabaseConfig()
    logging: LoggingConfig = LoggingConfig()
    environment: str = "development"
    debug: bool = False
    api_key: str = "your-api-key-here"
    allowed_hosts: list[str] = ["localhost", "127.0.0.1"]


def get_config_manager(env: str = "dev") -> ConfigManager[AppConfig]:
    """Get a configured ConfigManager instance."""
    return ConfigManager[AppConfig](
        config_model=AppConfig,
        program_name="_test_app",
        file_names=["default.toml", "development.toml", "local.toml"],
        env=env,
    )


config_manager: ConfigManager[AppConfig] = get_config_manager("dev")
config_manager.create_default_config()
config: AppConfig = config_manager.config

print(f"Database host: {config.database.host}")
print(f"Database port: {config.database.port}")
print(f"Debug mode: {config.debug}")
print(f"Environment: {config.environment}")

if config_manager.has_config(LoggingConfig):
    logging_config: LoggingConfig | None = config_manager.get_config(LoggingConfig)
    if logging_config is not None:
        print(f"Logging level: {logging_config.level}")
