"""Mobil "Belgelerim" sekmesi için çeviri anahtarlarını ekler (4 dil)."""

from pathlib import Path

LOCALES = Path(__file__).resolve().parents[1] / "mobile" / "i18n" / "locales"

NAV = {
    "tr": "Belgeler",
    "en": "Documents",
    "ru": "Документы",
    "ar": "المستندات",
}

INNER = {
    "tr": {
        "title": "Belgelerim",
        "subtitle": "Belge yükle, süresi dolanları gör",
        "uploadTitle": "Yeni belge yükle",
        "uploadHint": "PDF, Word, Excel veya fotoğraf seçebilirsiniz. Yüklenen belge yönetici onayına gider; tarihler otomatik okunur.",
        "uploadButton": "Belge Seç ve Yükle",
        "uploadDone": "Belge yüklendi",
        "uploadDoneHint": "Belgeniz yönetici onayına gönderildi.",
        "uploadError": "Belge yüklenemedi.",
        "loadError": "Belgeler yüklenemedi.",
        "empty": "Henüz belge yüklenmemiş.",
        "issueDate": "Düzenlenme",
        "expiryDate": "Son geçerlilik",
        "status": "Durum",
    },
    "en": {
        "title": "My documents",
        "subtitle": "Upload documents, track expiry",
        "uploadTitle": "Upload a new document",
        "uploadHint": "Pick a PDF, Word, Excel file or a photo. Uploads go to admin approval; dates are read automatically.",
        "uploadButton": "Pick and upload",
        "uploadDone": "Document uploaded",
        "uploadDoneHint": "Your document was sent for admin approval.",
        "uploadError": "Document could not be uploaded.",
        "loadError": "Documents could not be loaded.",
        "empty": "No documents uploaded yet.",
        "issueDate": "Issued",
        "expiryDate": "Valid until",
        "status": "Status",
    },
    "ru": {
        "title": "Мои документы",
        "subtitle": "Загружайте документы и следите за сроками",
        "uploadTitle": "Загрузить новый документ",
        "uploadHint": "Выберите PDF, Word, Excel или фото. Документ уходит на утверждение администратору; даты считываются автоматически.",
        "uploadButton": "Выбрать и загрузить",
        "uploadDone": "Документ загружен",
        "uploadDoneHint": "Документ отправлен на утверждение администратору.",
        "uploadError": "Не удалось загрузить документ.",
        "loadError": "Не удалось загрузить документы.",
        "empty": "Документы ещё не загружены.",
        "issueDate": "Выдан",
        "expiryDate": "Действителен до",
        "status": "Статус",
    },
    "ar": {
        "title": "مستنداتي",
        "subtitle": "ارفع المستندات وتابع تواريخ الانتهاء",
        "uploadTitle": "رفع مستند جديد",
        "uploadHint": "اختر ملف PDF أو Word أو Excel أو صورة. يُرسل المستند لموافقة المسؤول وتُقرأ التواريخ تلقائياً.",
        "uploadButton": "اختيار ورفع",
        "uploadDone": "تم رفع المستند",
        "uploadDoneHint": "تم إرسال المستند لموافقة المسؤول.",
        "uploadError": "تعذر رفع المستند.",
        "loadError": "تعذر تحميل المستندات.",
        "empty": "لم يتم رفع أي مستند بعد.",
        "issueDate": "تاريخ الإصدار",
        "expiryDate": "صالح حتى",
        "status": "الحالة",
    },
}


def patch(code: str) -> None:
    path = LOCALES / f"{code}.ts"
    text = path.read_text(encoding="utf-8")

    if "  documentsTab: {" in text:
        print(f"{code}: zaten ekli")
        return

    nav_marker = "    profile: "
    index = text.index(nav_marker)
    line_end = text.index("\n", index) + 1
    text = text[:line_end] + f"    documents: '{NAV[code]}',\n" + text[line_end:]

    lines = ["  documentsTab: {"]
    for key, value in INNER[code].items():
        lines.append(f"    {key}: '{value}',")
    lines.append("  },")

    position = text.rindex("\n};")
    text = text[:position] + "\n" + "\n".join(lines) + text[position:]
    path.write_text(text, encoding="utf-8")
    print(f"{code}: guncellendi")


def main() -> None:
    for code in ("tr", "en", "ru", "ar"):
        patch(code)


if __name__ == "__main__":
    main()
