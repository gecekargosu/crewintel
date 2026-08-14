"""Uygunluk (eligibility) motoru.

Amaç: "MV X için Başmühendis aranıyor" → 5000 personel içinden en uygun adayları
belge tamlığı, belge bitiş durumu, müsaitlik ve deneyim üzerinden skorlar.

Skor bileşenleri (0-100):
  - Zorunlu belge varlığı    (0-40): passport, seaman_book, stcw, medical
  - Belge bitiş sağlığı      (0-20): expired 0 / urgent 0.5 / approaching 0.75 / valid 1
  - Müsaitlik                (0-20): available 20 / on_leave 10 / on_board 0 / not_available 0
  - Pozisyon + deneyim       (0-20): pozisyon uyumu + deneyim yılı

Precision ilkesi: hiçbir tek sinyal tek başına yüksek skor üretemez; eksik/geçersiz
belgesi olan personel otomatik olarak üst sıralara çıkamaz.
"""

from __future__ import annotations

from datetime import date
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from app.models.crew_member import CrewMember
from app.models.document import Document
from app.services.document_processing import normalize

REQUIRED_DOC_TYPES = ["passport", "seaman_book", "stcw", "medical"]

AVAILABILITY_WEIGHTS = {
    "available": 1.0,
    "on_leave": 0.5,
    "on_board": 0.0,
    "not_available": 0.0,
    None: 1.0,  # bilinmeyen → müsait say (mevcut kayıtlar)
}

EXPIRY_DOC_TYPES = ["passport", "seaman_book", "stcw", "medical", "goc"]


def position_similarity(requested: str, candidate: str | None) -> float:
    if not candidate:
        return 0.0
    a = normalize(requested)
    b = normalize(candidate)
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.9
    return SequenceMatcher(None, a, b).ratio()


def score_crew(
    crew: CrewMember,
    documents: list[Document],
    requested_position: str,
    today: date,
    urgent_days: int = 30,
    approaching_days: int = 90,
) -> dict:
    """Tek personel için skor + kırılım döndürür."""
    docs_by_type: dict[str, list[Document]] = {}
    for doc in documents:
        if doc.archived_at is None:
            docs_by_type.setdefault(doc.document_type, []).append(doc)

    def best_doc(doc_type: str) -> Document | None:
        docs = docs_by_type.get(doc_type) or []
        return max(docs, key=lambda d: d.expiry_date or date.min) if docs else None

    # 1) Zorunlu belge varlığı (0-40)
    completeness = 0.0
    doc_details = {}
    for doc_type in REQUIRED_DOC_TYPES:
        doc = best_doc(doc_type)
        if doc is None:
            doc_details[doc_type] = "missing"
            continue
        if doc.expiry_date and doc.expiry_date < today:
            doc_details[doc_type] = "expired"
            completeness += 0.25
        elif doc.expiry_date is None:
            doc_details[doc_type] = "no_date"
            completeness += 0.5
        else:
            doc_details[doc_type] = "valid"
            completeness += 1.0
    completeness_score = round((completeness / len(REQUIRED_DOC_TYPES)) * 40)

    # 2) Bitiş sağlığı (0-20)
    expiry_score = 0.0
    for doc_type in EXPIRY_DOC_TYPES:
        doc = best_doc(doc_type)
        if doc is None or doc.expiry_date is None:
            continue
        days = (doc.expiry_date - today).days
        if days < 0:
            factor = 0.0
        elif days <= urgent_days:
            factor = 0.5
        elif days <= approaching_days:
            factor = 0.75
        else:
            factor = 1.0
        expiry_score += factor
    expiry_score = round((expiry_score / len(EXPIRY_DOC_TYPES)) * 20)

    # 3) Müsaitlik (0-20)
    avail_factor = AVAILABILITY_WEIGHTS.get(crew.availability, 1.0)
    availability_score = round(avail_factor * 20)

    # 4) Pozisyon + deneyim (0-20)
    pos_sim = position_similarity(requested_position, crew.position)
    pos_sim = max(pos_sim, position_similarity(requested_position, crew.rank))
    exp_years = crew.experience_years or 0
    exp_factor = min(1.0, exp_years / 5.0)  # 5+ yıl → tam puan
    position_score = round((0.7 * pos_sim + 0.3 * exp_factor) * 20)

    total = completeness_score + expiry_score + availability_score + position_score

    return {
        "crew_id": crew.id,
        "first_name": crew.first_name,
        "last_name": crew.last_name,
        "position": crew.position,
        "rank": crew.rank,
        "availability": crew.availability or "available",
        "experience_years": exp_years,
        "score": total,
        "breakdown": {
            "documents": completeness_score,
            "expiry": expiry_score,
            "availability": availability_score,
            "position": position_score,
        },
        "documents_status": doc_details,
    }


def find_eligible(
    db: Session,
    requested_position: str,
    min_score: int = 50,
    limit: int = 25,
    ship_id: int | None = None,
) -> list[dict]:
    """Tüm aktif personeli skorlar, en yüksekten sıralar.

    Not: 5000 kişi için tek seferde tüm belgeleri belleğe almak yerine
    grup bazlı okuma yapılır (crew başına N belge).
    """
    today = date.today()
    crews = db.query(CrewMember).filter(CrewMember.status == "active").all()
    crew_ids = [c.id for c in crews]

    docs = (
        db.query(Document)
        .filter(Document.crew_member_id.in_(crew_ids))
        .order_by(Document.crew_member_id)
        .all()
    ) if crew_ids else []
    docs_by_crew: dict[int, list[Document]] = {}
    for doc in docs:
        docs_by_crew.setdefault(doc.crew_member_id, []).append(doc)

    results = []
    for crew in crews:
        if crew.availability == "not_available":
            continue  # müsait olmayan personel aday listesine girmez
        if ship_id is not None and ship_id in {a.ship_id for a in crew.assignments if a.status == "active"}:
            continue  # zaten o gemide çalışıyor
        result = score_crew(crew, docs_by_crew.get(crew.id, []), requested_position, today)
        if result["score"] >= min_score:
            results.append(result)

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]
