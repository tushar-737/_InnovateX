# Official data sources to plug in later

The prototype ships with **ILLUSTRATIVE SEED DATA ONLY** (`seed_data/`, labelled).
Before any real-world use, replace each mock asset with verified official data:

| # | Source | Portal / custodian | Replaces / feeds |
|---|---|---|---|
| 1 | **NCVET / NSQF Qualification Packs (QPs)** | ncvet.gov.in · nsdcindia.org | `nsqf_job_roles.json`: job roles, NSQF levels, duration, curriculum, assessment criteria |
| 2 | **NSDC / PMKVY training-centre locator** | skillindia.gov.in | `districts.json → training_centers`: real centres, trades, seats, geo-coordinates |
| 3 | **NCS — National Career Service** | ncs.gov.in | local labour-demand analytics → `demand_tags`, vacancy trends |
| 4 | **e-Shram** (unorganised workers) | eshram.gov.in | anonymised district-level worker demographics for profile priors & coverage checks |
| 5 | **PLFS (MoSPI)** | mospi.gov.in | district/region livelihood structure, employment status for demand weighting |
| 6 | **Udyam Registration** | udyamregistration.gov.in | local micro-enterprise ecosystem → self-employment pathway realism |
| 7 | **Bhashini** (MeitY) | bhashini.gov.in | production STT/TTS/translation for Indian languages (replace browser Web Speech adapters) |
| 8 | **MoSJE / PM-AJAY (GIA) guidelines** | socialjustice.gov.in · pmajay | verified scheme names, eligibility rules (currently only "verify" pointers) |
| 9 | **District Skill Committees / State Skill Missions** | state portals | district demand validation, centre mapping, dropout-risk context |
| 10 | **Whisper / open models** (optional) | openai/whisper | on-device STT alternative behind the same adapter interface |

## Rules we follow until then

- No invented salaries, placement rates or eligibility rules — ever.
- Qualitative `low/medium/high` labels only, clearly marked as editorial.
- Every scheme string contains **"verify"** — a pointer, never a promise.
- Each seed file carries an `_notice` block stating it is mock data.
