"""
Expiration service test coverage.

ExpirationService davranışlarını ve sınır koşullarını doğrular.
Mevcut sabitlere göre:
  expiry_urgent_days     = 30  (config default)
  expiry_approaching_days = 90  (config default)

expiry_status mantığı (document_expiry_status):
  remaining < 0          → "expired"
  0 <= remaining <= 30   → "urgent"
  31 <= remaining <= 90  → "approaching"
  remaining > 90         → "valid"
  expiry_date is None    → "no_date"
"""
from datetime import date, timedelta


today = date.today()


def _upload(client, filename: str, expiry_date: date | None) -> dict:
    """Belirli bir expiry_date içeren tek bir belge yükler."""
    if expiry_date is not None:
        date_str = expiry_date.strftime("%d.%m.%Y")
        content = f"Medical certificate id={filename}\nExpiry Date: {date_str}".encode()
    else:
        content = f"Medical certificate id={filename} no expiry date mentioned".encode()
    response = client.post(
        "/api/documents/upload",
        files=[("files", (filename, content, "text/plain"))],
    )
    assert response.status_code == 201
    return response.json()[0]


# ── expired ──────────────────────────────────────────────────────────

def test_expired_document_appears_in_expired_list(client):
    doc = _upload(client, "exp_past.txt", today - timedelta(days=1))
    assert doc["expiry_status"] == "expired"
    response = client.get("/api/expiration/expired")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert all(d["expiry_status"] == "expired" for d in response.json())


def test_expired_document_is_absent_from_urgent_list(client):
    _upload(client, "exp_past2.txt", today - timedelta(days=1))
    result = client.get("/api/expiration/urgent").json()
    assert not any(d["expiry_status"] == "expired" for d in result)


# ── urgent — boundary ────────────────────────────────────────────────

def test_expiry_today_is_urgent_not_expired(client):
    """remaining = 0 → urgent (sıfır < 0 değil)."""
    doc = _upload(client, "urgent_today.txt", today)
    assert doc["expiry_status"] == "urgent"


def test_expiry_in_thirty_days_is_urgent(client):
    """remaining = 30 → urgent (üst sınır dahil)."""
    doc = _upload(client, "urgent_upper.txt", today + timedelta(days=30))
    assert doc["expiry_status"] == "urgent"


def test_expiry_in_thirty_one_days_is_approaching_not_urgent(client):
    """remaining = 31 → approaching (31 > 30, sınır dışı urgent)."""
    doc = _upload(client, "approaching_lower.txt", today + timedelta(days=31))
    assert doc["expiry_status"] == "approaching"


def test_urgent_documents_appear_in_urgent_list(client):
    _upload(client, "urgent_mid.txt", today + timedelta(days=15))
    response = client.get("/api/expiration/urgent")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert all(d["expiry_status"] == "urgent" for d in response.json())


# ── approaching — boundary ───────────────────────────────────────────

def test_expiry_in_ninety_days_is_approaching(client):
    """remaining = 90 → approaching (üst sınır dahil)."""
    doc = _upload(client, "approaching_upper.txt", today + timedelta(days=90))
    assert doc["expiry_status"] == "approaching"


def test_expiry_in_ninety_one_days_is_valid(client):
    """remaining = 91 → valid (91 > 90, sınır dışı approaching)."""
    doc = _upload(client, "valid_lower.txt", today + timedelta(days=91))
    assert doc["expiry_status"] == "valid"


def test_approaching_documents_appear_in_approaching_list(client):
    _upload(client, "approaching_mid.txt", today + timedelta(days=60))
    response = client.get("/api/expiration/approaching")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert all(d["expiry_status"] == "approaching" for d in response.json())


# ── valid ────────────────────────────────────────────────────────────

def test_valid_document_appears_in_valid_list(client):
    doc = _upload(client, "valid_far.txt", today + timedelta(days=365))
    assert doc["expiry_status"] == "valid"
    response = client.get("/api/expiration/valid")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert all(d["expiry_status"] == "valid" for d in response.json())


# ── no-date ──────────────────────────────────────────────────────────

def test_document_without_expiry_appears_in_no_date_list(client):
    doc = _upload(client, "nodate.txt", None)
    assert doc["expiry_status"] == "no_date"
    response = client.get("/api/expiration/no-date")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert all(d["expiry_status"] == "no_date" for d in response.json())


# ── summary ──────────────────────────────────────────────────────────

def test_expiration_summary_has_correct_structure_and_counts(client):
    """Her kategoriden en az bir belge yükle; summary alanlarını ve toplamı doğrula."""
    _upload(client, "sum_expired.txt",    today - timedelta(days=1))
    _upload(client, "sum_urgent.txt",     today + timedelta(days=15))
    _upload(client, "sum_approaching.txt",today + timedelta(days=60))
    _upload(client, "sum_valid.txt",      today + timedelta(days=200))
    _upload(client, "sum_nodate.txt",     None)

    response = client.get("/api/expiration/summary")
    assert response.status_code == 200
    summary = response.json()

    # Tüm beklenen alanlar mevcut olmalı
    for key in ("total", "expired", "urgent", "approaching", "valid", "no_date"):
        assert key in summary, f"'{key}' alanı summary'de bulunamadı"

    # Her kategori en az 1 belge içermeli
    assert summary["expired"]    >= 1
    assert summary["urgent"]     >= 1
    assert summary["approaching"]>= 1
    assert summary["valid"]      >= 1
    assert summary["no_date"]    >= 1

    # total, tüm kategorilerin toplamına eşit olmalı
    category_sum = (
        summary["expired"]
        + summary["urgent"]
        + summary["approaching"]
        + summary["valid"]
        + summary["no_date"]
    )
    assert summary["total"] == category_sum
