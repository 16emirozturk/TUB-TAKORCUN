# Güvenli Okul — Bildirim ve Takip Platformu (v3.1)

Okullarda akran zorbalığı bildirimlerini toplamak, **insan incelemesi** için önceliklendirmek ve süreci
izlenebilir kılmak için hazırlanmış bir Streamlit prototipidir. Karar veren bir sistem **değildir**.


### PDF dayanıklılık ve dağıtım eki (v3.1.3 paket düzeltmesi)
- `fonts/` klasörü DejaVu Sans ve Noto Sans Arabic yazı tipleri ile lisans dosyalarını içerir. Bu klasör `app.py` ile aynı proje kökünde tutulmalıdır.
- PDF yazı tipi yükleyicisi önce proje içindeki fontları, ardından kök/çalışma dizinlerini ve bilinen sistem font klasörlerini arar.
- Unicode yazı tipleri bulunamazsa PDF oluşturma işlemi durmaz; ReportLab'in yerleşik Helvetica/Helvetica-Bold fontlarıyla güvenli yedek üretir. Bu yedekte aksanlı karakterler sadeleştirilir.
- Arapça fontu veya `arabic-reshaper` / `python-bidi` paketleri yoksa bozuk Arapça metin üretmek yerine rapor İngilizce hazırlanır ve PDF içinde bilgilendirme notu gösterilir.
- PDF regresyon testleri normal font akışını, fontsuz Helvetica yedeğini, Arapça güvenli yedeğini, kişisel metinlerin PDF dışında kalmasını ve SQL toplu sayımını denetler.
- Paketleme için `.gitignore` ve `.streamlit/secrets.toml.example` eklendi; eski `gitignore.txt` dosyası korunmuştur.

**Önemli:** Bu düzeltme PDF üretimini dayanıklı hale getirir; Streamlit Cloud üzerindeki SQLite dosyasının kalıcı olmasını garanti etmez. Bulutta kalıcı veri için kalıcı/harici veritabanı veya doğrulanmış kalıcı disk ve düzenli yedekleme gerekir.

## Windows üzerinde çalıştırma
1. ZIP dosyasını çıkarın ve `guvenli_okul` klasörünü açın.
2. PowerShell veya Komut İstemi'nde bu klasörde şu komutları sırayla çalıştırın:
```powershell
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
py -c "from guvenlik import parola_hashle; print(parola_hashle(input('Yönetici parolası: ')))"
```
3. Son komutun verdiği `pbkdf2_sha256$...` değerini `.streamlit/secrets.toml` dosyasındaki `password_hash` alanına yapıştırın. `username` değerini de belirleyin.
4. Uygulamayı başlatın:
```powershell
streamlit run app.py
```
5. Tarayıcıda açılan yerel adreste uygulamayı görüntüleyin. Yönetici girişi, `secrets.toml` dosyasında belirlediğiniz kullanıcı adı ve parolayla yapılır.

Geliştirici testleri için ayrıca `py -m pip install -r requirements-dev.txt` ve `pytest -q` komutlarını kullanın. Gerçek okul/öğrenci verisi girmeyin; bu sürüm demo/prototiptir.

## Yapı
| Dosya | Görev |
|---|---|
| `app.py` | Arayüz ve sayfa akışı |
| `db.py` | SQLite katmanı: şema göçü, işlemler, istatistik, CSV, saklama süresi |
| `guvenlik.py` | Parola özeti/doğrulama, kişisel veri maskeleme, CSV enjeksiyon koruması |
| `hakaret_tespiti.py` | Kural tabanlı sinyal: kategori, öncelik, bağlam uyarısı |
| `degerlendirme.py` | Sentetik etiketli küme + precision/recall/F1 |
| `stil.py` | CSS (harici yazı tipi/CDN yok) |
| `ek_sayfalar.py` | Destek rehberi, trend/ortam analizi, gizlilik ve KVKK paneli (onam akışı simülasyonu) |
| `i18n.py` | 7 dil için merkezi çeviri altyapısı, temel arayüz sözlüğü, tarih-saat biçimi ve RTL yön bilgisi |
| `testler/` | Birim testleri |

## v1 → v2: düzeltilen hatalar
- Türkçe karakterli kullanıcı adı/parola `hmac.compare_digest` ile `TypeError` veriyordu → UTF-8 bayt karşılaştırması.
- Sayfa düğmeleri `session_state["ana_menu"]` değerini widget oluştuktan sonra değiştiriyordu → `on_click` geri çağrıları.
- `st.success(); st.rerun()` mesajı yutuyordu → `flash` mekanizması.
- `clear_on_submit=True` doğrulama hatasında da yazılan metni siliyordu → yalnızca başarıda form sıfırlanır.
- `with sqlite3.connect()` bağlantıyı kapatmıyordu → her işlemde kapatan bağlam yöneticisi.
- Saatler sunucu saatindeydi (bulutta UTC) → Europe/Istanbul.
- `ilk_acilista_kayitlari_temizle` bayrak yoksa TÜM kayıtları siliyordu → kaldırıldı; yerine şema sürümü + göç.
- Algılayıcı "gerizekalı" yazımını kaçırıyordu (sözlükte ASCII) → Türkçe'ye duyarlı katlama.
- Bozuk Markdown (`** Gizlilik**`), boş ikon kutuları, çift "10." bölüm numarası, harici Google Fonts çağrısı.

## Yeni özellikler
Öncelik sinyali ve kuyruk sıralaması · kişisel veri maskeleme (T.C. no sağlama toplamı dâhil) · takip kodu ile
durum sorgulama · hatalı giriş kilidi + oturum zaman aşımı + PBKDF2 parola özeti · denetim kaydı ·
yönetici işlemlerinde "kim yaptı" bilgisi · CSV dışa aktarım (kimlik varsayılan hariç) · kalıcı veri saklama · yedekleme/geri yükleme ·
anonim kayıtlarda saniye hassasiyetli zaman damgası · yanıt süresi metrikleri · otomatik algılayıcı değerlendirmesi.

## Bilimsel doğrulama yol haritası (TÜBİTAK için)
1. Araştırma sorusu ve hipotezlerin yazılması (ör. "Kural tabanlı sinyal, yönetici inceleme sırasını iyileştirir mi?").
2. Etik kurul / okul ve veli izniyle, kimliksizleştirilmiş gerçek veya uzmanca üretilmiş bir veri kümesi.
3. En az iki uzmanın (rehber öğretmen/psikolojik danışman) bağımsız etiketlemesi; Cohen kappa raporu.
4. Eğitim/doğrulama/test ayrımı; kural tabanlı yöntemin başka bir yöntemle (ör. sınıflandırıcı) karşılaştırması.
5. Kullanılabilirlik testi (SUS) ve yanıt süresi ölçümü.
6. Yanlış alarm/kaçırma analizi ve sınırlılıkların açıkça raporlanması.

## Yayına almadan önce
KVKK (aydınlatma, hukuki sebep, saklama-imha, yurt dışı sunucu), kişi bazlı hesap + 2FA, HTTPS, şifreli yedek,
bağımsız güvenlik testi ve okul acil durum protokolü gereklidir. Acil hat numaralarını (`sabitler.py`) resmi
kaynaklardan yeniden doğrulayın.

## v2.1 — Tam anonim bildirim ve sadeleştirilmiş akış
Artık tek bir **Yeni bildirim** ve tek bir **Bildirim sorgula** sayfası var (eski yinelenen sayfalar kaldırıldı).

- **Tam anonim:** formda ad, soyad, sınıf, telefon istenmez ve kaydedilmez; zaman dakika/saniye hassasiyetinde saklanır.
- **Günlük kota:** `app.py` içindeki küçük bir yerel bileşen (çalışma anında geçici klasöre yazılır, ayrı dosya gerekmez); rastgele cihaz jetonunu tarayıcının localStorage'ında
  (yedek: çerez) saklayıp uygulamaya iletir, sayfa yenilense de aynı kalır. Veritabanında jetonun SHA-256 özeti ve gün (`anonim_cihaz`) saklanır; rapora
  bağlanmaz, süre dolduğu için otomatik silinmez. Aynı gün ikinci bildirimde “Günlük bildirim hakkınız dolmuştur.” görünür.
- **Gizli takip kodu:** `GO-XXXXXXXXXX` (~50 bit). Sorgu sayfası durumu ve tarihleri gösterir.
- **Ek bilgi:** aynı sorgu sayfasında; yalnızca anonim kayıtlarda, bildirimin günü; 60 sn bekleme ve günde en çok 3 ek
  **sunucuda** uygulanır. Ek metin maskelenir, analiz edilir; daha yüksek sinyal çıkarsa kayıt önceliği yükselir.
  İnceleme ekranında “Anonim gönderenin ek bilgileri” ve kuyrukta “+N ek bilgi” görünür.
- **Mesajlaşma yok:** öğrenci yalnızca durumu görür; yönetici notları gösterilmez.
- **Telefon uyumu:** seçenekler alt alta dokunması kolay kartlar, büyük düğmeler, iOS'ta yakınlaştırmayı önleyen yazı
  boyutu, dar ekranda tek sütun.

Bilinen sınırlar: kota tarayıcı çerezine dayanır; çerez silme/gizli sekme ile aşılabilir (hesapsız anonimlikte kesin
kota mümkün değildir). Streamlit Cloud'da yerel SQLite dosyası kalıcı depolama garantisi taşımaz; çevrim içi gerçek kullanımda kalıcı harici veritabanı gerekir. Yerel kullanımda DB dosyası proje klasöründe kalır; yine de düzenli yedek alın.

## v2.3 — Modern arayüz ve ek sayfalar
- Gradyanlı karşılama alanı ve satır içi SVG illüstrasyon/ikon rozetleri (harici resim, CDN, yazı tipi yok).
- Logo kenar çubuğuna gömülü (base64) olarak yerleştirilir; ek istek yapılmaz.
- Acil hatlar: 112, 183, 444 0 632 (MEBİM). Yayından önce resmî kaynaklardan yeniden doğrulayın.
- Yeni sayfalar: **Destek rehberi** (herkese açık), **Trend ve ortam** (yönetici; küçük hücre bastırmalı),
  **Gizlilik ve KVKK** (aydınlatma taslağı, veri envanteri, saklama politikası, onam akışı simülasyonu).
- Güvenlik düzeltmeleri: kullanıcı metni artık Markdown olarak yorumlanmaz (görsel/bağlantı enjeksiyonu önlenir);
  günlük kota denetimi salt okunurdur; süreye bağlı kayıt silme devre dışıdır.


## Ek geliştirmeler
- Arayüzde yedi dil desteği: Türkçe, English, Deutsch, Français, Español, العربية ve Azərbaycan dili.
- Yönetici genel bakış ve inceleme ekranında günlük özet ve yüksek/acil uyarı bandı.
- İnceleme kuyruğunda tarih aralığı filtresi ve bekleme süresi / 24 saat gecikme göstergesi.
- Kategoriye göre rehberlik kontrol listesi.
- Yeni anonim bildirimler ve ek bilgiler için Europe/Istanbul saatinde saniye hassasiyetli zaman damgası.

Not: Eski veritabanında daha önce saat başına yuvarlanmış zaman damgalarının kaybolan dakika/saniye kısmı geriye dönük üretilemez. Yeni kayıtlar doğru hassasiyetle saklanır.


### Uygulama notları
- Dil seçimi Streamlit oturumunda korunur. Menü, formlar, seçenekler, yönetici ekranları, rehberlik içerikleri, uyarılar, tablolar ve bilgilendirme metinleri merkezi `i18n.py` kataloğundan çevrilir.
- SLA süresi her sayfa yenilemesinde/etkileşimde yeniden hesaplanır. Canlı saniyelik otomatik yenileme kullanılmaz; gereksiz arka plan yenilemesi ve veritabanı yükü oluşturulmaz.
- Rehberlik önerileri karar veya klinik yönlendirme değildir; okul psikolojik danışmanı tarafından onaylanmalıdır.


## Çok dilli arayüz desteği

- Kenar çubuğundan Türkçe, English, Deutsch, Français, Español, العربية veya Azərbaycan dili seçilebilir.
- Menü, bildirim formu ve seçenekleri, yönetici inceleme ekranları, istatistikler, trend/ortam analizi, Etki Merkezi, destek rehberi, güvenli kullanım, gizlilik/KVKK ve onam simülasyonu için yerelleştirme kataloğu kullanılır.
- Kullanıcıların yazdığı bildirim açıklamaları, yönetici notları ve Etki Merkezi çalışma başlığı/açıklaması/sorumlu kişi alanları otomatik çevrilmez; özgün metinleri korunur.
- Okulun resmî adı (**Bozüyük Fen Lisesi**) ve proje adı (**Güvenli Okul**) korunur. Arapça arayüz RTL yönünü, takip kodları ise LTR yönünü kullanır.
- Bilinen arayüz anahtarında hedef dil çevirisi henüz yoksa Türkçe metin sızdırmak yerine İngilizce karşılık gösterilir. Katalogda bulunmayan serbest metin olduğu gibi bırakılır; otomatik makine çevirisi yapılmaz.
- Tarih/saat gösterimleri dil bazında biçimlendirilir; veritabanındaki zaman damgaları değiştirilmez.
- Çeviriler uygulama içi kontrollerle sınanmıştır; yayımlanmadan önce özellikle hukuki ve öğrenci destek metinlerinin ilgili dillerde ana dili konuşan kişilerce son okuması önerilir.

## v2.4 — Çoklu dil altyapısı (TR / EN / DE / FR / ES / AR / AZ)
- Dil seçimi Türkçe, English, Deutsch, Français, Español, العربية ve Azərbaycan dili seçeneklerini içerir.
- Çeviri çağrıları merkezi `i18n.py` modülüne yönlendirilir; `set_language()` ile oturumun seçili dili uygulama genelinde kullanılır.
- Arapça seçildiğinde arayüz için RTL (sağdan sola) yön kuralları uygulanır; takip kodu gibi Latin karakterli alanlar LTR tutulur.
- Tarih/saat gösterimleri dil bazında biçimlendirilir; veritabanındaki zaman damgaları değiştirilmez.
- Serbest kullanıcı açıklamaları, yönetici notları ve okul/proje adları otomatik çevrilmez.

**Çeviri kapsamı ve doğrulama:** Bu sürümde beş ek dilin katalogları ana sayfa ile sınırlı kalmayacak şekilde genişletilmiştir. Destek rehberi, trend/ortam, yönetici inceleme, Etki Merkezi, güvenli kullanım, araştırma, gizlilik/KVKK bildirimi ve onam formu metinleri de kapsama alınmıştır. Otomatik testler çeviri anahtarlarının doluluğunu, önemli ekran metinlerini ve serbest kullanıcı metinlerinin değiştirilmemesini denetler. Bu kontroller profesyonel ana dili redaksiyonunun yerine geçmez; özellikle hukuki ve öğrenci destek metinleri gerçek kullanım öncesinde yetkili kişilerce gözden geçirilmelidir.

### Çok dilli doğrulama
- Olay türü, ortam, zaman, tekrar sıklığı, birim, durum ve öncelik seçenekleri beş ek dilde kontrol edilir.
- Takip kodu, ek bilgi, günlük sınır, yönetici oturumu, inceleme, trend, Etki Merkezi, gizlilik ve onam akışı için çeviri testleri bulunur.
- Kullanıcı tarafından yazılan açıklama ve notlar otomatik çevrilmez.
- Son kontrol: `python -m unittest discover -s testler -v`.

## v2.5 — Etki Merkezi (yöneticiye özel)
- Yönetim menüsüne yalnızca yönetici oturumuyla açılan **Etki Merkezi** eklendi.
- Yönetici önleyici çalışma başlığı, açıklama/hedef, ilişkili konu, hedef ortam, sorumlu öğretmen/yetkili kişi, sorumlu birim ve planlanan tarihi kendisi girer.
- Çalışmalar planlandı / devam ediyor / tamamlandı / iptal edildi durumlarıyla takip edilir; sorumlu ve durum değişiklikleri ile değerlendirme notları ayrı işlem geçmişine yazılır.
- Tamamlanma tarihinden önceki ve sonraki 30 günlük toplu bildirim sayıları, her iki dönemde de en az 5 kayıt varsa gösterilir. Sonraki 30 gün tamamlanmadan kıyaslama yapılmaz; küçük sayılar gizlenir.
- Bu karşılaştırma yalnızca bildirim adetlerindeki gözlemsel değişimi gösterir. Olayların gerçek sıklığını veya çalışmanın nedensel etkisini kanıtlamaz.
- Öğrenci isimleri/sınıfları ve tekil bildirim açıklamaları Etki Merkezi analizinde kullanılmaz. Bu demo sürümünde sorumlu alanları için de gerçek kişi bilgisi yerine örnek veri kullanılmalıdır.
- Etki Merkezi arayüzü ve durum metinleri yedi dilde yerelleştirilir. Yönetici tarafından girilen çalışma başlığı, açıklaması, sorumlu adı ve notlar otomatik çevrilmez.
- Veritabanına mevcut kayıtları silmeden iki yeni tablo eklenir: `onleyici_calismalar` ve `onleyici_calisma_gecmisi`.

## v3.1 — genişletilmiş sunum sürümü
- Yedi arayüz dili: Türkçe, English, Deutsch, Français, Español, العربية ve Azərbaycan dili.
- Önleyici çalışma takvimi, herkese açık farkındalık/eğitim ve yardım merkezleri.
- Dil ve erişilebilirlik sayfası (büyük metin, yüksek kontrast, Arapça RTL).
- Yönetici bildirim merkezi, gelişmiş işlem günlüğü ve kişisel açıklamaları içermeyen PDF proje raporu.
- Yöneticiye özel SQLite yedekleme ve doğrulamalı geri yükleme.
- **Veri saklama:** Bildirimler, ek bilgiler, notlar, önleyici çalışmalar ve işlem geçmişi 180/360 gün sonra otomatik silinmez. Süreye bağlı silme arayüzü kaldırılmıştır; DB silme yordamı da devre dışıdır. Düzenli yedek alın. Gerçek okul kullanımında saklama-imha politikası KVKK ve okulun yükümlülüklerine göre hukuk/kurum onayıyla belirlenmelidir.
- Rol/yetki yönetimi (#12) ve demo senaryo merkezi (#11) bu sürüme dahil değildir. Tek yönetici hesabı modeli korunur.

PDF çıktısı için `reportlab` bağımlılığı `requirements.txt` içine eklenmiştir.


## v3.1 — Öğretmen sunumu için birleştirilmiş sürüm
- Önleyici çalışma takvimi: Etki Merkezi'nde oluşturulan planları ve yaklaşan/geciken tarihleri gösterir.
- Farkındalık ve eğitim merkezi ile yardım merkezi: ziyaretçilere açık, yargılayıcı olmayan bilgilendirme.
- Dil ve erişilebilirlik merkezi: yedi dil, Arapça RTL, büyük metin ve yüksek kontrast seçenekleri.
- Yönetici bildirim merkezi: bekleyen kayıtlar, 24 saat SLA uyarıları ve yaklaşan çalışmalar.
- Gelişmiş yönetim günlüğü: kullanıcı/işlem araması; denetim kayıtları otomatik temizlenmez.
- PDF proje raporu: toplu istatistik kullanır; bildirim açıklamaları ve takip kodları eklenmez.
- Yedekleme/geri yükleme: SQLite çevrim içi yedeği ve geri yüklemeden önce dosya bütünlüğü kontrolü.
- Öncelik sinyali zaten mevcuttur; ikinci bir sistem oluşturulmadı, mevcut insan incelemesi yaklaşımı korundu.
- **Hariç tutulanlar:** Demo Senaryo Merkezi (#11) ve rol/yetki yönetimi (#12) bu sürümde yoktur. Tek yönetici hesabı modeli korunur.
- **Veri silme:** Bildirimler, ek bilgiler, notlar, önleyici çalışmalar, denetim kayıtları ve giriş denemeleri 180/360 gün sonra otomatik silinmez. Süreye bağlı silme ekranı kaldırıldı; silme fonksiyonu güvenlik gereği devre dışı bırakıldı.
- **Önemli dağıtım notu:** Yerel SQLite dosyası bilgisayarda proje klasöründe kalır; Streamlit Cloud gibi geçici dosya sistemlerinde kalıcı depolama garantisi yoktur. İnternetten gerçek kullanım için kalıcı harici veritabanı ve okul onayı gerekir. Bu proje demo/prototiptir; gerçek öğrenci verisi kullanmayın.
