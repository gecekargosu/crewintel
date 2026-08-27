"""CREWINTEL Crew Matcher — Personel-iş eşleştirme motoru.

Personel yeteneklerini, deneyimlerini ve sertifikalarını
iş ilanları ile eşleştirir.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from ai.llm_client import LLMClient
from ai.document_analyzer import ExtractedInfo


@dataclass
class JobRequirement:
    """İş gereksinim yapısı."""
    title: str = ""
    rank: str = ""
    required_certifications: list[str] = field(default_factory=list)
    preferred_certifications: list[str] = field(default_factory=list)
    min_experience_years: int = 0
    required_skills: list[str] = field(default_factory=list)
    ship_type: str = ""
    nationality_preference: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class MatchResult:
    """Eşleştirme sonucu."""
    crew_profile: ExtractedInfo | None = None
    job: JobRequirement | None = None
    score: float = 0.0  # 0-100
    certification_match: float = 0.0
    experience_match: float = 0.0
    skill_match: float = 0.0
    overall_fit: str = ""  # excellent, good, fair, poor
    missing_items: list[str] = field(default_factory=list)
    notes: str = ""


class CrewMatcher:
    """Personel-iş eşleştirme motoru."""

    RANK_HIERARCHY = {
        "captain": 10, "master": 10,
        "chief officer": 9, "first officer": 9,
        "chief engineer": 9,
        "second officer": 8, "second engineer": 8,
        "third officer": 7, "third engineer": 7,
        "bosun": 6, "boatswain": 6,
        "able seaman": 5, "ab": 5,
        "oiler": 4, "wiper": 3,
        "cook": 5, "steward": 4,
        "cadet": 2, "deck cadet": 2, "engine cadet": 2,
    }

    SYSTEM_PROMPT = """Sen CREWINTEL için bir personel-eşleştirme uzmanısın.
Verilen personel profili ve iş gereksinimlerini analiz et.

Yanıtı JSON formatında ver:
{
  "score": 0-100,
  "certification_match": 0.0-1.0,
  "experience_match": 0.0-1.0,
  "skill_match": 0.0-1.0,
  "overall_fit": "excellent|good|fair|poor",
  "missing_items": ["..."],
  "notes": "..."
}"""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()

    def match(self, profile: ExtractedInfo, job: JobRequirement) -> MatchResult:
        """Tek bir personeli bir iş ile eşleştir."""
        # Kurallar tabanlı skor hesaplama
        cert_score = self._certification_score(profile, job)
        exp_score = self._experience_score(profile, job)
        skill_score = self._skill_score(profile, job)

        # Ağırlıklı toplam
        raw_score = (cert_score * 0.4 + exp_score * 0.3 + skill_score * 0.3) * 100

        # Eksikler
        missing = self._find_missing(profile, job)

        # Genel uyum
        if raw_score >= 80:
            fit = "excellent"
        elif raw_score >= 60:
            fit = "good"
        elif raw_score >= 40:
            fit = "fair"
        else:
            fit = "poor"

        return MatchResult(
            crew_profile=profile,
            job=job,
            score=round(raw_score, 1),
            certification_match=round(cert_score, 3),
            experience_match=round(exp_score, 3),
            skill_match=round(skill_score, 3),
            overall_fit=fit,
            missing_items=missing,
        )

    def match_with_llm(self, profile: ExtractedInfo, job: JobRequirement) -> MatchResult:
        """LLM kullanarak derin eşleştirme."""
        prompt = f"""Personel Profili:
- İsim: {profile.person_name}
- Rütbe: {profile.rank}
- Sertifikalar: {', '.join(profile.certifications)}
- Deneyim: {profile.experience_years} yıl
- Yetenekler: {', '.join(profile.skills)}
- Uyruk: {profile.nationality}

İş Gereksinimleri:
- Pozisyon: {job.title} ({job.rank})
- Gerekli sertifikalar: {', '.join(job.required_certifications)}
- Tercih edilen sertifikalar: {', '.join(job.preferred_certifications)}
- Minimum deneyim: {job.min_experience_years} yıl
- Gerekli yetenekler: {', '.join(job.required_skills)}
- Gemi tipi: {job.ship_type}

Bu personelin bu iş için uygunluğunu analiz et."""

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
            return MatchResult(
                crew_profile=profile,
                job=job,
                score=data.get("score", 0),
                certification_match=data.get("certification_match", 0),
                experience_match=data.get("experience_match", 0),
                skill_match=data.get("skill_match", 0),
                overall_fit=data.get("overall_fit", "poor"),
                missing_items=data.get("missing_items", []),
                notes=data.get("notes", ""),
            )
        except Exception:
            # LLM başarısız olursa kurallar tabanlı sonuca dön
            return self.match(profile, job)

    def rank_candidates(
        self, profiles: list[ExtractedInfo], job: JobRequirement
    ) -> list[MatchResult]:
        """Birden fazla adayı sırala."""
        results = []
        for profile in profiles:
            result = self.match(profile, job)
            results.append(result)

        # Skora göre azalan sırayla sırala
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    def _certification_score(self, profile: ExtractedInfo, job: JobRequirement) -> float:
        """Sertifika uyumluluk skoru."""
        if not job.required_certifications:
            return 1.0

        profile_certs = {c.lower() for c in profile.certifications}
        required = {c.lower() for c in job.required_certifications}

        if not required:
            return 1.0

        matched = len(profile_certs & required)
        return matched / len(required)

    def _experience_score(self, profile: ExtractedInfo, job: JobRequirement) -> float:
        """Deneyim uyumluluk skoru."""
        if job.min_experience_years <= 0:
            return 1.0

        if profile.experience_years >= job.min_experience_years:
            return min(1.0, profile.experience_years / (job.min_experience_years * 1.5))
        else:
            return profile.experience_years / job.min_experience_years

    def _skill_score(self, profile: ExtractedInfo, job: JobRequirement) -> float:
        """Yetenek uyumluluk skoru."""
        if not job.required_skills:
            return 1.0

        profile_skills = {s.lower() for s in profile.skills}
        required = {s.lower() for s in job.required_skills}

        if not required:
            return 1.0

        matched = sum(1 for r in required if any(
            SequenceMatcher(None, r, p).ratio() > 0.7 for p in profile_skills
        ))
        return matched / len(required)

    def _find_missing(self, profile: ExtractedInfo, job: JobRequirement) -> list[str]:
        """Eksik gereksinimleri bul."""
        missing = []

        # Sertifikalar
        profile_certs = {c.lower() for c in profile.certifications}
        for cert in job.required_certifications:
            if cert.lower() not in profile_certs:
                missing.append(f"Eksik sertifika: {cert}")

        # Deneyim
        if profile.experience_years < job.min_experience_years:
            missing.append(
                f"Yetersiz deneyim: {profile.experience_years}/{job.min_experience_years} yıl"
            )

        # Yetenekler
        profile_skills = {s.lower() for s in profile.skills}
        for skill in job.required_skills:
            if not any(SequenceMatcher(None, skill.lower(), p).ratio() > 0.7
                      for p in profile_skills):
                missing.append(f"Eksik yetenek: {skill}")

        return missing
