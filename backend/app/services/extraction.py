"""
Deterministic profile extraction parser for Hindi / Hinglish / English answers.

Pure functions — no I/O, no LLM. Unit-tested in backend/tests/test_extraction.py.
Used BOTH as the fallback dialogue brain AND as a safety-net merge alongside the
LLM's extracted_fields, so the demo behaves consistently even without an API key.

Design notes
------------
* Romanised Hindi is matched with word-boundary regexes; Devanagari with substring.
* Canonical tags (e.g. 'sewing', 'farming') are shared with seed_data role
  `skill_tags`, so the recommender can compare profiles to roles without an LLM.
* `context_field` lets the caller say which question is being answered, so a bare
  number like "25" is read as age only when age was the question.
"""

from __future__ import annotations

import re
from typing import Optional

# Canonical tag -> match patterns. ASCII patterns use word boundaries;
# non-ASCII (Devanagari) patterns use substring matching.
TAG_KEYWORDS: dict[str, list[str]] = {
    "farming": ["farming", "farm", "kheti", "khet", "kisan", "agriculture", "agri", "crop", "fasal", "खेती", "किसान", "कृषि", "फसल"],
    "dairy": ["dairy", "doodh", "milk", "cattle", "pashu", "gai", "bhains", "buffalo", "दूध", "पशु", "गाय", "भैंस"],
    "poultry": ["poultry", "murgi", "murga", "hen", "chicken", "मुर्गी", "मुर्गा"],
    "tractor": ["tractor", "ट्रैक्टर", "trolley"],
    "driving": ["driving", "driver", "chala sakta", "gaadi chal", "gadi chal", "vehicle", "truck", "tempo", "ड्राइवर", "गाड़ी"],
    "cooking": ["cooking", "cook", "khana bana", "bawarchi", "rasoi", "kitchen", "chef", "roti", "रसोई", "रसोइया", "खाना", "रोटी"],
    "bakery": ["bakery", "baking", "cake", "bread", "बेकरी", "बिस्कुट"],
    "food_processing": ["food processing", "food processing", "packaging", "pickle", "papad", "achaar", "masala", "spice", "अचार", "पापड़", "मसाला", "खाद्य"],
    "sewing": ["silai", "silaai", "sewing", "stitching", "stitch", "silai machine", "सिलाई", "सिलई"],
    "tailoring": ["tailor", "tailoring", "darzi", "jama", "kapda", "kapdo", "kapde", "वस्त्र", "दर्जी", "कपड़", "कपड़ो", "कपड़े"],
    "embroidery": ["embroidery", "kadh", "kadhai", "chikankari", "zardozi", "कढ़ाई", "चिकनकारी"],
    "weaving": ["weaving", "bunai", "handloom", "tant", "katai", "बुनाई", "हथकरघा", "करघा"],
    "mason": ["mason", "mistri", "rajmistri", "eet", "brick", "plaster", "गारा", "राजमिस्त्री", "इंट", "प्लास्टर"],
    "construction": ["construction", "nirman", "building", "load", "majdoori", "mazdoori", "labour", "labor", "निर्माण", "मजदूरी", "मज़दूरी"],
    "painting": ["painting", "paint", "rang", "रंगाई", "पेंट"],
    "plumbing": ["plumbing", "plumber", "nal", "pipeline", "tanki", "प्लंबर", "नल", "पाइप", "टंकी"],
    "electrical": ["electrical", "electrician", "bijli", "wiring", "inverter", "बिजली", "वायरिंग", "इलेक्ट्रिशियन"],
    "solar": ["solar", "panel", "saur", "सोलर", "सौर"],
    "repair": ["repair", "marammat", "fixing", "servicing", "maintenance", "मरम्मत", "सुधार"],
    "appliance_repair": ["fridge", "cooler", "pankha", "fan repair", "mixer", "grinder", "washing machine", "घरेलू उपकरण", "पंखा", "फ्रिज", "कूलर"],
    "mobile_repair": ["mobile repair", "phone repair", "mobile", "smartphone", "मोबाइल"],
    "electronics_repair": ["electronics", "tv repair", "radio", "circuit", "soldering", "solder", "इलेक्ट्रॉनिक", "टीवी", "सोल्डरिंग"],
    "computer": ["computer", "laptop", "typing", "keyboard", "कंप्यूटर", "लैपटॉप", "टाइपिंग"],
    "data_entry": ["data entry", "data", "excel", "office", "ऑफिस", "डेटा"],
    "marketing": ["marketing", "digital", "social media", "online", "promotion", "बिक्री", "मार्केटिंग"],
    "retail": ["retail", "dukan", "shop", "shopkeeping", "kirana", "store", "दुकान", "किराना", "स्टोर"],
    "sales": ["sales", "selling", "bech", "vikri", "बेचना", "बिक्री", "विक्री"],
    "warehouse": ["warehouse", "godown", "loading", "packing", "stock", "गोदाम", "पैकिंग"],
    "healthcare": ["health", "hospital", "nursing", "swasthya", "aspatal", "अस्पताल", "स्वास्थ्य", "नर्स"],
    "patient_care": ["care", "caretaker", "sewa", "dekhbhal", "patient", "budhe", "old age", "बुजुर्ग", "सेवा", "देखभाल", "मरीज"],
    "community_health": ["asha", "anganwadi", "community", "samuday", "सामुदायिक", "आंगनवाड़ी"],
    "first_aid": ["first aid", "emergency", "prathmik", "प्राथमिक उपचार"],
    "yoga": ["yoga", "yog", "प्राणायाम", "योग"],
    "beauty": ["beauty", "makeup", "make up", "parlor", "parlour", "salon", "skin", "ब्यूटी", "पार्लर", "सैलून", "मेकअप"],
    "hair": ["hair", "baal", "cutting", "haircut", "barber", "nai", "hajam", "बाल", "नाई", "हज्जाम"],
    "spa": ["spa", "massage", "malish", "मालिश", "स्पा"],
    "housekeeping": ["housekeeping", "cleaning", "safai", "jhadu", "झाड़ू", "सफाई", "घर साफ"],
    "food_service": ["serving", "waiter", "steward", "restaurant", "hotel", "dhaba", "सर्विस", "होटल", "ढाबा", "रेस्टोरेंट"],
    "waste_management": ["waste", "kachra", "garbage", "recycling", "recycle", "compost", "कचरा", "रीसायकल"],
    "machine_operation": ["machine", "machinery", "machine operation", "मशीन"],
    "hygiene": ["hygiene", "safai", "sanitation", "swachh", "स्वच्छ", "सफाई"],
}

# Tags that read naturally as "skills I already have".
SKILL_CUE_RE = re.compile(
    r"\b(aata|aati|aate|sakta|sakti|karta|karti|karta hoon|karti hoon|jaanta|jaanti|"
    r"kar leta|kar leti|kaam aata|skill|know|can do|able to)\b|आता|आती|सकता|सकती|करता|जानता|जानती", re.I
)
INTEREST_CUE_RE = re.compile(
    r"\b(pasand|pasand hai|chahta|chahti|chahunga|chahungi|interest|like|love|wish|"
    r"man hai|karna hai|karna chahta|karna chahti)\b|पसंद|चाहता|चाहती|करना चाहता|करना चाहती|रुचि", re.I
)

AGE_RES = [
    re.compile(r"\b(\d{1,3})\s*(?:saal|sall|sal|saal ka|saal ki|years|year|varsh|umar)\b", re.I),
    re.compile(r"\b(?:umar|age)\b\s*(?:hai|is|:)?\s*(\d{1,3})", re.I),
    re.compile(r"(उम्र|साल|वर्ष)\s*(है|:)?\s*(\d{1,3})"),
    re.compile(r"(\d{1,3})\s*(साल|वर्ष|उम्र)"),
]
BARE_NUMBER_RE = re.compile(r"\b(\d{1,3})\b")

# Hindi number words (Web Speech hi-IN returns Devanagari — "तीस साल", not "30 saal").
NUM_WORDS: dict[str, int] = {
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पाँच": 5, "पांच": 5, "छह": 6, "छः": 6,
    "सात": 7, "आठ": 8, "नौ": 9, "दस": 10, "ग्यारह": 11, "बारह": 12, "तेरह": 13,
    "चौदह": 14, "पंद्रह": 15, "सोलह": 16, "सत्रह": 17, "अठारह": 18, "उन्नीस": 19,
    "बीस": 20, "इक्कीस": 21, "बाईस": 22, "तेईस": 23, "चौबीस": 24,
    "पच्चीस": 25, "छब्बीस": 26, "सत्ताईस": 27, "अट्ठाईस": 28, "उनतीस": 29,
    "तीस": 30, "इकतीस": 31, "बत्तीस": 32, "तैंतीस": 33, "तिरालीस": 33,
    "चौंतीस": 34, "पैंतीस": 35, "छत्तीस": 36, "सैंतीस": 37, "अड़तीस": 38,
    "उनतालीस": 39, "चालीस": 40, "इकतालीस": 41, "बयालीस": 42, "तैंतालीस": 43,
    "चवालीस": 44, "पैंतालीस": 45, "छियालीस": 46, "सैंतालीस": 47, "अड़तालीस": 48,
    "उनचास": 49, "पचास": 50, "इक्यावन": 51, "बावन": 52, "तिरपन": 53, "चौवन": 54,
    "पचपन": 55, "छप्पन": 56, "सत्तावन": 57, "अट्ठावन": 58, "उनसठ": 59,
    "साठ": 60, "इकसठ": 61, "बासठ": 62, "तिरसठ": 63, "चौंसठ": 64, "पैंसठ": 65,
    "छियासठ": 66, "सड़सठ": 67, "अड़सठ": 68, "उनहत्तर": 69, "सत्तर": 70,
    "इकहत्तर": 71, "बहत्तर": 72, "तिहत्तर": 73, "चौहत्तर": 74, "पचहत्तर": 75,
    "छिहत्तर": 76, "सतहत्तर": 77, "अठहत्तर": 78, "उन्यासी": 79, "अस्सी": 80,
    "इक्यासी": 81, "बयासी": 82, "तिरासी": 83, "चौरासी": 84, "पचासी": 85,
    "छियासी": 86, "सत्तासी": 87, "अट्ठासी": 88, "नवासी": 89, "नब्बे": 90,
    "इक्यानवे": 91, "बानवे": 92, "तिरानवे": 93, "चौरानवे": 94, "पंचानवे": 95,
    "छियानवे": 96, "सत्तानवे": 97, "अट्ठानवे": 98, "निन्यानवे": 99,
    # common romanisations
    "das": 10, "barah": 12, "pandrah": 15, "bees": 20, "pachees": 25, "tees": 30,
    "paintees": 35, "chalis": 40, "paintalis": 45, "pachas": 50, "pachpan": 55,
    "saath": 60, "sattar": 70, "assi": 80, "nabbe": 90,
}
# Longest word first so "पच्चीस" wins over "पाँच"-type prefixes.
_NUM_WORDS_SORTED = sorted(NUM_WORDS.items(), key=lambda kv: len(kv[0]), reverse=True)
AGE_UNIT_RE = re.compile(r"(साल|वर्ष|उम्र|saal|sall|sal|years|year|varsh|umar)", re.I)


def extract_age_words(text: str, context_field: Optional[str] = None) -> Optional[int]:
    """Age from Hindi number words: 'तीस साल', 'pachees saal', bare 'तीस' when asked."""
    t = text.lower()
    # Prefer a number word sitting next to an age unit.
    for word, value in _NUM_WORDS_SORTED:
        idx = t.find(word)
        while idx != -1:
            tail = t[idx + len(word): idx + len(word) + 8]
            if AGE_UNIT_RE.search(tail):
                return value
            idx = t.find(word, idx + 1)
    if context_field == "age":
        for word, value in _NUM_WORDS_SORTED:
            if re.search(r"(?:^|[\s,\.])" + re.escape(word) + r"(?:[\s,\.]|$)", t):
                return value
    return None

EDUCATION_PATTERNS: list[tuple[str, list[str]]] = [
    ("graduate", ["graduate", "graduation", "snatak", "स्नातक", "b.a", "b.sc", "b.com", "b.tech", "bachelor", "college kiya", "post graduate", "m.a", "m.sc", "pg kiya", "pg "]),
    ("diploma", ["diploma", "polytechnic", "डिप्लोमा", "पॉलिटेक्निक"]),
    ("iti", ["iti", "आईटीआई", "i.t.i", "iti kiya", "iti pass"]),
    ("grade12", ["12th", "12 vi", "12 pass", "barahvi", "barvi", "intermediate", "inter kiya", "plus two", "बारहवीं", "12वीं", "इंटर"]),
    ("grade10", ["10th", "10 vi", "10 pass", "dasvi", "matric", "high school", "दसवीं", "10वीं", "मैट्रिक"]),
    ("grade8", ["8th", "8 vi", "8 pass", "aathvi", "eight", "आठवीं", "8वीं"]),
    ("grade5", ["5th", "5 vi", "5 pass", "paanchvi", "panchvi", "primary", "पांचवी", "पाँचवी", "5वीं", "प्राइमरी"]),
    ("none", ["anpadh", "अनपढ़", "bina padhe", "nahi padha", "no school", "no education", "koi padhai nahi", "koi padhaai nahi", "zero", "never went"]),
]

PREFERENCE_SELF = ["apna kaam", "apna business", "apna dukan", "apni dukan", "khud ka kaam", "khud ka business", "self employment", "swayam", "dhandha", "dhanda", "karobar", "udyog", "business khol", "khud karna", "apna karna", "खुद का", "अपना काम", "अपना व्यापार", "अपनी दुकान", "धंधा", "कारोबार", "उद्योग", "दुकान"]
PREFERENCE_WAGE = ["naukri", "nokri", "job", "salary", "pagaar", "pagar", "wage", "mazdoori", "majdoori", "kahin kaam", "private naukri", "company mein", "नौकरी", "पगार", "वेतन", "मजदूरी", "मज़दूरी"]

MOBILITY_LIMITED = [
    # Travel/relocation unwillingness only — physical problems belong in 'constraints'.
    "door nahi", "nahi ja sak", "nahi ja sakti", "ghar ke aas", "ghar ke pas", "ghar ke paas",
    "nazdik", "nazdeek", "paas mein", "pas mein", "sirf paas", "dur nahi",
    "नज़दीक", "पास में", "दूर नहीं", "घर के पास", "घर के आस", "नहीं जा सकत",
]
PHYSICAL_CONSTRAINT = [
    "wheelchair", "व्हीलचेयर", "chal nahi", "chalne me dikkat", "chalne mein dikkat",
    "chala nahi", "divyang", "विकलांग", "bimari", "बीमारी", "बीमार", "kamzor",
    "ghutne", "ghutno", "kamar", "peeth", "dard", "pain", "भारी काम नहीं",
    "घुटन", "कमर", "पीठ", "दर्द", "थकान",
]
MOBILITY_WILLING = ["ja sakta", "ja sakti", "chal sakta", "chal sakti", "travel", "relocate", "shift ho", "door bhi", "koi dikkat nahi", "kahin bhi", "anywhere", "ready hoon", "kilometer", "kilometre", "km", "तैयार", "जा सकता", "जा सकती", "कोई दिक्कत नहीं", "किलोमीटर"]

CONSTRAINT_CUE = ["dikkat", "dikat", "pareshani", "problem", "bimari", "बीमार", "दिक्कत", "परेशानी", "challenges", "cannot", "nahi kar sak", "nahi kar sakti", "pain", "dard", "दर्द"]

NAME_PATTERNS = [
    re.compile(r"(?:mera|meri|my)\s+(?:naam|name)\s+(?:hai|is|:)?\s+([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s]{1,28}?)\s*(?:hai|hoon|hun|hu|he|is|हूं|हूँ|है)?\s*$", re.I),
    re.compile(r"\b(?:main|mai|i am|i'm)\s+([A-Z][a-z]{1,20})\s+(?:hoon|hun|hu|हूं|हूँ)\b"),
    re.compile(r"\bnaam\s+([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s]{1,28}?)\s+(?:hai|he|है)\b", re.I),
    re.compile(r"मेरा\s+नाम\s+([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s]{1,28}?)\s+(है|हूं|हूँ)"),
]

SKIP_WORDS = {"skip", "aage", "aage badho", "aage badhe", "naam nahi", "nahi batana", "nhi", "na", "no", "don't want", "dont want", "koi zarurat nahi", "मत पूछो", "आगे", "नाम नहीं"}
NEGATIVE_WORDS = {"nahi", "nhi", "no", "nah", "pata nahi", "nahi pata", "nahi malum", "kuch nahi", "koi nahi", "nahi hai", "nothing", "dont know", "don't know", "मालूम नहीं", "पता नहीं", "नहीं", "कुछ नहीं"}
GREETING_WORDS = {"hello", "hi", "namaste", "namaskar", "pranam", "salaam", "hey", "नमस्ते", "नमस्कार", "प्रणाम", "सलाम"}


def _contains(text_lower: str, pattern: str) -> bool:
    if re.search(r"[^\x00-\x7F]", pattern):  # Devanagari etc. — substring
        return pattern in text_lower
    if " " in pattern:  # multi-word romanised phrase — substring ("khana banana")
        return pattern.lower() in text_lower
    return re.search(r"\b" + re.escape(pattern.lower()) + r"\b", text_lower) is not None


def match_tags(text: str) -> list[str]:
    """Return canonical tags whose keywords appear in the text (stable order)."""
    t = text.lower()
    found = []
    for tag, patterns in TAG_KEYWORDS.items():
        if any(_contains(t, p) for p in patterns):
            found.append(tag)
    return found


def extract_age(text: str, context_field: Optional[str] = None) -> Optional[int]:
    for rx in AGE_RES:
        m = rx.search(text)
        if m:
            digits = [g for g in m.groups() if g and str(g).isdigit()]
            if digits:
                val = int(digits[-1])
                if 1 <= val <= 120:
                    return val
    words_age = extract_age_words(text, context_field)
    if words_age is not None:
        return words_age
    if context_field == "age":
        m = BARE_NUMBER_RE.search(text)
        if m:
            val = int(m.group(1))
            if 1 <= val <= 120:
                return val
    return None


def extract_education(text: str) -> Optional[str]:
    t = text.lower()
    for level, patterns in EDUCATION_PATTERNS:
        if any(_contains(t, p) for p in patterns):
            return level
    return None


def extract_district(text: str, districts: Optional[list[dict]] = None) -> tuple[Optional[str], Optional[str]]:
    """Return (district_name, state) using the loaded seed districts + aliases."""
    if not districts:
        return None, None
    t = text.lower()
    best = None
    for d in districts:
        candidates = [d["name"]] + list(d.get("aliases", []))
        for c in candidates:
            if _contains(t, c.lower()) or c.lower() in t:
                # Prefer the longest alias match
                if best is None or len(c) > len(best[1]):
                    best = (d, c)
    if best:
        return best[0]["name"], best[0].get("state")
    return None, None


def extract_preference(text: str) -> Optional[str]:
    t = text.lower()
    self_hit = any(p in t for p in PREFERENCE_SELF)
    # Devanagari phrasings like "अपना छोटा काम शुरू करना है" (words not adjacent):
    if not self_hit and re.search(r"(अपना|खुद)", t) and re.search(r"(काम|धंधा|दुकान|व्यापार|karobar|business|dhandha)", t):
        self_hit = True
    wage_hit = any(p in t for p in PREFERENCE_WAGE)
    if self_hit and wage_hit:
        return "either"
    if self_hit:
        return "self_employment"
    if wage_hit:
        return "wage_job"
    return None


def extract_mobility(text: str) -> tuple[Optional[str], Optional[str]]:
    """
    Return (mobility, constraints_text).

    'mobility' is TRAVEL willingness for training ('willing' | 'limited').
    Physical problems (pain, illness, disability) go to 'constraints' — the
    recommender combines them with physical_demand when scoring fit.
    """
    t = text.lower()
    travel_limited = any(p in t for p in MOBILITY_LIMITED)
    physical = any(p in t for p in PHYSICAL_CONSTRAINT)
    willing = any(p in t for p in MOBILITY_WILLING)

    mobility = None
    if travel_limited and not willing:
        mobility = "limited"
    elif willing and not travel_limited:
        mobility = "willing"
    elif travel_limited and willing:
        mobility = "limited"  # "ja sakta hoon par nazdik hi" → limited is safer

    constraints = None
    if physical or any(p in t for p in CONSTRAINT_CUE):
        # "कोई दिक्कत नहीं" means NO constraints — don't echo it as a problem.
        if any(p in t for p in ("koi dikkat nahi", "koi problem nahi", "no problem", "koi dikkat nhin", "कोई दिक्कत नहीं", "कोई परेशानी नहीं")):
            constraints = "कोई खास दिक्कत नहीं / no major constraints"
        else:
            constraints = text.strip()
    return mobility, constraints


def extract_name(text: str) -> Optional[str]:
    t = text.strip()
    for rx in NAME_PATTERNS:
        m = rx.search(t)
        if m:
            name = m.group(1).strip().title()
            if 1 < len(name) <= 30 and name.lower() not in NEGATIVE_WORDS | SKIP_WORDS:
                return name
    return None


def extract_fields(
    text: str,
    districts: Optional[list[dict]] = None,
    context_field: Optional[str] = None,
) -> dict:
    """
    Extract whatever profile fields can be found in `text`.

    Routing rules (predictable, testable):
    * Content questions (family_occupation / current_livelihood / skills /
      interests) record ONLY what was asked — nothing else.
    * All other questions use general extraction (a sentence may fill several
      fields, e.g. "gonda se hoon, 28 saal").
    * While the optional name question is live, a bare short phrase becomes the
      name only if it doesn't answer anything else.
    """
    out: dict = {}
    stripped = text.strip()
    lower = stripped.lower()
    skip_or_neg = _is_negative(lower) or is_skip(stripped)

    # ---- strict content questions -------------------------------------- #
    if context_field in ("family_occupation", "current_livelihood"):
        if not skip_or_neg:
            out[context_field] = stripped[:280]
        return out
    if context_field == "skills":
        tags = match_tags(stripped)
        if tags:
            out["skills"] = tags
        return out
    if context_field == "interests":
        tags = match_tags(stripped)
        if tags:
            out["interests"] = tags
        return out

    # ---- general extraction -------------------------------------------- #
    name = extract_name(stripped)
    if name:
        out["name"] = name

    age = extract_age(stripped, context_field)
    if age is not None:
        out["age"] = age

    district, state = extract_district(stripped, districts)
    if district:
        out["district"] = district
        out["state"] = state

    edu = extract_education(stripped)
    if edu:
        out["education"] = edu

    pref = extract_preference(stripped)
    if pref:
        out["preference"] = pref

    mobility, constraints = extract_mobility(stripped)
    if mobility:
        out["mobility"] = mobility
    if constraints:
        out["constraints"] = constraints[:280]

    if context_field not in ("name",):
        tags = match_tags(stripped)
        if tags and not out.get("family_occupation"):
            if SKILL_CUE_RE.search(stripped):
                out["skills"] = tags
            elif INTEREST_CUE_RE.search(stripped):
                out["interests"] = tags
            elif context_field not in ("constraints", "mobility", "age", "district", "education", "preference"):
                out["family_occupation"] = stripped[:280]

    # Bare-name fallback while the name question is live.
    if context_field == "name" and not out and not skip_or_neg:
        words = stripped.split()
        if (
            1 <= len(words) <= 3
            and not any(ch.isdigit() for ch in stripped)
            and len(stripped) <= 25
            and lower not in GREETING_WORDS
        ):
            out["name"] = stripped.title()

    return out


def is_negative(text: str) -> bool:
    return _is_negative(text.strip().lower())


def _is_negative(lower: str) -> bool:
    return lower in NEGATIVE_WORDS or any(lower.startswith(n) for n in ("nahi", "nhi", "no ", "pata nah", "नहीं", "पता नहीं", "मालूम नहीं"))


def is_greeting(text: str) -> bool:
    return text.strip().lower() in GREETING_WORDS


def is_skip(text: str) -> bool:
    lower = text.strip().lower()
    return (
        lower in SKIP_WORDS
        or lower.startswith(("skip", "aage", "आगे", "मत पूछ"))
        or "नाम नहीं" in lower
        or "नहीं बताना" in lower
    )


def is_confirmation(text: str) -> bool:
    lower = text.strip().lower()
    confirms = ["haan", "han", "yes", "sahi hai", "theek hai", "thik hai", "theek", "thik",
                "bilkul", "ok", "okay", "correct", "haan bilkul", "ha", "जी हाँ", "हाँ", "हां", "ठीक है", "सही है", "बिल्कुल"]
    return lower in confirms or any(lower.startswith(c) for c in confirms if len(c) > 3)
