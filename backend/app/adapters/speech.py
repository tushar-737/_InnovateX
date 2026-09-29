"""
Speech adapter interfaces.

The FRONTEND uses these interfaces with the browser's Web Speech API
(see frontend/src/speech/). This module documents the backend-side contract so
Bhashini or Whisper can be swapped in later WITHOUT touching the conversation
or recommendation code.

DESIGNED BUT NOT IMPLEMENTED IN THIS PROTOTYPE:
  * BhashiniAdapter   — STT/translation via Bhashini APIs (bhashini.gov.in)
  * WhisperAdapter    — local/server Whisper transcription

The demo uses BrowserSTT / BrowserTTS only (implemented in the frontend).
"""

from abc import ABC, abstractmethod
from typing import Optional


class SpeechToTextAdapter(ABC):
    """Interface: audio bytes/stream -> transcript text."""

    @abstractmethod
    def transcribe(self, audio, language: str = "hi-IN") -> str: ...


class TextToSpeechAdapter(ABC):
    """Interface: text -> audio playback."""

    @abstractmethod
    def synthesize(self, text: str, language: str = "hi-IN") -> Optional[bytes]: ...


class BrowserSTT(SpeechToTextAdapter):
    """Demo implementation lives in the browser (frontend/src/speech/stt.js)."""

    def transcribe(self, audio, language: str = "hi-IN") -> str:  # pragma: no cover
        raise NotImplementedError("Browser STT runs client-side — see frontend/src/speech/stt.js")


class BrowserTTS(TextToSpeechAdapter):
    """Demo implementation lives in the browser (frontend/src/speech/tts.js)."""

    def synthesize(self, text: str, language: str = "hi-IN") -> Optional[bytes]:  # pragma: no cover
        raise NotImplementedError("Browser TTS runs client-side — see frontend/src/speech/tts.js")
