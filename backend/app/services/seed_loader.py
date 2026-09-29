"""Load and cache the illustrative seed datasets (roles + districts)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parents[3] / "seed_data"


@lru_cache
def load_roles() -> list[dict]:
    data = json.loads((SEED_DIR / "nsqf_job_roles.json").read_text(encoding="utf-8"))
    return data["roles"]


@lru_cache
def load_districts() -> list[dict]:
    data = json.loads((SEED_DIR / "districts.json").read_text(encoding="utf-8"))
    return data["districts"]


@lru_cache
def data_notice() -> str:
    roles_notice = json.loads((SEED_DIR / "nsqf_job_roles.json").read_text(encoding="utf-8"))["_notice"]
    return roles_notice


@lru_cache
def district_notice() -> str:
    data = json.loads((SEED_DIR / "districts.json").read_text(encoding="utf-8"))["_notice"]
    return data
