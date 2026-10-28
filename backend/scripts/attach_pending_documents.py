"""Attach pending documents to their crew member via the `crew-0XX` filename convention.

These documents were uploaded but never auto-matched (match_status='pending',
crew_member_id IS NULL). The demo dataset names documents as
`<type>_<first>_<last>_crew-0XX.<ext>`, so the target crew is unambiguous.

This script only ADDS crew links (and deletes the four clearly-test files that
reference the removed test crew records 1/3). Every change is audit-logged.

Run from the backend container:
    python -m scripts.attach_pending_documents
"""

import re
from pathlib import Path

from app.db.database import SessionLocal
from app.models.crew_member import CrewMember
from app.models.document import Document
from app.services.audit import log_event

CREW_PATTERN = re.compile(r"crew-0?([0-9]+)")

# Files referencing the deleted test records (Test Crew id 1, Chatgpt GPT id 3).
TEST_REFERENCE_IDS = {1, 3}


def main() -> None:
    db = SessionLocal()
    attached = 0
    deleted = 0
    skipped = 0

    try:
        docs = (
            db.query(Document)
            .filter(
                Document.crew_member_id.is_(None),
                Document.match_status == "pending",
            )
            .all()
        )
        for doc in docs:
            match = CREW_PATTERN.search(doc.original_filename or "")
            if not match:
                skipped += 1
                continue
            target_id = int(match.group(1))

            if target_id in TEST_REFERENCE_IDS:
                # Document belongs to a deleted test record → remove file + row.
                Path(doc.storage_path).unlink(missing_ok=True)
                log_event(
                    db, "document_deleted_cleanup", "document", doc.id,
                    f"Test document deleted: {doc.original_filename}",
                    user_email="system:cleanup",
                )
                db.delete(doc)
                deleted += 1
                continue

            target = db.get(CrewMember, target_id)
            if target is None:
                skipped += 1
                continue

            doc.crew_member_id = target.id
            doc.match_status = "matched"
            doc.match_confidence = 100
            log_event(
                db, "document_attached_pending", "document", doc.id,
                f"Pending document {doc.original_filename} attached to crew {target.id} ({target.first_name} {target.last_name})",
                user_email="system:cleanup",
            )
            attached += 1

        db.commit()
        pending_left = (
            db.query(Document)
            .filter(Document.crew_member_id.is_(None))
            .count()
        )
        print(f"ATTACHED: {attached}")
        print(f"DELETED TEST FILES: {deleted}")
        print(f"SKIPPED (no/invalid target): {skipped}")
        print(f"PENDING DOCS REMAINING: {pending_left}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
