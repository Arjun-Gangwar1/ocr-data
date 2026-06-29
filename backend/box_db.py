import json

from database import db_cursor

_FIELDS = frozenset({"parent_id", "coordinates", "tag_category", "tag_attributes",
                     "content_text", "reading_order", "confidence"})


def _record_history(cur, action: str, box: dict, actor) -> None:
    """Append an audit row for a box mutation, using the caller's open cursor so it
    commits in the same transaction. `box` is the box state to snapshot."""
    if not box:
        return
    cur.execute(
        "INSERT INTO box_history (box_id, page_name, assignment_id, action, actor, snapshot) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (box.get("id"), box.get("page_name"), box.get("assignment_id"),
         action, actor, json.dumps(box, default=str)),
    )


def get_boxes(page_name: str) -> list:
    with db_cursor() as cur:
        cur.execute("""
            SELECT * FROM boxes WHERE page_name = %s
            ORDER BY CASE WHEN reading_order IS NULL THEN 1 ELSE 0 END, reading_order, id
        """, (page_name,))
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def get_boxes_for_assignment(page_name: str, assignment_id: int) -> list:
    with db_cursor() as cur:
        cur.execute("""
            SELECT * FROM boxes WHERE page_name = %s AND assignment_id = %s
            ORDER BY CASE WHEN reading_order IS NULL THEN 1 ELSE 0 END, reading_order, id
        """, (page_name, assignment_id))
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def insert_box(page_name: str, data: dict, actor=None) -> dict:
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO boxes (page_name, assignment_id, parent_id, coordinates, tag_category, tag_attributes,
                               content_text, reading_order, confidence)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (
            page_name,
            data.get("assignment_id"),
            data.get("parent_id"),
            data.get("coordinates", "[]"),
            data.get("tag_category"),
            data.get("tag_attributes"),
            data.get("content_text"),
            data.get("reading_order"),
            data.get("confidence"),
        ))
        row = dict(cur.fetchone())
        _record_history(cur, "create", row, actor)
    return row


def update_box(page_name: str, box_id: int, data: dict, actor=None) -> dict | None:
    updates = {k: v for k, v in data.items() if k in _FIELDS}
    if not updates:
        return fetch_box(page_name, box_id)
    sets = ", ".join(f"{k} = %s" for k in updates)
    with db_cursor() as cur:
        cur.execute(
            f"UPDATE boxes SET {sets} WHERE id = %s AND page_name = %s RETURNING *",
            (*updates.values(), box_id, page_name),
        )
        row = cur.fetchone()
        if row:
            _record_history(cur, "update", dict(row), actor)
    return dict(row) if row else None


def fetch_box(page_name: str, box_id: int) -> dict | None:
    with db_cursor() as cur:
        cur.execute("SELECT * FROM boxes WHERE id = %s AND page_name = %s", (box_id, page_name))
        row = cur.fetchone()
    return dict(row) if row else None


def remove_box(page_name: str, box_id: int, actor=None):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM boxes WHERE id = %s AND page_name = %s", (box_id, page_name))
        box = cur.fetchone()
        cur.execute("DELETE FROM boxes WHERE id = %s AND page_name = %s", (box_id, page_name))
        if box:
            _record_history(cur, "delete", dict(box), actor)
