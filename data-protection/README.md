# Data Protection Pack

**Project:** AI-Assisted Education System for Government Schools in Karnataka
**Parties:** Indian Institute of Technology Dharwad (IITDH) × Department of School Education and Literacy (DSEL), Government of Karnataka
**Status:** Draft v1.0 (2026-06-27) — pending IITDH DPO/legal review and MoU execution
**Not legal advice.** These are working documents to be confirmed by IITDH's institute DPO / legal cell.

---

## Purpose

This folder holds the internal data-protection documentation for the handling of student answer scripts used to train the project's handwriting-recognition (OCR) and assessment models. It operationalises **Clause 9 (Data Governance and Privacy)** of the MoU.

## DPDP roles

- **DSEL (Government of Karnataka) — Data Fiduciary.** Owns the data, decides the purpose, and holds the relationship with the data principals (students/parents). Responsible for consent/notice, grievance redressal, and overall accountability.
- **IIT Dharwad — Data Processor.** Processes the data solely on the Department's authorisation (MoU Clauses 6.2, 9.2) for the project's purposes. Responsible for security safeguards, redaction, sub-processor control, breach reporting, and deletion on termination.

The top-level instrument is the **MoU** (Clause 9). The documents below sit under it.

## Contents

| File | What it is | Owner |
|---|---|---|
| [data-handling-protocol.md](data-handling-protocol.md) | The operational SOP; to be annexed to the MoU | IITDH |
| [security-measures.md](security-measures.md) | Technical & organisational measures (DPDP §8 "reasonable safeguards") | IITDH |
| [retention-and-deletion.md](retention-and-deletion.md) | Retention schedule + secure deletion procedure | IITDH |
| [breach-response.md](breach-response.md) | Incident detection, escalation and notification procedure | IITDH → DSEL |
| [lawful-basis-note.md](lawful-basis-note.md) | Recorded basis for processing minors' data (Fourth Schedule) | IITDH (DSEL to confirm) |
| [processing-record.md](processing-record.md) | Record of processing activities (what/where/why) | IITDH |
| [annotator-undertaking.md](annotator-undertaking.md) | Confidentiality & data-handling undertaking signed by each annotator | IITDH |
| [ACTION_ITEMS.md](ACTION_ITEMS.md) | Open actions and owners — start here | IITDH / DSEL |

## How this maps to the MoU

- Clause 6.2 — facilitation of answer scripts for OCR training (the authorisation for the handover)
- Clause 9.1 — data is GoK property
- Clause 9.2 — use limited to project implementation / model improvement / research
- Clause 9.3 / 9.6 — technical & organisational safeguards, DPDP 2023 compliance, encryption, RBAC, audit logging, minimisation → see `security-measures.md`
- Clause 9.4 — return + secure deletion on termination → see `retention-and-deletion.md`
- Clause 9.5 — all data stored/processed within India only → see `security-measures.md`
- Clause 10.6 — no Student PII in commercial use without Department's written consent
