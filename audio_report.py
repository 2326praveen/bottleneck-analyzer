"""Text-to-speech feedback for analyzer results."""

from __future__ import annotations

import threading
from typing import Optional

import pyttsx3

_ENGINE: Optional[pyttsx3.Engine] = None
_ENGINE_LOCK = threading.Lock()


def _get_engine() -> pyttsx3.Engine:
    global _ENGINE
    with _ENGINE_LOCK:
        if _ENGINE is None:
            _ENGINE = pyttsx3.init()
        return _ENGINE


def narrate_result(bottleneck: str, suggestion: str) -> None:
    text = f"Detected {bottleneck}. Suggested action: {suggestion}"
    try:
        engine = _get_engine()
        engine.say(text)
        engine.runAndWait()
    except Exception:  # pragma: no cover - best effort audio feedback
        pass
