"""Personel Portalı (temel) — crew rolündeki kullanıcı kendi verisini görür.

- GET  /api/portal/me            → profil + belgeleri
- PUT  /api/portal/contact       → telefon / e-posta güncelle
- POST /api/portal/documents     → self-service belge yükle (admin onayına düşer)
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.database import get_db
from app.models.crew_member import CrewMember
from app.models.document import Document
from app.models.user import User
from app.services.audit import log_event
from app.services.document_processing import extract_metadata, extract_text, store_file


router = APIRouter(prefix="/api/portal", tags=["Portal"])


def _require_crew_user(current_user: User, db: Session) -> CrewMember:
    if current_user.role != "crew" or current_user.crew_member_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu uç yalnızca personel hesapları içindir.")
    crew = db.get(CrewMember, current_user.crew_member_id)
    if crew is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personel kaydı bulunamadı.")
    return crew


def _serialize_doc(doc: Document) -> dict:
    return {
        "id": doc.id,
        "document_type": doc.document_type,
        "document_number": doc.document_number,
        "original_filename": doc.original_filename,
        "issue_date": doc.issue_date.isoformat() if doc.issue_date else None,
        "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
        "match_status": doc.match_status,
        "archived": doc.archived_at is not None,
    }


@router.get("/me")
def portal_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    crew = _require_crew_user(current_user, db)
    documents = (
        db.query(Document)
        .filter(Document.crew_member_id == crew.id)
        .order_by(Document.archived_at.is_(None).desc(), Document.document_type)
        .all()
    )
    return {
        "profile": {
            "first_name": crew.first_name,
            "last_name": crew.last_name,
            "position": crew.position,
            "rank": crew.rank,
            "nationality": crew.nationality,
            "phone": crew.phone,
            "email": crew.email,
            "availability": crew.availability,
            "experience_years": crew.experience_years,
            "date_of_birth": crew.date_of_birth.isoformat() if crew.date_of_birth else None,
            "job_seeking": bool(crew.job_seeking),
        },
        "documents": [_serialize_doc(d) for d in documents],
        "required_types": ["passport", "seaman_book", "stcw", "medical"],
    }


# ── İş ilanları (portal) ─────────────────────────────────────────────────────


@router.get("/jobs")
def portal_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Yayındaki ilanları personel görebilir; kendi başvuru durumuyla birlikte."""
    crew = _require_crew_user(current_user, db)
    from app.models.job import JobApplication, JobPosting

    postings = (
        db.query(JobPosting)
        .filter(JobPosting.status.in_(("open", "published")))
        .order_by(JobPosting.id.desc())
        .all()
    )
    my_apps = {
        a.job_posting_id: a.status
        for a in db.query(JobApplication).filter(JobApplication.crew_member_id == crew.id).all()
    }
    return [
        {
            "id": p.id,
            "title": p.title,
            "position": p.position,
            "ship_name": p.ship.name if p.ship else None,
            "salary": p.salary,
            "currency": p.currency,
            "contract_duration": p.contract_duration,
            "join_date": p.join_date.isoformat() if p.join_date else None,
            "application_deadline": p.application_deadline.isoformat() if p.application_deadline else None,
            "description": p.description,
            "requirements": p.requirements,
            "contact_info": p.contact_info,
            "application_status": my_apps.get(p.id),
            "image_url": f"/api/jobs/{p.id}/image",
        }
        for p in postings
    ]


@router.post("/jobs/{job_id}/apply")
def portal_apply(
    job_id: int,
    payload: dict | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.job import JobApplication, JobPosting

    crew = _require_crew_user(current_user, db)
    posting = db.get(JobPosting, job_id)
    if posting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="İlan bulunamadı.")
    if posting.status not in ("open", "published"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu ilan kapalı.")
    existing = (
        db.query(JobApplication)
        .filter(JobApplication.job_posting_id == job_id,
                JobApplication.crew_member_id == crew.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bu ilana zaten başvurdunuz.")

    # M1: başvuru anında kural-bazlı uygunluk skoru (karar #5/#6)
    from datetime import date as date_type

    from app.models.document import Document
    from app.services.eligibility import score_crew

    documents = db.query(Document).filter(Document.crew_member_id == crew.id).all()
    match_score = score_crew(crew, documents, posting.position, date_type.today())["score"]

    application = JobApplication(
        job_posting_id=job_id,
        crew_member_id=crew.id,
        note=(payload or {}).get("note"),
        status="applied",
        match_score=match_score,
        applied_from="mobile",
    )
    db.add(application)
    log_event(db, "job_application_created", "job_application", application.id,
              f"Portal başvurusu: {posting.title} → #{crew.id} (skor {match_score})",
              user_email=current_user.email)
    db.commit()
    return {"id": application.id, "status": "applied", "match_score": match_score}


@router.patch("/job-seeking")
def set_job_seeking(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Personel 'İş Arıyorum' anahtarını açar/kapatır."""
    crew = _require_crew_user(current_user, db)
    crew.job_seeking = bool(payload.get("job_seeking"))
    log_event(db, "crew_job_seeking", "crew_member", crew.id,
              f"{crew.first_name} {crew.last_name} 'İş Arıyorum' = {crew.job_seeking}",
              user_email=current_user.email)
    db.commit()
    return {"job_seeking": bool(crew.job_seeking)}


@router.put("/contact")
def update_contact(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    crew = _require_crew_user(current_user, db)
    phone = (payload.get("phone") or "").strip() or None
    email = (payload.get("email") or "").strip().lower() or None
    if email and email != current_user.email:
        other = db.query(User).filter(User.email == email).first()
        if other and other.id != current_user.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bu e-posta başka bir kullanıcıda kayıtlı.")
        current_user.email = email
    crew.phone = phone
    crew.email = email
    log_event(db, "crew_contact_updated", "crew_member", crew.id,
              f"{crew.first_name} {crew.last_name} iletişim bilgilerini güncelledi (portal)",
              user_email=current_user.email)
    db.commit()
    return {"phone": crew.phone, "email": crew.email}


@router.post("/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Self-service belge yükleme: belge tipi otomatik algılanır, onay kuyruğuna düşer."""
    crew = _require_crew_user(current_user, db)
    settings = get_settings()

    allowed = {".pdf": "application/pdf", ".txt": "text/plain"}
    suffix = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""
    if f".{suffix}" not in allowed:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Sadece PDF veya TXT yükleyebilirsiniz.")
    content = await file.read()
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Dosya boyutu çok büyük.")
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Boş dosya yüklenemez.")

    path, stored_name, checksum = store_file(settings.storage_path, file.filename, content)
    text = extract_text(file.filename, content) or ""
    metadata = extract_metadata(file.filename, text)
    doc_type = metadata.get("document_type") or "other"

    document = Document(
        crew_member_id=crew.id,
        original_filename=file.filename,
        stored_filename=stored_name,
        storage_path=path,
        mime_type=allowed[f".{suffix}"],
        file_size=len(content),
        checksum=checksum,
        document_type=doc_type,
        match_status="pending_approval",
        match_confidence=0,
        extracted_text=text[:20000] or None,
        source="crew_upload",
    )
    db.add(document)
    db.flush()
    log_event(db, "crew_document_uploaded", "document", document.id,
              f"{crew.first_name} {crew.last_name} belge yükledi (onay bekliyor): {file.filename}",
              user_email=current_user.email)
    db.commit()
    return {"id": document.id, "document_type": doc_type, "status": "pending_approval",
            "message": "Belgeniz alındı, yönetici onayına gönderildi."}


# ── M1 Mobile: tam profil / tercihler / belgeler / kontrat / gemi / başvurular ──


def _doc_status(doc: Document) -> str:
    from datetime import date as date_type

    from app.core.config import get_settings
    from app.services.document_processing import document_expiry_status

    settings = get_settings()
    if doc.match_status in ("pending", "pending_approval", "processing"):
        return doc.match_status
    return document_expiry_status(
        doc.expiry_date,
        date_type.today(),
        settings.expiry_urgent_days,
        settings.expiry_approaching_days,
    )


def _doc_full(doc: Document) -> dict:
    data = _serialize_doc(doc)
    data["status"] = _doc_status(doc)
    data["match_confidence"] = doc.match_confidence
    data["created_at"] = doc.created_at.isoformat() if doc.created_at else None
    return data


@router.get("/me/full")
def portal_profile_full(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mobil ana ekran için tek yanıt: profil + belgeler + kontrat + gemi + tercihler."""
    from datetime import date as date_type

    from app.models.assignment import ShipCrewAssignment
    from app.models.contract import Contract
    from app.services.eligibility import score_crew

    crew = _require_crew_user(current_user, db)
    documents = (
        db.query(Document)
        .filter(Document.crew_member_id == crew.id)
        .order_by(Document.archived_at.is_(None).desc(), Document.document_type)
        .all()
    )

    today = date_type.today()
    active_contract = (
        db.query(Contract)
        .filter(
            Contract.crew_member_id == crew.id,
            Contract.status == "active",
            Contract.start_date <= today,
            (Contract.end_date.is_(None) | (Contract.end_date >= today)),
        )
        .order_by(Contract.end_date.desc())
        .first()
    )
    active_assignment = (
        db.query(ShipCrewAssignment)
        .filter(
            ShipCrewAssignment.crew_member_id == crew.id,
            ShipCrewAssignment.status == "active",
            (ShipCrewAssignment.end_date.is_(None) | (ShipCrewAssignment.end_date >= today)),
        )
        .order_by(ShipCrewAssignment.start_date.desc())
        .first()
    )

    eligibility = score_crew(crew, documents, crew.position or "", today)

    return {
        "profile": {
            "first_name": crew.first_name,
            "last_name": crew.last_name,
            "position": crew.position,
            "rank": crew.rank,
            "nationality": crew.nationality,
            "phone": crew.phone,
            "email": crew.email,
            "availability": crew.availability or "available",
            "experience_years": crew.experience_years,
            "date_of_birth": crew.date_of_birth.isoformat() if crew.date_of_birth else None,
            "job_seeking": bool(crew.job_seeking),
            "available_from": crew.available_from.isoformat() if crew.available_from else None,
            "job_preferences": crew.job_preferences or {},
            "vessel_types_experience": crew.vessel_types_experience,
            "expected_salary_min": crew.expected_salary_min,
            "expected_salary_max": crew.expected_salary_max,
            "expected_salary_currency": crew.expected_salary_currency,
            "expected_salary_period": crew.expected_salary_period,
        },
        "documents": [_doc_full(d) for d in documents],
        "eligibility": {
            "score": eligibility["score"],
            "breakdown": eligibility["breakdown"],
            "documents_status": eligibility["documents_status"],
        },
        "contract": (
            {
                "id": active_contract.id,
                "contract_number": active_contract.contract_number,
                "contract_type": active_contract.contract_type,
                "start_date": active_contract.start_date.isoformat(),
                "end_date": active_contract.end_date.isoformat() if active_contract.end_date else None,
                "days_remaining": (
                    (active_contract.end_date - today).days
                    if active_contract.end_date else None
                ),
                "ship_name": active_contract.ship.name if active_contract.ship else None,
            }
            if active_contract else None
        ),
        "vessel": (
            {
                "id": active_assignment.ship.id,
                "name": active_assignment.ship.name,
                "imo_number": active_assignment.ship.imo_number,
                "flag": active_assignment.ship.flag,
                "ship_type": active_assignment.ship.ship_type,
                "position": active_assignment.position,
                "start_date": active_assignment.start_date.isoformat(),
                "end_date": active_assignment.end_date.isoformat() if active_assignment.end_date else None,
            }
            if active_assignment else None
        ),
        "required_types": ["passport", "seaman_book", "stcw", "medical"],
    }


@router.put("/preferences")
def update_preferences(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """İş tercihleri + müsaitlik tarihi + maaş beklentisi güncelle (M1)."""
    from datetime import date as date_type

    crew = _require_crew_user(current_user, db)

    if "job_preferences" in payload and payload["job_preferences"] is not None:
        if not isinstance(payload["job_preferences"], dict):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                                detail="job_preferences bir nesne olmalı.")
        crew.job_preferences = payload["job_preferences"]
    if "available_from" in payload:
        raw = payload["available_from"]
        if raw in (None, ""):
            crew.available_from = None
        else:
            try:
                crew.available_from = date_type.fromisoformat(raw)
            except ValueError:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                                    detail="available_from YYYY-MM-DD formatında olmalı.") from None
    if "vessel_types_experience" in payload:
        crew.vessel_types_experience = (payload["vessel_types_experience"] or "").strip() or None
    if "expected_salary_min" in payload:
        crew.expected_salary_min = payload["expected_salary_min"]
    if "expected_salary_max" in payload:
        crew.expected_salary_max = payload["expected_salary_max"]
    if "expected_salary_currency" in payload:
        crew.expected_salary_currency = (payload["expected_salary_currency"] or "USD").upper()[:10]
    if "expected_salary_period" in payload:
        crew.expected_salary_period = payload["expected_salary_period"] or "monthly"

    log_event(db, "crew_preferences_updated", "crew_member", crew.id,
              f"{crew.first_name} {crew.last_name} iş tercihlerini güncelledi (mobil)",
              user_email=current_user.email)
    db.commit()
    return {"ok": True}


@router.get("/documents")
def portal_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Kendi belgelerim — durum hesaplı (valid/expiring/expired/pending...)."""
    crew = _require_crew_user(current_user, db)
    documents = (
        db.query(Document)
        .filter(Document.crew_member_id == crew.id)
        .order_by(Document.archived_at.is_(None).desc(), Document.document_type)
        .all()
    )
    return [_doc_full(d) for d in documents]


@router.get("/documents/{document_id}/file")
def portal_document_file(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Kendi belgesini indir (IDOR korumalı — yalnızca sahibi)."""
    import os

    from fastapi.responses import FileResponse

    crew = _require_crew_user(current_user, db)
    document = db.get(Document, document_id)
    if document is None or document.crew_member_id != crew.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Belge bulunamadı.")
    if not document.storage_path or not os.path.exists(document.storage_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dosya kayıtlarımızda bulunamadı.")
    log_event(db, "crew_document_downloaded", "document", document.id,
              f"{crew.first_name} {crew.last_name} belgesini indirdi (mobil)",
              user_email=current_user.email)
    db.commit()
    return FileResponse(
        document.storage_path,
        media_type=document.mime_type or "application/octet-stream",
        filename=document.original_filename,
    )


@router.get("/contracts/me")
def portal_contracts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Kendi kontratlarım — aktif olan önce, geri sayım ile (M1)."""
    from datetime import date as date_type

    from app.models.contract import Contract

    crew = _require_crew_user(current_user, db)
    today = date_type.today()
    contracts = (
        db.query(Contract)
        .filter(Contract.crew_member_id == crew.id)
        .order_by(Contract.start_date.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "contract_number": c.contract_number,
            "contract_type": c.contract_type,
            "start_date": c.start_date.isoformat(),
            "end_date": c.end_date.isoformat() if c.end_date else None,
            "status": c.status,
            "days_remaining": (c.end_date - today).days if c.end_date else None,
            "ship_name": c.ship.name if c.ship else None,
        }
        for c in contracts
    ]


@router.get("/vessel/me")
def portal_vessel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aktif atamadan gemim (M1)."""
    from datetime import date as date_type

    from app.models.assignment import ShipCrewAssignment

    crew = _require_crew_user(current_user, db)
    today = date_type.today()
    assignment = (
        db.query(ShipCrewAssignment)
        .filter(
            ShipCrewAssignment.crew_member_id == crew.id,
            ShipCrewAssignment.status == "active",
            (ShipCrewAssignment.end_date.is_(None) | (ShipCrewAssignment.end_date >= today)),
        )
        .order_by(ShipCrewAssignment.start_date.desc())
        .first()
    )
    if assignment is None:
        return None
    ship = assignment.ship
    return {
        "id": ship.id,
        "name": ship.name,
        "imo_number": ship.imo_number,
        "flag": ship.flag,
        "ship_type": ship.ship_type,
        "company": ship.company,
        "position": assignment.position,
        "start_date": assignment.start_date.isoformat(),
        "end_date": assignment.end_date.isoformat() if assignment.end_date else None,
        "status": assignment.status,
    }


@router.get("/applications")
def portal_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Başvurularım — ilan başlığı ve durum ile (M1)."""
    from app.models.job import JobApplication

    crew = _require_crew_user(current_user, db)
    applications = (
        db.query(JobApplication)
        .filter(JobApplication.crew_member_id == crew.id)
        .order_by(JobApplication.id.desc())
        .all()
    )
    return [
        {
            "id": a.id,
            "job_posting_id": a.job_posting_id,
            "title": a.posting.title if a.posting else None,
            "position": a.posting.position if a.posting else None,
            "ship_name": a.posting.ship.name if a.posting and a.posting.ship else None,
            "status": a.status,
            "match_score": a.match_score,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in applications
    ]


@router.get("/jobs/recommended")
def portal_recommended_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Profilime uygun ilanlar — kural-bazlı skor (M1, karar #5/#6)."""
    from app.models.document import Document
    from app.models.job import JobPosting
    from app.services.eligibility import position_similarity, score_crew

    crew = _require_crew_user(current_user, db)
    postings = (
        db.query(JobPosting)
        .filter(JobPosting.status.in_(("open", "published")))
        .order_by(JobPosting.id.desc())
        .all()
    )
    if not postings:
        return []

    documents = db.query(Document).filter(Document.crew_member_id == crew.id).all()
    from datetime import date as date_type

    today = date_type.today()

    results = []
    for posting in postings:
        base = score_crew(crew, documents, posting.position, today)
        score = base["score"]
        # Tercih bonusu: personel o pozisyonu arıyorsa
        prefs = crew.job_preferences or {}
        preferred_positions = prefs.get("positions") or []
        if posting.position in preferred_positions:
            score = min(100, score + 10)
        results.append(
            {
                "id": posting.id,
                "title": posting.title,
                "position": posting.position,
                "ship_name": posting.ship.name if posting.ship else None,
                "vessel_type": posting.vessel_type,
                "location": posting.location,
                "salary": posting.salary,
                "currency": posting.currency,
                "contract_duration": posting.contract_duration,
                "join_date": posting.join_date.isoformat() if posting.join_date else None,
                "application_deadline": posting.application_deadline.isoformat()
                if posting.application_deadline else None,
                "requirements": posting.requirements,
                "certificates_required": posting.certificates_required,
                "match_score": score,
                "breakdown": base["breakdown"],
            }
        )
    results.sort(key=lambda r: r["match_score"], reverse=True)
    return results
