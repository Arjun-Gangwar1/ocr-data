# Retention & Deletion Procedure

**Project:** AI-Assisted Education System for Government Schools in Karnataka (IIT Dharwad × DSEL)
**Version:** 1.0 (2026-06-27) — draft, pending DPO/legal review
**References:** MoU Clause 9.4; DPDP Act 2023 (storage limitation, data minimisation)

---

## 1. What is held

| Asset | Contains PII? | Access |
|---|---|---|
| Raw scans (original images) | Yes (name/roll visible) | Administrator only |
| Working / annotator-facing images | No (identifiers redacted) | Assigned annotators |
| Labelled dataset (annotations) | No | Project team |
| Identifier ↔ identity mapping (if kept) | Yes | Administrator only, separate store |
| Encrypted backups | As above | Administrator only |

## 2. Retention period

- **Project term, with raw scans retained for five (5) years** (project agreement / MoU), unless the Department directs otherwise.
- The **identifier ↔ identity mapping** is retained only as long as strictly necessary, and deleted at the earliest point it is no longer needed.

## 3. Deletion triggers

- End of the retention period.
- **Expiry or termination of the MoU** — on the Department's request, transfer all data to the Department and securely delete IITDH copies, except where retention is required by law (MoU Clause 9.4).
- A specific deletion request from the Department.

## 4. Deletion method

- Backups encrypted with managed keys: **crypto-erase** (destroy the keys) and delete the objects, then verify.
- On-disk data: secure erase / overwrite; remove from all replicas and the cloud backup; confirm removal.
- Record each deletion (what, when, by whom, verification) in the deletion log.

## 5. Records

- Maintain a short **deletion log** and a **handover record** (for return-to-Department events) for audit.
