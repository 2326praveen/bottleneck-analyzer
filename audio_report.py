"""Text-to-speech feedback for analyzer results."""

from __future__ import annotations

import threading
from typing import Optional

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

_ENGINE: Optional["pyttsx3.Engine"] = None
_ENGINE_LOCK = threading.Lock()


def _get_engine() -> Optional["pyttsx3.Engine"]:
    """Get or create the TTS engine. Returns None if pyttsx3 is not available."""
    global _ENGINE
    if pyttsx3 is None:
        return None
    
    with _ENGINE_LOCK:
        if _ENGINE is None:
            try:
                _ENGINE = pyttsx3.init()
            except Exception:
                return None
        return _ENGINE


def narrate_result(bottleneck: str, suggestion: str) -> None:
    """Narrate the analysis result using text-to-speech (if available)."""
    if pyttsx3 is None:
        return  # Silently skip if TTS not available
    
    text = f"Detected {bottleneck}. Suggested action: {suggestion}"
    try:
        engine = _get_engine()
        if engine:
            engine.say(text)
            engine.runAndWait()
    except Exception:  # pragma: no cover - best effort audio feedback
        pass
