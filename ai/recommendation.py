"""CREWINTEL Recommendation Engine — Akıllı öneriler.

Personel için iş önerileri, belge hatırlatmaları ve optimizasyon önerileri üretir.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from ai.llm_client import LLMClient
from ai.document_analyzer import ExtractedInfo


@dataclass
class Recommendation:
    """Tekil öneri."""
    type: str = ""  # job, certification, training, schedule, risk
    priority: str = "medium"  # low, medium, high
    title: str = ""
    description: str = ""
    action_items: list[str] = field(default_factory=list)


@dataclass
class RecommendationReport:
    """Öneri raporu."""
    total: int = 0
    recommendations: list[Recommendation] = field(default_factory=list)
    summary: str = ""


class RecommendationEngine:
    """Akıllı öneri motoru."""

    SYSTEM_PROMPT = """Sen CREWINTEL için bir öneri motoru uzmanısın.
Verilen personel verilerine dayanarak akıllı öneriler üret.

Öneri türleri:
- job: İş önerisi
- certification: Sertifika yenileme/ekleme
- training: Eğitim önerisi
- schedule: Zamanlama uyarısı
- risk: Risk uyarısı

Öncelik seviyeleri:
- high: Acil
- medium: Normal
- low: İyileştirme

Yanıtı JSON formatında ver:
{
  "recommendations": [
    {
      "type": "...",
      "priority": "...",
      "title": "...",
      "description": "...",
      "action_items": ["..."]
    }
  ],
  "summary": "..."
}"""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()

    def generate_recommendations(
        self, profiles: list[ExtractedInfo], context: str = ""
    ) -> RecommendationReport:
        """Personel listesi için öneriler üret."""
        profiles_text = "\n".join(
            f"- {p.person_name} ({p.rank}, {p.experience_years} yıl deneyim, "
            f"sertifikalar: {', '.join(p.certifications[:5])})"
            for p in profiles[:20]  # İlk 20 profili gönder
        )

        prompt = f"""Personel listesi:
{profiles_text}

Bağlam: {context or 'Genel personel optimizasyonu'}

Bu personel için akıllı öneriler üret."""

        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=self.SYSTEM_PROMPT,
            )
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())
            recs = []
            for r in data.get("recommendations", []):
                recs.append(Recommendation(
                    type=r.get("type", ""),
                    priority=r.get("priority", "medium"),
                    title=r.get("title", ""),
                    description=r.get("description", ""),
                    action_items=r.get("action_items", []),
                ))

            return RecommendationReport(
                total=len(recs),
                recommendations=recs,
                summary=data.get("summary", ""),
            )
        except Exception as e:
            return RecommendationReport(
                summary=f"Öneri üretme hatası: {str(e)}",
            )

    def recommend_for_crew(self, profile: ExtractedInfo) -> RecommendationReport:
        """Tek bir personel için öneriler üret."""
        prompt = f"""Personel profili:
- İsim: {profile.person_name}
- Rütbe: {profile.rank}
- Uyruk: {profile.nationality}
- Deneyim: {profile.experience_years} yıl
- Sertifikalar: {', '.join(profile.certifications)}
- Yetenekler: {', '.join(profile.skills)}
- Özet: {profile.summary}

Bu personel için önerilerini sun."""

        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=self.SYSTEM_PROMPT,
            )
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())
            recs = []
            for r in data.get("recommendations", []):
                recs.append(Recommendation(
                    type=r.get("type", ""),
                    priority=r.get("priority", "medium"),
                    title=r.get("title", ""),
                    description=r.get("description", ""),
                    action_items=r.get("action_items", []),
                ))

            return RecommendationReport(
                total=len(recs),
                recommendations=recs,
                summary=data.get("summary", ""),
            )
        except Exception as e:
            return RecommendationReport(
                summary=f"Öneri üretme hatası: {str(e)}",
            )
