"""CREWINTEL — kullanıcı şifresi sıfırlama / hesap listeleme aracı.

Kullanım (backend konteyneri içinden):

    # Tüm hesapları listele (şifre göstermez)
    python -m scripts.sifre_sifirla --liste

    # Belirli bir hesabın şifresini rastgele üret ve ekrana yaz
    python -m scripts.sifre_sifirla admin@crewintel.example

    # Kendi belirlediğin şifreyi ata
    python -m scripts.sifre_sifirla admin@crewintel.example --sifre "YeniSifre123!"

    # Hesap hiç yoksa admin olarak oluştur
    python -m scripts.sifre_sifirla patron@firma.com --olustur

Güvenlik notları:
  * Şifre asla veritabanına düz metin yazılmaz; bcrypt ile hash'lenir.
  * Rastgele şifre üretildiğinde yalnızca bir kez ekrana yazılır; not alın.
  * İşlem audit_logs tablosuna kaydedilir.
"""

from __future__ import annotations

import argparse
import secrets
import string
import sys

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.models.user import User
from app.services.audit import log_event

# Karıştırılması kolay karakterler (0/O, 1/l/I) bilinçli olarak dışarıda.
_ALPHABET = "".join(c for c in string.ascii_letters + string.digits + "!@#$%" if c not in "0O1lI")


def _generate_password(length: int = 16) -> str:
    """Kurumsal parola politikasına uygun, okunabilir rastgele şifre üret."""
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def _list_users(db) -> None:
    """Kayıtlı hesapları rol ve durum bilgisiyle listele."""
    users = db.query(User).order_by(User.id).all()
    if not users:
        print("Veritabanında hiç kullanıcı yok.")
        return
    print(f"{'ID':>4}  {'E-POSTA':<38} {'ROL':<8} {'AKTİF':<6} ŞİFRE")
    print("-" * 78)
    for user in users:
        has_password = "var" if user.password_hash else "YOK (şifre belirlenmemiş)"
        print(
            f"{user.id:>4}  {user.email:<38} {user.role:<8} "
            f"{'evet' if user.is_active else 'hayır':<6} {has_password}"
        )
    print("\nŞifresi 'YOK' görünen hesap giriş yapamaz; bu betikle şifre atayın.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="CREWINTEL kullanıcı şifresi sıfırlar veya hesapları listeler.",
    )
    parser.add_argument("email", nargs="?", help="Şifresi sıfırlanacak hesabın e-postası")
    parser.add_argument("--sifre", help="Kullanılacak şifre (verilmezse rastgele üretilir)")
    parser.add_argument("--liste", action="store_true", help="Hesapları listele ve çık")
    parser.add_argument("--olustur", action="store_true", help="Hesap yoksa admin olarak oluştur")
    parser.add_argument("--ad", default="CREWINTEL Yönetici", help="Yeni hesabın adı soyadı")
    args = parser.parse_args(argv)

    db = SessionLocal()
    try:
        if args.liste:
            _list_users(db)
            return 0

        if not args.email:
            parser.error("E-posta gerekli. Örnek: python -m scripts.sifre_sifirla admin@crewintel.example")

        email = args.email.strip().lower()
        user = db.query(User).filter(User.email == email).first()

        if user is None:
            if not args.olustur:
                print(f"HATA: '{email}' kayıtlı değil. Hesabı oluşturmak için --olustur ekleyin.")
                return 1
            password = args.sifre or _generate_password()
            user = User(
                email=email,
                full_name=args.ad,
                role="admin",
                is_active=True,
                password_hash=hash_password(password),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            log_event(
                db,
                "user_created_by_script",
                "user",
                user.id,
                f"Hesap betikle oluşturuldu: {email}",
                user_email="system:password_script",
            )
            print(f"Yeni hesap oluşturuldu: {email} (rol: admin)")
            print(f"  ŞİFRE: {password}")
            return 0

        password = args.sifre or _generate_password()
        if len(password) < 8:
            print("HATA: Şifre en az 8 karakter olmalı.")
            return 1

        user.password_hash = hash_password(password)
        user.is_active = True
        db.commit()
        log_event(
            db,
            "password_reset_by_script",
            "user",
            user.id,
            f"Şifre betikle sıfırlandı: {email}",
            user_email="system:password_script",
        )
        print(f"Şifre güncellendi: {email} (rol: {user.role}, hesap aktif)")
        print(f"  ŞİFRE: {password}")
        print("\nBu şifreyi not alın; ekranda bir daha gösterilmez.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
