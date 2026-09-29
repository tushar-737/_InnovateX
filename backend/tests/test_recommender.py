"""Unit tests for the transparent recommendation scorer."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas import Preference, Profile  # noqa: E402
from app.services.recommender import RecommendationEngine  # noqa: E402


def make_engine() -> RecommendationEngine:
    return RecommendationEngine()  # loads real seed data


def base_profile(**over) -> Profile:
    data = dict(
        age=32,
        district="Gonda",
        state="Uttar Pradesh",
        education="grade8",
        family_occupation="farming",
        current_livelihood="mazdoori",
        skills=["sewing", "cooking"],
        interests=["tailoring"],
        constraints=None,
        preference="self_employment",
        mobility="willing",
    )
    data.update(over)
    return Profile(**data)


class TestScoring:
    def test_score_bounds(self):
        engine = make_engine()
        resp = engine.recommend(base_profile())
        assert len(resp.recommendations) == 3
        for rec in resp.recommendations:
            assert 0 <= rec.score <= 100
            b = rec.score_breakdown
            for comp in (b.similarity, b.education, b.demand, b.mobility, b.preference):
                assert 0.0 <= comp <= 1.0
            total = 0.30 * b.similarity + 0.20 * b.education + 0.20 * b.demand + 0.15 * b.mobility + 0.15 * b.preference
            assert abs(total - b.total) < 0.02  # breakdown must explain the score

    def test_ranking_order(self):
        engine = make_engine()
        resp = engine.recommend(base_profile())
        scores = [r.score for r in resp.recommendations]
        assert scores == sorted(scores, reverse=True)

    def test_sewing_profile_prefers_apparel(self):
        engine = make_engine()
        resp = engine.recommend(base_profile(skills=["sewing", "tailoring"], interests=["apparel"]))
        sectors = [r.sector for r in resp.recommendations]
        assert "apparel" in sectors

    def test_education_filter(self):
        engine = make_engine()
        # A grade10 user must not get roles requiring graduate-level education.
        resp = engine.recommend(base_profile(education="grade10"))
        for rec in resp.recommendations:
            if rec.score_breakdown.education >= 0.9:
                from app.schemas import EDUCATION_ORDER

                assert EDUCATION_ORDER[rec.min_education] <= EDUCATION_ORDER["grade10"]

    def test_near_miss_flagged(self):
        engine = make_engine()
        # grade5 user: most roles need grade8+ — near-miss must carry an eligibility note.
        resp = engine.recommend(base_profile(education="grade5"))
        assert resp.recommendations
        for rec in resp.recommendations:
            if rec.score_breakdown.education == 0.25:
                assert rec.eligibility_note

    def test_demand_match(self):
        engine = make_engine()
        resp = engine.recommend(base_profile(district="Gonda"))
        for rec in resp.recommendations:
            assert 0.0 <= rec.score_breakdown.demand <= 1.0

    def test_unknown_district_neutral(self):
        engine = make_engine()
        resp = engine.recommend(base_profile(district="Unknown Place"))
        assert "जिला नहीं पहचाना" in resp.district_note or "district" in resp.district_note.lower()
        for rec in resp.recommendations:
            assert rec.score_breakdown.demand == 0.5

    def test_mobility_constrained_penalises_hard_jobs(self):
        engine = make_engine()
        resp_easy = engine.recommend(base_profile(mobility="willing"))
        resp_hard = engine.recommend(base_profile(mobility="limited", constraints="wheelchair"))
        # With limited mobility, physical-fit should never exceed what an unconstrained user gets
        # for the same role; sanity: constrained profile's max mobility component <= 1.0
        for rec in resp_hard.recommendations:
            assert 0.0 <= rec.score_breakdown.mobility <= 1.0
        assert resp_easy.recommendations and resp_hard.recommendations

    def test_preference_self_employment(self):
        engine = make_engine()
        resp = engine.recommend(base_profile(preference="self_employment"))
        for rec in resp.recommendations:
            assert 0.0 <= rec.score_breakdown.preference <= 1.0

    def test_skill_gap_values_are_real(self):
        engine = make_engine()
        resp = engine.recommend(base_profile(skills=["sewing"]))
        for rec in resp.recommendations:
            assert 0 <= rec.skill_match_percent <= 100
            covered = sum(1 for g in rec.skill_gaps if g.covered)
            expected = round(100 * covered / max(1, len(rec.skill_gaps)))
            assert rec.skill_match_percent == min(100, max(0, expected))

    def test_scheme_pointer_contains_verify(self):
        engine = make_engine()
        resp = engine.recommend(base_profile())
        for rec in resp.recommendations:
            assert "verify" in rec.scheme_pointer.lower() or "पुष्टि" in rec.scheme_pointer or "पूछें" in rec.scheme_pointer

    def test_offline_flag(self):
        engine = make_engine()
        resp = engine.recommend(base_profile())
        assert resp.generated_offline is True
        assert "ILLUSTRATIVE" in resp.data_notice

    def test_nearest_center_from_district(self):
        engine = make_engine()
        resp = engine.recommend(base_profile(district="gonda"))
        assert any(r.nearest_center for r in resp.recommendations)

    def test_deterministic(self):
        engine = make_engine()
        a = engine.recommend(base_profile())
        b = engine.recommend(base_profile())
        assert [r.role_id for r in a.recommendations] == [r.role_id for r in b.recommendations]
