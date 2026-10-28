"""Çalışan sürümün tam yedeğini oluşturur.

Hedef: ../YEDEK-CREWINTEL-<tarih>/
  kaynak/     → proje kaynak kodu (node_modules, .venv, geçici klasörler hariç)
  storage/    → yüklenen belgeler
  veritabani/ → PostgreSQL dökümü
  git/        → tüm dalları içeren git paketi (bundle)
  OKUBENI.md  → geri yükleme talimatı
"""

from __future__ import annotations

import shutil
import subprocess
from datetime import date
from pathlib import Path

SOURCE = Path.cwd()
TARGET = SOURCE.parent / f"YEDEK-CREWINTEL-{date.today().isoformat()}"

SKIP_DIRS = {
    "node_modules", ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
    "dist", "build", ".expo", ".vite", "backups", "_arsiv",
    "cooper_cms", "NGD_MONTFORT_DESIGN_PACKAGE",
}
SKIP_PREFIXES = ("CREWINTEL_HANDOFF_", "_RECOVERY_")
SKIP_SUFFIXES = (".zip", ".apk", ".aab", ".log")


def ignore(directory: str, names: list[str]) -> set[str]:
    skipped: set[str] = set()
    for name in names:
        path = Path(directory) / name
        if name in SKIP_DIRS and path.is_dir():
            skipped.add(name)
        elif name.startswith(SKIP_PREFIXES) and path.is_dir():
            skipped.add(name)
        elif path.is_file() and (name.endswith(SKIP_SUFFIXES) or name == ".env"):
            # .env sırları ayrıca saklanır (asagidaki adimda kopyalanir).
            skipped.add(name)
    return skipped


def main() -> None:
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True)

    print("1/5 kaynak kod kopyalaniyor...")
    source_copy = TARGET / "kaynak"
    shutil.copytree(SOURCE, source_copy, ignore=ignore, symlinks=False)

    # .env (ayarlar) yedeğe ayrıca eklenir: geri yüklerken gerekir.
    env_file = SOURCE / ".env"
    if env_file.exists():
        shutil.copy2(env_file, TARGET / "env-yedek.txt")

    print("2/5 storage kopyalaniyor...")
    storage = SOURCE / "storage"
    if storage.exists():
        shutil.copytree(storage, TARGET / "storage")

    print("3/5 veritabani dokumu aliniyor...")
    db_dir = TARGET / "veritabani"
    db_dir.mkdir()
    dump_path = db_dir / f"crewintel-{date.today().isoformat()}.sql"
    with dump_path.open("wb") as handle:
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "postgres",
             "pg_dump", "-U", "crewintel", "-d", "crewintel", "--clean", "--if-exists"],
            cwd=SOURCE, stdout=handle, stderr=subprocess.PIPE, check=False,
        )
    if result.returncode != 0:
        print("   UYARI: pg_dump basarisiz:", result.stderr.decode(errors="replace")[:300])
    else:
        print("   döküm:", dump_path.name, round(dump_path.stat().st_size / 1024, 1), "KB")

    print("4/5 git paketi olusturuluyor...")
    git_dir = TARGET / "git"
    git_dir.mkdir()
    subprocess.run(
        ["git", "bundle", "create", str(git_dir / "crewintel-tum-dallar.bundle"), "--all"],
        cwd=SOURCE, check=False,
    )

    print("5/5 OKUBENI yaziliyor...")
    (TARGET / "OKUBENI.md").write_text(RESTORE_DOC, encoding="utf-8")
    print("TAMAM:", TARGET)


RESTORE_DOC = """# CREWINTEL Yedek — geri yükleme talimatı

Bu klasör, programın **çalışan son hâlinin** yedeğidir.

| Klasör / dosya | İçerik |
|---|---|
| `kaynak/` | Proje kaynak kodu (KURULUM klasörü ve tüm rehberler dahil) |
| `storage/` | Yüklenen belgeler (PDF/Word/resim) |
| `veritabani/crewintel-*.sql` | PostgreSQL dökümü (tüm personel, gemi, belge kayıtları) |
| `git/crewintel-tum-dallar.bundle` | Tüm git geçmişi (tek dosya) |
| `env-yedek.txt` | `.env` ayarları — **gizli**, kimseyle paylaşmayın |

## A) Yeni bilgisayarda sıfırdan kurulum (önerilen)

1. Docker Desktop'ı kurun, bilgisayarı yeniden başlatın.
2. `kaynak/` klasörünü örneğin `C:\\CREWINTEL` altına kopyalayın.
3. `env-yedek.txt` içeriğini `C:\\CREWINTEL\\.env` olarak kaydedin.
4. `KURULUM\\kur.bat` yerine doğrudan:
   ```
   docker compose up -d --build
   ```
5. Veritabanını geri yükleyin:
   ```
   docker compose exec -T postgres psql -U crewintel -d crewintel < veritabani\\crewintel-YYYY-MM-DD.sql
   ```
6. `storage/` klasörünü `C:\\CREWINTEL\\storage` üzerine kopyalayın.
7. Tarayıcıda <http://localhost:5173> açın, `.env` içindeki yönetici
   e-postası/şifresiyle girin.

## B) Sadece kod değişikliklerini geri almak

```
git clone git/crewintel-tum-dallar.bundle CREWINTEL-geri
```

## C) Veritabanı olmadan taze başlangıç

`kaynak/` klasöründe `KURULUM\\kur.bat` çalıştırın; program boş veritabanıyla
kurulur ve `.env` içindeki yönetici hesabı oluşturulur.

> Not: `.env` ve `storage/` kişisel veri içerir. Yedeği başkasıyla
> paylaşmayın, buluta yüklerken şifreleyin.
"""


if __name__ == "__main__":
    main()
