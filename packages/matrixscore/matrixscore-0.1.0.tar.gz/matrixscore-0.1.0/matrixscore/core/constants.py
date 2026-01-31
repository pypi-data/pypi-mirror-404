"""Generic constants and default paths for rating engine."""
from pathlib import Path

_BASE_DIR = Path(__file__).parent.parent
LOG_DIR = _BASE_DIR / "logs"
ITEM_CACHE_PATH = _BASE_DIR / "item_cache.json"
