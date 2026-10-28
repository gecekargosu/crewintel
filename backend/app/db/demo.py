"""Demo verisi yükleyici (kurulum sonrası ilk bakış için).

Kullanım (Docker içinde, host'ta Python gerekmez):

    docker compose exec -T backend python -m app.db.demo          # yükle
    docker compose exec -T backend python -m app.db.demo --purge  # sil

Yalnızca bu betiğin oluşturduğu kayıtları yükler/siler; gerçek verilere
dokunmaz. Tekrar çalıştırıldığında mükerrer kayıt oluşturmaz.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta

from app.db.database import SessionLocal
from app.models.assignment import ShipCrewAssignment
from app.models.contract import Contract
from app.models.crew_member import CrewMember
from app.models.ship import Ship

DEMO_MARK = "demo-crewintel"

SHIPS = [
    ("MV DEMO STAR", "9000001", "Malta", "Bulk Carrier", "Demo Denizcilik"),
    ("MT DEMO TANKER", "9000002", "Panama", "Tanker", "Demo Denizcilik"),
    ("MV DEMO CONTAINER", "9000003", "Liberya", "Container", "Demo Denizcilik"),
]

CREW = [
    ("Mehmet", "Kaya", "Master", "Captain", "1980-04-12", "+905321112233", "U12345678"),
    ("Ahmet", "Yılmaz", "Chief Officer", "Chief Officer", "1988-09-03", "+905332223344", "U22334455"),
    ("Zeynep", "Kaya", "Second Engineer", "2nd Engineer", "1992-01-22", "+905443334455", "U33445566"),
    ("Ivan", "Petrov", "Able Seaman", "AB", "1995-06-30", "+79001112233", "RU7788990"),
    ("Carlos", "Santos", "Cook", "Cook", "1985-11-17", "+551199887766", "BR5566778"),
    ("Ali", "Veli", "Oiler", "Oiler", "1990-02-08", "+905554445566", "U44556677"),
    ("Raj", "Kumar", "Third Engineer", "3rd Engineer", "1993-07-25", "+919988776655", "IN9988776"),
    ("Ayşe", "Çelik", "Stewardess", "Stewardess", "1997-03-14", "+905665556677", "U66778899"),
]


def seed() -> None:
    db = SessionLocal()
    try:
        today = date.today()
        ships: list[Ship] = []
        for name, imo, flag, stype, company in SHIPS:
            ship = db.query(Ship).filter(Ship.name == name).first()
            if ship is None:
                ship = Ship(name=name, imo_number=imo, flag=flag, ship_type=stype,
                            company=company, status="active")
                db.add(ship)
                db.flush()
            ships.append(ship)

        crew_rows: list[CrewMember] = []
        for first, last, position, rank, dob, phone, passport in CREW:
            # "(DEMO)" eki sayesinde demo kayıtları gerçek personelle
            # karışmaz ve purge güvenle silebilir.
            demo_last = f"{last} (DEMO)"
            person = (
                db.query(CrewMember)
                .filter(CrewMember.first_name == first, CrewMember.last_name == demo_last)
                .first()
            )
            if person is None:
                person = CrewMember(
                    first_name=first,
                    last_name=demo_last,
                    position=position,
                    rank=rank,
                    nationality="Türkiye" if phone.startswith("+90") else None,
                    date_of_birth=date.fromisoformat(dob),
                    phone=phone,
                    email=f"{first.lower()}.{last.lower()}@example.com",
                    passport_number=passport,
                    seaman_book_number=f"SB{passport[-6:]}" if passport else None,
                    experience_years=8,
                    sea_service_months=96,
                    availability="available",
                    profile_data={"seed": DEMO_MARK},
                )
                db.add(person)
                db.flush()
            crew_rows.append(person)

        # Kontratlar (biri yakında bitecek şekilde)
        contract_plan = [
            (crew_rows[0], ships[0], "DEMO-CNT-001", -180, 14),
            (crew_rows[1], ships[0], "DEMO-CNT-002", -90, 120),
            (crew_rows[2], ships[1], "DEMO-CNT-003", -30, 300),
        ]
        for person, ship, number, start_off, end_off in contract_plan:
            exists = db.query(Contract).filter(Contract.contract_number == number).first()
            if exists is None:
                db.add(Contract(
                    crew_member_id=person.id,
                    ship_id=ship.id,
                    contract_number=number,
                    contract_type="Seafarer Employment Agreement",
                    start_date=today + timedelta(days=start_off),
                    end_date=today + timedelta(days=end_off),
                    status="active",
                ))

        # Atamalar
        assign_plan = [
            (ships[0], crew_rows[1], "Chief Officer"),
            (ships[1], crew_rows[3], "Able Seaman"),
        ]
        for ship, person, position in assign_plan:
            exists = (
                db.query(ShipCrewAssignment)
                .filter(
                    ShipCrewAssignment.ship_id == ship.id,
                    ShipCrewAssignment.crew_member_id == person.id,
                )
                .first()
            )
            if exists is None:
                db.add(ShipCrewAssignment(
                    ship_id=ship.id,
                    crew_member_id=person.id,
                    position=position,
                    start_date=today - timedelta(days=45),
                    status="active",
                ))

        db.commit()
        print(f"Demo verisi hazır: {len(ships)} gemi, {len(crew_rows)} personel, "
              f"{len(contract_plan)} kontrat, {len(assign_plan)} atama.")
        print("Panele girip 'Personel' ve 'Gemiler' ekranlarından görebilirsin.")
    finally:
        db.close()


def purge() -> None:
    db = SessionLocal()
    try:
        demo_crew = (
            db.query(CrewMember)
            .filter(CrewMember.profile_data.isnot(None))
            .all()
        )
        demo_ids = [
            c.id for c in demo_crew
            if isinstance(c.profile_data, dict) and c.profile_data.get("seed") == DEMO_MARK
        ]
        removed = 0
        if demo_ids:
            for model in (ShipCrewAssignment, Contract):
                removed += (
                    db.query(model)
                    .filter(model.crew_member_id.in_(demo_ids))
                    .delete(synchronize_session=False)
                )
            removed += (
                db.query(CrewMember)
                .filter(CrewMember.id.in_(demo_ids))
                .delete(synchronize_session=False)
            )
        for name, *_ in SHIPS:
            ship = db.query(Ship).filter(Ship.name == name).first()
            if ship is not None:
                db.query(ShipCrewAssignment).filter(
                    ShipCrewAssignment.ship_id == ship.id
                ).delete(synchronize_session=False)
                db.query(Contract).filter(
                    Contract.ship_id == ship.id
                ).delete(synchronize_session=False)
                db.delete(ship)
                removed += 1
        db.commit()
        print(f"Demo verisi silindi ({removed} kayıt).")
    finally:
        db.close()


if __name__ == "__main__":
    if "--purge" in sys.argv:
        purge()
    else:
        seed()
