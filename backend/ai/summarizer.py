"""CREWINTEL Summarizer — Belge ve veri özetleme.

Belgeleri, kontratları, raporları özetler.
"""

from __future__ import annotations

from ai.llm_client import LLMClient


class Summarizer:
    """Belge özetleme motoru."""

    SYSTEM_PROMPT = """Sen CREWINTEL için bir belge özetleme uzmanısın.
Verilen belgeyi kısa, net ve profesyonelce özetle.
Özellikle gemi personeli yönetimi açısından kritik bilgileri vurgula.
Maksimum 3-4 paragraf yaz."""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()

    def summarize(self, text: str, context: str = "") -> str:
        """Metni özetle."""
        prompt = f"Belgeyi özetle:\n\n{text}"
        if context:
            prompt = f"Bağlam: {context}\n\n{prompt}"

        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=self.SYSTEM_PROMPT,
        )
        return response.content

    def summarize_crew(self, profile_text: str) -> str:
        """Personel profilini özetle."""
        prompt = f"Aşağıdaki gemi personeli profilini özetle:\n\n{profile_text}"
        system = (
            "Sen CREWINTEL için bir personel özetleme uzmanısın. "
            "Profildeki kritik bilgileri (rütbeler, sertifikalar, deneyim, "
            "uyruk, özel yetenekler) vurgula. Kısa ve profesyonelce yaz."
        )

        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=system,
        )
        return response.content

    def summarize_contract(self, contract_text: str) -> str:
        """Kontratı özetle."""
        prompt = f"Aşağıdaki personel kontratını özetle:\n\n{contract_text}"
        system = (
            "Sen CREWINTEL için bir kontrat özetleme uzmanısın. "
            "Kontratın süresini, maaşını, görev kapsamını, "
            "özel koşullarını ve süre sonu tarihlerini vurgula."
        )

        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=system,
        )
        return response.content
