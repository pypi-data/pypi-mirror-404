from pathlib import Path
from typing import Final

__version__: Final[str] = "0.2.0"

MDC_API_KEY_NAME: Final[str] = "MDC_API_KEY"
MDC_CACHE_NAME: Final[str] = "MDC_CACHE"
DEFAULT_MDC_CACHE: Final[Path] = Path("~/.cache/mdc-ds/downloads").expanduser()
