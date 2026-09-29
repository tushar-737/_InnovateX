"""Session lifecycle + consent + privacy (delete my data)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DbSession

from ..database import get_db
from ..models import ConversationTurn, Profile as ProfileRow, Session as SessionRow
from ..schemas import ConsentRequest, DeleteResponse, SessionOut

router = APIRouter()

CONSENT_TEXT_HI = (
    "नमस्ते! मैं कौशल साथी हूँ। मैं आपकी मदद के लिए कुछ आसान सवाल पूछूँगा — जैसे उम्र, ज़िला, "
    "पढ़ाई और काम। आपकी बातचीत से यह जानकारी इस फ़ोन/कंप्यूटर में सुरक्षित रखी जाती है ताकि आपको "
    "सही प्रशिक्षण और काम के रास्ते बताए जा सकें। कोई पैसा या नौकरी पक्की नहीं होती — सिर्फ़ "
    "जानकारी और सुझाव मिलते हैं। आप कभी भी कह सकते हैं 'मेरा डेटा मिटाओ' और आपकी सारी जानकारी "
    "मिटा दी जाएगी। क्या आप आगे बढ़ना चाहेंगे?"
)
CONSENT_TEXT_EN = (
    "Hello! I am Kaushal Saathi. I will ask a few easy questions — like age, district, "
    "education and work — to suggest training and livelihood options. Your conversation is "
    "stored on this device for this purpose only. No money or job is guaranteed; these are "
    "information and suggestions only. You can say 'delete my data' any time and everything "
    "will be erased. Shall we begin?"
)
CONSENT_READ_TEXT_HI = (
    "नमस्ते! मैं कौशल साथी हूँ। मैं आपकी मदद के लिए कुछ आसान सवाल पूछूँगा। आपकी जानकारी सिर्फ़ "
    "सही प्रशिक्षण और काम के सुझाव देने के लिए रखी जाती है। कोई नौकरी या पैसा पक्का नहीं होता। "
    "आप कभी भी कह सकते हैं मेरा डेटा मिटाओ। क्या हम शुरू करें?"
)


@router.post("/session", response_model=SessionOut)
def create_session(body: ConsentRequest, db: DbSession = Depends(get_db)) -> SessionOut:
    session_id = str(uuid.uuid4())
    row = SessionRow(
        id=session_id,
        consent_given=bool(body.consent_given),
        consent_audio=True,
        locale=body.locale or "hi-IN",
    )
    db.add(row)
    db.commit()
    return SessionOut(
        session_id=session_id,
        consent_text=CONSENT_TEXT_HI,
        consent_text_en=CONSENT_TEXT_EN,
        consent_read_text=CONSENT_READ_TEXT_HI,
    )


@router.get("/session/{session_id}")
def get_session(session_id: str, db: DbSession = Depends(get_db)):
    row = db.get(SessionRow, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    profile_row = db.get(ProfileRow, session_id)
    turns = (
        db.query(ConversationTurn)
        .filter(ConversationTurn.session_id == session_id)
        .order_by(ConversationTurn.id)
        .all()
    )
    return {
        "session_id": session_id,
        "consent_given": row.consent_given,
        "profile": profile_row.fields if profile_row else {},
        "turns": [{"role": t.role, "text": t.text} for t in turns],
    }


@router.delete("/session/{session_id}", response_model=DeleteResponse)
def delete_my_data(session_id: str, db: DbSession = Depends(get_db)) -> DeleteResponse:
    """'Delete my data' — erases turns, profile and session. Privacy by design."""
    deleted_something = False
    turns = db.query(ConversationTurn).filter(ConversationTurn.session_id == session_id)
    deleted_something |= turns.count() > 0
    turns.delete(synchronize_session=False)

    profile_row = db.get(ProfileRow, session_id)
    if profile_row:
        deleted_something = True
        db.delete(profile_row)

    session_row = db.get(SessionRow, session_id)
    if session_row:
        deleted_something = True
        db.delete(session_row)

    db.commit()
    return DeleteResponse(
        deleted=True,
        detail="आपकी सारी जानकारी मिटा दी गई है। / All your data has been deleted."
        if deleted_something
        else "कोई जानकारी नहीं मिली। / No data found for this session.",
    )
