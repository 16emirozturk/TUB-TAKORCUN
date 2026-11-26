"""Güvenli Okul — bildirim ve takip platformu (Streamlit, sürüm 3.1).

Mimari: app.py (arayüz) · db.py (veri) · guvenlik.py (kimlik/maskeleme) ·
hakaret_tespiti.py (kural tabanlı sinyal) · degerlendirme.py (ölçüm) · stil.py (CSS).
"""
from __future__ import annotations

import base64
import html
import json
import re
import secrets
import sqlite3
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import db
import ek_sayfalar
import gelistirmeler
import degerlendirme
import guvenlik
import hakaret_tespiti as ht
import stil
from sabitler import (ACIL_HATLAR, BIRIMLER, DURUMLAR, ONCELIK_SIRASI, ONCELIKLER, OLAY_TURLERI,
                      ORTAMLAR, SINIFLAR, TEKRARLAR, ZAMANLAR)

st.set_page_config(page_title="Güvenli Okul", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")
stil.uygula()

# ------------------------------------------------------------------ ayarlar
OTURUM_ZAMAN_ASIMI_SN = 30 * 60      # hareketsizlikte yönetici oturumu kapanır
OTURUM_HATALI_ESIK = 5               # bir tarayıcı oturumunda ardışık hatalı giriş sınırı
OTURUM_KILIT_SN = 5 * 60
GLOBAL_HATALI_ESIK = 20              # tüm oturumlarda 15 dakikadaki hatalı giriş sınırı
FORM_PENCERE_SN, FORM_PENCERE_MAKS = 600, 5   # bildirim spamına karşı oturum başına sınır
SORGU_PENCERE_SN, SORGU_MAKS = 300, 10        # takip kodu tahminine karşı sınır
ISTATISTIKLER_HERKESE_ACIK = False
SLA_SAAT = 24                        # ilk incelemeye alınmayan kayıt bu süreden sonra "gecikmiş" sayılır

ss = st.session_state


def _secret(bolum: str, anahtar: str, varsayilan: str = "") -> str:
    try:
        return str(st.secrets[bolum][anahtar])
    except Exception:  # secrets.toml yok / anahtar yok
        return varsayilan


ADMIN_KULLANICI = _secret("admin", "username")
ADMIN_PAROLA = _secret("admin", "password_hash") or _secret("admin", "password")
DEMO_MODU = _secret("uygulama", "demo_modu", "true").lower() != "false"


@st.cache_resource
def _veritabanini_hazirla() -> bool:
    db.hazirla()
    db.anonim_hazirla()   # v2.1: tam anonim akış tabloları (mevcut veriye dokunmaz)
    return True


_veritabanini_hazirla()

# ------------------------------------------------------------ oturum durumu

from i18n import (translate as _tr, format_timestamp, translate_structure, set_language, LANGUAGES, text_direction)

for _k,_v in {"yonetici_giris":False,"yonetici_adi":"","son_etkinlik":0.0,"hatali_giris":0,"kilit_bitis":0.0,
              "form_surumu":0,"son_bildirim":None,"ana_menu":"Genel bakış","dil":"Türkçe"}.items():
    ss.setdefault(_k,_v)
set_language(ss.get("dil", "Türkçe"))


def flash(tur: str, mesaj: str) -> None:
    """st.rerun() sonrasında da görünen bildirim (v1'de rerun mesajı yutuyordu)."""
    ss["_flash"] = (tur, mesaj)


def flash_goster() -> None:
    f = ss.pop("_flash", None)
    if f:
        getattr(st, f[0])(f[1])


def sayfaya_git(ad: str) -> None:
    # Düğme geri çağrısı (callback): widget anahtarı yalnızca burada güvenle değiştirilebilir.
    ss["ana_menu"] = ad


def oturumu_kapat(neden: str = "Oturum kapatıldı") -> None:
    if ss.yonetici_giris:
        db.denetim_ekle(ss.yonetici_adi, neden)
    ss.yonetici_giris = False
    ss.yonetici_adi = ""


def oturum_denetle() -> None:
    if ss.yonetici_giris:
        if time.time() - ss.son_etkinlik > OTURUM_ZAMAN_ASIMI_SN:
            oturumu_kapat("Oturum zaman aşımı")
            flash("warning", "Hareketsizlik nedeniyle yönetici oturumu kapatıldı.")
        else:
            ss.son_etkinlik = time.time()


def hiz_siniri(anahtar: str, pencere_sn: int, maks: int) -> tuple[bool, int]:
    simdi = time.time()
    liste = [t for t in ss.get(anahtar, []) if simdi - t < pencere_sn]
    if len(liste) >= maks:
        ss[anahtar] = liste
        return False, int(pencere_sn - (simdi - liste[0])) + 1
    liste.append(simdi)
    ss[anahtar] = liste
    return True, 0


def acil_hat_html() -> str:
    parca = " · ".join(f"<b>{html.escape(n)}</b> {html.escape(_tr(a))}" for n, a in ACIL_HATLAR)
    return f"<div class='emergency'>{html.escape(_tr('Acil bir tehlike varsa beklemeyin:'))} {parca}</div>"


def yonetici_gerekli() -> None:
    if ss.yonetici_giris:
        return
    st.markdown(
        "<div class='access-panel'><strong>Yönetici erişimi gerekli</strong><br>"
        "<span style='color:#5b6b7e'>Bu bölümü görüntülemek için yönetici oturumu açın.</span></div>",
        unsafe_allow_html=True,
    )
    st.button("Yönetici girişine git", type="primary", on_click=sayfaya_git, args=("Yönetici girişi",))
    altbilgi()
    st.stop()


def altbilgi() -> None:
    st.divider()
    st.caption("Güvenli Okul · Bildirim ve takip sistemi · Kural tabanlı sinyaller karar değildir.")


def pill(metin: str, sinif: str) -> str:
    if metin.startswith("Sinyal: "):
        metin = _tr("Sinyal:") + " " + _tr(metin.split(": ", 1)[1])
    else:
        metin = _tr(metin)
    return f"<span class='pill {sinif}'>{html.escape(metin)}</span>"


def guvenli_metin(metin: str) -> None:
    """Kullanıcı kaynaklı metni Markdown/HTML olarak yorumlamadan gösterir (görsel/bağlantı enjeksiyonunu önler)."""
    # Report descriptions and reviewer notes are user-authored data. Bypass the
    # UI translation wrapper so their original wording is never altered.
    original_markdown = getattr(st, "_guvenli_okul_originals", {}).get("markdown", st.markdown)
    original_markdown("<div style='white-space:pre-wrap;word-break:break-word'>" + html.escape(metin or "") + "</div>",
                      unsafe_allow_html=True)


_IKON_YOLLARI = {
    "edit": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "book": '<path d="M4 19.5A2.5 2.5 0 016.5 17H20V3H6.5A2.5 2.5 0 004 5.5z"/><path d="M8 7h8M8 11h6"/>',
    "lock": '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/>',
    "users": '<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.5"/><path d="M17 14c2.5 0 4.5 2 4.5 5"/>',
    "heart": '<path d="M12 20s-7-4.5-7-10a4 4 0 017-2.5A4 4 0 0119 10c0 5.5-7 10-7 10z"/>',
    "eye": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
}


def ikon_rozeti(ad: str, renk: str) -> str:
    """Pastel arka planlı, satır içi (harici dosya yok) SVG ikon rozeti."""
    return (f"<div class='icon-badge ib-{renk}'><svg viewBox='0 0 24 24' fill='none' stroke='currentColor' "
            f"stroke-width='2' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>"
            f"{_IKON_YOLLARI[ad]}</svg></div>")


def kart(ikon: str, renk: str, baslik: str, metin: str) -> str:
    return (f"<div class='soft-card'>{ikon_rozeti(ikon, renk)}<h3>{html.escape(_tr(baslik))}</h3>"
            f"<p>{html.escape(_tr(metin))}</p></div>")


HERO_SVG = (
    "<svg viewBox='0 0 320 260' xmlns='http://www.w3.org/2000/svg' role='img' aria-label='Kalkan ve kilit'>"
    "<defs><linearGradient id='gsh' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#9bd8ff'/>"
    "<stop offset='1' stop-color='#4f8cff'/></linearGradient></defs>"
    "<circle cx='160' cy='130' r='112' fill='#fff' fill-opacity='.08'/>"
    "<circle cx='160' cy='130' r='78' fill='#fff' fill-opacity='.1'/>"
    "<path d='M160 42l70 26v52c0 46-30 76-70 90-40-14-70-44-70-90V68z' fill='url(#gsh)'/>"
    "<path d='M160 42l70 26v52c0 46-30 76-70 90z' fill='#fff' fill-opacity='.16'/>"
    "<rect x='136' y='120' width='48' height='40' rx='9' fill='#fff'/>"
    "<path d='M146 120v-12a14 14 0 0128 0v12' fill='none' stroke='#fff' stroke-width='8' stroke-linecap='round'/>"
    "<circle cx='160' cy='138' r='6' fill='#4f8cff'/><rect x='157' y='140' width='6' height='12' rx='3' fill='#4f8cff'/>"
    "<g fill='#fff' fill-opacity='.9'><circle cx='58' cy='196' r='12'/><path d='M38 236c0-12 9-20 20-20s20 8 20 20z'/>"
    "<circle cx='262' cy='196' r='12'/><path d='M242 236c0-12 9-20 20-20s20 8 20 20z'/></g>"
    "<circle cx='268' cy='62' r='7' fill='#ffd166'/><circle cx='46' cy='92' r='5' fill='#7ee0c3'/>"
    "<circle cx='286' cy='130' r='4' fill='#fff' fill-opacity='.7'/></svg>"
)


@st.cache_resource
def _logo_veri_adresi() -> str:
    """Logo, sayfaya satır içi gömülür (harici istek yok)."""
    yol = Path(__file__).with_name("bozuyuk_fen_lisesi_logo.png")
    if not yol.exists():
        return ""
    return "data:image/png;base64," + base64.b64encode(yol.read_bytes()).decode("ascii")


DURUM_SINIF = {"İnceleme bekliyor": "status-waiting", "İnceleniyor": "status-active",
               "Takip gerekiyor": "status-followup", "Sonuçlandırıldı": "status-done"}
ONCELIK_SINIF = {"Sinyal yok": "prio-none", "Düşük": "prio-low", "Orta": "prio-mid",
                 "Yüksek": "prio-high", "Acil": "prio-urgent"}



def _gunluk_ozet(kayitlar: list[dict]) -> None:
    bugun = datetime.now(db.TZ).date().isoformat()
    yeni = sum((k.get("olusturma_zamani") or "")[:10] == bugun for k in kayitlar)
    kritik = [k for k in kayitlar if k.get("oncelik") in ("Acil","Yüksek") and k.get("durum") != "Sonuçlandırıldı"]
    bekleyen = sum(k.get("durum") == "İnceleme bekliyor" for k in kayitlar)
    st.subheader(_tr("Günlük Durum Özeti"))
    c1,c2,c3=st.columns(3)
    c1.metric(_tr("Bugünkü yeni bildirim"), yeni)
    c2.metric(_tr("Aktif yüksek/acil"), len(kritik))
    c3.metric(_tr("İnceleme bekleyen"), bekleyen)
    if kritik:
        acil_var=any(k.get("oncelik")=="Acil" for k in kritik)
        baslik="Acil öncelikli bildirim" if acil_var else "Yüksek öncelikli bildirim"
        st.markdown("<div class='emergency'><b>⚠ "+html.escape(_tr(baslik))+"</b> · "+
                    str(len(kritik))+" "+_tr("aktif yüksek/acil öncelikli kayıt var. Yetkili personel tarafından insan incelemesi gerekir.")+"</div>",
                    unsafe_allow_html=True)

# ============================================================ 1. GENEL BAKIŞ
def sayfa_genel_bakis() -> None:
    st.markdown(
        "<div class='hero'><div class='hero-text'><div class='eyebrow'>GÜVENLİ OKUL</div>"
        f"<h1>{html.escape(_tr('Güvenli bir okul, herkesin hakkı.'))}</h1>"
        f"<p>{html.escape(_tr('Zorbalığı kimliğini vermeden bildir, gizli kodunla durumu takip et.'))}</p>"
        f"<div class='hero-pills'><span class='hero-pill'>{html.escape(_tr('Anonim'))}</span>"
        f"<span class='hero-pill'>{html.escape(_tr('Gizli takip kodu'))}</span>"
        f"<span class='hero-pill'>{html.escape(_tr('İnsan incelemesi'))}</span></div></div>"
        f"<div class='hero-art'>{HERO_SVG}</div></div>",
        unsafe_allow_html=True,
    )
    if ss.yonetici_giris:
        kay = db.kayitlari_getir()
        _gunluk_ozet(kay)
        st.button("İnceleme kuyruğunu aç", type="primary", on_click=sayfaya_git, args=("Bildirim inceleme",), key="g_kuyruk")
    st.markdown(acil_hat_html(), unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Nasıl kullanılır?</div>", unsafe_allow_html=True)
    a, b, c = st.columns(3, gap="medium")
    with a:
        st.markdown(kart("edit", "blue", "1 · Bildir", "Formu doldur. Ad ve sınıf istenmez; sana gizli bir kod verilir."),
                    unsafe_allow_html=True)
        st.button("Yeni bildirim", type="primary", on_click=sayfaya_git, args=("Yeni bildirim",), key="g_yeni")
    with b:
        st.markdown(kart("search", "green", "2 · Takip et", "Kodunla durumu gör, aynı gün ek bilgi ekle."),
                    unsafe_allow_html=True)
        st.button("Bildirim sorgula", on_click=sayfaya_git, args=("Bildirim sorgula",), key="g_sorgu")
    with c:
        st.markdown(kart("shield", "violet", "3 · İnsan inceler", "Yetkili kişiler kaydı inceler. Kararı makine vermez."),
                    unsafe_allow_html=True)
        st.button("Güvenli kullanım", on_click=sayfaya_git, args=("Güvenli kullanım",), key="g_guv")

    st.markdown("<div class='section-title'>Rehberlik bilgi bankası</div>", unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3, gap="medium")
    with r1:
        st.markdown(kart("heart", "rose", "Yaşıyorsan", "Kime anlatabileceğini ve neler yapabileceğini öğren."),
                    unsafe_allow_html=True)
    with r2:
        st.markdown(kart("users", "amber", "Tanık olduysan", "Sessiz kalmadan, güvenli şekilde nasıl destek olursun?"),
                    unsafe_allow_html=True)
    with r3:
        st.markdown(kart("book", "blue", "Veli ve öğretmenler", "İşaretleri tanı, çocuğu dinle, doğru adımı at."),
                    unsafe_allow_html=True)
    st.button("Destek rehberini aç", on_click=sayfaya_git, args=("Destek rehberi",), key="g_destek")

    st.markdown("<div class='section-title'>Güvenlik ilkeleri</div>", unsafe_allow_html=True)
    g1, g2, g3 = st.columns(3, gap="medium")
    g1.markdown(kart("lock", "blue", "Gizlilik", "Telefon, T.C. no, e-posta ve IBAN otomatik gizlenir."), unsafe_allow_html=True)
    g2.markdown(kart("eye", "green", "Sinyal, karar değil", "Otomatik eşleşme yalnızca inceleme sırasına yardım eder."),
                unsafe_allow_html=True)
    g3.markdown(kart("shield", "violet", "Hesap verebilirlik", "Yönetici işlemleri kim yaptığıyla kayda geçer."),
                unsafe_allow_html=True)


# =========================================================== 2. YENİ BİLDİRİM
def baslik_blogu(ust: str, baslik: str, aciklama: str = "") -> None:
    st.markdown(f"<div class='page-heading'><div class='eyebrow-dark'>{html.escape(_tr(ust))}</div>"
                f"<h1>{html.escape(_tr(baslik))}</h1>" + (f"<p>{html.escape(_tr(aciklama))}</p>" if aciklama else "")
                + "</div>", unsafe_allow_html=True)


def sorguya_git(kod: str = "") -> None:
    """Geri çağrı: sorgu sayfasını açar; kod biliniyorsa durumu doğrudan gösterir."""
    if kod:
        ss["sorgu_aktif_kod"] = kod
    ss["ana_menu"] = "Bildirim sorgula"


def _bildirim_basari_karti(son: dict) -> None:
    with st.container(border=True):
        st.success("Bildirimin kaydedildi. Teşekkür ederiz.")
        st.write("**Gizli takip kodun.** Durumu ve ek bilgi eklemeyi bu kodla yaparsın. "
                 "Not al ya da ekran görüntüsü al; kod kaybolursa yeniden oluşturulamaz:")
        st.code(son["takip_no"])
        if son["maskelenen"]:
            st.info("Açıklamandaki şu bilgiler gizlilik için otomatik gizlendi: " + ", ".join(son["maskelenen"]) + ".")
        if son["oncelik"] in ("Acil", "Yüksek"):
            st.error("Yazdıkların için endişeleniyoruz. Şu an güvende değilsen ya da kendini veya başkasını "
                     "tehlikede hissediyorsan lütfen hemen güvendiğin bir yetişkine, okul rehber öğretmenine "
                     "ya da yukarıdaki acil hatlara ulaş.")
        st.caption("Bu takip kodu yalnızca uygulamadaki kaydı tanımlar. Rehberlikle mesajlaşma yoktur; "
                   "yalnızca bildirimin durumunu görürsün."
                   + (" Herhangi bir kuruma otomatik bildirim gönderilmez." if DEMO_MODU else ""))
        c1, c2 = st.columns(2)
        c1.button("Durumu sorgula", type="primary", on_click=sorguya_git, args=(son["takip_no"],), key="son_sorgu")
        c2.button("Kodumu not aldım", on_click=lambda: ss.update(son_bildirim=None), key="son_kapat")


def sayfa_yeni_bildirim() -> None:
    baslik_blogu("BİLDİRİM", "Yeni bildirim",
                 "Kimliğini vermeden bildir. Ad, sınıf veya telefon istenmez.")
    st.markdown(acil_hat_html(), unsafe_allow_html=True)

    jeton = _cihaz_jetonu()          # her çalışmada çağrılır (bileşen sayfada kalmalı)
    son = ss.get("son_bildirim")
    if son:
        _bildirim_basari_karti(son)
        return
    if not jeton:
        st.caption("Hazırlanıyor…")
        return
    if db.anonim_kota_dolu_mu(jeton):
        st.warning("Günlük bildirim hakkınız dolmuştur. Yarın yeniden bildirim yapabilirsin. "
                   "Bugünkü bildirimine takip koduyla ek bilgi ekleyebilirsin.")
        st.button("Bildirimime ek bilgi ekle", on_click=sorguya_git, key="kota_sorgu")
        return
    st.caption("Günde bir bildirim hakkın var. Bu hak, tarayıcında saklanan rastgele bir kodla uygulanır; "
               "kimliğinle ilişkili değildir."
               + ("" if DEMO_MODU else " Telefon, adres gibi bilgileri yazmana gerek yok; yalnızca olayı anlat."))

    no = ss.form_surumu
    with st.form(f"bildirim_formu_{no}", clear_on_submit=False):
        olay_turu = st.selectbox("Ne oldu?", OLAY_TURLERI, key=f"tur_{no}")
        ortam = st.selectbox("Nerede oldu?", ORTAMLAR, key=f"ortam_{no}")
        zaman_bilgisi = st.selectbox("Ne zaman oldu?", ZAMANLAR, key=f"zaman_{no}")
        tekrar = st.radio("Bu olay kaç kez yaşandı?", TEKRARLAR, key=f"tekrar_{no}")
        aciklama = st.text_area("Olayı kendi cümlelerinle anlat", max_chars=3000, height=150, key=f"aciklama_{no}",
                                placeholder="Ne oldu, nerede ve ne zaman oldu? Ad, telefon gibi bilgileri yazma.")
        onay = st.checkbox(
            "Gerçek kişisel bilgi içermeyen örnek bir açıklama girdiğimi onaylıyorum." if DEMO_MODU
            else "Bilgilendirme metnini okudum; verdiğim bilgilerin bildirim sürecinde işlenmesini kabul ediyorum.",
            key=f"onay_{no}")
        gonder = st.form_submit_button("Bildirimi gönder", type="primary")

    if not gonder:
        return
    if not aciklama.strip():
        st.error("Lütfen olayı anlat.")
    elif not any(ch.isalnum() for ch in aciklama):
        st.error("Açıklama yalnızca boşluk veya noktalama işaretlerinden oluşamaz. Kısaca ne olduğunu yaz.")
    elif not onay:
        st.error("Lütfen onay kutusunu işaretle.")
    else:
        izin, bekle = hiz_siniri("gonderim_zamanlari", FORM_PENCERE_SN, FORM_PENCERE_MAKS)
        if not izin:
            st.error(f"Kısa sürede çok fazla bildirim gönderildi. Lütfen yaklaşık {bekle} saniye sonra tekrar dene.")
            return
        try:
            sonuc = db.anonim_bildirim_ekle(jeton, olay_turu=olay_turu, ortam=ortam, zaman_bilgisi=zaman_bilgisi,
                                            tekrar_durumu=tekrar, aciklama=aciklama.strip(), demo=DEMO_MODU)
        except db.AnonimHata as e:
            st.warning(e.mesaj)
            return
        except (sqlite3.Error, RuntimeError):
            st.error("Kayıt oluşturulamadı. Lütfen daha sonra tekrar dene.")
            return
        ss.son_bildirim = {"takip_no": sonuc["takip_no"], "maskelenen": sonuc["maskelenen"],
                           "oncelik": sonuc["analiz"].oncelik}
        ss.form_surumu += 1   # formu (yalnızca BAŞARIDA) temizler
        st.rerun()


# ========================================================= 3. BİLDİRİM SORGULA
DURUM_ACIKLAMA = {
    "İnceleme bekliyor": "Bildirimin alındı. Yetkili kişi henüz incelemeye başlamadı.",
    "İnceleniyor": "Bildirimin yetkili kişiler tarafından inceleniyor.",
    "Takip gerekiyor": "İnceleme sürüyor; konu takip edilmeye devam ediyor.",
    "Sonuçlandırıldı": "Bildirimin değerlendirildi ve süreç tamamlandı.",
}


def sayfa_sorgula() -> None:
    baslik_blogu("TAKİP", "Bildirim sorgula",
                 "Takip koduyla durumu gör, aynı gün ek bilgi ekle. Mesajlaşma yoktur.")
    with st.form("sorgu_formu"):
        kod = st.text_input("Gizli takip kodu", placeholder="GO-XXXXXXXXXX", max_chars=20)
        ara = st.form_submit_button("Durumu göster", type="primary")
    if ara:
        izin, bekle = hiz_siniri("sorgu_zamanlari", SORGU_PENCERE_SN, SORGU_MAKS)
        if not izin:
            st.error(f"Çok fazla sorgu yapıldı. Lütfen yaklaşık {bekle} saniye sonra tekrar dene.")
            return
        ozet = db.anonim_takip_ozeti(kod)
        if not ozet:
            ss.pop("sorgu_aktif_kod", None)
            st.error("Bu kodla eşleşen bir kayıt bulunamadı. Kodu kontrol edip tekrar dene.")
            return
        ss["sorgu_aktif_kod"] = ozet["takip_no"]
    aktif = ss.get("sorgu_aktif_kod")
    if not aktif:
        return
    ozet = db.anonim_takip_ozeti(aktif)
    if not ozet:
        ss.pop("sorgu_aktif_kod", None)
        return
    st.markdown(
        f"<div class='record-banner'><div><div class='record-kicker'>TAKİP KODU</div>"
        f"<div class='record-id'>{html.escape(ozet['takip_no'])}</div></div>"
        f"{pill(ozet['durum'], DURUM_SINIF.get(ozet['durum'], 'status-waiting'))}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='durum-not'>{html.escape(_tr(DURUM_ACIKLAMA.get(ozet['durum'], '')))}</div>",
                unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric("Oluşturulma", format_timestamp(ozet["olusturma_zamani"], ss.get("dil", "Türkçe")))
    c2.metric("Son güncelleme", format_timestamp(ozet["son_guncelleme"], ss.get("dil", "Türkçe")))

    st.markdown("#### Ek bilgi ekle")
    if not ozet["ek_uygun"]:
        st.info("Ek bilgi yalnızca anonim bildirimlerde, bildirimin yapıldığı gün ve bildirim sonuçlanmadan önce "
                "eklenebilir.")
        return
    st.caption(f"Eklenen ek bilgi: {ozet['ek_adet']} / {db.MAKS_EK_SAYISI}. Ek bilgiler aynı bildirimin altına "
               f"eklenir; her ek arasında {db.EK_BEKLEME_SN} saniye beklenir.")
    if ozet["ek_kalan_hak"] == 0:
        st.info("Bugün için ek bilgi sınırına ulaştın.")
        return
    if ozet["bekle_sn"] > 0:
        st.warning(f"Yeni ek bilgi için yaklaşık {ozet['bekle_sn']} saniye beklemen gerekiyor.")
    ss.setdefault("anon_ek_surumu", 0)
    with st.form("anon_ek_formu"):
        ek = st.text_area("Eklemek istediğin bilgi", max_chars=db.MAKS_EK_UZUNLUGU, height=110,
                          key=f"anon_ek_{ss.anon_ek_surumu}",
                          placeholder="Ad, telefon gibi bilgileri yazma.")
        gonder = st.form_submit_button("Ek bilgiyi gönder", type="primary")
    if not gonder:
        return
    try:
        sonuc = db.ek_bilgi_ekle(aktif, ek)
    except db.AnonimHata as e:
        st.error(e.mesaj)
        return
    except (sqlite3.Error, RuntimeError):
        st.error("Ek bilgi kaydedilemedi. Lütfen daha sonra tekrar dene.")
        return
    ss.anon_ek_surumu += 1
    flash("success", f"Ek bilgin eklendi. Bugün {sonuc['kalan_hak']} ek bilgi hakkın kaldı.")
    st.rerun()


# ======================================================== 4. YÖNETİCİ GİRİŞİ
def sayfa_yonetici_girisi() -> None:
    st.markdown("<div class='hero'><h1>Yönetici girişi</h1><p>Bildirim inceleme alanına yalnızca "
                "yetkili kullanıcılar erişebilir.</p></div>", unsafe_allow_html=True)
    if ss.yonetici_giris:
        st.success("Yönetici oturumu açık.")
        st.button("Bildirim incelemeye git", type="primary", on_click=sayfaya_git, args=("Bildirim inceleme",))
        return
    if not ADMIN_KULLANICI or not ADMIN_PAROLA:
        st.error("Yönetici bilgileri ayarlanmamış. .streamlit/secrets.toml (veya Streamlit Cloud > Settings > "
                 "Secrets) içindeki [admin] bölümünü yapılandırın.")
        return
    kalan = int(ss.kilit_bitis - time.time())
    if kalan > 0:
        st.error(f"Çok fazla hatalı deneme. Lütfen {kalan} saniye sonra tekrar deneyin.")
        return
    if db.basarisiz_giris_sayisi(15) >= GLOBAL_HATALI_ESIK:
        st.error("Sistem genelinde çok fazla hatalı giriş denemesi var. Lütfen bir süre sonra tekrar deneyin.")
        return

    with st.form("yonetici_giris_formu"):
        kullanici = st.text_input("Kullanıcı adı")
        parola = st.text_input("Parola", type="password")
        giris = st.form_submit_button("Giriş yap", type="primary")
    if not giris:
        return
    if guvenlik.kimlik_dogrula(kullanici, parola, ADMIN_KULLANICI, ADMIN_PAROLA):
        db.giris_denemesi_kaydet(True)
        ss.update(yonetici_giris=True, yonetici_adi=ADMIN_KULLANICI, son_etkinlik=time.time(), hatali_giris=0)
        db.denetim_ekle(ADMIN_KULLANICI, "Yönetici girişi")
        flash("success", "Yönetici girişi başarılı.")
        st.rerun()
    else:
        db.giris_denemesi_kaydet(False)
        ss.hatali_giris += 1
        db.denetim_ekle("(bilinmiyor)", "Başarısız giriş denemesi")
        if ss.hatali_giris >= OTURUM_HATALI_ESIK:
            ss.kilit_bitis = time.time() + OTURUM_KILIT_SN
            ss.hatali_giris = 0
        st.error("Kullanıcı adı veya parola yanlış.")


# ===================================================== 5. BİLDİRİM İNCELEME
def _kayit_detayi(k: dict) -> None:
    st.markdown("#### Bildirim ayrıntıları")
    a, b = st.columns(2)
    a.markdown(f"**Olay türü**  \n{_tr(k['olay_turu'])}\n\n**Ortam**  \n{_tr(k['ortam'])}\n\n**Yaklaşık zaman**  \n{_tr(k['zaman_bilgisi'])}")
    b.markdown(f"**Tekrarlanma**  \n{_tr(k['tekrar_durumu'])}\n\n**Oluşturulma**  \n{format_timestamp(k['olusturma_zamani'], ss.get('dil', 'Türkçe'))}\n\n"
               f"**Bildirim türü**  \n{_tr('Anonim' if k['anonim'] else 'Kimlik bilgisi belirtilmiş')}")
    if not k["anonim"]:
        with st.expander("Bildirimde belirtilen kişi bilgileri"):
            guvenli_metin(f"{_tr('Ad soyad:')} {(k['ad'] or _tr('Belirtilmedi'))} {k['soyad'] or ''}")
            guvenli_metin(f"{_tr('Sınıf:')} {_tr(k['sinif'] or 'Belirtilmedi')}")

    kategori_metin = ((k.get("olay_turu") or "") + " " + (k.get("kategoriler") or "")).casefold()
    tavsiyeler = None
    if "dijital" in kategori_metin or "siber" in kategori_metin:
        tavsiyeler = ["Varsa ilgili mesaj, bağlantı ve ekran görüntülerini güvenli biçimde muhafaza edin; gereksiz kişilerle paylaşmayın.",
                      "Öğrenciyle ayrı ve gizliliği koruyan bireysel görüşme yapın.",
                      "Okul prosedürüne uygun platform bildirim adımlarını ve güvenlik riskini değerlendirin.",
                      "Gerekirse veli ve okul yönetimiyle yetkili süreç üzerinden koordinasyon sağlayın."]
    elif "dışlama" in kategori_metin or "akran" in kategori_metin:
        tavsiyeler = ["Öğrenciyi suçlamadan, yönlendirici olmayan sorularla bireysel olarak dinleyin.",
                      "Olayın tekrarı, güç dengesi ve farklı ortamlardaki etkisini değerlendirin.",
                      "Sınıf ortamını ve akran ilişkilerini gözlemleyin; öğrencileri topluluk önünde etiketlemeyin.",
                      "Destek planını rehberlik servisi ve okulun ilgili ekibiyle birlikte belirleyin."]
    elif "tehdit" in kategori_metin or "fiziksel" in kategori_metin:
        tavsiyeler = ["Önce öğrencilerin o anki güvenliğini değerlendirin; yakın tehlikede okulun acil durum protokolünü uygulayın.",
                      "Tarafları tek başına yüzleştirmeyin; ilgili yetişkinleri ve okul yönetimini bilgilendirin.",
                      "Görüşmeleri ayrı ve gizli yürütün; beyanları yorum eklemeden kaydedin."]
    elif "hakaret" in kategori_metin or "alay" in kategori_metin:
        tavsiyeler = ["Öğrenciyi bireysel ve yargılamadan dinleyin; olayın sıklığını, bağlamını ve etkisini netleştirin.",
                      "Tanık beyanlarını ayrı alın; otomatik sinyali tek başına kanıt kabul etmeyin.",
                      "Güvenli sınıf iklimi ve davranış değişikliği için takip planı oluşturun."]
    if tavsiyeler:
        st.markdown("#### " + _tr("Rehberlik için önerilen adımlar"))
        with st.container(border=True):
            st.info("Genel kontrol listesidir; okul psikolojik danışmanı ve kurum protokolü tarafından uyarlanmalıdır.")
            for madde in tavsiyeler: st.markdown("- " + _tr(madde))

    st.markdown("**Açıklama**")
    with st.container(border=True):
        guvenli_metin(k["aciklama"] or "Açıklama bulunmuyor.")
    ekler = db.ek_bilgileri_getir(k["takip_no"])
    if ekler:
        st.markdown(f"**Anonim gönderenin ek bilgileri ({len(ekler)})**")
        for e in ekler:
            with st.container(border=True):
                st.caption(format_timestamp(e["zaman"], ss.get("dil", "Türkçe")))
                guvenli_metin(e["metin"])
    with st.expander("Otomatik sinyal ve değerlendirme notu", expanded=k["oncelik"] in ("Acil", "Yüksek")):
        st.write(f"**Öncelik sinyali:** {k['oncelik']}")
        kategori_goster = ", ".join(_tr(x) for x in (k["kategoriler"] or "").split(", ") if x)
        st.write(f"**Kategoriler:** {kategori_goster or '—'}")
        st.markdown(f"**{_tr('Eşleşen ifadeler:')}**")
        guvenli_metin(k["eslesmeler"] or _tr("Belirgin eşleşme yok"))
        for u in filter(None, (k["baglam_uyarilari"] or "").split(" | ")):
            st.warning(_tr(u))
        if k["maskelenen"]:
            maskeli_turler = ", ".join(_tr(x) for x in (k["maskelenen"] or "").split(", "))
            st.caption(f"Açıklamada otomatik maskelenen bilgi türleri: {maskeli_turler}")
        # Basit kalite kontrolü: kayıt silmez; yalnızca incelemeciye dikkat notu verir.
        aciklama_kontrol = (k.get("aciklama") or "").strip()
        kelimeler = [parca for parca in aciklama_kontrol.split() if any(ch.isalnum() for ch in parca)]
        yalniz_tekrar = len(aciklama_kontrol) >= 4 and len(set(aciklama_kontrol.lower().replace(" ", ""))) <= 2
        if len(aciklama_kontrol) < 8 or len(kelimeler) < 2 or yalniz_tekrar:
            st.warning("**Açıklama kalitesi kontrolü:** Metin çok kısa, yeterince açıklayıcı olmayabilir veya tekrar eden karakterler içeriyor. "
                       "Bu bir spam/asılsız bildirim kanıtı değildir; otomatik silinmez, yetkili kişi bağlamı kontrol etmelidir.")
        else:
            st.info("**Açıklama kalitesi kontrolü:** Metin temel uzunluk kontrolünü geçti. Bu, bildirimin doğru olduğu anlamına gelmez.")
        st.caption(f"Algılayıcı sürümü: {k['analiz_surumu'] or 'v1 (eski kayıt)'}. Bu sürüm gerçek bir yapay zekâ modeli değil, kural tabanlı sinyal ve basit metin kalite kontrolü kullanır. "
                   "Sinyal kanıt veya karar değildir; bağlamı anlayamaz. Eşleşme olmaması da sorun olmadığı anlamına gelmez.")


def _inceleme_formlari(k: dict) -> None:
    no = k["takip_no"]
    st.markdown("#### İnceleme ve yönlendirme")
    with st.form(f"inceleme_{no}"):
        c1, c2 = st.columns(2)
        durum = c1.selectbox("İnceleme durumu", DURUMLAR, key=f"durum_{no}",
                             index=DURUMLAR.index(k["durum"]) if k["durum"] in DURUMLAR else 0)
        birim = c2.selectbox("Sorumlu birim", BIRIMLER, key=f"birim_{no}",
                             index=BIRIMLER.index(k["birim"]) if k["birim"] in BIRIMLER else 0)
        kaydet = st.form_submit_button("Değişiklikleri kaydet", type="primary")
    if kaydet:
        try:
            degisen = db.durum_ve_birim_guncelle(no, durum, birim, ss.yonetici_adi)
        except (sqlite3.Error, ValueError, LookupError):
            st.error("Değişiklik kaydedilemedi. Lütfen yeniden deneyin.")
        else:
            flash("success" if degisen else "info",
                  "İnceleme bilgileri kaydedildi." if degisen else "Değişiklik yapılmadı; bilgiler zaten güncel.")
            st.rerun()

    notlar_k, gecmis_k = st.columns(2, gap="large")
    with notlar_k:
        st.markdown("#### İnceleme notları")
        with st.form(f"not_{no}"):
            metin = st.text_area("Yeni not", max_chars=db.MAKS_NOT_UZUNLUGU, key=f"not_metni_{no}",
                                 placeholder="İncelemeyle ilgili kısa not ekleyin.")
            gonder = st.form_submit_button("Notu kaydet")
        if gonder:
            try:
                db.not_ekle(no, metin, ss.yonetici_adi)
            except ValueError:
                st.error("Boş not eklenemez.")
            except (sqlite3.Error, LookupError):
                st.error("Not kaydedilemedi.")
            else:
                flash("success", "Not eklendi.")
                st.rerun()
        notlar = db.notlari_getir(no)
        if not notlar:
            st.caption("Henüz not eklenmemiş.")
        for n in notlar:
            with st.container(border=True):
                st.caption(f"{format_timestamp(n['zaman'], ss.get('dil', 'Türkçe'))} · {n['yazar'] or '—'}")
                guvenli_metin(n["not_metni"])
    with gecmis_k:
        st.markdown("#### İşlem geçmişi")
        gecmis = db.gecmisi_getir(no)
        if not gecmis:
            st.caption("Henüz işlem geçmişi yok.")
        for g in gecmis:
            with st.container(border=True):
                st.markdown(f"**{g['islem']}**")
                st.caption(f"{format_timestamp(g['zaman'], ss.get('dil', 'Türkçe'))} · {g['aktor'] or '—'}")
                if g["ayrinti"]:
                    st.write(g["ayrinti"])


def _kayitlar_sekmesi(kayitlar: list[dict]) -> None:
    sayac = {d: sum(k["durum"] == d for k in kayitlar) for d in DURUMLAR}
    acil = sum(k["oncelik"] in ("Acil", "Yüksek") and k["durum"] != "Sonuçlandırıldı" for k in kayitlar)
    gecikmis = sum(k["durum"] == "İnceleme bekliyor" and db.gecen_saat(k["olusturma_zamani"]) > SLA_SAAT for k in kayitlar)
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m6.metric(f"{SLA_SAAT} saati aşan bekleyen", gecikmis)
    m1.metric("Toplam kayıt", len(kayitlar))
    m2.metric("İlk inceleme", sayac["İnceleme bekliyor"])
    m3.metric("Aktif takip", sayac["İnceleniyor"] + sayac["Takip gerekiyor"])
    m4.metric("Sonuçlandırıldı", sayac["Sonuçlandırıldı"])
    m5.metric("Yüksek veya acil sinyal (açık)", acil)
    if not kayitlar:
        st.info("Henüz kayıt yok. Yeni bir bildirim oluşturulduğunda burada görünür.")
        return

    filtre_k, detay_k = st.columns([0.9, 1.7], gap="large")
    with filtre_k:
        st.markdown("#### Kayıt kuyruğu")
        arama = st.text_input("Kayıt ara", placeholder="Takip kodu, olay türü, ortam veya birim", key="inc_arama")
        durum_f = st.selectbox("İnceleme durumu", ["Tüm durumlar"] + DURUMLAR, key="inc_durum")
        oncelik_f = st.selectbox("Öncelik sinyali", ["Tümü"] + list(ONCELIKLER[::-1]), key="inc_oncelik")
        tur_f = st.selectbox("Bildirim türü", ["Tümü", "Anonim", "Kimlik bilgisi belirtilmiş"], key="inc_anonim")
        birim_f = st.selectbox("Sorumlu birim", ["Tüm birimler"] + BIRIMLER, key="inc_birim")
        st.markdown("**Tarih aralığı**")
        tarih_bugun = datetime.now(db.TZ).date()
        tarih_siniri = min((datetime.strptime(k["olusturma_zamani"][:10], "%Y-%m-%d").date()
                            for k in kayitlar), default=tarih_bugun)
        t1, t2 = st.columns(2)
        tarih_bas = t1.date_input("Başlangıç tarihi", value=max(tarih_siniri, tarih_bugun - timedelta(days=7)),
                                  min_value=tarih_siniri, max_value=tarih_bugun, key="inc_tarih_bas")
        tarih_son = t2.date_input("Bitiş tarihi", value=tarih_bugun, min_value=tarih_siniri,
                                  max_value=tarih_bugun, key="inc_tarih_son")
        sirala = st.selectbox("Sıralama", ["Öncelik (yüksekten)", "En yeni önce", "En eski önce"], key="inc_sira")

        gorunen = []
        a = arama.strip().casefold()
        for k in kayitlar:
            try:
                kayit_tarihi = datetime.strptime(k["olusturma_zamani"][:10], "%Y-%m-%d").date()
            except (TypeError, ValueError):
                continue
            if tarih_bas > tarih_son or not (tarih_bas <= kayit_tarihi <= tarih_son): continue
            if durum_f != "Tüm durumlar" and k["durum"] != durum_f: continue
            if oncelik_f != "Tümü" and k["oncelik"] != oncelik_f: continue
            if tur_f == "Anonim" and not k["anonim"]: continue
            if tur_f == "Kimlik bilgisi belirtilmiş" and k["anonim"]: continue
            if birim_f != "Tüm birimler" and k["birim"] != birim_f: continue
            if a and a not in " ".join(str(k.get(x, "")) for x in ("takip_no", "olay_turu", "ortam", "birim")).casefold():
                continue
            gorunen.append(k)
        gorunen.sort(key=lambda x: x["olusturma_zamani"], reverse=(sirala != "En eski önce"))
        if sirala.startswith("Öncelik"):
            gorunen.sort(key=lambda x: ONCELIK_SIRASI.get(x["oncelik"], 0), reverse=True)  # kararlı sıralama

        st.caption(f"{len(gorunen)} kayıt")
        if not gorunen:
            st.info("Bu filtrelerle eşleşen kayıt bulunamadı.")
            return
        secenekler = [k["takip_no"] for k in gorunen]
        ek_say = db.ek_sayilari()
        etiket = {k["takip_no"]: f"{k['takip_no']} · {_tr(k['olay_turu'])} · {_tr(k['oncelik'])} · {_tr(k['durum'])}"
                  + (f" · {db.gecen_saat(k['olusturma_zamani']):.1f} {_tr('saat bekliyor')}" if k["durum"] == "İnceleme bekliyor" else "")
                  + (f" · +{ek_say[k['takip_no']]} {_tr('ek bilgi')}" if k["takip_no"] in ek_say else "")
                  + (" · " + _tr("GECİKMİŞ") if k["durum"] == "İnceleme bekliyor" and db.gecen_saat(k["olusturma_zamani"]) > SLA_SAAT else "")
                  for k in gorunen}
        if ss.get("inceleme_secili") not in secenekler:
            ss["inceleme_secili"] = secenekler[0]   # widget oluşturulmadan ÖNCE atama güvenlidir
        secili_no = st.selectbox("Kayıt seç", secenekler, key="inceleme_secili", format_func=etiket.get)
        k = next(x for x in gorunen if x["takip_no"] == secili_no)
        st.markdown(
            f"<div class='record-banner'><div><div class='record-kicker'>SEÇİLİ KAYIT</div>"
            f"<div class='record-id'>{html.escape(k['takip_no'])}</div></div><div class='pills'>"
            f"{pill(k['durum'], DURUM_SINIF.get(k['durum'], 'status-waiting'))}"
            f"{pill('Sinyal: ' + k['oncelik'], ONCELIK_SINIF.get(k['oncelik'], 'prio-none'))}</div></div>",
            unsafe_allow_html=True)
    with detay_k:
        _kayit_detayi(k)
        _inceleme_formlari(k)


def sayfa_inceleme() -> None:
    st.markdown("<div class='page-heading'><div class='eyebrow-dark'>KAYIT YÖNETİMİ</div><h1>Bildirim inceleme</h1>"
                "<p>Kayıtları tek bir çalışma alanında görüntüleyin, yönlendirin ve işlem geçmişini takip edin.</p></div>",
                unsafe_allow_html=True)
    yonetici_gerekli()
    kayitlar = db.kayitlari_getir()
    _gunluk_ozet(kayitlar)
    sekme1, sekme2, sekme3 = st.tabs(["Kayıtlar", "Denetim kaydı", "Dışa aktarım ve saklama"])
    with sekme1:
        _kayitlar_sekmesi(kayitlar)
    with sekme2:
        st.caption("Girişler, başarısız denemeler, dışa aktarımlar ve silme işlemleri burada izlenir.")
        satirlar = db.denetim_getir()
        if satirlar:
            st.dataframe([{"Zaman": format_timestamp(r["zaman"], ss.get("dil", "Türkçe")), "Kullanıcı": r["aktor"], "İşlem": r["islem"],
                           "Ayrıntı": r["ayrinti"]} for r in satirlar], hide_index=True)
        else:
            st.info("Henüz denetim kaydı yok.")
    with sekme3:
        st.subheader("Dışa aktarım")
        kimlik = st.checkbox("Kimlik bilgilerini (ad, soyad, sınıf) dahil et", value=False,
                             help="Varsayılan olarak kapalıdır (veri minimizasyonu).")
        st.download_button("CSV indir", data=db.csv_aktar(kayitlar, kimlik),
                           file_name=f"guvenli_okul_{datetime.now(db.TZ):%Y%m%d_%H%M}.csv", mime="text/csv",
                           on_click=db.denetim_ekle,
                           args=(ss.yonetici_adi, "CSV dışa aktarım", "kimlik dahil" if kimlik else "kimlik hariç"))
        st.subheader("Kalıcı veri saklama")
        st.success("Bildirimler, inceleme notları, ek bilgiler, önleyici çalışmalar ve işlem geçmişi için 180/360 günlük otomatik silme yoktur. Süre dolduğu için kayıt silinmez.")
        st.caption("Kayıt silme arayüzü devre dışıdır. Veri kaybı riskine karşı Yönetim → Yedekleme ve geri yükleme bölümünden düzenli yedek alın.")
    altbilgi()


# ========================================================== 6. İSTATİSTİKLER
def _saat_metni(o: dict) -> str:
    if not o["n"]:
        return _tr("Veri yok")
    birim = "h" if ss.get("dil") == "English" else "sa"
    return f"{o['medyan']:.1f} {birim} (n={o['n']})"


def sayfa_istatistikler() -> None:
    st.title("İstatistikler")
    if not ISTATISTIKLER_HERKESE_ACIK:
        yonetici_gerekli()
    s = db.istatistik_ozeti()
    st.caption("Grafikler yalnızca bu uygulamada kayıtlı bilgileri özetler; okul geneline ilişkin sonuç göstermez.")
    if not s["toplam"]:
        st.info("Henüz kayıt yok. Yeni kayıtlar eklendikçe istatistikler burada görüntülenir.")
        return
    if s["toplam"] < 10:
        st.warning("Kayıt sayısı çok az; yüzdeler ve karşılaştırmalar yanıltıcı olabilir, yorum yapmayın.")
    m = st.columns(4)
    m[0].metric("Toplam bildirim", s["toplam"])
    m[1].metric("Anonim oranı", f"%{100 * s['anonim'] / s['toplam']:.0f}")
    m[2].metric("İlk işlem süresi (medyan)", _saat_metni(s["ilk_inceleme_saat"]))
    m[3].metric("Sonuçlanma süresi (medyan)", _saat_metni(s["sonuclanma_saat"]))
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.subheader("Durum dağılımı")
        st.bar_chart(s["durum"], horizontal=True)
        st.subheader("Öncelik sinyali dağılımı")
        st.bar_chart(s["oncelik"], horizontal=True)
    with c2:
        st.subheader("Olay türü dağılımı")
        st.bar_chart(s["tur"], horizontal=True)
        st.subheader("Son 30 gün: günlük bildirim")
        if s["gunluk"]:
            gunluk_veri = {}
            for gun, adet in s["gunluk"]:
                try:
                    dt = datetime.strptime(gun, "%Y-%m-%d")
                    etiket = dt.strftime("%d.%m") if ss.get("dil") != "English" else f"{('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec')[dt.month - 1]} {dt.day:02d}"
                except ValueError:
                    etiket = gun
                gunluk_veri[etiket] = adet
            st.bar_chart(gunluk_veri)
        else:
            st.caption("Bu dönemde kayıt yok.")
    st.caption("Süreler kayıt oluşturma ile ilk durum değişikliği / 'Sonuçlandırıldı' arasındaki farktır. "
               "Yeni anonim kayıtlar dakika ve saniye hassasiyetinde kaydedilir; eski yuvarlanmış kayıtların geçmiş zamanı geriye dönük kesinleştirilemez.")


# ================================================== 7. ARAŞTIRMA VE TEST
KONTROL_LISTESI = (
    ("T01", "Anonim bildirim", "Formda ad/soyad/sınıf istenmemeli ve kaydedilmemeli."),
    ("T02", "Sınıf seçenekleri", "9/A … 12/B seçenekleri görünmeli."),
    ("T03", "Takip kodu", "Her kayıt benzersiz ve tahmin edilmesi zor bir kod üretmeli."),
    ("T04", "Yetkisiz erişim", "Girişsiz, inceleme/istatistik/denetim kayıtları görünmemeli."),
    ("T05", "Durum güncelleme", "Değişiklik kaydedilmeli, geçmişe işlemi yapanla birlikte eklenmeli."),
    ("T06", "Not geçmişi", "Not kaydedilmeli; yazar bilgisiyle ilgili kayıtta görünmeli."),
    ("T07", "Boş form", "Açıklama veya onay yoksa kayıt oluşturulmamalı; yazılan metin silinmemeli."),
    ("T08", "Temiz başlangıç", "Yeni kurulumda örnek kayıt olmamalı; yeniden başlatmada kayıt silinmemeli."),
    ("T09", "İstatistikler", "Grafik toplamları kayıt sayılarıyla uyumlu olmalı."),
    ("T10", "Güvenli metin", "Arayüz gerçek kişisel veri girilmemesi gerektiğini açıkça belirtmeli."),
    ("T11", "Hatalı giriş sınırı", "5 hatalı denemeden sonra giriş geçici olarak kilitlenmeli."),
    ("T12", "Oturum zaman aşımı", "30 dakika hareketsizlikte yönetici oturumu kapanmalı."),
    ("T13", "Kişisel veri maskeleme", "Açıklamaya yazılan telefon/T.C. no/e-posta/IBAN kayıtta maskeli olmalı."),
    ("T14", "Takip kodu sorgusu", "Sorgu yalnızca durum ve tarih göstermeli; açıklama/not göstermemeli."),
    ("T15", "CSV dışa aktarım", "Kimlik alanları varsayılan olarak dışarıda olmalı; işlem denetim kaydına yazılmalı."),
    ("T16", "Günlük kota", "Anonim bildirimden sonra aynı cihazdan ikinci anonim bildirim engellenmeli."),
    ("T17", "Ek bilgi", "Takip koduyla aynı gün ek bilgi eklenebilmeli; 60 sn bekleme ve günde 3 sınırı uygulanmalı."),
)


def _degerlendirme_sekmesi() -> None:
    st.write("Algılayıcının sentetik (elle yazılmış, gerçek veri içermeyen) örnek kümesindeki performansını ölçer. "
             "Aynı ölçüm komut satırından `python -m unittest discover -s testler` ile de çalışır.")
    st.caption(f"Algılayıcı sürümü: {ht.SURUM} · Sözlük: {sum(ht.sozluk_ozeti().values())} ifade, "
               + ", ".join(f"{_tr(k)}: {v}" for k, v in ht.sozluk_ozeti().items()))
    if st.button("Değerlendirmeyi çalıştır", type="primary"):
        ss["degerlendirme_sonucu"] = degerlendirme.degerlendir()
    r = ss.get("degerlendirme_sonucu")
    if not r:
        return
    m = st.columns(5)
    m[0].metric("Örnek sayısı", r["toplam"])
    m[1].metric("Kesinlik (precision)", f"{r['precision']:.2f}")
    m[2].metric("Duyarlılık (recall)", f"{r['recall']:.2f}")
    m[3].metric("F1", f"{r['f1']:.2f}")
    m[4].metric("Doğruluk", f"{r['accuracy']:.2f}")
    st.markdown("**Karışıklık matrisi**")
    st.table({"": ["Gerçekte sinyal var", "Gerçekte sinyal yok"],
              "Sinyal verildi": [r["tp"], r["fp"]], "Sinyal verilmedi": [r["fn"], r["tn"]]})
    st.markdown("**Örnek türüne göre doğruluk**")
    st.dataframe([{"Tür": t, "Örnek": o["n"], "Doğru": o["dogru"], "Oran": round(o["dogru"] / o["n"], 2)}
                  for t, o in r["tur_ozeti"].items()], hide_index=True)
    st.markdown("**Kategoriye göre yakalama (duyarlılık)**")
    st.dataframe([{"Kategori": t, "Örnek": o["n"], "Yakalanan": o["bulunan"], "Oran": round(o["bulunan"] / o["n"], 2)}
                  for t, o in r["kategori_ozeti"].items()], hide_index=True)
    with st.expander(f"Yanlış alarmlar ({len(r['yanlis_pozitifler'])}) ve kaçırılanlar ({len(r['kacirilanlar'])})"):
        st.write("**Yanlış alarm:**", r["yanlis_pozitifler"] or "—")
        st.write("**Kaçırılan:**", r["kacirilanlar"] or "—")
    st.warning("Küme küçüktür, araştırmacılar tarafından yazılmıştır ve sözlük bu kümeye bakılarak iyileştirilmiştir; "
               "sonuçlar iyimserdir ve genellenemez. Bilimsel geçerlik için bağımsız, etik onaylı ve en az iki "
               "değerlendiricinin etiketlediği bir veri kümesi gerekir.")
    st.download_button("Sonucu JSON olarak indir", json.dumps(r, ensure_ascii=False, indent=2),
                       file_name="degerlendirme_sonucu.json", mime="application/json")


def sayfa_arastirma() -> None:
    st.title("Araştırma ve kalite kontrol")
    s1, s2, s3 = st.tabs(["Otomatik değerlendirme", "Elle kontrol listesi", "Yöntem ve sınırlılıklar"])
    with s1:
        _degerlendirme_sekmesi()
    with s2:
        for kod, baslik, aciklama in KONTROL_LISTESI:
            with st.expander(f"{kod} · {baslik}"):
                st.write(aciklama)
                st.checkbox("Bu senaryoyu test ettim", key=f"test_{kod}")
        bitti = sum(bool(ss.get(f"test_{kod}")) for kod, _, _ in KONTROL_LISTESI)
        st.progress(bitti / len(KONTROL_LISTESI), text=f"İşaretlenen test: {bitti}/{len(KONTROL_LISTESI)}")
        st.warning("İşaretler yalnızca bu oturumda tutulur; resmi test raporu veya bilimsel doğrulama yerine geçmez.")
    with s3:
        st.markdown("""
1. **Amaç:** Bildirim sürecinin anlaşılırlığını, temel işlevlerin doğruluğunu ve kural tabanlı sinyalin ölçülebilir
   başarımını raporlamak.
2. **Algılayıcı:** Makine öğrenmesi içermez; Türkçe'ye duyarlı normalleştirme (İ/ı, ASCII katlama), kelime başı sınırı,
   harf tekrarı/ayraç/rakamla yazım çözümü ve kategori+ağırlık tabanlı öncelik kuralı kullanır.
3. **Ölçüt:** Kesinlik, duyarlılık, F1 ve kategori bazlı yakalama; ayrıca "zor örnek" kümesiyle bilinen sınırlılıklar.
4. **Sınırlılıklar:** Bağlam, ironi, imâ ve ima yoluyla dışlama yakalanmaz; deyimsel abartı ("babam beni öldürecek")
   yanlış alarm üretir; yazım hataları ("apdal") kaçar; sözlük küçüktür.
5. **Yol haritası:** (a) etik kurul/okul izniyle, kimliksizleştirilmiş ve en az iki uzmanca etiketlenmiş veri kümesi,
   (b) değerlendiriciler arası uyum (Cohen kappa), (c) eğitim/doğrulama/test ayrımı, (d) kural tabanlı yöntemin bir
   dil modeli veya sınıflandırıcı ile karşılaştırılması, (e) kullanılabilirlik testi (SUS ölçeği).
6. **Etik:** Gerçek öğrenci verisi için önceden okul/veli onayı, gönüllülük, veri minimizasyonu ve güvenli saklama planı
   gerekir. Bu uygulamada gerçek öğrenci verisi kullanmayın.""")


# ======================================================= 8. GÜVENLİ KULLANIM
def sayfa_guvenli_kullanim() -> None:
    st.title("Güvenli kullanım")
    st.markdown(acil_hat_html(), unsafe_allow_html=True)
    st.subheader("Platformun işlevleri")
    st.markdown("""
- Tam anonim bildirim alır (ad, sınıf, telefon istenmez; zaman dakika ve saniye hassasiyetinde kaydedilir); günde bir bildirim hakkı vardır.
- Açıklamadaki telefon, T.C. kimlik numarası, e-posta ve IBAN'ı otomatik maskeler.
- Takip koduyla durum sorgulamaya ve (anonim kayıtlarda, aynı gün) ek bilgi eklemeye izin verir.
- Yönetici girişinden sonra kayıtları listeler; durum/birim günceller; not ve işlem geçmişi tutar.
- Girişleri ve yönetici işlemlerini denetim kaydında saklar; CSV dışa aktarım ve veritabanı yedekleme/geri yükleme sunar. Kayıtlar süre dolduğu için otomatik silinmez.
- İfade eşleşmelerini yalnızca insan incelemesi için öncelik sinyali olarak gösterir.""")
    st.subheader("Sınırlar")
    st.markdown("""
- Gerçek bir okul veya rehberlik servisine bağlı değildir; acil yardım ya da resmi bildirim hizmeti değildir.
- Zorbalık hakkında otomatik kesin karar vermez; sinyaller yanlış alarm üretebilir ve olayları kaçırabilir.
- Tek yönetici hesabı kurumsal kimlik doğrulamanın (SSO/2FA) yerini tutmaz.
- Yerel SQLite dosyasının bulut ortamında kalıcı olacağı garanti edilmez; yedekleme planı gerekir.
- Hatalı giriş ve zaman aşımı korumaları vardır, ancak bu bir güvenlik denetiminden geçmemiştir.""")
    st.subheader("Gerçek kullanıma geçmeden önce (kontrol listesi)")
    st.markdown("""
- **KVKK (6698):** veri sorumlusunun belirlenmesi, aydınlatma metni, hukuki sebep/veli onayı, saklama-imha politikası,
  gerekiyorsa VERBİS ve veri işleyen sözleşmeleri. Çocuk verisi ve olası yurt dışı sunucu kullanımı (ör. bulut barındırma)
  ayrıca hukuki değerlendirme gerektirir.
- **Yasal bildirim yükümlülükleri:** çocuğa yönelik istismar/şiddet şüphesinde mevzuattaki bildirim yükümlülükleri bu
  uygulamanın kayıt akışından bağımsızdır; okul yönetimi ve hukuk danışmanıyla netleştirilmelidir.
- **Erişim:** kişi bazlı hesaplar, rol ayrımı, iki aşamalı doğrulama, parola özeti (`tools/parola_hash.py`).
- **Altyapı:** HTTPS, şifreli yedek, günlüklerin korunması, bağımsız güvenlik testi.
- **Okul süreci:** kayıtları kimin, ne kadar sürede inceleyeceği, acil durum protokolü ve rehberlik servisiyle iş akışı.""")
    altbilgi()


_CIHAZ_HTML = r"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"></head><body>
<script>
/* Cihaz jetonu bileşeni: jeton bu bileşenin KENDİ localStorage'ında (yedek: çerez) saklanır ve
   Streamlit'e geri gönderilir. Kimlikle ilişkisi yoktur; yalnızca günlük kotayı uygulamak içindir. */
(function () {
  var HEX = /^[a-f0-9]{48}$/;
  function uret() {
    var a = new Uint8Array(24); crypto.getRandomValues(a);
    return Array.from(a, function (b) { return ("0" + b.toString(16)).slice(-2); }).join("");
  }
  function cerezOku() {
    var m = document.cookie.match(/(?:^|; )gb_cihaz=([a-f0-9]{48})/); return m ? m[1] : null;
  }
  var t = null;
  try { t = localStorage.getItem("gb_cihaz"); } catch (e) {}
  if (!t || !HEX.test(t)) t = cerezOku();
  if (!t || !HEX.test(t)) t = uret();
  try { localStorage.setItem("gb_cihaz", t); } catch (e) {}
  try { document.cookie = "gb_cihaz=" + t + ";max-age=31536000;path=/;SameSite=Lax"; } catch (e) {}

  function gonder(tip, ek) {
    window.parent.postMessage(Object.assign({ isStreamlitMessage: true, type: tip }, ek), "*");
  }
  var gonderildi = false;
  window.addEventListener("message", function (e) {
    if (e.data && e.data.type === "streamlit:render" && !gonderildi) {
      gonderildi = true;
      gonder("streamlit:setComponentValue", { value: t, dataType: "json" });
    }
  });
  gonder("streamlit:componentReady", { apiVersion: 1 });
  gonder("streamlit:setFrameHeight", { height: 0 });
})();
</script></body></html>
"""


def _cihaz_bileseni_hazirla():
    """Bileşen dosyasını çalışma anında geçici klasöre yazar (depoda ayrı klasör gerekmez).
    Başarısız olursa None döner; uygulama çökmez, kota yalnızca oturum düzeyinde çalışır."""
    try:
        klasor = Path(tempfile.gettempdir()) / "guvenli_okul_cihaz_bileseni"
        klasor.mkdir(parents=True, exist_ok=True)
        dosya = klasor / "index.html"
        if not dosya.exists() or dosya.read_text(encoding="utf-8") != _CIHAZ_HTML:
            dosya.write_text(_CIHAZ_HTML, encoding="utf-8")
        return components.declare_component("cihaz_jetonu", path=str(klasor))
    except Exception:
        return None


_CIHAZ_BILESENI = _cihaz_bileseni_hazirla()


def _cihaz_jetonu() -> str | None:
    """Tarayıcıda kalıcı (localStorage + çerez yedeği) rastgele cihaz jetonu. Küçük bir yerel bileşen
    jetonu tarayıcıdan okuyup Streamlit'e gönderir; ilk çalışmada henüz gelmemiş olabilir (None).
    Kimlikle ilişkisi yoktur; veritabanında yalnızca SHA-256 özeti ve gün saklanır."""
    if _CIHAZ_BILESENI is None:  # yedek: yalnızca bu oturum için jeton (yenilemede sıfırlanır)
        ss.setdefault("cihaz_jetonu_deger", secrets.token_hex(24))
        return ss["cihaz_jetonu_deger"]
    deger = _CIHAZ_BILESENI(key="cihaz_jetonu", default=None)
    if isinstance(deger, str) and re.fullmatch(r"[a-f0-9]{48}", deger):
        ss["cihaz_jetonu_deger"] = deger
    return ss.get("cihaz_jetonu_deger")


def sayfa_destek() -> None:
    ek_sayfalar.destek()
    altbilgi()


def sayfa_trend() -> None:
    yonetici_gerekli()
    ek_sayfalar.trend()
    altbilgi()


def sayfa_kvkk() -> None:
    ek_sayfalar.kvkk(bool(ss.yonetici_giris))
    altbilgi()


def sayfa_etki_merkezi() -> None:
    yonetici_gerekli()
    st.title("Etki Merkezi")
    st.caption("Anonim ve toplu bildirim eğilimlerinden hareketle önleyici çalışmalar planlayın ve takip edin.")
    st.info("Bu bölüm demo amaçlıdır. Sorumlu öğretmen/yetkili kişi bilgisini yönetici kendisi girer. Bu sürümde gerçek öğrenci veya personel bilgisi yerine örnek veri kullanın.")
    ozet = db.onleyici_ozeti()
    kartlar = st.columns(4)
    for kolon, etiket in zip(kartlar, ("Planlandı", "Devam ediyor", "Tamamlandı", "Toplam")):
        kolon.metric(etiket, ozet.get(etiket, 0))

    with st.expander("+ Yeni önleyici çalışma oluştur", expanded=not bool(db.onleyici_calismalari_getir())):
        with st.form("etki_yeni_calisma_form"):
            baslik = st.text_input("Çalışma başlığı", max_chars=120, placeholder="Örn. Dijital güvenlik farkındalık çalışması")
            aciklama = st.text_area("Açıklama ve hedef", max_chars=2000, placeholder="Çalışmanın amacı ve planlanan adımlar...")
            c1, c2 = st.columns(2)
            with c1:
                konu = st.selectbox("İlişkili konu", ["Genel"] + OLAY_TURLERI)
                hedef = st.selectbox("Hedef ortam", ["Tümü"] + ORTAMLAR)
                plan_tarih = st.date_input("Planlanan tarih", value=datetime.now(db.TZ).date())
            with c2:
                sorumlu = st.text_input("Sorumlu öğretmen / yetkili kişi", max_chars=100, placeholder="Yönetici kendisi yazar")
                birim = st.text_input("Sorumlu birim", max_chars=100, placeholder="Örn. Rehberlik servisi")
            olustur = st.form_submit_button("Çalışmayı kaydet", type="primary", use_container_width=True)
        if olustur:
            try:
                yeni_id = db.onleyici_calisma_ekle(
                    baslik=baslik, aciklama=aciklama, konu=konu, hedef_ortam=hedef,
                    sorumlu_kisi=sorumlu, sorumlu_birim=birim,
                    planlanan_tarih=plan_tarih.isoformat(), aktor=ss.yonetici_adi or "Yönetici")
                db.denetim_ekle(ss.yonetici_adi or "Yönetici", "Önleyici çalışma oluşturuldu", f"Çalışma no: {yeni_id}")
                flash("success", "Önleyici çalışma kaydedildi.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.subheader("Önleyici çalışmalar")
    calismalar = db.onleyici_calismalari_getir()
    if not calismalar:
        st.info("Henüz çalışma oluşturulmadı. İlk çalışmayı yukarıdaki formdan ekleyebilirsiniz.")
        altbilgi()
        return
    for calisma in calismalar:
        # Başlık, açıklama ve sorumlu bilgisi yönetici tarafından yazılan serbest metindir; otomatik çevrilmez.
        _orijinal_expander = getattr(st, "_guvenli_okul_originals", {}).get("expander", st.expander)
        with _orijinal_expander(f"{calisma['baslik']} · {_tr(calisma['durum'])}"):
            if calisma["aciklama"]:
                guvenli_metin(calisma["aciklama"])
            else:
                st.caption("Açıklama eklenmedi.")
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**{_tr('Konu:')}** {_tr(calisma['konu'])}")
            c2.markdown(f"**{_tr('Hedef ortam:')}** {_tr(calisma['hedef_ortam'])}")
            c3.markdown(f"**{_tr('Planlanan tarih:')}** {calisma['planlanan_tarih']}")
            st.markdown(f"**{_tr('Sorumlu:')}**")
            guvenli_metin(calisma["sorumlu_kisi"])
            st.markdown(f"**{_tr('Sorumlu birim:')}**")
            guvenli_metin(calisma["sorumlu_birim"] or _tr("Belirtilmedi"))
            with st.form(f"etki_guncelle_{calisma['id']}"):
                yeni_durum = st.selectbox("Çalışma durumu", db.ONLEYICI_DURUMLAR,
                                          index=db.ONLEYICI_DURUMLAR.index(calisma['durum']), key=f"etki_durum_{calisma['id']}")
                yeni_sorumlu = st.text_input("Sorumlu öğretmen / yetkili kişi", value=calisma["sorumlu_kisi"], max_chars=100, key=f"etki_sorumlu_{calisma['id']}")
                yeni_birim = st.text_input("Sorumlu birim", value=calisma["sorumlu_birim"], max_chars=100, key=f"etki_birim_{calisma['id']}")
                degerlendirme = st.text_area("Değerlendirme / işlem notu", max_chars=1000, key=f"etki_not_{calisma['id']}")
                guncelle = st.form_submit_button("Değişiklikleri kaydet")
            if guncelle:
                try:
                    db.onleyici_calisma_guncelle(calisma["id"], durum=yeni_durum, sorumlu_kisi=yeni_sorumlu,
                                                 sorumlu_birim=yeni_birim, aktor=ss.yonetici_adi or "Yönetici", not_metni=degerlendirme)
                    db.denetim_ekle(ss.yonetici_adi or "Yönetici", "Önleyici çalışma güncellendi", f"Çalışma no: {calisma['id']}")
                    flash("success", "Çalışma bilgileri güncellendi.")
                    st.rerun()
                except (ValueError, LookupError) as exc:
                    st.error(str(exc))
            gecmis = db.onleyici_calisma_gecmisi_getir(calisma["id"])
            st.markdown("**İşlem geçmişi**")
            if gecmis:
                _orijinal_dataframe = getattr(st, "_guvenli_okul_originals", {}).get("dataframe", st.dataframe)
                _orijinal_dataframe([{"Zaman": format_timestamp(g["zaman"], ss.get("dil", "Türkçe")),
                                      _tr("İşlemi yapan"): g["aktor"], _tr("İşlem"): _tr(g["islem"]),
                                      _tr("Ayrıntı"): g["ayrinti"]}
                                     for g in gecmis], hide_index=True, use_container_width=True)
            else:
                st.caption("Henüz işlem geçmişi yok.")
            if calisma["durum"] == "Tamamlandı":
                etki = db.onleyici_etki_karsilastir(calisma["id"])
                st.markdown("**Öncesi / sonrası gözlemsel karşılaştırma**")
                if not etki:
                    st.caption("Karşılaştırma için yeterli tarih bilgisi bulunmuyor.")
                elif etki.get("bekleniyor"):
                    st.caption("Sonraki 30 günlük dönem henüz tamamlanmadı. Karşılaştırma için 30 günün geçmesi bekleniyor.")
                elif etki["gizli"]:
                    st.caption("Her iki 30 günlük dönemde de en az 5 kayıt gerekir. Daha azsa sayılar gizlilik için gösterilmez.")
                else:
                    a, b, c = st.columns(3)
                    a.metric("Önceki 30 gün", etki["once"])
                    b.metric("Sonraki 30 gün", etki["sonra"])
                    c.metric("Fark", f"{etki['degisim']:+d}")
                st.caption("Bu karşılaştırma yalnızca bildirim sayısındaki gözlemsel değişimi gösterir; olayların gerçek sıklığını veya çalışmanın nedensel etkisini kanıtlamaz.")
    altbilgi()


# ============================================================== YÖNLENDİRME
# ======================================================= 10. YENİ YARDIMCI MERKEZLER

def sayfa_farkindalik() -> None:
    st.title("Farkındalık ve eğitim merkezi")
    st.caption("Öğrenciler, veliler ve okul topluluğu için güvenli, yargılayıcı olmayan bilgilendirme.")
    for kart in gelistirmeler.EGITIM_KARTLARI:
        with st.expander(_tr(kart["title"]), expanded=False):
            st.write(_tr(kart["summary"]))
            for adim in kart["steps"]:
                st.markdown(f"- {_tr(adim)}")
    st.info("Bu içerikler genel bilgilendirmedir; profesyonel destek veya okulun resmî prosedürlerinin yerine geçmez.")
    altbilgi()


def sayfa_yardim() -> None:
    st.title("Yardım merkezi")
    st.caption("Platformu güvenli biçimde kullanmak için kısa adımlar.")
    for baslik, aciklama in gelistirmeler.HELP_STEPS:
        st.markdown(f"### {_tr(baslik)}")
        st.write(_tr(aciklama))
    st.warning("Güvenli Okul bu aşamada demo/prototiptir. Gerçek okul sistemine bağlı değildir ve acil yardım hattı değildir.")
    altbilgi()


def sayfa_dil_erisim() -> None:
    st.title("Dil ve erişilebilirlik merkezi")
    st.caption("Arayüz dilini sol menüden değiştirebilirsiniz. Kullanıcı tarafından yazılan bildirimler ve yönetici notları özgün dilinde korunur.")
    st.markdown("**Desteklenen arayüz dilleri**")
    st.write("Türkçe · English · Deutsch · Français · Español · العربية · Azərbaycan dili")
    buyuk = st.checkbox("Yazıları büyüt", key="eris_buyuk")
    kontrast = st.checkbox("Yüksek kontrastı aç", key="eris_kontrast")
    if buyuk or kontrast:
        css = "<style>" + (".stApp {font-size:1.12rem!important} p,li,label {font-size:1.12rem!important}" if buyuk else "") + (".stApp {filter:contrast(1.18)}" if kontrast else "") + "</style>"
        st.markdown(css, unsafe_allow_html=True)
    st.info("Arapça seçildiğinde sağdan sola yazım yönü etkinleştirilir. Takip kodları soldan sağa korunur.")
    st.caption("Okulun ve projenin özel adları çevrilmez. Otomatik çeviri kullanıcı metinlerine uygulanmaz.")
    altbilgi()


def sayfa_takvim() -> None:
    yonetici_gerekli()
    st.title("Önleyici çalışma takvimi")
    st.caption("Etki Merkezi'nde oluşturulan çalışmaların yaklaşan tarihleri ve gecikme durumları.")
    uyarilar = gelistirmeler.takvim_uyarilari()
    if not uyarilar:
        st.success("Yaklaşan veya gecikmiş çalışma görünmüyor.")
    for u in uyarilar:
        item = u["item"]
        if u["type"] == "overdue":
            st.warning(f"Gecikmiş: {item['baslik']} · {u['days']} gün")
        else:
            st.info(f"Yaklaşıyor: {item['baslik']} · {u['days']} gün kaldı")
    calismalar = db.onleyici_calismalari_getir()
    if calismalar:
        st.dataframe([{"Çalışma":x["baslik"],"Tarih":x["planlanan_tarih"],"Durum":_tr(x["durum"]),"Sorumlu":x["sorumlu_kisi"],"Birim":x["sorumlu_birim"]} for x in calismalar], hide_index=True, use_container_width=True)
    st.caption("Takvim, Etki Merkezi'ndeki kayıtları kullanır; burada ikinci bir çalışma kaydı oluşturulmaz.")
    altbilgi()


def sayfa_bildirim_merkezi() -> None:
    yonetici_gerekli()
    st.title("Yönetici bildirim merkezi")
    st.caption("Bekleyen bildirimler, SLA uyarıları ve yaklaşan önleyici çalışmalar için yönetim özeti.")
    kayitlar = db.kayitlari_getir(limit=10000)
    bekleyen = [k for k in kayitlar if k.get("durum") == "İnceleme bekliyor"]
    geciken = [k for k in bekleyen if db.gecen_saat(k.get("olusturma_zamani", db.simdi())) >= SLA_SAAT]
    c1,c2,c3=st.columns(3); c1.metric("Bekleyen bildirim",len(bekleyen)); c2.metric("24 saati aşan",len(geciken)); c3.metric("Yaklaşan çalışma",sum(1 for a in gelistirmeler.takvim_uyarilari() if a["type"]=="upcoming"))
    if geciken:
        st.warning("İlk inceleme süresi 24 saati aşan kayıtlar var. Bu yalnızca takip uyarısıdır; acil müdahale hizmeti değildir.")
        st.dataframe([{"Takip kodu":k["takip_no"],"Oluşturulma":format_timestamp(k["olusturma_zamani"],ss.get("dil")),"Bekleme (saat)":round(db.gecen_saat(k["olusturma_zamani"]),1)} for k in geciken],hide_index=True)
    else:
        st.success("24 saati aşan bekleyen kayıt görünmüyor.")
    altbilgi()


def sayfa_yonetim_gunlugu() -> None:
    yonetici_gerekli()
    st.title("Gelişmiş yönetim işlem günlüğü")
    st.caption("Yönetici girişleri, kayıt değişiklikleri, dışa aktarımlar ve sistem işlemleri. Günlük kayıtları otomatik temizlenmez.")
    arama=st.text_input("İşlem veya kullanıcı ara",key="gunluk_ara")
    satirlar=db.denetim_getir(limit=5000)
    if arama:
        satirlar=[r for r in satirlar if arama.casefold() in " ".join(str(v) for v in r.values()).casefold()]
    st.metric("Gösterilen işlem",len(satirlar))
    if satirlar:
        st.dataframe([{"Zaman":format_timestamp(r["zaman"],ss.get("dil")),"Kullanıcı":r["aktor"],"İşlem":_tr(r["islem"]),"Ayrıntı":r["ayrinti"]} for r in satirlar],hide_index=True,use_container_width=True)
    else: st.info("Aramayla eşleşen işlem bulunamadı.")
    altbilgi()


def sayfa_pdf_rapor() -> None:
    yonetici_gerekli()
    st.title("Otomatik proje raporu")
    st.caption("Kişisel bildirim açıklamaları ve takip kodları rapora eklenmez; yalnızca toplu sayılar kullanılır.")
    if st.button("PDF raporunu oluştur",type="primary"):
        try:
            pdf=gelistirmeler.pdf_proje_raporu(ss.get("dil","Türkçe"))
            db.denetim_ekle(ss.yonetici_adi,"PDF proje raporu oluşturuldu")
            st.download_button("PDF dosyasını indir",pdf,file_name="guvenli_okul_proje_raporu.pdf",mime="application/pdf")
        except Exception as exc:
            st.error(f"PDF oluşturulamadı: {exc}")
    st.info("Rapor, bildirim sayısındaki değişimin tek başına zorbalık sıklığını veya önleyici çalışmanın nedensel etkisini kanıtlamadığını açıkça belirtir.")
    altbilgi()


def sayfa_yedekleme() -> None:
    yonetici_gerekli()
    st.title("Yedekleme ve geri yükleme")
    st.caption("Veri kaybına karşı veritabanının tutarlı yedeğini alın. Geri yükleme mevcut veritabanının üzerine yazar.")
    durum=db.veritabani_durumunu_kontrol_et()
    c1,c2,c3=st.columns(3); c1.metric("Bildirim",durum["bildirim"]); c2.metric("Önleyici çalışma",durum["onleyici"]); c3.metric("Veritabanı",f"{durum['boyut']/1024:.1f} KB")
    st.write("Bütünlük kontrolü:",durum["durum"])
    if st.button("Şimdi yedek oluştur",type="primary"):
        try:
            veri=db.veritabani_yedegi_uret(); db.denetim_ekle(ss.yonetici_adi,"Veritabanı yedeği alındı",f"{len(veri)} bayt")
            st.download_button("SQLite yedeğini indir",veri,file_name=f"guvenli_okul_yedek_{datetime.now(db.TZ):%Y%m%d_%H%M}.db",mime="application/x-sqlite3")
        except Exception as exc: st.error(f"Yedek alınamadı: {exc}")
    st.divider(); st.subheader("Yedekten geri yükle")
    yuklenen=st.file_uploader("Güvenli Okul .db yedek dosyası",type=["db","sqlite","sqlite3"],key="yedek_yukle")
    onay=st.checkbox("Mevcut veritabanının seçtiğim yedekle değiştirileceğini anlıyorum",key="yedek_onay")
    if st.button("Yedeği geri yükle",disabled=not (yuklenen and onay)):
        try:
            db.veritabani_yedegini_yukle(yuklenen.getvalue())
            db.denetim_ekle(ss.yonetici_adi,"Veritabanı yedeği geri yüklendi",yuklenen.name)
            flash("success","Yedek doğrulandı ve geri yüklendi. Sayfa yenilenecek."); st.rerun()
        except Exception as exc: st.error(f"Geri yükleme yapılmadı: {exc}")
    st.warning("Geri yükleme sonrasında yedekte bulunmayan yeni kayıtlar görünmez. İşlemden önce mevcut veritabanının da yedeğini indirin.")
    altbilgi()


SAYFALAR = {
    "Genel bakış": sayfa_genel_bakis,
    "Yeni bildirim": sayfa_yeni_bildirim,
    "Bildirim sorgula": sayfa_sorgula,
    "Destek rehberi": sayfa_destek,
    "Yönetici girişi": sayfa_yonetici_girisi,
    "Bildirim inceleme": sayfa_inceleme,
    "İstatistikler": sayfa_istatistikler,
    "Trend ve ortam": sayfa_trend,
    "Etki Merkezi": sayfa_etki_merkezi,
    "Önleyici çalışma takvimi": sayfa_takvim,
    "Farkındalık ve eğitim": sayfa_farkindalik,
    "Yardım merkezi": sayfa_yardim,
    "Dil ve erişilebilirlik": sayfa_dil_erisim,
    "Yönetici bildirim merkezi": sayfa_bildirim_merkezi,
    "Yönetim günlüğü": sayfa_yonetim_gunlugu,
    "PDF proje raporu": sayfa_pdf_rapor,
    "Yedekleme ve geri yükleme": sayfa_yedekleme,
    "Gizlilik ve KVKK": sayfa_kvkk,
    "Araştırma ve test": sayfa_arastirma,
    "Güvenli kullanım": sayfa_guvenli_kullanim,
}

oturum_denetle()

NAV = (
    ("KULLANICI", (("Genel bakış", "dashboard"), ("Yeni bildirim", "edit_note"), ("Bildirim sorgula", "search"),
                  ("Destek rehberi", "menu_book"), ("Yardım merkezi", "help"),
                  ("Farkındalık ve eğitim", "school"), ("Dil ve erişilebilirlik", "language"))),
    ("YÖNETİM", (("Yönetici girişi", "login"), ("Bildirim inceleme", "inbox"), ("İstatistikler", "bar_chart"),
                ("Trend ve ortam", "monitoring"), ("Etki Merkezi", "track_changes"),
                ("Önleyici çalışma takvimi", "calendar_month"), ("Yönetici bildirim merkezi", "notifications"),
                ("Yönetim günlüğü", "history"), ("PDF proje raporu", "picture_as_pdf"),
                ("Yedekleme ve geri yükleme", "backup"))),
    ("KURUMSAL", (("Araştırma ve test", "science"), ("Güvenli kullanım", "verified_user"),
                  ("Gizlilik ve KVKK", "policy"))),
)
KORUMALI = {"Bildirim inceleme", "İstatistikler", "Trend ve ortam", "Etki Merkezi", "Önleyici çalışma takvimi", "Yönetici bildirim merkezi", "Yönetim günlüğü", "PDF proje raporu", "Yedekleme ve geri yükleme"}

if ss.get("ana_menu") not in SAYFALAR:
    ss["ana_menu"] = "Genel bakış"
secili_sayfa = ss["ana_menu"]

with st.sidebar:
    st.selectbox("Dil / Language", list(LANGUAGES.keys()), key="dil")
    set_language(ss.get("dil", "Türkçe"))
    # Arabic uses right-to-left reading order while preserving the Latin tracking codes.
    if text_direction(ss.get("dil")) == "rtl":
        st.markdown("""<style>
        [data-testid="stAppViewContainer"] { direction: rtl; }
        [data-testid="stSidebar"] { direction: rtl; }
        [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"] { text-align: right; }
        input, textarea { direction: rtl; text-align: right; }
        code, .stCode, input[placeholder^="GO-"] { direction: ltr !important; text-align: left !important; }
        [data-testid="stMetric"] { text-align: right; }
        </style>""", unsafe_allow_html=True)
    else:
        st.markdown("<style>[data-testid='stAppViewContainer'],[data-testid='stSidebar']{direction:ltr}</style>", unsafe_allow_html=True)
    if not getattr(st, "_guvenli_okul_i18n_wrapped", False):
        _originals = {}
        for _component in ("markdown","write","caption","title","header","subheader","info","warning","error","success",
                           "button","text_input","text_area","checkbox","form_submit_button","metric","tabs",
                           "selectbox","radio","date_input","number_input","download_button","expander","slider",
                           "dataframe","table","bar_chart","progress"):
            _original = getattr(st, _component)
            _originals[_component] = _original
            def _translated(*args, __fn=_original, __name=_component, **kwargs):
                if st.session_state.get("dil", "Türkçe") == "Türkçe":
                    return __fn(*args, **kwargs)
                if args:
                    first = args[0]
                    if isinstance(first, str):
                        args = (_tr(first),) + args[1:]
                    elif isinstance(first, (list,tuple)) and __name in ("tabs",):
                        args = ([_tr(x) for x in first],) + args[1:]
                    elif __name in ("dataframe", "table", "bar_chart"):
                        args = (translate_structure(first, ss.get("dil", "Türkçe")),) + args[1:]
                for _key in ("label","help","placeholder","text"):
                    if isinstance(kwargs.get(_key), str):
                        kwargs[_key] = _tr(kwargs[_key])
                if __name in ("selectbox","radio") and len(args) > 1 and isinstance(args[1], (list,tuple)):
                    _onceki_format = kwargs.get("format_func", str)
                    kwargs["format_func"] = lambda value, _f=_onceki_format: _tr(str(_f(value)))
                return __fn(*args, **kwargs)
            setattr(st, _component, _translated)
        st._guvenli_okul_originals = _originals
        st._guvenli_okul_i18n_wrapped = True
    _logo = _logo_veri_adresi()
    if _logo:
        st.markdown(f"<div class='sb-logo'><img src='{_logo}' alt='Bozüyük Fen Lisesi logosu'></div>",
                    unsafe_allow_html=True)
    st.markdown("<div class='top-brand'><div><div class='top-brand-name'>Bozüyük Fen Lisesi"
                "</div><div class='top-brand-sub'>Güvenli Okul · Bildirim ve takip</div></div></div>", unsafe_allow_html=True)
    for baslik, ogeler in NAV:
        st.markdown(f"<div class='nav-title'>{_tr(baslik)}</div>", unsafe_allow_html=True)
        for ad, ikon in ogeler:
            kilit = ad in KORUMALI and not ss.yonetici_giris
            st.button(_tr(ad), key=f"nav_{ad}", icon=":material/lock:" if kilit else f":material/{ikon}:",
                      type="primary" if ad == secili_sayfa else "secondary", on_click=sayfaya_git, args=(ad,))
    st.markdown(f"<div class='nav-title'>{_tr('OTURUM')}</div>", unsafe_allow_html=True)
    if ss.yonetici_giris:
        st.caption(f"Yönetici: {ss.yonetici_adi}")
        st.button("Oturumu kapat", on_click=oturumu_kapat, key="oturum_kapat", icon=":material/logout:")
    else:
        st.caption("Ziyaretçi (giriş yapılmadı)")
    st.caption(_tr("Acil:") + " " + " · ".join(n for n, _ in ACIL_HATLAR))
    st.caption(f"Sürüm 3.1 · Algılayıcı {ht.SURUM}")

st.markdown(
    f"<div class='topbar'><div class='crumb'>Güvenli Okul <span>/</span> <b>{html.escape(_tr(secili_sayfa))}</b></div>"
    f"<div class='pills'>{pill('DEMO' if DEMO_MODU else 'PİLOT', 'prio-mid')}"
    f"{pill('Yönetici' if ss.yonetici_giris else 'Ziyaretçi', 'status-active' if ss.yonetici_giris else 'prio-none')}</div></div>",
    unsafe_allow_html=True)
if DEMO_MODU:
    st.markdown("<div class='notice-bar'><span class='notice-dot'></span><span>Bağımsız çalışma alanı · Gerçek okul "
                "sistemine bağlı değildir. Gerçek kişisel verileri girmeyin.</span></div>", unsafe_allow_html=True)
flash_goster()

SAYFALAR[secili_sayfa]()
if secili_sayfa in ("Genel bakış", "Yeni bildirim", "Bildirim sorgula", "Yönetici girişi",
                    "İstatistikler", "Araştırma ve test"):
    altbilgi()
