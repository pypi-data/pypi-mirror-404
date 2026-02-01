"""Bear Config package.

A useful Pydantic based config system with various options
"""

from bear_config._internal.cli import main
from bear_config._internal.info import METADATA

__version__: str = METADATA.version

__all__: list[str] = ["METADATA", "__version__", "main"]
