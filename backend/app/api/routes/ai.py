"""CREWINTEL AI API Routes — Yapay zeka endpointleri.

Bu route'lar CREWINTEL'in AI modüllerine HTTP erişim sağlar:
- Belge analizi
- Personel-eşleştirme
- Anomali tespiti
- Öneri üretimi
- Belge özetleme
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

# AI modüllerini import et
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from ai.llm_client import LLMClient, LLMConfig
from ai.document_analyzer import DocumentAnalyzer, ExtractedInfo
from ai.crew_matcher import CrewMatcher, JobRequirement, MatchResult
from ai.anomaly_detector import AnomalyDetector, AnomalyReport
from ai.recommendation import RecommendationEngine, RecommendationReport
from ai.summarizer import Summarizer


router = APIRouter(prefix="/api/ai", tags=["ai"])


# --- Request/Response modelleri ---

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


# --- Yardımcı fonksiyonlar ---

def _get_llm() -> LLMClient:
    """LLM istemcisi oluştur."""
    config = LLMConfig(
        api_key=os.environ.get("GROQ_API_KEY", ""),
        base_url=os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        model=os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
    )
    return LLMClient(config)


def _profile_from_dict(d: dict) -> ExtractedInfo:
    """Dict'ten ExtractedInfo oluştur."""
    return ExtractedInfo(
        person_name=d.get("person_name", ""),
        rank=d.get("rank", ""),
        certifications=d.get("certifications", []),
        experience_years=d.get("experience_years", 0),
        skills=d.get("skills", []),
        nationality=d.get("nationality", ""),
    )


# --- Endpointler ---

@router.get("/health")
def ai_health():
    """AI modülü sağlık kontrolü."""
    try:
        llm = _get_llm()
        available = llm.is_available()
        return {
            "status": "healthy" if available else "degraded",
            "llm_available": available,
            "model": llm.config.model,
            "provider": "groq",
        }
    except ValueError as e:
        return {
            "status": "not_configured",
            "llm_available": False,
            "error": str(e),
            "setup_url": "https://console.groq.com",
        }


@router.post("/analyze")
def analyze_document(req: AnalyzeTextRequest):
    """Belge metnini analiz et."""
    try:
        llm = _get_llm()
        analyzer = DocumentAnalyzer(llm)
        result = analyzer.extract_from_text(req.text, req.source_file)
        return {
            "status": "success",
            "result": {
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
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=503, detail=f"AI yapılandırılmamış: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analiz hatası: {e}")


@router.post("/analyze/upload")
async def analyze_upload(file: UploadFile = File(...)):
    """Dosya yükle ve analiz et."""
    try:
        content = await file.read()
        llm = _get_llm()
        analyzer = DocumentAnalyzer(llm)
        result = analyzer.extract_from_bytes(content, file.filename or "unknown")
        return {
            "status": "success",
            "filename": file.filename,
            "result": {
                "document_type": result.document_type,
                "person_name": result.person_name,
                "rank": result.rank,
                "certifications": result.certifications,
                "experience_years": result.experience_years,
                "summary": result.summary,
                "confidence": result.confidence,
                "anomalies": result.anomalies,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=503, detail=f"AI yapılandırılmamış: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analiz hatası: {e}")


@router.post("/match")
def match_crew(req: MatchRequest):
    """Personel-iş eşleştirme."""
    try:
        llm = _get_llm()
        matcher = CrewMatcher(llm)

        profile = _profile_from_dict({
            "person_name": req.person_name,
            "rank": req.rank,
            "certifications": req.certifications,
            "experience_years": req.experience_years,
            "skills": req.skills,
            "nationality": req.nationality,
        })

        job = JobRequirement(
            title=req.job_title,
            rank=req.job_rank,
            required_certifications=req.required_certifications,
            min_experience_years=req.min_experience_years,
            required_skills=req.required_skills,
        )

        result = matcher.match_with_llm(profile, job)
        return {
            "status": "success",
            "result": {
                "score": result.score,
                "overall_fit": result.overall_fit,
                "certification_match": result.certification_match,
                "experience_match": result.experience_match,
                "skill_match": result.skill_match,
                "missing_items": result.missing_items,
                "notes": result.notes,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=503, detail=f"AI yapılandırılmamış: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eşleştirme hatası: {e}")


@router.post("/anomalies")
def detect_anomalies(req: AnalyzeTextRequest):
    """Anomali tespiti."""
    try:
        llm = _get_llm()
        detector = AnomalyDetector(llm)
        report = detector.analyze_with_llm(req.text)
        return {
            "status": "success",
            "result": {
                "total": report.total_anomalies,
                "critical": report.critical,
                "high": report.high,
                "medium": report.medium,
                "low": report.low,
                "anomalies": [
                    {
                        "severity": a.severity,
                        "category": a.category,
                        "description": a.description,
                        "affected_item": a.affected_item,
                        "recommendation": a.recommendation,
                    }
                    for a in report.anomalies
                ],
                "summary": report.summary,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=503, detail=f"AI yapılandırılmamış: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomali tespit hatası: {e}")


@router.post("/recommend")
def get_recommendations(req: RecommendRequest):
    """Akıllı öneriler üret."""
    try:
        llm = _get_llm()
        engine = RecommendationEngine(llm)
        profiles = [_profile_from_dict(p) for p in req.profiles]
        report = engine.generate_recommendations(profiles, req.context)
        return {
            "status": "success",
            "result": {
                "total": report.total,
                "recommendations": [
                    {
                        "type": r.type,
                        "priority": r.priority,
                        "title": r.title,
                        "description": r.description,
                        "action_items": r.action_items,
                    }
                    for r in report.recommendations
                ],
                "summary": report.summary,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=503, detail=f"AI yapılandırılmamış: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Öneri hatası: {e}")


@router.post("/summarize")
def summarize_text(req: SummarizeRequest):
    """Metni özetle."""
    try:
        llm = _get_llm()
        summarizer = Summarizer(llm)
        summary = summarizer.summarize(req.text, req.context)
        return {
            "status": "success",
            "summary": summary,
        }
    except ValueError as e:
        raise HTTPException(status_code=503, detail=f"AI yapılandırılmamış: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Özetleme hatası: {e}")
