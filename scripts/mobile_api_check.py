"""Mobil API sözleşme kontrolü.

`mobile/services/api.ts` içindeki her çağrıyı gerçek backend'e karşı, gerçek bir
crew (personel) hesabıyla dener. Amaç: mobil ekranların kullandığı uçların,
HTTP metotlarının, gövde alanlarının ve dönen alanların backend ile uyumunu
cihaz/emülatör olmadan doğrulamak.

Kullanım:
    backend/.venv/Scripts/python.exe scripts/mobile_api_check.py
"""
from __future__ import annotations

import sys

import httpx

API = "http://127.0.0.1:8001"
ADMIN_EMAIL = "admin@crewintel.com"
ADMIN_PASSWORD = "Admin1234!"
CREW_EMAIL = "crew1@crewintel.com"
CREW_PASSWORD = "Crew1234!"

failures: list[str] = []


def check(
    label: str,
    resp: httpx.Response,
    required: tuple[str, ...] = (),
    allow: tuple[int, ...] = (),
) -> object:
    status_ok = resp.status_code < 400 or resp.status_code in allow
    body = None
    try:
        body = resp.json()
    except ValueError:
        body = resp.text[:200]
    missing = []
    # Alan kontrolü yalnızca başarılı yanıtlarda; `allow` ile kabul edilen
    # durumlar (ör. 409 = zaten başvurulmuş) hata gövdesi döner.
    if resp.status_code < 400 and required:
        if isinstance(body, dict):
            missing = [key for key in required if key not in body]
        elif isinstance(body, list) and body and isinstance(body[0], dict):
            missing = [key for key in required if key not in body[0]]

    ok = status_ok and not missing
    print(f"{'OK  ' if ok else 'FAIL'} {label:52s} {resp.status_code}"
          + (f"  eksik alan: {missing}" if missing else "")
          + ("" if status_ok else f"  {str(body)[:160]}"))
    if not ok:
        failures.append(label)
    return body


def main() -> int:
    admin = httpx.Client(base_url=API, timeout=60)
    token = admin.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if token.status_code != 200:
        print("admin login başarısız:", token.status_code, token.text[:200])
        return 1
    admin.headers["Authorization"] = f"Bearer {token.json()['access_token']}"

    # Personel hesabı yoksa oluştur
    users = admin.get("/api/auth/users").json()
    crew_list = admin.get("/api/crew/?limit=5").json()
    if not crew_list:
        print("DB'de personel yok — önce scripts/dev_seed_local.py çalıştırılmalı.")
        return 1
    target = crew_list[0]
    if not any(u["email"] == CREW_EMAIL for u in users):
        admin.post("/api/auth/users", json={
            "email": CREW_EMAIL,
            "password": CREW_PASSWORD,
            "full_name": f"{target['first_name']} {target['last_name']}",
            "role": "crew",
            "crew_member_id": target["id"],
        })

    crew = httpx.Client(base_url=API, timeout=60)
    login = crew.post("/api/auth/login", json={"email": CREW_EMAIL, "password": CREW_PASSWORD})
    check("POST /api/auth/login (crew)", login, ("access_token",))
    if login.status_code != 200:
        return 1
    crew.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    # authAPI
    check("GET  /api/auth/me", crew.get("/api/auth/me"), ("id", "email", "role"))

    # crewAPI
    me = check("GET  /api/portal/me", crew.get("/api/portal/me"), ("profile", "documents"))
    full = check("GET  /api/portal/me/full", crew.get("/api/portal/me/full"),
                 ("profile", "documents", "contract", "vessel", "eligibility"))
    check("PUT  /api/portal/contact", crew.put("/api/portal/contact",
                                               json={"phone": "+90 555 000 00 00",
                                                     "email": CREW_EMAIL}), ("phone",))
    check("PUT  /api/portal/preferences", crew.put("/api/portal/preferences",
                                                   json={"job_preferences": {"preferred_positions": ["Master"]},
                                                         "vessel_types_experience": "Container"}))
    check("PATCH /api/portal/job-seeking", crew.patch("/api/portal/job-seeking",
                                                      json={"job_seeking": True}), ("job_seeking",))

    # documentsAPI
    docs = check("GET  /api/portal/documents", crew.get("/api/portal/documents"))
    print("     belge sayısı:", len(docs) if isinstance(docs, list) else "?")

    # jobsAPI
    jobs = check("GET  /api/portal/jobs", crew.get("/api/portal/jobs"))
    check("GET  /api/portal/jobs/recommended", crew.get("/api/portal/jobs/recommended"))
    check("GET  /api/portal/applications", crew.get("/api/portal/applications"))
    if isinstance(jobs, list) and jobs:
        job_id = jobs[0]["id"]
        check(f"GET  /api/portal/jobs/{{id}}", crew.get(f"/api/portal/jobs/{job_id}"),
              ("title", "has_applied"))
        # 409 = daha önce başvurulmuş (betik tekrar çalıştırılabilir olmalı)
        check(f"POST /api/portal/jobs/{{id}}/apply", crew.post(f"/api/portal/jobs/{job_id}/apply"),
              ("id", "status"), allow=(409,))

    # contractsAPI / vesselAPI
    check("GET  /api/portal/contracts/me", crew.get("/api/portal/contracts/me"))
    check("GET  /api/portal/vessel/me", crew.get("/api/portal/vessel/me"))

    # notificationsAPI
    check("GET  /api/portal/notifications", crew.get("/api/portal/notifications"))

    # messagesAPI — konuşma yoksa yönetici tarafında bir tane açılır
    conversations = check("GET  /api/messages/conversations", crew.get("/api/messages/conversations"))
    if isinstance(conversations, list) and not conversations:
        crew_me = crew.get("/api/auth/me").json()
        created = admin.post("/api/messages/conversations",
                             json={"crew_user_id": crew_me["id"], "subject": "Mobil test"})
        print("     test konuşması:", created.status_code, created.text[:80])
        conversations = crew.get("/api/messages/conversations").json()
    if isinstance(conversations, list) and conversations:
        conv_id = conversations[0]["id"]
        conv = check(f"GET  /api/messages/conversations/{{id}}",
                     crew.get(f"/api/messages/conversations/{conv_id}"),
                     ("conversation", "messages"))
        check(f"POST /api/messages/conversations/{{id}}",
              crew.post(f"/api/messages/conversations/{conv_id}", json={"body": "mobil test"}),
              ("id", "body"))
        if isinstance(conv, dict) and conv.get("messages"):
            msg_id = conv["messages"][0]["id"]
            check("PATCH /api/messages/{id}/read", crew.patch(f"/api/messages/{msg_id}/read"))
    else:
        print("     (konuşma yok — mesaj uçları atlandı)")

    # deviceAPI
    check("POST /api/devices", crew.post("/api/devices",
                                          json={"platform": "android", "push_token": "test-token-mobile-check"}),
          ("registered",))

    # Güvenlik: crew yönetim uçlarına erişememeli
    for path in ("/api/notifications/", "/api/crew/", "/api/documents/"):
        resp = crew.get(path)
        ok = resp.status_code == 403
        print(f"{'OK  ' if ok else 'FAIL'} crew erişimi engellendi {path:32s} {resp.status_code}")
        if not ok:
            failures.append(f"403 {path}")

    print("\n" + ("TÜM KONTROLLER GEÇTİ" if not failures
                  else f"{len(failures)} KONTROL BAŞARISIZ: {failures}"))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
