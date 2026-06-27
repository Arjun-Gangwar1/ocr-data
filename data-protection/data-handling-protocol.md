# Data-Handling Protocol — Answer Script Annotation

**Project:** AI-Assisted Education System for Government Schools in Karnataka (IIT Dharwad × DSEL, Government of Karnataka)
**Version:** 1.0 (2026-06-27) — interim, pending execution of the MoU; to be annexed to the MoU on execution
**References:** MoU Clauses 6.2, 9.1–9.6, 10.6

---

## 1. Parties and roles

- **DSEL, Government of Karnataka** — owner of the data and **Data Fiduciary** under the DPDP Act, 2023.
- **IIT Dharwad** — **Data Processor**, processing solely on the Department's authorisation for development of the project's OCR/assessment system (MoU Clauses 2.3, 6.2, 9.2).

## 2. Dataset

- Handwritten preparatory examination answer scripts, Grades 8–10 (Kannada and English), Karnataka government schools.
- Initial set: ~5,000 pages made available by the Office of the Commissioner for School Education, Dharwad. The experimental pilot uses a small subset.

## 3. Lawful basis

Processing for narrowly-defined educational/research purposes through an educational institution, consistent with the **Fourth Schedule** (entity- and purpose-based exemptions) of the DPDP Rules, 2025, on a strictly necessary, proportionate and **data-minimised** basis. See `lawful-basis-note.md`. The Department's confirmation of the basis (and of whether any notice/consent is required) is being sought.

## 4. Storage and residency

- All images and data are stored and processed **entirely within India**, on IIT Dharwad's secure intranet server (PowerEdge).
- Any backup is kept **within India only** (MeitY-empanelled cloud, India region), encrypted.
- No data is stored in, or accessed from, any location outside India (MoU Clause 9.5).

## 5. De-identification (redaction)

- Student **names and roll numbers are masked on the working (annotator-facing) copy before annotation**.
- The original unredacted scans are kept access-restricted (administrator only).
- Students are referenced only by **anonymous identifiers** (e.g. `en_8_eng_id1`). The identifier ↔ identity mapping, if retained, is held in a separate, access-controlled store.
- **No identifying information enters the labelled dataset.**

## 6. Access control and confidentiality

- Access is limited to authorised project members under signed confidentiality undertakings (`annotator-undertaking.md`).
- Role-based access control; least privilege; unique accounts; audit logging (MoU Clauses 9.3, 9.6).
- During the experimental pilot, annotation is performed by **in-house IIT Dharwad personnel only**.

## 7. Sub-processing

- No third-party / vendor annotators are engaged during the experimental pilot.
- Any future sub-processor will be engaged only under a written data-processing agreement, on **redacted** data, **within India**, with the same safeguards and the Department's prior intimation.

## 8. Use limitation

- Data is used solely for the development, evaluation and improvement of the project's OCR/assessment system.
- It is not shared publicly or with any third party.
- No Student PII is used in any commercial activity without the Department's prior written consent (MoU Clause 10.6).

## 9. Retention and deletion

- Retained only for the project term (proposed five years). On expiry/termination, data is transferred to the Department and copies securely deleted, except where retention is required by law (MoU Clause 9.4). See `retention-and-deletion.md`.

## 10. Breach handling

- Any suspected personal-data breach is contained and reported to the Department without undue delay, to enable notification to the Data Protection Board and affected data principals. See `breach-response.md`.

## 11. Status

Interim protocol for the experimental pilot, pending execution of the MoU. To be reviewed by IITDH's DPO/legal and annexed to the MoU.
