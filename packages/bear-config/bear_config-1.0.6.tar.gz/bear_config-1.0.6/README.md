
# Bear Config

[![pypi version](https://img.shields.io/pypi/v/bear-config.svg)](https://pypi.org/project/bear-config/)

A useful Pydantic based config system with various options

## Installation

With [`uv`](https://docs.astral.sh/uv/): `uv tool install bear-config`

## Configuration precedence

Values are merged in order; later sources override earlier ones:

1. `default.toml`
2. `{env}.toml` (for the active environment, e.g., `dev.toml`, `prod.toml`)
3. `local.toml`
4. Environment variables prefixed with your program name (e.g., `MY_APP_...`)

Search paths (by default): `~/.config/{program}/` and `./config/{program}/`.

## Quickstart

Define a Pydantic model for your settings, then load it with the `ConfigManager`.

```python
from pydantic import BaseModel
from bear_config.config_manager import ConfigManager


class Database(BaseModel):
    host: str = "localhost"
    port: int = 5432


class Settings(BaseModel):
    database: Database = Database()
    debug: bool = False


config = ConfigManager[Settings](
    config_model=Settings,
    program_name="my_app",
    env="dev",
).config

print(config.database.host)
print(config.debug)
```

Environment variables can override nested keys using the program prefix. For example, `MY_APP_DATABASE_HOST=prod.db` and `MY_APP_DEBUG=true` will replace the corresponding fields after files are loaded.

## Generating a default config

You can scaffold a TOML file with the model’s default values:

```python
from bear_config.config_manager import ConfigManager

config_mgr = ConfigManager[Settings](Settings, program_name="my_app")
config_mgr.create_default_config()  # writes default.toml into the local config dir
```
