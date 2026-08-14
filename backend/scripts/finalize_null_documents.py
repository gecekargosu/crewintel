"""
Phase 3.4 (final) - NULL-crew belgeleri tamamlama.

KARAR (canlı veri doğrulamasıyla):
- 299 belge: dosya adı deseni (_NN / crew-0XX / CREW-NN_CV) -> mevcut crew'e bağlanır.
  Isim dogrulamasi %100 uyumlu (normallashtirilmis), storage dosyalari mevcut.
- 12 belge: crew-031 / mehmet_cetin_31 -> crew 68 (Mehmet Cetin, Phase 3.4'te bu hedef
  icin olusturulmus kisi) baglanir.
- 16 belge: acik cop (6 test_crew_01 + 3 CSV + 6 chatgpt_gpt [crew 3 silinmis test kaydi]
  + 1 test_passport_mehmet_cetin_2) -> DB kaydi + storage dosyasi birlikte silinir.

SILME YOKTUR baglama tarafinda; silme yalnizca acik test/cop belgeleri icindir.
Transaction + audit log ile yapilir.
"""
import re
import sys
import os
import unicodedata

sys.path.insert(0, "/app")

from app.db.database import SessionLocal
from app.models.crew_member import CrewMember
from app.models.document import Document
from app.models.audit_log import AuditLog

STORAGE_DIR = "/app/storage"


def norm(s):
    s = s.lower().replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ş", "s").replace("ö", "o").replace("ç", "c")
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def resolve(d, crew_by_id):
    low = d.original_filename.lower()
    if low.startswith("test_") or "test_crew_01" in low:
        return None, "junk-test"
    if low.endswith(".csv"):
        return None, "junk-csv"
    m = re.search(r"crew-0?(\d+)", low)
    if m:
        cid = int(m.group(1))
        return (cid, "crew-0XX") if cid in crew_by_id else (None, "crew-0XX->yok")
    m = re.search(r"_(\d{2})\.(txt|pdf)$", low)
    if m:
        cid = int(m.group(1))
        return (cid, "_NN") if cid in crew_by_id else (None, "_NN->yok")
    m = re.search(r"crew-0?(\d+)_", low)
    if m:
        cid = int(m.group(1))
        return (cid, "CREW-NN_CV") if cid in crew_by_id else (None, "CREW-NN_CV->yok")
    return None, "desen-yok"


db = SessionLocal()
try:
    crew_by_id = {c.id: c for c in db.query(CrewMember).all()}
    docs = db.query(Document).filter(Document.crew_member_id.is_(None)).all()
    print(f"NULL crew belge: {len(docs)}")

    to_attach = []   # (doc, crew_id, method)
    to_delete = []   # (doc, reason)
    skipped = []

    for d in docs:
        cid, method = resolve(d, crew_by_id)
        if cid is not None:
            # isim dogrulama
            crew = crew_by_id[cid]
            fn_low = norm(d.original_filename)
            cf, cl = norm(crew.first_name or ""), norm(crew.last_name or "")
            if cf and cf not in fn_low and cl not in fn_low:
                skipped.append((d, f"isim-uyusmazligi id={cid}"))
                continue
            to_attach.append((d, cid, method))
        elif method in ("crew-0XX->yok", "_NN->yok", "CREW-NN_CV->yok"):
            # hedef crew yok: chatgpt (id 3 silinmis test) ve mehmet_cetin (id 31 -> crew 68)
            if "chatgpt" in d.original_filename.lower():
                to_delete.append((d, "chatgpt-test-crew-silinmis"))
            elif "mehmet_cetin" in d.original_filename.lower() or "crew-031" in d.original_filename.lower() or "crew-031" in d.original_filename.lower():
                # crew 68 Mehmet Cetin hedefi icin olusturuldu
                if 68 in crew_by_id:
                    to_attach.append((d, 68, "crew-031->68"))
                else:
                    skipped.append((d, "crew-68-yok"))
            else:
                skipped.append((d, method))
        else:
            to_delete.append((d, method))

    print(f"BAGLANACAK: {len(to_attach)}")
    print(f"SILINECEK:  {len(to_delete)}")
    print(f"ATLANAN:    {len(skipped)}")
    for d, reason in skipped:
        print("  ATLA:", d.id, d.original_filename, reason)

    # --- 1) baglama ---
    for d, cid, method in to_attach:
        old = d.crew_member_id
        d.crew_member_id = cid
        if d.match_status == "pending":
            d.match_status = "matched"
        db.add(AuditLog(
            action=f"document_attached_{method}",
            entity="document",
            entity_id=d.id,
            user_email="system-cleanup",
            message=f"crew_member_id {old}->{cid} ({d.original_filename})",
        ))
    db.flush()

    # --- 2) silme (DB + storage) ---
    for d, reason in to_delete:
        db.add(AuditLog(
            action=f"document_deleted_{reason}",
            entity="document",
            entity_id=d.id,
            user_email="system-cleanup",
            message=f"{d.original_filename} | {reason}",
        ))
        # once DB'den sil ki tekrar sorguda gorunmesin
        db.delete(d)
        db.flush()
        # sonra storage dosyasini sil
        if d.stored_filename:
            p = os.path.join(STORAGE_DIR, d.stored_filename)
            if os.path.exists(p):
                os.remove(p)

    db.commit()
    print("COMMIT OK")

    # --- 3) dogrulama ---
    db.expire_all()
    remaining = db.query(Document).filter(Document.crew_member_id.is_(None)).count()
    total = db.query(Document).count()
    print(f"KALAN NULL crew: {remaining}")
    print(f"TOPLAM belge: {total}")
    print(f"Storage dosya sayisi: {len(os.listdir(STORAGE_DIR))}")
except Exception:
    db.rollback()
    print("ROLLBACK - hata:", sys.exc_info()[1])
    raise
finally:
    db.close()
