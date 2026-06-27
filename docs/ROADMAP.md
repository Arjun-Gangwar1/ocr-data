# Platform Roadmap & Handoff

**Project:** AI-Assisted Education System for Government Schools in Karnataka (IIT Dharwad × DSEL)
**Component:** OCR / answer-script annotation platform
**Branch:** `feat/qc-layer`
**Updated:** 2026-06-27

This document is the single source of truth for the QC-layer build-out. It records what is **done**, the **detailed design** for the remaining work (so it is implemented once, not redone), and the **ownership split**. Live task tracking mirrors this list.

---

## Ownership split

- **Heavy / architecture (done in-session):** the masker flow (done), and **A1 double-blind + IAA** (the foundational schema change — do before A2/B1/B2).
- **Collaborators (specs below):** B3 audit trail, A2 gold pages, B1 analytics, B2 export, C1 hotkeys, C2 data manager, the data-protection technical fixes, and the repo consolidation.

> A3 (ML pre-annotation) is intentionally **out of scope** for now.

---

## Platform baseline (as built)

- **Stack:** FastAPI + Postgres (`backend/`), React/Vite (`frontend/`). Roles: `pictaker`, `masker`, `annotator`, `manager`, `admin`.
- **Page lifecycle:**
  ```
  upload → upload_approval(admin) → MASK(masker) → assign(admin) → annotate(annotator) → review(manager) → approved(locked)
  ```
- **State columns on `pages`:** `upload_approval_status` (pending/approved/flagged/redo), `mask_status` (pending/done), `area` (assigned/pending_approval/approved/needs_rework/flagged_admin), `assigned_to`.
- **Images:** raw original in `storage/raw` (admin-only via `/pages/{name}/raw`); processed annotator-facing copy in `storage/uploads` (served at `/uploads`). Both mirrored to Google Drive (⚠ see security fixes).

---

## PR-1 — Masker flow ✅ DONE

Inserts an identifier-redaction stage between upload-approval and assignment. **A page cannot reach an annotator until `mask_status='done'`.**

- **DB (`database.py`):** `pages.mask_status` (default `pending`); `masker` added to the role CHECK (+ migration for existing DBs); `mask_regions` audit table; index on `mask_status`.
- **Auth (`auth.py`):** `require_masker` (allows `masker` + `admin`).
- **API (`main.py`):** `GET /masker/pages` (queue), `POST /masker/pages/{name}/mask` (regions → burn black boxes into the processed image via `_apply_redaction`, log regions, set `mask_status='done'`). Empty regions = "no identifier present". Assignment query gated on `mask_status='done'`. Re-cropping a page resets `mask_status='pending'`.
- **Frontend:** `MaskerPage.jsx` (draw-to-redact canvas), `getMaskerPages`/`maskPage` in `client.js`, `/masker` route + `masker` role redirect in `App.jsx`.

**Remaining for collaborators:** smoke-test against a real Postgres DB; optionally surface `mask_status` in the admin dashboard; optional heuristic auto-suggest of the header region (kept manual for v1).

---

## PR-3 — A1: Double-blind + IAA  ⭐ FOUNDATIONAL (do next, in-session)

### The problem
Today `boxes.page_name` scopes boxes to a **page**, and `pages.assigned_to` is a single annotator. PIPELINE.md requires **two annotators to annotate the same page independently**, then an agreement check. That is impossible without re-scoping boxes to a **(page, annotator)** pair. **This is the change most likely to be done wrong and force a redo — hence it is owned in-session.**

### Schema
```sql
CREATE TABLE assignments (
    id          SERIAL PRIMARY KEY,
    page_name   TEXT NOT NULL REFERENCES pages(page_name) ON DELETE CASCADE ON UPDATE CASCADE,
    annotator   TEXT NOT NULL,
    tier        INTEGER NOT NULL DEFAULT 1,     -- 1 = primary, 2 = reviewer, 3 = adjudicator
    status      TEXT NOT NULL DEFAULT 'assigned', -- assigned | submitted | accepted | superseded
    review_note TEXT,
    assigned_at TIMESTAMP DEFAULT NOW(),
    submitted_at TIMESTAMP,
    UNIQUE(page_name, annotator)
);
-- Re-scope boxes to an assignment:
ALTER TABLE boxes ADD COLUMN assignment_id INTEGER REFERENCES assignments(id) ON DELETE CASCADE;
```
- **Migration / back-compat:** for every existing page with `assigned_to`, create one tier-1 `assignment` and backfill `boxes.assignment_id` from `(page_name, assigned_to)`. Keep `boxes.page_name` (it stays valid and is handy for queries); `assignment_id` is the new authority for "whose boxes".
- Add a per-page aggregate (either keep `pages.area` for the page's overall state, or derive it from its assignments). Recommended: keep `pages.area` as the **aggregate** (assigned → pending_approval → approved …) driven by the assignments' collective state.

### Assignment flow
- `approve_annotation_request` creates **two** assignments per page (tier 1 + tier 2) to **two different** annotators. (Respect `mask_status='done'` gate — already enforced.) Pick the two annotators round-robin / least-loaded among eligible annotators for that folder.
- The annotator works only their **own** assignment: box endpoints become `assignment`-scoped (`GET /assignments/{id}/boxes`, etc.), or keep page-scoped endpoints but filter by the caller's assignment. New `GET /my-assignments`.

### IAA computation
- Trigger when **both** tier-1 and tier-2 assignments for a page are `submitted`.
- v1 metric: **character-level agreement** on the reading-order-concatenated transcript of each annotator → `agreement = 1 − CER` (CER = edit distance / reference length). Put the helper in a small `scoring.py` (pure function, unit-testable).
- v2 (later): per-region match = bbox IoU ≥ τ **and** text match; report block-level precision/recall + per-field agreement.
- **Decision:** `agreement ≥ 0.98` → mark both `accepted`, `pages.area='approved'` (or route to manager). Else create a **tier-3** adjudication assignment.

### Adjudication (Tier 3) — see PR "A1: adjudication + annotator UI"
- Adjudicator view: tier-1 vs tier-2 boxes/transcript **side by side**; pick or edit per region → the final accepted annotation. The final adjudicated page may enter the gold pool (feeds A2).

### Endpoints (sketch)
- `POST /annotation-requests/{id}/approve` → dual-assign (modify existing).
- `GET /my-assignments`; `GET /assignments/{id}/boxes`; box CRUD scoped to assignment.
- `POST /assignments/{id}/submit` → on pair-complete, compute IAA, set outcome.
- `GET /pages/{name}/iaa`; `GET /adjudication` (queue); `POST /adjudication/{page}/resolve`.

### Acceptance criteria
- A page is annotated independently by two annotators who cannot see each other's work.
- IAA is computed and stored; ≥98% auto-accepts; <98% creates a tier-3 task.
- Existing single-annotator data migrates without loss.

### Implemented in `feat/qc-layer` (backend) — follow-ups for #4
**Done:** `assignments` table + `boxes.assignment_id` (+ one-time backfill); `scoring.py`
(char-level CER / agreement, self-tested); dual-assignment in request approval (tier 1/2,
cap 2/page); assignment-scoped box read/write (annotators isolated; managers/admins see
all); `submit` computes IAA on pair completion (page row `FOR UPDATE` to serialise the two
submits); `needs_adjudication` on disagreement; `GET /my-assignments`, `GET /pages/{name}/iaa`
(manager-only), `GET /adjudication`.

**Follow-ups for #4 (frontend + adjudication):**
- **Annotator UI must switch from `/my-pages` to `/my-assignments`** — `/my-pages` keys off `assigned_to` (tier-1 only), so a tier-2 annotator's work is invisible there.
- **Canonical boxes for accepted pages:** an "agreed" page still has *two* box sets; pick tier-1 (or the adjudicated tier-3) as canonical for manager view / B2 export.
- **Tier-3 adjudication:** auto-create / assign a tier-3 assignment for `needs_adjudication` pages and build the side-by-side view. (Backend already finalises the page when a tier-3 assignment is submitted → `area='approved'`, `iaa_status='adjudicated'` — so only the assign + UI remain.)
- **Concurrency:** the 2-assignments-per-page cap is enforced sequentially, not by a DB constraint — add a row lock / partial unique index if concurrent approvals become possible.
- Optionally lock an annotator's boxes once their assignment is `submitted` (today only terminal page states block re-submit).

---

## PR-2 — B3: Annotation history / audit trail

- `box_history(id, box_id, assignment_id, page_name, action {create|update|delete}, actor, snapshot JSONB/TEXT, at TIMESTAMP)`.
- Write a history row in `box_db.insert/update/remove` (pass the actor through from the endpoint). Add `GET /pages/{name}/history` (manager/admin).
- Needed for dispute resolution + the fraud checks in PIPELINE §6, and referenced by `data-protection/breach-response.md`.

## PR-4 — A2: Gold pages + calibration scoring

- Mark gold pages: `pages.is_gold BOOLEAN` + a stored **ground-truth** annotation (a tier with `annotator='__gold__'`, or a `gold_boxes` table).
- Mix ~10% gold into each annotator's assignments (assignment query change). Annotators don't know which are gold.
- Score each annotator's gold work vs ground truth (reuse the `scoring.py` CER from A1). Flag annotators <93%. Calibration test = first N gold pages for a new annotator.

## PR-5 — B1: Per-annotator analytics dashboard

- Endpoints aggregating `assignments` + IAA + gold scores: per-annotator accuracy, throughput (pages/day), gold-accuracy, IAA trend; acceptance rate per batch.
- Admin/manager dashboard + a one-screen **weekly PI summary** (PIPELINE §12).

## PR-6 — B2: Standard training export (JSONL / COCO-text)

- New export endpoint producing, per accepted page: `image_path`, and per box `bbox` (pixels), `block_type`, `text`, `language`, `confidence`, `reading_order`. Emit **JSONL** (one record per page) and/or **COCO-text**. Keep the existing LaTeX export for document reconstruction.
- Do after A1 so boxes are sourced from the **accepted/adjudicated** assignment.

## PR-7 — C1 hotkeys · C2 data manager

- **C1:** number keys to pick block type in `AnnotatePage`/`TagDropdown`; arrow keys to move between regions. Frontend-only.
- **C2:** admin table to filter/sort pages across folders (by status, folder, annotator, mask/IAA state) and **bulk-assign**.

---

## Security / data-protection fixes (see `data-protection/ACTION_ITEMS.md`)

Track as one task; **security-critical — ⚠ the masker's PII guarantee is NOT real until this lands** (must be done before annotators touch real data):
- **Auth-gate `/uploads` and `/raw`** static mounts (currently unauthenticated, page names enumerable). ⚠ The processed `image_path` and the raw `raw_image_path` are the **same relative path**, so any annotator who knows `image_path` can fetch the **un-redacted** original at `/raw/<image_path>` and see name + roll number — defeating the masker. Fix: replace the static `/raw` mount with the auth'd `/pages/{name}/raw` endpoint (update `AdminPage`/`PictakerPage` raw-image display to fetch it as a blob), and stop returning `raw_image_path` to annotators (`my_pages` already strips it as a stopgap, but the open mount is the real hole).
- **Disable consumer Google Drive mirroring** → India-region encrypted backup (GCP `asia-south1`) + signed DPA. MoU Clause 9.5 makes India-only **mandatory**.
- Set a strong `JWT_SECRET`; lock `CORS` to the IIT-D origin(s); enforce TLS at the proxy.
- (Redaction-before-annotation is done via the masker.)

---

## Repo consolidation

Make **`prabodha-ai/ocr-data`** the one platform by adopting `aperture-sud/annotation-platform`'s history. Coordinated, not unilateral: Abhiram freezes his repo (nothing unpushed) → consolidate → he archives `annotation-platform` (read-only) with a pointer to ocr-data. The `feat/qc-layer` branch (this work) lands on the consolidated repo.
