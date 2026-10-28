"""CREWINTEL Match Engine.

Pipeline:
    extract_text -> extract_entities -> classify -> find_candidates -> score
    -> conflict_check -> decision -> (dry_run: raporla | gerçek: yaz)

Tasarım ilkeleri:
- Dosya adı yalnızca yardımcı sinyaldir; içerik her zaman önceliklidir.
- Güçlü identifier (pasaport/seaman/national id) eşleşmesi isimden üstündür.
- Çelişkili bilgi (aynı identifier iki kişide, isim+identifier uyuşmazlığı)
  otomatik eşleşmeyi engeller -> CONFLICT.
- Belirsiz/çok yakın adaylar -> REVIEW_REQUIRED (asla zorla bağlanmaz).
- Dry-run modu hiçbir DB yazmadan rapor üretir.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.crew_member import CrewMember
from app.models.document import Document
from app.models.document_match import DocumentMatch
from app.services.document_processing import (
    classify_document_type,
    extract_metadata,
    extract_name,
    normalize,
    normalize_identifier,
)

# ── Karar sabitleri ──────────────────────────────────────────────────────────
AUTO_MATCH = "AUTO_MATCH"
REVIEW = "REVIEW_REQUIRED"
CONFLICT = "MATCH_CONFLICT"
UNMATCHED = "UNMATCHED"
FAILED = "FAILED"

# Status eşleme: karar -> documents.match_status
DECISION_TO_STATUS = {
    AUTO_MATCH: "matched",
    REVIEW: "review_required",
    CONFLICT: "conflict",
    UNMATCHED: "unmatched",
    FAILED: "failed",
}

# ── Ağırlıklar (deneyle kalibre edildi; isim tek başına asla 90+ yapamaz) ────
WEIGHTS = {
    "passport_exact": 100,
    "seaman_book_exact": 100,
    "national_id_exact": 100,
    "crew_id_exact": 95,
    "email_exact": 90,
    # İsim tam eşleşmesi: 90 — tek başına auto-match eder (eski sistem 95'ti;
    # aynı isimli iki personel durumunda 90 vs 90 -> margin 0 -> REVIEW kalır).
    "name_exact": 90,
    "name_normalized": 65,
    "dob_exact": 50,
    "phone_exact": 40,
    "filename_name": 25,
    "name_fuzzy": 15,
}

# AUTO_MATCH için alt sınır ve liderlik marjı.
AUTO_MATCH_THRESHOLD = 90
LEAD_MARGIN = 15
# REVIEW_REQUIRED alt sınırı (altında kalırsa UNMATCHED).
REVIEW_THRESHOLD = 35

# İsim eşleşme oranı sınıfları.
EXACT_NAME_RATIO = 0.999
NORMALIZED_NAME_RATIO = 0.98
FUZZY_NAME_RATIO = 0.82


@dataclass
class Candidate:
    crew_id: int
    first_name: str
    last_name: str
    score: int = 0
    signals: list[str] = field(default_factory=list)


@dataclass
class MatchResult:
    decision: str
    best_candidate: Candidate | None = None
    candidates: list[Candidate] = field(default_factory=list)
    signals: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    reason: str = ""


class EntityExtractor:
    """Belge içeriğinden personel entity'lerini çıkarır.

    Mevcut extract_metadata'ya ek olarak telefon, national id, crew id,
    document number, employer ve vessel çıkarımı yapar.
    """

    PHONE_RE = re.compile(
        r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3}[\s.-]?\d{2,4}[\s.-]?\d{2,4}",
    )
    NATIONAL_ID_RE = re.compile(
        r"(?:national\s*id|tc\s*(?:kimlik)?|kimlik\s*no|tckn)\s*[:#-]?\s*([0-9]{11})",
        re.IGNORECASE,
    )
    CREW_ID_RE = re.compile(
        r"(?:crew\s*id|crew\s*no|personel\s*no|employee\s*id)\s*[:#-]?\s*([A-Z0-9-]{2,15})",
        re.IGNORECASE,
    )
    EMPLOYER_RE = re.compile(
        r"(?:employer|company|şirket|sirket|firma|vessel\s*operator)\s*[:#-]?\s*([A-Za-zÇĞİÖŞÜçğıöşü0-9 .&'-]{3,60})",
        re.IGNORECASE,
    )
    VESSEL_RE = re.compile(
        r"(?:vessel|ship|gemi)\s*(?:name)?\s*[:#-]?\s*([A-Za-zÇĞİÖŞÜçğıöşü0-9 .'-]{2,40})",
        re.IGNORECASE,
    )
    DOCUMENT_NUMBER_RE = re.compile(
        r"(?:document\s*(?:no|number)|belge\s*no|belge\s*numarası|belge\s*numarasi)\s*[:#-]?\s*([A-Z0-9-]{4,20})",
        re.IGNORECASE,
    )

    def extract(self, filename: str, text: str, metadata: dict) -> dict:
        combined = f"{filename}\n{text}"
        entities = dict(metadata)

        phone_match = self.PHONE_RE.search(combined)
        if phone_match:
            raw = re.sub(r"[^\d+]", "", phone_match.group(0))
            if 7 <= len(raw) <= 15:
                entities["phone"] = raw

        national_id = self.NATIONAL_ID_RE.search(combined)
        if national_id:
            entities["national_id"] = national_id.group(1)

        crew_id = self.CREW_ID_RE.search(combined)
        if crew_id:
            entities["crew_id"] = crew_id.group(1).upper()

        employer = self.EMPLOYER_RE.search(combined)
        if employer:
            entities["employer"] = employer.group(1).strip()

        vessel = self.VESSEL_RE.search(combined)
        if vessel:
            entities["vessel"] = vessel.group(1).strip()

        doc_number = self.DOCUMENT_NUMBER_RE.search(combined)
        if doc_number:
            entities["document_number"] = doc_number.group(1).upper()

        return entities


def _keyword_in(haystack: str, keyword: str) -> bool:
    """Kısa anahtar kelimelerde (cv, goc…) kelime sınırı arar."""
    if len(keyword) <= 3:
        return re.search(rf"\b{re.escape(keyword)}\b", haystack) is not None
    return keyword in haystack


class DocumentClassifier:
    """Belge tipini içerikten belirler (genişletilmiş taksonomi).

    Temel tipler (cv, passport, seaman_book, stcw, goc, medical, contract)
    `document_processing.classify_document_type` ile belirlenir; o fonksiyon
    başlık bölgesini, dosya adını ve gövdeyi ayrı ağırlıklarla puanlar.

    Eskiden bu sınıf "ilk eşleşen anahtar kelime kazanır" mantığıyla
    çalışıyordu ve belge gövdesindeki tek bir satır sınıflandırmayı
    belirleyebiliyordu: bir İŞ SÖZLEŞMESİ içinde geçen "medical certificate"
    satırı belgeyi "medical" yapıyordu. Artık tek doğru kaynak temel
    sınıflandırıcıdır; buradaki ek (alias) tipler yalnızca o "other"
    dediğinde, aynı ağırlıklı mantıkla aranır.
    """

    # Yalnızca temel sınıflandırıcının kapsamadığı ek tipler.
    EXTRA_RULES: dict[str, tuple[str, ...]] = {
        "employment_contract": ("employment contract",),
        "training_certificate": (
            "training certificate",
            "certificate of training",
            "egitim belgesi",
        ),
        "certificate": (
            "certificate of competency",
            "competency certificate",
            "certificate",
            "sertifika",
        ),
        "license": ("license", "licence", "lisans"),
        "id_card": ("identity card", "id card", "kimlik", "identity"),
        "visa": ("visa", "vize"),
        "work_permit": ("work permit", "calisma izni"),
        "reference_letter": (
            "reference letter",
            "letter of reference",
            "recommendation letter",
            "referans mektubu",
        ),
        "education_certificate": (
            "education certificate",
            "school certificate",
            "diploma",
            "mezuniyet",
        ),
    }

    def classify(self, filename: str, text: str, metadata: dict) -> str:
        base = classify_document_type(filename, text)
        if base != "other":
            return base
        return self._classify_extra(filename, text) or metadata.get("document_type") or "other"

    def _classify_extra(self, filename: str, text: str) -> str | None:
        """Ek tipler için ağırlıklı arama (başlık > dosya adı > gövde)."""
        lines = [line for line in text.splitlines() if line.strip()]
        header = normalize("\n".join(lines[:3]))
        stem = normalize(Path(filename).stem)
        body = normalize(f"{filename}\n{text}")

        best: str | None = None
        best_score = 0.0
        for kind, words in self.EXTRA_RULES.items():
            score = 0.0
            for word in words:
                keyword = normalize(word)
                if not keyword:
                    continue
                weight = 1 + len(keyword) / 20
                if _keyword_in(header, keyword):
                    score += 3 * weight
                if _keyword_in(stem, keyword):
                    score += 4 * weight
                elif _keyword_in(body, keyword):
                    score += weight
            if score > best_score:
                best, best_score = kind, score

        # Yalnızca gövdede geçen genel bir kelime (ör. "certificate") yeterli
        # değildir; başlık veya dosya adı eşleşmesi aranır.
        return best if best_score >= 2 else None


class CrewCandidateFinder:
    """DB'den aday personel listesi bulur.

    Güçlü identifier'larla doğrudan sorgu; isim için tüm aktif personeli çeker
    (mevcut ölçekte kabul edilebilir; 5000+ için SQL isim filtreleme roadmap).
    """

    def find(self, db: Session, entities: dict, first_name: str | None, last_name: str | None) -> list[CrewMember]:
        candidates: list[CrewMember] = []
        seen: set[int] = set()

        def _add(crew: CrewMember | None) -> None:
            if crew is not None and crew.id not in seen:
                seen.add(crew.id)
                candidates.append(crew)

        # 1) Güçlü identifier sorguları.
        for attribute, value in (
            ("passport_number", entities.get("passport_number")),
            ("seaman_book_number", entities.get("seaman_book_number")),
        ):
            if value:
                for crew in db.query(CrewMember).filter(
                    getattr(CrewMember, attribute).isnot(None),
                ).all():
                    if normalize_identifier(getattr(crew, attribute)) == normalize_identifier(value):
                        _add(crew)

        if entities.get("email"):
            _add(
                db.query(CrewMember)
                .filter(CrewMember.email == entities["email"])
                .first()
            )

        if entities.get("national_id"):
            # profile_data generic JSON kolonudur; PostgreSQL JSONB `.astext`
            # burada bulunmadığı için (ve SQLite'ta hiç olmadığı için) adaylar
            # Python tarafında normalize edilerek karşılaştırılır. Aynı yaklaşım
            # pasaport/seaman aramasında da kullanılıyor.
            wanted = normalize_identifier(entities["national_id"])
            if wanted:
                for crew in (
                    db.query(CrewMember)
                    .filter(CrewMember.profile_data.isnot(None))
                    .all()
                ):
                    stored = (crew.profile_data or {}).get("national_id")
                    if stored and normalize_identifier(str(stored)) == wanted:
                        _add(crew)
                        break

        if entities.get("crew_id"):
            numeric = re.sub(r"[^0-9]", "", str(entities["crew_id"]))
            if numeric.isdigit():
                _add(db.get(CrewMember, int(numeric)))

        # 2) İsim eşleşmesi (ilk ad + soyad normalize).
        if first_name and last_name:
            nf, nl = normalize(first_name), normalize(last_name)
            for crew in db.query(CrewMember).all():
                if normalize(crew.first_name) == nf and normalize(crew.last_name) == nl:
                    _add(crew)

        # 3) Güvenli fuzzy adaylar: her iki alanda da yüksek benzerlik (>= 0.85).
        #    Skorlayıcı bunlara düşük puan verir (name_fuzzy=15) — asla auto-match
        #    edemez; yalnızca incelemeye düşer.
        if first_name and last_name and not candidates:
            nf, nl = normalize(first_name), normalize(last_name)
            for crew in db.query(CrewMember).all():
                cf, cl = normalize(crew.first_name), normalize(crew.last_name)
                first_ratio = SequenceMatcher(None, nf, cf).ratio()
                last_ratio = SequenceMatcher(None, nl, cl).ratio()
                if min(first_ratio, last_ratio) >= FUZZY_NAME_RATIO:
                    _add(crew)

        return candidates


class MatchScorer:
    """Her aday için sinyal bazlı puan hesaplar.

    Çelişki tespiti: güçlü identifier adayda yoksa/uyuşmuyorsa ve isim başka
    bir adayla eşleşiyorsa -> conflict sinyali. Skor çelişkide düşürülür.
    """

    def score(
        self,
        crew: CrewMember,
        entities: dict,
        first_name: str | None,
        last_name: str | None,
        filename: str,
    ) -> tuple[int, list[str], list[str]]:
        score = 0
        signals: list[str] = []
        conflicts: list[str] = []

        # Güçlü identifier'lar: eşleşme +100, uyuşmazlık -> çelişki.
        for attribute, signal, label in (
            ("passport_number", "passport_exact", "pasaport"),
            ("seaman_book_number", "seaman_book_exact", "seaman book"),
        ):
            doc_value = entities.get(attribute)
            crew_value = getattr(crew, attribute)
            if doc_value:
                if crew_value and normalize_identifier(doc_value) == normalize_identifier(crew_value):
                    score += WEIGHTS[signal]
                    signals.append(signal)
                elif crew_value:
                    conflicts.append(f"{label} uyuşmazlığı (belge: {doc_value}, kayıt: {crew_value})")

        # E-posta.
        doc_email = (entities.get("email") or "").lower()
        crew_email = (crew.email or "").lower()
        if doc_email and crew_email:
            if doc_email == crew_email:
                score += WEIGHTS["email_exact"]
                signals.append("email_exact")
            else:
                conflicts.append("e-posta uyuşmazlığı")

        # Doğum tarihi.
        doc_dob = entities.get("date_of_birth")
        if doc_dob and crew.date_of_birth:
            if doc_dob == crew.date_of_birth:
                score += WEIGHTS["dob_exact"]
                signals.append("dob_exact")
            else:
                conflicts.append("doğum tarihi uyuşmazlığı")

        # İsim.
        if first_name and last_name:
            nf, nl = normalize(first_name), normalize(last_name)
            cf, cl = normalize(crew.first_name), normalize(crew.last_name)
            if nf == cf and nl == cl:
                score += WEIGHTS["name_exact"]
                signals.append("name_exact")
            else:
                first_ratio = SequenceMatcher(None, nf, cf).ratio()
                last_ratio = SequenceMatcher(None, nl, cl).ratio()
                similarity = (first_ratio + last_ratio) / 2
                if similarity >= NORMALIZED_NAME_RATIO:
                    score += WEIGHTS["name_normalized"]
                    signals.append("name_normalized")
                elif similarity >= FUZZY_NAME_RATIO:
                    score += WEIGHTS["name_fuzzy"]
                    signals.append("name_fuzzy")

        # Dosya adı sinyali (yalnızca yardımcı).
        filename_norm = normalize(Path(filename).stem)
        if first_name and last_name and filename_norm:
            if normalize(first_name) in filename_norm or normalize(last_name) in filename_norm:
                score += WEIGHTS["filename_name"]
                signals.append("filename_name")

        # Telefon.
        doc_phone = entities.get("phone")
        if doc_phone and crew.phone:
            if re.sub(r"[^\d]", "", doc_phone) == re.sub(r"[^\d]", "", crew.phone):
                score += WEIGHTS["phone_exact"]
                signals.append("phone_exact")

        # Çelişkiler skoru düşürür: otomatik eşleşmeyi engellemek için.
        if conflicts:
            score = min(score, 60)  # conflict varken asla 90+ (auto-match) olamaz.

        return score, signals, conflicts


class MatchDecisionEngine:
    """Aday puanlarından karar üretir.

    - AUTO_MATCH: en iyi puan >= threshold VE ikinci adaydan marj kadar önde.
    - REVIEW_REQUIRED: en iyi puan >= review threshold (belirsiz/çok aday).
    - CONFLICT: identifier çelişkisi olan en iyi aday (yukarıda skor kırpıldı)
      yine de en yüksekse ve çelişki belirginse -> incelemeye.
    - UNMATCHED: hiçbir aday eşiğe ulaşamadı.
    """

    def decide(self, candidates: list[Candidate]) -> MatchResult:
        if not candidates:
            return MatchResult(
                decision=UNMATCHED,
                reason="Hiçbir aday bulunamadı.",
            )

        ordered = sorted(candidates, key=lambda c: c.score, reverse=True)
        best = ordered[0]
        second = ordered[1] if len(ordered) > 1 else None

        if best.score >= AUTO_MATCH_THRESHOLD:
            if second is None or best.score - second.score >= LEAD_MARGIN:
                return MatchResult(
                    decision=AUTO_MATCH,
                    best_candidate=best,
                    candidates=ordered,
                    signals=best.signals,
                    reason=f"En iyi aday {best.score} puan, liderlik marjı yeterli.",
                )
            # İki aday eşit ve yüksekse: ortak güçlü tanımlayıcı (aynı pasaport/
            # seaman iki personelde kayıtlı) -> CONFLICT; yalnızca isim eşitliği
            # (aynı isimli iki personel) -> REVIEW.
            shared_strong = set(best.signals) & set(second.signals) & {
                "passport_exact",
                "seaman_book_exact",
                "national_id_exact",
                "email_exact",
            }
            if shared_strong:
                return MatchResult(
                    decision=CONFLICT,
                    best_candidate=best,
                    candidates=ordered,
                    signals=best.signals,
                    conflicts=list(shared_strong),
                    reason=f"Güçlü tanımlayıcı ({', '.join(shared_strong)}) birden fazla personelde kayıtlı.",
                )
            return MatchResult(
                decision=REVIEW,
                best_candidate=best,
                candidates=ordered,
                signals=best.signals,
                reason=f"En iyi aday {best.score} ancak ikinci aday çok yakın ({second.score}).",
            )

        if best.score >= REVIEW_THRESHOLD:
            return MatchResult(
                decision=REVIEW,
                best_candidate=best,
                candidates=ordered,
                signals=best.signals,
                reason=f"En iyi aday {best.score} puan — inceleme gerekli.",
            )

        return MatchResult(
            decision=UNMATCHED,
            candidates=ordered,
            reason=f"En iyi aday {best.score} puan eşiğin altında.",
        )


class MatchEngine:
    """Pipeline orkestrasyonu.

    dry_run=True: hiçbir DB yazmaz (DocumentMatch dahil), yalnızca sonuç döner.
    dry_run=False: kararı belgeye uygular + DocumentMatch kaydı oluşturur.
    """

    def __init__(self, db: Session, actor_email: str | None = None):
        self.db = db
        self.actor_email = actor_email
        self.extractor = EntityExtractor()
        self.classifier = DocumentClassifier()
        self.finder = CrewCandidateFinder()
        self.scorer = MatchScorer()
        self.decider = MatchDecisionEngine()

    def process(
        self,
        document: Document,
        text: str | None = None,
        dry_run: bool = False,
    ) -> MatchResult:
        filename = document.original_filename
        if text is None:
            text = document.extracted_text or ""

        metadata = extract_metadata(filename, text)
        entities = self.extractor.extract(filename, text, metadata)
        document_type = self.classifier.classify(filename, text, metadata)

        # Doküman tipini güncelle (yalnızca gerçek modda; dry_run'da dokunma).
        if not dry_run and document.document_type != document_type:
            document.document_type = document_type

        first_name, last_name = extract_name(filename, text)

        crew_candidates = self.finder.find(
            self.db, entities, first_name, last_name
        )

        scored: list[Candidate] = []
        for crew in crew_candidates:
            score, signals, conflicts = self.scorer.score(
                crew, entities, first_name, last_name, filename
            )
            if score == 0 and not conflicts:
                continue
            candidate = Candidate(
                crew_id=crew.id,
                first_name=crew.first_name,
                last_name=crew.last_name,
                score=score,
                signals=signals,
            )
            scored.append(candidate)
            # Çelişkili en iyi adayı da karar motoruna taşı (conflict için).
            if conflicts:
                candidate.signals = list(set(signals) | {f"conflict:{c}" for c in conflicts})

        result = self.decider.decide(scored)

        if dry_run:
            return result

        # Kararı uygula.
        status = DECISION_TO_STATUS.get(result.decision, "pending")
        # Güven skoru arayüzde yüzde olarak gösterilir; birden fazla sinyal
        # (pasaport + isim + doğum tarihi) toplandığı için ham skor 100'ü
        # aşabiliyordu ("%215" gibi). 0-100 aralığına sıkıştırılır; ham skor
        # audit/DocumentMatch kaydında korunur.
        raw_score = result.best_candidate.score if result.best_candidate else 0
        confidence = max(0, min(100, int(raw_score)))

        if result.decision == AUTO_MATCH and result.best_candidate:
            document.crew_member_id = result.best_candidate.crew_id
            document.match_status = "matched"
            document.match_confidence = confidence
        elif result.decision == UNMATCHED:
            document.match_status = "unmatched"
            document.match_confidence = confidence
        else:
            # REVIEW / CONFLICT: bağlama, incelemeye bırak.
            document.match_status = status
            document.match_confidence = confidence

        self._log_match(document, result)

        return result

    def _log_match(self, document: Document, result: MatchResult) -> None:
        """DocumentMatch + audit log kaydı oluşturur."""
        self.db.add(DocumentMatch(
            document_id=document.id,
            candidate_crew_id=(
                result.best_candidate.crew_id if result.best_candidate else None
            ),
            final_crew_id=(
                result.best_candidate.crew_id
                if result.decision == AUTO_MATCH and result.best_candidate
                else None
            ),
            score=result.best_candidate.score if result.best_candidate else 0,
            decision=result.decision,
            signals={
                signal: WEIGHTS.get(signal.split(":")[0], 0)
                for signal in (result.best_candidate.signals if result.best_candidate else [])
            }
            if result.best_candidate
            else {},
            candidates=[
                {
                    "crew_id": c.crew_id,
                    "first_name": c.first_name,
                    "last_name": c.last_name,
                    "score": c.score,
                    "signals": c.signals,
                }
                for c in result.candidates
            ],
            actor_email=self.actor_email,
        ))

    def manual_override(
        self,
        document: Document,
        crew_member_id: int | None,
    ) -> None:
        """Kullanıcı onayı: belgeyi personele bağlar veya bağlantıyı kaldırır.

        crew_member_id=None -> eşleşmemiş olarak işaretler.
        """
        old_crew_id = document.crew_member_id
        document.crew_member_id = crew_member_id
        if crew_member_id is not None:
            document.match_status = "matched"
            document.match_confidence = 100
        else:
            document.match_status = "unmatched"
            document.match_confidence = 0

        self.db.add(DocumentMatch(
            document_id=document.id,
            candidate_crew_id=old_crew_id,
            final_crew_id=crew_member_id,
            score=100 if crew_member_id is not None else 0,
            decision="MATCH_OVERRIDE",
            signals={"manual": 1},
            candidates=[],
            actor_email=self.actor_email,
        ))
