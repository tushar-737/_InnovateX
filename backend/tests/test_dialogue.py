"""
Integration test: the EXACT Devanagari demo conversation from docs/DEMO_SCRIPT.md.

Web Speech API with lang=hi-IN returns Devanagari text — this test guarantees the
full slot-filling flow works with it, end to end, on the rules engine.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas import Profile  # noqa: E402
from app.services.dialogue import DialogueEngine, build_readback, next_question_field  # noqa: E402


def run_conversation():
    engine = DialogueEngine(llm=None)  # rules engine — deterministic
    profile = Profile()
    history = []
    transcript = [
        "नमस्ते",
        "मेरा नाम सुनीता है",
        "तीस साल",
        "मैं गोंडा से हूँ",
        "दसवीं तक पढ़ी हूँ",
        "घर में सब खेती करते हैं",
        "अभी खेत में मज़दूरी करती हूँ",
        "मुझे सिलाई आती है, खाना भी बना लेती हूँ",
        "कपड़ों का काम पसंद है",
        "घुटनों में दर्द रहता है, भारी काम नहीं कर पाती",
        "मुझे अपना छोटा काम शुरू करना है",
        "हाँ, दस-बीस किलोमीटर जा सकती हूँ",
    ]
    turns = []
    for text in transcript:
        resp = engine.turn(profile, text, history)
        history.append({"role": "user", "text": text})
        history.append({"role": "assistant", "text": resp.reply_text})
        turns.append((text, resp))
    return engine, profile, turns


class TestDemoConversation:
    def test_full_flow_completes(self):
        _, profile, turns = run_conversation()
        assert profile.is_complete(), f"missing: {profile.missing_fields()}"

    def test_name_and_age(self):
        _, profile, _ = run_conversation()
        # Name is kept in the script the user spoke (Devanagari).
        assert profile.name == "सुनीता"
        assert profile.age == 30  # "तीस साल"

    def test_district_education(self):
        _, profile, _ = run_conversation()
        assert profile.district == "Gonda"
        assert profile.state == "Uttar Pradesh"
        assert profile.education.value == "grade10"

    def test_occupations_stay_in_their_slots(self):
        _, profile, _ = run_conversation()
        assert "खेती" in (profile.family_occupation or "")
        assert "मज़दूरी" in (profile.current_livelihood or "")

    def test_skills_interests(self):
        _, profile, _ = run_conversation()
        assert "sewing" in profile.skills
        assert "cooking" in profile.skills
        assert "tailoring" in profile.interests

    def test_constraints_and_preference_and_mobility(self):
        _, profile, _ = run_conversation()
        assert profile.constraints and "घुटन" in profile.constraints
        assert profile.preference.value == "self_employment"
        # Knee pain is a CONSTRAINT; travel willingness is answered separately.
        assert profile.mobility == "willing"

    def test_each_reply_is_short_hindi_with_next_question(self):
        _, _, turns = run_conversation()
        for text, resp in turns:
            assert resp.reply_text, f"no reply for {text}"
            # Keep replies speakable (spec: one short question at a time).
            assert len(resp.reply_text) < 220, f"reply too long for {text}"

    def test_readback_mentions_key_facts(self):
        _, profile, _ = run_conversation()
        hi, en = build_readback(profile)
        assert "सुनीता" in hi and "30" in hi and "Gonda" in hi
        assert "Sunita" in en or "सुनीता" in en

    def test_completion_wraps_up(self):
        _, _, turns = run_conversation()
        assert turns[-1][1].is_complete
        assert "शुक्रिया" in turns[-1][1].reply_text


class TestJumpAheadAndSkip:
    def test_skipping_name_moves_on(self):
        engine = DialogueEngine(llm=None)
        profile = Profile()
        resp = engine.turn(profile, "28 saal", [])
        assert "name" in profile.skipped_fields
        assert profile.age == 28
        assert resp.current_question_field == "district"

    def test_skip_button_at_name(self):
        engine = DialogueEngine(llm=None)
        profile = Profile()
        resp = engine.turn(profile, "आगे बढ़ें", [])
        assert "name" in profile.skipped_fields
        assert "उम्र" in resp.reply_text

    def test_offtopic_gets_gentle_reask(self):
        engine = DialogueEngine(llm=None)
        profile = Profile()
        resp = engine.turn(profile, "मौसम आज अच्छा है", [])
        assert "नाम" in resp.reply_text  # first question asked again, gently
        assert "कोई बात नहीं" in resp.reply_text

    def test_devanagari_number_words(self):
        engine = DialogueEngine(llm=None)
        profile = Profile()
        engine.turn(profile, "पैंतालीस साल", [])
        assert profile.age == 45

    def test_recommend_after_demo_flow(self):
        from app.services.recommender import RecommendationEngine

        _, profile, _ = run_conversation()
        recs = RecommendationEngine().recommend(profile)
        assert len(recs.recommendations) == 3
        sectors = [r.sector for r in recs.recommendations]
        # A sewing-loving user in Gonda should see apparel pathways in top-3.
        assert "apparel" in sectors
