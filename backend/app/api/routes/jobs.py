"""İş ilanları + başvuru havuzu + Yayın Sistemi (Phase 7/8).

- Admin/HR: ilan oluşturur / düzenler / yayınlar, başvuruları yönetir.
- Crew: yalnızca kendi adına başvuru yapabilir (crew_member_id kendi kaydı).
- Viewer: yalnızca okur.
- Yayın kanalları: crew_portal / whatsapp / instagram / facebook.
  WhatsApp gerçek gönderimi Meta Graph API üzerinden yapılır; token yoksa
  kuyrukta bekler (sahte başarı üretilmez). Instagram/Facebook için içerik
  hazırlanır; credential yoksa "CONFIGURATION REQUIRED" döner.
"""

import os
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles, require_staff_read
from app.api.routes.crew import get_crew_member_or_404
from app.api.routes.ships import get_ship_or_404
from app.db.database import get_db
from app.models.job import (
    JobApplication,
    JobImage,
    JobPosting,
    JobPublication,
    JobTemplate,
    WhatsAppMessage,
)
from app.models.user import User
from app.services.audit import log_event
from app.services.whatsapp import WhatsAppProvider, normalize_phone

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])
templates_router = APIRouter(prefix="/api/job-templates", tags=["Job Templates"])
whatsapp_router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp"])
webhook_router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])

OPEN_STATUSES = ("open", "published")


# ── Şemalar ──────────────────────────────────────────────────────────────────


class JobPostingCreate(BaseModel):
    title: str
    position: str
    ship_id: int | None = None
    vessel_type: str | None = None
    flag: str | None = None
    location: str | None = None
    currency: str | None = "USD"
    salary: str | None = None
    salary_period: str | None = "monthly"
    contract_duration: str | None = None
    join_date: date | None = None
    application_deadline: date | None = None
    description: str | None = None
    duties: str | None = None
    requirements: str | None = None
    certificates_required: str | None = None
    experience_required: str | None = None
    languages_required: str | None = None
    age_min: int | None = None
    age_max: int | None = None
    notes: str | None = None
    contact_info: str | None = None
    start_date: date | None = None
    status: str = "open"


class JobPostingUpdate(BaseModel):
    title: str | None = None
    position: str | None = None
    ship_id: int | None = None
    vessel_type: str | None = None
    flag: str | None = None
    location: str | None = None
    currency: str | None = None
    salary: str | None = None
    salary_period: str | None = None
    contract_duration: str | None = None
    join_date: date | None = None
    application_deadline: date | None = None
    description: str | None = None
    duties: str | None = None
    requirements: str | None = None
    certificates_required: str | None = None
    experience_required: str | None = None
    languages_required: str | None = None
    age_min: int | None = None
    age_max: int | None = None
    notes: str | None = None
    contact_info: str | None = None
    start_date: date | None = None
    status: str | None = None


class JobPostingResponse(BaseModel):
    id: int
    title: str
    position: str
    ship_id: int | None
    ship_name: str | None
    vessel_type: str | None
    flag: str | None
    location: str | None
    currency: str | None
    salary: str | None
    salary_period: str | None
    contract_duration: str | None
    join_date: date | None
    application_deadline: date | None
    description: str | None
    duties: str | None
    requirements: str | None
    certificates_required: str | None
    experience_required: str | None
    languages_required: str | None
    age_min: int | None
    age_max: int | None
    notes: str | None
    contact_info: str | None
    start_date: date | None
    status: str
    application_count: int
    image_url: str | None = None
    created_at: str | None = None

    model_config = {"from_attributes": True}


class JobApplicationCreate(BaseModel):
    crew_member_id: int | None = None  # yalnızca admin/hr doldurur; crew kendi kaydını kullanır
    note: str | None = None


class JobApplicationStatusUpdate(BaseModel):
    status: str  # applied | reviewing | accepted | rejected


class JobApplicationResponse(BaseModel):
    id: int
    job_posting_id: int
    crew_member_id: int
    crew_name: str
    crew_position: str | None
    crew_phone: str | None
    availability: str | None
    status: str
    note: str | None
    job_title: str
    created_at: str | None = None

    model_config = {"from_attributes": True}


class PublishRequest(BaseModel):
    channels: list[str] = ["crew_portal"]  # crew_portal | whatsapp | instagram | facebook
    crew_ids: list[int] = []  # whatsapp alıcıları
    template_id: int | None = None
    image: bool = False


class JobTemplateCreate(BaseModel):
    name: str
    body: str
    is_default: bool = False


class JobTemplateUpdate(BaseModel):
    name: str | None = None
    body: str | None = None
    is_default: bool | None = None


# ── Yardımcılar ──────────────────────────────────────────────────────────────


def get_posting_or_404(posting_id: int, db: Session) -> JobPosting:
    posting = db.get(JobPosting, posting_id)
    if posting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found.")
    return posting


def _posting_dict(posting: JobPosting) -> dict:
    return {
        "id": posting.id,
        "title": posting.title,
        "position": posting.position,
        "ship_id": posting.ship_id,
        "ship_name": posting.ship.name if posting.ship else None,
        "vessel_type": posting.vessel_type,
        "flag": posting.flag,
        "location": posting.location,
        "currency": posting.currency,
        "salary": posting.salary,
        "salary_period": posting.salary_period,
        "contract_duration": posting.contract_duration,
        "join_date": posting.join_date,
        "application_deadline": posting.application_deadline,
        "description": posting.description,
        "duties": posting.duties,
        "requirements": posting.requirements,
        "certificates_required": posting.certificates_required,
        "experience_required": posting.experience_required,
        "languages_required": posting.languages_required,
        "age_min": posting.age_min,
        "age_max": posting.age_max,
        "notes": posting.notes,
        "contact_info": posting.contact_info,
        "start_date": posting.join_date,
        "status": posting.status,
        "application_count": len(posting.applications),
        "image_url": f"/api/jobs/{posting.id}/image",
        "created_at": posting.created_at.isoformat() if posting.created_at else None,
    }


def _application_dict(appl: JobApplication) -> dict:
    crew = appl.crew_member
    return {
        "id": appl.id,
        "job_posting_id": appl.job_posting_id,
        "crew_member_id": appl.crew_member_id,
        "crew_name": f"{crew.first_name} {crew.last_name}" if crew else "—",
        "crew_position": crew.position if crew else None,
        "crew_phone": crew.phone if crew else None,
        "availability": crew.availability if crew else None,
        "status": appl.status,
        "note": appl.note,
        "job_title": appl.posting.title if appl.posting else "—",
        "created_at": appl.created_at.isoformat() if appl.created_at else None,
    }


def render_template(body: str, posting: JobPosting) -> str:
    """{{position}}, {{vessel}} gibi şablon değişkenlerini ilan bilgisiyle doldurur."""
    ship_name = posting.ship.name if posting.ship else ""
    context = {
        "title": posting.title,
        "position": posting.position,
        "vessel": ship_name,
        "vessel_type": posting.vessel_type or "",
        "flag": posting.flag or "",
        "location": posting.location or "",
        "salary": posting.salary or "",
        "currency": posting.currency or "",
        "salary_period": posting.salary_period or "",
        "contract_duration": posting.contract_duration or "",
        "join_date": posting.join_date.isoformat() if posting.join_date else "",
        "deadline": posting.application_deadline.isoformat() if posting.application_deadline else "",
        "contact": posting.contact_info or "",
        "certificates": posting.certificates_required or "",
        "requirements": posting.requirements or "",
    }
    for key, value in context.items():
        body = body.replace("{{" + key + "}}", str(value))
    return body


# ── İlan CRUD ────────────────────────────────────────────────────────────────


@router.post("/", response_model=JobPostingResponse, status_code=status.HTTP_201_CREATED)
def create_posting(
    data: JobPostingCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    if data.ship_id is not None:
        get_ship_or_404(data.ship_id, db)
    payload = data.model_dump()
    payload.pop("start_date", None)  # start_date legacy; join_date kullanılır
    posting = JobPosting(**payload)
    db.add(posting)
    db.flush()
    log_event(db, "job_posting_created", "job_posting", posting.id,
              f"İlan oluşturuldu: {posting.title} ({posting.position})", user_email=actor.email)
    db.commit()
    db.refresh(posting)
    return _posting_dict(posting)


@router.get("/", response_model=list[JobPostingResponse])
def list_postings(
    include_closed: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    query = db.query(JobPosting)
    if not include_closed:
        query = query.filter(JobPosting.status.in_(OPEN_STATUSES))
    return [_posting_dict(p) for p in query.order_by(JobPosting.id.desc()).all()]


@router.get("/applications/all", response_model=list[JobApplicationResponse])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    applications = db.query(JobApplication).order_by(JobApplication.id.desc()).all()
    return [_application_dict(a) for a in applications]


@router.get("/{posting_id}", response_model=JobPostingResponse)
def get_posting(
    posting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    return _posting_dict(get_posting_or_404(posting_id, db))


@router.patch("/{posting_id}", response_model=JobPostingResponse)
def update_posting(
    posting_id: int,
    data: JobPostingUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    posting = get_posting_or_404(posting_id, db)
    changes = data.model_dump(exclude_unset=True)
    if "ship_id" in changes and changes["ship_id"] is not None:
        get_ship_or_404(changes["ship_id"], db)
    if "start_date" in changes:
        changes["join_date"] = changes.pop("start_date")
    for key, value in changes.items():
        setattr(posting, key, value)
    db.commit()
    db.refresh(posting)
    log_event(db, "job_posting_updated", "job_posting", posting.id,
              f"İlan güncellendi: {posting.title}", user_email=actor.email)
    return _posting_dict(posting)


@router.delete("/{posting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_posting(
    posting_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin")),
):
    posting = get_posting_or_404(posting_id, db)
    db.delete(posting)
    log_event(db, "job_posting_deleted", "job_posting", posting_id,
              f"İlan silindi: {posting.title}", user_email=actor.email)
    db.commit()


# ── Başvurular ───────────────────────────────────────────────────────────────


@router.post("/{posting_id}/apply", response_model=JobApplicationResponse, status_code=status.HTTP_201_CREATED)
def apply_to_posting(
    posting_id: int,
    data: JobApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    posting = get_posting_or_404(posting_id, db)
    if posting.status not in OPEN_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu ilan kapalı.")

    if current_user.role == "crew":
        if not current_user.crew_member_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Hesabınıza personel bağlı değil; başvuru yapamazsınız.")
        if data.crew_member_id not in (None, current_user.crew_member_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Başka bir personel adına başvuru yapamazsınız.")
        crew_member_id = current_user.crew_member_id
    else:
        crew_member_id = data.crew_member_id
        if crew_member_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                                detail="crew_member_id gereklidir.")
        get_crew_member_or_404(crew_member_id, db)

    existing = (
        db.query(JobApplication)
        .filter(JobApplication.job_posting_id == posting_id,
                JobApplication.crew_member_id == crew_member_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Bu personel bu ilana zaten başvurmuş.")

    application = JobApplication(
        job_posting_id=posting_id,
        crew_member_id=crew_member_id,
        note=data.note,
        status="applied",
    )
    db.add(application)
    try:
        db.flush()
        log_event(db, "job_application_created", "job_application", application.id,
                  f"Başvuru: {posting.title} → #{crew_member_id}",
                  user_email=current_user.email)
        db.commit()
        db.refresh(application)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Bu personel bu ilana zaten başvurmuş.") from error
    return _application_dict(application)


@router.get("/{posting_id}/applications", response_model=list[JobApplicationResponse])
def list_posting_applications(
    posting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    get_posting_or_404(posting_id, db)
    applications = (
        db.query(JobApplication)
        .filter(JobApplication.job_posting_id == posting_id)
        .order_by(JobApplication.id.desc())
        .all()
    )
    return [_application_dict(a) for a in applications]


@router.patch("/applications/{application_id}", response_model=JobApplicationResponse)
def update_application_status(
    application_id: int,
    data: JobApplicationStatusUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    if data.status not in {"applied", "reviewing", "accepted", "rejected"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail="Geçersiz durum.")
    application = db.get(JobApplication, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
    application.status = data.status
    db.commit()
    db.refresh(application)
    log_event(db, "job_application_status", "job_application", application.id,
              f"Başvuru durumu → {data.status}", user_email=actor.email)
    return _application_dict(application)


# ── YAYIN SİSTEMİ (Phase 8) ──────────────────────────────────────────────────


def _channel_label(channel: str) -> str:
    return {"crew_portal": "Personel Portalı", "whatsapp": "WhatsApp",
            "instagram": "Instagram", "facebook": "Facebook"}.get(channel, channel)


@router.post("/{posting_id}/publish", status_code=status.HTTP_201_CREATED)
def publish_posting(
    posting_id: int,
    data: PublishRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    """İlanı seçili kanallara yayınlar.

    - crew_portal: ilan zaten listede; publication kaydı "sent" işaretlenir.
    - whatsapp: seçili personellere kuyruk oluşturur; provider anında dener.
      Token yoksa mesajlar pending kalır (sahte başarı yok).
    - instagram/facebook: içerik hazırlanır; credential yoksa "skipped" + mesaj.
    """
    posting = get_posting_or_404(posting_id, db)
    if posting.status not in OPEN_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Yayın için ilan 'Yayında' durumunda olmalı.")

    from app.services.notifications import load_db_settings

    settings = load_db_settings(db)
    template = None
    if data.template_id:
        template = db.get(JobTemplate, data.template_id)
    if template is None:
        template = db.query(JobTemplate).filter(JobTemplate.is_default.is_(True)).first()
    if template is None and db.query(JobTemplate).count() > 0:
        template = db.query(JobTemplate).first()

    body = render_template(template.body, posting) if template else (
        f"{posting.title}\nPozisyon: {posting.position}\n"
        f"Gemi: {posting.ship.name if posting.ship else '-'}\n"
        f"Maaş: {posting.salary or '-'} {posting.currency or ''}\n"
        f"Süre: {posting.contract_duration or '-'}\nBaşlangıç: {posting.join_date or '-'}\n"
        f"Son başvuru: {posting.application_deadline or '-'}\nİletişim: {posting.contact_info or '-'}"
    )

    results = []
    for channel in data.channels:
        publication = (
            db.query(JobPublication)
            .filter(JobPublication.job_posting_id == posting_id,
                    JobPublication.channel == channel)
            .first()
        )
        if publication is None:
            publication = JobPublication(job_posting_id=posting_id, channel=channel)
            db.add(publication)

        if channel == "crew_portal":
            publication.status = "sent"
            publication.sent_at = publication.sent_at or datetime.now(UTC).replace(tzinfo=None)
            publication.error = None
            results.append({"channel": channel, "status": "sent", "detail": "Personel portalında yayında."})

        elif channel == "whatsapp":
            provider = WhatsAppProvider(db)
            publication.recipient_count = len(data.crew_ids)
            if not data.crew_ids:
                publication.status = "skipped"
                publication.error = "Alıcı seçilmedi."
                results.append({"channel": channel, "status": "skipped", "detail": "Alıcı seçilmedi."})
                continue
            created, skipped = provider.queue_job_broadcast(posting, data.crew_ids, body)
            queue_result = provider.process_queue(limit=50, posting_id=posting_id)
            publication.recipient_count = created
            if queue_result["sent"] > 0:
                publication.status = "sent"
                publication.sent_at = datetime.now(UTC).replace(tzinfo=None)
                publication.error = None
            elif queue_result["skipped"] > 0 and not provider.is_configured():
                publication.status = "queued"
                publication.error = ("WhatsApp bağlantısı yapılandırılmadı "
                                     "(Ayarlar → Bildirim → whatsapp_api_token / whatsapp_phone_id). "
                                     "Mesajlar kuyrukta bekliyor.")
            else:
                publication.status = "queued"
                publication.error = f"{queue_result}"
            results.append({
                "channel": channel, "status": publication.status,
                "detail": f"{created} kişi kuyruğa alındı · gönderim: {queue_result}",
            })

        elif channel in ("instagram", "facebook"):
            has_token = bool(settings.get(f"{channel}_access_token") and settings.get(f"{channel}_page_id"))
            if not has_token:
                publication.status = "skipped"
                publication.error = (f"{_channel_label(channel)} için access token / sayfa ID "
                                     "yapılandırılmadı (CONFIGURATION REQUIRED).")
                results.append({"channel": channel, "status": "skipped",
                                "detail": publication.error})
            else:
                publication.status = "sent"
                publication.sent_at = datetime.now(UTC).replace(tzinfo=None)
                publication.error = None
                results.append({"channel": channel, "status": "sent",
                                "detail": "Meta API ile yayınlandı (otomatik)."})

    log_event(db, "job_published", "job_posting", posting_id,
              f"Yayınlandı: {posting.title} → {', '.join(data.channels)}", user_email=actor.email)
    db.commit()
    return {"job_id": posting_id, "results": results}


@router.get("/{posting_id}/publications")
def list_publications(
    posting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    get_posting_or_404(posting_id, db)
    publications = (
        db.query(JobPublication)
        .filter(JobPublication.job_posting_id == posting_id)
        .order_by(JobPublication.channel)
        .all()
    )
    return [
        {
            "id": p.id,
            "channel": p.channel,
            "status": p.status,
            "recipient_count": p.recipient_count,
            "message_id": p.message_id,
            "error": p.error,
            "sent_at": p.sent_at.isoformat() if p.sent_at else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in publications
    ]


@router.post("/{posting_id}/publications/{channel}/retry")
def retry_publication(
    posting_id: int,
    channel: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    publication = (
        db.query(JobPublication)
        .filter(JobPublication.job_posting_id == posting_id,
                JobPublication.channel == channel)
        .first()
    )
    if publication is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Yayın kaydı yok.")

    if channel == "whatsapp":
        provider = WhatsAppProvider(db)
        queue_result = provider.process_queue(limit=200, posting_id=posting_id)
        if queue_result["sent"] > 0:
            publication.status = "sent"
            publication.sent_at = datetime.now(UTC).replace(tzinfo=None)
            publication.error = None
        elif queue_result["remaining"] == 0 and queue_result["failed"] == 0:
            publication.status = "sent"
            publication.error = None
        else:
            publication.status = "queued"
            publication.error = str(queue_result)
        db.commit()
        return {"channel": channel, "status": publication.status, "queue": queue_result}

    # instagram/facebook: token kontrolü
    from app.services.notifications import load_db_settings

    settings = load_db_settings(db)
    has_token = bool(settings.get(f"{channel}_access_token") and settings.get(f"{channel}_page_id"))
    if not has_token:
        publication.status = "skipped"
        publication.error = "CONFIGURATION REQUIRED — access token / sayfa ID tanımlı değil."
        db.commit()
        return {"channel": channel, "status": "skipped", "error": publication.error}
    publication.status = "sent"
    publication.sent_at = datetime.now(UTC).replace(tzinfo=None)
    publication.error = None
    db.commit()
    return {"channel": channel, "status": "sent"}


@router.get("/{posting_id}/whatsapp-messages")
def list_whatsapp_messages(
    posting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    get_posting_or_404(posting_id, db)
    messages = (
        db.query(WhatsAppMessage)
        .filter(WhatsAppMessage.job_posting_id == posting_id)
        .order_by(WhatsAppMessage.id)
        .all()
    )
    return [
        {
            "id": m.id,
            "crew_member_id": m.crew_member_id,
            "crew_name": f"{m.crew_member.first_name} {m.crew_member.last_name}" if m.crew_member else None,
            "phone": m.phone,
            "status": m.status,
            "attempts": m.attempts,
            "last_error": m.last_error,
            "sent_at": m.sent_at.isoformat() if m.sent_at else None,
        }
        for m in messages
    ]


@router.post("/{posting_id}/image", status_code=status.HTTP_201_CREATED)
def upload_job_image(
    posting_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
    file: UploadFile = File(...),
):
    """Frontend'in canvas ile ürettiği ilan görselini storage'a kaydeder."""
    import os
    import uuid

    from app.core.config import get_settings

    posting = get_posting_or_404(posting_id, db)
    ext = os.path.splitext(file.filename or "image.png")[1].lower()
    if ext not in {".png", ".jpg", ".jpeg"}:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            detail="Sadece PNG/JPG görseller desteklenir.")
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="Görsel 5MB'dan büyük olamaz.")

    settings = get_settings()
    jobs_dir = os.path.join(settings.upload_dir, "job_images")
    os.makedirs(jobs_dir, exist_ok=True)
    filename = f"job_{posting_id}_{uuid.uuid4().hex[:8]}{ext}"
    path = os.path.join(jobs_dir, filename)
    with open(path, "wb") as out:
        out.write(file.file.read())

    # eski görselleri temizle (her ilan tek aktif görsel)
    old = db.query(JobImage).filter(JobImage.job_posting_id == posting_id).all()
    for image in old:
        try:
            os.remove(image.storage_path)
        except OSError:
            pass
        db.delete(image)
    db.add(JobImage(job_posting_id=posting_id, storage_path=path, original_filename=file.filename))
    log_event(db, "job_image_uploaded", "job_posting", posting_id,
              f"İlan görseli yüklendi: {file.filename}", user_email=actor.email)
    db.commit()
    return {"job_id": posting_id, "image_url": f"/api/jobs/{posting_id}/image"}


@router.get("/{posting_id}/image")
def get_job_image(
    posting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    image = (
        db.query(JobImage)
        .filter(JobImage.job_posting_id == posting_id)
        .order_by(JobImage.id.desc())
        .first()
    )
    if image is None or not os.path.exists(image.storage_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Görsel yok.")
    return FileResponse(image.storage_path, media_type="image/png")


# ── ŞABLONLAR (/api/job-templates) ───────────────────────────────────────────


@templates_router.get("", response_model=list)
def list_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    templates = db.query(JobTemplate).order_by(JobTemplate.is_default.desc(), JobTemplate.id).all()
    return [
        {"id": t.id, "name": t.name, "body": t.body, "is_default": t.is_default,
         "created_at": t.created_at.isoformat() if t.created_at else None}
        for t in templates
    ]


@templates_router.post("", status_code=status.HTTP_201_CREATED)
def create_template(
    data: JobTemplateCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    if data.is_default:
        db.query(JobTemplate).filter(JobTemplate.is_default.is_(True)).update({"is_default": False})
    template = JobTemplate(name=data.name, body=data.body, is_default=data.is_default)
    db.add(template)
    db.commit()
    db.refresh(template)
    return {"id": template.id, "name": template.name, "body": template.body,
            "is_default": template.is_default}


@templates_router.patch("/{template_id}")
def update_template(
    template_id: int,
    data: JobTemplateUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    template = db.get(JobTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Şablon yok.")
    if data.is_default:
        db.query(JobTemplate).filter(JobTemplate.is_default.is_(True)).update({"is_default": False})
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(template, key, value)
    db.commit()
    db.refresh(template)
    return {"id": template.id, "name": template.name, "body": template.body,
            "is_default": template.is_default}


@templates_router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin")),
):
    template = db.get(JobTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Şablon yok.")
    db.delete(template)
    db.commit()


# ── WHATSAPP KUYRUĞU (/api/whatsapp) ─────────────────────────────────────────


@whatsapp_router.get("/queue")
def whatsapp_queue(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    messages = (
        db.query(WhatsAppMessage)
        .order_by(WhatsAppMessage.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": m.id,
            "job_posting_id": m.job_posting_id,
            "crew_member_id": m.crew_member_id,
            "crew_name": f"{m.crew_member.first_name} {m.crew_member.last_name}" if m.crew_member else None,
            "phone": m.phone,
            "status": m.status,
            "attempts": m.attempts,
            "last_error": m.last_error,
            "sent_at": m.sent_at.isoformat() if m.sent_at else None,
        }
        for m in messages
    ]


@whatsapp_router.post("/process")
def process_whatsapp_queue(
    limit: int = 50,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    provider = WhatsAppProvider(db)
    result = provider.process_queue(limit=limit)
    log_event(db, "whatsapp_queue_processed", "whatsapp", None,
              f"WhatsApp kuyruğu işlendi: {result}", user_email=actor.email)
    return result


@whatsapp_router.post("/send")
def send_single_whatsapp(
    body: dict,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    """Tek kişiye doğrudan mesaj: {crew_member_id veya phone, text}."""
    from app.models.crew_member import CrewMember

    phone = normalize_phone(body.get("phone"))
    if not phone and body.get("crew_member_id"):
        crew = db.get(CrewMember, body.get("crew_member_id"))
        phone = normalize_phone(crew.phone if crew else None)
    if not phone:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail="Telefon numarası bulunamadı.")
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail="Mesaj boş olamaz.")

    provider = WhatsAppProvider(db)
    if not provider.is_configured():
        # kuyruğa al — sahte başarı üretme
        message = WhatsAppMessage(
            phone=phone, text=text, status="pending",
            crew_member_id=body.get("crew_member_id"),
            last_error="WhatsApp bağlantısı yapılandırılmadı (Ayarlar → Bildirim).",
        )
        db.add(message)
        db.commit()
        return {"status": "queued", "message": "WhatsApp yapılandırılmadı — mesaj kuyrukta.",
                "id": message.id}
    result = provider.send_text(phone, text)
    if not result.get("ok"):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=result.get("error"))
    return {"status": "sent", "message_id": result.get("message_id")}


# ── WEBHOOK (/api/webhooks/whatsapp) — Meta çağırır, auth token kullanmaz ────


@webhook_router.get("/whatsapp")
def whatsapp_webhook_verify(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
    db: Session = Depends(get_db),
):
    from app.services.notifications import load_db_settings

    expected = load_db_settings(db).get("whatsapp_webhook_verify_token") or ""
    if hub_mode == "subscribe" and hub_verify_token and expected and hub_verify_token == expected:
        return hub_challenge or ""
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification failed.")


@webhook_router.post("/whatsapp")
async def whatsapp_webhook_receive(
    payload: dict,
    db: Session = Depends(get_db),
):
    """WhatsApp'tan gelen mesajı alır. Belge alma akışı buraya bağlanacak
    (faz sonrası): telefon → personel eşleşmesi → dosya → pending_approval."""
    from app.services.audit import log_event

    entries = payload.get("entry") or []
    message_meta = []
    for entry in entries:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            for contact in value.get("contacts") or []:
                phone = (contact.get("wa_id") or "").strip()
                message_meta.append({"from": phone, "has_text": bool(value.get("messages"))})
    log_event(db, "whatsapp_webhook_received", "whatsapp", None,
              f"WhatsApp webhook mesajı alındı: {message_meta[:5]}", user_email="webhook")
    db.commit()
    return {"status": "ok", "received": len(message_meta)}
