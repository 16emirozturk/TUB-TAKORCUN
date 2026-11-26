# Güvenli Okul — v3.1.3 paket ve PDF sağlamlaştırma notları

## Kaynak alınan sürüm
Bu paket, kullanıcı tarafından yüklenen `TUBİTAK(1).zip` içeriği üzerine hazırlanmıştır. Mevcut modüler dosya yapısı korunmuştur.

## Yapılan değişiklikler
1. `gelistirmeler.py` içindeki PDF font yükleme fonksiyonu eklendi/güncellendi: proje `fonts/`, proje kökü, çalışma dizini ve bilinen Linux font konumları aranır.
2. Yerel Unicode fontlar bulunamazsa ReportLab'in yerleşik `Helvetica` ve `Helvetica-Bold` fontlarıyla PDF oluşturulur. Helvetica'nın Unicode kapsamı sınırlı olduğundan bu yedekte aksanlı karakterler ASCII'ye sadeleştirilir ve PDF içinde uyarı gösterilir.
3. Arapça fontu veya Arapça şekillendirme bağımlılıkları yoksa bozuk glifler üretmek yerine güvenli İngilizce rapor fallback'i uygulanır.
4. `fonts/` klasörüne DejaVu Sans ve Noto Sans Arabic fontları ile lisans dosyaları eklendi.
5. PDF raporu, bildirim metinleri ve takip kodları yerine `db.istatistik_ozeti()` ile SQL toplu sayımı kullanır.
6. PDF testleri eklendi: 7 dil için PDF oluşturma, fontsuz yedek, Arapça yedek, kişisel açıklama içermeme ve kayıt listesi sınırından bağımsızlık.
7. `.gitignore`, `.streamlit/secrets.toml.example`, `PDF_HATASI_COZUMU.txt` ve bu değişiklik notu eklendi. Var olan `gitignore.txt` korunmuştur.

## Özellikle değiştirilmedi
`app.py`, `db.py`, `guvenlik.py`, `ek_sayfalar.py`, `hakaret_tespiti.py`, `degerlendirme.py`, `i18n.py`, `sabitler.py`, `stil.py`, logo ve mevcut veritabanı şeması değiştirilmedi. Mevcut renkler, CSS, menüler ve sayfa düzeni korunmuştur.

## Kaynak koddan doğrulanan mevcut işlevler
- Yönetici girişi, hatalı giriş sınırı ve oturum zaman aşımı.
- Öğrenci/ziyaretçi sayfalarından ayrılmış yönetici incelemesi, istatistikler, trend/ortam, Etki Merkezi, takvim, bildirim merkezi, yönetim günlüğü, PDF ve yedekleme ekranları; bunlar `yonetici_gerekli()` korumasını çağırır.
- 24 saatlik bekleyen bildirim SLA uyarısı ve yönetici günlük durum özeti.
- Rehberlik öneri kartları ve insan incelemesi ilkesi.
- Kural tabanlı metin sinyali; kod ve kullanıcı arayüzü bunun makine öğrenmesi/otomatik karar olmadığını açıkça belirtir.
- `db.sonuclanmis_kayitlari_sil()` kayıt silmeyi devre dışı bırakır; README/KVKK metinleri süreye bağlı otomatik silme olmadığını açıklar.
- SQLite yedekleme/geri yükleme işlevleri.

## Sınırlar ve kurulum
- Otomatik testler Streamlit Cloud üzerinde gerçek tarayıcı dağıtım testi yerine geçmez.
- Helvetica yedeği PDF'nin oluşturulmasını sağlar ancak Unicode fontların görsel kalitesini vermez. En iyi sonuç için `fonts/` klasörünü GitHub deposunun köküne yükleyin.
- `requirements.txt` içindeki bağımlılıklar deploy ortamında kurulmalıdır. Arapça PDF için `arabic-reshaper` ve `python-bidi` gereklidir.
- Bu çalışma ortamında ReportLab mevcut olduğu için PDF testleri çalıştırılabilir; Arapça şekillendirme paketleri kurulu değilse Arapça test akışı güvenli İngilizce fallback'ini denetler.
- Streamlit Cloud'un yerel SQLite dosyası kalıcı depolama garantisi taşımaz. Veri kalıcılığı gereksinimi için ayrıca kalıcı veritabanı altyapısı gerekir.
