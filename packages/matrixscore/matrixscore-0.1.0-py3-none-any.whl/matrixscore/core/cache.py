"""Generic cache helpers for rating engine items."""
import json
from pathlib import Path
from typing import Callable, Dict, Optional, Any, Tuple

ITEM_CACHE: Dict[Tuple[str, Optional[str]], Dict[str, Any]] = {}
ITEM_CACHE_STATS = {"hit": 0, "miss": 0, "persist_fail": 0, "loaded": 0}

_BASE_DIR = Path(__file__).resolve().parent.parent
_CACHE_PATH = _BASE_DIR / "item_cache.json"


def cache_key(name: str, context: Optional[str] = None) -> Tuple[str, Optional[str]]:
    return (name.strip().lower(), context)


def load_cache() -> None:
    if not _CACHE_PATH.exists():
        return
    try:
        data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        for k, v in data.items():
            try:
                nm, ctx = k.split("|", 1)
            except ValueError:
                nm, ctx = k, ""
            ctx_val = ctx if ctx else None
            ITEM_CACHE[(nm, ctx_val)] = v
            ITEM_CACHE_STATS["loaded"] += 1
    except Exception:
        pass


def save_cache() -> None:
    try:
        ser = {}
        for (nm, ctx), val in ITEM_CACHE.items():
            ctx_part = "" if ctx is None else ctx
            ser[f"{nm}|{ctx_part}"] = val
        _CACHE_PATH.write_text(json.dumps(ser), encoding="utf-8")
    except Exception:
        ITEM_CACHE_STATS["persist_fail"] += 1


def cache_item(
    name: str,
    context: Optional[str] = None,
    loader: Optional[Callable[[str], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    key = cache_key(name, context=context)
    cached = ITEM_CACHE.get(key)
    if cached:
        ITEM_CACHE_STATS["hit"] += 1
        return cached
    ITEM_CACHE_STATS["miss"] += 1
    info = {"name": name.strip(), "context": context}
    if loader:
        try:
            info.update(loader(name))
        except Exception:
            pass
    cached = {"info": info}
    ITEM_CACHE[key] = cached
    save_cache()
    return cached


def portfolio_infos_from_cache(
    portfolio,
    context: Optional[str] = None,
    loader: Optional[Callable[[str], Dict[str, Any]]] = None,
):
    infos = []
    for item in portfolio:
        name = item.get("name", "")
        cached = cache_item(name, context=context, loader=loader)
        info = dict(cached.get("info") or {})
        info.setdefault("issues", item.get("issues") or [])
        info.setdefault("capabilities", item.get("capabilities") or [])
        info.setdefault("strength", item.get("strength"))
        info.setdefault("category", item.get("category"))
        infos.append(info)
    return infos
