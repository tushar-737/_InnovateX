"""Health + product metadata (data notices, honesty notes)."""

from fastapi import APIRouter

from ..config import get_settings
from ..schemas import MetaOut

router = APIRouter()
settings = get_settings()

DATA_NOTICE = (
    "ILLUSTRATIVE SEED DATA — NOT OFFICIAL. Job roles, district demand and training "
    "centres are mock values for this prototype. Replace with official NCVET/NSQF QPs, "
    "NSDC, NCS, e-Shram and district data before any real use. No salary, placement or "
    "scheme-eligibility claims are made."
)
HONESTY_NOTE = (
    "Prototype for SIH 2026. Speech recognition and speech output use the browser's Web "
    "Speech API in this demo (Bhashini/Whisper adapters are designed but not connected). "
    "The conversational brain uses Claude if an API key is configured on the backend, and "
    "a built-in Hindi rule engine otherwise. The recommendation engine is transparent "
    "TF-IDF + weighted rules and runs fully offline."
)


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


@router.get("/meta", response_model=MetaOut)
def meta() -> MetaOut:
    return MetaOut(
        app_name=settings.app_name,
        version=settings.app_version,
        data_notice=DATA_NOTICE,
        honesty_note=HONESTY_NOTE,
        languages=["hi-IN (Hindi)", "Hinglish friendly", "en-IN (English display)"],
    )
