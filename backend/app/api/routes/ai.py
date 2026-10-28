"""Yapay zekâ destekli analiz uçları.

Tüm uçlar **isteğe bağlıdır**: `AI_API_KEY` tanımlı değilse 503 döner ve
arayüz bunu "AI yapılandırılmadı" olarak gösterir. Anahtar olmadan hiçbir
temel özellik (belge yükleme, eşleştirme, süre takibi) bozulmaz.

OpenAI-uyumlu her sağlayıcı çalışır (Groq, OpenRouter, yerel vLLM…);
`AI_BASE_URL` ve `AI_MODEL` ile seçilir.
"""

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from ai.anomaly_detector import AnomalyDetector
from ai.crew_matcher import CrewMatcher, JobRequirement
from ai.document_analyzer import DocumentAnalyzer, ExtractedInfo
from ai.llm_client import LLMClient, LLMConfig
from ai.recommendation import RecommendationEngine
from ai.summarizer import Summarizer
from app.api.deps import require_roles
from app.core.config import get_settings
from app.models.user import User

router = APIRouter(prefix="/api/ai", tags=["AI"])


class AnalyzeTextRequest(BaseModel):
    text: str
    source_file: str = ""


class MatchRequest(BaseModel):
    person_name: str = ""
    rank: str = ""
    certifications: list[str] = []
    experience_years: int = 0
    skills: list[str] = []
    nationality: str = ""
    job_title: str = ""
    job_rank: str = ""
    required_certifications: list[str] = []
    min_experience_years: int = 0
    required_skills: list[str] = []


class SummarizeRequest(BaseModel):
    text: str
    context: str = ""


class RecommendRequest(BaseModel):
    profiles: list[dict[str, Any]] = []
    context: str = ""


def _llm() -> LLMClient:
    """Ayarlardan LLM istemcisi üretir; anahtar yoksa 503 fırlatır."""
    settings = get_settings()
    if not settings.ai_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI yapılandırılmadı: AI_API_KEY tanımlı değil.",
        )
    return LLMClient(
        LLMConfig(
            api_key=settings.ai_api_key,
            base_url=settings.ai_base_url,
            model=settings.ai_model,
        )
    )


def _profile_from_dict(data: dict) -> ExtractedInfo:
    return ExtractedInfo(
        person_name=data.get("person_name", ""),
        rank=data.get("rank", ""),
        certifications=data.get("certifications", []),
        experience_years=data.get("experience_years", 0),
        skills=data.get("skills", []),
        nationality=data.get("nationality", ""),
    )


@router.get("/health")
def ai_health():
    """AI modülü hazır mı? (Arayüz bu uca bakıp sekmeyi gösterir/gizler.)"""
    settings = get_settings()
    if not settings.ai_api_key:
        return {
            "status": "not_configured",
            "llm_available": False,
            "model": settings.ai_model,
            "setup_hint": "AI_API_KEY ortam değişkenini .env dosyasına ekleyin.",
        }
    try:
        available = _llm().is_available()
    except HTTPException:
        available = False
    return {
        "status": "healthy" if available else "degraded",
        "llm_available": available,
        "model": settings.ai_model,
        "base_url": settings.ai_base_url,
    }


@router.post("/analyze")
def analyze_document(
    payload: AnalyzeTextRequest,
    _user: User = Depends(require_roles("admin", "hr")),
):
    if not payload.text.strip():
        raise HTTPException(status_code=422, detail="Analiz için metin gerekli.")

    result = DocumentAnalyzer(_llm()).extract_from_text(payload.text, payload.source_file)
    return {
        "document_type": result.document_type,
        "person_name": result.person_name,
        "nationality": result.nationality,
        "rank": result.rank,
        "certifications": result.certifications,
        "experience_years": result.experience_years,
        "skills": result.skills,
        "contract_start": result.contract_start,
        "contract_end": result.contract_end,
        "ship_name": result.ship_name,
        "summary": result.summary,
        "confidence": result.confidence,
        "anomalies": result.anomalies,
    }


@router.post("/analyze/upload")
async def analyze_upload(
    file: UploadFile = File(...),
    _user: User = Depends(require_roles("admin", "hr")),
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="Boş dosya.")

    result = DocumentAnalyzer(_llm()).extract_from_bytes(content, file.filename or "unknown")
    return {
        "filename": file.filename,
        "document_type": result.document_type,
        "person_name": result.person_name,
        "rank": result.rank,
        "certifications": result.certifications,
        "experience_years": result.experience_years,
        "summary": result.summary,
        "confidence": result.confidence,
        "anomalies": result.anomalies,
    }


@router.post("/match")
def match_crew(
    payload: MatchRequest,
    _user: User = Depends(require_roles("admin", "hr")),
):
    profile = _profile_from_dict(
        {
            "person_name": payload.person_name,
            "rank": payload.rank,
            "certifications": payload.certifications,
            "experience_years": payload.experience_years,
            "skills": payload.skills,
            "nationality": payload.nationality,
        }
    )
    job = JobRequirement(
        title=payload.job_title,
        rank=payload.job_rank,
        required_certifications=payload.required_certifications,
        min_experience_years=payload.min_experience_years,
        required_skills=payload.required_skills,
    )

    result = CrewMatcher(_llm()).match_with_llm(profile, job)
    return {
        "score": result.score,
        "overall_fit": result.overall_fit,
        "certification_match": result.certification_match,
        "experience_match": result.experience_match,
        "skill_match": result.skill_match,
        "missing_items": result.missing_items,
        "notes": result.notes,
    }


@router.post("/anomalies")
def detect_anomalies(
    payload: AnalyzeTextRequest,
    _user: User = Depends(require_roles("admin", "hr")),
):
    report = AnomalyDetector(_llm()).analyze_with_llm(payload.text)
    return {
        "total": report.total_anomalies,
        "critical": report.critical,
        "high": report.high,
        "medium": report.medium,
        "low": report.low,
        "anomalies": [
            {
                "severity": item.severity,
                "category": item.category,
                "description": item.description,
                "affected_item": item.affected_item,
                "recommendation": item.recommendation,
            }
            for item in report.anomalies
        ],
        "summary": report.summary,
    }


@router.post("/recommend")
def get_recommendations(
    payload: RecommendRequest,
    _user: User = Depends(require_roles("admin", "hr")),
):
    profiles = [_profile_from_dict(profile) for profile in payload.profiles]
    report = RecommendationEngine(_llm()).generate_recommendations(profiles, payload.context)
    return {
        "total": report.total,
        "recommendations": [
            {
                "type": item.type,
                "priority": item.priority,
                "title": item.title,
                "description": item.description,
                "action_items": item.action_items,
            }
            for item in report.recommendations
        ],
        "summary": report.summary,
    }


@router.post("/summarize")
def summarize_text(
    payload: SummarizeRequest,
    _user: User = Depends(require_roles("admin", "hr")),
):
    return {"summary": Summarizer(_llm()).summarize(payload.text, payload.context)}
