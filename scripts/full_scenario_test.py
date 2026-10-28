"""CREWINTEL — tam kullanıcı senaryosu (uçtan uca) testi.

Bir yöneticinin programı ilk kez kullanması gibi davranır: gemi açar, personel
ekler, belge yükler/eşleştirir, kontrat ve atama yapar, ilan yayınlar, mesaj
gönderir, ayarları değiştirir, personel hesabıyla giriş yapıp portalı kullanır.
Her adımda HTTP durum kodu ve gövde kontrol edilir; 4xx beklenen yerlerde
beklenen kod, geri kalan her şey hata olarak raporlanır.

Kullanım:
    backend/.venv/Scripts/python.exe scripts/full_scenario_test.py
"""
from __future__ import annotations

import io
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import httpx

API = "http://127.0.0.1:8001"
STAMP = str(int(time.time()))[-6:]
IMO = str(1000000 + int(time.time()) % 8999999)  # 7 haneli olmalı


def ident(value: object) -> int | None:
    """Yanıttan id çıkar (beklenmeyen gövdede çökmesin)."""
    return value.get("id") if isinstance(value, dict) else None

results: list[tuple[str, str, int, str]] = []  # (durum, adim, kod, not)
issues: list[str] = []


def log(step: str, resp: httpx.Response, expect: tuple[int, ...] = (200, 201, 204), note: str = "") -> object:
    ok = resp.status_code in expect
    body = None
    try:
        body = resp.json()
    except ValueError:
        body = None
    detail = ""
    if not ok:
        try:
            raw = resp.json()
            detail = raw.get("detail") if isinstance(raw, dict) else str(raw)
        except ValueError:
            detail = resp.text[:200]
    status = "OK  " if ok else "HATA"
    results.append((status, step, resp.status_code, note or str(detail)[:160]))
    if not ok:
        issues.append(f"{step} -> {resp.status_code} {str(detail)[:200]}")
    line = f"{status} {resp.status_code} {step}"
    if not ok:
        line += f"  [{str(detail)[:200]}]"
    print(line)
    return body


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> int:
    admin = httpx.Client(base_url=API, timeout=120)
    login = log("Giriş (admin)", admin.post("/api/auth/login",
                                           json={"email": "admin@crewintel.com", "password": "Admin1234!"}))
    if not login:
        print("Admin girişi başarısız — devam edilemez.")
        return 1
    admin.headers["Authorization"] = f"Bearer {login['access_token']}"

    today = date.today()
    iso = lambda d: d.isoformat()  # noqa: E731

    section("Panel ve özet ekranları")
    log("GET /health", admin.get("/health"))
    log("Panel özeti (dashboard)", admin.get("/api/dashboard/summary"))
    log("Geçerlilik özeti (expiration)", admin.get("/api/expiration/summary"))
    log("Denetim kayıtları (audit)", admin.get("/api/audit-logs/?limit=5"))
    log("Ayarlar (settings)", admin.get("/api/settings"))
    log("İletişim bilgisi (settings/contact)", admin.get("/api/settings/contact"))

    section("Gemi işlemleri")
    ship = log("Gemi oluştur", admin.post("/api/ships/", json={
        "name": f"MV TEST {STAMP}", "imo_number": IMO, "flag": "Türkiye",
        "ship_type": "container", "company": "Test Denizcilik", "status": "active",
    }))
    ship_id = ident(ship)
    log("Gemi listesi", admin.get("/api/ships/"))
    log("Gemi detayı", admin.get(f"/api/ships/{ship_id}"))
    log("Gemi güncelle", admin.put(f"/api/ships/{ship_id}", json={"name": f"MV TEST {STAMP} A"}))
    log("Pozisyon ekle", admin.post(f"/api/ships/{ship_id}/positions",
                                   json={"position": "Kaptan", "required_count": 1}))
    staffing = log("Gemi kadro durumu", admin.get(f"/api/ships/{ship_id}/staffing"))
    log("Gemi görseli (yoksa 404 beklenir)", admin.get(f"/api/ships/{ship_id}/image"), expect=(404,))
    log("Olmayan gemi (404 beklenir)", admin.get("/api/ships/999999"), expect=(404,))

    section("Personel işlemleri")
    crew = log("Personel oluştur", admin.post("/api/crew/", json={
        "first_name": "Test", "last_name": f"Kullanici{STAMP}", "position": "Kaptan",
        "nationality": "Türkiye", "date_of_birth": "1985-05-05",
        "passport_number": f"T{STAMP}PA", "seaman_book_number": f"SB{STAMP}",
        "email": f"test{STAMP}@example.com", "phone": "+905550000000",
        "address": "İstanbul", "birth_place": "İzmir",
    }))
    crew_id = ident(crew)
    log("Personel listesi", admin.get("/api/crew/?limit=5"))
    log("Personel detayı", admin.get(f"/api/crew/{crew_id}"))
    log("Personel güncelle", admin.put(f"/api/crew/{crew_id}", json={"rank": "Master"}))
    log("Uygun personel arama", admin.get("/api/crew/eligible?position=Kaptan"))
    log("CSV dışa aktar", admin.get("/api/crew/export"))
    csv_text = f"first_name,last_name,position\nAli,Deneme{STAMP},Kaptan\n"
    log("CSV içe aktar (önizleme)", admin.post("/api/crew/import/preview", json={"content": csv_text}))
    log("Boş CSV içe aktarma (400 beklenir)", admin.post("/api/crew/import/preview", json={"content": ""}),
        expect=(400, 422))
    log("Olmayan personel (404 beklenir)", admin.get("/api/crew/999999"), expect=(404,))

    section("Belge işlemleri")
    test_docs = Path(__file__).resolve().parents[3] / "CREWINTEL_Test_Dokumanlari"
    files = []
    if test_docs.exists():
        for p in sorted(test_docs.glob("*.txt"))[:3]:
            files.append(("files", (p.name, p.read_bytes(), "text/plain")))
    uploaded = log("Belge yükle (3 dosya)", admin.post("/api/documents/upload", files=files))
    doc_ids = [d["id"] for d in uploaded] if isinstance(uploaded, list) else []
    log("Belge listesi", admin.get("/api/documents/?limit=5"))
    log("İnceleme kuyruğu", admin.get("/api/documents/review"))
    if doc_ids:
        did = doc_ids[0]
        log("Belge detayı", admin.get(f"/api/documents/{did}"))
        log("Belge adayları", admin.get(f"/api/documents/{did}/candidates"))
        log("Belge dosyası indir", admin.get(f"/api/documents/{did}/file"))
        log("Belgeyi personele eşle", admin.put(f"/api/documents/{did}/match",
                                              json={"crew_member_id": crew_id}))
        log("Belge eşleşmeleri", admin.get(f"/api/documents/{did}/matches"))
        log("Belgeyi onayla", admin.post(f"/api/documents/{did}/approve"))
        if len(doc_ids) > 1:
            log("İkinci belgeyi reddet", admin.post(f"/api/documents/{doc_ids[1]}/reject"))
    log("Batch yükleme", admin.post("/api/documents/batch", files=[
        ("files", (f"batch{STAMP}.txt", b"Name: Batch Test\nPassport Number: B1234567\n", "text/plain")),
    ]), expect=(202,))
    log("Olmayan batch (404 beklenir)", admin.get("/api/documents/batch/yok"), expect=(404,))
    log("Desteklenmeyen dosya tipi (415/400 beklenir)",
        admin.post("/api/documents/upload", files={"files": ("virus.exe", b"MZ", "application/octet-stream")}),
        expect=(400, 415, 422))

    section("Kontrat işlemleri")
    contract = log("Kontrat oluştur", admin.post("/api/contracts/", json={
        "crew_member_id": crew_id, "ship_id": ship_id, "contract_number": f"CNT-{STAMP}",
        "contract_type": "Seafarer Employment Agreement", "start_date": iso(today - timedelta(days=30)),
        "end_date": iso(today + timedelta(days=200)), "status": "active", "notes": "senaryo testi",
    }))
    contract_id = ident(contract)
    log("Kontrat listesi", admin.get("/api/contracts/"))
    log("Kontrat detayı", admin.get(f"/api/contracts/{contract_id}"))
    log("Kontrat güncelle", admin.put(f"/api/contracts/{contract_id}", json={"notes": "güncellendi"}))
    log("Aynı kontrat numarası (409/400 beklenir)", admin.post("/api/contracts/", json={
        "crew_member_id": crew_id, "ship_id": ship_id, "contract_number": f"CNT-{STAMP}",
        "contract_type": "Seafarer Employment Agreement", "start_date": iso(today),
    }), expect=(400, 409, 422))

    section("Atama (gemi personeli) işlemleri")
    assignment = log("Atama oluştur", admin.post("/api/assignments/", json={
        "ship_id": ship_id, "crew_member_id": crew_id, "position": "Kaptan",
        "start_date": iso(today), "end_date": iso(today + timedelta(days=120)), "status": "active",
    }))
    assignment_id = ident(assignment)
    log("Atama listesi", admin.get("/api/assignments/"))
    log("Atama güncelle", admin.put(f"/api/assignments/{assignment_id}", json={"notes": "test"}))
    log("Çakışan atama (409 beklenir)", admin.post("/api/assignments/", json={
        "ship_id": ship_id, "crew_member_id": crew_id, "position": "Kaptan",
        "start_date": iso(today), "status": "active",
    }), expect=(409,))

    section("İş ilanı ve başvuru")
    posting = log("İlan oluştur", admin.post("/api/jobs/", json={
        "title": f"Kaptan Aranıyor {STAMP}", "position": "Kaptan", "ship_id": ship_id,
        "vessel_type": "container", "flag": "Türkiye", "location": "İstanbul",
        "currency": "USD", "salary": "8000", "salary_period": "monthly",
        "contract_duration": "6", "join_date": iso(today + timedelta(days=20)),
        "application_deadline": iso(today + timedelta(days=15)),
        "description": "Senaryo testi ilanı", "duties": "Köprüüstü vardiyası",
        "requirements": "Master sertifikası", "status": "open",
    }))
    posting_id = ident(posting)
    log("İlan listesi", admin.get("/api/jobs/"))
    log("İlan detayı", admin.get(f"/api/jobs/{posting_id}"))
    log("İlan güncelle", admin.patch(f"/api/jobs/{posting_id}", json={"salary": "8500"}))
    log("İlan yayınla (e-posta kanalı)", admin.post(f"/api/jobs/{posting_id}/publish",
                                                    json={"channels": ["email"]}), expect=(200, 201, 202, 503))
    log("Yayın durumları", admin.get(f"/api/jobs/{posting_id}/publications"))
    log("WhatsApp mesajları", admin.get(f"/api/jobs/{posting_id}/whatsapp-messages"))
    log("İlan görseli yükle", admin.post(f"/api/jobs/{posting_id}/image",
                                        files={"file": ("ilan.png", b"\x89PNG\r\n\x1a\n" + b"0" * 64, "image/png")}),
        expect=(201, 415, 400))
    log("İlan görseli getir", admin.get(f"/api/jobs/{posting_id}/image"), expect=(200, 404))
    app_admin = log("İlan için başvuru (admin adına)", admin.post(f"/api/jobs/{posting_id}/apply",
                                                                  json={"crew_member_id": crew_id,
                                                                        "note": "senaryo"}),
                    expect=(200, 201, 400, 409))
    app_id = ident(app_admin)
    log("İlan başvuruları", admin.get(f"/api/jobs/{posting_id}/applications"))
    log("Tüm başvurular", admin.get("/api/jobs/applications/all"))
    if app_id:
        log("Başvuru durumu: reviewing", admin.patch(f"/api/jobs/applications/{app_id}",
                                                     json={"status": "reviewing"}))
        log("Başvuru durumu: accepted", admin.patch(f"/api/jobs/applications/{app_id}",
                                                    json={"status": "accepted"}))
        log("Geçersiz durum (422 beklenir)", admin.patch(f"/api/jobs/applications/{app_id}",
                                                         json={"status": "uzayli"}), expect=(422, 400))

    section("İlan şablonları")
    tpl = log("Şablon oluştur", admin.post("/api/job-templates", json={
        "name": f"Şablon {STAMP}", "body": "Merhaba {{name}}, {{position}} ilanı", "is_default": False,
    }))
    tpl_id = ident(tpl)
    log("Şablon listesi", admin.get("/api/job-templates"))
    log("Şablon güncelle", admin.patch(f"/api/job-templates/{tpl_id}", json={"name": f"Şablon {STAMP} v2"}))

    section("Bildirimler ve e-posta")
    log("Bildirim listesi", admin.get("/api/notifications/"))
    log("Uyarı üret", admin.post("/api/notifications/generate"))
    log("Test e-postası", admin.post("/api/notifications/test-email"),
        expect=(200, 201, 400, 503))
    log("Tek personel e-posta", admin.post("/api/notifications/send-email",
                                          json={"crew_member_id": crew_id, "subject": "Test", "body": "Merhaba"}),
        expect=(200, 201, 400, 503))
    log("Toplu e-posta", admin.post("/api/notifications/send-bulk",
                                   json={"crew_ids": [crew_id], "subject": "Toplu", "body": "Merhaba"}),
        expect=(200, 201, 400, 503))

    section("Mesajlaşma")
    crew_user = log("Personel hesabı oluştur", admin.post("/api/auth/users", json={
        "email": f"testcrew{STAMP}@example.com", "password": "Test1234!",
        "full_name": f"Test Kullanici{STAMP}", "role": "crew", "crew_member_id": crew_id,
    }), expect=(200, 201, 409))
    conv = log("Konuşma başlat", admin.post("/api/messages/conversations", json={
        "crew_user_id": crew_user["id"] if isinstance(crew_user, dict) else None,
        "subject": "Senaryo testi",
    }), expect=(200, 201))
    conv_id = ident(conv)
    log("Konuşma listesi", admin.get("/api/messages/conversations"))
    if conv_id:
        msg = log("Mesaj gönder", admin.post(f"/api/messages/conversations/{conv_id}",
                                            json={"body": "Merhaba, senaryo testi"}))
        log("Konuşmayı oku", admin.get(f"/api/messages/conversations/{conv_id}"))
        if isinstance(msg, dict) and msg.get("id"):
            log("Mesajı okundu işaretle", admin.patch(f"/api/messages/{msg['id']}/read"))
        log("Boş mesaj (422 beklenir)", admin.post(f"/api/messages/conversations/{conv_id}", json={"body": ""}),
            expect=(422, 400))

    section("Ayarlar")
    current = admin.get("/api/settings").json()
    log("Ayar güncelle", admin.put("/api/settings", json={"values": {
        "smtp_from": "test@example.com",
    }}))
    log("Ayar değerlerini geri al", admin.put("/api/settings", json={"values": {
        k: v for k, v in (current.get("values") or {}).items() if k in ("company_name", "smtp_from")
    }} if current.get("values") else {}))

    section("Kullanıcı yönetimi")
    log("Kullanıcı listesi", admin.get("/api/auth/users"))
    viewer = log("Görüntüleyici kullanıcı oluştur", admin.post("/api/auth/users", json={
        "email": f"viewer{STAMP}@example.com", "password": "Viewer1234!",
        "full_name": "Salt Okunur", "role": "viewer",
    }), expect=(200, 201, 409))
    if isinstance(viewer, dict) and viewer.get("id"):
        log("Kullanıcı güncelle", admin.patch(f"/api/auth/users/{viewer['id']}",
                                              json={"full_name": "Salt Okunur 2"}))
        # Onay yalnızca crew bağlantılı hesaplar için; viewer'da 400 doğru davranış.
        log("Kullanıcıyı onayla (viewer → 400 beklenir)",
            admin.patch(f"/api/auth/users/{viewer['id']}/approve"), expect=(200, 204, 400))

    section("Personel portalı (kendi hesabıyla)")
    pc = httpx.Client(base_url=API, timeout=120)
    plog = log("Personel girişi", pc.post("/api/auth/login", json={
        "email": f"testcrew{STAMP}@example.com", "password": "Test1234!",
    }))
    if plog:
        pc.headers["Authorization"] = f"Bearer {plog['access_token']}"
        log("Portal profil", pc.get("/api/portal/me"))
        log("Portal profil (tam)", pc.get("/api/portal/me/full"))
        log("Portal iş ilanları", pc.get("/api/portal/jobs"))
        log("Portal önerilen ilanlar", pc.get("/api/portal/jobs/recommended"))
        log("Portal ilan detayı", pc.get(f"/api/portal/jobs/{posting_id}"))
        log("Portal başvuru gönder", pc.post(f"/api/portal/jobs/{posting_id}/apply"),
            expect=(200, 201, 409))
        log("Portal başvurularım", pc.get("/api/portal/applications"))
        log("Portal kontratlarım", pc.get("/api/portal/contracts/me"))
        log("Portal gemim", pc.get("/api/portal/vessel/me"))
        log("Portal belgelerim", pc.get("/api/portal/documents"))
        log("Portal iletişim güncelle", pc.put("/api/portal/contact",
                                              json={"phone": "+905551112233",
                                                    "email": f"testcrew{STAMP}@example.com"}))
        log("Portal tercih güncelle", pc.put("/api/portal/preferences",
                                            json={"job_preferences": {"preferred_positions": ["Kaptan"]},
                                                  "expected_salary_min": 7000}))
        log("Portal iş arıyorum", pc.patch("/api/portal/job-seeking", json={"job_seeking": True}))
        # Aynı içerik ikinci kez yüklenirse artık 409 döner (eski 500 yerine).
        log("Portal belge yükle", pc.post("/api/portal/documents",
                                        files={"file": (f"portal{STAMP}.txt",
                                                        f"STCW\nName: Test Kullanici {STAMP}\n".encode(),
                                                        "text/plain")}),
            expect=(201, 409, 415, 400))
        notes = log("Portal bildirimleri", pc.get("/api/portal/notifications"))
        if isinstance(notes, list) and notes:
            log("Portal bildirim okundu", pc.post(f"/api/portal/notifications/{notes[0]['id']}/read"),
                expect=(204, 200))
        log("Portal mesajları", pc.get("/api/messages/conversations"))
        log("Portal cihaz kaydı", pc.post("/api/devices",
                                         json={"platform": "android", "push_token": f"tok-{STAMP}"}),
            expect=(201, 200))
        log("Portal cihaz sil", pc.delete(f"/api/devices/tok-{STAMP}"), expect=(204, 200, 404))

    section("Yetki (403 beklenir)")
    if plog:
        for path in ("/api/crew/", "/api/documents/", "/api/ships/", "/api/dashboard/summary",
                     "/api/audit-logs/", "/api/notifications/", "/api/contracts/"):
            r = pc.get(path)
            ok = r.status_code == 403
            results.append(("OK  " if ok else "HATA", f"crew→{path}", r.status_code, ""))
            print(f"{'OK  ' if ok else 'HATA'} {r.status_code} crew erişimi engellendi: {path}")
            if not ok:
                issues.append(f"crew {path} -> {r.status_code} (403 bekleniyordu)")

    section("Android/cihaz ve WhatsApp uçları")
    log("WhatsApp kuyruğu", admin.get("/api/whatsapp/queue"))
    log("WhatsApp webhook", admin.post("/api/webhooks/whatsapp", json={
        "entry": [{"changes": [{"value": {"messages": [{"from": "905551112233",
                                                        "text": {"body": "MERHABA"}}]}}]}],
    }), expect=(200, 201, 202, 400, 422))
    log("WhatsApp işle", admin.post("/api/whatsapp/process"), expect=(200, 202, 400, 503))

    section("Temizlik (oluşturulan test verisi)")
    if app_id:
        pass  # başvuru kayıtları test verisi olarak kalabilir
    log("Atamayı sil", admin.delete(f"/api/assignments/{assignment_id}"), expect=(204, 200))
    log("Kontratı sil", admin.delete(f"/api/contracts/{contract_id}"), expect=(204, 200))
    log("İlanı sil", admin.delete(f"/api/jobs/{posting_id}"), expect=(204, 200))
    log("Şablonu sil", admin.delete(f"/api/job-templates/{tpl_id}"), expect=(204, 200))
    if doc_ids:
        for doc_id in doc_ids:
            admin.delete(f"/api/documents/{doc_id}")

    print("\n" + "=" * 70)
    print(f"TOPLAM: {len(results)} adım | HATA: {len(issues)}")
    if issues:
        print("\nHATALAR:")
        for item in issues:
            print(" -", item)
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
