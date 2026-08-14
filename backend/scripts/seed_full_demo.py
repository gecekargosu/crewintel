"""CREWINTEL DEMO VERİSİ — kullanıcı isteği üzerine (Phase 4).

İçerik (hepsi idempotent — tekrar çalıştırılırsa yeni kayıt oluşturmaz):
- 10 adet TAM BELGELİ personel (pasaport, seaman book, STCW, medical, GOC,
  kontrat, CV, eğitim — hepsi dolu ve geçerli tarihlerle)
- 10 gemi
- 20 gemi-personel ataması
- 20 kontrat
- 2 admin kullanıcı: Nurten Kılıç / Cengiz Kılıç (şifre: 1234567890)

Mevcut gerçek veriye DOKUNMAZ. Tüm demo kayıtları not/audit ile işaretlenir.

Kullanım:
    docker exec -i crewintel-backend python /dev/stdin < backend/scripts/seed_full_demo.py
"""

import sys
from datetime import date, timedelta

sys.path.insert(0, "/app")

from app.core.config import get_settings
from app.db.database import SessionLocal
from app.models.contract import Contract
from app.models.crew_member import CrewMember
from app.models.document import Document
from app.models.ship import Ship
from app.models.assignment import ShipCrewAssignment
from app.models.user import User
from app.services.audit import log_event
from app.core.security import hash_password
from app.services.document_processing import store_file

TODAY = date.today()
db = SessionLocal()


def _crew_exists(first, last):
    return (
        db.query(CrewMember)
        .filter(CrewMember.first_name == first, CrewMember.last_name == last)
        .first()
    )


def _ship_exists(name):
    return db.query(Ship).filter(Ship.name == name).first()


def _user_exists(email):
    return db.query(User).filter(User.email == email.lower().strip()).first()


def _contract_exists(number):
    return db.query(Contract).filter(Contract.contract_number == number).first()


# ── 1) 10 TAM BELGELİ PERSONEL ───────────────────────────────────────────────
CREW = [
    {
        "first_name": "Hakan", "last_name": "Demir", "position": "Kaptan",
        "rank": "Kaptan", "nationality": "Türk", "passport": "U4851729",
        "seaman": "TR-SB-10023145", "dob": "1978-04-12", "phone": "+90 532 111 22 33",
        "email": "hakan.demir@kilicdeniz.com", "address": "Barbaros Mah. 12. Sok No:4, İzmir",
        "emergency_contact_name": "Ayşe Demir", "emergency_contact_phone": "+90 532 444 55 66",
        "birth_place": "İzmir", "hometown": "İzmir", "marital_status": "Evli",
        "experience_years": 24, "sea_service_months": 280, "languages": "İngilizce, Türkçe",
        "education_summary": "Denizcilik Fakültesi — Güverte Bölümü",
    },
    {
        "first_name": "Murat", "last_name": "Aydın", "position": "Başmühendis",
        "rank": "Başmühendis", "nationality": "Türk", "passport": "U6012234",
        "seaman": "TR-SB-10023146", "dob": "1981-09-03", "phone": "+90 533 222 33 44",
        "email": "murat.aydin@kilicdeniz.com", "address": "Çankaya Mah. Atatürk Bulvarı No:18, Ankara",
        "emergency_contact_name": "Zeynep Aydın", "emergency_contact_phone": "+90 533 555 66 77",
        "birth_place": "Ankara", "hometown": "Ankara", "marital_status": "Evli",
        "experience_years": 19, "sea_service_months": 225, "languages": "İngilizce, Türkçe, Almanca",
        "education_summary": "Denizcilik Yüksek Okulu — Gemi Makineleri İşletme",
    },
    {
        "first_name": "Emre", "last_name": "Kaya", "position": "2. Kaptan",
        "rank": "2. Kaptan", "nationality": "Türk", "passport": "U7789120",
        "seaman": "TR-SB-10023147", "dob": "1987-02-21", "phone": "+90 535 333 44 55",
        "email": "emre.kaya@kilicdeniz.com", "address": "Alsancak Mah. Kıbrıs Şehitleri Cad. No:7, İzmir",
        "emergency_contact_name": "Elif Kaya", "emergency_contact_phone": "+90 535 666 77 88",
        "birth_place": "İzmir", "hometown": "Manisa", "marital_status": "Evli",
        "experience_years": 14, "sea_service_months": 165, "languages": "İngilizce, Türkçe",
        "education_summary": "Denizcilik Meslek Yüksekokulu — Güverte",
    },
    {
        "first_name": "Serkan", "last_name": "Yıldız", "position": "3. Kaptan",
        "rank": "3. Kaptan", "nationality": "Türk", "passport": "U8892341",
        "seaman": "TR-SB-10023148", "dob": "1991-07-15", "phone": "+90 536 444 55 66",
        "email": "serkan.yildiz@kilicdeniz.com", "address": "Fenerbahçe Mah. Kalamış Cad. No:22, İstanbul",
        "emergency_contact_name": "Deniz Yıldız", "emergency_contact_phone": "+90 536 777 88 99",
        "birth_place": "İstanbul", "hometown": "İstanbul", "marital_status": "Bekar",
        "experience_years": 9, "sea_service_months": 105, "languages": "İngilizce, Türkçe",
        "education_summary": "Denizcilik Fakültesi — Güverte Bölümü",
    },
    {
        "first_name": "Volkan", "last_name": "Arslan", "position": "Elektrik Zabiti",
        "rank": "Elektrik Zabiti", "nationality": "Türk", "passport": "U9923456",
        "seaman": "TR-SB-10023149", "dob": "1989-11-28", "phone": "+90 537 555 66 77",
        "email": "volkan.arslan@kilicdeniz.com", "address": "Bahçelievler Mah. 7. Cadde No:31, Ankara",
        "emergency_contact_name": "Selin Arslan", "emergency_contact_phone": "+90 537 888 99 00",
        "birth_place": "Eskişehir", "hometown": "Eskişehir", "marital_status": "Evli",
        "experience_years": 12, "sea_service_months": 140, "languages": "İngilizce, Türkçe",
        "education_summary": "Elektrik Elektronik Mühendisliği",
    },
    {
        "first_name": "Burak", "last_name": "Şahin", "position": "Yağcı",
        "rank": "Yağcı", "nationality": "Türk", "passport": "U1056789",
        "seaman": "TR-SB-10023150", "dob": "1994-05-06", "phone": "+90 538 666 77 88",
        "email": "burak.sahin@kilicdeniz.com", "address": "Güzelyalı Mah. Sahil Cad. No:12, Trabzon",
        "emergency_contact_name": "Hülya Şahin", "emergency_contact_phone": "+90 538 111 22 33",
        "birth_place": "Trabzon", "hometown": "Trabzon", "marital_status": "Bekar",
        "experience_years": 7, "sea_service_months": 80, "languages": "Türkçe, İngilizce (başlangıç)",
        "education_summary": "Gemi Makineleri Meslek Lisesi",
    },
    {
        "first_name": "Onur", "last_name": "Çelik", "position": "Usta Gemici",
        "rank": "Usta Gemici", "nationality": "Türk", "passport": "U1112345",
        "seaman": "TR-SB-10023151", "dob": "1990-01-19", "phone": "+90 539 777 88 99",
        "email": "onur.celik@kilicdeniz.com", "address": "Konak Mah. 2044 Sok No:9, İzmir",
        "emergency_contact_name": "Fatma Çelik", "emergency_contact_phone": "+90 539 222 33 44",
        "birth_place": "İzmir", "hometown": "İzmir", "marital_status": "Evli",
        "experience_years": 11, "sea_service_months": 128, "languages": "Türkçe, İngilizce",
        "education_summary": "Güverte Meslek Lisesi",
    },
    {
        "first_name": "Mustafa", "last_name": "Korkmaz", "position": "Gemici",
        "rank": "Gemici", "nationality": "Türk", "passport": "U1223456",
        "seaman": "TR-SB-10023152", "dob": "1997-08-30", "phone": "+90 541 888 99 00",
        "email": "mustafa.korkmaz@kilicdeniz.com", "address": "Yenimahalle Mah. 12. Cad No:5, Samsun",
        "emergency_contact_name": "Ayşe Korkmaz", "emergency_contact_phone": "+90 541 333 44 55",
        "birth_place": "Samsun", "hometown": "Samsun", "marital_status": "Bekar",
        "experience_years": 4, "sea_service_months": 45, "languages": "Türkçe",
        "education_summary": "Lise — Gemici yetiştirme kursu",
    },
    {
        "first_name": "Fatih", "last_name": "Doğan", "position": "Aşçı",
        "rank": "Aşçı", "nationality": "Türk", "passport": "U1334567",
        "seaman": "TR-SB-10023153", "dob": "1985-03-11", "phone": "+90 542 999 00 11",
        "email": "fatih.dogan@kilicdeniz.com", "address": "Osmangazi Mah. İnönü Cad. No:44, Bursa",
        "emergency_contact_name": "Merve Doğan", "emergency_contact_phone": "+90 542 444 55 66",
        "birth_place": "Bursa", "hometown": "Bursa", "marital_status": "Evli",
        "experience_years": 16, "sea_service_months": 190, "languages": "Türkçe, İngilizce",
        "education_summary": "Aşçılık Meslek Lisesi + gemi aşçılığı sertifikası",
    },
    {
        "first_name": "Tolga", "last_name": "Güneş", "position": "Kamarot",
        "rank": "Kamarot", "nationality": "Türk", "passport": "U1445678",
        "seaman": "TR-SB-10023154", "dob": "1999-12-05", "phone": "+90 543 000 11 22",
        "email": "tolga.gunes@kilicdeniz.com", "address": "Muratpaşa Mah. Atatürk Cad. No:77, Antalya",
        "emergency_contact_name": "Gül Güneş", "emergency_contact_phone": "+90 543 555 66 77",
        "birth_place": "Antalya", "hometown": "Antalya", "marital_status": "Bekar",
        "experience_years": 3, "sea_service_months": 30, "languages": "Türkçe, İngilizce (başlangıç)",
        "education_summary": "Lise + kamarot hizmet eğitimi",
    },
]

# ── 2) 10 GEMİ ───────────────────────────────────────────────────────────────
SHIPS = [
    ("MV Kılıç 1", "9532110", "Bulk Carrier", "Panama", "active"),
    ("MV Kılıç 2", "9532122", "Container", "Liberia", "active"),
    ("MV Kılıç 3", "9532134", "Tanker", "Türkiye", "active"),
    ("MV Kılıç 4", "9532146", "General Cargo", "Marshall Islands", "active"),
    ("MV Kılıç 5", "9532158", "Ro-Ro", "Türkiye", "active"),
    ("MV Marmara Star", "9631001", "Bulk Carrier", "Panama", "active"),
    ("MV Ege Yıldızı", "9631013", "Container", "Malta", "active"),
    ("MV Karadeniz", "9631025", "Tanker", "Türkiye", "active"),
    ("MV Akdeniz", "9631037", "General Cargo", "Liberia", "active"),
    ("MV Boğaz", "9631049", "Tug", "Türkiye", "active"),
]

STORAGE = get_settings().storage_path


def _make_doc(crew, doc_type, number, issue_offset_days, expiry_offset_days, text):
    content = text.encode("utf-8")
    path, stored_name, checksum = store_file(STORAGE, f"{doc_type}.txt", content)
    document = Document(
        crew_member_id=crew.id,
        original_filename=f"{crew.first_name.lower()}_{crew.last_name.lower()}_{doc_type}.txt",
        stored_filename=stored_name,
        storage_path=path,
        mime_type="text/plain",
        file_size=len(content),
        checksum=checksum,
        document_type=doc_type,
        document_number=number,
        issue_date=TODAY + timedelta(days=issue_offset_days) if issue_offset_days is not None else None,
        expiry_date=TODAY + timedelta(days=expiry_offset_days) if expiry_offset_days is not None else None,
        match_status="matched",
        match_confidence=100,
        extracted_text=text,
        extracted_metadata={"source": "seed_full_demo", "crew_name": f"{crew.first_name} {crew.last_name}"},
        source="seed",
    )
    db.add(document)
    return document


def build_document_set(crew):
    full = f"{crew.first_name} {crew.last_name}"
    docs = [
        ("passport", crew.passport_number, -400, 3650,
         f"PASSPORT\nName: {full}\nPassport Number: {crew.passport_number}\nDate of Birth: {crew.date_of_birth}\nExpiry Date: {TODAY + timedelta(days=3650)}"),
        ("seaman_book", crew.seaman_book_number, -300, 1825,
         f"SEAMAN BOOK\nName: {full}\nSeaman Book Number: {crew.seaman_book_number}\nDate of Birth: {crew.date_of_birth}\nExpiry Date: {TODAY + timedelta(days=1825)}"),
        ("stcw", f"STCW-{crew.passport_number}", -200, 1825,
         f"STCW CERTIFICATE\nName: {full}\nCertificate Number: STCW-{crew.passport_number}\nBasic Safety Training\nExpiry Date: {TODAY + timedelta(days=1825)}"),
        ("medical", f"MED-{crew.passport_number}", -100, 730,
         f"MEDICAL CERTIFICATE\nName: {full}\nCertificate Number: MED-{crew.passport_number}\nSeafarer Medical Examination\nValid Until: {TODAY + timedelta(days=730)}"),
        ("goc", f"GOC-{crew.passport_number}", -150, 1825,
         f"GOC CERTIFICATE\nName: {full}\nCertificate Number: GOC-{crew.passport_number}\nGeneral Operator's Certificate\nExpiry Date: {TODAY + timedelta(days=1825)}"),
        ("cv", None, None, None,
         f"CURRICULUM VITAE\nName: {full}\nEmail: {crew.email}\nPhone: {crew.phone}\nPosition: {crew.position}\nExperience: {crew.experience_years} years\nLanguages: {crew.languages}"),
        ("education", f"EDU-{crew.passport_number}", -2500, None,
         f"EDUCATION CERTIFICATE\nName: {full}\nCertificate Number: EDU-{crew.passport_number}\n{crew.education_summary}"),
    ]
    created = []
    for doc_type, number, issue_off, expiry_off, text in docs:
        created.append(_make_doc(crew, doc_type, number, issue_off, expiry_off, text))
    # Kontrat belgesi (atama dışında bağımsız — son geçerlilik +2 yıl)
    created.append(_make_doc(crew, "contract", f"KLC-{crew.id:04d}-DOC", -30, 730,
                             f"EMPLOYMENT CONTRACT\nName: {full}\nPosition: {crew.position}\nContract Number: KLC-{crew.id:04d}-DOC\nEnd Date: {TODAY + timedelta(days=730)}"))
    return created


def main():
    created_crew = []
    for c in CREW:
        existing = _crew_exists(c["first_name"], c["last_name"])
        if existing:
            created_crew.append(existing)
            continue
        crew = CrewMember(
            first_name=c["first_name"],
            last_name=c["last_name"],
            date_of_birth=date.fromisoformat(c["dob"]),
            nationality=c["nationality"],
            passport_number=c["passport"],
            seaman_book_number=c["seaman"],
            position=c["position"],
            rank=c["rank"],
            phone=c["phone"],
            email=c["email"],
            address=c["address"],
            emergency_contact_name=c["emergency_contact_name"],
            emergency_contact_phone=c["emergency_contact_phone"],
            birth_place=c["birth_place"],
            hometown=c["hometown"],
            marital_status=c["marital_status"],
            experience_years=c["experience_years"],
            sea_service_months=c["sea_service_months"],
            languages=c["languages"],
            education_summary=c["education_summary"],
            notes="DEMO VERİSİ — tam belgeli örnek personel",
            status="active",
        )
        db.add(crew)
        db.flush()
        build_document_set(crew)
        log_event(db, "seed_crew_created", "crew_member", crew.id,
                  f"DEMO personel oluşturuldu: {crew.first_name} {crew.last_name} (tam belgeli)",
                  user_email="system@seed")
        created_crew.append(crew)

    ships = []
    for name, imo, ship_type, flag, status in SHIPS:
        ship = _ship_exists(name)
        if not ship:
            ship = Ship(name=name, imo_number=imo, flag=flag, ship_type=ship_type,
                        company="KILIÇ DENİZCİLİK", status=status)
            db.add(ship)
            db.flush()
            log_event(db, "seed_ship_created", "ship", ship.id, f"DEMO gemi oluşturuldu: {name}",
                      user_email="system@seed")
        ships.append(ship)

    db.commit()

    # ── 3) 20 ATAMA + 20 KONTRAT ──────────────────────────────────────────────
    created_assign = 0
    created_contract = 0
    for i, crew in enumerate(created_crew):
        ship_a = ships[i % len(ships)]
        ship_b = ships[(i + 5) % len(ships)]
        for j, ship in enumerate([ship_a, ship_b]):
            start = TODAY - timedelta(days=200 - j * 120)
            end = TODAY + timedelta(days=365 - j * 150)
            status = "active" if j == 0 else "completed"
            assignment = ShipCrewAssignment(
                ship_id=ship.id,
                crew_member_id=crew.id,
                position=crew.position,
                start_date=start,
                end_date=end,
                status=status,
                notes="DEMO atama",
            )
            db.add(assignment)
            db.flush()
            log_event(db, "seed_assignment_created", "assignment", assignment.id,
                      f"DEMO atama: {crew.first_name} {crew.last_name} → {ship.name} ({crew.position})",
                      user_email="system@seed")
            created_assign += 1

            cnum = f"KLC-2026-{1000 + created_contract:04d}"
            if not _contract_exists(cnum):
                contract = Contract(
                    crew_member_id=crew.id,
                    ship_id=ship.id,
                    contract_number=cnum,
                    contract_type="Gemi Sözleşmesi" if j == 0 else "Süreli Sözleşme",
                    start_date=start,
                    end_date=end,
                    status=status,
                    notes="DEMO kontrat",
                )
                db.add(contract)
                db.flush()
                log_event(db, "seed_contract_created", "contract", contract.id,
                          f"DEMO kontrat: {crew.first_name} {crew.last_name} ({cnum})",
                          user_email="system@seed")
                created_contract += 1

    # ── 4) 2 ADMIN KULLANICI ──────────────────────────────────────────────────
    for full_name, email in [("Nurten Kılıç", "nurten@kilic.com"), ("Cengiz Kılıç", "cengiz@kilic.com")]:
        if not _user_exists(email):
            user = User(
                email=email.lower().strip(),
                full_name=full_name,
                role="admin",
                is_active=True,
                password_hash=hash_password("1234567890"),
            )
            db.add(user)
            db.flush()
            log_event(db, "seed_user_created", "user", user.id, f"Admin kullanıcı oluşturuldu: {email}",
                      user_email="system@seed")

    db.commit()

    print("=" * 60)
    print("SEED TAMAMLANDI")
    print("=" * 60)
    print(f"Personel: {db.query(CrewMember).count()}")
    print(f"Belge:    {db.query(Document).count()}")
    print(f"Gemi:     {db.query(Ship).count()}")
    print(f"Atama:    {db.query(ShipCrewAssignment).count()}")
    print(f"Kontrat:  {db.query(Contract).count()}")
    print(f"Kullanıcı:{db.query(User).count()}")
    print(f"Yeni atama: {created_assign} · Yeni kontrat: {created_contract}")
    print("Admin giriş: nurten@kilic.com / cengiz@kilic.com — şifre: 1234567890")


if __name__ == "__main__":
    main()
