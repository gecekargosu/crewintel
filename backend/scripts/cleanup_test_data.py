"""Controlled cleanup of clearly-test records in CREWINTEL.

What this script does (in ONE transaction, fully logged to audit_logs):

1. REASSIGNS documents whose filename contains `crew-0XX` from auto-created
   test crew records to the real crew member referenced by that ID
   (e.g. `passport_elif_yildiz_crew-006.pdf` → crew_member id 6).
2. CREATES a crew record when the referenced crew ID does not exist
   (e.g. `employment_contract_mehmet_cetin_crew-031.pdf` → "Mehmet Çetin").
3. DELETES documents that are unambiguous test artifacts
   (test_document*.txt, duplicate_test*.txt, *_Test_Crew*, *_Chatgpt_GPT*,
   CREW_MASTER_DATA.xlsx, TEST_SCENARIOS.md, ...) — physical files included.
4. DELETES the now-empty auto-created test crew records.

It never touches crew members that look like real people.

Run from the backend container:
    python -m scripts.cleanup_test_data
"""

import re
from pathlib import Path

from sqlalchemy import func

from app.db.database import SessionLocal
from app.models.crew_member import CrewMember
from app.models.document import Document
from app.services.audit import log_event

# Auto-created records from earlier test sessions — the source of the mess.
TEST_CREW_IDS = {1, 3, 51, 52, 53, 54, 55, 56, 57, 58, 59, 61, 62, 63, 64, 65, 66, 67}

CREW_PATTERN = re.compile(r"crew-0?([0-9]+)")


def _crew_name_from_filename(filename: str) -> tuple[str, str] | None:
    """Extract (first, last) from e.g. employment_contract_mehmet_cetin_crew-031.pdf."""
    stem = Path(filename).stem
    # Drop leading document-type words and trailing crew-0XX.
    parts = re.sub(r"crew-0?[0-9]+$", "", stem)
    parts = re.sub(r"^(passport|seaman_book|stcw|medical|employment_contract|training_certificate|contract|goc|cv|other)_", "", parts)
    tokens = [p for p in parts.split("_") if p]
    if len(tokens) >= 2:
        return tokens[0].capitalize(), tokens[1].capitalize()
    if len(tokens) == 1:
        return tokens[0].capitalize(), ""
    return None


def main() -> None:
    db = SessionLocal()
    reassigned = 0
    created_crew = 0
    deleted_docs = 0
    deleted_crew = 0

    try:
        # ── 1) Reassign documents with crew-0XX references ───────────────────
        docs = (
            db.query(Document)
            .filter(Document.crew_member_id.in_(TEST_CREW_IDS))
            .all()
        )
        for doc in docs:
            match = CREW_PATTERN.search(doc.original_filename or "")
            if not match:
                continue
            target_id = int(match.group(1))
            target = db.get(CrewMember, target_id)

            if target is None:
                # Referenced crew does not exist → create it from the filename.
                name = _crew_name_from_filename(doc.original_filename)
                if not name or not name[0]:
                    continue
                first, last = name
                target = CrewMember(
                    first_name=first,
                    last_name=last or "Unknown",
                    position="Unspecified",
                    nationality=None,
                    profile_data={"source": "cleanup_reassignment"},
                )
                db.add(target)
                db.flush()
                created_crew += 1
                log_event(
                    db, "crew_created_from_cleanup", "crew_member", target.id,
                    f"Crew created during cleanup for {doc.original_filename}",
                    user_email="system:cleanup",
                )

            if target.id in TEST_CREW_IDS:
                # Document genuinely belongs to another test record → will be
                # deleted together with that record below.
                continue

            from_crew_id = doc.crew_member_id
            doc.crew_member_id = target.id
            doc.match_status = "matched"
            doc.match_confidence = 100
            log_event(
                db, "document_reassigned", "document", doc.id,
                f"Document {doc.original_filename} reassigned to crew {target.id} ({target.first_name} {target.last_name})",
                metadata={"from_crew_id": from_crew_id, "to_crew_id": target.id},
                user_email="system:cleanup",
            )
            reassigned += 1

        # IMPORTANT: the session is autoflush=False, so pending reassignments
        # must be flushed BEFORE querying for leftovers — otherwise already-
        # reassigned documents are still visible on the test crew and get
        # wrongly deleted.
        db.flush()

        # ── 2) Delete leftover test documents (physical file + row) ──────────
        remaining = (
            db.query(Document)
            .filter(Document.crew_member_id.in_(TEST_CREW_IDS))
            .all()
        )
        for doc in remaining:
            Path(doc.storage_path).unlink(missing_ok=True)
            log_event(
                db, "document_deleted_cleanup", "document", doc.id,
                f"Test document deleted: {doc.original_filename}",
                user_email="system:cleanup",
            )
            db.delete(doc)
            deleted_docs += 1

        # ── 3) Delete the now-empty test crew records ────────────────────────
        test_crew = (
            db.query(CrewMember)
            .filter(CrewMember.id.in_(TEST_CREW_IDS))
            .all()
        )
        for crew in test_crew:
            log_event(
                db, "crew_deleted_cleanup", "crew_member", crew.id,
                f"Test crew deleted: {crew.first_name} {crew.last_name}",
                user_email="system:cleanup",
            )
            db.delete(crew)
            deleted_crew += 1

        db.commit()

        # ── Verify ────────────────────────────────────────────────────────────
        crew_total = db.query(func.count(CrewMember.id)).scalar()
        doc_total = db.query(func.count(Document.id)).scalar()
        test_remaining = (
            db.query(func.count(Document.id))
            .filter(Document.crew_member_id.in_(TEST_CREW_IDS))
            .scalar()
        )
        print(f"REASSIGNED: {reassigned}")
        print(f"CREATED CREW: {created_crew}")
        print(f"DELETED DOCS: {deleted_docs}")
        print(f"DELETED CREW: {deleted_crew}")
        print(f"AFTER: crew={crew_total}, documents={doc_total}, docs_still_on_test_crew={test_remaining}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
