"""
Recommendation engine — deliberately transparent, no black box.

Score (0..1) = 0.30 · similarity   (TF-IDF cosine between profile text and role text, ×2 capped at 1)
             + 0.20 · education    (1.0 eligible, 0.25 near-miss within one level, 0 otherwise)
             + 0.20 · demand       (matching district demand tags ÷ 2, capped at 1)
             + 0.15 · mobility     (0.7 · physical-fit + 0.3 · travel-fit)
             + 0.15 · preference   (self-employment potential vs stated preference)

Every component is returned in `score_breakdown` and rendered in the "why this?" panel.
Runs fully offline against seed_data/ — no internet, no LLM required.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from ..schemas import (
    EDUCATION_ORDER,
    EducationLevel,
    Preference,
    Profile,
    RecommendResponse,
    Recommendation,
    ScoreBreakdown,
    SkillGap,
    TrainingCenter,
)
from .extraction import TAG_KEYWORDS, match_tags
from .seed_loader import data_notice, district_notice, load_districts, load_roles

WEIGHTS = {"similarity": 0.30, "education": 0.20, "demand": 0.20, "mobility": 0.15, "preference": 0.15}

SECTOR_LABELS = {
    "agriculture": "कृषि / Agriculture",
    "food_processing": "खाद्य प्रसंस्करण / Food processing",
    "construction": "निर्माण / Construction",
    "plumbing": "प्लंबिंग / Plumbing",
    "electrical": "इलेक्ट्रिकल / Electrical",
    "apparel": "कपड़ा-सिलाई / Apparel",
    "healthcare": "स्वास्थ्य सहायता / Healthcare support",
    "retail": "खुदरा-गोदाम / Retail & logistics",
    "it_ites": "कंप्यूटर-आईटी / IT-ITeS",
    "automotive": "ऑटोमोटिव / Automotive",
    "beauty_wellness": "ब्यूटी-वेलनेस / Beauty & wellness",
    "hospitality": "आतिथ्य / Hospitality",
    "electronics": "इलेक्ट्रॉनिक्स / Electronics",
    "green_jobs": "ग्रीन जॉब्स / Green jobs",
}

PHYSICAL_FIT_UNCONSTRAINED = {"low": 1.0, "medium": 0.9, "high": 0.8}
PHYSICAL_FIT_CONSTRAINED = {"low": 1.0, "medium": 0.55, "high": 0.2}

PREF_FIT = {
    Preference.self_employment: {"high": 1.0, "medium": 0.6, "low": 0.25},
    Preference.wage_job: {"high": 0.6, "medium": 0.9, "low": 1.0},
    Preference.either: {"high": 1.0, "medium": 1.0, "low": 1.0},
    Preference.unknown: {"high": 0.9, "medium": 0.9, "low": 0.9},
}

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


class RecommendationEngine:
    def __init__(self, roles: list[dict] | None = None, districts: list[dict] | None = None):
        self.roles = roles if roles is not None else load_roles()
        self.districts = districts if districts is not None else load_districts()
        self._role_vectors: list[dict[str, float]] = []
        self._idf: dict[str, float] = {}
        self._build_tfidf()

    # ------------------------------------------------------------------ #
    # TF-IDF
    # ------------------------------------------------------------------ #

    @staticmethod
    def _role_document(role: dict) -> str:
        parts = [
            role["job_role"],
            role["sector"].replace("_", " "),
            " ".join(role.get("skill_tags", [])),
            " ".join(role.get("typical_local_demand_tags", [])),
            " ".join(role.get("related_family_occupations", [])),
        ]
        return " ".join(parts).lower()

    @staticmethod
    def _profile_document(profile: Profile) -> str:
        """Canonical tags + raw words from free-text answers."""
        parts: list[str] = []
        parts += profile.skills
        parts += profile.interests
        for field in (profile.family_occupation, profile.current_livelihood, profile.constraints):
            if field:
                parts += match_tags(field)  # map Hindi words → canonical tags
                parts += tokenize(field)
        if profile.district:
            parts.append(profile.district.lower())
        return " ".join(parts)

    def _build_tfidf(self) -> None:
        docs = [self._role_document(r) for r in self.roles]
        n = len(docs)
        df: Counter[str] = Counter()
        tokenized = []
        for doc in docs:
            toks = tokenize(doc)
            tokenized.append(Counter(toks))
            df.update(set(toks))
        self._idf = {t: math.log((1 + n) / (1 + c)) + 1.0 for t, c in df.items()}
        for counts in tokenized:
            vec = {t: cnt * self._idf.get(t, 1.0) for t, cnt in counts.items()}
            self._role_vectors.append(vec)

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(a[t] * b.get(t, 0.0) for t in a)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def _profile_vector(self, profile: Profile) -> dict[str, float]:
        counts = Counter(tokenize(self._profile_document(profile)))
        return {t: c * self._idf.get(t, 1.0) for t, c in counts.items()}

    # ------------------------------------------------------------------ #
    # District resolution
    # ------------------------------------------------------------------ #

    def resolve_district(self, district_name: str | None) -> dict | None:
        if not district_name:
            return None
        t = district_name.strip().lower()
        for d in self.districts:
            candidates = [d["name"], d["id"]] + list(d.get("aliases", []))
            if any(c.lower() in t or t in c.lower() for c in candidates):
                return d
        return None

    # ------------------------------------------------------------------ #
    # Scoring
    # ------------------------------------------------------------------ #

    def _education_component(self, profile: Profile, role: dict) -> tuple[float, str]:
        if profile.education is None:
            return 0.5, "पढ़ाई की जानकारी नहीं मिली / education unknown — treated neutrally"
        have = EDUCATION_ORDER[profile.education.value]
        need = EDUCATION_ORDER[role["min_education"]]
        if have >= need:
            return 1.0, "पढ़ाई की शर्त पूरी है / education requirement met"
        if have == need - 1:
            return 0.25, "एक स्तर कम पढ़ाई — ब्रिज/पूरक पाठ्यक्रम ज़रूरी हो सकता है (केंद्र से पुष्टि करें)"
        return 0.0, "पढ़ाई की शर्त पूरी नहीं होती / does not meet minimum education"

    def _demand_component(self, role: dict, district: dict | None) -> tuple[float, str]:
        if district is None:
            return 0.5, "जिले की माँग का डेटा उपलब्ध नहीं (डेमो) — treated neutrally"
        role_tags = set(role.get("typical_local_demand_tags", [])) | {role["sector"]}
        role_tags = {t for t in role_tags if not t.startswith("_")}
        district_tags = set(district.get("demand_tags", []))
        matched = sorted(role_tags & district_tags)
        score = min(1.0, len(matched) / 2.0)
        if matched:
            note = f"{district['name']} में माँग के टैग मिले: {', '.join(matched[:4])} (डेमो डेटा)"
        else:
            note = f"{district['name']} में स्थानिक माँग टैग नहीं मिले (डेमो डेटा)"
        return score, note

    def _mobility_component(self, profile: Profile, role: dict, district: dict | None) -> tuple[float, str]:
        # Physical limitation: stated in constraints (pain/illness) or travel limits.
        constraint_text = (profile.constraints or "").lower()
        physically_limited = constraint_text and not constraint_text.startswith("कोई खास दिक्कत नहीं") and any(
            k in constraint_text for k in
            ("wheelchair", "chal", "dikkat", "bimar", "dard", "kamzor", "दर्द", "दिक्कत", "बीमार", "कमज़ोर", "कमजोर", "घुटन", "पीठ", "कमर", "विकलांग", "थकान", "भारी काम नहीं")
        )
        constrained = profile.mobility == "limited" or bool(physically_limited)
        phys_key = role.get("physical_demand", "medium")
        if constrained:
            physical_fit = PHYSICAL_FIT_CONSTRAINED.get(phys_key, 0.55)
            phys_note = f"शारीरिक माँग {phys_key} — आपकी दिक्कत को ध्यान में रखा गया"
        else:
            physical_fit = PHYSICAL_FIT_UNCONSTRAINED.get(phys_key, 0.9)
            phys_note = f"शारीरिक माँग {phys_key}"

        travel_fit = 1.0
        travel_note = "यात्रा/स्थानांतरण की इच्छा के अनुकूल"
        center = self._nearest_center(role, district)
        if profile.mobility == "limited" and center and center.get("distance_km"):
            if center["distance_km"] > 15:
                travel_fit = 0.7
                travel_note = f"नज़दीकी केंद्र लगभग {center['distance_km']} किमी — आपकी सीमित यात्रा क्षमता के कारण थोड़ा कठिन"
            else:
                travel_note = f"नज़दीकी केंद्र लगभग {center['distance_km']} किमी"
        score = 0.7 * physical_fit + 0.3 * travel_fit
        return score, f"{phys_note}; {travel_note}"

    @staticmethod
    def _preference_component(profile: Profile, role: dict) -> tuple[float, str]:
        pref = profile.preference or Preference.unknown
        level = role.get("self_employment_potential", "medium")
        score = PREF_FIT.get(pref, PREF_FIT[Preference.unknown]).get(level, 0.6)
        if pref == Preference.self_employment:
            note = "आप स्वरोज़गार चाहते हैं; इस काम में खुद काम शुरू करने की संभावना " + {"high": "अच्छी", "medium": "मध्यम", "low": "कम"}.get(level, "मध्यम")
        elif pref == Preference.wage_job:
            note = "आप नौकरी चाहते हैं; यह भूमिका वेतन-रोज़गार के लिए " + {"high": "उपयुक्त है (साथ ही स्वरोज़गार भी संभव)", "medium": "उपयुक्त है", "low": "सबसे उपयुक्त है"}.get(level, "उपयुक्त है")
        else:
            note = "स्वरोज़गार/नौकरी — दोनों विकल्प खुले हैं"
        return score, note

    def _similarity_component(self, profile: Profile, role_vec: dict) -> tuple[float, str]:
        cosine = self._cosine(self._profile_vector(profile), role_vec)
        scaled = min(1.0, cosine * 2.0)  # documented scaling for readability
        return scaled, f"TF-IDF cosine={cosine:.2f} (×2 करके सीमित / scaled ×2, capped)"

    @staticmethod
    def _nearest_center(role: dict, district: dict | None) -> dict | None:
        if not district:
            return None
        centers = district.get("training_centers", [])
        if not centers:
            return None
        sector = role["sector"]
        matching = [c for c in centers if sector in c.get("sector_tags", []) or role["sector"] in c.get("sector_tags", [])]
        pool = matching or centers
        return sorted(pool, key=lambda c: c.get("distance_km", 999))[0]

    def _skill_gaps(self, profile: Profile, role: dict) -> tuple[list[SkillGap], int]:
        user_tags = set(profile.skills) | set(profile.interests)
        if profile.family_occupation:
            user_tags |= set(match_tags(profile.family_occupation))
        if profile.current_livelihood:
            user_tags |= set(match_tags(profile.current_livelihood))
        gaps: list[SkillGap] = []
        covered = 0
        for skill in role.get("core_skills", []):
            has = skill["tag"] in user_tags
            covered += 1 if has else 0
            gaps.append(SkillGap(
                skill_name=skill["name"],
                covered=has,
                note="आपको पहले से थोड़ा अनुभव/जानकारी दिखती है" if has else "ट्रेनिंग में सिखाया जाएगा",
            ))
        total = max(1, len(gaps))
        percent = round(100 * covered / total)
        return gaps, max(0, min(100, percent))

    @staticmethod
    def _why_it_fits(profile: Profile, role: dict, parts: dict[str, float]) -> str:
        """Plain-language Hindi, 1–2 sentences, built from the strongest components."""
        reasons = []
        if parts["similarity"] >= 0.35:
            match_tags_found = set(profile.skills) & set(role.get("skill_tags", []))
            if match_tags_found:
                pretty = ", ".join(sorted(match_tags_found)[:3])
                reasons.append(f"आपके मौजूदा अनुभव ({pretty}) इस काम से मिलते हैं")
            else:
                reasons.append("आपकी रुचि और पारिवारिक पृष्ठभूमि इस काम से मेल खाती है")
        if parts["demand"] >= 0.5:
            reasons.append("आपके जिले में इस काम की माँग दिखती है (डेमो डेटा)")
        if parts["education"] >= 0.9:
            reasons.append("आपकी पढ़ाई इसके लिए उपयुक्त है")
        elif parts["education"] < 0.3:
            reasons.append("पढ़ाई की शर्त के लिए छोटा पूरक कोर्स करना पड़ सकता है")
        if parts["preference"] >= 0.8:
            reasons.append("आपकी पसंद (नौकरी/स्वरोज़गार) के अनुकूल")
        if not reasons:
            reasons.append("यह भूमिका आपकी प्रोफ़ाइल के सबसे करीब है")
        return "। ".join(reasons[:2]) + "।"

    @staticmethod
    def _duration_display(hours: int) -> str:
        weeks = max(1, round(hours / 40))
        return f"लगभग {weeks} हफ़्ते ({hours} घंटे)"

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def recommend(self, profile: Profile, top_n: int = 3) -> RecommendResponse:
        district = self.resolve_district(profile.district)
        pvec = self._profile_vector(profile)
        scored: list[tuple[float, dict, ScoreBreakdown, dict]] = []

        for role, vec in zip(self.roles, self._role_vectors):
            sim, sim_note = self._similarity_component(profile, vec)
            edu, edu_note = self._education_component(profile, role)
            demand, demand_note = self._demand_component(role, district)
            mobility, mobility_note = self._mobility_component(profile, role, district)
            pref, pref_note = self._preference_component(profile, role)

            total = (
                WEIGHTS["similarity"] * sim
                + WEIGHTS["education"] * edu
                + WEIGHTS["demand"] * demand
                + WEIGHTS["mobility"] * mobility
                + WEIGHTS["preference"] * pref
            )
            breakdown = ScoreBreakdown(
                similarity=round(sim, 3), education=round(edu, 3), demand=round(demand, 3),
                mobility=round(mobility, 3), preference=round(pref, 3), total=round(total, 3),
                notes={
                    "similarity": sim_note, "education": edu_note, "demand": demand_note,
                    "mobility": mobility_note, "preference": pref_note,
                },
            )
            notes = {
                "similarity": sim_note, "education": edu_note, "demand": demand_note,
                "mobility": mobility_note, "preference": pref_note,
            }
            scored.append((total, role, breakdown, notes))

        # Eligibility as a soft filter: prefer eligible roles, fall back gracefully.
        eligible = [s for s in scored if s[2].education >= 0.9]
        near_miss = [s for s in scored if 0 < s[2].education < 0.9]
        pool = eligible if len(eligible) >= top_n else eligible + near_miss

        pool.sort(key=lambda s: s[0], reverse=True)
        top = pool[:top_n]

        recs: list[Recommendation] = []
        for rank, (total, role, breakdown, notes) in enumerate(top, start=1):
            gaps, match_percent = self._skill_gaps(profile, role)
            center = self._nearest_center(role, district)
            center_out = None
            if center:
                center_out = TrainingCenter(
                    name=center["name"], distance_km=center.get("distance_km"),
                    sector_tags=center.get("sector_tags", []), note=center.get("note", ""),
                )
            elig_note = notes["education"] if breakdown.education < 0.9 else ""
            recs.append(Recommendation(
                rank=rank,
                role_id=role["id"],
                job_role=role["job_role"],
                sector=role["sector"],
                nsqf_level=role["nsqf_level"],
                min_education=role["min_education"],
                duration_hours=role["duration_hours"],
                duration_display=self._duration_display(role["duration_hours"]),
                why_it_fits=self._why_it_fits(profile, role, {
                    "similarity": breakdown.similarity, "education": breakdown.education,
                    "demand": breakdown.demand, "mobility": breakdown.mobility,
                    "preference": breakdown.preference,
                }),
                skill_gaps=gaps,
                skill_match_percent=match_percent,
                nearest_center=center_out,
                scheme_pointer=role["schemes_supported"][0] if role.get("schemes_supported") else "कोई आधिकारिक योजना नहीं जोड़ी गई — अधिकारी से पूछें",
                physical_demand=role.get("physical_demand", "medium"),
                self_employment_potential=role.get("self_employment_potential", "medium"),
                score=max(0, min(100, round(total * 100))),
                score_breakdown=breakdown,
                eligibility_note=elig_note,
            ))

        district_note = ""
        if district:
            district_note = district.get("demand_summary_hi", "")
        else:
            district_note = "जिला नहीं पहचाना गया — स्थानिक माँग और केंद्र दिखाने के लिए जिला जोड़ें।"

        return RecommendResponse(
            recommendations=recs,
            generated_offline=True,
            data_notice=data_notice(),
            district_note=district_note,
        )
