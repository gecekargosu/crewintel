"""OpenAPI şemasındaki tüm GET uçlarını gerçek sunucuda dener, hataları raporlar.

Kullanım:
    python scripts/api_smoke.py
    CREWINTEL_API=http://127.0.0.1:8000 CREWINTEL_EMAIL=... CREWINTEL_PASSWORD=... python scripts/api_smoke.py

Yalnızca okuma yapar; veri oluşturmaz/silmez.
"""

from __future__ import annotations

import os

import httpx

API = os.environ.get("CREWINTEL_API", "http://127.0.0.1:8000")
EMAIL = os.environ.get("CREWINTEL_EMAIL", "admin@crewintel.example")
PASSWORD = os.environ.get("CREWINTEL_PASSWORD", "")

# Yönetici hesabıyla denenince normal olarak 4xx dönen uçlar:
#   * personel portalı uçları yalnızca "crew" rolüne açıktır (403),
#   * webhook doğrulaması token ister (403),
#   * uygunluk motoru zorunlu ?position= parametresi ister (422).
EXPECTED_PATH_PREFIXES = ("/api/portal/",)
EXPECTED_PATHS = {"/api/webhooks/whatsapp"}
EXPECTED_QUERY_ONLY = {"/api/crew/eligible"}


def login(client: httpx.Client) -> str:
    response = client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    response.raise_for_status()
    return response.json()["access_token"]


def main() -> int:
    if not PASSWORD:
        print("UYARI: CREWINTEL_PASSWORD verilmedi; giriş yapılamıyor.")
        return 2

    client = httpx.Client(base_url=API, timeout=60)
    client.headers["Authorization"] = f"Bearer {login(client)}"

    schema = client.get("/openapi.json").json()
    paths = sorted(schema["paths"].items())
    checked = 0
    failures: list[tuple[str, str, object, str]] = []

    for path, operations in paths:
        if "get" not in operations or "{" in path:
            continue
        checked += 1
        try:
            response = client.get(path)
        except httpx.HTTPError as exc:
            failures.append(("GET", path, "EXC", str(exc)[:120]))
            continue
        if response.status_code < 400:
            continue
        if path.startswith(EXPECTED_PATH_PREFIXES) or path in EXPECTED_PATHS:
            continue
        if path in EXPECTED_QUERY_ONLY and response.status_code == 422:
            continue
        failures.append(("GET", path, response.status_code, response.text[:200]))

    print(f"denenen GET ucu: {checked}")
    for method, path, code, detail in failures:
        print(f"HATA {method} {path} -> {code} {detail}")
    print(f"toplam hata: {len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
