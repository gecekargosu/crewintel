from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_staff_read
from app.db.database import get_db
from app.models.contract import Contract
from app.models.crew_member import CrewMember
from app.models.document import Document
from app.models.ship import Ship
from app.models.ship_position import ShipPosition
from app.models.assignment import ShipCrewAssignment
from app.models.user import User


router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    """Operasyon Merkezi: bugünün işleri ve gemi durumu özeti."""
    today = date.today()

    # Belge durumları
    total_docs = db.query(Document).count()
    expired_docs = db.query(Document).filter(Document.expiry_date.isnot(None), Document.expiry_date < today).count()
    urgent_docs = db.query(Document).filter(
        Document.expiry_date.isnot(None),
        Document.expiry_date >= today,
        Document.expiry_date <= today + timedelta(days=30),
    ).count()
    approaching_docs = db.query(Document).filter(
        Document.expiry_date.isnot(None),
        Document.expiry_date > today + timedelta(days=30),
        Document.expiry_date <= today + timedelta(days=90),
    ).count()
    pending_review = db.query(Document).filter(
        Document.match_status.in_(["review_required", "pending_approval"])
    ).count()

    # Kontratlar
    contracts_ending_7 = (
        db.query(Contract, CrewMember)
        .join(CrewMember, Contract.crew_member_id == CrewMember.id)
        .filter(
            Contract.end_date.isnot(None),
            Contract.end_date >= today,
            Contract.end_date <= today + timedelta(days=7),
            Contract.status == "active",
        )
        .all()
    )
    contracts_ending_30 = (
        db.query(Contract)
        .filter(
            Contract.end_date.isnot(None),
            Contract.end_date >= today,
            Contract.end_date <= today + timedelta(days=30),
            Contract.status == "active",
        )
        .count()
    )

    # Müsaitlik dağılımı
    availability_counts = {
        label: db.query(CrewMember).filter(CrewMember.status == "active", CrewMember.availability == label).count()
        for label in ["available", "on_board", "on_leave", "not_available"]
    }

    # Gemi kadro durumu
    ships = db.query(Ship).all()
    ship_status = []
    total_open_positions = 0
    for ship in ships:
        positions = db.query(ShipPosition).filter(ShipPosition.ship_id == ship.id).all()
        filled_counts = dict(
            db.query(ShipCrewAssignment.position, func.count(ShipCrewAssignment.id))
            .filter(ShipCrewAssignment.ship_id == ship.id, ShipCrewAssignment.status == "active")
            .group_by(ShipCrewAssignment.position)
            .all()
        )
        position_rows = []
        openings = 0
        for pos in positions:
            filled = filled_counts.get(pos.position, 0)
            openings += max(0, pos.required_count - filled)
            position_rows.append({
                "position": pos.position,
                "required": pos.required_count,
                "filled": filled,
                "open": max(0, pos.required_count - filled),
            })
        total_open_positions += openings
        ship_status.append({
            "ship_id": ship.id,
            "name": ship.name,
            "status": ship.status,
            "open_positions": openings,
            "positions": position_rows,
        })

    # Bugünün işleri (Operasyon Merkezi listesi)
    tasks = []
    for contract, crew in contracts_ending_7:
        tasks.append({
            "type": "contract",
            "priority": "red",
            "text": f"{crew.first_name} {crew.last_name} — kontratı {contract.end_date} bitiyor",
            "link": f"/contracts",
            "crew_id": crew.id,
        })
    expired_crew = (
        db.query(Document, CrewMember)
        .join(CrewMember, Document.crew_member_id == CrewMember.id)
        .filter(Document.expiry_date.isnot(None), Document.expiry_date < today, Document.archived_at.is_(None))
        .limit(8)
        .all()
    )
    for doc, crew in expired_crew:
        tasks.append({
            "type": "document",
            "priority": "red",
            "text": f"{crew.first_name} {crew.last_name} — {doc.document_type} belgesi DOLDU",
            "link": f"/documents",
            "crew_id": crew.id,
            "document_type": doc.document_type,
        })
    if pending_review > 0:
        tasks.append({
            "type": "review",
            "priority": "orange",
            "text": f"{pending_review} belge onay/inceleme bekliyor",
            "link": "/documents",
        })
    for ship in ship_status:
        if ship["open_positions"] > 0:
            tasks.append({
                "type": "staffing",
                "priority": "red" if ship["open_positions"] >= 2 else "orange",
                "text": f"{ship['name']} — {ship['open_positions']} pozisyon açığı",
                "link": f"/ship-detail/{ship['ship_id']}",
            })

    return {
        "documents": {
            "total": total_docs,
            "expired": expired_docs,
            "urgent": urgent_docs,
            "approaching": approaching_docs,
            "pending_review": pending_review,
        },
        "contracts": {
            "ending_7_days": len(contracts_ending_7),
            "ending_30_days": contracts_ending_30,
        },
        "availability": availability_counts,
        "ships": {
            "total": len(ships),
            "with_open_positions": sum(1 for s in ship_status if s["open_positions"] > 0),
            "open_positions_total": total_open_positions,
        },
        "ship_status": ship_status,
        "tasks": tasks,
    }
