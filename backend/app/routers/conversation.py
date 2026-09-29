"""Conversation endpoints — voice-turn flow and the confirmation read-back."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DbSession

from ..database import get_db
from ..models import ConversationTurn, Profile as ProfileRow, Session as SessionRow
from ..schemas import ConfirmRequest, ConfirmResponse, Profile, TurnRequest, TurnResponse
from ..services.dialogue import DialogueEngine, build_readback
from ..services.extraction import extract_fields, is_confirmation
from ..services.seed_loader import load_districts

router = APIRouter()
engine = DialogueEngine(districts=load_districts())


def _load_profile(db: DbSession, session_id: str) -> Profile:
    row = db.get(ProfileRow, session_id)
    if row and row.fields:
        return Profile(**row.fields)
    return Profile()


def _save_profile(db: DbSession, session_id: str, profile: Profile, confirmed: bool = False) -> None:
    row = db.get(ProfileRow, session_id)
    if row is None:
        row = ProfileRow(session_id=session_id, fields=profile.as_field_dict(), is_confirmed=confirmed)
        db.add(row)
    else:
        row.fields = profile.as_field_dict()
        row.is_confirmed = confirmed
    db.commit()


def _history(db: DbSession, session_id: str, limit: int = 12) -> list[dict]:
    turns = (
        db.query(ConversationTurn)
        .filter(ConversationTurn.session_id == session_id)
        .order_by(ConversationTurn.id.desc())
        .limit(limit)
        .all()
    )
    return [{"role": t.role, "text": t.text} for t in reversed(turns)]


@router.post("/conversation/turn", response_model=TurnResponse)
def conversation_turn(body: TurnRequest, db: DbSession = Depends(get_db)) -> TurnResponse:
    if not db.get(SessionRow, body.session_id):
        raise HTTPException(status_code=404, detail="Session not found — please accept consent first.")

    profile = _load_profile(db, body.session_id)
    history = _history(db, body.session_id)

    db.add(ConversationTurn(session_id=body.session_id, role="user", text=body.user_text))
    db.commit()

    response = engine.turn(profile, body.user_text, history)
    _save_profile(db, body.session_id, profile)

    db.add(ConversationTurn(session_id=body.session_id, role="assistant", text=response.reply_text))
    db.commit()
    return response


@router.post("/conversation/confirm", response_model=ConfirmResponse)
def conversation_confirm(body: ConfirmRequest, db: DbSession = Depends(get_db)) -> ConfirmResponse:
    """Read the profile back by voice ('Aapne bataya ki...') and accept corrections."""
    if not db.get(SessionRow, body.session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    profile = _load_profile(db, body.session_id)
    readback_hi, readback_en = build_readback(profile)

    is_confirmed = False
    reply_hi = "क्या यह जानकारी सही है? अगर कुछ बदलना हो तो बताइए।"

    if body.user_text and body.user_text.strip():
        text = body.user_text.strip()
        if is_confirmation(text):
            is_confirmed = True
            reply_hi = "बहुत शुक्रिया! अब मैं आपके लिए सबसे अच्छे प्रशिक्षण और काम के रास्ते देख रहा हूँ।"
        else:
            # Corrections like "umar 26 hai" / "silai bhi aati hai" / "district barmer"
            updates = extract_fields(text, load_districts(), context_field=None)
            if updates:
                merged = profile.model_dump()
                for key, value in updates.items():
                    if key in ("skills", "interests"):
                        existing = merged.get(key) or []
                        for tag in value:
                            if tag not in existing:
                                existing.append(tag)
                        merged[key] = existing
                    else:
                        merged[key] = value
                profile = Profile(**merged)
                readback_hi, readback_en = build_readback(profile)
                reply_hi = "ठीक है, मैंने बदलाव जोड़ लिया। यह दोबारा सुनिए। क्या अब सही है?"
            else:
                reply_hi = "माफ़ कीजिए, मैं बदलाव नहीं समझ पाया। कृपया फिर से कहिए — जैसे 'उम्र 26 साल'।"

    _save_profile(db, body.session_id, profile, confirmed=is_confirmed)
    return ConfirmResponse(
        readback_text=readback_hi,
        readback_text_en=readback_en,
        profile=profile,
        is_confirmed=is_confirmed,
        reply_text=reply_hi,
    )
