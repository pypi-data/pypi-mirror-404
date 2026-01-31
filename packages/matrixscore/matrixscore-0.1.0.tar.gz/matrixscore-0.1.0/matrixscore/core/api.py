"""Generic data loader hooks for rating engine."""
from typing import Callable, Dict, Any, Optional, Tuple

_log_verbose = lambda _msg: None
_item_loader: Optional[Callable[[str], Dict[str, Any]]] = None
_context_loader: Optional[Callable[[str], Dict[str, Any]]] = None


def set_log_verbose(fn):
    global _log_verbose
    _log_verbose = fn or (lambda _msg: None)


def register_item_loader(fn: Callable[[str], Dict[str, Any]]):
    """Register a loader that returns item metadata by name."""
    global _item_loader
    _item_loader = fn


def register_context_loader(fn: Callable[[str], Dict[str, Any]]):
    """Register a loader that returns context metadata by key."""
    global _context_loader
    _context_loader = fn


def load_item(name: str) -> Dict[str, Any]:
    if not _item_loader:
        return {"name": name}
    try:
        return _item_loader(name) or {"name": name}
    except Exception as exc:
        _log_verbose(f"[loader] item failed for {name}: {exc}")
        return {"name": name}


def load_context(key: str) -> Dict[str, Any]:
    if not _context_loader:
        return {"key": key}
    try:
        return _context_loader(key) or {"key": key}
    except Exception as exc:
        _log_verbose(f"[loader] context failed for {key}: {exc}")
        return {"key": key}


def load_item_bundle(name: str, context: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Convenience helper to load item + optional context metadata."""
    item = load_item(name)
    ctx = load_context(context) if context else {}
    return item, ctx
