# Seed data — ILLUSTRATIVE ONLY

**⚠️ ILLUSTRATIVE SEED DATA — NOT OFFICIAL.**

Everything in this folder is hand-crafted for the Smart India Hackathon 2026 prototype
demo of *Kaushal Saathi*. It exists so the recommendation engine can run **fully offline**
with transparent, testable logic.

| File | What it is | Must be replaced with |
|---|---|---|
| `nsqf_job_roles.json` | ~42 NSQF-aligned job roles across 13 sectors | Official NCVET/NSQF **Qualification Packs (QPs)** and **NCS** occupation/role data (nsdcindia.org, ncvet.gov.in, ncs.gov.in) |
| `districts.json` | 3 districts: demand tags + mock training centres | District Skill Committee / state skill-mission verified demand data and the official **PMKVY centre locator** |

## Honesty rules baked into this data

- **No salary, placement-rate or employment statistics are claimed.** Where uncertain,
  fields use qualitative levels: `low` / `medium` / `high`.
- `self_employment_potential`, `physical_demand`, `typical_local_demand_tags` are
  **editorial judgements for demo purposes**, not measured values.
- Training-centre names, distances (`distance_km`) and district `demand_tags` are
  **mock values** and are labelled as such per entry.
- `schemes_supported` entries are **pointers only** ("verify" is part of every string).
  They are NOT eligibility claims. Always check current scheme names/rules on official
  portals before advising anyone.

## Schema notes (job role)

```jsonc
{
  "id": "tailor-basic",              // stable id
  "job_role": "Tailor (Basic Garments)",
  "sector": "apparel",
  "nsqf_level": 3,                    // 2–5 in seed; verify against NCVET QP
  "min_education": "none",            // none|grade5|grade8|grade10|grade12|iti|diploma|graduate
  "duration_hours": 240,
  "typical_local_demand_tags": ["tailoring", "apparel", ...],
  "self_employment_potential": "high",// low|medium|high (qualitative)
  "physical_demand": "low",           // low|medium|high (qualitative)
  "related_family_occupations": ["tailoring", "embroidery"],
  "skill_tags": ["tailoring", "sewing", ...],   // canonical tags → used by TF-IDF scorer
  "core_skills": [ {"name": "Body measurement", "tag": "measurement"} ],
  "schemes_supported": ["PMKVY 4.0 (verify)", ...]  // pointers, never eligibility claims
}
```
