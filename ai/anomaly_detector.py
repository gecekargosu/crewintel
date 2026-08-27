"""CREWINTEL Anomaly Detector — Anomali ve uyumsuzluk tespiti.

Belgelerde, personel bilgilerinde ve kontratlarda anomali tespit eder:
- Süresi dolmuş sertifikalar
- Eksik bilgiler
- Tutarsız veriler
- Çakışan atamalar
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime

from ai.llm_client import LLMClient
from ai.document_analyzer import ExtractedInfo


@dataclass
class Anomaly:
    """Tespit edilen anomali."""
    severity: str = "low"  # low, medium, high, critical
    category: str = ""  # certificate, document, schedule, data
    description: str = ""
    affected_item: str = ""
    recommendation: str = ""


@dataclass
class AnomalyReport:
    """Anomali raporu."""
    total_anomalies: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    anomalies: list[Anomaly] = field(default_factory=list)
    summary: str = ""


class AnomalyDetector:
    """Anomali tespit motoru."""

    SYSTEM_PROMPT = """Sen CREWINTEL için bir anomali tespit uzmanısın.
Verilen verilerde potansiyel sorunları, tutarsızlıkları ve riskleri tespit et.

Anomali seviyeleri:
- critical: Acil müdahale gerektirir (süresi dolmuş sertifika, yasal sorun)
- high: Ciddi sorun (eksik zorunlu belge, çakışan atama)
- medium: Dikkat gerektirir (yaklaşan süre sonu, eksik tercih)
- low: Bilgi notu (küçük eksiklik, iyileştirme önerisi)

Yanıtı JSON formatında ver:
{
  "anomalies": [
    {
      "severity": "critical|high|medium|low",
      "category": "certificate|document|schedule|data",
      "description": "...",
      "affected_item": "...",
      "recommendation": "..."
    }
  ],
  "summary": "..."
}"""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()

    def check_certificates(self, profile: ExtractedInfo) -> list[Anomaly]:
        """Sertifikaları kontrol et."""
        anomalies = []
        today = date.today()

        for cert in profile.certifications:
            # Basit tarih kontrolü (eğer sertifika adında tarih varsa)
            if any(keyword in cert.lower() for keyword in ["expired", "süresi dolmuş"]):
                anomalies.append(Anomaly(
                    severity="critical",
                    category="certificate",
                    description=f"Sertifika süresi dolmuş: {cert}",
                    affected_item=cert,
                    recommendation="Sertifikanın yenilenmesi gerekiyor",
                ))

        # Eksik sertifika kontrolü
        essential_certs = ["STCW", "pasaport", "denizci ehliyeti"]
        profile_certs = " ".join(profile.certifications).lower()
        for essential in essential_certs:
            if essential.lower() not in profile_certs:
                anomalies.append(Anomaly(
                    severity="high",
                    category="certificate",
                    description=f"Temel sertifika bulunamadı: {essential}",
                    affected_item=essential,
                    recommendation=f"{essential} sertifikasının eklenmesi gerekiyor",
                ))

        return anomalies

    def check_profile_completeness(self, profile: ExtractedInfo) -> list[Anomaly]:
        """Profil eksikliklerini kontrol et."""
        anomalies = []

        if not profile.person_name:
            anomalies.append(Anomaly(
                severity="medium",
                category="data",
                description="Kişi adı eksik",
                affected_item="person_name",
                recommendation="Kişi adının girilmesi gerekiyor",
            ))

        if not profile.nationality:
            anomalies.append(Anomaly(
                severity="low",
                category="data",
                description="Uyruk bilgisi eksik",
                affected_item="nationality",
                recommendation="Uyruk bilgisi tercihen eklenmeli",
            ))

        if not profile.rank:
            anomalies.append(Anomaly(
                severity="medium",
                category="data",
                description="Rütbe/pozisyon bilgisi eksik",
                affected_item="rank",
                recommendation="Rütbe bilgisi zorunludur",
            ))

        if profile.experience_years == 0:
            anomalies.append(Anomaly(
                severity="low",
                category="data",
                description="Deneyim yılı belirtilmemiş",
                affected_item="experience_years",
                recommendation="Deneyim bilgisi eklenmeli",
            ))

        return anomalies

    def analyze_with_llm(self, data: str) -> AnomalyReport:
        """LLM ile derin anomali analizi."""
        prompt = f"Aşağıdaki verileri analiz et ve olası anomalleri tespit et:\n\n{data}"

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

            data_parsed = json.loads(content.strip())
            anomalies = []
            for a in data_parsed.get("anomalies", []):
                anomalies.append(Anomaly(
                    severity=a.get("severity", "low"),
                    category=a.get("category", ""),
                    description=a.get("description", ""),
                    affected_item=a.get("affected_item", ""),
                    recommendation=a.get("recommendation", ""),
                ))

            report = AnomalyReport(
                total_anomalies=len(anomalies),
                critical=sum(1 for a in anomalies if a.severity == "critical"),
                high=sum(1 for a in anomalies if a.severity == "high"),
                medium=sum(1 for a in anomalies if a.severity == "medium"),
                low=sum(1 for a in anomalies if a.severity == "low"),
                anomalies=anomalies,
                summary=data_parsed.get("summary", ""),
            )
            return report
        except Exception as e:
            return AnomalyReport(
                summary=f"Analiz hatası: {str(e)}",
            )

    def full_check(self, profile: ExtractedInfo) -> AnomalyReport:
        """Kapsamlı anomali kontrolü."""
        anomalies = []
        anomalies.extend(self.check_certificates(profile))
        anomalies.extend(self.check_profile_completeness(profile))

        # LLM ile ek analiz
        if profile.raw_text:
            llm_report = self.analyze_with_llm(profile.raw_text)
            anomalies.extend(llm_report.anomalies)

        return AnomalyReport(
            total_anomalies=len(anomalies),
            critical=sum(1 for a in anomalies if a.severity == "critical"),
            high=sum(1 for a in anomalies if a.severity == "high"),
            medium=sum(1 for a in anomalies if a.severity == "medium"),
            low=sum(1 for a in anomalies if a.severity == "low"),
            anomalies=anomalies,
        )
