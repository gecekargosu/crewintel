"""Generate PDF and DOCX from the final CV HTML."""
import os
import shutil

# Paths
html_path = r"C:\CREWINTEL\cengiz_kilic_cv_final.html"
output_dir = r"C:\Users\isitm\Desktop\Cengiz_Kilic_CV_Yenilenmis"
os.makedirs(output_dir, exist_ok=True)

# === 1. Generate PDF with Playwright ===
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file:///{html_path.replace(os.sep, '/')}")
        page.pdf(
            path=os.path.join(output_dir, "cengiz_kilic_cv_final.pdf"),
            format="A4",
            margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"},
            print_background=True
        )
        browser.close()
    print("PDF generated successfully!")
except Exception as e:
    print(f"PDF generation failed: {e}")

# === 2. Generate DOCX ===
try:
    from docx import Document
    from docx.shared import Pt, Inches, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE

    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.2)
        section.right_margin = Cm(2.2)

    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(10)
    style.font.color.rgb = RGBColor(0x1a, 0x1a, 0x1a)
    style.paragraph_format.space_after = Pt(4)
    style.paragraph_format.line_spacing = 1.15

    def add_heading_styled(text, level=1):
        h = doc.add_heading(text, level=level)
        for run in h.runs:
            run.font.color.rgb = RGBColor(0x1a, 0x1a, 0x1a)
            run.font.name = 'Calibri'
        return h

    def add_para(text, bold=False, italic=False, size=10, color=None, align=None, space_after=4):
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.bold = bold
        run.italic = italic
        run.font.size = Pt(size)
        run.font.name = 'Calibri'
        if color:
            run.font.color.rgb = RGBColor(*color)
        if align:
            p.alignment = align
        p.paragraph_format.space_after = Pt(space_after)
        return p

    def add_bullet(text, bold_prefix=""):
        p = doc.add_paragraph(style='List Bullet')
        if bold_prefix:
            run_bold = p.add_run(bold_prefix)
            run_bold.bold = True
            run_bold.font.size = Pt(9.5)
            run_bold.font.name = 'Calibri'
        run = p.add_run(text)
        run.font.size = Pt(9.5)
        run.font.name = 'Calibri'
        p.paragraph_format.space_after = Pt(2)
        return p

    # HEADER
    add_para("Cengiz Kılıç", bold=True, size=22, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=2)
    add_para("AI & Machine Learning Student · Full-Stack Developer · AI Automation Specialist", size=10, color=(0x44,0x44,0x44), space_after=4)
    add_para("+90 532 327 61 21  |  cengizkilic1980@gmail.com  |  İzmir, Türkiye", size=9, color=(0x33,0x33,0x33), space_after=1)
    add_para("linkedin.com/in/cengizkilic  |  github.com/cengizkilic", size=9, color=(0x33,0x33,0x33), space_after=1)
    add_para("Full-time · Remote / Hybrid · No travel restrictions", size=9, color=(0x55,0x55,0x55), space_after=8)

    # SEPARATOR
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)

    # PROFESYONEL ÖZET
    add_heading_styled("PROFESYONEL ÖZET", level=2)
    add_para("20 yılı aşkın profesyonel deneyimini, girişimcilik geçmişini ve ürün geliştirme bilgisini AI/ML, software development ve automation alanına taşıyan bir geliştirici. İstanbul Rumeli Üniversitesi Yapay Zeka ve Makine Öğrenmesi lisans programında eğitimine devam ediyor.", space_after=4)
    add_para("CrewIntel adlı full-stack crew management sistemini sıfırdan geliştirerek Python/FastAPI backend, PostgreSQL veritabanı, React frontend, Android mobil uygulama ve Groq LLM entegrasyonu içeren tam bir AI uygulaması oluşturdu. n8n workflow otomasyonu, prompt engineering, AI agent tasarımı ve LLM tabanlı uygulama geliştirme konularında aktif çalışmalar yürütüyor.", space_after=8)

    # EĞİTİM
    add_heading_styled("EĞİTİM", level=2)
    p = doc.add_paragraph()
    run = p.add_run("İstanbul Rumeli Üniversitesi — Mühendislik Fakültesi")
    run.bold = True
    run.font.size = Pt(10)
    run.font.name = 'Calibri'
    run2 = p.add_run("                                                                                              2025 – Devam Ediyor (Tahmini: 2029)")
    run2.font.size = Pt(9)
    run2.font.color.rgb = RGBColor(0x55,0x55,0x55)
    run2.font.name = 'Calibri'
    p.paragraph_format.space_after = Pt(1)
    add_para("Yapay Zeka ve Makine Öğrenmesi — Lisans Programı", size=9.5, color=(0x33,0x33,0x33), space_after=1)
    add_para("Bölüm Öğrenci Temsilcisi · Algoritmalar, Veri Yapıları, Machine Learning, Deep Learning, Software Development, AI Applications", size=9, color=(0x55,0x55,0x55), space_after=6)

    p = doc.add_paragraph()
    run = p.add_run("Karadeniz Teknik Üniversitesi")
    run.bold = True
    run.font.size = Pt(10)
    run.font.name = 'Calibri'
    run2 = p.add_run("                                                                                              1999 – 2001 · Mezun")
    run2.font.size = Pt(9)
    run2.font.color.rgb = RGBColor(0x55,0x55,0x55)
    run2.font.name = 'Calibri'
    p.paragraph_format.space_after = Pt(1)
    add_para("İnşaat Teknikerliği — Ön Lisans", size=9.5, color=(0x33,0x33,0x33), space_after=8)

    # TEKNİK YETKİNLİKLER
    add_heading_styled("TEKNİK YETKİNLİKLER", level=2)
    add_bullet("LLM (Groq / llama-3.3-70b-versatile) · Prompt Engineering · AI Agents · AI Application Development · Document Analysis with LLM · AI-powered Matching Systems", bold_prefix="AI & Machine Learning: ")
    add_bullet("n8n · API Integration · Workflow Automation · AI-assisted Automation · Multi-step Prompt Architectures", bold_prefix="AI Automation & Workflow: ")
    add_bullet("Python · FastAPI · SQLAlchemy · PostgreSQL · Pydantic · Alembic · REST API · JWT Authentication", bold_prefix="Backend & Programming: ")
    add_bullet("HTML · CSS · JavaScript · React · Vite · Android (Java/Kotlin) · Retrofit", bold_prefix="Frontend & Mobile: ")
    add_bullet("Git · GitHub · Docker · Docker Compose · VS Code · Linux · WSL", bold_prefix="DevOps & Developer Tools: ")
    add_bullet("ChatGPT · Claude · Gemini · GitHub Copilot · Cursor · C (Basic)", bold_prefix="AI Tools & Others: ", space_after=8)

    # PROJELER
    add_heading_styled("PROJELER", level=2)

    add_para("CrewIntel — Yapay Zeka Destekli Mürettebat Yönetim Sistemi", bold=True, size=10.5, space_after=1)
    add_para("Python · FastAPI · PostgreSQL · SQLAlchemy · React · Vite · Android · Groq LLM · Docker Compose", italic=True, size=9, color=(0x55,0x55,0x55), space_after=3)
    add_bullet("geliştirerek 20+ REST API endpoint'i, JWT kimlik doğrulama, CORS, rate limiting ve audit logging içeren backend mimarisi kurdum.", bold_prefix="Python/FastAPI backend ")
    add_bullet("ile crew, document, ship, contract, assignment gibi veri modellerini tasarladım ve Alembic ile yönetim uyguladım.", bold_prefix="PostgreSQL + SQLAlchemy ORM ")
    add_bullet("ile PDF belgelerden personel bilgileri, sertifikalar ve deneyim verilerini çıkaran AI document analyzer modülü geliştirdim.", bold_prefix="Groq LLM API entegrasyonu ")
    add_bullet("— LLM ve algoritmik skorlama ile personel yeteneklerini, sertifikalarını ve deneyimlerini iş ilanlarıyla eşleştiren matching motoru tasarladım.", bold_prefix="AI-powered crew matcher ")
    add_bullet("— Belgelerde tutarsızlık ve veri anomali tespiti yapan AI tabanlı kontrol modülü oluşturdum.", bold_prefix="Anomaly detector ")
    add_bullet("(Java, Retrofit) geliştirerek admin paneli ve mobil erişim sağladım.", bold_prefix="React + Vite frontend ve Android mobil uygulama ")
    add_bullet("ile multi-container deployment (PostgreSQL + Backend) yapılandırarak taşınabilir development environment kurdum.", bold_prefix="Docker Compose ")
    add_bullet("E-posta ve WhatsApp bildirim sistemi, maaş takibi, iş ilanı yönetimi, belge yükleme ve dinamik dashboard özelliklerini uyguladım.")
    p_empty = doc.add_paragraph()
    p_empty.paragraph_format.space_after = Pt(4)

    add_para("Social Media Downloader — Sosyal Medya Video İndirici API", bold=True, size=10.5, space_after=1)
    add_para("Python · FastAPI · yt-dlp · Docker", italic=True, size=9, color=(0x55,0x55,0x55), space_after=3)
    add_bullet("YouTube, Instagram, TikTok, Facebook ve Pinterest videolarını indiren FastAPI tabanlı REST API geliştirdim.")
    add_bullet("entegrasyonu ile çoklu platform desteği, video metadata çıkarma ve dosya yönetimi sağladım.", bold_prefix="yt-dlp ")
    add_bullet("containerization ile taşınabilir deployment mimarisi kurdum.", bold_prefix="Docker ")

    # GİRİŞİMCİLİK
    add_heading_styled("GİRİŞİMCİLİK DENEYİMİ", level=2)
    p = doc.add_paragraph()
    run = p.add_run("NGD — New Generation Design · Kurucu & Ürün Geliştirici")
    run.bold = True
    run.font.size = Pt(10)
    run.font.name = 'Calibri'
    run2 = p.add_run("                                                                                              2016 – 2022")
    run2.font.size = Pt(9)
    run2.font.color.rgb = RGBColor(0x55,0x55,0x55)
    run2.font.name = 'Calibri'
    p.paragraph_format.space_after = Pt(1)
    add_para("Termal yönetim, teknik tekstil ve savunma sanayii — Ar-Ge odaklı ürün geliştirme", size=9.5, color=(0x44,0x44,0x44), space_after=3)
    add_bullet("Şirketi sıfırdan kurdu; müşteri problemini tanımladı, çözüm hipotezi oluşturdu, prototip geliştirdi ve MVP'yi piyasaya çıkardı — start-up süreçlerini uçtan uca yönetti.")
    add_bullet("Müşteri ihtiyacı analizi, ürün-pazar uyumu araştırması ve ürün doğrulama süreçlerini yürüttü; B2B müşteriler için özel çözümler geliştirdi.")
    add_bullet("Kurumsal web sitesi, dijital pazarlama, ürün lansmanı ve e-ticaret süreçlerini yönetti.")
    add_bullet("Savunma sanayii için özel termal sistemler geliştirdi; Milli Savunma Bakanlığı ve Silahlı Kuvvetler'e teknik sunum yaptı.")
    add_bullet("Almanya, Fransa, İsveç, ABD ve Rusya dahil uluslararası tedarikçi ve ihracat süreçlerini koordine etti.")

    # MESLEKİ GEÇMİŞ
    add_heading_styled("MESLEKİ GEÇMİŞ", level=2)
    add_para("Yurt içi ve dışında yaklaşık 20 yıl boyunca teknik operasyon, proje koordinasyonu, ekip yönetimi ve kalite kontrol alanlarında görev aldı:", size=9.5, color=(0x33,0x33,0x33), space_after=3)
    add_bullet("Farklı ülkelerde ve disiplinlerde saha deneyimi kazanarak değişen şartlara uyum sağlama ve sonuç odaklı hareket etme becerilerini geliştirdi.")
    add_bullet("Teknik operasyon ve proje yönetiminde yüksek sorumluluk gerektiren görevlerde analitik bakış açısı ve problem çözme yetkinliğini ortaya koydu.")
    add_bullet("Uluslararası projelerde müşteri ve tedarikçi iletişimi, kalite kontrol ve ekip koordinasyonu süreçlerini yürüttü.")
    add_bullet("Bu deneyimler, yazılım geliştirme sürecinde Agile thinking, technical problem solving, cross-functional collaboration ve project management gibi transferable skills olarak doğrudan katkı sağlamaktadır.")

    # NİTELİKLER & DİLLER
    add_heading_styled("NİTELİKLER", level=2)
    add_para("Analitik düşünme · Problem çözme · Girişimci bakış açısı · Takım çalışması · Sonuç odaklı · Hızlı öğrenme", size=9.5, color=(0x33,0x33,0x33), space_after=6)

    add_heading_styled("YABANCI DİL", level=2)
    add_para("Türkçe — Ana dil", bold=True, size=9.5, space_after=1)
    add_para("İngilizce — B2 / Upper-Intermediate · Teknik doküman okuma, yazma ve temel konuşma", size=9, color=(0x55,0x55,0x55), space_after=6)

    # KARİYER HEDEFİ
    add_heading_styled("KARİYER HEDEFİ", level=2)
    add_para("AI/ML, LLM uygulamaları, AI automation ve backend development alanlarında uzmanlaşarak gerçek problemlere yönelik yazılım çözümleri geliştirmeyi hedefliyorum. Full-stack AI proje deneyimi, AI/ML lisans eğitimi ve 20+ yıllık profesyonel/problem-solving geçmişimi birleştirerek Junior AI Developer, AI Automation Developer ve Junior Backend Developer rollerinde değer üretmeye odaklanıyorum.", size=9.5, space_after=8)

    # REFERANSLAR
    add_heading_styled("REFERANSLAR", level=2)
    add_para("Talep edilmesi halinde profesyonel referanslarım paylaşılacaktır.", size=9, color=(0x55,0x55,0x55), space_after=4)

    # FOOTER
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("CV Updated: September 2026")
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0x99,0x99,0x99)
    run.font.name = 'Calibri'

    docx_path = os.path.join(output_dir, "cengiz_kilic_cv_final.docx")
    doc.save(docx_path)
    print(f"DOCX generated: {docx_path}")

except Exception as e:
    print(f"DOCX generation failed: {e}")

# Also copy HTML to output
html_out = os.path.join(output_dir, "cengiz_kilic_cv_final.html")
shutil.copy2(html_path, html_out)
print(f"HTML copied: {html_out}")

print("\n=== DONE ===")
print(f"Output directory: {output_dir}")
for f in os.listdir(output_dir):
    fpath = os.path.join(output_dir, f)
    size = os.path.getsize(fpath)
    print(f"  {f} ({size:,} bytes)")
