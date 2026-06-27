# Security Measures (Technical & Organisational Measures)

**Project:** AI-Assisted Education System for Government Schools in Karnataka (IIT Dharwad × DSEL)
**Version:** 1.0 (2026-06-27) — draft, pending DPO/legal review
**References:** DPDP Act 2023 §8 (reasonable security safeguards); MoU Clauses 9.3, 9.5, 9.6

Status legend: ✅ in place · 🔧 to implement · ⏳ on setup

---

## 1. Encryption
- 🔧 **At rest:** full-disk / database encryption on the PowerEdge server holding scans and the database.
- ⏳ **Backups:** client-side encryption (or CMEK via Cloud KMS, India region) before any cloud backup, so the provider holds only ciphertext.
- 🔧 **In transit:** HTTPS/TLS for all platform access (terminate TLS at the IIT-D reverse proxy).

## 2. Access control
- ✅ **Role-based access** — pictaker / annotator / manager / admin roles enforced server-side.
- ✅ **Authentication** — JWT sessions; passwords bcrypt-hashed; 8-hour token expiry.
- 🔧 **Set a strong `JWT_SECRET`** in production (do not ship the default `change-me-in-production`).
- 🔧 **Least privilege** — annotators see only assigned, redacted pages; raw originals are admin-only.
- ✅ Unique per-user accounts; admin-managed user creation.

## 3. Network & exposure
- 🔧 **Close the unauthenticated image mounts.** The static `/uploads` and `/raw` mounts currently serve images without auth and page names are enumerable — gate image serving behind authentication/authorisation.
- 🔧 **Lock CORS** to the IIT-D front-end origin(s) (remove `allow_origins=["*"]`).
- ✅ Hosting on the IIT Dharwad intranet (PowerEdge), not public infrastructure.

## 4. Data residency (MoU 9.5 — mandatory, not optional)
- 🔧 **Disable consumer Google Drive mirroring** (`gdrive.upload_async`) — consumer Drive gives no India-residency guarantee.
- ⏳ If cloud backup is used, **pin to GCP `asia-south1` (Mumbai)**, set an org policy restricting resource locations to India, and ensure admin/console access is from within India.
- ⏳ Sign the cloud provider's **Data Processing Addendum (DPA)**.

## 5. De-identification
- 🔧 **Redact student name/roll on the working copy before annotation**; keep originals admin-only. Implement as an action at the existing admin upload-approval step (draw box → burn black rectangle into the annotator-facing image).

## 6. Logging & monitoring
- 🔧 **Audit logging** of access to images and changes to annotations (who/what/when).
- 🔧 **Annotation history** (versioning) to support dispute resolution and fraud checks.

## 7. Backups & recovery
- ⏳ Encrypted backups within India; periodic, with a tested restore procedure.

## 8. Endpoint / annotator handling
- 🔧 **Browser-only access** for annotators — no local download, copy, or export of source images.
- ✅ Anonymous identifiers used throughout the UI.

## 9. Sub-processors / vendors
- ⏳ Any vendor bound by a DPA + these same measures; redacted data only; within India.

---

**Open technical actions are consolidated in `ACTION_ITEMS.md`.** Items marked 🔧 that touch the platform code are to be done in the live `annotation-platform` repository.
