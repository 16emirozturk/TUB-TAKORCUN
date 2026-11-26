"""Güvenli Okul v3.0: rapor, yedek, takvim ve içerik yardımcıları."""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path

import db


def _pdf_yazitiplerini_hazirla(dil: str):
    """Unicode fontları arar; bulunamazsa Helvetica ile güvenli ASCII yedeği döndürür.

    Dönüş: (normal_font, kalın_font, metin_dönüştürücü, uyarı, efektif_dil).
    Arapça için Noto ve şekillendirme paketleri bulunamazsa bozuk glif üretmek
    yerine İngilizce içerikli, standart fontlu bir PDF kullanılır.
    """
    import unicodedata

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    project_dir = Path(__file__).resolve().parent
    cwd = Path.cwd()
    font_dirs = [
        project_dir / "fonts",
        project_dir,
        cwd / "fonts",
        cwd,
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/usr/share/fonts/dejavu"),
        Path("/usr/share/fonts/truetype/noto"),
        Path("/usr/share/fonts/opentype/noto"),
    ]

    filenames = {
        "regular": ("DejaVuSans.ttf",),
        "bold": ("DejaVuSans-Bold.ttf",),
        "arabic": ("NotoSansArabic-Regular.ttf",),
        "arabic_bold": ("NotoSansArabic-Bold.ttf",),
    }

    def find_font(key: str):
        for folder in font_dirs:
            for filename in filenames[key]:
                path = folder / filename
                try:
                    if path.is_file() and path.stat().st_size > 10_000:
                        return path
                except OSError:
                    continue
        return None

    # Built-in Helvetica uses WinAnsi, not full Unicode. Transliteration keeps
    # the PDF valid and readable when bundled/system Unicode fonts are absent.
    turkish = str.maketrans({
        "ç": "c", "Ç": "C", "ğ": "g", "Ğ": "G", "ı": "i", "İ": "I",
        "ö": "o", "Ö": "O", "ş": "s", "Ş": "S", "ü": "u", "Ü": "U",
        "â": "a", "Â": "A", "î": "i", "Î": "I", "û": "u", "Û": "U",
        "ß": "ss", "Æ": "AE", "æ": "ae", "Ø": "O", "ø": "o",
    })

    def safe_ascii(value: str) -> str:
        value = unicodedata.normalize("NFKD", str(value).translate(turkish))
        value = "".join(ch for ch in value if not unicodedata.combining(ch))
        return value.encode("ascii", "replace").decode("ascii")

    def builtin(reason: str, effective_language: str = "English"):
        return "Helvetica", "Helvetica-Bold", safe_ascii, reason, effective_language

    def register_font(name: str, path: Path) -> bool:
        try:
            if name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(name, str(path)))
            return True
        except Exception:
            return False

    if dil == "العربية":
        arabic_regular = find_font("arabic")
        arabic_bold = find_font("arabic_bold") or arabic_regular
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
            shaping_ready = True
        except ImportError:
            shaping_ready = False

        if (arabic_regular and shaping_ready
                and register_font("GONotoArabic", arabic_regular)
                and register_font("GONotoArabic-Bold", arabic_bold)):
            pdfmetrics.registerFontFamily(
                "GONotoArabic", normal="GONotoArabic", bold="GONotoArabic-Bold",
                italic="GONotoArabic", boldItalic="GONotoArabic-Bold",
            )
            return (
                "GONotoArabic", "GONotoArabic-Bold",
                lambda value: get_display(arabic_reshaper.reshape(str(value))),
                None, "العربية",
            )
        reason = (
            "Arabic font or shaping package unavailable; the report is shown in English "
            "with built-in Helvetica to avoid broken Arabic characters."
        )
        return builtin(reason, "English")

    regular = find_font("regular")
    bold = find_font("bold") or regular
    if regular and register_font("GOSans", regular):
        if not register_font("GOSans-Bold", bold):
            # If the bold file is damaged, reuse the regular Unicode font.
            if not register_font("GOSans-Bold", regular):
                return builtin(
                    "Unicode font could not be loaded; built-in Helvetica is used and accents are simplified."
                )
        pdfmetrics.registerFontFamily(
            "GOSans", normal="GOSans", bold="GOSans-Bold",
            italic="GOSans", boldItalic="GOSans-Bold",
        )
        return "GOSans", "GOSans-Bold", lambda value: str(value), None, dil

    return builtin(
        "Unicode font files were not found; built-in Helvetica is used and accented characters are simplified."
    )


def pdf_proje_raporu(dil: str = "Türkçe") -> bytes:
    """Kişisel bildirim açıklamalarını içermeyen, toplu ve dayanıklı proje PDF'i üretir."""
    from xml.sax.saxutils import escape

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    supported = {"Türkçe", "English", "Deutsch", "Français", "Español", "العربية", "Azərbaycan dili"}
    if dil not in supported:
        dil = "Türkçe"

    font, bold_font, shape_text, font_warning, effective_language = _pdf_yazitiplerini_hazirla(dil)
    texts = {
        "Türkçe": ["Güvenli Okul — Proje Özeti", "Bu rapor demo verileri ve toplu istatistiklerle oluşturulmuştur.", "Toplam bildirim", "Açık bildirim", "Önleyici çalışma", "Önemli not", "Kural tabanlı öncelik sinyalleri karar değildir. Bildirim sayısındaki değişim, zorbalığın gerçek sıklığını veya bir çalışmanın nedensel etkisini kanıtlamaz.", "Sayfa", "Oluşturulma"],
        "English": ["Güvenli Okul — Project Summary", "Generated from demonstration data and aggregate statistics.", "Total reports", "Open reports", "Preventive activities", "Important note", "Rule-based priority signals are not decisions. Changes in report counts do not prove the true frequency of bullying or causal impact.", "Page", "Generated"],
        "Deutsch": ["Güvenli Okul — Projektübersicht", "Erstellt aus Demodaten und aggregierten Statistiken.", "Meldungen gesamt", "Offene Meldungen", "Präventionsmaßnahmen", "Wichtiger Hinweis", "Regelbasierte Prioritätssignale sind keine Entscheidungen. Änderungen der Meldezahlen belegen weder die tatsächliche Häufigkeit noch eine kausale Wirkung.", "Seite", "Erstellt"],
        "Français": ["Güvenli Okul — Synthèse du projet", "Établi à partir de données de démonstration et de statistiques agrégées.", "Signalements au total", "Signalements ouverts", "Actions de prévention", "Remarque importante", "Les signaux de priorité fondés sur des règles ne sont pas des décisions. L’évolution du nombre de signalements ne prouve ni la fréquence réelle ni un effet causal.", "Page", "Créé le"],
        "Español": ["Güvenli Okul — Resumen del proyecto", "Generado a partir de datos de demostración y estadísticas agregadas.", "Informes totales", "Informes abiertos", "Actividades preventivas", "Nota importante", "Las señales de prioridad basadas en reglas no son decisiones. Los cambios en el número de informes no demuestran la frecuencia real ni un efecto causal.", "Página", "Generado"],
        "العربية": ["Güvenli Okul — ملخص المشروع", "أُنشئ باستخدام بيانات تجريبية وإحصاءات مجمعة.", "إجمالي البلاغات", "البلاغات المفتوحة", "أنشطة الوقاية", "ملاحظة مهمة", "إشارات الأولوية القائمة على القواعد ليست قرارات. ولا تثبت التغيرات في عدد البلاغات معدل التنمر الفعلي أو وجود أثر سببي.", "الصفحة", "تاريخ الإنشاء"],
        "Azərbaycan dili": ["Güvenli Okul — Layihə xülasəsi", "Demo məlumatları və ümumiləşdirilmiş statistika əsasında yaradılıb.", "Ümumi bildiriş", "Açıq bildiriş", "Profilaktik fəaliyyət", "Vacib qeyd", "Qayda əsaslı prioritet siqnalları qərar deyil. Bildiriş sayındakı dəyişiklik zorakılığın real tezliyini və ya səbəb-nəticə təsirini sübut etmir.", "Səhifə", "Yaradılma"],
    }
    t = [shape_text(value) for value in texts[effective_language]]

    # SQL toplu sayımı; bildirim listesi ve kişisel açıklamalar PDF'e taşınmaz.
    stats = db.istatistik_ozeti()
    total_count = int(stats.get("toplam", 0))
    finalized = int(stats.get("durum", {}).get("Sonuçlandırıldı", 0))
    open_count = max(0, total_count - finalized)
    activities = int(db.onleyici_ozeti().get("Toplam", 0))

    out = BytesIO()
    doc = SimpleDocTemplate(
        out, pagesize=A4,
        rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=19 * mm, bottomMargin=23 * mm,
        title=t[0], author="Guvenli Okul", subject="Aggregate project statistics",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "GOTitle", parent=styles["Title"], fontName=bold_font,
        alignment=TA_CENTER, textColor=colors.HexColor("#17345B"),
        fontSize=18, leading=24, spaceAfter=2 * mm,
    )
    body = ParagraphStyle(
        "GOBody", parent=styles["BodyText"], fontName=font,
        fontSize=9, leading=14, textColor=colors.HexColor("#34445A"),
    )
    heading = ParagraphStyle(
        "GOHeading", parent=styles["Heading2"], fontName=bold_font,
        textColor=colors.HexColor("#17345B"), fontSize=12, leading=16,
        spaceBefore=1 * mm, spaceAfter=2 * mm,
    )
    label_style = ParagraphStyle("GOTableLabel", parent=body, fontSize=9, leading=12)
    value_style = ParagraphStyle("GOTableValue", parent=body, fontName=bold_font, alignment=TA_CENTER, fontSize=10)

    story = [
        Paragraph(escape(t[0]), title),
        Spacer(1, 4 * mm),
        Paragraph(escape(t[1]), body),
        Spacer(1, 5 * mm),
    ]
    if font_warning:
        story.extend([Paragraph(escape(shape_text(font_warning)), body), Spacer(1, 3 * mm)])

    rows = [
        [Paragraph(escape(t[2]), label_style), Paragraph(str(total_count), value_style)],
        [Paragraph(escape(t[3]), label_style), Paragraph(str(open_count), value_style)],
        [Paragraph(escape(t[4]), label_style), Paragraph(str(activities), value_style)],
    ]
    table = Table(rows, colWidths=[110 * mm, 35 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5FA")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#172B4D")),
        ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#D8E1EC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend([
        table, Spacer(1, 8 * mm),
        Paragraph(escape(t[5]), heading),
        Paragraph(escape(t[6]), body),
        Spacer(1, 7 * mm),
        Paragraph(f"{escape(t[8])}: {datetime.now(db.TZ).strftime('%d.%m.%Y %H:%M')}", body),
    ])

    def draw_footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D8E1EC"))
        canvas.setLineWidth(.5)
        canvas.line(18 * mm, 16 * mm, A4[0] - 18 * mm, 16 * mm)
        canvas.setFont(font, 8)
        canvas.setFillColor(colors.HexColor("#64748B"))
        page_text = f"Guvenli Okul  ·  {t[7]} {document.page}"
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, shape_text(page_text))
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    result = out.getvalue()
    if not result.startswith(b"%PDF-"):
        raise RuntimeError("PDF oluşturma tamamlanamadı; çıktı geçerli bir PDF değil.")
    return result


def takvim_uyarilari() -> list[dict]:
    """Yaklaşan ve gecikmiş önleyici çalışmalar; yalnızca yönetim ekranında gösterilir."""
    today = datetime.now(db.TZ).date()
    alerts = []
    for item in db.onleyici_calismalari_getir():
        if item["durum"] in ("Tamamlandı", "İptal edildi"):
            continue
        try:
            due = datetime.strptime(item["planlanan_tarih"], "%Y-%m-%d").date()
        except (TypeError, ValueError):
            continue
        days = (due - today).days
        if days < 0:
            alerts.append({"type": "overdue", "days": abs(days), "item": item})
        elif days <= 14:
            alerts.append({"type": "upcoming", "days": days, "item": item})
    return sorted(alerts, key=lambda a: (a["type"] != "overdue", a["days"]))


EGITIM_KARTLARI = [
    {"title": "Akran zorbalığını tanımak", "summary": "Tekrarlayan, güç dengesizliği içeren davranışları; tek seferlik anlaşmazlıklardan ayırt etmeye yardımcı bilgiler.", "steps": ["Davranışın tekrar edip etmediğine bakın.", "Taraflar arasındaki güç dengesizliğini değerlendirin.", "Etiket koymadan, somut davranışı ve etkisini anlatın."]},
    {"title": "Dijital güvenlik", "summary": "Çevrim içi ortamda saygı, mahremiyet ve güvenli destek arama yolları.", "steps": ["Kişisel bilgileri ve başkalarının özel içeriklerini paylaşmayın.", "Rahatsız edici iletişime yanıt vermek zorunda değilsiniz.", "Güvendiğiniz bir yetişkinden destek isteyin."]},
    {"title": "Tanık olanlar ne yapabilir?", "summary": "Güvenli ve destekleyici müdahale yolları.", "steps": ["Güvenli değilse doğrudan müdahale etmeyin.", "Dışlamaya katılmayın; destekleyici bir tutum gösterin.", "Durumu güvenilir bir yetişkine bildirin."]},
    {"title": "Destek istemek", "summary": "Yardım istemek güçsüzlük değildir; güvenilir yetişkinler ve okul destek birimleriyle konuşun.", "steps": ["Kendinizi güvende hissettiğiniz yetişkini seçin.", "Ne olduğunu ve nasıl etkilendiğinizi anlatın.", "Acil tehlikede yerel acil yardım hizmetlerine başvurun."]},
]

HELP_STEPS = [
    ("1. Bildirim gönder", "Yeni bildirim sayfasında olay türü, ortam ve zaman bilgilerini seçin. Gerçek ad, telefon veya başka kişisel bilgi yazmayın."),
    ("2. Takip kodunu sakla", "Gönderimden sonra oluşan kodu güvenli bir yerde saklayın. Kod, bildirimin durumunu sorgulamak içindir."),
    ("3. Durumu takip et", "Bildirim sorgula alanında takip kodunu girin. Öğrenci ekranında açıklama ve inceleme notları gösterilmez."),
    ("4. Yetkili incelemesi", "Yetkili personel bildirimi insan değerlendirmesiyle inceler. Otomatik sinyaller tek başına karar vermez."),
]
