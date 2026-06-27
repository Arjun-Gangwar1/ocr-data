import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()


def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "annotation_platform"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            SERIAL PRIMARY KEY,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role          TEXT NOT NULL CHECK (role IN ('pictaker','annotator','masker','manager','admin')),
            created_at    TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS folders (
            id      SERIAL PRIMARY KEY,
            medium  TEXT NOT NULL,
            cls     TEXT NOT NULL,
            subject TEXT NOT NULL,
            UNIQUE(medium, cls, subject)
        );
        CREATE TABLE IF NOT EXISTS documents (
            id          SERIAL PRIMARY KEY,
            doc_name    TEXT UNIQUE NOT NULL,
            folder_id   INTEGER NOT NULL,
            uploaded_by TEXT,
            uploaded_at TIMESTAMP DEFAULT NOW(),
            page_count  INTEGER NOT NULL DEFAULT 0,
            CONSTRAINT documents_folder_id_fk FOREIGN KEY (folder_id) REFERENCES folders(id)
        );
        CREATE TABLE IF NOT EXISTS pages (
            page_name              TEXT PRIMARY KEY,
            doc_id                 INTEGER,
            page_number            INTEGER NOT NULL DEFAULT 1,
            image_path             TEXT NOT NULL DEFAULT '',
            raw_image_path         TEXT NOT NULL DEFAULT '',
            crop_corners           TEXT,
            width                  INTEGER,
            height                 INTEGER,
            area                   TEXT NOT NULL DEFAULT 'pending_approval',
            assigned_to            TEXT,
            review_note            TEXT,
            reviewed_by            TEXT,
            reviewed_at            TIMESTAMP,
            upload_approval_status TEXT NOT NULL DEFAULT 'pending',
            upload_approval_note   TEXT,
            mask_status            TEXT NOT NULL DEFAULT 'pending',
            CONSTRAINT pages_doc_id_fk FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS boxes (
            id             SERIAL PRIMARY KEY,
            page_name      TEXT NOT NULL,
            assignment_id  INTEGER,
            parent_id      INTEGER,
            coordinates    TEXT NOT NULL DEFAULT '[]',
            tag_category   TEXT,
            tag_attributes TEXT,
            content_text   TEXT,
            reading_order  INTEGER,
            confidence     TEXT,
            created_at     TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS annotation_requests (
            id           SERIAL PRIMARY KEY,
            requested_by TEXT NOT NULL,
            medium       TEXT NOT NULL,
            cls          TEXT NOT NULL,
            subject      TEXT NOT NULL,
            folder_id    INTEGER,
            quantity     INTEGER NOT NULL CHECK (quantity > 0),
            status       TEXT NOT NULL DEFAULT 'pending',
            fulfilled    INTEGER NOT NULL DEFAULT 0,
            created_at   TIMESTAMP DEFAULT NOW(),
            reviewed_by  TEXT,
            reviewed_at  TIMESTAMP,
            CONSTRAINT annotation_requests_folder_id_fk FOREIGN KEY (folder_id) REFERENCES folders(id)
        );
        CREATE TABLE IF NOT EXISTS mask_regions (
            id          SERIAL PRIMARY KEY,
            page_name   TEXT NOT NULL,
            coordinates TEXT NOT NULL,
            created_by  TEXT,
            created_at  TIMESTAMP DEFAULT NOW(),
            CONSTRAINT mask_regions_page_name_fk FOREIGN KEY (page_name)
                REFERENCES pages(page_name) ON DELETE CASCADE ON UPDATE CASCADE
        );
        CREATE TABLE IF NOT EXISTS assignments (
            id           SERIAL PRIMARY KEY,
            page_name    TEXT NOT NULL,
            annotator    TEXT NOT NULL,
            tier         INTEGER NOT NULL DEFAULT 1,
            status       TEXT NOT NULL DEFAULT 'assigned',
            review_note  TEXT,
            assigned_at  TIMESTAMP DEFAULT NOW(),
            submitted_at TIMESTAMP,
            UNIQUE(page_name, annotator),
            CONSTRAINT assignments_page_name_fk FOREIGN KEY (page_name)
                REFERENCES pages(page_name) ON DELETE CASCADE ON UPDATE CASCADE
        );
        CREATE TABLE IF NOT EXISTS box_history (
            id            SERIAL PRIMARY KEY,
            box_id        INTEGER,
            page_name     TEXT NOT NULL,
            assignment_id INTEGER,
            action        TEXT NOT NULL,
            actor         TEXT,
            snapshot      TEXT,
            at            TIMESTAMP DEFAULT NOW(),
            CONSTRAINT box_history_page_name_fk FOREIGN KEY (page_name)
                REFERENCES pages(page_name) ON DELETE CASCADE ON UPDATE CASCADE
        );
    """)

    # Add new columns to existing installs
    for col_def in [
        "doc_id                 INTEGER",
        "page_number            INTEGER NOT NULL DEFAULT 1",
        "image_path             TEXT NOT NULL DEFAULT ''",
        "raw_image_path         TEXT NOT NULL DEFAULT ''",
        "crop_corners           TEXT",
        "width                  INTEGER",
        "height                 INTEGER",
        "assigned_to            TEXT",
        "review_note            TEXT",
        "reviewed_by            TEXT",
        "reviewed_at            TIMESTAMP",
        "upload_approval_status TEXT NOT NULL DEFAULT 'pending'",
        "upload_approval_note   TEXT",
        "mask_status            TEXT NOT NULL DEFAULT 'pending'",
    ]:
        cur.execute(f"ALTER TABLE pages ADD COLUMN IF NOT EXISTS {col_def}")

    cur.execute("ALTER TABLE annotation_requests ADD COLUMN IF NOT EXISTS folder_id INTEGER")

    # Widen users.role CHECK to include the 'masker' role (for existing installs)
    cur.execute("""
        DO $$
        DECLARE c text;
        BEGIN
            SELECT conname INTO c FROM pg_constraint
              WHERE conrelid = 'users'::regclass AND contype = 'c'
                AND pg_get_constraintdef(oid) ILIKE '%role%';
            IF c IS NOT NULL THEN
                EXECUTE 'ALTER TABLE users DROP CONSTRAINT ' || quote_ident(c);
            END IF;
            ALTER TABLE users ADD CONSTRAINT users_role_check
              CHECK (role IN ('pictaker','annotator','masker','manager','admin'));
        END $$;
    """)

    # Populate folders from annotation_requests (always safe — those columns are kept)
    cur.execute("""
        INSERT INTO folders (medium, cls, subject)
        SELECT DISTINCT medium, cls, subject FROM annotation_requests
        WHERE medium IS NOT NULL AND cls IS NOT NULL AND subject IS NOT NULL
        ON CONFLICT DO NOTHING;
    """)
    cur.execute("""
        UPDATE annotation_requests ar SET folder_id = f.id
        FROM folders f
        WHERE ar.folder_id IS NULL
          AND ar.medium = f.medium AND ar.cls = f.cls AND ar.subject = f.subject;
    """)

    # Migrate pages → folders + documents (only if old columns still exist)
    cur.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'pages' AND column_name = 'doc_name'
            ) THEN
                INSERT INTO folders (medium, cls, subject)
                SELECT DISTINCT medium, cls, subject FROM pages
                WHERE medium IS NOT NULL AND cls IS NOT NULL AND subject IS NOT NULL
                ON CONFLICT DO NOTHING;

                INSERT INTO documents (doc_name, folder_id, uploaded_by, uploaded_at)
                SELECT p.doc_name, f.id, MIN(p.uploaded_by), MIN(p.uploaded_at)
                FROM pages p
                JOIN folders f
                  ON f.medium = p.medium AND f.cls = p.cls AND f.subject = p.subject
                WHERE p.doc_name IS NOT NULL AND p.doc_name != ''
                GROUP BY p.doc_name, f.id
                ON CONFLICT (doc_name) DO NOTHING;

                UPDATE pages p SET doc_id = d.id
                FROM documents d
                WHERE p.doc_id IS NULL AND p.doc_name = d.doc_name;
            END IF;
        END $$;
    """)

    # Drop the now-redundant columns from pages
    cur.execute("""
        ALTER TABLE pages
            DROP COLUMN IF EXISTS doc_name,
            DROP COLUMN IF EXISTS medium,
            DROP COLUMN IF EXISTS cls,
            DROP COLUMN IF EXISTS subject,
            DROP COLUMN IF EXISTS uploaded_by,
            DROP COLUMN IF EXISTS uploaded_at;
    """)

    # FK constraints (named so the DO block can skip them if already present)
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pages_doc_id_fk') THEN
                ALTER TABLE pages ADD CONSTRAINT pages_doc_id_fk
                    FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'documents_folder_id_fk') THEN
                ALTER TABLE documents ADD CONSTRAINT documents_folder_id_fk
                    FOREIGN KEY (folder_id) REFERENCES folders(id);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'annotation_requests_folder_id_fk') THEN
                ALTER TABLE annotation_requests ADD CONSTRAINT annotation_requests_folder_id_fk
                    FOREIGN KEY (folder_id) REFERENCES folders(id);
            END IF;
        END $$;
    """)

    # page_count column on documents (for existing installs)
    cur.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS page_count INTEGER NOT NULL DEFAULT 0")

    # Initialise page_count from actual page rows
    cur.execute("""
        UPDATE documents d
        SET page_count = (SELECT COUNT(*) FROM pages p WHERE p.doc_id = d.id)
        WHERE page_count = 0
    """)

    # Trigger to keep page_count in sync
    cur.execute("""
        CREATE OR REPLACE FUNCTION _sync_doc_page_count() RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                UPDATE documents SET page_count = page_count + 1 WHERE id = NEW.doc_id;
            ELSIF TG_OP = 'DELETE' THEN
                UPDATE documents SET page_count = page_count - 1 WHERE id = OLD.doc_id;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger WHERE tgname = 'trg_pages_page_count'
            ) THEN
                CREATE TRIGGER trg_pages_page_count
                AFTER INSERT OR DELETE ON pages
                FOR EACH ROW EXECUTE FUNCTION _sync_doc_page_count();
            END IF;
        END $$;
    """)

    # Indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pages_doc_id ON pages(doc_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pages_area ON pages(area)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pages_assigned_to ON pages(assigned_to)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pages_mask_status ON pages(mask_status)")

    # Pages already assigned/annotated pre-date the masker stage — treat them as masked
    # so they neither flood the masker queue nor get re-masked over live annotation work.
    cur.execute("UPDATE pages SET mask_status = 'done' WHERE assigned_to IS NOT NULL AND mask_status = 'pending'")

    # ── A1: double-blind assignments + inter-annotator agreement ──
    cur.execute("ALTER TABLE boxes ADD COLUMN IF NOT EXISTS assignment_id INTEGER")
    cur.execute("ALTER TABLE pages ADD COLUMN IF NOT EXISTS iaa REAL")
    cur.execute("ALTER TABLE pages ADD COLUMN IF NOT EXISTS iaa_status TEXT")
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'boxes_assignment_id_fk') THEN
                ALTER TABLE boxes ADD CONSTRAINT boxes_assignment_id_fk
                    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE;
            END IF;
        END $$;
    """)
    # One-time backfill: a tier-1 assignment per existing assigned page + attach its
    # boxes. Gated on an empty assignments table so it never re-runs (re-running would
    # capture manager/admin-created NULL-assignment boxes and corrupt double-blind sets).
    cur.execute("SELECT COUNT(*) AS c FROM assignments")
    if cur.fetchone()["c"] == 0:
        cur.execute("""
            INSERT INTO assignments (page_name, annotator, tier, status, submitted_at)
            SELECT p.page_name, p.assigned_to, 1,
                   CASE WHEN p.area IN ('pending_approval','approved','needs_rework','flagged_admin')
                        THEN 'submitted' ELSE 'assigned' END,
                   CASE WHEN p.area IN ('pending_approval','approved','needs_rework','flagged_admin')
                        THEN NOW() ELSE NULL END
            FROM pages p
            WHERE p.assigned_to IS NOT NULL
            ON CONFLICT (page_name, annotator) DO NOTHING
        """)
        cur.execute("""
            UPDATE boxes b SET assignment_id = a.id
            FROM assignments a
            WHERE b.assignment_id IS NULL AND a.page_name = b.page_name AND a.tier = 1
        """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_assignments_page ON assignments(page_name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_assignments_annotator ON assignments(annotator)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_boxes_assignment ON boxes(assignment_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_box_history_page ON box_history(page_name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_folder_id ON documents(folder_id)")

    # Ensure FK with ON DELETE CASCADE + ON UPDATE CASCADE for boxes
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'boxes_page_name_fk'
            ) THEN
                ALTER TABLE boxes DROP CONSTRAINT IF EXISTS boxes_page_name_fkey;
                ALTER TABLE boxes ADD CONSTRAINT boxes_page_name_fk
                    FOREIGN KEY (page_name) REFERENCES pages(page_name)
                    ON DELETE CASCADE ON UPDATE CASCADE;
                ALTER TABLE boxes DROP CONSTRAINT IF EXISTS boxes_parent_id_fkey;
                ALTER TABLE boxes ADD CONSTRAINT boxes_parent_id_fk
                    FOREIGN KEY (parent_id) REFERENCES boxes(id)
                    ON DELETE CASCADE;
            END IF;
        END $$;
    """)

    conn.commit()
    cur.close()
    conn.close()
