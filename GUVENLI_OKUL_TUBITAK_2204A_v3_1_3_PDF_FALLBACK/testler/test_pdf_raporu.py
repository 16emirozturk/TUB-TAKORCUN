"""PDF raporunun dil, font fallback ve veri minimizasyonu testleri."""
from __future__ import annotations

from pathlib import Path

import db
import gelistirmeler


def test_pdf_raporu_tum_dillerde_olusturulur(temiz_veritabani):
    for language in (
        "Türkçe", "English", "Deutsch", "Français", "Español", "العربية", "Azərbaycan dili"
    ):
        pdf = gelistirmeler.pdf_proje_raporu(language)
        assert pdf.startswith(b"%PDF-")
        assert len(pdf) > 1200


def test_fontlar_yokken_helvetica_yedegi_pdf_uretir(temiz_veritabani, monkeypatch):
    # Simüle edilen Streamlit Cloud ortamında proje fontları ve sistem fontları yok.
    monkeypatch.setattr(Path, "is_file", lambda self: False)
    font, bold, shape_text, warning, effective_language = gelistirmeler._pdf_yazitiplerini_hazirla("Türkçe")
    assert font == "Helvetica"
    assert bold == "Helvetica-Bold"
    assert warning
    assert "Turkce" in shape_text("Türkçe")
    pdf = gelistirmeler.pdf_proje_raporu("Türkçe")
    assert pdf.startswith(b"%PDF-")


def test_arapca_font_ve_sekillendirme_yokken_ingilizce_guvenli_yedek(temiz_veritabani, monkeypatch):
    monkeypatch.setattr(Path, "is_file", lambda self: False)
    font, bold, shape_text, warning, effective_language = gelistirmeler._pdf_yazitiplerini_hazirla("العربية")
    assert font == "Helvetica"
    assert effective_language == "English"
    assert warning
    pdf = gelistirmeler.pdf_proje_raporu("العربية")
    assert pdf.startswith(b"%PDF-")


def test_pdf_ozel_bildirim_metnini_icermez(temiz_veritabani):
    db.bildirim_ekle(
        olay_turu="Hakaret veya alay",
        ortam="Sınıfta",
        zaman_bilgisi="Bugün",
        tekrar_durumu="Bir kez",
        aciklama="PDF_TEST_GIZLI_METIN_7F3A",
        anonim=True,
        demo=True,
    )
    pdf = gelistirmeler.pdf_proje_raporu("Türkçe")
    assert b"PDF_TEST_GIZLI_METIN_7F3A" not in pdf


def test_pdf_verisi_bir_yuz_bin_kayitlik_listeye_bagimli_degil(temiz_veritabani, monkeypatch):
    def liste_okuma_kullanilmasin(*args, **kwargs):
        raise AssertionError("PDF raporu tüm bildirim listesini okumamalı.")

    monkeypatch.setattr(db, "kayitlari_getir", liste_okuma_kullanilmasin)
    pdf = gelistirmeler.pdf_proje_raporu("English")
    assert pdf.startswith(b"%PDF-")
