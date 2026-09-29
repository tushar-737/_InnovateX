"""
Anthropic Claude adapter for the conversational brain.

* API key lives in .env on the BACKEND only — never exposed to the frontend.
* Every call is wrapped: on any failure we return None and the rule-based
  dialogue engine takes over, so the demo never breaks (friendly fallback).
* The LLM must return structured JSON each turn:
  {reply_text, reply_text_en, extracted_fields, missing_fields, is_complete}
"""

from __future__ import annotations

import json
import re
import logging
from typing import Optional

from ..config import get_settings
from ..schemas import PROFILE_FIELDS, Profile

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are "Kaushal Saathi" (कौशल साथी), a warm, patient voice assistant helping an Indian beneficiary — often with low literacy — build a simple profile for skilling and livelihood guidance under PM-AJAY (MoSJE). You speak simple Hindi (Hinglish is fine; avoid bureaucratic words).

RULES OF CONVERSATION
1. Ask exactly ONE short, friendly question per turn. Never ask two questions together.
2. Be empathetic and human. Use simple words like "kaam", "padhai", "shehar/zila", "karna hai". No jargon, no form-speak.
3. Handle vague, off-topic, mixed Hindi-English answers gracefully: gently acknowledge and re-ask the same question with a tiny example.
4. If the user says something emotional or a problem ("beemar hoon", "kuch nahi milta"), acknowledge with one warm sentence first, then re-ask.
5. Never invent scheme eligibility, salaries, or placement promises. You may only mention that government schemes exist and will be shown as "pointers to verify".
6. Keep each reply under 30 words so it can be spoken aloud comfortably.
7. Reply in Hindi (Devanagari or romanised). reply_text_en is an English translation for display.

PROFILE FIELDS TO FILL (in this order)
name (optional), age, district, education (none/grade5/grade8/grade10/grade12/iti/diploma/graduate), family_occupation, current_livelihood, skills (list of lowercase tags like 'sewing','farming','cooking'), interests (same tag style), constraints (text), preference (self_employment | wage_job | either), mobility ('willing' if they can travel/relocate for training, 'limited' if not).

SKILL/INTEREST TAG VOCABULARY (use these exact lowercase tags when possible):
farming, dairy, poultry, tractor, driving, cooking, bakery, food_processing, sewing, tailoring, embroidery, weaving, mason, construction, painting, plumbing, electrical, solar, repair, appliance_repair, mobile_repair, electronics_repair, computer, data_entry, marketing, retail, sales, warehouse, healthcare, patient_care, community_health, beauty, hair, spa, housekeeping, food_service, waste_management, machine_operation, hygiene

OUTPUT — return ONLY this JSON, no markdown fences:
{
 "reply_text": "…Hindi reply + your one question…",
 "reply_text_en": "…English translation…",
 "extracted_fields": { "field": value, ... },     // only fields clearly stated this turn
 "missing_fields": ["age", "district", ...],      // fields still missing after this turn
 "is_complete": false                              // true when everything except name is filled
}

When is_complete becomes true, reply_text should be a short warm wrap-up ("Bahut shukriya! ...") and the frontend will show the confirmation read-back next."""


class LLMClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None
        if self.settings.anthropic_api_key:
            try:
                import anthropic

                self._client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
            except Exception:  # pragma: no cover - import/config issues
                logger.warning("anthropic SDK unavailable; falling back to rules")
                self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def generate_turn(
        self,
        profile: Profile,
        user_text: str,
        history: list[dict],
        current_question_field: Optional[str],
    ) -> Optional[dict]:
        """Return the parsed JSON contract dict, or None on any failure."""
        if not self.available:
            return None
        convo_lines = "\n".join(f"{m['role']}: {m['text']}" for m in history[-10:])
        prompt = (
            f"Current profile state (JSON): {json.dumps(profile.as_field_dict(), ensure_ascii=False)}\n"
            f"Field you should ask about next (if any): {current_question_field or 'none — profile complete'}\n"
            f"Recent conversation:\n{convo_lines}\n"
            f"user: {user_text}\n\n"
            "Return ONLY the JSON object described in the system prompt."
        )
        try:
            response = self._client.messages.create(  # type: ignore[union-attr]
                model=self.settings.anthropic_model,
                max_tokens=self.settings.llm_max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text if response.content else ""
            return parse_json_block(text)
        except Exception as exc:  # noqa: BLE001 — any LLM failure falls back to rules
            logger.warning("LLM call failed, using rules fallback: %s", exc)
            return None


def parse_json_block(text: str) -> Optional[dict]:
    """Robustly parse the JSON contract out of a model reply (fences, chatter)."""
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    # Fast path
    try:
        data = json.loads(cleaned)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    # Balanced-brace scan for the first object
    start = cleaned.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(cleaned)):
            ch = cleaned[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        data = json.loads(cleaned[start : i + 1])
                        return data if isinstance(data, dict) else None
                    except json.JSONDecodeError:
                        break
        start = cleaned.find("{", start + 1)
    return None


def merge_extracted(llm_fields: dict, parser_fields: dict) -> dict:
    """LLM values win; the deterministic parser fills anything the LLM missed."""
    merged = dict(parser_fields)
    for key, value in (llm_fields or {}).items():
        if key not in PROFILE_FIELDS:
            continue
        if value in (None, "", [], "unknown"):
            continue
        merged[key] = value
    return merged
