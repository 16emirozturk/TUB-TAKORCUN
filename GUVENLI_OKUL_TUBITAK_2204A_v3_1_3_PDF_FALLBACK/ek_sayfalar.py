"""Ek sayfalar (v2.2): Destek rehberi (B), Trend ve ortam analizi (D), Gizlilik ve KVKK paneli (E).

Metinler TASLAKTIR; yayımlanmadan önce okul psikolojik danışmanı (içerik) ve hukuk danışmanı (KVKK)
tarafından incelenmelidir.
"""
from __future__ import annotations

import html

import streamlit as st

import db
from sabitler import ACIL_HATLAR, OLAY_TURLERI, ORTAMLAR

ss = st.session_state


def _acil() -> None:
    from i18n import translate as _tr
    parca = " · ".join(f"<b>{html.escape(n)}</b> {html.escape(_tr(a))}" for n, a in ACIL_HATLAR)
    st.markdown(f"<div class='emergency'>{html.escape(_tr('Acil bir tehlike varsa beklemeyin:'))} {parca}</div>", unsafe_allow_html=True)


def _baslik(ust: str, baslik: str, aciklama: str) -> None:
    from i18n import translate as _tr
    st.markdown(f"<div class='page-heading'><div class='eyebrow-dark'>{html.escape(_tr(ust))}</div>"
                f"<h1>{html.escape(_tr(baslik))}</h1><p>{html.escape(_tr(aciklama))}</p></div>", unsafe_allow_html=True)


# ============================================================ B) DESTEK REHBERİ
ICERIK = {
    "Öğrenciler": (
        ("Zorbalık nedir, ne değildir?",
         ("Zorbalık; bilerek yapılan, tekrar eden ve güç dengesizliği olan davranıştır (alay, tehdit, dışlama, fiziksel "
          "saldırı, internette aşağılama).",
          "Arkadaşlar arasındaki tek seferlik tartışma genellikle zorbalık sayılmaz; ama seni korkutuyor ya da "
          "üzüyorsa yine de anlatmaya değer.",
          "Olanlar senin suçun değildir.")),
        ("Yaşıyorsan ne yapabilirsin?",
         ("Güvendiğin bir yetişkine (rehber öğretmen, sınıf öğretmeni, aile) olanı anlat.",
          "Cevap vermek zorunda değilsin; güvenli bir yere git, yanında birileriyle ol.",
          "Mesaj ve ekran görüntülerini sakla, silme; yetişkine gösterirsin.",
          "Bu sitedeki anonim formu kullanabilirsin; ama form acil durum hattı değildir.")),
        ("Kendine zarar verme düşüncen varsa",
         ("Bu düşünceleri tek başına taşımak zorunda değilsin. Hemen güvendiğin bir yetişkine söyle.",
          "Acil tehlikede 112'yi, destek için 183'ü arayabilirsin.")),
    ),
    "Tanık olanlar": (
        ("Gördüysen sessiz kalma",
         ("Zorbalığa gülmek ya da paylaşmak onu büyütür. Katılmamak bile bir destektir.",
          "Güvenliysen mağdurun yanına git, yalnız olmadığını hissettir.",
          "Müdahale etmek tehlikeliyse bir yetişkine haber ver. Bu ‘çaksıl’ değil, arkadaşını korumaktır.",
          "Anonim form ile adını vermeden bildirebilirsin.")),
    ),
    "Siber zorbalık": (
        ("İnternette aşağılanıyor ya da tehdit ediliyorsan",
         ("Cevap verme, kişiyi engelle, platformda şikâyet et.",
          "Kanıtları (ekran görüntüsü, tarih, hesap adı) sakla.",
          "Özel fotoğrafın izinsiz paylaşılıyorsa ya da paylaşılmakla tehdit ediliyorsan hemen bir yetişkine söyle; "
          "bu ciddi bir durumdur ve suç oluşturabilir.",
          "Şifrelerini kimseyle paylaşma, gizlilik ayarlarını gözden geçir.")),
    ),
    "Veliler": (
        ("Çocuğunuz zorbalığa uğruyor olabilir",
         ("Sık görülen işaretler: okula gitmek istememe, uyku/iştah değişikliği, eşya kaybı, çekingenlik, "
          "telefona karşı aşırı tedirginlik. Bunlar tek başına kanıt değildir.",
          "Önce sakin kalın, dinleyin; suçlamayın, ‘sen de karşılık ver’ demeyin.",
          "Olayı tarih ve ayrıntılarıyla yazın; okul rehberlik servisiyle görüşün.",
          "Çocuğunuzun kendine zarar verme düşüncesi olabileceğinden endişeleniyorsanız 112'yi arayın.")),
        ("Çocuğunuzun zorbalık yaptığı söyleniyorsa",
         ("Savunmaya geçmeden dinleyin; davranışın başkasına verdiği zararı konuşun.",
          "Okul rehberlik servisiyle birlikte çalışın; cezadan çok davranış değişikliğini hedefleyin.")),
    ),
    "Öğretmenler": (
        ("Bildirim geldiğinde",
         ("Kaydı yalnızca insan olarak değerlendirin; otomatik sinyal kanıt veya karar değildir.",
          "Kaynağı belirlemeye çalışmayın; bildirimin anonimliğini koruyun.",
          "Şüpheli öğrencinin yanlış suçlanma riskini gözetin; süreci rehberlik servisi ve okul yönetimiyle yürütün.",
          "Acil sinyal veya doğrudan zarar riski varsa okulun acil durum protokolünü uygulayın.")),
    ),
}

AKIS = ("Formu gönderirsin ve gizli takip kodunu alırsın.",
        "Kayıt, yetkili kişiler (rehberlik / okul yönetimi) tarafından incelenir; bunu bir insan yapar.",
        "Takip koduyla durumu görürsün. Sistemde mesajlaşma yoktur; bu yüzden acil durumlarda bir yetişkine ulaş.")


def destek() -> None:
    _baslik("DESTEK", "Destek rehberi",
            "Zorbalıkla baş etme yolları ve kime nasıl ulaşabileceğin. Bu içerik bilgilendirme amaçlıdır.")
    _acil()
    sekmeler = st.tabs(list(ICERIK) + ["Bildirimden sonra ne olur?"])
    for sekme, (ad, bolumler) in zip(sekmeler, ICERIK.items()):
        with sekme:
            for baslik, maddeler in bolumler:
                with st.expander(baslik, expanded=baslik == bolumler[0][0]):
                    st.markdown("\n".join(f"- {m}" for m in maddeler))
    with sekmeler[-1]:
        st.markdown("\n".join(f"{i}. {a}" for i, a in enumerate(AKIS, 1)))
        st.caption("Rehberlik içerikleri taslaktır; okul psikolojik danışmanı tarafından onaylanmalıdır.")


# ======================================================= D) TREND VE ORTAM ANALİZİ
def _isi_tablosu(matris: dict, satirlar: list[str], sutunlar: list[str]) -> str:
    """Ortam × olay türü ısı tablosu (bağımlılıksız HTML). Gizlenen hücreler '·' ile gösterilir."""
    from i18n import translate as _tr
    en_buyuk = max(matris.values(), default=1)
    bas = "".join(f"<th style='padding:.4rem;font-size:.75rem'>{html.escape(_tr(c))}</th>" for c in sutunlar)
    govde = []
    for r in satirlar:
        hucre = []
        for c in sutunlar:
            v = matris.get((r, c))
            if v is None:
                hucre.append("<td style='text-align:center;color:#9aa8b8'>·</td>")
            else:
                a = 0.15 + 0.75 * v / en_buyuk
                hucre.append(f"<td style='text-align:center;font-weight:700;background:rgba(49,95,150,{a:.2f});"
                             f"color:{'#fff' if a > .55 else '#1d2b3d'}'>{v}</td>")
        govde.append(f"<tr><th style='text-align:left;padding:.4rem;font-size:.8rem'>{html.escape(_tr(r))}</th>"
                     + "".join(hucre) + "</tr>")
    return ("<div style='overflow-x:auto'><table style='border-collapse:collapse;width:100%'>"
            f"<tr><th></th>{bas}</tr>{''.join(govde)}</table></div>")


def trend() -> None:
    _baslik("ANALİTİK", "Trend ve ortam analizi",
            "Bildirimlerin saat, gün, mekân ve türlere göre dağılımı. Yalnızca bu uygulamadaki kayıtları özetler.")
    c1, c2 = st.columns(2)
    gun = c1.selectbox("Dönem", [30, 90, 180, 365], index=1, format_func=lambda g: f"Son {g} gün", key="trend_gun")
    k = c2.number_input("Küçük hücre eşiği (k)", min_value=3, max_value=20, value=5, key="trend_k",
                        help="Çapraz tabloda sayısı bu değerden küçük hücreler kimliksizleştirme için gizlenir.")
    o = db.trend_ozeti(int(gun), int(k))
    if not o["toplam"]:
        st.info("Bu dönemde kayıt yok.")
        return
    if o["toplam"] < 20:
        st.warning(f"Yalnızca {o['toplam']} kayıt var; yüzdeler ve eğilimler yanıltıcı olabilir, yorum yapmayın.")
    m = st.columns(3)
    m[0].metric("Kayıt sayısı", o["toplam"])
    en_cok_ortam = next(iter(o["ortam"]), "—")
    from i18n import translate as _tr
    m[1].metric("En çok bildirilen ortam", _tr(en_cok_ortam))
    m[2].metric("En çok bildirilen tür", _tr(next(iter(o["tur"]), "—")))

    st.subheader("Ne zaman bildiriliyor?")
    a, b = st.columns(2, gap="large")
    with a:
        st.caption("Saate göre (bildirimin yapıldığı saat)")
        st.bar_chart({f"{h:02d}": v for h, v in o["saat"].items()})
    with b:
        st.caption("Haftanın gününe göre")
        st.bar_chart(o["haftanin_gunu"])
    st.subheader("Haftalık eğilim")
    st.bar_chart(o["hafta"])
    st.caption("Bildirim sayısındaki artış, olayların arttığını değil bildirme isteğinin arttığını da gösterebilir; "
               "ayrım için ayrı bir ölçüm (ör. anket) gerekir. Saat, olayın değil bildirimin saatidir; "
               "anonim kayıtlarda zaman dakika ve saniye hassasiyetinde kaydedilir.")

    st.subheader("Hangi ortamda, hangi tür?")
    d1, d2 = st.columns(2, gap="large")
    with d1:
        st.caption("Ortama göre")
        st.bar_chart(o["ortam"], horizontal=True)
    with d2:
        st.caption("Olay türüne göre")
        st.bar_chart(o["tur"], horizontal=True)
    st.markdown("**Ortam haritası (ısı tablosu)**")
    st.markdown(_isi_tablosu(o["matris"], ORTAMLAR, [t for t in OLAY_TURLERI]), unsafe_allow_html=True)
    if o["gizlenen_hucre"]:
        st.caption(f"‘·’ ile gösterilen {o['gizlenen_hucre']} hücre (toplam {o['gizlenen_kayit']} kayıt) "
                   f"{int(k)}'den az olduğu için gizlendi.")


# ================================================ E) GİZLİLİK, KVKK VE ONAM PANELİ
AYDINLATMA = """\
**Veri sorumlusu:** [OKUL ADI / KURUM] · **İletişim:** [KVKK İLETİŞİM ADRESİ]

**İşlenen veriler:** Bildirim formunda yazdığınız olay bilgisi (tür, ortam, zaman, açıklama). Ad, soyad, sınıf,
telefon istenmez. Açıklamadaki telefon, T.C. kimlik no, e-posta ve IBAN otomatik maskelenir.

**Amaç:** Akran zorbalığı bildirimlerinin yetkili kişilerce incelenmesi ve öğrencinin korunması. Veriler başka
amaçla kullanılmaz. Otomatik sinyal yalnızca inceleme sırasına yardımcıdır; hiçbir karar otomatik verilmez.

**Hukuki sebep:** [HUKUK DANIŞMANI BELİRLEYECEK: ör. KVKK m.5/2 ilgili bendi / açık rıza / veli onamı]

**Aktarım:** Veriler yetkili okul personeli dışında paylaşılmaz. [BARINDIRMA YERİ VE YURT DIŞI AKTARIM DURUMU YAZILACAK]

**Saklama ve imha:** Bu demo sürümünde bildirimler, inceleme notları, ek bilgiler, önleyici çalışmalar ve denetim geçmişi için 180/360 gün sonunda otomatik silme uygulanmaz. Veriler süre dolduğu için silinmez. Gerçek okul kullanımından önce veri sorumlusu, hukuk danışmanı ve okul yönetimi tarafından mevzuata uygun saklama-imha politikası ayrıca belirlenmelidir.

**Haklarınız:** KVKK m.11 kapsamındaki haklar için yukarıdaki adrese başvurabilirsiniz. Anonim bildirimlerde bildirimi
size bağlamak mümkün olmadığından bazı haklar (erişim, düzeltme) teknik olarak kullanılamayabilir.
"""

ENVANTER = (
    ("Olay açıklaması (maskelenmiş)", "Bildirimi incelemek", "Bildirim gönderildiğinde", "Süre dolumuyla otomatik silinmez (demo politikası)",
     "Serbest metin; üçüncü kişilerin adı geçebilir, maskeleme adları yakalamaz."),
    ("Olay türü, ortam, zaman, tekrar", "İstatistik ve önceliklendirme", "Bildirim gönderildiğinde", "Süre dolumuyla otomatik silinmez (demo politikası)",
     "Seçmeli alanlar."),
    ("Takip kodu", "Durum sorgulama, ek bilgi", "Bildirim gönderildiğinde", "Kayıtla birlikte",
     "Rastgele; kimlikle ilişkisiz."),
    ("Cihaz jetonu özeti (SHA-256)", "Günlük bildirim hakkı", "Bildirim gönderildiğinde", "Otomatik süreli silme yok",
     "Rapora bağlanmaz."),
    ("Ek bilgiler", "Aynı bildirimi tamamlamak", "Takip koduyla, aynı gün", "Kayıtla birlikte", "En çok 3 ek."),
    ("Öncelik sinyali / kategoriler", "İnceleme sırası", "Kayıt anında (otomatik)", "Kayıtla birlikte",
     "Kural tabanlı; karar değildir."),
    ("İnceleme notları, işlem geçmişi", "Hesap verebilirlik", "Yönetici işlemlerinde", "Kayıtla birlikte",
     "Kim yaptı bilgisi içerir."),
    ("Denetim kaydı, giriş denemeleri", "Güvenlik", "Yönetici girişlerinde", "Otomatik süreli silme yok",
     "Denetim kaydı için saklama süresi karar verilmeli."),
    ("Ad, soyad, sınıf (yalnızca eski kayıtlar)", "—", "Formda artık istenmiyor", "Eski kayıtlarla birlikte",
     "Eski kimlikli kayıtlar varsa erişim kısıtlanmalı ve yetkili kişilerce gözden geçirilmelidir."),
)

ONAM_TASLAK = """\
GÖNÜLLÜ KATILIM VE VELİ ONAM FORMU (TASLAK)

Proje: Güvenli Okul — Akran Zorbalığı Bildirim ve Takip Platformu
Okul: [OKUL ADI]   Danışman öğretmen: [AD SOYAD]

1. Amaç: Bildirim sisteminin kullanılabilirliğini ve kural tabanlı sinyalin başarımını değerlendirmek.
2. Katılım gönüllüdür; istediğiniz zaman, gerekçe göstermeden ayrılabilirsiniz.
3. Toplanan veri: Formdaki olay bilgisi (ad, soyad, telefon toplanmaz). Gerçek kişileri tanıtan bilgi yazmayınız.
4. Saklama: [SÜRE]. Veriler yalnızca araştırma ekibi ve yetkili okul personelince görülür.
5. Riskler: Zorbalık konusu bazı öğrencileri üzebilir; bu durumda rehberlik servisine başvurabilirsiniz.

Öğrenci: Bilgilendirildim, gönüllü katılıyorum.        Tarih: ____  İmza: ________
Veli/Yasal temsilci: Bilgilendirildim, çocuğumun katılımına izin veriyorum.   Tarih: ____  İmza: ________
"""


def _onam_ileri() -> None:
    ss["onam_adim"] = min(ss.get("onam_adim", 1) + 1, 4)


def _onam_sifirla() -> None:
    for k in ("onam_adim", "onam_yas", "onam_ogrenci", "onam_veli"):
        ss.pop(k, None)


def _onam_simulasyonu() -> None:
    st.info("SİMÜLASYON: Bu akış gerçek onam toplamaz, hiçbir veri kaydetmez ve kimseyle iletişime geçmez. "
            "Araştırmada onam, okulun resmî kanallarıyla yazılı olarak alınmalıdır.")
    adim = ss.setdefault("onam_adim", 1)
    st.progress(adim / 4, text=f"Adım {adim}/4")
    if adim == 1:
        ss.setdefault("onam_yas", "18 yaşından küçük")
        st.radio("Katılımcının yaş grubu", ["18 yaşından küçük", "18 yaş ve üzeri"], key="onam_yas")
        st.caption("18 yaşından küçüklerde gönüllü katılımın yanında veli/yasal temsilcinin bilgilendirilmesi ve izni gerekir.")
        st.button("İleri", on_click=_onam_ileri, key="onam_i1", type="primary")
    elif adim == 2:
        st.markdown("**Katılımcı bilgilendirmesi:** amaç, gönüllülük, toplanan veri (ad/telefon yok), saklama süresi, "
                    "ayrılma hakkı ve rehberlik desteği.")
        ok = st.checkbox("Bilgilendirmeyi okudum, gönüllü katılıyorum (simülasyon).", key="onam_ogrenci")
        st.button("İleri", on_click=_onam_ileri, key="onam_i2", type="primary", disabled=not ok)
    elif adim == 3:
        if ss.get("onam_yas") == "18 yaşından küçük":
            st.markdown("**Veli/yasal temsilci bilgilendirmesi ve izni.** Gerçek sistemde bu adım, okulun resmî "
                        "iletişim kanalıyla ve yazılı olarak yürütülür; bu uygulama veli iletişim bilgisi toplamaz.")
            ok = st.checkbox("Veli/yasal temsilci izin verdi (simülasyon).", key="onam_veli")
        else:
            st.markdown("18 yaş ve üzeri katılımcı için veli izni gerekmez; kendi gönüllü onamı yeterlidir.")
            ok = True
        st.button("İleri", on_click=_onam_ileri, key="onam_i3", type="primary", disabled=not ok)
    else:
        st.success("Simülasyon tamamlandı: katılım koşulları sağlandı.")
        st.markdown("Bu aşamadan sonra katılımcı bildirim formunu kullanabilir. Katılımcıdan **ad, sınıf, telefon "
                    "istenmez**; onay kaydı bu uygulamada tutulmaz, okulda yazılı saklanır.")
        st.button("Baştan başla", on_click=_onam_sifirla, key="onam_reset")
    from i18n import translate as _tr
    dil = ss.get("dil", "Türkçe")
    dosya_adlari = {
        "Türkçe": "onam_formu_taslak.txt",
        "English": "consent_form_draft.txt",
        "Deutsch": "einwilligungsformular_entwurf.txt",
        "Français": "formulaire_consentement_projet.txt",
        "Español": "formulario_consentimiento_borrador.txt",
        "العربية": "نموذج_الموافقة_مسودة.txt",
        "Azərbaycan dili": "raziliq_formasi_layihe.txt",
    }
    st.download_button("Gönüllü katılım ve veli onam formu taslağı (.txt)", _tr(ONAM_TASLAK),
                       file_name=dosya_adlari.get(dil, "onam_formu_taslak.txt"), mime="text/plain")


def kvkk(yonetici: bool) -> None:
    _baslik("GİZLİLİK", "Gizlilik ve KVKK paneli",
            "Hangi verinin neden toplandığını ve demo sürümündeki saklama yaklaşımını açıklar. Metinler taslaktır.")
    s1, s2, s3, s4 = st.tabs(["Aydınlatma metni", "Veri envanteri", "Saklama politikası", "Onam akışı (simülasyon)"])
    with s1:
        st.markdown(AYDINLATMA)
        st.warning("Köşeli parantezli alanlar doldurulmadan ve hukuk danışmanı onaylamadan yayımlanmamalıdır.")
    with s2:
        st.dataframe([dict(zip(("Veri", "Amaç", "Ne zaman", "Saklama", "Not"), r)) for r in ENVANTER],
                     hide_index=True)
        st.markdown("**Veri minimizasyonu (sistemde uygulananlar)**")
        st.markdown("- Formda ad, sınıf, telefon istenmez.\n"
                    "- Açıklamadaki T.C. no, telefon, e-posta, IBAN maskelenir; ham metin saklanmaz.\n"
                    "- Anonim kayıt ve ek bilgi zamanı dakika ve saniye hassasiyetinde kaydedilir.\n"
                    "- Cihaz jetonu yalnızca özet olarak ve 1 gün saklanır; rapora bağlanmaz.\n"
                    "- Öğrenci sorgusunda açıklama, not ve değerlendirme gösterilmez.")
        st.markdown("**Açık riskler (raporda belirtilmeli)**")
        st.markdown("- Serbest metin kişileri dolaylı tanıtabilir; ‘tam anonim’ yerine ‘kimliksizleştirilmiş’ "
                    "demek daha doğrudur.\n"
                    "- Üçüncü kişilerin (şüpheli öğrenci) adı metinde geçebilir; maskeleme adları yakalamaz.\n"
                    "- Barındırma yeri ve olası yurt dışı aktarım hukuken değerlendirilmelidir.")
    with s3:
        st.markdown("**Veri saklama politikası**")
        st.success("Bu sürümde bildirimler, ek bilgiler, inceleme notları, önleyici çalışma kayıtları ve denetim günlüğü 180/360 gün gibi bir süre sonunda otomatik silinmez.")
        st.markdown("- Otomatik veri temizliği ve süreye bağlı kayıt silme kapalıdır.\n- Kayıt silme düğmesi yönetim ekranından kaldırılmıştır.\n- Verileri korumak için düzenli SQLite yedeği alınmalıdır.\n- Bu demo ayarı, gerçek okulda mevzuata uygun saklama-imha yükümlülüklerinin yerine geçmez.")
    with s4:
        _onam_simulasyonu()
