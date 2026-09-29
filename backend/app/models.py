"""ORM tables. Only what is needed is stored; everything is deletable per session."""

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_audio: Mapped[bool] = mapped_column(Boolean, default=False)  # consent read aloud
    locale: Mapped[str] = mapped_column(String(16), default="hi-IN")


class Profile(Base):
    __tablename__ = "profiles"

    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id"), primary_key=True
    )
    # Structured profile as JSON — portable to PostgreSQL JSONB later.
    fields: Mapped[dict] = mapped_column(JSON, default=dict)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class ConversationTurn(Base):
    __tablename__ = "conversation_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # "user" | "assistant"
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
