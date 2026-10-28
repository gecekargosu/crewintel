"""Match Engine DRY RUN — mevcut tüm belgeler üzerinde salt-okunur analiz.

DB'deki crew_id / match_status / match_confidence DEĞİŞTİRMEZ. Yalnızca okur,
pipeline'ı çalıştırır ve özet + örnekler basar.

Kullanım:
    docker exec -i crewintel-backend python /dev/stdin < backend/scripts/match_engine_dry_run.py
    # veya
    cd backend && python scripts/match_engine_dry_run.py
"""

import sys
from collections import Counter

sys.path.insert(0, "/app")

from app.db.database import SessionLocal
from app.models.document import Document
from app.services.match_engine import MatchEngine

db = SessionLocal()
try:
    documents = db.query(Document).order_by(Document.id).all()
    engine = MatchEngine(db, actor_email="dry-run")

    counts: Counter = Counter()
    examples: dict[str, list[str]] = {}
    score_dist: Counter = Counter()
    false_positive_candidates = []

    for document in documents:
        result = engine.process(
            document,
            text=document.extracted_text or "",
            dry_run=True,
        )
        counts[result.decision] += 1

        score = result.best_candidate.score if result.best_candidate else 0
        bucket = (score // 10) * 10
        score_dist[f"{bucket:02d}-{bucket+9:02d}"] += 1

        # Mevcut durumla çelişen kararlar (risk sinyali):
        if (
            document.crew_member_id is not None
            and result.decision != "AUTO_MATCH"
            and result.best_candidate
            and result.best_candidate.crew_id != document.crew_member_id
        ):
            false_positive_candidates.append(
                f"doc={document.id} {document.original_filename}: "
                f"DB'de crew={document.crew_member_id}, engine en iyi={result.best_candidate.crew_id} "
                f"({result.best_candidate.score}p/{result.decision})"
            )

        if result.decision not in examples:
            examples[result.decision] = []
        if len(examples[result.decision]) < 5:
            best = result.best_candidate
            examples[result.decision].append(
                f"  doc={document.id} {document.original_filename} | "
                f"tip={document.document_type} | "
                f"en_iyi={best.first_name if best else '-'} {best.last_name if best else '-'} "
                f"({best.score if best else 0}p) | "
                f"sinyaller={best.signals if best else []}"
            )

    total = len(documents)
    print("=" * 70)
    print("MATCH ENGINE DRY RUN — SONUÇ RAPORU")
    print("=" * 70)
    print(f"TOPLAM BELGE: {total}")
    print(f"  AUTO_MATCH (otomatik eşleşebilir):        {counts.get('AUTO_MATCH', 0)}")
    print(f"  REVIEW_REQUIRED (inceleme gerekli):       {counts.get('REVIEW_REQUIRED', 0)}")
    print(f"  MATCH_CONFLICT (çelişki — otomatik YOK):  {counts.get('MATCH_CONFLICT', 0)}")
    print(f"  UNMATCHED (eşleşme yok):                  {counts.get('UNMATCHED', 0)}")
    print(f"  FAILED:                                   {counts.get('FAILED', 0)}")
    print()
    print("SKOR DAĞILIMI (en iyi aday puanı):")
    for bucket in sorted(score_dist):
        print(f"  {bucket}: {score_dist[bucket]}")

    print()
    print("ÖRNEKLER:")
    for decision in ("AUTO_MATCH", "REVIEW_REQUIRED", "MATCH_CONFLICT", "UNMATCHED"):
        print(f"--- {decision} ---")
        for line in examples.get(decision, ["  (yok)"]):
            print(line)

    print()
    print("MEVCUT BAĞLANTIYLA ÇELİŞEN KARARLAR (false-positive riski):")
    if false_positive_candidates:
        for line in false_positive_candidates:
            print("  ⚠", line)
    else:
        print("  Yok — mevcut tüm crew_id bağlantıları engine kararıyla uyumlu.")

    print()
    print("NOT: Bu çalıştırma hiçbir DB satırını değiştirmedi (dry_run=True).")
finally:
    db.close()
