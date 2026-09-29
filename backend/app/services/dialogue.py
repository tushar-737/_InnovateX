"""
Conversation engine.

Every turn:
  1. Deterministic parser extracts fields from the user's words (Hindi/Hinglish/English).
  2. If an Anthropic API key is configured, Claude is asked for the structured
     JSON turn {reply_text, extracted_fields, missing_fields, is_complete}.
  3. Parser + LLM extractions are merged (parser fills gaps), the reply falls back
     to the rule-based question flow if the LLM is unavailable or fails.
The rule-based engine is fully capable on its own — the demo works offline.
"""

from __future__ import annotations

from typing import Optional

from ..schemas import (
    PROFILE_FIELDS,
    REQUIRED_FIELDS,
    EDUCATION_LABELS,
    Preference,
    Profile,
    TurnResponse,
)
from . import extraction as ex
from .llm import LLMClient, merge_extracted

# Question order. 'name' is optional — it never blocks completion.
QUESTION_ORDER = [
    "name", "age", "district", "education", "family_occupation",
    "current_livelihood", "skills", "interests", "constraints",
    "preference", "mobility",
]

QUESTIONS_HI: dict[str, str] = {
    "name": "सबसे पहले, आपका नाम क्या है? (अगर नहीं बताना है तो 'आगे बढ़ें' कह दीजिए)",
    "age": "आपकी उम्र कितनी है?",
    "district": "आप किस ज़िले से हैं?",
    "education": "आपने कितनी पढ़ाई की है? जैसे आठवीं, दसवीं, बारहवीं, या ग्रेजुएट।",
    "family_occupation": "आपके घर में लोग क्या काम करते हैं? जैसे खेती, मज़दूरी, सिलाई।",
    "current_livelihood": "अभी आप क्या काम करते हैं?",
    "skills": "आपको कौन-कौन से काम आते हैं? जैसे खाना बनाना, सिलाई, ट्रैक्टर चलाना।",
    "interests": "आप किस तरह का काम करना पसंद करेंगे?",
    "constraints": "कोई दिक्कत है जो हमें ध्यान में रखनी चाहिए? जैसे चलने-फिरने की दिक्कत, या बीमारी।",
    "preference": "आप अपना काम/धंधा शुरू करना चाहते हैं, या नौकरी करना चाहते हैं?",
    "mobility": "ट्रेनिंग के लिए थोड़ा दूर जा सकते हैं? जैसे 10-20 किलोमीटर?",
}

QUESTIONS_EN: dict[str, str] = {
    "name": "First, may I know your name? (You can say 'skip'.)",
    "age": "How old are you?",
    "district": "Which district are you from?",
    "education": "How much schooling have you completed? For example 8th, 10th, 12th or graduate.",
    "family_occupation": "What work do people in your family do? For example farming, labour, sewing.",
    "current_livelihood": "What work do you do right now?",
    "skills": "Which kinds of work do you already know? For example cooking, sewing, driving a tractor.",
    "interests": "What kind of work would you like to do?",
    "constraints": "Is there any difficulty we should keep in mind? For example problems with movement, or illness.",
    "preference": "Would you like to start your own work/business, or do a job?",
    "mobility": "Can you travel a little for training? For example 10–20 km?",
}

TAP_OPTIONS: dict[str, list[str]] = {
    "name": ["आगे बढ़ें (नाम नहीं बताना)", "राहुल", "सुनीता"],
    "age": ["22 साल", "30 साल", "40 साल", "50 साल"],
    "district": ["गोंडा", "बाड़मेर", "अलीराजपुर"],
    "education": ["8वीं तक", "10वीं तक", "12वीं तक", "ग्रेजुएट"],
    "family_occupation": ["खेती", "मज़दूरी", "सिलाई", "दुकान"],
    "current_livelihood": ["खेती करता हूँ", "मज़दूरी करता हूँ", "घर का काम", "अभी कुछ नहीं"],
    "skills": ["सिलाई", "खाना बनाना", "ट्रैक्टर चलाना", "बिजली का काम"],
    "interests": ["खेती", "सिलाई", "खाना बनाना", "मोबाइल रिपेयर"],
    "constraints": ["कोई दिक्कत नहीं", "चलने में दिक्कत", "घुटनों में दर्द"],
    "preference": ["अपना काम करना है", "नौकरी करनी है", "दोनों चलेगा"],
    "mobility": ["हाँ, जा सकता हूँ", "सिर्फ पास में", "घर से दूर नहीं"],
}

GREETING_HI = (
    "नमस्ते! मैं कौशल साथी हूँ। मैं आपसे कुछ आसान सवाल पूछूँगा ताकि आपके लिए सही कौशल "
    "प्रशिक्षण और काम के रास्ते बता सकूँ।"
)
GREETING_EN = "Hello! I am Kaushal Saathi. I will ask a few easy questions so I can suggest the right skilling and livelihood options for you."

OFFTOPIC_REASK_HI = "कोई बात नहीं, आराम से बताइए। "
TOO_YOUNG_HI = "माफ़ कीजिए, यह सेवा 14 साल से बड़े लोगों के लिए है। आप किसी बड़े परिवार के सदस्य की मदद ले सकते हैं।"

EXAMPLES_HI = {
    "age": "जैसे — '25 साल'।",
    "district": "जैसे — 'गोंडा' या 'बाड़मेर'।",
    "current_livelihood": "जैसे — 'मैं मज़दूरी करता हूँ'।",
    "name": "",
    "education": "",
    "family_occupation": "",
    "skills": "",
    "interests": "",
    "constraints": "",
    "preference": "",
    "mobility": "",
}


def next_question_field(profile: Profile) -> Optional[str]:
    missing = profile.missing_fields()
    for field in QUESTION_ORDER:
        if field == "name":
            # Optional: ask once at the start, never block completion.
            if profile.name is None and "name" not in profile.skipped_fields:
                return "name"
            continue
        if field in missing:
            return field
    return None


def _field_value_label(field: str, value) -> str:
    if field == "education" and value:
        return EDUCATION_LABELS.get(str(getattr(value, "value", value)), str(value))
    if field == "preference" and value:
        labels = {
            "self_employment": "अपना काम/धंधा",
            "wage_job": "नौकरी",
            "either": "नौकरी या अपना काम — दोनों चलेंगे",
        }
        return labels.get(str(getattr(value, "value", value)), str(value))
    if field == "mobility" and value:
        labels = {"willing": "थोड़ा दूर जाने को तैयार", "limited": "ज़्यादा दूर जाना मुश्किल"}
        return labels.get(str(value), str(value))
    if field in ("skills", "interests") and value:
        return ", ".join(value)
    return str(value)


def build_readback(profile: Profile) -> tuple[str, str]:
    """Voice read-back: 'Aapne bataya ki...' + English mirror."""
    parts_hi, parts_en = [], []
    mapping = {
        "name": ("आपका नाम", "your name"),
        "age": ("आपकी उम्र", "your age"),
        "district": ("आपका ज़िला", "your district"),
        "education": ("आपकी पढ़ाई", "your education"),
        "family_occupation": ("घर का काम", "family occupation"),
        "current_livelihood": ("अभी का काम", "current work"),
        "skills": ("आपको यह काम आते हैं", "your skills"),
        "interests": ("आपकी रुचि", "your interests"),
        "constraints": ("आपकी दिक्कत", "your constraints"),
        "preference": ("आपकी पसंद", "your preference"),
        "mobility": ("यात्रा", "travel"),
    }
    for field in QUESTION_ORDER:
        value = getattr(profile, field, None)
        if value in (None, "", [], Preference.unknown, "unknown"):
            continue
        hi_label, en_label = mapping[field]
        pretty = _field_value_label(field, value)
        parts_hi.append(f"{hi_label} {pretty}")
        parts_en.append(f"{en_label}: {pretty}")
    readback_hi = "आपने बताया कि " + ", ".join(parts_hi) + ". क्या यह सही है?"
    readback_en = "You shared: " + "; ".join(parts_en) + ". Is this correct?"
    return readback_hi, readback_en


class DialogueEngine:
    def __init__(self, llm: Optional[LLMClient] = None, districts: Optional[list[dict]] = None):
        self.llm = llm or LLMClient()
        from .seed_loader import load_districts

        self.districts = districts if districts is not None else load_districts()

    # ------------------------------------------------------------------ #

    def greeting(self) -> TurnResponse:
        return TurnResponse(
            reply_text=f"{GREETING_HI} {QUESTIONS_HI['name']}",
            reply_text_en=f"{GREETING_EN} {QUESTIONS_EN['name']}",
            extracted_fields={},
            missing_fields=[],  # filled by caller with actual missing
            is_complete=False,
            current_question_field="name",
            tap_options=TAP_OPTIONS["name"],
            engine="rules",
        )

    def turn(self, profile: Profile, user_text: str, history: list[dict]) -> TurnResponse:
        current_field = next_question_field(profile)
        effective_field = current_field  # the question currently being asked

        parser_fields = ex.extract_fields(user_text, self.districts, context_field=effective_field)
        self._apply_skip_and_specials(profile, user_text, parser_fields, effective_field)

        llm_result = None
        engine_used = "rules"
        warning = None
        if self.llm.available:
            llm_result = self.llm.generate_turn(profile, user_text, history, effective_field)
            if llm_result is not None:
                engine_used = "llm+rules"
            else:
                warning = "AI ब्रेन अभी उपलब्ध नहीं है — सरल ऑफ़लाइन मोड में बातचीत चल रही है।"

        extracted = merge_extracted(
            (llm_result or {}).get("extracted_fields", {}), parser_fields
        )
        self._validate_and_apply(profile, extracted, effective_field)

        # Graceful jump-ahead: while the optional name question is live, a real
        # answer to any other question means the user is skipping the name.
        if (
            effective_field == "name"
            and profile.name is None
            and "name" not in profile.skipped_fields
            and any(k in extracted for k in REQUIRED_FIELDS)
        ):
            profile.skipped_fields.append("name")

        missing = profile.missing_fields()
        is_complete = profile.is_complete()

        if llm_result and isinstance(llm_result.get("reply_text"), str) and llm_result["reply_text"].strip():
            reply_hi = llm_result["reply_text"].strip()
            reply_en = (llm_result.get("reply_text_en") or "").strip()
        else:
            reply_hi, reply_en = self._rule_reply(profile, user_text, extracted, effective_field)

        next_field = next_question_field(profile)
        ask_field = next_field if next_field else "name"
        return TurnResponse(
            reply_text=reply_hi,
            reply_text_en=reply_en,
            extracted_fields=extracted,
            missing_fields=missing,
            is_complete=is_complete,
            current_question_field=None if is_complete else next_field,
            tap_options=TAP_OPTIONS.get(ask_field, []),
            engine=engine_used,
            warning=warning,
        )

    # ------------------------------------------------------------------ #

    def _apply_skip_and_specials(self, profile: Profile, user_text: str, parser_fields: dict, current_field) -> None:
        if ex.is_skip(user_text):
            if current_field == "name":
                profile.name = None
                if "name" not in profile.skipped_fields:
                    profile.skipped_fields.append("name")
                parser_fields.pop("name", None)
            elif current_field:
                if current_field not in profile.skipped_fields:
                    profile.skipped_fields.append(current_field)

    def _validate_and_apply(self, profile: Profile, extracted: dict, current_field) -> None:
        allowed = set(PROFILE_FIELDS) | {"state"}  # state travels with district
        updates = {}
        for key in allowed:
            if key in extracted and extracted[key] not in (None, "", []):
                updates[key] = extracted[key]
        # Age sanity: this service is for adults; politely reject very low ages.
        if "age" in updates and isinstance(updates["age"], int) and updates["age"] < 14:
            updates.pop("age", None)
            updates["_too_young"] = True
        self._too_young = updates.pop("_too_young", False)

        merged = profile.model_dump()
        for key, value in updates.items():
            if key in ("skills", "interests"):
                existing = merged.get(key) or []
                for tag in value:
                    if tag not in existing:
                        existing.append(tag)
                merged[key] = existing
            elif key == "preference":
                merged[key] = Preference(value) if not isinstance(value, Preference) else value
            else:
                merged[key] = value
        new_profile = Profile(**merged)
        profile.__dict__.update(new_profile.__dict__)

    def _rule_reply(self, profile: Profile, user_text: str, extracted: dict, current_field) -> tuple[str, str]:
        too_young = getattr(self, "_too_young", False)
        if too_young:
            return TOO_YOUNG_HI, "Sorry, this service is for people above 14 years."

        if profile.is_complete():
            return (
                "बहुत-बहुत शुक्रिया! मुझे सारी जानकारी मिल गई है। अब मैं आपको आपकी जानकारी दोबारा पढ़कर सुनाता हूँ।",
                "Thank you so much! I have everything. Now I will read your information back to you.",
            )

        if ex.is_greeting(user_text):
            return (
                f"नमस्ते! चलिए शुरू करते हैं। {QUESTIONS_HI.get(current_field or 'name', QUESTIONS_HI['name'])}",
                f"Hello! Let's begin. {QUESTIONS_EN.get(current_field or 'name', QUESTIONS_EN['name'])}",
            )

        # Skip handling — optional name can be skipped, required fields get a nudge.
        if ex.is_skip(user_text):
            if current_field in (None, "name"):
                next_f = next_question_field(profile)
                if next_f is None:
                    return (
                        "ठीक है, कोई बात नहीं। अब मैं आपकी जानकारी दोबारा पढ़कर सुनाता हूँ।",
                        "Alright, no problem. Now I will read your information back to you.",
                    )
                return (
                    f"ठीक है, कोई बात नहीं। {QUESTIONS_HI[next_f]}",
                    f"Alright, no problem. {QUESTIONS_EN[next_f]}",
                )
            example = EXAMPLES_HI.get(current_field, "")
            return (
                f"ठीक है, कोई बात नहीं। फिर भी यह जानकारी थोड़ी मदद करेगी। {QUESTIONS_HI[current_field]} {example}",
                f"Alright, no problem. This information still helps a little though. {QUESTIONS_EN[current_field]}",
            )

        # Did this answer actually contribute anything to the profile?
        answered = bool(extracted) and (
            current_field is None or self._answers_current(current_field, extracted)
            or any(k in extracted for k in PROFILE_FIELDS)
        )

        if not answered:
            # Vague / off-topic / negative / unparseable → warm re-ask with an example.
            if ex.is_negative(user_text) and current_field:
                return (
                    f"कोई बात नहीं। फिर भी अगर थोड़ा बता सकें तो अच्छा रहेगा। {QUESTIONS_HI[current_field]}",
                    f"No problem. Still, if you can share a little, it helps. {QUESTIONS_EN[current_field]}",
                )
            if ex.is_confirmation(user_text) and current_field:
                example = EXAMPLES_HI.get(current_field, "")
                return (
                    f"{OFFTOPIC_REASK_HI}{QUESTIONS_HI[current_field]} {example}",
                    f"No problem. {QUESTIONS_EN[current_field]}",
                )
            example = EXAMPLES_HI.get(current_field or "name", "")
            q_hi = QUESTIONS_HI.get(current_field or "name", QUESTIONS_HI["name"])
            q_en = QUESTIONS_EN.get(current_field or "name", QUESTIONS_EN["name"])
            return (
                f"{OFFTOPIC_REASK_HI}{q_hi} {example}",
                f"No problem, take your time. {q_en}",
            )

        # Something was understood → acknowledge briefly, then continue.
        ack_hi, ack_en = self._acknowledge(extracted, current_field)

        next_f = next_question_field(profile)
        if next_f is None:
            return (
                f"{ack_hi} बहुत-बहुत शुक्रिया! मुझे सारी जानकारी मिल गई है। अब मैं आपकी जानकारी दोबारा पढ़कर सुनाता हूँ।",
                f"{ack_en} Thank you so much! I have everything. Now I will read your information back to you.",
            )
        q_hi = QUESTIONS_HI[next_f]
        example = EXAMPLES_HI.get(next_f, "")
        # If the user answered something else while the current question is still
        # open, gently point back to it instead of silently moving on.
        if current_field and current_field != next_f and current_field in profile.missing_fields():
            return (
                f"{ack_hi} {q_hi} {example}",
                f"{ack_en} {QUESTIONS_EN[next_f]}",
            )
        return (
            f"{ack_hi} {q_hi} {example}",
            f"{ack_en} {QUESTIONS_EN[next_f]}",
        )

    @staticmethod
    def _acknowledge(extracted: dict, current_field) -> tuple[str, str]:
        if current_field == "age" and "age" in extracted:
            return f"जी, {extracted['age']} साल। शुक्रिया!", f"Okay, {extracted['age']} years. Thank you!"
        if "name" in extracted and current_field == "name":
            return f"जी {extracted['name']} जी, शुक्रिया!", f"Okay {extracted['name']}, thank you!"
        if "district" in extracted:
            return f"{extracted['district']} से, ठीक है। शुक्रिया!", f"From {extracted['district']}, okay. Thank you!"
        return "समझ गया, शुक्रिया!", "Understood, thank you!"

    @staticmethod
    def _answers_current(current_field: str, extracted: dict) -> bool:
        if current_field == "name":
            return "name" in extracted
        if current_field == "mobility":
            return "mobility" in extracted or "constraints" in extracted
        return current_field in extracted
