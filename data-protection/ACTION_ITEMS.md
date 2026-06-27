# Data Protection — Action Items

**Project:** AI-Assisted Education System for Government Schools in Karnataka (IIT Dharwad × DSEL)
**Updated:** 2026-06-27

Status: ✅ done · 🔄 in progress · ⬜ to do

---

## A. Governance / paperwork

- ✅ Informatory email to Commissioner (CPI Dharwad) drafted (Gmail draft, to send from @iitdh.ac.in).
- ✅ WhatsApp message to CPI Dharwad drafted (interim notice + consent flag + request for more scripts).
- ⬜ **Get the MoU executed** — apex DSEL (Principal Secretary / Commissioner for Public Instruction, Bengaluru). This is the binding basis.
- ⬜ Obtain **interim written concurrence** from the Department for the pilot, pending MoU signature.
- ⬜ Annex `data-handling-protocol.md` (and this pack) to the MoU on execution.
- ⬜ **DSEL to confirm** lawful basis / whether notice or consent is required, and confirm the **nodal officer** (MoU 6.4).
- ⬜ **IITDH DPO/legal to review** this pack and confirm the Fourth Schedule basis (`lawful-basis-note.md`).
- ⬜ Designate a **project data-protection contact** (fill into `breach-response.md`).
- ⬜ Sign the **cloud provider DPA** when backup is set up.

## B. Technical (to be done in the live `annotation-platform` repo)

- ⬜ **Close the unauthenticated `/uploads` and `/raw` static mounts** — gate image serving behind auth.
- ⬜ **Disable consumer Google Drive mirroring**; move backup to **GCP `asia-south1`** (India), encrypted (client-side or CMEK), India-only org policy.
- ⬜ **Implement the redaction step** at the admin upload-approval stage (mask name/roll on the annotator-facing image; keep raw admin-only).
- ⬜ Set a strong **`JWT_SECRET`** in production (remove the default).
- ⬜ **Lock CORS** to the IIT-D front-end origin(s).
- ⬜ Add **audit logging** / annotation history.
- ⬜ Enforce **encryption at rest** (disk/DB) and **TLS** in front of the app.

## C. Operational (before/at pilot)

- ⬜ Every annotator signs the **confidentiality undertaking** (`annotator-undertaking.md`) before access.
- ⬜ Keep the pilot **in-house only** (no external vendors yet).
- ⬜ Secure the already-photographed scripts (access-restricted) until concurrence is in hand.
- ⬜ Start backups within India with a **tested restore**.

## D. Department-side (flag only — DSEL owns)

- ⬜ Consent/notice to students-parents OR confirmation of the exemption basis.
- ⬜ Grievance redressal route for data principals.

---

### Suggested order
1. B (technical fixes) + C (undertakings) — so the pilot is safe to run now.
2. A (interim concurrence, then MoU execution + DPO review).
3. D — Department's, in parallel.
