"""AI endpoint tests — RBAC authorization, health, mocked LLM, regression.

Test policy:
- /api/ai/health → public (no auth)
- /api/ai/analyze, /match, /summarize, /anomalies, /recommend → require admin or hr
- viewer → 403
- crew → 403
- unauthenticated → 401
- admin/hr → passes auth, reaches LLM layer
"""

import os
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_db
from app.main import app
from app.models.user import User


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures — reuse conftest's database_fixture + add crew_client
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture()
def crew_client(db_session):
    """Create a crew user and return authenticated TestClient."""
    from app.core.security import hash_password
    from app.models.crew_member import CrewMember

    crew_member = CrewMember(first_name="AI", last_name="Crew", position="Sailor", status="active")
    db_session.add(crew_member)
    db_session.commit()
    db_session.refresh(crew_member)

    crew_user = User(
        email="crew.ai@test.example",
        full_name="AI Crew",
        role="crew",
        is_active=True,
        crew_member_id=crew_member.id,
        password_hash=hash_password("crew-pass-123", rounds=4),
    )
    db_session.add(crew_user)
    db_session.commit()
    db_session.refresh(crew_user)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as tc:
        login_resp = tc.post("/api/auth/login", json={"email": "crew.ai@test.example", "password": "crew-pass-123"})
        assert login_resp.status_code == 200, login_resp.text
        tc.headers["Authorization"] = f"Bearer {login_resp.json()['access_token']}"
        yield tc
    app.dependency_overrides.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Health endpoint — PUBLIC
# ═══════════════════════════════════════════════════════════════════════════════


def test_ai_health_returns_200(client):
    """Health endpoint her zaman 200 dönmeli (key olsa da olmasa da)."""
    response = client.get("/api/ai/health")
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "llm_available" in body


def test_ai_health_without_groq_key(client):
    """GROQ_API_KEY yokken health 'not_configured' veya 'degraded' dönmeli."""
    with patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=False):
        response = client.get("/api/ai/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] in ("not_configured", "degraded")
        assert body["llm_available"] is False


def test_ai_health_public(no_auth_client):
    """Health endpoint auth gerektirmez — herkes erişebilir."""
    response = no_auth_client.get("/api/ai/health")
    assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Unauthenticated → 401
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("endpoint,payload", [
    ("/api/ai/analyze", {"text": "test"}),
    ("/api/ai/match", {"person_name": "x"}),
    ("/api/ai/summarize", {"text": "x"}),
    ("/api/ai/anomalies", {"text": "x"}),
    ("/api/ai/recommend", {"profiles": []}),
])
def test_unauthenticated_returns_401(no_auth_client, endpoint, payload):
    """Token olmadan AI write endpoint'leri 401 dönmeli."""
    response = no_auth_client.post(endpoint, json=payload)
    assert response.status_code == 401, f"{endpoint} -> {response.status_code}"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Viewer → 403
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("endpoint,payload", [
    ("/api/ai/analyze", {"text": "test"}),
    ("/api/ai/match", {"person_name": "x"}),
    ("/api/ai/summarize", {"text": "x"}),
    ("/api/ai/anomalies", {"text": "x"}),
    ("/api/ai/recommend", {"profiles": []}),
])
def test_viewer_returns_403(viewer_client, endpoint, payload):
    """Viewer AI write endpoint'lerine erişmemeli — 403."""
    response = viewer_client.post(endpoint, json=payload)
    assert response.status_code == 403, f"{endpoint} -> {response.status_code}"


def test_viewer_health_accessible(viewer_client):
    """Viewer health endpoint'ine erişebilmeli (public)."""
    response = viewer_client.get("/api/ai/health")
    assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Crew → 403
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("endpoint,payload", [
    ("/api/ai/analyze", {"text": "test"}),
    ("/api/ai/match", {"person_name": "x"}),
    ("/api/ai/summarize", {"text": "x"}),
])
def test_crew_returns_403(crew_client, endpoint, payload):
    """Crew AI write endpoint'lerine erişmemeli — 403."""
    response = crew_client.post(endpoint, json=payload)
    assert response.status_code == 403, f"{endpoint} -> {response.status_code}"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Unauthorized request does NOT call LLM
# ═══════════════════════════════════════════════════════════════════════════════


def test_viewer_does_not_call_llm(viewer_client):
    """Viewer isteği LLM'i çağırmamalı — auth layer'da engellenmeli."""
    with patch("app.api.routes.ai._get_llm") as mock_get_llm:
        response = viewer_client.post("/api/ai/analyze", json={"text": "test"})
        assert response.status_code == 403
        mock_get_llm.assert_not_called()


def test_unauthenticated_does_not_call_llm(no_auth_client):
    """Tokensız istek LLM'i çağırmamalı."""
    with patch("app.api.routes.ai._get_llm") as mock_get_llm:
        response = no_auth_client.post("/api/ai/analyze", json={"text": "test"})
        assert response.status_code == 401
        mock_get_llm.assert_not_called()


def test_crew_does_not_call_llm(crew_client):
    """Crew isteği LLM'i çağırmamalı."""
    with patch("app.api.routes.ai._get_llm") as mock_get_llm:
        response = crew_client.post("/api/ai/match", json={"person_name": "x"})
        assert response.status_code == 403
        mock_get_llm.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Authorized roles → passes auth, reaches LLM layer
# ═══════════════════════════════════════════════════════════════════════════════


def test_admin_reaches_llm_layer(client):
    """Admin auth'ı geçer, _get_llm çağrılır."""
    with patch("app.api.routes.ai._get_llm") as mock_get_llm:
        mock_get_llm.side_effect = ValueError("GROQ_API_KEY ayarlanmamış")
        response = client.post("/api/ai/analyze", json={"text": "test"})
        assert response.status_code == 503
        mock_get_llm.assert_called_once()


def test_hr_reaches_llm_layer(hr_client):
    """HR auth'ı geçer, _get_llm çağrılır."""
    with patch("app.api.routes.ai._get_llm") as mock_get_llm:
        mock_get_llm.side_effect = ValueError("GROQ_API_KEY ayarlanmamış")
        response = hr_client.post("/api/ai/analyze", json={"text": "test"})
        assert response.status_code == 503
        mock_get_llm.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Mock LLM ile başarılı endpoint testleri
# ═══════════════════════════════════════════════════════════════════════════════


def test_analyze_with_mocked_llm(client):
    """Mock LLM ile /analyze endpoint'i doğru veri döndürmeli."""
    mock_result = MagicMock()
    mock_result.document_type = "passport"
    mock_result.person_name = "Test User"
    mock_result.nationality = "Turkish"
    mock_result.rank = "Captain"
    mock_result.certifications = ["STCW"]
    mock_result.experience_years = 10
    mock_result.skills = ["navigation"]
    mock_result.contract_start = "2026-01-01"
    mock_result.contract_end = "2026-12-31"
    mock_result.ship_name = "MV Test"
    mock_result.summary = "Test summary"
    mock_result.confidence = 0.95
    mock_result.anomalies = []

    with patch("app.api.routes.ai._get_llm") as mock_get_llm, \
         patch("app.api.routes.ai.DocumentAnalyzer") as MockAnalyzer:
        mock_get_llm.return_value = MagicMock()
        MockAnalyzer.return_value.extract_from_text.return_value = mock_result

        response = client.post("/api/ai/analyze", json={
            "text": "Name: Test User, Rank: Captain",
            "source_file": "test.txt",
        })
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["result"]["document_type"] == "passport"
        assert body["result"]["person_name"] == "Test User"
        assert body["result"]["confidence"] == 0.95


def test_match_with_mocked_llm(client):
    """Mock LLM ile /match endpoint'i doğru skor döndürmeli."""
    mock_result = MagicMock()
    mock_result.score = 85
    mock_result.overall_fit = "good"
    mock_result.certification_match = True
    mock_result.experience_match = True
    mock_result.skill_match = False
    mock_result.missing_items = ["navigation"]
    mock_result.notes = "Good candidate but missing navigation cert"

    with patch("app.api.routes.ai._get_llm") as mock_get_llm, \
         patch("app.api.routes.ai.CrewMatcher") as MockMatcher:
        mock_get_llm.return_value = MagicMock()
        MockMatcher.return_value.match_with_llm.return_value = mock_result

        response = client.post("/api/ai/match", json={
            "person_name": "Test User",
            "rank": "Captain",
            "certifications": ["STCW"],
            "experience_years": 10,
            "job_title": "Chief Officer",
            "job_rank": "Chief Officer",
            "required_certifications": ["STCW", "navigation"],
            "min_experience_years": 5,
        })
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["result"]["score"] == 85
        assert "navigation" in body["result"]["missing_items"]


def test_summarize_with_mocked_llm(client):
    """Mock LLM ile /summarize endpoint'i özet döndürmeli."""
    with patch("app.api.routes.ai._get_llm") as mock_get_llm, \
         patch("app.api.routes.ai.Summarizer") as MockSummarizer:
        mock_get_llm.return_value = MagicMock()
        MockSummarizer.return_value.summarize.return_value = "This is a summary."

        response = client.post("/api/ai/summarize", json={
            "text": "Long document text that needs summarization.",
            "context": "crew management",
        })
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["summary"] == "This is a summary."


def test_anomalies_with_mocked_llm(client):
    """Mock LLM ile /anomalies endpoint'i anomali raporu döndürmeli."""
    mock_anomaly = MagicMock()
    mock_anomaly.severity = "high"
    mock_anomaly.category = "document_forgery"
    mock_anomaly.description = "Suspicious date format"
    mock_anomaly.affected_item = "expiry_date"
    mock_anomaly.recommendation = "Verify with original"

    mock_report = MagicMock()
    mock_report.total_anomalies = 1
    mock_report.critical = 0
    mock_report.high = 1
    mock_report.medium = 0
    mock_report.low = 0
    mock_report.anomalies = [mock_anomaly]
    mock_report.summary = "1 high severity anomaly found"

    with patch("app.api.routes.ai._get_llm") as mock_get_llm, \
         patch("app.api.routes.ai.AnomalyDetector") as MockDetector:
        mock_get_llm.return_value = MagicMock()
        MockDetector.return_value.analyze_with_llm.return_value = mock_report

        response = client.post("/api/ai/anomalies", json={
            "text": "Passport document with suspicious dates",
        })
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["result"]["total"] == 1
        assert body["result"]["anomalies"][0]["category"] == "document_forgery"


def test_recommend_with_mocked_llm(client):
    """Mock LLM ile /recommend endpoint'i öneri listesi döndürmeli."""
    mock_rec = MagicMock()
    mock_rec.type = "renewal"
    mock_rec.priority = "high"
    mock_rec.title = "STCW yenileme"
    mock_rec.description = "Crew member X's STCW expires in 30 days"
    mock_rec.action_items = ["Contact crew member", "Schedule renewal"]

    mock_report = MagicMock()
    mock_report.total = 1
    mock_report.recommendations = [mock_rec]
    mock_report.summary = "1 high priority recommendation"

    with patch("app.api.routes.ai._get_llm") as mock_get_llm, \
         patch("app.api.routes.ai.RecommendationEngine") as MockEngine:
        mock_get_llm.return_value = MagicMock()
        MockEngine.return_value.generate_recommendations.return_value = mock_report

        response = client.post("/api/ai/recommend", json={
            "profiles": [{"person_name": "Test", "rank": "Captain"}],
            "context": "upcoming expirations",
        })
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["result"]["total"] == 1


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Validation
# ═══════════════════════════════════════════════════════════════════════════════


def test_analyze_empty_text_returns_422(client):
    """Boş text ile /analyze 422 dönmeli (Pydantic validation)."""
    response = client.post("/api/ai/analyze", json={})
    assert response.status_code == 422


def test_groq_key_missing_returns_503(client):
    """GROQ_API_KEY yokken auth başarılı olsa bile 503 dönmeli."""
    with patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=False):
        response = client.post("/api/ai/analyze", json={"text": "test"})
        assert response.status_code == 503
        assert "AI" in response.json()["detail"]
