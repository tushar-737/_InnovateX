# Kaushal Saathi — 3-minute demo script (SIH 2026)

**Problem Statement 26097** · Product: *Kaushal Saathi* · Audience: judges (mixed
technical + governance). One phone/laptop, one speaker, one mic.

> Everything shown uses **ILLUSTRATIVE SEED DATA**. Say this out loud once during
> the demo — it is a feature (honesty), not a weakness.

---

## Minute 0:00–0:30 — Problem & promise (30 s)

**Say:** *"For a beneficiary with low literacy, skilling portals are forms full of
jargon. Kaushal Saathi replaces the form with a warm Hindi conversation on any
phone, builds a profile by voice, and gives three transparent, NSQF-aligned
pathways — plus an officials' view of aggregate demand gaps."*

**Show:** the consent screen. Press **🔊 पढ़कर सुनाएँ** — the consent is read aloud
in Hindi. Press **✅ हाँ, आगे बढ़ें**.

## Minute 0:30–1:45 — The conversation (75 s)

Speak (or tap the chips) in Hindi. Sample transcript below — the full flow fills
all slots. Keep answers short; watch the live transcript and hear each reply.

| # | उपयोगकर्ता (Hindi spoken) | English translation | Assistant asks next |
|---|---|---|---|
| 0 | *(auto)* | *"Hello! I am Kaushal Saathi… may I know your name?"* | name |
| 1 | मेरा नाम सुनीता है | "My name is Sunita." | age |
| 2 | तीस साल | "Thirty years." | district |
| 3 | मैं गोंडा से हूँ | "I am from Gonda." | education |
| 4 | दसवीं तक पढ़ी हूँ | "I have studied up to 10th grade." | family occupation |
| 5 | घर में सब खेती करते हैं | "Everyone at home does farming." | current work |
| 6 | अभी मैं खेत में मज़दूरी करती हूँ | "Right now I work as farm labour." | skills |
| 7 | मुझे सिलाई आती है, खाना भी बना लेती हूँ | "I know sewing, and I can cook too." | interests |
| 8 | कपड़ों का काम पसंद है | "I like garment/clothing work." | constraints |
| 9 | घुटनों में दर्द रहता है, ज़्यादा भारी काम नहीं कर पाती | "My knees hurt; I can't do very heavy work." | preference |
| 10 | मुझे अपना छोटा काम शुरू करना है | "I want to start my own small work." | travel |
| 11 | हाँ, दस-बीस किलोमीटर जा सकती हूँ | "Yes, I can travel 10–20 km." | — complete |

**While this runs, point out:**
- 🎤 big mic, **live transcript** (partial results), reply **spoken AND shown**;
- **ONE question at a time** — no form, no jargon;
- mixed Hindi-English answers understood ("तीस साल", "10th");
- the **tap-to-answer chips** appear automatically if speech recognition fails
  twice (and type-in box as extra fallback) — demo-safe in a noisy hall.

## Minute 1:45–2:15 — Confirmation & correction (30 s)

**Show:** *"आपने बताया कि आपका नाम सुनीता है, आपकी उम्र 30 साल…"* — read back by
voice. Tap a field to fix it (or say **"umar 31 hai"**). Press
**✅ हाँ, यह सही है**.

**Say:** *"The profile is confirmed BY the beneficiary — not inferred silently."*

## Minute 2:15–2:50 — Three pathways, explained (35 s)

**Show:** three large cards, e.g. (illustrative):
1. **Tailor (Basic Garments)** — NSQF 3 · *"सिलाई का अनुभव है, गोंडा में कपड़े के काम की माँग, आपकी पढ़ाई उपयुक्त"*
2. **Sewing Machine Operator** — NSQF 3
3. **Traditional Food Products Maker** — NSQF 2 · self-employment friendly

On each card: **🔊 play aloud**, training duration, nearest centre (demo),
skill-gap bars (real skill names: *fabric cutting, body measurement…*), scheme
pointer **with "verify"**. Open **🔍 यह क्यों?** — the 5-part score breakdown with
weights and plain-language notes.

**Say:** *"No black box. Score = profile-match (TF-IDF) + education eligibility +
local demand + mobility fit + preference — every part visible, runs offline on
cached seed data."*

## Minute 2:50–3:00 — Close (10 s)

Press **📤 सारांश भेजें** — SMS/WhatsApp **simulated preview** (say "simulated").
Show **🗑️ मेरा डेटा मिटाएँ** works (privacy by design).

**Close:** *"Plugged into NCVET QPs, NCS demand and the PMKVY centre locator —
with Bhashini speech — this becomes a production assistant. Officials' dashboard
next."*

---

## Judge-proof Q&A cheat sheet

| Likely question | Honest answer |
|---|---|
| Is this real data? | **No** — clearly labelled illustrative seed data; lists exactly what official sources replace it (README → Data sources). |
| Which LLM? | Claude via backend `.env` key; if absent, a built-in Hindi rule engine runs the demo. Either way a deterministic parser validates every field. |
| Does it work offline? | The recommendation engine: **yes** (cached seed data). Conversation degrades gracefully to the rule engine; speech needs the browser. |
| Why top-3 only? | Cognitive load for low-literacy users; ranking is fully scored (all 42 roles scored, 3 shown). |
| Scheme eligibility? | **Never claimed.** Pointers labelled "verify". |
| Accuracy of recommendations? | Transparent heuristic scorer — validated later against real enrolment/outcome data; no outcome claims made. |
