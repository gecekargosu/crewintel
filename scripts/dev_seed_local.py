"""Dev seed: realistic CREWINTEL data for local UI verification."""
import json
import random
from pathlib import Path

import httpx

API = "http://127.0.0.1:8001"
ROOT = Path(__file__).resolve().parent

client = httpx.Client(base_url=API, timeout=60)

r = client.post("/api/auth/login", json={"email": "admin@crewintel.com", "password": "Admin1234!"})
r.raise_for_status()
token = r.json()["access_token"]
client.headers["Authorization"] = f"Bearer {token}"

ships = [
    {"name": "MV GERMAN SKY", "imo_number": "9456789", "flag": "Malta", "ship_type": "Bulk Carrier", "company": "NGD Shipping"},
    {"name": "MV NGD MONTFRONT", "imo_number": "9567812", "flag": "Liberia", "ship_type": "Container", "company": "NGD Shipping"},
    {"name": "MT OCEAN STAR", "imo_number": "9678901", "flag": "Panama", "ship_type": "Tanker", "company": "UMAY Maritime"},
    {"name": "MV BLACK SEA TRADER", "imo_number": "9789012", "flag": "Türkiye", "ship_type": "General Cargo", "company": "UMAY Maritime"},
]
existing_ships = {row["name"]: row["id"] for row in client.get("/api/ships/").json()}
ship_ids = []
for s in ships:
    if s["name"] in existing_ships:
        ship_ids.append(existing_ships[s["name"]])
        continue
    r = client.post("/api/ships/", json=s)
    if r.status_code not in (200, 201):
        print("ship fail", s["name"], r.status_code, r.text[:200])
        continue
    ship_ids.append(r.json()["id"])
print("ships:", ship_ids)

crew = [
    {"first_name": "Mehmet", "last_name": "Kaya", "position": "Master", "rank": "Captain", "nationality": "Türkiye",
     "date_of_birth": "1980-04-12", "passport_number": "U12345678", "seaman_book_number": "SB998877",
     "phone": "+905321112233", "email": "mehmet.kaya@example.com", "experience_years": 18, "sea_service_months": 210,
     "languages": "Turkish, English", "availability": "available"},
    {"first_name": "Ahmet", "last_name": "Yılmaz", "position": "Chief Officer", "rank": "Chief Officer", "nationality": "Türkiye",
     "date_of_birth": "1988-09-03", "passport_number": "U22334455", "seaman_book_number": "SB112233",
     "phone": "+905332223344", "email": "ahmet.yilmaz@example.com", "experience_years": 11, "sea_service_months": 130,
     "languages": "Turkish, English", "availability": "on_board"},
    {"first_name": "Zeynep", "last_name": "Kaya", "position": "Second Engineer", "rank": "2nd Engineer", "nationality": "Türkiye",
     "date_of_birth": "1992-01-22", "passport_number": "U33445566", "seaman_book_number": "SB445566",
     "phone": "+905443334455", "email": "zeynep.kaya@example.com", "experience_years": 7, "sea_service_months": 84,
     "languages": "Turkish, English, German", "availability": "available"},
    {"first_name": "Ivan", "last_name": "Petrov", "position": "Able Seaman", "rank": "AB", "nationality": "Russia",
     "date_of_birth": "1995-06-30", "passport_number": "RU7788990", "seaman_book_number": "SB778899",
     "phone": "+79001112233", "email": "ivan.petrov@example.com", "experience_years": 5, "sea_service_months": 60,
     "languages": "Russian, English", "availability": "on_leave"},
    {"first_name": "Carlos", "last_name": "Santos", "position": "Cook", "rank": "Cook", "nationality": "Brazil",
     "date_of_birth": "1985-11-17", "passport_number": "BR5566778", "seaman_book_number": "SB556677",
     "phone": "+551199887766", "email": "carlos.santos@example.com", "experience_years": 12, "sea_service_months": 144,
     "languages": "Portuguese, English", "availability": "available"},
    {"first_name": "Ali", "last_name": "Veli", "position": "Oiler", "rank": "Oiler", "nationality": "Türkiye",
     "date_of_birth": "1990-02-08", "passport_number": "U44556677", "seaman_book_number": "SB223344",
     "phone": "+905554445566", "email": "ali.veli@example.com", "experience_years": 6, "sea_service_months": 72,
     "languages": "Turkish", "availability": "not_available"},
    {"first_name": "Raj", "last_name": "Kumar", "position": "Third Engineer", "rank": "3rd Engineer", "nationality": "India",
     "date_of_birth": "1993-07-25", "passport_number": "IN9988776", "seaman_book_number": "SB889900",
     "phone": "+919988776655", "email": "raj.kumar@example.com", "experience_years": 8, "sea_service_months": 96,
     "languages": "Hindi, English", "availability": "available"},
    {"first_name": "Ayşe", "last_name": "Çelik", "position": "Stewardess", "rank": "Stewardess", "nationality": "Türkiye",
     "date_of_birth": "1997-03-14", "passport_number": "U66778899", "seaman_book_number": "SB334455",
     "phone": "+905665556677", "email": "ayse.celik@example.com", "experience_years": 3, "sea_service_months": 36,
     "languages": "Turkish, English", "availability": "available"},
    {"first_name": "John", "last_name": "Doe", "position": "Deck Cadet", "rank": "Cadet", "nationality": "United Kingdom",
     "date_of_birth": "2001-08-19", "passport_number": "GB1234567", "seaman_book_number": "SB001122",
     "phone": "+447700900123", "email": "john.doe@example.com", "experience_years": 1, "sea_service_months": 12,
     "languages": "English", "availability": "available"},
    {"first_name": "Hasan", "last_name": "Özdemir", "position": "Chief Engineer", "rank": "Chief Engineer", "nationality": "Türkiye",
     "date_of_birth": "1978-12-01", "passport_number": "U88990011", "seaman_book_number": "SB667788",
     "phone": "+905776667788", "email": "hasan.ozdemir@example.com", "experience_years": 22, "sea_service_months": 260,
     "languages": "Turkish, English", "availability": "on_board"},
]
existing_crew = {
    (row["first_name"], row["last_name"]): row["id"]
    for row in client.get("/api/crew/?limit=200").json()
}
crew_ids = []
for c in crew:
    key = (c["first_name"], c["last_name"])
    if key in existing_crew:
        crew_ids.append(existing_crew[key])
        continue
    r = client.post("/api/crew/", json=c)
    if r.status_code not in (200, 201):
        print("crew fail", c["first_name"], r.status_code, r.text[:300])
        continue
    crew_ids.append(r.json()["id"])
print("crew:", crew_ids)

# assignments
from datetime import date, timedelta

today = date.today()
assign_plan = [
    (ship_ids[0], 1, "Chief Officer", -120),
    (ship_ids[0], 9, "Chief Engineer", -200),
    (ship_ids[1], 4, "Able Seaman", -60),
]
for ship_id, idx, position, offset in assign_plan:
    if idx >= len(crew_ids):
        continue
    r = client.post("/api/assignments/", json={
        "ship_id": ship_id,
        "crew_member_id": crew_ids[idx],
        "position": position,
        "start_date": (today + timedelta(days=offset)).isoformat(),
        "status": "active",
    })
    if r.status_code not in (200, 201):
        print("assignment fail", r.status_code, r.text[:200])

# contracts (one expiring in 14 days, one 60 days, one healthy)
contract_plan = [
    (crew_ids[0], ship_ids[0], "CNT-2026-001", -180, 14),
    (crew_ids[2], ship_ids[1], "CNT-2026-002", -120, 60),
    (crew_ids[7], ship_ids[2], "CNT-2026-003", -30, 240),
]
for crew_id, ship_id, number, start_off, end_off in contract_plan:
    r = client.post("/api/contracts/", json={
        "crew_member_id": crew_id,
        "ship_id": ship_id,
        "contract_number": number,
        "contract_type": "Seafarer Employment Agreement",
        "start_date": (today + timedelta(days=start_off)).isoformat(),
        "end_date": (today + timedelta(days=end_off)).isoformat(),
        "status": "active",
    })
    if r.status_code not in (200, 201):
        print("contract fail", number, r.status_code, r.text[:200])

# documents: single upload
WORKSPACE = ROOT.parents[2]
candidates = [
    WORKSPACE / "CREWINTEL_Test_Dokumanlari",
    ROOT.parent / "CREWINTEL_Test_Dokumanlari",
    ROOT.parent / "sample_documents",  # depo ile birlikte gelen örnek belgeler
]
doc_dir = next((p for p in candidates if p.exists()), candidates[0])
files = []
for p in sorted(doc_dir.glob("*.txt")):
    files.append(("files", (p.name, p.read_bytes(), "text/plain")))
if files:
    r = client.post("/api/documents/upload", files=files)
    print("upload:", r.status_code, r.text[:200] if r.status_code >= 400 else "ok")

# batch upload from karma test folder
candidates2 = [WORKSPACE / "CREWINTEL_Karmasik_Test", ROOT.parent / "CREWINTEL_Karmasik_Test"]
doc_dir2 = next((p for p in candidates2 if p.exists()), candidates2[0])
files2 = []
for p in sorted(doc_dir2.glob("*.txt")):
    files2.append(("files", (p.name, p.read_bytes(), "text/plain")))
if files2:
    r = client.post("/api/documents/batch", files=files2)
    print("batch:", r.status_code, r.text[:300])

print("ships", ship_ids)
print("crew", crew_ids)
