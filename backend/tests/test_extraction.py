"""Unit tests for the deterministic profile-extraction parser."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.extraction import (  # noqa: E402
    extract_age,
    extract_district,
    extract_education,
    extract_fields,
    extract_mobility,
    extract_name,
    extract_preference,
    is_confirmation,
    is_negative,
    match_tags,
)


DISTRICTS = [
    {"name": "Gonda", "state": "Uttar Pradesh", "aliases": ["gonda", "गोंडा"]},
    {"name": "Barmer", "state": "Rajasthan", "aliases": ["barmer", "बाड़मेर"]},
    {"name": "Alirajpur", "state": "Madhya Pradesh", "aliases": ["alirajpur", "अलीराजपुर"]},
]


class TestAge:
    def test_hinglish_saal(self):
        assert extract_age("मैं 25 साल का हूँ") == 25

    def test_roman_saal(self):
        assert extract_age("meri umar 35 saal hai") == 35

    def test_english(self):
        assert extract_age("I am 42 years old") == 42

    def test_bare_number_needs_context(self):
        assert extract_age("25") is None
        assert extract_age("25", context_field="age") == 25

    def test_no_age(self):
        assert extract_age("hello namaste") is None


class TestEducation:
    def test_grade10(self):
        assert extract_education("maine 10th tak padhai ki hai") == "grade10"

    def test_hindi_dasvi(self):
        assert extract_education("मैंने दसवीं तक पढ़ाई की") == "grade10"

    def test_graduate(self):
        assert extract_education("main graduate hoon") == "graduate"

    def test_iti(self):
        assert extract_education("iti kiya hai") == "iti"

    def test_none(self):
        assert extract_education("main anpadh hoon") == "none"

    def test_ordering_prefers_higher(self):
        # 12th mentioned with graduate → graduate wins (checked first)
        assert extract_education("12th ke baad graduate kiya") == "graduate"


class TestDistrict:
    def test_english(self):
        name, state = extract_district("I am from Gonda", DISTRICTS)
        assert name == "Gonda" and state == "Uttar Pradesh"

    def test_devanagari(self):
        name, _ = extract_district("मैं बाड़मेर से हूँ", DISTRICTS)
        assert name == "Barmer"

    def test_unknown(self):
        assert extract_district("main Delhi se hoon", DISTRICTS) == (None, None)


class TestPreference:
    def test_self(self):
        assert extract_preference("mujhe apna dukan kholna hai") == "self_employment"

    def test_wage(self):
        assert extract_preference("mujhe naukri karni hai") == "wage_job"

    def test_both(self):
        assert extract_preference("naukri bhi chalega apna kaam bhi") == "either"

    def test_none(self):
        assert extract_preference("kuch bhi chalega") is None


class TestMobilityConstraints:
    def test_willing(self):
        mob, _ = extract_mobility("haan main door ja sakta hoon")
        assert mob == "willing"

    def test_limited(self):
        mob, _ = extract_mobility("nahi ja sakta door, ghutne mein dard hai")
        assert mob == "limited"

    def test_constraints_captured(self):
        _, constraints = extract_mobility("chalne mein dikkat hai")
        assert constraints and "dikkat" in constraints


class TestNameAndTags:
    def test_name_pattern(self):
        assert extract_name("mera naam rahul hai") == "Rahul"

    def test_tags_hinglish(self):
        assert "sewing" in match_tags("mujhe silai aati hai")
        assert "farming" in match_tags("kheti karta hoon")
        assert "cooking" in match_tags("khana banana aata hai")

    def test_tags_devanagari(self):
        assert "sewing" in match_tags("मुझे सिलाई आती है")


class TestExtractFields:
    def test_full_sentence_many_fields(self):
        out = extract_fields(
            "Mera naam Sunita hai, 32 saal ki, Gonda se, 10th tak padha, ghar mein kheti hoti hai",
            DISTRICTS,
        )
        assert out.get("name") == "Sunita"
        assert out.get("age") == 32
        assert out.get("district") == "Gonda"
        assert out.get("education") == "grade10"
        assert out.get("family_occupation")  # free text kept

    def test_context_skills_routing(self):
        out = extract_fields("silai aur khana banana", DISTRICTS, context_field="skills")
        assert set(out["skills"]) >= {"sewing", "cooking"}

    def test_context_interests_routing(self):
        out = extract_fields("mujhe mobile repair pasand hai", DISTRICTS, context_field="interests")
        assert "mobile_repair" in out.get("interests", [])

    def test_negative_answer_yields_nothing(self):
        out = extract_fields("nahi pata", DISTRICTS, context_field="age")
        assert out == {}

    def test_mixed_language(self):
        out = extract_fields("I am from अलीराजपुर, umar 28, sewing aati hai", DISTRICTS)
        assert out.get("district") == "Alirajpur"
        assert out.get("age") == 28
        assert "sewing" in out.get("skills", [])


class TestHelpers:
    def test_confirmation(self):
        assert is_confirmation("haan bilkul sahi hai")
        assert is_confirmation("हाँ")
        assert not is_confirmation("umar 26 hai")

    def test_negative(self):
        assert is_negative("nahi")
        assert is_negative("pata nahi")
        assert not is_negative("silai aati hai")
