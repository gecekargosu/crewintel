"""Local verification for the fixes: upload 500, classification, portal endpoints."""
from pathlib import Path

import httpx

API = "http://127.0.0.1:8001"
WS = Path(__file__).resolve().parents[3]
admin = httpx.Client(base_url=API, timeout=120)
tok = admin.post("/api/auth/login", json={"email": "admin@crewintel.com", "password": "Admin1234!"}).json()["access_token"]
admin.headers["Authorization"] = f"Bearer {tok}"

# 1) Single upload (used to crash with 500 when a national_id was present)
files = []
for p in sorted((WS / "CREWINTEL_Test_Dokumanlari").glob("*.txt")):
    files.append(("files", (p.name, p.read_bytes(), "text/plain")))
r = admin.post("/api/documents/upload", files=files)
print("upload:", r.status_code, "" if r.status_code == 201 else r.text[:400])
if r.status_code == 201:
    for d in r.json():
        print("   ", d["original_filename"], "->", d["document_type"], d["match_status"])

# 3) Crew user + portal endpoints
crew_list = admin.get("/api/crew/?limit=5").json()
first = crew_list[0]
users = admin.get("/api/auth/users").json()
if not any(u["email"] == "crew1@crewintel.com" for u in users):
    r = admin.post("/api/auth/users", json={
        "email": "crew1@crewintel.com",
        "password": "Crew1234!",
        "full_name": f"{first['first_name']} {first['last_name']}",
        "role": "crew",
        "crew_member_id": first["id"],
    })
    print("create crew user:", r.status_code, r.text[:150] if r.status_code >= 400 else "ok")

crew = httpx.Client(base_url=API, timeout=60)
r = crew.post("/api/auth/login", json={"email": "crew1@crewintel.com", "password": "Crew1234!"})
print("crew login:", r.status_code)
if r.status_code == 200:
    crew.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
    for path in ["/api/portal/me/full", "/api/portal/jobs", "/api/portal/applications",
                 "/api/portal/contracts/me", "/api/portal/vessel/me", "/api/portal/jobs/recommended",
                 "/api/notifications/", "/api/messages/conversations"]:
        resp = crew.get(path)
        body = resp.text[:80].replace("\n", " ")
        print(f"   {path}: {resp.status_code} {body}")
    jobs = crew.get("/api/portal/jobs").json()
    if jobs:
        jid = jobs[0]["id"]
        resp = crew.get(f"/api/portal/jobs/{jid}")
        print("   /api/portal/jobs/{id}:", resp.status_code, resp.text[:120])

# 4) Admin seeded with a reserved-domain email can now log in
r = admin.post("/api/auth/login", json={"email": "ADMIN@crewintel.com  ", "password": "Admin1234!"})
print("login with messy casing/space:", r.status_code)
