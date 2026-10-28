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
from app.services.document_processing import extract_metadata, extract_text
from app.services.document_service import store_document_file, validate_upload

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

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dosya adı gerekli.")
    content = await file.read()
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Dosya boyutu çok büyük.")
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Boş dosya yüklenemez.")

    # Personel de yönetici ile aynı formatları yükleyebilir (PDF, DOCX, XLSX,
    # resim…). Uzantı/içerik uyuşmazlığında uzantı düzeltilir.
    filename = validate_upload(file.filename, content)

    path, stored_name, checksum = store_document_file(settings.storage_path, filename, content)

    # Aynı belge (aynı içerik) ikinci kez yüklenirse DB'deki checksum unique
    # kısıtı IntegrityError üretip uç 500 dönüyordu. Burada anlaşılır bir
    # mesajla 409 dönüyor ve boşuna yazılan dosya temizleniyor.
    duplicate = db.query(Document).filter(Document.checksum == checksum).first()
    if duplicate is not None:
        try:
            from pathlib import Path as _Path

            _Path(path).unlink(missing_ok=True)
        except OSError:
            pass
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Bu belge daha önce yüklenmiş (aynı içerik). "
                f"Mevcut kayıt: {duplicate.original_filename}"
            ),
        )

    text = extract_text(filename, content) or ""
    metadata = extract_metadata(filename, text)
    doc_type = metadata.get("document_type") or "other"

    document = Document(
        crew_member_id=crew.id,
        original_filename=filename,
        stored_filename=stored_name,
        storage_path=path,
        mime_type="application/pdf" if stored_name.lower().endswith(".pdf") else file.content_type,
        file_size=len(content),
        checksum=checksum,
        document_type=doc_type,
        document_number=(
            metadata.get("passport_number") or metadata.get("seaman_book_number")
        ),
        match_status="pending_approval",
        match_confidence=0,
        extracted_text=text[:20000] or None,
        source="crew_upload",
    )
    db.add(document)
    db.flush()
    log_event(db, "crew_document_uploaded", "document", document.id,
              f"{crew.first_name} {crew.last_name} belge yükledi (onay bekliyor): {filename}",
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
    from app.services.eligibility import score_crew

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


# NOT: `/jobs/{job_id}` rotası `/jobs/recommended` ve `/applications` gibi sabit
# yolları gölgelememesi için en sonda tanımlanır (FastAPI tanım sırasına uyar).
@router.get("/jobs/{job_id}")
def portal_job_detail(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tek ilan detayı (mobil) — kendi başvuru durumuyla birlikte."""
    from app.models.job import JobApplication, JobPosting

    crew = _require_crew_user(current_user, db)
    posting = db.get(JobPosting, job_id)
    if posting is None or posting.status not in ("open", "published"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="İlan bulunamadı.")

    application = (
        db.query(JobApplication)
        .filter(
            JobApplication.job_posting_id == job_id,
            JobApplication.crew_member_id == crew.id,
        )
        .first()
    )
    return {
        "id": posting.id,
        "title": posting.title,
        "position": posting.position,
        "ship_name": posting.ship.name if posting.ship else None,
        "vessel_type": posting.vessel_type,
        "flag": posting.flag,
        "location": posting.location,
        "salary": posting.salary,
        "currency": posting.currency,
        "salary_period": posting.salary_period,
        "contract_duration": posting.contract_duration,
        "join_date": posting.join_date.isoformat() if posting.join_date else None,
        "application_deadline": posting.application_deadline.isoformat()
        if posting.application_deadline else None,
        "description": posting.description,
        "duties": posting.duties,
        "requirements": posting.requirements,
        "certificates_required": posting.certificates_required,
        "experience_required": posting.experience_required,
        "languages_required": posting.languages_required,
        "contact_info": posting.contact_info,
        "status": posting.status,
        "has_applied": application is not None,
        "application_status": application.status if application else None,
        "match_score": application.match_score if application else None,
        "image_url": f"/api/jobs/{posting.id}/image",
    }


# ── Bildirimler (portal) ──────────────────────────────────────────────────────
# Yönetim ucu (/api/notifications) staff rollerine aittir; personel kendi
# bildirimlerini buradan okur. Sorgu yalnızca kullanıcıya ait + genel
# (user_id NULL) kayıtları döndürür, böylece başka bir kullanıcının
# bildirimi sızmaz.


def _serialize_portal_notification(notification) -> dict:
    return {
        "id": notification.id,
        "title": notification.title,
        "message": notification.message,
        "channel": notification.channel,
        "status": notification.status,
        "entity_type": notification.entity_type,
        "entity_id": notification.entity_id,
        "link": notification.link,
        "read": notification.read_at is not None,
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
    }


@router.get("/notifications")
def portal_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    unread_only: bool = False,
):
    """Personelin kendi bildirimleri (mobil)."""
    from app.models.notification import Notification

    _require_crew_user(current_user, db)
    query = db.query(Notification).filter(
        (Notification.user_id == current_user.id) | (Notification.user_id.is_(None))
    )
    if unread_only:
        query = query.filter(Notification.read_at.is_(None))
    rows = query.order_by(Notification.created_at.desc()).limit(100).all()

    # Eski kayıtlarda belge/kontrat uyarıları user_id olmadan (genel) üretilmişti.
    # Bu kayıtlar başka personelin belge durumunu gösterdiği için portaldan
    # çıkarılır; yalnızca kendi belge/kontratına ait olanlar gösterilir.
    own_document_ids: set[int] = set()
    own_contract_ids: set[int] = set()
    if current_user.crew_member_id:
        from app.models.contract import Contract
        from app.models.document import Document

        own_document_ids = {
            row[0]
            for row in db.query(Document.id).filter(
                Document.crew_member_id == current_user.crew_member_id
            )
        }
        own_contract_ids = {
            row[0]
            for row in db.query(Contract.id).filter(
                Contract.crew_member_id == current_user.crew_member_id
            )
        }

    def _visible(notification) -> bool:
        if notification.user_id is not None:
            return True
        if notification.entity_type == "document":
            return notification.entity_id is None or notification.entity_id in own_document_ids
        if notification.entity_type == "contract":
            return notification.entity_id is None or notification.entity_id in own_contract_ids
        return True

    return [
        _serialize_portal_notification(n) for n in rows if _visible(n)
    ]


@router.post("/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def portal_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Personelin kendi bildirimini okundu işaretlemesi."""
    from datetime import UTC, datetime

    from app.models.notification import Notification

    _require_crew_user(current_user, db)
    notification = db.get(Notification, notification_id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bildirim bulunamadı.")
    if notification.user_id is not None and notification.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu bildirim size ait değil.")
    notification.read_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
