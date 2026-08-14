from datetime import date, timedelta
import re

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_staff_read, require_roles
from app.core.config import get_settings
from app.db.database import get_db
from app.models.user import User
from app.models.assignment import ShipCrewAssignment
from app.models.contract import Contract
from app.models.crew_member import CrewMember
from app.models.document import Document
from app.schemas.crew_member import CrewMemberCreate, CrewMemberResponse, CrewMemberUpdate
from app.services.audit import log_event
from app.services.document_processing import document_expiry_status


router = APIRouter(prefix="/api/crew", tags=["Crew"])


def get_crew_member_or_404(crew_member_id: int, db: Session) -> CrewMember:
    crew_member = db.get(CrewMember, crew_member_id)
    if crew_member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew member not found.")
    return crew_member


def _mask_sensitive(value: str | None) -> str | None:
    """Pasaport / seaman book numaralarını viewer & crew'den gizler (örn. AB12****34)."""
    if not value:
        return value
    text = str(value)
    if len(text) <= 6:
        return text[:2] + "***"
    return text[:2] + "*" * (len(text) - 4) + text[-2:]


def serialize_crew(crew_member: CrewMember, role: str) -> dict:
    """CrewMember'ı yanıt dict'ine çevirir; hassas alanları rol dışındakilerden gizler.

    admin / hr tam görür; viewer ve crew için passport_number ve
    seaman_book_number maskelenir.
    """
    data = CrewMemberResponse.model_validate(crew_member).model_dump()
    if role not in ("admin", "hr"):
        data["passport_number"] = _mask_sensitive(crew_member.passport_number)
        data["seaman_book_number"] = _mask_sensitive(crew_member.seaman_book_number)
    return data


@router.post("/", response_model=CrewMemberResponse, status_code=status.HTTP_201_CREATED)
def create_crew_member(
    member: CrewMemberCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    crew_member = CrewMember(**member.model_dump())
    try:
        db.add(crew_member)
        db.flush()
        log_event(db, "crew_created", "crew_member", crew_member.id,
                  f"Crew member created: {crew_member.first_name} {crew_member.last_name}",
                  user_email=actor.email)
        db.commit()
        db.refresh(crew_member)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Crew member conflicts with an existing record.") from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Crew member could not be created.") from error
    return crew_member


@router.get("/", response_model=list[CrewMemberResponse])
def list_crew_members(
    response: Response,
    # ── Temel metin filtreleri (mevcut) ───────────────────────────────────────
    name: str | None = None,
    surname: str | None = None,
    position: str | None = None,
    nationality: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    ship_id: int | None = Query(default=None, gt=0),
    # ── Yeni: CrewMember alan filtreleri ──────────────────────────────────────
    rank: str | None = Query(default=None, description="Rank/görev kısmi eşleşme (örn. 'Chief')"),
    languages: str | None = Query(default=None, description="Dil kısmi eşleşme (örn. 'English')"),
    experience_years_min: int | None = Query(default=None, ge=0, description="Minimum deneyim yılı"),
    sea_service_months_min: int | None = Query(default=None, ge=0, description="Minimum deniz hizmet ayı"),
    availability: str | None = Query(default=None, description="Müsaitlik durumu: available / on_leave / on_board / not_available"),
    # ── Yeni: Sözleşme filtreleri ─────────────────────────────────────────────
    contract_status: str | None = Query(default=None, description="Sözleşme durumu (örn. 'active', 'expired')"),
    contract_expiring_days: int | None = Query(default=None, ge=1, le=365, description="N gün içinde bitecek aktif sözleşmeler"),
    # ── Yeni: Belge durumu filtreleri ─────────────────────────────────────────
    has_no_documents: bool | None = Query(default=None, description="True → hiç belgesi olmayan personel"),
    show_problematic: bool | None = Query(default=None, description="True → eksik veya süresi geçen/acil belgesi olan personel"),
    # ── Sayfalama ──────────────────────────────────────────────────────────────
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    try:
        query = db.query(CrewMember)

        # ── Temel metin filtreleri ─────────────────────────────────────────────
        if name:
            query = query.filter(CrewMember.first_name.ilike(f"%{name.strip()}%"))
        if surname:
            query = query.filter(CrewMember.last_name.ilike(f"%{surname.strip()}%"))
        if position:
            query = query.filter(CrewMember.position.ilike(f"%{position.strip()}%"))
        if nationality:
            query = query.filter(CrewMember.nationality.ilike(f"%{nationality.strip()}%"))
        if status_filter:
            query = query.filter(CrewMember.status == status_filter.strip())
        if ship_id:
            query = query.join(ShipCrewAssignment).filter(ShipCrewAssignment.ship_id == ship_id).distinct()

        # ── CrewMember alan filtreleri ─────────────────────────────────────────
        if rank:
            query = query.filter(CrewMember.rank.ilike(f"%{rank.strip()}%"))
        if languages:
            query = query.filter(CrewMember.languages.ilike(f"%{languages.strip()}%"))
        if experience_years_min is not None:
            query = query.filter(CrewMember.experience_years >= experience_years_min)
        if sea_service_months_min is not None:
            query = query.filter(CrewMember.sea_service_months >= sea_service_months_min)
        if availability:
            query = query.filter(CrewMember.availability == availability.strip())

        # ── Sözleşme filtreleri ────────────────────────────────────────────────
        if contract_status:
            query = (
                query
                .join(Contract, Contract.crew_member_id == CrewMember.id)
                .filter(Contract.status == contract_status.strip())
                .distinct()
            )
        if contract_expiring_days is not None:
            today = date.today()
            deadline = today + timedelta(days=contract_expiring_days)
            query = (
                query
                .join(Contract, Contract.crew_member_id == CrewMember.id)
                .filter(
                    Contract.status == "active",
                    Contract.end_date != None,  # noqa: E711
                    Contract.end_date >= today,
                    Contract.end_date <= deadline,
                )
                .distinct()
            )

        # ── Belge durumu filtreleri ────────────────────────────────────────────
        if has_no_documents is True:
            query = (
                query
                .outerjoin(Document, Document.crew_member_id == CrewMember.id)
                .filter(Document.id == None)  # noqa: E711
            )
        elif has_no_documents is False:
            # En az bir belgesi olan personel
            query = (
                query
                .join(Document, Document.crew_member_id == CrewMember.id)
                .distinct()
            )

        # ── Sorunlu personel filtresi (eksik veya süresi geçen/acil belge) ────
        if show_problematic is True:
            settings = get_settings()
            today = date.today()
            required_types = {"passport", "seaman_book", "stcw", "medical", "contract"}

            docs_by_crew: dict[int, list[Document]] = {}
            for doc in db.query(Document).all():
                if doc.crew_member_id is not None:
                    docs_by_crew.setdefault(doc.crew_member_id, []).append(doc)

            problematic_ids: list[int] = []
            for crew in db.query(CrewMember).all():
                member_docs = docs_by_crew.get(crew.id, [])
                doc_types = {doc.document_type for doc in member_docs}
                missing_required = bool(required_types - doc_types)
                has_issue = any(
                    document_expiry_status(
                        doc.expiry_date,
                        today,
                        settings.expiry_urgent_days,
                        settings.expiry_approaching_days,
                    )
                    in {"expired", "urgent"}
                    for doc in member_docs
                )
                if missing_required or has_issue:
                    problematic_ids.append(crew.id)

            if problematic_ids:
                query = query.filter(CrewMember.id.in_(problematic_ids))
            else:
                query = query.filter(CrewMember.id.in_([-1]))

        # Total count before pagination so the frontend can render accurate
        # totals and pagination controls (X-Total-Count header).
        total_count = query.count()
        response.headers["X-Total-Count"] = str(total_count)

        members = query.order_by(CrewMember.id).offset(offset).limit(limit).all()
        return [serialize_crew(member, current_user.role) for member in members]

    except SQLAlchemyError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Crew members are temporarily unavailable.") from error



@router.get("/{crew_member_id:int}", response_model=CrewMemberResponse)
def get_crew_member(
    crew_member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    crew_member = get_crew_member_or_404(crew_member_id, db)
    return serialize_crew(crew_member, current_user.role)


@router.put("/{crew_member_id:int}", response_model=CrewMemberResponse)
def update_crew_member(
    crew_member_id: int,
    member: CrewMemberUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    crew_member = get_crew_member_or_404(crew_member_id, db)
    for field_name, value in member.model_dump(exclude_unset=True).items():
        setattr(crew_member, field_name, value)
    try:
        log_event(db, "crew_updated", "crew_member", crew_member.id,
                  f"Crew member updated: {crew_member.first_name} {crew_member.last_name}",
                  user_email=actor.email)
        db.commit()
        db.refresh(crew_member)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Crew member conflicts with an existing record.") from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Crew member could not be updated.") from error
    return serialize_crew(crew_member, actor.role)


@router.delete("/{crew_member_id:int}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crew_member(
    crew_member_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    crew_member = get_crew_member_or_404(crew_member_id, db)
    crew_member_id_val = crew_member.id
    name = f"{crew_member.first_name} {crew_member.last_name}"
    try:
        db.delete(crew_member)
        log_event(db, "crew_deleted", "crew_member", crew_member_id_val,
                  f"Crew member deleted: {name}",
                  user_email=actor.email)
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Crew member has related records and cannot be deleted.") from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Crew member could not be deleted.") from error


# ── UYGUNLUK MOTORU (Eligibility) ────────────────────────────────────────────


@router.get("/eligible", response_model=list[dict])
def eligible_crew_members(
    position: str = Query(..., min_length=1),
    min_score: int = Query(default=50, ge=0, le=100),
    limit: int = Query(default=25, ge=1, le=200),
    ship_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    """İstenen pozisyon için en uygun aktif personelleri skorlar."""
    from app.services.eligibility import find_eligible

    return find_eligible(db, position, min_score=min_score, limit=limit, ship_id=ship_id)


# ── CSV EXPORT / IMPORT ──────────────────────────────────────────────────────


@router.get("/export", response_class=Response)
def export_crew_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    """Tüm personeli CSV olarak dışa aktarır (Excel ile açılabilir)."""
    import csv
    import io

    crew = db.query(CrewMember).order_by(CrewMember.id).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "id", "first_name", "last_name", "position", "rank", "nationality",
        "date_of_birth", "passport_number", "seaman_book_number", "phone",
        "email", "availability", "experience_years", "sea_service_months",
        "languages", "address", "status",
    ])
    for c in crew:
        writer.writerow([
            c.id, c.first_name, c.last_name, c.position, c.rank or "", c.nationality or "",
            c.date_of_birth.isoformat() if c.date_of_birth else "", c.passport_number or "",
            c.seaman_book_number or "", c.phone or "", c.email or "",
            c.availability or "", c.experience_years or "", c.sea_service_months or "",
            c.languages or "", c.address or "", c.status,
        ])
    return Response(
        content="\ufeff" + buffer.getvalue(),  # BOM: Excel Türkçe karakter desteği
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="crew_export.csv"'},
    )


class CrewImportPreview(BaseModel):
    rows: list[dict]
    total: int
    new_count: int
    existing_count: int
    conflict_count: int
    sample_conflicts: list[dict]
    error_count: int = 0


def _valid_email(value: str | None) -> bool:
    """CSV satırındaki e-posta formatını doğrular (boş değer geçerli)."""
    if not value:
        return True
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value.strip()))


@router.post("/import/preview", response_model=CrewImportPreview)
def preview_crew_import(
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
    body: dict | None = None,
):
    """CSV içeriğini analiz eder: yeni / mevcut / çakışma sayıları.

    Body: {"content": "csv-metin"}  (Excel'den 'Virgülle Ayrılmış' ile kopyalanabilir)
    """
    import csv
    import io

    if body is None or not body.get("content"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV content is required.")
    try:
        reader = csv.DictReader(io.StringIO(body["content"]))
        rows = list(reader)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid CSV: {exc}") from exc

    normalized: list[dict] = []
    existing_keys = {
        (c.first_name.lower(), c.last_name.lower()): c
        for c in db.query(CrewMember).all()
    }
    new_count = 0
    existing_count = 0
    conflict_count = 0
    error_count = 0
    sample_conflicts: list[dict] = []

    for row in rows:
        first = (row.get("first_name") or "").strip()
        last = (row.get("last_name") or "").strip()
        position = (row.get("position") or "").strip()
        raw_email = (row.get("email") or "").strip().lower()
        # Geçersiz e-posta içeren satırları hatalı say, DB'ye girmesine izin verme
        if not _valid_email(raw_email):
            error_count += 1
            continue
        if not first or not last:
            continue
        item = {
            "first_name": first,
            "last_name": last,
            "position": position,
            "rank": (row.get("rank") or "").strip(),
            "nationality": (row.get("nationality") or "").strip(),
            "phone": (row.get("phone") or "").strip(),
            "email": raw_email,
            "availability": (row.get("availability") or "available").strip(),
            "experience_years": _parse_int(row.get("experience_years")),
        }
        key = (first.lower(), last.lower())
        if key in existing_keys:
            existing_count += 1
            existing = existing_keys[key]
            if (existing.email or "").lower() and item["email"] and existing.email.lower() != item["email"]:
                conflict_count += 1
                if len(sample_conflicts) < 5:
                    sample_conflicts.append({"row": item, "existing_email": existing.email})
        else:
            new_count += 1
        normalized.append(item)

    return CrewImportPreview(
        rows=normalized,
        total=len(normalized),
        new_count=new_count,
        existing_count=existing_count,
        conflict_count=conflict_count,
        sample_conflicts=sample_conflicts,
        error_count=error_count,
    )


def _parse_int(value: str | int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    value = str(value).strip()
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


@router.post("/import/confirm", response_model=dict)
def confirm_crew_import(
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
    body: dict | None = None,
):
    """Önizlemeden gelen satırları içe aktarır (sadece yenileri; mevcutları güncellemez)."""
    if body is None or not body.get("rows"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="rows are required.")
    existing = {
        (c.first_name.lower(), c.last_name.lower())
        for c in db.query(CrewMember).all()
    }
    created = 0
    for row in body["rows"]:
        first = (row.get("first_name") or "").strip()
        last = (row.get("last_name") or "").strip()
        if (first.lower(), last.lower()) in existing:
            continue
        # Geçersiz e-posta satırlarını atla (önizleme de bunları error_count olarak sayar)
        raw_email = (row.get("email") or "").strip().lower()
        if not _valid_email(raw_email):
            continue
        crew = CrewMember(
            first_name=first,
            last_name=last,
            position=(row.get("position") or "Gemici").strip() or "Gemici",
            rank=(row.get("rank") or "").strip() or None,
            nationality=(row.get("nationality") or "").strip() or None,
            phone=(row.get("phone") or "").strip() or None,
            email=raw_email or None,
            availability=(row.get("availability") or "available").strip(),
            experience_years=_parse_int(row.get("experience_years")),
        )
        db.add(crew)
        db.flush()
        log_event(db, "crew_imported", "crew_member", crew.id,
                  f"Crew imported via CSV: {crew.first_name} {crew.last_name}",
                  user_email=actor.email)
        existing.add((first.lower(), last.lower()))
        created += 1
    log_event(db, "crew_bulk_import", "crew_member", None,
              f"Bulk CSV import: {created} crew member(s) created.",
              user_email=actor.email)
    db.commit()
    return {"created": created}
