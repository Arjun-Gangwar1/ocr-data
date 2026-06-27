# Lawful Basis Note — Processing of Students' Answer Scripts

**Project:** AI-Assisted Education System for Government Schools in Karnataka (IIT Dharwad × DSEL)
**Version:** 1.0 (2026-06-27) — draft, **to be confirmed by IITDH DPO/legal and acknowledged by DSEL**
**References:** DPDP Act 2023 §9 (children), §17 / DPDP Rules 2025 Fourth Schedule; MoU Clauses 6.2, 9.2

---

## 1. Why this note exists

The answer scripts are written by school students, most of whom are minors. The DPDP Rules 2025 ordinarily require **verifiable parental consent** before processing a child's personal data (Rule 10). This note records the basis on which the project processes these scripts **without obtaining individual parental consent for each student**, so the position is documented and reviewable.

## 2. The basis relied upon

1. **Department authorisation.** DSEL (the Data Fiduciary, and owner of the data under MoU Clause 9.1) authorises IIT Dharwad, as Data Processor, to process the scripts for OCR/assessment model development (MoU Clauses 6.2, 9.2).
2. **Fourth Schedule exemptions (DPDP Rules 2025):**
   - *Part A (entity-based)* — relief for **educational institutions** processing children's data for educational purposes/child safety; and
   - *Part B (purpose-based)* — narrowly-defined **research / archival** processing permitted without ordinary consent formalities.
   Both are **subject to conditions**: processing must be strictly necessary, proportionate, and limited to the minimum data required.
3. **Data minimisation.** Student names and roll numbers are **redacted before annotation**, and no identifying information enters the labelled dataset — so the personal-data footprint is minimal by design.

## 3. Conditions we meet

- **Necessity / proportionality** — only what is needed to train and evaluate the handwriting-recognition model.
- **Minimisation** — identifiers removed before annotation; anonymous identifiers used.
- **Purpose limitation** — used solely for this project (MoU Clause 9.2); no behavioural tracking, profiling, or targeting of children.
- **Security & residency** — see `security-measures.md`; all processing within India.

## 4. Open items (must close)

- [ ] **DSEL to confirm** the basis on which it shares the scripts, and whether any notice or consent is required at its end (flagged to the Commissioner, Dharwad).
- [ ] **IITDH DPO/legal to confirm** that the Fourth Schedule exemption applies to this processing as designed.

Until confirmed, processing proceeds on the **experimental pilot** basis only, with the safeguards above.

## 5. Disclaimer

This is an internal working note, not a legal opinion. The final position rests with IITDH's DPO/legal and the Department.
