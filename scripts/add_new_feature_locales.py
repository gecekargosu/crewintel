"""Yeni ekranların (Notlar / Maaş / Yapay Zekâ) çeviri anahtarlarını ekler.

Betik idempotenttir: anahtar zaten varsa dosyaya dokunmaz.
"""

from pathlib import Path

LOCALES = Path(__file__).resolve().parents[1] / "frontend" / "src" / "i18n" / "locales"

NAV = {
    "tr": {"notes": "Notlar", "payroll": "Maaş", "ai": "Yapay Zekâ"},
    "en": {"notes": "Notes", "payroll": "Payroll", "ai": "AI"},
    "ru": {"notes": "Заметки", "payroll": "Зарплата", "ai": "ИИ"},
    "ar": {"notes": "الملاحظات", "payroll": "الرواتب", "ai": "الذكاء الاصطناعي"},
}

SECTIONS = {
    "tr": {
        "unsupportedFormat": "{{count}} dosya reddedildi — desteklenmeyen format.",
        "notesPage": {
            "title": "Notlar",
            "subtitle": "Operasyon notları — yalnızca kendi hesabınızda görünür.",
            "noteTitle": "Not başlığı",
            "priority": "Öncelik",
            "relatedCrew": "İlgili personel",
            "deleteConfirm": "Bu not silinsin mi?",
            "markDone": "Tamamlandı",
            "reopen": "Yeniden aç",
            "priorities": {"low": "Düşük", "normal": "Normal", "high": "Yüksek", "urgent": "Acil"},
        },
        "payroll": {
            "title": "Maaş ve Ödemeler",
            "subtitle": "Personel ödemelerini kaydedin; toplamlar para birimine göre hesaplanır.",
            "amount": "Tutar",
            "currency": "Para birimi",
            "type": "Ödeme tipi",
            "paymentDate": "Ödeme tarihi",
            "description": "Açıklama",
            "addPayment": "Ödeme Ekle",
            "deleteConfirm": "Bu ödeme kaydı silinsin mi?",
            "types": {"salary": "Maaş", "bonus": "Prim", "advance": "Avans", "other": "Diğer"},
        },
        "aiPage": {
            "title": "Yapay Zekâ",
            "subtitle": "Belge metnini özetleyin veya tutarsızlıkları bulun.",
            "notConfigured": "Yapay zekâ yapılandırılmadı",
            "notConfiguredHelp": "Bu özellik isteğe bağlıdır. Anahtar eklenene kadar programın diğer tüm bölümleri normal çalışır.",
            "optionalNote": "Anahtar yalnızca sunucuda (.env) tutulur; tarayıcıya gönderilmez.",
            "textLabel": "Belge metni",
            "textPlaceholder": "Analiz edilecek metni buraya yapıştırın…",
            "summarize": "Özetle",
            "anomalies": "Tutarsızlıkları bul",
            "summary": "Özet",
        },
    },
    "en": {
        "unsupportedFormat": "{{count}} file(s) rejected — unsupported format.",
        "notesPage": {
            "title": "Notes",
            "subtitle": "Operational notes — visible only to your own account.",
            "noteTitle": "Note title",
            "priority": "Priority",
            "relatedCrew": "Related crew member",
            "deleteConfirm": "Delete this note?",
            "markDone": "Mark done",
            "reopen": "Reopen",
            "priorities": {"low": "Low", "normal": "Normal", "high": "High", "urgent": "Urgent"},
        },
        "payroll": {
            "title": "Payroll and payments",
            "subtitle": "Record crew payments; totals are grouped by currency.",
            "amount": "Amount",
            "currency": "Currency",
            "type": "Payment type",
            "paymentDate": "Payment date",
            "description": "Description",
            "addPayment": "Add payment",
            "deleteConfirm": "Delete this payment record?",
            "types": {"salary": "Salary", "bonus": "Bonus", "advance": "Advance", "other": "Other"},
        },
        "aiPage": {
            "title": "Artificial intelligence",
            "subtitle": "Summarise document text or detect inconsistencies.",
            "notConfigured": "AI is not configured",
            "notConfiguredHelp": "This feature is optional. Every other part of the program keeps working until a key is added.",
            "optionalNote": "The key stays on the server (.env) and is never sent to the browser.",
            "textLabel": "Document text",
            "textPlaceholder": "Paste the text to analyse here…",
            "summarize": "Summarise",
            "anomalies": "Find inconsistencies",
            "summary": "Summary",
        },
    },
    "ru": {
        "unsupportedFormat": "{{count}} файл(ов) отклонено — неподдерживаемый формат.",
        "notesPage": {
            "title": "Заметки",
            "subtitle": "Рабочие заметки — видны только в вашей учётной записи.",
            "noteTitle": "Заголовок заметки",
            "priority": "Приоритет",
            "relatedCrew": "Связанный сотрудник",
            "deleteConfirm": "Удалить эту заметку?",
            "markDone": "Выполнено",
            "reopen": "Открыть снова",
            "priorities": {"low": "Низкий", "normal": "Обычный", "high": "Высокий", "urgent": "Срочный"},
        },
        "payroll": {
            "title": "Зарплата и выплаты",
            "subtitle": "Учёт выплат персоналу; итоги группируются по валюте.",
            "amount": "Сумма",
            "currency": "Валюта",
            "type": "Тип выплаты",
            "paymentDate": "Дата выплаты",
            "description": "Описание",
            "addPayment": "Добавить выплату",
            "deleteConfirm": "Удалить эту выплату?",
            "types": {"salary": "Зарплата", "bonus": "Премия", "advance": "Аванс", "other": "Другое"},
        },
        "aiPage": {
            "title": "Искусственный интеллект",
            "subtitle": "Краткое содержание текста документа и поиск несоответствий.",
            "notConfigured": "ИИ не настроен",
            "notConfiguredHelp": "Функция необязательна. Без ключа все остальные разделы программы работают как обычно.",
            "optionalNote": "Ключ хранится только на сервере (.env) и не передаётся в браузер.",
            "textLabel": "Текст документа",
            "textPlaceholder": "Вставьте текст для анализа…",
            "summarize": "Кратко изложить",
            "anomalies": "Найти несоответствия",
            "summary": "Сводка",
        },
    },
    "ar": {
        "unsupportedFormat": "تم رفض {{count}} ملف — صيغة غير مدعومة.",
        "notesPage": {
            "title": "الملاحظات",
            "subtitle": "ملاحظات تشغيلية — تظهر في حسابك فقط.",
            "noteTitle": "عنوان الملاحظة",
            "priority": "الأولوية",
            "relatedCrew": "الموظف المرتبط",
            "deleteConfirm": "هل تريد حذف هذه الملاحظة؟",
            "markDone": "تم",
            "reopen": "إعادة الفتح",
            "priorities": {"low": "منخفضة", "normal": "عادية", "high": "مرتفعة", "urgent": "عاجلة"},
        },
        "payroll": {
            "title": "الرواتب والمدفوعات",
            "subtitle": "تسجيل مدفوعات الموظفين؛ تُجمع الإجماليات حسب العملة.",
            "amount": "المبلغ",
            "currency": "العملة",
            "type": "نوع الدفع",
            "paymentDate": "تاريخ الدفع",
            "description": "الوصف",
            "addPayment": "إضافة دفعة",
            "deleteConfirm": "هل تريد حذف هذه الدفعة؟",
            "types": {"salary": "راتب", "bonus": "مكافأة", "advance": "سلفة", "other": "أخرى"},
        },
        "aiPage": {
            "title": "الذكاء الاصطناعي",
            "subtitle": "تلخيص نص المستند أو كشف التناقضات.",
            "notConfigured": "لم يتم إعداد الذكاء الاصطناعي",
            "notConfiguredHelp": "هذه الميزة اختيارية. جميع أجزاء البرنامج الأخرى تعمل بشكل طبيعي بدون مفتاح.",
            "optionalNote": "يبقى المفتاح على الخادم (.env) ولا يُرسل إلى المتصفح.",
            "textLabel": "نص المستند",
            "textPlaceholder": "الصق النص المراد تحليله هنا…",
            "summarize": "تلخيص",
            "anomalies": "اكتشاف التناقضات",
            "summary": "الملخص",
        },
    },
}


def render_section(name: str, body: dict) -> str:
    lines = [f"  {name}: {{"]
    for key, value in body.items():
        if isinstance(value, dict):
            lines.append(f"    {key}: {{")
            for sub_key, sub_value in value.items():
                lines.append(f"      {sub_key}: '{sub_value}',")
            lines.append("    },")
        else:
            lines.append(f"    {key}: '{value}',")
    lines.append("  },")
    return "\n".join(lines)


def patch(code: str) -> str:
    path = LOCALES / f"{code}.ts"
    text = path.read_text(encoding="utf-8")

    if "notesPage:" in text:
        print(f"{code}: zaten ekli, atlandi")
        return

    nav_keys = NAV[code]
    marker = "  nav: {\n"
    block = "".join(f"    {key}: '{value}',\n" for key, value in nav_keys.items())
    text = text.replace(marker, marker + block, 1)

    documents = SECTIONS[code]["unsupportedFormat"]
    text = text.replace(
        "  documents: {\n",
        f"  documents: {{\n    unsupportedFormat: '{documents}',\n",
        1,
    )

    additions = "\n".join(
        render_section(name, SECTIONS[code][name])
        for name in ("notesPage", "payroll", "aiPage")
    )

    position = text.rindex("\n};")
    text = text[:position] + "\n" + additions + text[position:]
    path.write_text(text, encoding="utf-8")
    print(f"{code}: guncellendi")


def main() -> None:
    for code in ("tr", "en", "ru", "ar"):
        patch(code)


if __name__ == "__main__":
    main()
