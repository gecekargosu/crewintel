"""CREWINTEL Document Analyzer — Belge analizi ve bilgi çıkarma.

PDF, Word, CSV gibi belgelerden personel bilgilerini, sertifikaları,
kontrat detaylarını ve diğer kritik verileri çıkarır.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader

from ai.llm_client import LLMClient, LLMConfig


@dataclass
class ExtractedInfo:
    """Çıkarılan bilgi yapısı."""
    document_type: str = ""  # cv, contract, certificate, report
    person_name: str = ""
    nationality: str = ""
    rank: str = ""  # captain, officer, engineer, etc.
    certifications: list[str] = field(default_factory=list)
    experience_years: int = 0
    skills: list[str] = field(default_factory=list)
    contract_start: str = ""
    contract_end: str = ""
    ship_name: str = ""
    summary: str = ""
    raw_text: str = ""
    confidence: float = 0.0
    anomalies: list[str] = field(default_factory=list)


class DocumentAnalyzer:
    """Belge analiz ve bilgi çıkarma motoru."""

    SYSTEM_PROMPT = """Sen CREWINTEL için bir belge analiz uzmanısın.
Görevin verilen belge metninden yapılandırılmış bilgi çıkarmak.

Çıkarılması gereken bilgiler:
- Belge türü (CV, kontrat, sertifika, rapor)
- Kişi adı
- Uyruk
- Rütbe/pozisyon
- Sertifikalar (STCW, pasaport, denizci ehliyeti vb.)
- Deneyim yılı
- Yetenekler
- Kontrat başlangıç/bitiş tarihleri
- Gemi adı
- Özet
- Olası anormal durumlar (eksik bilgi, tutarsızlık, süre dolmuş sertifika)

Yanıtı JSON formatında ver:
{
  "document_type": "...",
  "person_name": "...",
  "nationality": "...",
  "rank": "...",
  "certifications": [...],
  "experience_years": 0,
  "skills": [...],
  "contract_start": "...",
  "contract_end": "...",
  "ship_name": "...",
  "summary": "...",
  "anomalies": [...],
  "confidence": 0.0-1.0
}"""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()

    def extract_from_pdf(self, file_path: str | Path) -> ExtractedInfo:
        """PDF dosyasından bilgi çıkar."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Dosya bulunamadı: {path}")

        reader = PdfReader(str(path))
        text_parts = []
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text_parts.append(extracted)

        raw_text = "\n".join(text_parts)
        return self._analyze_text(raw_text, source_file=path.name)

    def extract_from_text(self, text: str, source_file: str = "") -> ExtractedInfo:
        """Düz metinden bilgi çıkar."""
        return self._analyze_text(text, source_file=source_file)

    def extract_from_bytes(self, content: bytes, filename: str) -> ExtractedInfo:
        """Byte içeriğinden bilgi çıkar."""
        if filename.lower().endswith(".pdf"):
            import io
            reader = PdfReader(io.BytesIO(content))
            text_parts = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted)
            raw_text = "\n".join(text_parts)
        else:
            raw_text = content.decode("utf-8", errors="replace")

        return self._analyze_text(raw_text, source_file=filename)

    def _analyze_text(self, text: str, source_file: str = "") -> ExtractedInfo:
        """Metni LLM ile analiz et."""
        if not text.strip():
            return ExtractedInfo(raw_text="", anomalies=["Belge boş veya metin çıkarılamadı"])

        # Metni kısalt (LLM context limiti için)
        truncated = text[:8000] if len(text) > 8000 else text

        prompt = f"Kaynak dosya: {source_file}\n\nBelge içeriği:\n{truncated}"

        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=self.SYSTEM_PROMPT,
            )

            # JSON parse et
            content = response.content
            # Markdown code block'larını temizle
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())

            return ExtractedInfo(
                document_type=data.get("document_type", ""),
                person_name=data.get("person_name", ""),
                nationality=data.get("nationality", ""),
                rank=data.get("rank", ""),
                certifications=data.get("certifications", []),
                experience_years=data.get("experience_years", 0),
                skills=data.get("skills", []),
                contract_start=data.get("contract_start", ""),
                contract_end=data.get("contract_end", ""),
                ship_name=data.get("ship_name", ""),
                summary=data.get("summary", ""),
                raw_text=text[:500],
                confidence=data.get("confidence", 0.5),
                anomalies=data.get("anomalies", []),
            )
        except json.JSONDecodeError:
            return ExtractedInfo(
                raw_text=text[:500],
                summary="LLM yanıtı JSON formatında değildi",
                anomalies=["JSON parse hatası"],
                confidence=0.1,
            )
        except Exception as e:
            return ExtractedInfo(
                raw_text=text[:500],
                summary=f"Analiz hatası: {str(e)}",
                anomalies=[f"Hata: {str(e)}"],
                confidence=0.0,
            )

    def batch_analyze(self, file_paths: list[str | Path]) -> list[ExtractedInfo]:
        """Birden fazla belgeyi toplu analiz et."""
        results = []
        for path in file_paths:
            try:
                if str(path).lower().endswith(".pdf"):
                    results.append(self.extract_from_pdf(path))
                else:
                    text = Path(path).read_text(encoding="utf-8", errors="replace")
                    results.append(self.extract_from_text(text, source_file=str(path)))
            except Exception as e:
                results.append(ExtractedInfo(
                    anomalies=[f"Dosya okuma hatası: {str(e)}"],
                    confidence=0.0,
                ))
        return results
