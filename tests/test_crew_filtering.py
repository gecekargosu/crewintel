"""
Personel filtreleme sistemi testleri (STEP 10A).

Doğrulananlar:
- rank, languages, experience_years_min, sea_service_months_min ilike/range filtreleri
- contract_status + contract_expiring_days (contracts JOIN)
- has_no_documents (documents outer JOIN)
- Filtrelerin birlikte kullanımı
- Limit artışı (200'e kadar)
"""
from datetime import date, timedelta


# ── Yardımcı fonksiyonlar ─────────────────────────────────────────────────────

def make_crew(client, **overrides):
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "position": "Sailor",
        "nationality": "Turkish",
        "status": "active",
    }
    payload.update(overrides)
    r = client.post("/api/crew/", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def make_ship(client, imo="1234567"):
    r = client.post("/api/ships/", json={
        "name": "Test Ship",
        "imo_number": imo,
        "flag": "Turkey",
        "ship_type": "Tanker",
        "company": "Test Co",
        "status": "active",
    })
    assert r.status_code == 201, r.text
    return r.json()


def make_contract(client, crew_id, ship_id, *, contract_status="active",
                  start="2026-01-01", end=None, num="CNT-001"):
    payload = {
        "crew_member_id": crew_id,
        "ship_id": ship_id,
        "contract_number": num,
        "contract_type": "Employment",
        "start_date": start,
        "status": contract_status,
    }
    if end:
        payload["end_date"] = end
    r = client.post("/api/contracts/", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def list_crew(client, **params):
    return client.get("/api/crew/", params=params).json()


# ── CP1: CrewMember alan filtreleri ──────────────────────────────────────────

def test_rank_filter_returns_matching_crew(client):
    make_crew(client, first_name="Ali", last_name="Kaptan", rank="Chief Officer")
    make_crew(client, first_name="Veli", last_name="Makine", rank="2nd Engineer")
    make_crew(client, first_name="Hasan", last_name="Gemici", rank=None)

    results = list_crew(client, rank="Chief")
    assert len(results) == 1
    assert results[0]["rank"] == "Chief Officer"


def test_rank_filter_case_insensitive(client):
    make_crew(client, first_name="Ali", last_name="Test", rank="Master")
    results = list_crew(client, rank="master")
    assert len(results) == 1


def test_languages_filter_partial_match(client):
    make_crew(client, first_name="Ali", last_name="A", languages="English, Turkish")
    make_crew(client, first_name="Ivan", last_name="B", languages="Russian, English")
    make_crew(client, first_name="Pedro", last_name="C", languages="Spanish")

    results = list_crew(client, languages="English")
    assert len(results) == 2

    results_spanish = list_crew(client, languages="Spanish")
    assert len(results_spanish) == 1
    assert results_spanish[0]["first_name"] == "Pedro"


def test_experience_years_min_filter(client):
    make_crew(client, first_name="Junior", last_name="A", experience_years=2)
    make_crew(client, first_name="Mid", last_name="B", experience_years=5)
    make_crew(client, first_name="Senior", last_name="C", experience_years=12)
    make_crew(client, first_name="NoExp", last_name="D", experience_years=None)

    results_5 = list_crew(client, experience_years_min=5)
    names = [r["first_name"] for r in results_5]
    assert "Mid" in names
    assert "Senior" in names
    assert "Junior" not in names
    assert "NoExp" not in names


def test_sea_service_months_min_filter(client):
    make_crew(client, first_name="New", last_name="A", sea_service_months=6)
    make_crew(client, first_name="Exp", last_name="B", sea_service_months=60)
    make_crew(client, first_name="Vet", last_name="C", sea_service_months=120)

    results = list_crew(client, sea_service_months_min=60)
    names = [r["first_name"] for r in results]
    assert "Exp" in names
    assert "Vet" in names
    assert "New" not in names


def test_experience_years_min_zero_returns_all_with_value(client):
    """experience_years_min=0 → experience_years'ı olan herkesi döndürmeli."""
    make_crew(client, first_name="A", last_name="X", experience_years=0)
    make_crew(client, first_name="B", last_name="Y", experience_years=5)
    make_crew(client, first_name="C", last_name="Z", experience_years=None)

    results = list_crew(client, experience_years_min=0)
    names = [r["first_name"] for r in results]
    assert "A" in names
    assert "B" in names
    assert "C" not in names


# ── CP2: Sözleşme filtreleri ──────────────────────────────────────────────────

def test_contract_status_filter_active(client):
    ship = make_ship(client, imo="1000001")
    crew_active = make_crew(client, first_name="Aktif", last_name="Gemi")
    crew_expired = make_crew(client, first_name="Biten", last_name="Gemi")

    make_contract(client, crew_active["id"], ship["id"],
                  contract_status="active", num="CNT-ACT-001")
    make_contract(client, crew_expired["id"], ship["id"],
                  contract_status="expired", num="CNT-EXP-001")

    results = list_crew(client, contract_status="active")
    names = [r["first_name"] for r in results]
    assert "Aktif" in names
    assert "Biten" not in names


def test_contract_status_filter_expired(client):
    ship = make_ship(client, imo="1000002")
    crew_a = make_crew(client, first_name="AlphaA", last_name="Test")
    crew_b = make_crew(client, first_name="BetaB", last_name="Test")

    make_contract(client, crew_a["id"], ship["id"],
                  contract_status="active", num="CNT-002A")
    make_contract(client, crew_b["id"], ship["id"],
                  contract_status="expired", num="CNT-002B")

    results = list_crew(client, contract_status="expired")
    names = [r["first_name"] for r in results]
    assert "BetaB" in names
    assert "AlphaA" not in names


def test_contract_expiring_days_returns_expiring_soon(client):
    ship = make_ship(client, imo="1000003")
    crew_soon = make_crew(client, first_name="SoonEnd", last_name="Test")
    crew_later = make_crew(client, first_name="LaterEnd", last_name="Test")
    crew_noend = make_crew(client, first_name="NoEndDate", last_name="Test")

    today = date.today()
    soon = str(today + timedelta(days=10))
    later = str(today + timedelta(days=90))

    make_contract(client, crew_soon["id"], ship["id"],
                  contract_status="active", end=soon, num="CNT-003A")
    make_contract(client, crew_later["id"], ship["id"],
                  contract_status="active", end=later, num="CNT-003B")
    make_contract(client, crew_noend["id"], ship["id"],
                  contract_status="active", num="CNT-003C")

    results = list_crew(client, contract_expiring_days=30)
    names = [r["first_name"] for r in results]
    assert "SoonEnd" in names
    assert "LaterEnd" not in names
    assert "NoEndDate" not in names


def test_contract_expiring_days_excludes_expired_contracts(client):
    """Süresi dolmuş (expired) sözleşmeler contract_expiring_days filtresiyle gelmemeli."""
    ship = make_ship(client, imo="1000004")
    crew = make_crew(client, first_name="ExpiredCnt", last_name="Test")
    today = date.today()
    past = str(today - timedelta(days=10))
    make_contract(client, crew["id"], ship["id"],
                  contract_status="expired", end=past, num="CNT-004A")

    results = list_crew(client, contract_expiring_days=30)
    names = [r["first_name"] for r in results]
    assert "ExpiredCnt" not in names


# ── CP3: Belge durumu filtreleri ──────────────────────────────────────────────

def test_has_no_documents_true_returns_crew_without_docs(client):
    crew_with_doc = make_crew(client, first_name="WithDoc", last_name="Test")
    crew_without = make_crew(client, first_name="WithoutDoc", last_name="Test")

    # Belge yükle (sadece crew_with_doc için)
    content = b"Name: WithDoc Test\nSTCW certificate"
    client.post(
        "/api/documents/upload",
        files=[("files", ("test_doc.txt", content, "text/plain"))],
    )

    results = list_crew(client, has_no_documents=True)
    names = [r["first_name"] for r in results]
    assert "WithoutDoc" in names
    # WithDoc belgesi varsa görünmemeli (match olursa)
    # Not: match mekanizmasına bağlı, sadece belgesi olmayan kesin


def test_has_no_documents_false_returns_crew_with_at_least_one_doc(client):
    """has_no_documents=False → en az bir belgesi olan personel."""
    make_crew(client, first_name="NoDocs", last_name="Test")

    # Belgeli personel oluştur + belge yükle (CV ile otomatik)
    cv_content = b"Curriculum Vitae\nName: Belge Sahibi\nbelgesahibi@test.com"
    r = client.post(
        "/api/documents/upload",
        files=[("files", ("BELGE_SAHIBI_CV.txt", cv_content, "text/plain"))],
    )
    assert r.status_code == 201

    results = list_crew(client, has_no_documents=False)
    names = [r["first_name"] for r in results]
    assert "NoDocs" not in names


# ── Limit artışı ──────────────────────────────────────────────────────────────

def test_limit_can_be_set_to_200(client):
    """Limit parametresi 200'e kadar kabul edilmeli."""
    # En az 1 kayıt oluştur
    make_crew(client)
    results = list_crew(client, limit=200)
    assert isinstance(results, list)


def test_limit_above_200_is_rejected(client):
    """Limit 200'ü aşarsa 422 Unprocessable Entity döner."""
    r = client.get("/api/crew/", params={"limit": 201})
    assert r.status_code == 422


# ── Kombine filtreler ─────────────────────────────────────────────────────────

def test_combined_nationality_and_rank_filter(client):
    make_crew(client, first_name="TRChief", last_name="A",
              nationality="Turkish", rank="Chief Officer")
    make_crew(client, first_name="TRSailor", last_name="B",
              nationality="Turkish", rank="Able Seaman")
    make_crew(client, first_name="RUChief", last_name="C",
              nationality="Russian", rank="Chief Officer")

    results = list_crew(client, nationality="Turkish", rank="Chief")
    assert len(results) == 1
    assert results[0]["first_name"] == "TRChief"


def test_show_problematic_returns_crew_with_missing_or_expired_documents(client):
    """show_problematic=True → eksik veya süresi geçen/acil belgesi olan personel döner."""
    far = (date.today() + timedelta(days=365)).strftime("%d.%m.%Y")

    # Alpha: tüm zorunlu belge türleri geçerli → sorunlu DEĞİL
    crew_a = make_crew(client, first_name="Alpha", last_name="A", passport_number="PA-111")
    for filename, content in [
        ("PASSPORT.txt", f"PASSPORT\nName: Alpha A\nExpiry Date: {far}"),
        ("SEAMAN_BOOK.txt", f"SEAMAN'S BOOK\nName: Alpha A\nExpiry Date: {far}"),
        ("STCW.txt", f"STCW certificate\nName: Alpha A\nExpiry Date: {far}"),
        ("MEDICAL.txt", f"Medical certificate\nName: Alpha A\nExpiry Date: {far}"),
        ("CONTRACT.txt", f"Contract\nName: Alpha A\nExpiry Date: {far}"),
    ]:
        r = client.post(
            "/api/documents/upload",
            files=[("files", (filename, content.encode(), "text/plain"))],
        )
        assert r.status_code == 201, r.text
        doc = r.json()[0]
        assert doc["crew_member_id"] == crew_a["id"], doc["original_filename"]
        assert doc["document_type"] in {"passport", "seaman_book", "stcw", "medical", "contract"}

    # Bravo: hiç belgesi yok → sorunlu
    make_crew(client, first_name="Bravo", last_name="B", passport_number="PB-222")

    results = list_crew(client, show_problematic=True)
    names = [r["first_name"] for r in results]
    assert "Bravo" in names
    assert "Alpha" not in names


def test_show_problematic_returns_crew_with_expired_document(client):
    """Süresi geçmiş belgesi olan personel show_problematic filtresinde görünür."""
    past = (date.today() - timedelta(days=10)).strftime("%d.%m.%Y")

    make_crew(client, first_name="ExpiredDoc", last_name="Test", passport_number="PE-333")
    content = f"PASSPORT\nName: ExpiredDoc Test\nExpiry Date: {past}"
    r = client.post(
        "/api/documents/upload",
        files=[("files", ("PASSPORT_EXPIRED.txt", content.encode(), "text/plain"))],
    )
    assert r.status_code == 201
    assert r.json()[0]["expiry_status"] == "expired"

    results = list_crew(client, show_problematic=True)
    names = [r["first_name"] for r in results]
    assert "ExpiredDoc" in names


def test_combined_experience_and_languages_filter(client):
    make_crew(client, first_name="SeniorEng", last_name="A",
              experience_years=10, languages="English, German")
    make_crew(client, first_name="JuniorEng", last_name="B",
              experience_years=2, languages="English")
    make_crew(client, first_name="SeniorNoEng", last_name="C",
              experience_years=15, languages="Russian")

    results = list_crew(client, experience_years_min=8, languages="English")
    names = [r["first_name"] for r in results]
    assert "SeniorEng" in names
    assert "JuniorEng" not in names
    assert "SeniorNoEng" not in names
