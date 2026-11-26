"""Veri katmanı (SQLite). Streamlit'e bağımlı değildir; bağımsız test edilebilir.

v1'e göre düzeltmeler
- `with sqlite3.connect()` bağlantıyı KAPATMAZ (yalnızca commit/rollback yapar);
  burada bağlantı her zaman kapatılır.
- Saat dilimi Europe/Istanbul (bulut sunucuları UTC çalışır; v1 saatleri 3 saat kayıktı).
- Şema sürümü (PRAGMA user_version) ve eski veritabanını koruyan göç.
- v1'deki "ilk açılışta tüm kayıtları sil" mantığı kaldırıldı (veri kaybı riski).
- Takip kodu 32 bit yerine ~50 bit entropi, çakışmada yeniden deneme.
- Dizinler, WAL, işlem (aktör) ve denetim kaydı, giriş denemesi sayacı.

v2.1 (EK): tam anonim akış — cihaz jetonu özetiyle günlük kota, takip koduyla ek bilgi,
sunucu tarafı bekleme süresi. Mevcut işlevler değiştirilmedi; yalnızca dosya sonuna eklendi.
"""
from __future__ import annotations

import csv
import io
import os
import re
import hashlib
import math
import secrets
import sqlite3
import time
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import guvenlik
import hakaret_tespiti as ht
from sabitler import BIRIMLER, DURUMLAR, OLAY_TURLERI, ONCELIKLER

DB_YOLU = Path(os.environ.get("GUVENLI_OKUL_DB", Path(__file__).with_name("guvenli_okul_demo.db")))
TZ = ZoneInfo("Europe/Istanbul")
SEMA_SURUMU = 2
ANONIM_ZAMAN_YUVARLA = False  # doğru SLA ve olay sıralaması için dakika/saniye korunur
MAKS_NOT_UZUNLUGU = 1000
_KOD_ALFABESI = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # 0/O, 1/I/L karışmaz
_ZAMAN_BICIMI = "%Y-%m-%d %H:%M:%S"


# ------------------------------------------------------------------ yardımcılar
def simdi(saate_yuvarla: bool = False) -> str:
    t = datetime.now(TZ)
    if saate_yuvarla:
        t = t.replace(minute=0, second=0, microsecond=0)
    return t.strftime(_ZAMAN_BICIMI)


def _onceki(dakika: int) -> str:
    return (datetime.now(TZ) - timedelta(minutes=dakika)).strftime(_ZAMAN_BICIMI)


def _saat_farki(baslangic: str, bitis: str) -> float:
    return (datetime.strptime(bitis, _ZAMAN_BICIMI) - datetime.strptime(baslangic, _ZAMAN_BICIMI)).total_seconds() / 3600


def gecen_saat(zaman: str) -> float:
    """Verilen zaman damgasından bu yana geçen saat."""
    return max(0.0, _saat_farki(zaman, simdi()))


@contextmanager
def baglanti():
    conn = sqlite3.connect(DB_YOLU, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def takip_kodu_uret() -> str:
    return "GO-" + "".join(secrets.choice(_KOD_ALFABESI) for _ in range(10))


def takip_kodu_normalle(girdi: str) -> str | None:
    kod = re.sub(r"\s+", "", (girdi or "")).upper()
    return kod if re.fullmatch(r"GO-[A-Z0-9]{8,10}", kod) else None


# ------------------------------------------------------------------------ şema
_EK_SUTUNLAR = {
    "bildirimler": (
        ("anonim", "INTEGER NOT NULL DEFAULT 1"),
        ("ad", "TEXT NOT NULL DEFAULT ''"),
        ("soyad", "TEXT NOT NULL DEFAULT ''"),
        ("sinif", "TEXT NOT NULL DEFAULT ''"),
        ("birim", "TEXT NOT NULL DEFAULT 'Henüz atanmadı'"),
        ("son_guncelleme", "TEXT NOT NULL DEFAULT ''"),
        ("oncelik", "TEXT NOT NULL DEFAULT 'Sinyal yok'"),
        ("kategoriler", "TEXT NOT NULL DEFAULT ''"),
        ("baglam_uyarilari", "TEXT NOT NULL DEFAULT ''"),
        ("maskelenen", "TEXT NOT NULL DEFAULT ''"),
        ("analiz_surumu", "TEXT NOT NULL DEFAULT ''"),
    ),
    "inceleme_notlari": (("yazar", "TEXT NOT NULL DEFAULT ''"),),
    "islem_gecmisi": (("aktor", "TEXT NOT NULL DEFAULT ''"),),
}


def hazirla() -> None:
    """Tabloları oluşturur, eksik sütunları ekler; mevcut veriyi silmez."""
    with baglanti() as conn:
        mevcut_surum = conn.execute("PRAGMA user_version").fetchone()[0]
        if mevcut_surum > SEMA_SURUMU:
            raise RuntimeError("Veritabanı bu uygulamadan daha yeni bir şema sürümüne sahip.")
        conn.execute("PRAGMA journal_mode = WAL")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS bildirimler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                takip_no TEXT UNIQUE NOT NULL,
                olusturma_zamani TEXT NOT NULL,
                olay_turu TEXT NOT NULL,
                ortam TEXT NOT NULL,
                zaman_bilgisi TEXT NOT NULL,
                tekrar_durumu TEXT NOT NULL,
                aciklama TEXT NOT NULL,
                eslesmeler TEXT NOT NULL,
                durum TEXT NOT NULL DEFAULT 'İnceleme bekliyor',
                demo INTEGER NOT NULL DEFAULT 1
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inceleme_notlari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                takip_no TEXT NOT NULL REFERENCES bildirimler(takip_no),
                zaman TEXT NOT NULL,
                not_metni TEXT NOT NULL
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS islem_gecmisi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                takip_no TEXT NOT NULL REFERENCES bildirimler(takip_no),
                zaman TEXT NOT NULL,
                islem TEXT NOT NULL,
                ayrinti TEXT NOT NULL DEFAULT ''
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS giris_denemeleri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zaman TEXT NOT NULL,
                basarili INTEGER NOT NULL
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS onleyici_calismalar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                baslik TEXT NOT NULL,
                aciklama TEXT NOT NULL DEFAULT '',
                konu TEXT NOT NULL DEFAULT 'Genel',
                hedef_ortam TEXT NOT NULL DEFAULT 'Tümü',
                sorumlu_kisi TEXT NOT NULL,
                sorumlu_birim TEXT NOT NULL DEFAULT '',
                planlanan_tarih TEXT NOT NULL,
                tamamlanma_tarihi TEXT NOT NULL DEFAULT '',
                durum TEXT NOT NULL DEFAULT 'Planlandı',
                olusturan TEXT NOT NULL DEFAULT '',
                olusturma_zamani TEXT NOT NULL,
                guncelleme_zamani TEXT NOT NULL
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS onleyici_calisma_gecmisi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                calisma_id INTEGER NOT NULL REFERENCES onleyici_calismalar(id) ON DELETE CASCADE,
                zaman TEXT NOT NULL,
                aktor TEXT NOT NULL DEFAULT '',
                islem TEXT NOT NULL,
                ayrinti TEXT NOT NULL DEFAULT ''
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS denetim_kaydi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zaman TEXT NOT NULL,
                aktor TEXT NOT NULL,
                islem TEXT NOT NULL,
                ayrinti TEXT NOT NULL DEFAULT ''
            )""")

        for tablo, sutunlar in _EK_SUTUNLAR.items():
            var = {r["name"] for r in conn.execute(f"PRAGMA table_info({tablo})")}
            for ad, tanim in sutunlar:  # tablo/sütun adları yukarıdaki sabitlerden gelir
                if ad not in var:
                    conn.execute(f"ALTER TABLE {tablo} ADD COLUMN {ad} {tanim}")

        for ad, ifade in (
            ("ix_notlar_takip", "inceleme_notlari(takip_no)"),
            ("ix_gecmis_takip", "islem_gecmisi(takip_no)"),
            ("ix_bildirim_durum", "bildirimler(durum)"),
            ("ix_bildirim_zaman", "bildirimler(olusturma_zamani)"),
            ("ix_giris_zaman", "giris_denemeleri(zaman)"),
            ("ix_onleyici_durum", "onleyici_calismalar(durum, planlanan_tarih)"),
            ("ix_onleyici_gecmis", "onleyici_calisma_gecmisi(calisma_id, zaman)"),
        ):
            conn.execute(f"CREATE INDEX IF NOT EXISTS {ad} ON {ifade}")

        conn.execute(f"PRAGMA user_version = {SEMA_SURUMU}")


# ----------------------------------------------------------- yazma işlemleri
def _islem(conn, takip_no, islem, ayrinti="", aktor="", zaman=None):
    conn.execute(
        "INSERT INTO islem_gecmisi (takip_no, zaman, islem, ayrinti, aktor) VALUES (?, ?, ?, ?, ?)",
        (takip_no, zaman or simdi(), islem, ayrinti, aktor),
    )


def bildirim_ekle(*, olay_turu, ortam, zaman_bilgisi, tekrar_durumu, aciklama,
                  anonim, ad="", soyad="", sinif="", demo=True) -> dict:
    """Bildirimi kaydeder. Dönüş: {takip_no, analiz, maskelenen}."""
    analiz = ht.analiz_et(aciklama)
    maskeli, maskelenen = guvenlik.hassas_veri_maskele(aciklama)
    if anonim:  # anonim bildirimlerde kimlik alanları hiç yazılmaz
        ad = soyad = sinif = ""
    zaman = simdi(saate_yuvarla=bool(anonim) and ANONIM_ZAMAN_YUVARLA)
    eslesme_metni = ", ".join(analiz.ifadeler) if analiz.ifadeler else "Belirgin eşleşme yok"

    for _ in range(5):
        takip_no = takip_kodu_uret()
        try:
            with baglanti() as conn:
                conn.execute(
                    """INSERT INTO bildirimler (
                        takip_no, olusturma_zamani, olay_turu, ortam, zaman_bilgisi, tekrar_durumu,
                        aciklama, eslesmeler, durum, demo, anonim, ad, soyad, sinif, birim,
                        son_guncelleme, oncelik, kategoriler, baglam_uyarilari, maskelenen, analiz_surumu)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (takip_no, zaman, olay_turu, ortam, zaman_bilgisi, tekrar_durumu,
                     maskeli, eslesme_metni, "İnceleme bekliyor", int(demo), int(bool(anonim)),
                     ad, soyad, sinif, "Henüz atanmadı", zaman, analiz.oncelik,
                     ", ".join(analiz.kategoriler), " | ".join(analiz.baglam_uyarilari),
                     ", ".join(maskelenen), analiz.surum),
                )
                _islem(conn, takip_no, "Yeni bildirim oluşturuldu", aktor="Bildirim formu", zaman=zaman)
            return {"takip_no": takip_no, "analiz": analiz, "maskelenen": maskelenen}
        except sqlite3.IntegrityError as e:
            if "takip_no" not in str(e):
                raise
    raise RuntimeError("Benzersiz takip kodu üretilemedi.")


def durum_ve_birim_guncelle(takip_no: str, yeni_durum: str, yeni_birim: str, aktor: str) -> list[str]:
    """Değişiklik yoksa hiçbir şey yazmaz. Dönüş: yapılan değişikliklerin listesi."""
    if yeni_durum not in DURUMLAR or yeni_birim not in BIRIMLER:
        raise ValueError("Geçersiz durum veya birim.")
    degisiklikler: list[str] = []
    with baglanti() as conn:
        eski = conn.execute("SELECT durum, birim FROM bildirimler WHERE takip_no = ?", (takip_no,)).fetchone()
        if eski is None:
            raise LookupError("Kayıt bulunamadı.")
        if eski["durum"] != yeni_durum:
            _islem(conn, takip_no, "Durum değiştirildi", f"{eski['durum']} → {yeni_durum}", aktor)
            degisiklikler.append("durum")
        if eski["birim"] != yeni_birim:
            _islem(conn, takip_no, "Birim ataması değiştirildi", f"{eski['birim']} → {yeni_birim}", aktor)
            degisiklikler.append("birim")
        if degisiklikler:
            conn.execute(
                "UPDATE bildirimler SET durum = ?, birim = ?, son_guncelleme = ? WHERE takip_no = ?",
                (yeni_durum, yeni_birim, simdi(), takip_no),
            )
    return degisiklikler


def not_ekle(takip_no: str, metin: str, yazar: str) -> None:
    metin = (metin or "").strip()
    if not metin or len(metin) > MAKS_NOT_UZUNLUGU:
        raise ValueError("Not boş olamaz ve en fazla 1000 karakter olabilir.")
    with baglanti() as conn:
        if conn.execute("SELECT 1 FROM bildirimler WHERE takip_no = ?", (takip_no,)).fetchone() is None:
            raise LookupError("Kayıt bulunamadı.")
        conn.execute(
            "INSERT INTO inceleme_notlari (takip_no, zaman, not_metni, yazar) VALUES (?, ?, ?, ?)",
            (takip_no, simdi(), metin, yazar),
        )
        _islem(conn, takip_no, "İnceleme notu eklendi", aktor=yazar)


# ------------------------------------------------------------ okuma işlemleri
def kayitlari_getir(limit: int = 5000) -> list[dict]:
    with baglanti() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM bildirimler ORDER BY id DESC LIMIT ?", (limit,))]


def notlari_getir(takip_no: str) -> list[dict]:
    with baglanti() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT zaman, not_metni, yazar FROM inceleme_notlari WHERE takip_no = ? ORDER BY id DESC", (takip_no,))]


def gecmisi_getir(takip_no: str) -> list[dict]:
    with baglanti() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT zaman, islem, ayrinti, aktor FROM islem_gecmisi WHERE takip_no = ? ORDER BY id DESC", (takip_no,))]


def takip_durumu_getir(girdi: str) -> dict | None:
    """Bildirimi yapan kişiye gösterilebilecek asgari bilgi (not, analiz, kimlik YOK)."""
    kod = takip_kodu_normalle(girdi)
    if not kod:
        return None
    with baglanti() as conn:
        r = conn.execute(
            "SELECT takip_no, durum, olusturma_zamani, son_guncelleme FROM bildirimler WHERE takip_no = ?", (kod,)
        ).fetchone()
    return dict(r) if r else None


# --------------------------------------------------------------- istatistik
def _sure_ozeti(saatler: list[float]) -> dict:
    if not saatler:
        return {"n": 0, "ortalama": None, "medyan": None}
    s = sorted(saatler)
    orta = len(s) // 2
    medyan = s[orta] if len(s) % 2 else (s[orta - 1] + s[orta]) / 2
    return {"n": len(s), "ortalama": sum(s) / len(s), "medyan": medyan}


def istatistik_ozeti(gun: int = 30) -> dict:
    with baglanti() as conn:
        toplam = conn.execute("SELECT COUNT(*) FROM bildirimler").fetchone()[0]
        durum = dict(conn.execute("SELECT durum, COUNT(*) FROM bildirimler GROUP BY durum").fetchall())
        tur = dict(conn.execute("SELECT olay_turu, COUNT(*) FROM bildirimler GROUP BY olay_turu").fetchall())
        oncelik = dict(conn.execute("SELECT oncelik, COUNT(*) FROM bildirimler GROUP BY oncelik").fetchall())
        anonim = conn.execute("SELECT COALESCE(SUM(anonim),0) FROM bildirimler").fetchone()[0]
        esik = (datetime.now(TZ) - timedelta(days=gun)).strftime("%Y-%m-%d")
        gunluk = [(r[0], r[1]) for r in conn.execute(
            "SELECT substr(olusturma_zamani,1,10) g, COUNT(*) FROM bildirimler "
            "WHERE substr(olusturma_zamani,1,10) >= ? GROUP BY g ORDER BY g", (esik,))]
        ilk = [_saat_farki(r[0], r[1]) for r in conn.execute(
            "SELECT b.olusturma_zamani, MIN(g.zaman) FROM bildirimler b "
            "JOIN islem_gecmisi g ON g.takip_no = b.takip_no AND g.islem = 'Durum değiştirildi' "
            "GROUP BY b.takip_no")]
        bitis = [_saat_farki(r[0], r[1]) for r in conn.execute(
            "SELECT b.olusturma_zamani, MIN(g.zaman) FROM bildirimler b "
            "JOIN islem_gecmisi g ON g.takip_no = b.takip_no AND g.ayrinti LIKE '% → Sonuçlandırıldı' "
            "GROUP BY b.takip_no")]
    return {
        "toplam": toplam,
        "durum": {d: durum.get(d, 0) for d in DURUMLAR},
        "tur": {t: tur.get(t, 0) for t in OLAY_TURLERI},
        "oncelik": {o: oncelik.get(o, 0) for o in ONCELIKLER},
        "anonim": anonim,
        "gunluk": gunluk,
        "ilk_inceleme_saat": _sure_ozeti(ilk),
        "sonuclanma_saat": _sure_ozeti(bitis),
    }


# ---------------------------------------------- güvenlik: giriş ve denetim kaydı
def giris_denemesi_kaydet(basarili: bool) -> None:
    with baglanti() as conn:
        conn.execute("INSERT INTO giris_denemeleri (zaman, basarili) VALUES (?, ?)", (simdi(), int(basarili)))


def basarisiz_giris_sayisi(dakika: int = 15) -> int:
    with baglanti() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM giris_denemeleri WHERE basarili = 0 AND zaman >= ?", (_onceki(dakika),)
        ).fetchone()[0]


def denetim_ekle(aktor: str, islem: str, ayrinti: str = "") -> None:
    with baglanti() as conn:
        conn.execute(
            "INSERT INTO denetim_kaydi (zaman, aktor, islem, ayrinti) VALUES (?, ?, ?, ?)",
            (simdi(), aktor, islem, ayrinti),
        )


def denetim_getir(limit: int = 300) -> list[dict]:
    with baglanti() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT zaman, aktor, islem, ayrinti FROM denetim_kaydi ORDER BY id DESC LIMIT ?", (limit,))]


# ------------------------------------------------- dışa aktarım ve veri saklama
_CSV_ALANLARI = ("takip_no", "olusturma_zamani", "son_guncelleme", "olay_turu", "ortam", "zaman_bilgisi",
                 "tekrar_durumu", "durum", "birim", "oncelik", "kategoriler", "anonim", "maskelenen", "aciklama")
_CSV_KIMLIK = ("ad", "soyad", "sinif")


def csv_aktar(kayitlar: list[dict], kimlik_dahil: bool = False) -> bytes:
    """Excel'de Türkçe karakterler için UTF-8 BOM'lu CSV; formül enjeksiyonuna karşı temizlenir."""
    alanlar = _CSV_ALANLARI + (_CSV_KIMLIK if kimlik_dahil else ())
    cikti = io.StringIO()
    yazici = csv.writer(cikti, delimiter=";")
    yazici.writerow(alanlar)
    for k in kayitlar:
        yazici.writerow([guvenlik.csv_hucre_temizle(k.get(a, "")) for a in alanlar])
    return cikti.getvalue().encode("utf-8-sig")


def sonuclanmis_kayitlari_sil(gun: int, aktor: str) -> int:
    """Güvenli Okul politikası: bildirimler otomatik/elle süre dolumu ile silinmez."""
    raise RuntimeError("Veri saklama politikası gereği kayıt silme devre dışıdır. Kayıtlar süre dolunca silinmez.")


# =====================================================================================
# v2.1 EK: TAM ANONİM AKIŞ (hesap, ad, telefon yok)
# - Günlük kota: tarayıcıdaki rastgele jetonun SHA-256 özeti + gün saklanır. Jeton kimlikle
#   ilişkili değildir ve rapora bağlanmaz. Kayıtlar otomatik temizlenmez.
# - Ek bilgi: takip koduyla, yalnızca bildirimin yapıldığı gün; bekleme süresi ve üst sınır
#   sunucuda (veritabanında) uygulanır, tarayıcıya güvenilmez.
# =====================================================================================
MAKS_EK_SAYISI = 3
EK_BEKLEME_SN = 60
MAKS_EK_UZUNLUGU = 1000


class AnonimHata(Exception):
    """Kullanıcıya gösterilebilir iş kuralı hatası. kod: kota | gecersiz_kod | gun_gecti |
    kapali | limit | bekle | bos | jeton."""

    def __init__(self, kod: str, mesaj: str, bekle_sn: int = 0):
        super().__init__(mesaj)
        self.kod, self.mesaj, self.bekle_sn = kod, mesaj, bekle_sn


def _bugun() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d")


def _jeton_ozeti(jeton: str) -> str:
    if not jeton or len(jeton) < 32:
        raise AnonimHata("jeton", "Cihaz jetonu geçersiz.")
    return hashlib.sha256(("gb1:" + jeton).encode("utf-8")).hexdigest()


def anonim_hazirla() -> None:
    """Yeni tabloları oluşturur (mevcut veriye dokunmaz)."""
    with baglanti() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS anonim_cihaz ("
                     "token_ozeti TEXT PRIMARY KEY, gun TEXT NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS ek_bilgiler ("
                     "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                     "takip_no TEXT NOT NULL REFERENCES bildirimler(takip_no), "
                     "zaman TEXT NOT NULL, metin TEXT NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS ek_kilit ("
                     "takip_no TEXT PRIMARY KEY REFERENCES bildirimler(takip_no), son_epoch REAL NOT NULL)")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_ek_takip ON ek_bilgiler(takip_no)")


def anonim_kota_dolu_mu(jeton: str) -> bool:
    """Bu cihaz bugün zaten bildirim gönderdiyse True."""
    ozet, bugun = _jeton_ozeti(jeton), _bugun()
    with baglanti() as conn:  # salt okunur: eski kayıtlar anonim_bildirim_ekle içinde temizlenir
        return conn.execute("SELECT 1 FROM anonim_cihaz WHERE token_ozeti = ? AND gun = ?",
                            (ozet, bugun)).fetchone() is not None


def anonim_bildirim_ekle(jeton: str, *, olay_turu, ortam, zaman_bilgisi, tekrar_durumu, aciklama, demo=True) -> dict:
    """Günlük hakkı atomik olarak ayırır, sonra bildirimi tam anonim kaydeder."""
    ozet, bugun = _jeton_ozeti(jeton), _bugun()
    with baglanti() as conn:
        try:
            conn.execute("INSERT INTO anonim_cihaz (token_ozeti, gun) VALUES (?, ?)", (ozet, bugun))
        except sqlite3.IntegrityError:
            raise AnonimHata("kota", "Günlük bildirim hakkınız dolmuştur.") from None
    try:
        return bildirim_ekle(olay_turu=olay_turu, ortam=ortam, zaman_bilgisi=zaman_bilgisi,
                             tekrar_durumu=tekrar_durumu, aciklama=aciklama, anonim=True, demo=demo)
    except BaseException:
        with baglanti() as conn:  # kayıt oluşmadıysa hak geri verilir
            conn.execute("DELETE FROM anonim_cihaz WHERE token_ozeti = ? AND gun = ?", (ozet, bugun))
        raise


def anonim_takip_ozeti(girdi: str) -> dict | None:
    """Durum + ek bilgi uygunluğu. Açıklama, not ve analiz içermez."""
    d = takip_durumu_getir(girdi)
    if not d:
        return None
    with baglanti() as conn:
        r = conn.execute("SELECT anonim, durum, olusturma_zamani FROM bildirimler WHERE takip_no = ?",
                         (d["takip_no"],)).fetchone()
        adet = conn.execute("SELECT COUNT(*) FROM ek_bilgiler WHERE takip_no = ?", (d["takip_no"],)).fetchone()[0]
        k = conn.execute("SELECT son_epoch FROM ek_kilit WHERE takip_no = ?", (d["takip_no"],)).fetchone()
    bekle = max(0, math.ceil(EK_BEKLEME_SN - (time.time() - k["son_epoch"]))) if k else 0
    d.update(
        ek_adet=adet,
        ek_kalan_hak=max(0, MAKS_EK_SAYISI - adet),
        bekle_sn=bekle,
        ek_uygun=bool(r["anonim"]) and r["olusturma_zamani"][:10] == _bugun() and r["durum"] != "Sonuçlandırıldı",
    )
    return d


def ek_bilgi_ekle(girdi: str, metin: str) -> dict:
    """Aynı gün, takip koduyla ek bilgi ekler. Kurallar sunucuda uygulanır."""
    metin = (metin or "").strip()
    if not metin or not any(c.isalnum() for c in metin):
        raise AnonimHata("bos", "Ek bilgi boş olamaz.")
    if len(metin) > MAKS_EK_UZUNLUGU:
        raise AnonimHata("bos", f"Ek bilgi en fazla {MAKS_EK_UZUNLUGU} karakter olabilir.")
    kod = takip_kodu_normalle(girdi)
    analiz = ht.analiz_et(metin)
    maskeli, maskelenen = guvenlik.hassas_veri_maskele(metin)
    with baglanti() as conn:
        conn.execute("BEGIN IMMEDIATE")  # yazma kilidi: eşzamanlı isteklerde sınır aşılamaz
        r = conn.execute("SELECT * FROM bildirimler WHERE takip_no = ?", (kod,)).fetchone() if kod else None
        if r is None or not r["anonim"]:
            raise AnonimHata("gecersiz_kod", "Bu kodla ek bilgi eklenebilecek bir bildirim bulunamadı.")
        if r["olusturma_zamani"][:10] != _bugun():
            raise AnonimHata("gun_gecti", "Ek bilgi yalnızca bildirimin yapıldığı gün eklenebilir.")
        if r["durum"] == "Sonuçlandırıldı":
            raise AnonimHata("kapali", "Bu bildirim sonuçlandırıldığı için ek bilgi eklenemez.")
        adet = conn.execute("SELECT COUNT(*) FROM ek_bilgiler WHERE takip_no = ?", (kod,)).fetchone()[0]
        if adet >= MAKS_EK_SAYISI:
            raise AnonimHata("limit", f"Bugün en fazla {MAKS_EK_SAYISI} ek bilgi eklenebilir.")
        k = conn.execute("SELECT son_epoch FROM ek_kilit WHERE takip_no = ?", (kod,)).fetchone()
        if k:
            kalan = math.ceil(EK_BEKLEME_SN - (time.time() - k["son_epoch"]))
            if kalan > 0:
                raise AnonimHata("bekle", f"Yeni ek bilgi için yaklaşık {kalan} saniye beklemelisin.", kalan)

        zaman = simdi()  # Europe/Istanbul gerçek zaman damgası; dakika/saniye korunur
        conn.execute("INSERT INTO ek_bilgiler (takip_no, zaman, metin) VALUES (?, ?, ?)", (kod, zaman, maskeli))
        conn.execute("INSERT INTO ek_kilit (takip_no, son_epoch) VALUES (?, ?) "
                     "ON CONFLICT(takip_no) DO UPDATE SET son_epoch = excluded.son_epoch", (kod, time.time()))

        # Ek metin daha yüksek bir sinyal üretiyorsa kayıt önceliği yükselir (insan yine inceler).
        oncelik = max(r["oncelik"], analiz.oncelik, key=lambda o: ONCELIKLER.index(o) if o in ONCELIKLER else 0)
        kat = sorted({x for x in (r["kategoriler"] or "").split(", ") if x} | set(analiz.kategoriler))
        esk = [x for x in (r["eslesmeler"] or "").split(", ") if x and x != "Belirgin eşleşme yok"]
        esk += [x for x in analiz.ifadeler if x not in esk]
        uyari = [x for x in (r["baglam_uyarilari"] or "").split(" | ") if x]
        uyari += [x for x in analiz.baglam_uyarilari if x not in uyari]
        mask = sorted({x for x in (r["maskelenen"] or "").split(", ") if x} | set(maskelenen))
        conn.execute(
            "UPDATE bildirimler SET oncelik = ?, kategoriler = ?, eslesmeler = ?, baglam_uyarilari = ?, "
            "maskelenen = ?, son_guncelleme = ? WHERE takip_no = ?",
            (oncelik, ", ".join(kat), ", ".join(esk) or "Belirgin eşleşme yok", " | ".join(uyari),
             ", ".join(mask), zaman, kod))
        _islem(conn, kod, "Anonim ek bilgi eklendi", f"{adet + 1}. ek bilgi", "Anonim gönderen", zaman)
    return {"adet": adet + 1, "kalan_hak": MAKS_EK_SAYISI - adet - 1, "oncelik": analiz.oncelik,
            "maskelenen": maskelenen}


def ek_bilgileri_getir(takip_no: str) -> list[dict]:
    with baglanti() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT zaman, metin FROM ek_bilgiler WHERE takip_no = ? ORDER BY id", (takip_no,))]


def ek_sayilari() -> dict[str, int]:
    with baglanti() as conn:
        return {r[0]: r[1] for r in conn.execute("SELECT takip_no, COUNT(*) FROM ek_bilgiler GROUP BY takip_no")}


# =====================================================================================
# v2.2 EK: trend/ortam analizi ve saklama süresi önizlemesi
# =====================================================================================
GUN_ADLARI = ("Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz")


def trend_ozeti(gun: int = 90, k_esik: int = 5) -> dict:
    """Saat, haftanın günü, hafta, ortam, tür ve ortam×tür dağılımı. Küçük hücre bastırma: ortam×tür
    çapraz tablosunda sayısı k_esik'ten küçük hücreler gizlenir (kimliksizleştirme için).
    Saat, KAYIT (bildirim) saatidir; olayın gerçekleştiği saat değildir."""
    esik = (datetime.now(TZ) - timedelta(days=gun)).strftime("%Y-%m-%d")
    with baglanti() as conn:
        satirlar = conn.execute(
            "SELECT olusturma_zamani, olay_turu, ortam FROM bildirimler "
            "WHERE substr(olusturma_zamani,1,10) >= ?", (esik,)).fetchall()
    saat, gun_say, hafta, ortam, tur, matris = Counter(), Counter(), Counter(), Counter(), Counter(), Counter()
    for r in satirlar:
        t = datetime.strptime(r["olusturma_zamani"], _ZAMAN_BICIMI)
        yil, hf, _ = t.isocalendar()
        saat[t.hour] += 1
        gun_say[t.weekday()] += 1
        hafta[f"{yil}-H{hf:02d}"] += 1
        ortam[r["ortam"]] += 1
        tur[r["olay_turu"]] += 1
        matris[(r["ortam"], r["olay_turu"])] += 1
    gorunen = {k: v for k, v in matris.items() if v >= k_esik}
    return {
        "toplam": len(satirlar), "gun": gun, "k_esik": k_esik,
        "saat": {h: saat.get(h, 0) for h in range(24)},
        "haftanin_gunu": {GUN_ADLARI[i]: gun_say.get(i, 0) for i in range(7)},
        "hafta": dict(sorted(hafta.items())),
        "ortam": dict(ortam.most_common()), "tur": dict(tur.most_common()),
        "matris": gorunen, "gizlenen_hucre": len(matris) - len(gorunen),
        "gizlenen_kayit": sum(v for v in matris.values() if v < k_esik),
    }


# =====================================================================================
# v2.3 EK: yöneticiye özel önleyici çalışma / Etki Merkezi
# =====================================================================================
ONLEYICI_DURUMLAR = ("Planlandı", "Devam ediyor", "Tamamlandı", "İptal edildi")

def onleyici_calisma_ekle(*, baslik: str, aciklama: str, konu: str, hedef_ortam: str,
                          sorumlu_kisi: str, sorumlu_birim: str, planlanan_tarih: str, aktor: str) -> int:
    """Yönetici tarafından oluşturulan önleyici çalışmayı ve ilk geçmiş kaydını ekler."""
    baslik = (baslik or "").strip()
    sorumlu_kisi = (sorumlu_kisi or "").strip()
    aciklama = (aciklama or "").strip()
    if not baslik or len(baslik) > 120:
        raise ValueError("Çalışma başlığı 1-120 karakter olmalıdır.")
    if not sorumlu_kisi or len(sorumlu_kisi) > 100:
        raise ValueError("Sorumlu kişi/birim bilgisi 1-100 karakter olmalıdır.")
    if len(aciklama) > 2000:
        raise ValueError("Açıklama en fazla 2000 karakter olabilir.")
    try:
        datetime.strptime(planlanan_tarih, "%Y-%m-%d")
    except (TypeError, ValueError):
        raise ValueError("Geçerli bir planlanan tarih girilmelidir.")
    zaman = simdi()
    with baglanti() as conn:
        cur = conn.execute(
            """INSERT INTO onleyici_calismalar
               (baslik, aciklama, konu, hedef_ortam, sorumlu_kisi, sorumlu_birim, planlanan_tarih,
                durum, olusturan, olusturma_zamani, guncelleme_zamani)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'Planlandı', ?, ?, ?)""",
            (baslik, aciklama, konu, hedef_ortam, sorumlu_kisi, sorumlu_birim, planlanan_tarih, aktor, zaman, zaman),
        )
        cid = int(cur.lastrowid)
        conn.execute(
            "INSERT INTO onleyici_calisma_gecmisi (calisma_id, zaman, aktor, islem, ayrinti) VALUES (?, ?, ?, ?, ?)",
            (cid, zaman, aktor, "Çalışma oluşturuldu", f"Sorumlu: {sorumlu_kisi}"),
        )
        return cid

def onleyici_calismalari_getir() -> list[dict]:
    with baglanti() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM onleyici_calismalar ORDER BY CASE durum WHEN 'Devam ediyor' THEN 0 WHEN 'Planlandı' THEN 1 WHEN 'Tamamlandı' THEN 2 ELSE 3 END, planlanan_tarih DESC, id DESC"
        )]

def onleyici_calisma_guncelle(calisma_id: int, *, durum: str, sorumlu_kisi: str,
                               sorumlu_birim: str, aktor: str, not_metni: str = "") -> None:
    if durum not in ONLEYICI_DURUMLAR:
        raise ValueError("Geçersiz çalışma durumu.")
    sorumlu_kisi = (sorumlu_kisi or "").strip()
    if not sorumlu_kisi or len(sorumlu_kisi) > 100:
        raise ValueError("Sorumlu kişi/birim bilgisi 1-100 karakter olmalıdır.")
    not_metni = (not_metni or "").strip()
    if len(not_metni) > 1000:
        raise ValueError("Değerlendirme notu en fazla 1000 karakter olabilir.")
    zaman = simdi()
    with baglanti() as conn:
        eski = conn.execute("SELECT * FROM onleyici_calismalar WHERE id = ?", (int(calisma_id),)).fetchone()
        if eski is None:
            raise LookupError("Önleyici çalışma bulunamadı.")
        tamamlanma = eski["tamamlanma_tarihi"]
        if durum == "Tamamlandı" and not tamamlanma:
            tamamlanma = datetime.now(TZ).date().isoformat()
        if durum != "Tamamlandı":
            tamamlanma = ""
        degisen = []
        if eski["durum"] != durum: degisen.append(f"Durum: {eski['durum']} → {durum}")
        if eski["sorumlu_kisi"] != sorumlu_kisi: degisen.append(f"Sorumlu: {eski['sorumlu_kisi']} → {sorumlu_kisi}")
        if eski["sorumlu_birim"] != (sorumlu_birim or ""): degisen.append("Sorumlu birim güncellendi")
        if not_metni: degisen.append("Değerlendirme: " + not_metni)
        if degisen:
            conn.execute(
                "UPDATE onleyici_calismalar SET durum=?, sorumlu_kisi=?, sorumlu_birim=?, tamamlanma_tarihi=?, guncelleme_zamani=? WHERE id=?",
                (durum, sorumlu_kisi, sorumlu_birim or "", tamamlanma, zaman, int(calisma_id)),
            )
            conn.execute(
                "INSERT INTO onleyici_calisma_gecmisi (calisma_id, zaman, aktor, islem, ayrinti) VALUES (?, ?, ?, ?, ?)",
                (int(calisma_id), zaman, aktor, "Çalışma güncellendi", " · ".join(degisen)),
            )

def onleyici_calisma_gecmisi_getir(calisma_id: int) -> list[dict]:
    with baglanti() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM onleyici_calisma_gecmisi WHERE calisma_id=? ORDER BY id DESC", (int(calisma_id),))]

def onleyici_ozeti() -> dict[str, int]:
    with baglanti() as conn:
        rows = conn.execute("SELECT durum, COUNT(*) AS adet FROM onleyici_calismalar GROUP BY durum").fetchall()
    sonuc = {d: 0 for d in ONLEYICI_DURUMLAR}
    sonuc.update({r["durum"]: int(r["adet"]) for r in rows})
    sonuc["Toplam"] = sum(sonuc.values())
    return sonuc

def onleyici_etki_karsilastir(calisma_id: int, k_esik: int = 5) -> dict | None:
    """Tamamlanma tarihinin 30 gün öncesi/sonrası toplu bildirim sayılarını karşılaştırır.
    Her iki pencere de k eşiğine ulaşmıyorsa sayı açıklanmaz. Nedensellik/başarı iddiası değildir."""
    with baglanti() as conn:
        w = conn.execute("SELECT konu, hedef_ortam, tamamlanma_tarihi, durum FROM onleyici_calismalar WHERE id=?", (int(calisma_id),)).fetchone()
        if not w or w["durum"] != "Tamamlandı" or not w["tamamlanma_tarihi"]:
            return None
        bitis = datetime.strptime(w["tamamlanma_tarihi"], "%Y-%m-%d").date()
        bugun = datetime.now(TZ).date()
        if bugun < bitis + timedelta(days=30):
            return {"bekleniyor": True, "gizli": False, "esik": k_esik, "once": None, "sonra": None, "degisim": None}
        once_bas, once_son = (bitis - timedelta(days=30)).isoformat(), bitis.isoformat()
        sonra_bas, sonra_son = bitis.isoformat(), (bitis + timedelta(days=30)).isoformat()
        clauses, params = [], []
        if w["konu"] not in ("Genel", "Tümü"):
            clauses.append("olay_turu = ?"); params.append(w["konu"])
        if w["hedef_ortam"] not in ("Tümü", "Genel"):
            clauses.append("ortam = ?"); params.append(w["hedef_ortam"])
        extra = (" AND " + " AND ".join(clauses)) if clauses else ""
        q = "SELECT COUNT(*) FROM bildirimler WHERE substr(olusturma_zamani,1,10) >= ? AND substr(olusturma_zamani,1,10) < ?" + extra
        once = int(conn.execute(q, [once_bas, once_son, *params]).fetchone()[0])
        sonra = int(conn.execute(q, [sonra_bas, sonra_son, *params]).fetchone()[0])
    if once < k_esik or sonra < k_esik:
        return {"gizli": True, "esik": k_esik, "once": None, "sonra": None, "degisim": None}
    return {"gizli": False, "esik": k_esik, "once": once, "sonra": sonra, "degisim": sonra - once}


# =====================================================================================
# v3.1: kalıcı saklama, yedekleme ve güvenli geri yükleme
# =====================================================================================
def veritabani_yedegi_uret() -> bytes:
    """WAL dâhil tutarlı SQLite çevrim içi yedeği üretir; kaynak DB'yi değiştirmez."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        hedef = Path(tmp.name)
    try:
        kaynak = sqlite3.connect(DB_YOLU, timeout=15)
        try:
            with sqlite3.connect(hedef) as yedek:
                kaynak.backup(yedek)
        finally:
            kaynak.close()
        return hedef.read_bytes()
    finally:
        hedef.unlink(missing_ok=True)

def veritabani_durumunu_kontrol_et() -> dict:
    with baglanti() as conn:
        kontrol = conn.execute("PRAGMA integrity_check").fetchone()[0]
        tablolar = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        return {"durum": kontrol, "bildirim": int(conn.execute("SELECT COUNT(*) FROM bildirimler").fetchone()[0]),
                "onleyici": int(conn.execute("SELECT COUNT(*) FROM onleyici_calismalar").fetchone()[0]),
                "tablo_sayisi": len(tablolar), "boyut": DB_YOLU.stat().st_size if DB_YOLU.exists() else 0}

def veritabani_yedegini_yukle(veri: bytes) -> None:
    """Yüklenen SQLite dosyasını doğrular ve mevcut DB'ye güvenli backup API ile aktarır."""
    import tempfile
    if not veri or len(veri) > 100 * 1024 * 1024:
        raise ValueError("Yedek dosyası boş veya 100 MB sınırını aşıyor.")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp.write(veri)
        gecici = Path(tmp.name)
    try:
        kaynak = sqlite3.connect(gecici)
        try:
            if kaynak.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Yedek dosyası sağlam değil; geri yükleme iptal edildi.")
            tablolar = {r[0] for r in kaynak.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "bildirimler" not in tablolar or "denetim_kaydi" not in tablolar:
                raise ValueError("Dosya Güvenli Okul veritabanı yedeği değil.")
            hedef = sqlite3.connect(DB_YOLU, timeout=20)
            try:
                kaynak.backup(hedef)
                hedef.commit()
            finally:
                hedef.close()
        finally:
            kaynak.close()
    finally:
        gecici.unlink(missing_ok=True)
