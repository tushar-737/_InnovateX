"""Recommendation endpoint — works fully offline on cached seed data."""

from __future__ import annotations

from fastapi import APIRouter

from ..schemas import RecommendRequest, RecommendResponse
from ..services.recommender import RecommendationEngine

router = APIRouter()
engine = RecommendationEngine()


@router.post("/recommend", response_model=RecommendResponse)
def recommend(body: RecommendRequest) -> RecommendResponse:
    return engine.recommend(body.profile)
