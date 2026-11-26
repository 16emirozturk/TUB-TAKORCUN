"""Güvenli Okul arayüzü için yedi dilli yerelleştirme katmanı.

Veritabanındaki sabit kodlar ve kayıtlar Türkçe/orijinal biçimde tutulur;
çeviri yalnızca kullanıcıya gösterilen arayüz katmanında uygulanır.
Resmî kurum/okul adları ve proje adı çevrilmez.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
import re

TR = "Türkçe"
EN = "English"

# Tam cümleler önce, kısa terimler sonra uygulanır. Serbest kullanıcı metinleri
# translate() ile otomatik çevrilmez; yalnızca bilinen arayüz ifadeleri eşlenir.
CATALOG: dict[str, str] = {
    # Navigasyon ve genel
    "Genel bakış": "Overview", "Yeni bildirim": "New report", "Bildirim sorgula": "Track a report",
    "Destek rehberi": "Support guide", "Yönetici girişi": "Administrator sign-in",
    "Bildirim inceleme": "Report review", "İstatistikler": "Statistics", "Trend ve ortam": "Trends and settings",
    "Gizlilik ve KVKK": "Privacy and data protection", "Araştırma ve test": "Research and testing",
    "Güvenli kullanım": "Safe use", "KULLANICI": "USER", "YÖNETİM": "ADMINISTRATION",
    "KURUMSAL": "INFORMATION", "OTURUM": "SESSION", "Oturumu kapat": "Sign out",
    "Ziyaretçi (giriş yapılmadı)": "Visitor (not signed in)", "Yönetici:": "Administrator:",
    "Dil / Language": "Language / Dil", "Türkçe": "Türkçe", "English": "English",
    "Güvenli Okul · Bildirim ve takip": "Güvenli Okul · Reporting and follow-up",
    "Güvenli Okul · Bildirim ve takip sistemi · Kural tabanlı sinyaller karar değildir.":
        "Güvenli Okul · Reporting and follow-up platform · Rule-based signals are not decisions.",
    "Bağımsız çalışma alanı": "Independent demonstration environment",
    "Gerçek okul sistemine bağlı değildir. Gerçek kişisel verileri girmeyin.":
        "This platform is not connected to a live school system. Do not enter real personal data.",
    "Bağımsız çalışma alanı · Gerçek okul sistemine bağlı değildir. Gerçek kişisel verileri girmeyin.":
        "Independent demonstration environment · Not connected to a live school system. Do not enter real personal data.",
    "DEMO": "DEMO", "PİLOT": "PILOT", "Yönetici": "Administrator", "Ziyaretçi": "Visitor",
    "Sürüm": "Version", "Algılayıcı": "Detector",

    # Genel bakış
    "Güvenli bir okul, herkesin hakkı.": "A safe school is everyone's right.",
    "Zorbalığı kimliğini vermeden bildir, gizli kodunla durumu takip et.":
        "Report bullying without identifying yourself and track its status using your private code.",
    "Anonim": "Anonymous", "Gizli takip kodu": "Private tracking code", "İnsan incelemesi": "Human review",
    "Yönetici özeti": "Administrator dashboard", "Açık kayıt": "Open reports", "Toplam kayıt": "Total reports",
    "Nasıl kullanılır?": "How it works", "Rehberlik bilgi bankası": "Guidance resource centre",
    "Güvenlik ilkeleri": "Security principles", "İnceleme kuyruğunu aç": "Open review queue",
    "Destek rehberini aç": "Open support guide", "Yeni bildirim": "New report",
    "Bildirim sorgula": "Track a report", "Güvenli kullanım": "Safe use",
    "Gizlilik": "Privacy", "Sinyal, karar değil": "A signal is not a decision",
    "Hesap verebilirlik": "Accountability", "1 · Bildir": "1 · Report",
    "2 · Takip et": "2 · Track", "3 · İnsan inceler": "3 · Human review",
    "Formu doldur. Ad ve sınıf istenmez; sana gizli bir kod verilir.":
        "Complete the form. Your name and class are not requested; you will receive a private tracking code.",
    "Kodunla durumu gör, aynı gün ek bilgi ekle.": "Check the status using your code and add further information on the same day.",
    "Yetkili kişiler kaydı inceler. Kararı makine vermez.":
        "Authorised staff review the report. The system does not make decisions.",
    "Telefon, T.C. no, e-posta ve IBAN otomatik gizlenir.":
        "Phone numbers, national ID numbers, email addresses and IBANs are automatically masked.",

    # Yetkilendirme
    "Yönetici erişimi gerekli": "Administrator access required",
    "Bu bölümü görüntülemek için yönetici oturumu açın.": "Sign in as an administrator to view this section.",
    "Yönetici girişine git": "Go to administrator sign-in", "Yönetici girişi": "Administrator sign-in",
    "Bildirim inceleme alanına yalnızca yetkili kullanıcılar erişebilir.":
        "Only authorised users can access the report review area.",
    "Yönetici oturumu açık.": "Administrator session is active.",
    "Bildirim incelemeye git": "Go to report review", "Kullanıcı adı": "Username", "Parola": "Password",
    "Giriş yap": "Sign in", "Kullanıcı adı veya parola yanlış.": "The username or password is incorrect.",
    "Yönetici bilgileri ayarlanmamış.": "Administrator credentials have not been configured.",
    "Çok fazla hatalı deneme. Lütfen": "Too many failed attempts. Please wait",
    "Sistem genelinde çok fazla hatalı giriş denemesi var. Lütfen bir süre sonra tekrar deneyin.":
        "There have been too many failed sign-in attempts across the system. Please try again later.",
    "Hareketsizlik nedeniyle yönetici oturumu kapatıldı.": "The administrator session was signed out due to inactivity.",
    "Oturum kapatıldı": "Session signed out", "Oturum zaman aşımı": "Session timed out",

    # Bildirim formu / takip
    "BİLDİRİM": "REPORT", "Kimliğini vermeden bildir. Ad, sınıf veya telefon istenmez.":
        "Submit a report without identifying yourself. Your name, class and phone number are not requested.",
    "Hazırlanıyor…": "Preparing…", "Günde bir bildirim hakkın var.": "You can submit one report per day.",
    "Ne oldu?": "What happened?", "Nerede oldu?": "Where did it happen?", "Ne zaman oldu?": "When did it happen?",
    "Bu olay kaç kez yaşandı?": "How often has this happened?", "Olayı kendi cümlelerinle anlat": "Describe what happened in your own words",
    "Ne oldu, nerede ve ne zaman oldu? Ad, telefon gibi bilgileri yazma.":
        "Describe what happened, where and when. Do not include names, phone numbers or other identifying details.",
    "Gerçek kişisel bilgi içermeyen örnek bir açıklama girdiğimi onaylıyorum.":
        "I confirm that I have entered a sample description that contains no real personal information.",
    "Bilgilendirme metnini okudum; verdiğim bilgilerin bildirim sürecinde işlenmesini kabul ediyorum.":
        "I have read the privacy notice and agree to the processing of the information I provide for the reporting process.",
    "Bildirimi gönder": "Submit report", "Lütfen olayı anlat.": "Please describe what happened.",
    "Açıklama yalnızca boşluk veya noktalama işaretlerinden oluşamaz. Kısaca ne olduğunu yaz.":
        "The description cannot consist only of spaces or punctuation. Please briefly describe what happened.",
    "Lütfen onay kutusunu işaretle.": "Please tick the confirmation box.",
    "Kısa sürede çok fazla bildirim gönderildi. Lütfen yaklaşık": "Too many reports have been submitted in a short period. Please try again in approximately",
    "saniye sonra tekrar dene.": "seconds.", "Bildirimin kaydedildi. Teşekkür ederiz.": "Your report has been submitted. Thank you.",
    "Gizli takip kodun.": "Your private tracking code.",
    "Durumu ve ek bilgi eklemeyi bu kodla yaparsın.": "Use this code to check the status and add further information.",
    "Not al ya da ekran görüntüsü al; kod kaybolursa yeniden oluşturulamaz:":
        "Save this code or take a screenshot. It cannot be recovered if lost:",
    "Açıklamandaki şu bilgiler gizlilik için otomatik gizlendi:":
        "The following information in your description was automatically masked for privacy:",
    "Durumu sorgula": "Check status", "Kodumu not aldım": "I have saved my code",
    "Bu takip kodu yalnızca uygulamadaki kaydı tanımlar. Rehberlikle mesajlaşma yoktur; yalnızca bildirimin durumunu görürsün.":
        "This tracking code identifies only the report in this platform. It does not provide messaging with the guidance service; it only lets you view the report status.",
    "Herhangi bir kuruma otomatik bildirim gönderilmez.": "No automatic notification is sent to any institution.",
    "TAKİP": "TRACKING", "Takip koduyla durumu gör, aynı gün ek bilgi ekle. Mesajlaşma yoktur.":
        "Check the status using your tracking code and add further information on the same day. Messaging is not available.",
    "Gizli takip kodu": "Private tracking code", "GO-XXXXXXXXXX": "GO-XXXXXXXXXX",
    "Durumu göster": "Show status", "Bu kodla eşleşen bir kayıt bulunamadı. Kodu kontrol edip tekrar dene.":
        "No report was found for this code. Check the code and try again.",
    "Ek bilgi ekle": "Add further information", "Ek bilgi yalnızca anonim bildirimlerde, bildirimin yapıldığı gün ve bildirim sonuçlanmadan önce eklenebilir.":
        "Further information can only be added to anonymous reports on the day they were submitted and before the report is closed.",
    "Eklenen ek bilgi:": "Additional entries:", "Ek bilgiler aynı bildirimin altına eklenir.":
        "Additional information is attached to the same report.", "Bugün için ek bilgi sınırına ulaştın.":
        "You have reached today's limit for additional information.",
    "Yeni ek bilgi için yaklaşık": "Please wait approximately", "beklemen gerekiyor.": "before adding more information.",
    "Eklemek istediğin bilgi": "Additional information", "Ek bilgiyi gönder": "Submit additional information",
    "Ek bilgi kaydedilemedi. Lütfen daha sonra tekrar dene.": "Additional information could not be saved. Please try again later.",
    "Günlük bildirim hakkınız dolmuştur. Yarın yeniden bildirim yapabilirsin. Bugünkü bildirimine takip koduyla ek bilgi ekleyebilirsin.":
        "You have reached the daily report limit. You can submit another report tomorrow. You may add information to today's report using your tracking code.",
    "Bildirimime ek bilgi ekle": "Add information to my report", "Lütfen yaklaşık": "Please wait approximately",

    # Kayıt ve inceleme
    "Oluşturulma": "Created", "Son güncelleme": "Last updated", "Bildirim ayrıntıları": "Report details",
    "Olay türü": "Incident type", "Ortam": "Setting", "Yaklaşık zaman": "Approximate time",
    "Tekrarlanma": "Frequency", "Açıklama": "Description", "Bildirimde belirtilen kişi bilgileri": "Personal details mentioned in the report",
    "Otomatik sinyal ve değerlendirme notu": "Automated signals and assessment notes",
    "Öncelik sinyali:": "Priority signal:", "Kategoriler:": "Categories:", "Eşleşen ifadeler:": "Matched phrases:",
    "Belirgin eşleşme yok": "No notable matches", "Açıklamada otomatik maskelenen bilgi türleri:":
        "Types of information automatically masked in the description:",
    "Açıklama kalitesi kontrolü:": "Description quality check:",
    "Metin çok kısa, yeterince açıklayıcı olmayabilir veya tekrar eden karakterler içeriyor. ":
        "The text may be too short, insufficiently descriptive, or contain repeated characters. ",
    "Bu bir spam/asılsız bildirim kanıtı değildir; otomatik silinmez, yetkili kişi bağlamı kontrol etmelidir.":
        "This is not evidence of spam or a false report. The report is not deleted automatically; an authorised reviewer should assess the context.",
    "Metin temel uzunluk kontrolünü geçti. Bu, bildirimin doğru olduğu anlamına gelmez.":
        "The text passed the basic length check. This does not mean that the report is accurate.",
    "Algılayıcı sürümü:": "Detector version:", "Bu sürüm gerçek bir yapay zekâ modeli değil, kural tabanlı sinyal ve basit metin kalite kontrolü kullanır.":
        "This version is not an AI model; it uses rule-based signals and a basic text-quality check.",
    "İnceleme ve yönlendirme": "Review and assignment", "Durum": "Status", "Sorumlu birim": "Assigned team",
    "Değişiklikleri kaydet": "Save changes", "İnceleme notları": "Review notes", "Yeni not": "New note",
    "Notu kaydet": "Save note", "İşlem geçmişi": "Activity history", "Henüz not eklenmemiş.": "No notes have been added yet.",
    "Henüz işlem geçmişi yok.": "There is no activity history yet.", "Henüz kayıt yok. Yeni bir bildirim oluşturulduğunda burada görünür.":
        "There are no reports yet. New reports will appear here when submitted.",
    "Kayıt kuyruğu": "Report queue", "Kayıt ara": "Search reports", "Takip kodu, olay türü, ortam veya birim":
        "Tracking code, incident type, setting or team", "İnceleme durumu": "Review status", "Öncelik sinyali": "Priority signal",
    "Bildirim türü": "Report type", "Sıralama": "Sort by", "Tüm durumlar": "All statuses", "Tüm birimler": "All teams",
    "Tümü": "All", "Öncelik (yüksekten)": "Priority (highest first)", "En yeni önce": "Newest first",
    "En eski önce": "Oldest first", "Kayıt seç": "Select a report", "Seçili kayıt": "Selected report",
    "Tarih aralığı": "Date range", "Başlangıç tarihi": "Start date", "Bitiş tarihi": "End date",
    "Bu filtrelerle eşleşen kayıt bulunamadı.": "No reports match these filters.", "Kayıt": "Report",
    "kayıt": "reports", "GECİKMİŞ": "OVERDUE", "Gecikmiş": "Overdue", "Açık": "Open",
    "İnceleme kuyruğunu aç": "Open review queue", "Anonim": "Anonymous", "Kimlik bilgisi belirtilmiş": "Identifying details provided",
    "Kayıtlar": "Reports", "Denetim kaydı": "Audit log", "Dışa aktarım ve saklama": "Export and retention",
    "Girişler, başarısız denemeler, dışa aktarımlar ve silme işlemleri burada izlenir.":
        "Sign-ins, failed attempts, exports and deletion actions are tracked here.", "Henüz denetim kaydı yok.": "There are no audit records yet.",
    "Dışa aktarım": "Export", "Kimlik bilgilerini (ad, soyad, sınıf) dahil et": "Include identifying details (first name, last name, class)",
    "CSV indir": "Download CSV", "Saklama süresi": "Retention period", "Saklama süresi (gün)": "Retention period (days)",
    "Süresi dolan, sonuçlandırılmış kayıtlar notları ve geçmişiyle birlikte kalıcı olarak silinir.":
        "Expired, closed reports are permanently deleted together with their notes and history.",
    "Silmenin geri alınamayacağını anlıyorum": "I understand that deletion cannot be undone",
    "Süresi dolan kayıtları sil": "Delete expired reports", "Kayıtlar silindi.": "Reports have been deleted.",
    "İnceleme bilgileri kaydedildi.": "Review details have been saved.", "Değişiklik yapılmadı; bilgiler zaten güncel.": "No changes were made; the information is already up to date.",
    "Değişiklik kaydedilemedi. Lütfen yeniden deneyin.": "Changes could not be saved. Please try again.",
    "Boş not eklenemez.": "A note cannot be empty.", "Not kaydedilemedi.": "The note could not be saved.",
    "Not kaydedildi.": "The note has been saved.", "Açıklama": "Description", "Anonim gönderenin ek bilgileri": "Additional information from the anonymous reporter",

    # Günlük yönetici paneli ve tavsiyeler
    "Günlük Durum Özeti": "Daily Status Summary", "Bugünkü yeni bildirim": "New reports today",
    "Aktif yüksek/acil": "Active high/urgent", "İnceleme bekleyen": "Awaiting review",
    "Acil öncelikli bildirim": "Urgent-priority report", "Yüksek öncelikli bildirim": "High-priority report",
    "Rehberlik için önerilen adımlar": "Suggested guidance steps",
    "Genel kontrol listesidir; okul psikolojik danışmanı ve kurum protokolü tarafından uyarlanmalıdır.":
        "This is a general checklist and should be adapted by the school counsellor and the institution's procedures.",
    "Ekran görüntülerini ve ilgili dijital kayıtları, öğrencinin güvenliğini gözeterek koruyun; içeriği yaymayın.":
        "Preserve screenshots and relevant digital records while safeguarding the student's privacy; do not redistribute the content.",
    "Öğrenciyle güvenli ve gizli bir ortamda bireysel görüşme yapın.":
        "Meet with the student individually in a safe and confidential setting.",
    "Olayın tekrar edip etmediğini ve öğrencinin kendini güvende hissedip hissetmediğini değerlendirin.":
        "Assess whether the incident is recurring and whether the student feels safe.",
    "Gerekli görülürse okulun ilgili koruma ve yönlendirme prosedürlerini izleyin.":
        "If needed, follow the school's relevant safeguarding and referral procedures.",

    # Dashboard / statistics
    "Yüksek veya acil sinyal (açık)": "High or urgent signals (open)", "saati aşan bekleyen": "Awaiting review for over hours",
    "Toplam kayıt": "Total reports", "İstatistikler": "Statistics", "Grafikler yalnızca bu uygulamada kayıtlı bilgileri özetler; okul geneline ilişkin sonuç göstermez.":
        "Charts summarise information recorded in this platform only; they do not represent findings about the whole school.",
    "Henüz kayıt yok. Yeni kayıtlar eklendikçe istatistikler burada görüntülenir.":
        "There are no reports yet. Statistics will appear here as reports are added.",
    "Kayıt sayısı çok az; yüzdeler ve karşılaştırmalar yanıltıcı olabilir, yorum yapmayın.":
        "The number of reports is very small; percentages and comparisons may be misleading and should not be interpreted.",
    "Durum dağılımı": "Status distribution", "Öncelik sinyali dağılımı": "Priority-signal distribution",
    "Olay türü dağılımı": "Incident-type distribution", "Son 30 gün: günlük bildirim": "Daily reports: last 30 days",
    "Süreler kayıt oluşturma ile ilk durum değişikliği / 'Sonuçlandırıldı' arasındaki farktır.":
        "Durations are measured from report creation to the first status change or closure.",
    "Yeni anonim kayıtlar dakika ve saniye hassasiyetinde kaydedilir; eski yuvarlanmış kayıtların geçmiş zamanı geriye dönük kesinleştirilemez.":
        "New anonymous reports are recorded to the minute and second; the original time of older rounded records cannot be reconstructed retrospectively.",
    "Bu dönemde kayıt yok.": "There are no reports for this period.", "Kayıt sayısı": "Number of reports",

    # Destek rehberi
    "DESTEK": "SUPPORT", "Destek rehberi": "Support guide",
    "Zorbalıkla baş etme yolları ve kime nasıl ulaşabileceğin. Bu içerik bilgilendirme amaçlıdır.":
        "Ways to respond to bullying and how to seek help. This content is provided for information only.",
    "Öğrenciler": "Students", "Tanık olanlar": "Witnesses", "Siber zorbalık": "Cyberbullying",
    "Veliler": "Parents and carers", "Öğretmenler": "Teachers", "Bildirimden sonra ne olur?": "What happens after a report?",
    "Zorbalık nedir, ne değildir?": "What is bullying and what is not?", "Yaşıyorsan ne yapabilirsin?": "What can you do if this is happening to you?",
    "Kendine zarar verme düşüncen varsa": "If you are having thoughts of harming yourself",
    "Gördüysen sessiz kalma": "If you witness bullying, do not stay silent",
    "İnternette aşağılanıyor ya da tehdit ediliyorsan": "If you are being humiliated or threatened online",
    "Çocuğunuz zorbalığa uğruyor olabilir": "Your child may be experiencing bullying",
    "Çocuğunuzun zorbalık yaptığı söyleniyorsa": "If you are told that your child has bullied someone",
    "Bildirim geldiğinde": "When a report is received", "Rehberlik içerikleri taslaktır; okul psikolojik danışmanı tarafından onaylanmalıdır.":
        "The guidance content is a draft and must be reviewed by the school's counsellor before use.",
    "Acil bir tehlike varsa beklemeyin:": "If there is immediate danger, do not wait:",

    # Trend and analytics
    "ANALİTİK": "ANALYTICS", "Trend ve ortam analizi": "Trends and setting analysis",
    "Bildirimlerin saat, gün, mekân ve türlere göre dağılımı. Yalnızca bu uygulamadaki kayıtları özetler.":
        "Distribution of reports by time, day, setting and type. This summarises records in this platform only.",
    "Dönem": "Period", "Son": "Last", "gün": "days", "Küçük hücre eşiği (k)": "Small-cell threshold (k)",
    "Çapraz tabloda sayısı bu değerden küçük hücreler kimliksizleştirme için gizlenir.":
        "Cells with counts below this value are suppressed in the cross-tabulation to reduce identification risk.",
    "Ne zaman bildiriliyor?": "When are reports submitted?", "Haftalık eğilim": "Weekly trend",
    "Saate göre (bildirimin yapıldığı saat)": "By hour (time the report was submitted)",
    "Haftanın gününe göre": "By day of the week", "Hangi ortamda, hangi tür?": "Which types are reported in which settings?",
    "Ortama göre": "By setting", "Olay türüne göre": "By incident type", "Ortam haritası (ısı tablosu)": "Setting map (heatmap)",
    "Bildirim sayısındaki artış, olayların arttığını değil bildirme isteğinin arttığını da gösterebilir; ayrım için ayrı bir ölçüm (ör. anket) gerekir. Saat, olayın değil bildirimin saatidir; anonim kayıtlarda zaman saate yuvarlanır.":
        "An increase in reports may reflect a greater willingness to report rather than an increase in incidents; a separate measure (such as a survey) is needed to distinguish these. The time shown is the submission time, not the time of the incident.",
    "yalnızca": "only", "kayıt var; yüzdeler ve eğilimler yanıltıcı olabilir, yorum yapmayın.":
        "reports are available; percentages and trends may be misleading and should not be interpreted.",

    # Privacy, consent, research and app limits
    "GİZLİLİK": "PRIVACY", "Gizlilik ve KVKK paneli": "Privacy and data protection panel",
    "Hangi veri neden toplanıyor, ne kadar saklanıyor ve nasıl siliniyor. Metinler taslaktır.":
        "What data is collected and why, how long it is retained, and how it is deleted. The texts are drafts.",
    "Aydınlatma metni": "Privacy notice", "Veri envanteri": "Data inventory", "Saklama ve imha": "Retention and deletion",
    "Onam akışı (simülasyon)": "Consent flow (simulation)",
    "Köşeli parantezli alanlar doldurulmadan ve hukuk danışmanı onaylamadan yayımlanmamalıdır.":
        "Do not publish this notice until all bracketed fields have been completed and it has been reviewed by legal counsel.",
    "Veri": "Data", "Amaç": "Purpose", "Ne zaman": "When", "Saklama": "Retention", "Not": "Note",
    "Veri minimizasyonu (sistemde uygulananlar)": "Data minimisation (implemented in the platform)",
    "Açık riskler (raporda belirtilmeli)": "Open risks (to be disclosed in the report)",
    "Otomatik/elle imha kuralları": "Automatic and manual deletion rules", "Önizleme: saklama süresi (gün)": "Preview: retention period (days)",
    "günden eski sonuçlanmış kayıt (silinecek)": "closed reports older than days (to be deleted)",
    "Canlı silinecek kayıt sayısı yalnızca yönetici oturumunda görünür.":
        "The live count of reports eligible for deletion is visible only to administrators.",
    "SİMÜLASYON: Bu akış gerçek onam toplamaz, hiçbir veri kaydetmez ve kimseyle iletişime geçmez. Araştırmada onam, okulun resmî kanallarıyla yazılı olarak alınmalıdır.":
        "SIMULATION: This flow does not collect real consent, save any data or contact anyone. For research, consent must be obtained in writing through the school's official channels.",
    "Katılımcının yaş grubu": "Participant age group", "18 yaşından küçük": "Under 18", "18 yaş ve üzeri": "18 or over",
    "18 yaşından küçüklerde gönüllü katılımın yanında veli/yasal temsilcinin bilgilendirilmesi ve izni gerekir.":
        "For participants under 18, a parent or legal guardian must be informed and provide permission in addition to the participant's voluntary agreement.",
    "İleri": "Continue", "Katılımcı bilgilendirmesi": "Participant information", "Bilgilendirmeyi okudum, gönüllü katılıyorum (simülasyon).":
        "I have read the information and agree to participate voluntarily (simulation).",
    "Veli/yasal temsilci bilgilendirmesi ve izni.": "Parent/legal guardian information and permission.",
    "Veli/yasal temsilci izin verdi (simülasyon).": "The parent/legal guardian has given permission (simulation).",
    "18 yaş ve üzeri katılımcı için veli izni gerekmez; kendi gönüllü onamı yeterlidir.":
        "Participants aged 18 or over do not need parental permission; their own voluntary consent is sufficient.",
    "Simülasyon tamamlandı: katılım koşulları sağlandı.": "Simulation complete: participation conditions have been met.",
    "Baştan başla": "Start again", "Gönüllü katılım ve veli onam formu taslağı (.txt)": "Draft voluntary participation and parental consent form (.txt)",
    "Araştırma ve kalite kontrol": "Research and quality assurance", "Otomatik değerlendirme": "Automated evaluation",
    "Elle kontrol listesi": "Manual checklist", "Yöntem ve sınırlılıklar": "Methodology and limitations",
    "Değerlendirmeyi çalıştır": "Run evaluation", "Sonucu JSON olarak indir": "Download result as JSON",
    "Karışıklık matrisi": "Confusion matrix", "Örnek türüne göre doğruluk": "Accuracy by sample type",
    "Kategoriye göre yakalama (duyarlılık)": "Detection by category (recall)", "Yanlış alarm": "False positive",
    "Kaçırılan": "Missed", "İşaretler yalnızca bu oturumda tutulur; resmi test raporu veya bilimsel doğrulama yerine geçmez.":
        "Selections are stored only for this session; they do not replace an official test report or scientific validation.",
    "Bu senaryoyu test ettim": "I have tested this scenario", "Yanlış alarmlar": "False positives", "ve kaçırılanlar": "and missed cases",
    "Algılayıcının sentetik (elle yazılmış, gerçek veri içermeyen) örnek kümesindeki performansını ölçer.":
        "Measures the detector's performance on a synthetic (manually written and containing no real data) sample set.",
    "Platformun işlevleri": "Platform features", "Sınırlar": "Limitations", "Gerçek kullanıma geçmeden önce (kontrol listesi)": "Before real-world use (checklist)",
    "Güvenli kullanım": "Safe use", "Bu dönemde kayıt yok.": "There are no reports in this period.",

    # Static content / privacy notice and research notes
    "Veri sorumlusu": "Data controller", "İletişim": "Contact", "İşlenen veriler": "Data processed",
    "Bildirim formunda yazdığınız olay bilgisi (tür, ortam, zaman, açıklama). Ad, soyad, sınıf, telefon istenmez.":
        "Incident information entered in the report form (type, setting, time and description). First name, last name, class and phone number are not requested.",
    "Amaç": "Purpose", "Hukuki sebep": "Legal basis", "Aktarım": "Data transfers", "Saklama ve imha": "Retention and deletion", "Haklarınız": "Your rights",
    "GÖNÜLLÜ KATILIM VE VELİ ONAM FORMU (TASLAK)": "VOLUNTARY PARTICIPATION AND PARENTAL CONSENT FORM (DRAFT)",
    "Proje:": "Project:", "Okul:": "School:", "Danışman öğretmen:": "Supervising teacher:",
    "Öğrenci:": "Student:", "Veli/Yasal temsilci:": "Parent/Legal guardian:", "Tarih:": "Date:", "İmza:": "Signature:",

    # Enum values shown to end users (database values remain Turkish)
    "İnceleme bekliyor": "Awaiting review", "İnceleniyor": "Under review", "Takip gerekiyor": "Follow-up required",
    "Sonuçlandırıldı": "Closed", "Henüz atanmadı": "Not yet assigned", "Rehberlik birimi": "Guidance service",
    "Okul yönetimi": "School administration", "Öğrenci destek ekibi": "Student support team",
    "Hakaret veya alay": "Insults or mockery", "Tehdit": "Threat", "Dışlama": "Exclusion",
    "Dijital zorbalık": "Cyberbullying", "Fiziksel zorbalık şüphesi": "Suspected physical bullying", "Diğer": "Other",
    "Sınıfta": "In the classroom", "Okul bahçesinde": "In the school yard", "Koridorda": "In the corridor",
    "Sosyal medyada": "On social media", "Mesajlaşmada": "In messaging apps", "Bugün": "Today", "Dün": "Yesterday",
    "Bu hafta": "This week", "Daha önce": "Earlier", "Emin değilim": "Not sure", "Bir kez oldu": "Once",
    "Birkaç kez oldu": "A few times", "Sık sık / sürekli oluyor": "Frequently / ongoing",
    "Sinyal yok": "No signal", "Düşük": "Low", "Orta": "Medium", "Yüksek": "High", "Acil": "Urgent",
    "Sonuçlandırıldı": "Closed", "İnceleme bekliyor": "Awaiting review",

    # Emergency/help and validation messages
    "Yazdıkların için endişeleniyoruz. Şu an güvende değilsen ya da kendini veya başkasını tehlikede hissediyorsan lütfen hemen güvendiğin bir yetişkine, okul rehber öğretmenine ya da yukarıdaki acil hatlara ulaş.":
        "We are concerned about what you have written. If you are not safe right now, or feel that you or someone else may be in danger, contact a trusted adult, your school counsellor or one of the emergency services listed above immediately.",
    "Ek bilgi boş olamaz.": "Additional information cannot be empty.",
    "Bu bildirim sonuçlandırıldığı için ek bilgi eklenemez.": "Additional information cannot be added because this report has been closed.",
    "Ek bilgi yalnızca bildirimin yapıldığı gün eklenebilir.": "Additional information can only be added on the day the report was submitted.",
}



CATALOG.update({
    # Home-page cards and additional interface copy
    "Yaşıyorsan": "If you are experiencing bullying", "Kime anlatabileceğini ve neler yapabileceğini öğren.": "Learn whom you can talk to and what you can do.",
    "Tanık olduysan": "If you witnessed bullying", "Sessiz kalmadan, güvenli şekilde nasıl destek olursun?": "How can you offer support safely instead of staying silent?",
    "Veli ve öğretmenler": "Parents and teachers", "İşaretleri tanı, çocuğu dinle, doğru adımı at.": "Recognise the signs, listen to the child and take appropriate action.",
    "Otomatik eşleşme yalnızca inceleme sırasına yardım eder.": "Automated matching only helps prioritise reports for review.",
    "Yönetici işlemleri kim yaptığıyla kayda geçer.": "Administrator actions are logged with the identity of the person who performed them.",
    "Kime anlatabileceğini ve neler yapabileceğini öğren.": "Learn whom you can talk to and what you can do.",
    "Kayıtları tek bir çalışma alanında görüntüleyin, yönlendirin ve işlem geçmişini takip edin.": "View reports, assign them and follow their activity history in one workspace.",
    "KAYIT YÖNETİMİ": "REPORT MANAGEMENT", "BİLDİRİM": "REPORT", "TAKİP": "TRACKING",
    "Bildirim alındı": "Report received", "Durum": "Status", "Oluşturulma zamanı": "Date submitted",
    "Son güncelleme": "Last updated", "Bu bildirim için ek bilgi": "Additional information for this report",
    "Aynı gün içinde ek bilgi gönderebilirsin.": "You can submit additional information on the same day.",
    "Bildirim alındı. Yetkili kişi henüz incelemeye başlamadı.": "Your report has been received. An authorised reviewer has not started reviewing it yet.",
    "Bildirimin yetkili kişiler tarafından inceleniyor.": "Your report is being reviewed by authorised staff.",
    "İnceleme sürüyor; konu takip edilmeye devam ediyor.": "The review is ongoing and the matter will continue to be monitored.",
    "Bildirimin değerlendirildi ve süreç tamamlandı.": "Your report has been assessed and the process is complete.",
    "Kayıt seçimi": "Report selection", "Seçili kaydı görüntüle": "View selected report",
    "Kayıt ayrıntısı": "Report details", "Açıklama metni": "Report description", "Ek bilgiler": "Additional information",
    "Kayıt tarihi": "Report date", "İşlem": "Action", "Kullanıcı": "User", "Ayrıntı": "Details",
    "İşlemi yapan": "Performed by", "Yazar": "Author", "Birim": "Team", "Atama": "Assignment",
    "Sinyal değerlendirmesi": "Signal assessment", "İlk incelemeye kadar geçen süre": "Time to initial review",
    "Bekleme süresi": "Waiting time", "Saat": "Hour", "Dakika": "Minute", "saat": "hours",
    "Gecikmiş kayıt": "Overdue report", "SLA süresi": "SLA threshold", "SLA": "SLA",
    "Acil bir tehlike varsa beklemeyin:": "If there is immediate danger, do not wait:",
    "Acil Çağrı Merkezi (Polis, Sağlık, Jandarma - 7/24)": "Emergency Call Centre (Police, Medical and Gendarmerie services – 24/7)",
    "ALO Sosyal Destek Hattı (7/24)": "ALO Social Support Line (24/7)", "MEB İletişim Merkezi (MEBİM)": "Ministry of National Education Contact Centre (MEBİM)",
    "İnceleme bekliyor": "Awaiting review", "İnceleniyor": "Under review", "Takip gerekiyor": "Follow-up required",
    "Sonuçlandırıldı": "Closed", "Henüz atanmadı": "Not yet assigned", "Rehberlik birimi": "Guidance service",
    "Okul yönetimi": "School administration", "Öğrenci destek ekibi": "Student support team",
    "Hakaret veya alay": "Insults or mockery", "Fiziksel zorbalık şüphesi": "Suspected physical bullying",
    "Sınıfta": "In the classroom", "Okul bahçesinde": "In the school yard", "Koridorda": "In the corridor",
    "Sosyal medyada": "On social media", "Mesajlaşmada": "In messaging apps", "Bir kez oldu": "Once",
    "Birkaç kez oldu": "A few times", "Sık sık / sürekli oluyor": "Frequently / ongoing",
    "Sinyal yok": "No signal", "Düşük": "Low", "Orta": "Medium", "Yüksek": "High", "Acil": "Urgent",
    "Tüm durumlar": "All statuses", "Tüm birimler": "All teams", "Tüm öncelikler": "All priorities",
    "Kimlik bilgisi belirtilmiş": "Identifying details provided", "Anonim bildirim": "Anonymous report",
    "Kimlik bilgili bildirim": "Report with identifying details", "Kayıt bulunamadı.": "No report was found.",
    "Kayıt güncellenemedi.": "The report could not be updated.", "İşlem tamamlandı.": "Action completed.",
    "İnceleme için önerilen adımlar": "Recommended review steps", "Rehberlik servisi için not": "Guidance service note",
    "Bu öneriler karar veya tanı değildir; yetkili uzman değerlendirmesinin yerine geçmez.":
        "These suggestions are not decisions or diagnoses and do not replace assessment by an authorised professional.",
    "Siber zorbalıkta": "For cyberbullying", "Akran dışlamasında": "For peer exclusion",
    "Ekran görüntülerini, bağlantıları ve tarih bilgilerini güvenli biçimde muhafaza edin; içerikleri yaymayın.":
        "Preserve screenshots, links and date information securely; do not redistribute the content.",
    "Öğrenciyle bireysel ve güvenli bir görüşme yapın; öğrenciyi suçlayıcı sorulardan kaçının.":
        "Arrange an individual meeting in a safe setting and avoid questions that blame the student.",
    "Olayın tekrar sıklığını, güç dengesizliğini ve öğrencinin güvenlik ihtiyacını değerlendirin.":
        "Assess recurrence, power imbalance and the student's safeguarding needs.",
    "Gerekli durumlarda okulun koruma, bilgilendirme ve yönlendirme prosedürlerini izleyin.":
        "Where necessary, follow the school's safeguarding, notification and referral procedures.",
    "Destek içerikleri bilgilendirme amaçlıdır; okulun rehberlik ve koruma prosedürlerinin yerini almaz.":
        "Support content is for information only and does not replace the school's counselling and safeguarding procedures.",
    "Zorbalık; bilerek yapılan, tekrar eden ve güç dengesizliği olan davranıştır (alay, tehdit, dışlama, fiziksel saldırı, internette aşağılama).":
        "Bullying is intentional, repeated behaviour involving a power imbalance (such as mockery, threats, exclusion, physical aggression or online humiliation).",
    "Arkadaşlar arasındaki tek seferlik tartışma genellikle zorbalık sayılmaz; ama seni korkutuyor ya da üzüyorsa yine de anlatmaya değer.":
        "A one-off disagreement between friends is not usually considered bullying. However, if it frightens or upsets you, it is still worth talking about.",
    "Olanlar senin suçun değildir.": "What is happening is not your fault.",
    "Güvendiğin bir yetişkine (rehber öğretmen, sınıf öğretmeni, aile) olanı anlat.":
        "Tell a trusted adult, such as a school counsellor, classroom teacher or family member, what happened.",
    "Cevap vermek zorunda değilsin; güvenli bir yere git, yanında birileriyle ol.":
        "You do not have to respond. Move to a safe place and stay with someone you trust.",
    "Mesaj ve ekran görüntülerini sakla, silme; yetişkine gösterirsin.":
        "Keep messages and screenshots; do not delete them. You can show them to a trusted adult.",
    "Bu sitedeki anonim formu kullanabilirsin; ama form acil durum hattı değildir.":
        "You can use the anonymous form on this platform, but it is not an emergency service.",
    "Bu düşünceleri tek başına taşımak zorunda değilsin. Hemen güvendiğin bir yetişkine söyle.":
        "You do not have to deal with these thoughts alone. Tell a trusted adult immediately.",
    "Acil tehlikede 112'yi, destek için 183'ü arayabilirsin.": "In an emergency, call 112. For support, you can call 183.",
    "Zorbalığa gülmek ya da paylaşmak onu büyütür. Katılmamak bile bir destektir.":
        "Laughing at or sharing bullying makes it worse. Choosing not to take part is already a form of support.",
    "Güvenliysen mağdurun yanına git, yalnız olmadığını hissettir.":
        "If it is safe, approach the person affected and let them know they are not alone.",
    "Müdahale etmek tehlikeliyse bir yetişkine haber ver. Bu ‘çaksıl’ değil, arkadaşını korumaktır.":
        "If intervening could be dangerous, tell an adult. This is not 'snitching'; it is helping to keep someone safe.",
    "Anonim form ile adını vermeden bildirebilirsin.": "You can submit an anonymous report without giving your name.",
    "Cevap verme, kişiyi engelle, platformda şikâyet et.": "Do not respond. Block the person and report the content on the platform.",
    "Kanıtları (ekran görüntüsü, tarih, hesap adı) sakla.": "Keep relevant evidence (screenshots, dates and account names).",
    "Şifrelerini kimseyle paylaşma, gizlilik ayarlarını gözden geçir.": "Do not share your passwords and review your privacy settings.",
    "Sık görülen işaretler: okula gitmek istememe, uyku/iştah değişikliği, eşya kaybı, çekingenlik, telefona karşı aşırı tedirginlik. Bunlar tek başına kanıt değildir.":
        "Possible signs include reluctance to attend school, changes in sleep or appetite, missing belongings, withdrawal or unusual anxiety about a phone. These signs alone are not proof of bullying.",
    "Önce sakin kalın, dinleyin; suçlamayın, ‘sen de karşılık ver’ demeyin.":
        "First, stay calm and listen. Do not blame the child or tell them to retaliate.",
    "Olayı tarih ve ayrıntılarıyla yazın; okul rehberlik servisiyle görüşün.":
        "Record the incident with dates and relevant details, and contact the school's guidance service.",
    "Savunmaya geçmeden dinleyin; davranışın başkasına verdiği zararı konuşun.":
        "Listen without becoming defensive and discuss the impact the behaviour has had on others.",
    "Okul rehberlik servisiyle birlikte çalışın; cezadan çok davranış değişikliğini hedefleyin.":
        "Work with the school's guidance service and focus on changing behaviour rather than punishment alone.",
    "Kaydı yalnızca insan olarak değerlendirin; otomatik sinyal kanıt veya karar değildir.":
        "Assess the report through human review only; an automated signal is not evidence or a decision.",
    "Kaynağı belirlemeye çalışmayın; bildirimin anonimliğini koruyun.":
        "Do not try to identify the reporter; protect the anonymity of the report.",
    "Şüpheli öğrencinin yanlış suçlanma riskini gözetin; süreci rehberlik servisi ve okul yönetimiyle yürütün.":
        "Be mindful of the risk of wrongly accusing a student; follow the process with the guidance service and school administration.",
    "Acil sinyal veya doğrudan zarar riski varsa okulun acil durum protokolünü uygulayın.":
        "If an urgent signal or immediate risk of harm is identified, follow the school's emergency protocol.",
    "Formu gönderirsin ve gizli takip kodunu alırsın.": "You submit the form and receive a private tracking code.",
    "Kayıt, yetkili kişiler (rehberlik / okul yönetimi) tarafından incelenir; bunu bir insan yapar.":
        "The report is reviewed by authorised staff (the guidance service or school administration); a person makes the assessment.",
    "Takip koduyla durumu görürsün. Sistemde mesajlaşma yoktur; bu yüzden acil durumlarda bir yetişkine ulaş.":
        "You can check the status using your tracking code. Messaging is not available, so contact an adult in an emergency.",
    "Bildirim sayısındaki artış, olayların arttığını değil bildirme isteğinin arttığını da gösterebilir; ayrım için ayrı bir ölçüm (ör. anket) gerekir.":
        "An increase in reports may reflect greater willingness to report rather than an increase in incidents; a separate measure (such as a survey) is needed to distinguish the two.",
    "Saat, olayın değil bildirimin saatidir; anonim kayıtlarda zaman saate yuvarlanır.":
        "The time shown is when the report was submitted, not when the incident occurred.",
    "SİMÜLASYON:": "SIMULATION:", "Bu akış gerçek onam toplamaz, hiçbir veri kaydetmez ve kimseyle iletişime geçmez.":
        "This flow does not collect real consent, save data or contact anyone.",
    "Araştırmada onam, okulun resmî kanallarıyla yazılı olarak alınmalıdır.":
        "For research, consent must be obtained in writing through the school's official channels.",
    "Bu aşamadan sonra katılımcı bildirim formunu kullanabilir.": "After this step, the participant may use the report form.",
    "Katılımcıdan": "The participant is not asked for", "ad, sınıf, telefon istenmez": "a name, class or phone number",
    "onay kaydı bu uygulamada tutulmaz, okulda yazılı saklanır.": "; the consent record is not stored in this platform and must be retained in writing by the school.",
    "Gerçek sistemde bu adım, okulun resmî iletişim kanalıyla ve yazılı olarak yürütülür; bu uygulama veli iletişim bilgisi toplamaz.":
        "In a live system, this step must be handled in writing through the school's official communication channel. This platform does not collect parent contact details.",
    "Açıklamadaki telefon, T.C. kimlik numarası, e-posta ve IBAN'ı otomatik maskeler.":
        "Automatically masks phone numbers, Turkish national ID numbers, email addresses and IBANs in report descriptions.",
    "Takip koduyla durum sorgulamaya ve (anonim kayıtlarda, aynı gün) ek bilgi eklemeye izin verir.":
        "Allows users to check report status and, for anonymous reports, add further information on the same day using a tracking code.",
    "Yönetici girişinden sonra kayıtları listeler; durum/birim günceller; not ve işlem geçmişi tutar.":
        "After administrator sign-in, lists reports, updates statuses and assigned teams, and maintains notes and an activity history.",
    "Girişleri ve yönetici işlemlerini denetim kaydında saklar; CSV dışa aktarım ve saklama süresi temizliği sunar.":
        "Maintains an audit log of sign-ins and administrator actions, provides CSV export and supports retention-based deletion.",
    "İfade eşleşmelerini yalnızca insan incelemesi için öncelik sinyali olarak gösterir.":
        "Displays phrase matches only as priority signals to support human review.",
    "Gerçek bir okul veya rehberlik servisine bağlı değildir; acil yardım ya da resmi bildirim hizmeti değildir.":
        "It is not connected to a real school or guidance service and is not an emergency or official reporting service.",
    "Zorbalık hakkında otomatik kesin karar vermez; sinyaller yanlış alarm üretebilir ve olayları kaçırabilir.":
        "It does not make definitive automated decisions about bullying; signals may produce false positives or miss incidents.",
    "Tek yönetici hesabı kurumsal kimlik doğrulamanın (SSO/2FA) yerini tutmaz.":
        "A single administrator account is not a substitute for institutional authentication (SSO/2FA).",
    "Yerel SQLite dosyasının bulut ortamında kalıcı olacağı garanti edilmez; yedekleme planı gerekir.":
        "Persistence of a local SQLite file in a cloud environment is not guaranteed; a backup plan is required.",
    "Hatalı giriş ve zaman aşımı korumaları vardır, ancak bu bir güvenlik denetiminden geçmemiştir.":
        "Failed-login and session-timeout protections are implemented, but the platform has not undergone a security audit.",
    "Veri sorumlusunun belirlenmesi, aydınlatma metni, hukuki sebep/veli onayı, saklama-imha politikası":
        "Determine the data controller, prepare a privacy notice, establish the legal basis and parental consent requirements, and define retention and deletion policies",
    "Çocuk verisi ve olası yurt dışı sunucu kullanımı ayrıca hukuki değerlendirme gerektirir.":
        "The processing of children's data and any use of servers outside the country require separate legal assessment.",
    "Kişi bazlı hesaplar, rol ayrımı, iki aşamalı doğrulama, parola özeti":
        "Individual accounts, role-based access, two-factor authentication and password hashing",
    "HTTPS, şifreli yedek, günlüklerin korunması, bağımsız güvenlik testi.":
        "HTTPS, encrypted backups, log protection and independent security testing.",
    "Kayıtları kimin, ne kadar sürede inceleyeceği, acil durum protokolü ve rehberlik servisiyle iş akışı.":
        "Define who reviews reports and within what timeframe, the emergency protocol and the workflow with the guidance service.",
    "Sonuçlar iyimserdir ve genellenemez.": "The results are optimistic and cannot be generalised.",
    "Bilimsel geçerlik için bağımsız, etik onaylı ve en az iki değerlendiricinin etiketlediği bir veri kümesi gerekir.":
        "Scientific validity requires an independent, ethically approved dataset labelled by at least two evaluators.",
    "İşaretler yalnızca bu oturumda tutulur; resmi test raporu veya bilimsel doğrulama yerine geçmez.":
        "Selections are stored only for this session and do not replace an official test report or scientific validation.",
    "Açıklama yalnızca boşluk veya noktalama işaretlerinden oluşamaz.": "The description cannot consist only of spaces or punctuation.",
    "Kayıt ara": "Search reports", "Kayıt sayısı": "Number of reports", "Örnek sayısı": "Sample size",
    "Kesinlik (precision)": "Precision", "Duyarlılık (recall)": "Recall", "Doğruluk": "Accuracy",
    "Yakalanan": "Detected", "Oran": "Rate", "Örnek": "Samples", "Doğru": "Correct",
    "Saklama süresi (gün)": "Retention period (days)", "Süresi dolan kayıtları sil": "Delete expired reports",
    "Bu kodla eşleşen bir kayıt bulunamadı. Kodu kontrol edip tekrar dene.": "No report was found for this code. Check the code and try again.",
})


CATALOG.update({
    "Sınırlar": "Limitations", "Sıralama": "Sort order", "**Açıklama**": "**Description**",
    "Kayıt oluşturulamadı. Lütfen daha sonra tekrar dene.": "The report could not be created. Please try again later.",
    "Sınırlılıklar": "Limitations", "Süreç": "Process", "İşaretlenen test:": "Tests checked:",
    "OTURUM": "SESSION", "Sinyal:": "Signal:", "saat bekliyor": "hours waiting",
    "Günlük durum özeti": "Daily status summary", "Yeni bildirim": "New report",
    "24 saati aşan bekleyen": "Awaiting review for over 24 hours",
    "Yüksek veya acil sinyal (açık)": "High or urgent signals (open)",
    "İlk inceleme": "Initial review", "Aktif takip": "Active follow-up",
    "24 saati aşan bekleyen": "Awaiting review for over 24 hours",
    "Öncelik (yüksekten)": "Priority (highest first)",
    "{n} kayıt": "{n} reports",
    "Bu hak, tarayıcında saklanan rastgele bir kodla uygulanır; kimliğinle ilişkili değildir.":
        "This limit is enforced using a random code stored in your browser; it is not linked to your identity.",
    "Telefon, adres gibi bilgileri yazmana gerek yok; yalnızca olayı anlat.":
        "You do not need to provide a phone number or address; describe only what happened.",
    "Ad, telefon gibi bilgileri yazma.": "Do not include names, phone numbers or similar identifying details.",
    "Ek bilgin eklendi. Bugün": "Your additional information has been added. You have",
    "ek bilgi hakkın kaldı.": "additional entries remaining today.",
    "Yönetici girişi başarılı.": "Administrator sign-in successful.",
    "Yönetici bilgileri ayarlanmamış. .streamlit/secrets.toml (veya Streamlit Cloud > Settings > Secrets) içindeki [admin] bölümünü yapılandırın.":
        "Administrator credentials have not been configured. Set up the [admin] section in .streamlit/secrets.toml (or Streamlit Cloud > Settings > Secrets).",
    "Lütfen": "Please", "tekrar deneyin.": "try again.",
    "Sınıf:": "Class:", "Ad soyad:": "Full name:", "Belirtilmedi": "Not provided",
    "Tekrarlanma": "Frequency", "Yaklaşık zaman": "Approximate time", "Bildirim türü": "Report type",
    "SEÇİLİ KAYIT": "SELECTED REPORT", "TAKİP KODU": "TRACKING CODE", "KAYIT YÖNETİMİ": "REPORT MANAGEMENT",
    "İşlem geçmişi": "Activity history", "Anonim gönderenin ek bilgileri": "Additional information from the anonymous reporter",
    "İnceleme bilgileri kaydedildi.": "Review details have been saved.", "Not eklendi.": "Note added.",
    "CSV dışa aktarım": "CSV export", "kimlik dahil": "identifiers included", "kimlik hariç": "identifiers excluded",
    "Kayıt sayısı": "Number of reports", "En çok bildirilen ortam": "Most frequently reported setting",
    "En çok bildirilen tür": "Most frequently reported type", "Ne zaman bildiriliyor?": "When are reports submitted?",
    "Yalnızca": "Only", "kayıt var; yüzdeler ve eğilimler yanıltıcı olabilir, yorum yapmayın.":
        "reports are available; percentages and trends may be misleading and should not be interpreted.",
    "Bu dönemde kayıt yok.": "There are no reports for this period.",
    "‘·’ ile gösterilen": "Cells marked with '·'", "hücre (toplam": "are suppressed (a total of",
    "kayıt)": "reports)", "'den az olduğu için gizlendi.": "were hidden because their count is below the threshold.",
    "Çapraz tabloda sayısı bu değerden küçük hücreler kimliksizleştirme için gizlenir.":
        "Cells with counts below this threshold are suppressed in the cross-tabulation to reduce identification risk.",
    "Zorbalıkla baş etme yolları ve kime nasıl ulaşabileceğin. Bu içerik bilgilendirme amaçlıdır.":
        "Ways to respond to bullying and how to seek help. This content is provided for information only.",
    "Özel fotoğrafın izinsiz paylaşılıyorsa ya da paylaşılmakla tehdit ediliyorsan hemen bir yetişkine söyle; bu ciddi bir durumdur ve suç oluşturabilir.":
        "If a private image is shared without your permission or someone threatens to share it, tell a trusted adult immediately. This is serious and may be a criminal offence.",
    "Çocuğunuzun kendine zarar verme düşüncesi olabileceğinden endişeleniyorsanız 112'yi arayın.":
        "If you are concerned that your child may be at risk of harming themselves, contact emergency services on 112.",
    "Müdahale etmek tehlikeliyse bir yetişkine haber ver. Bu ‘çaksıl’ değil, arkadaşını korumaktır.":
        "If intervening could be unsafe, tell an adult. This is not 'snitching'; it is helping to protect someone.",
    "**Veri sorumlusu:**": "**Data controller:**", "**İletişim:**": "**Contact:**",
    "**İşlenen veriler:**": "**Data processed:**", "**Amaç:**": "**Purpose:**", "**Hukuki sebep:**": "**Legal basis:**",
    "**Aktarım:**": "**Data transfers:**", "**Saklama ve imha:**": "**Retention and deletion:**", "**Haklarınız:**": "**Your rights:**",
    "[OKUL ADI / KURUM]": "[SCHOOL / INSTITUTION NAME]", "[KVKK İLETİŞİM ADRESİ]": "[DATA PROTECTION CONTACT ADDRESS]",
    "Bildirim formunda yazdığınız olay bilgisi (tür, ortam, zaman, açıklama). Ad, soyad, sınıf, telefon istenmez.":
        "Incident information entered in the report form (type, setting, time and description). First name, last name, class and phone number are not requested.",
    "Açıklamadaki telefon, T.C. kimlik no, e-posta ve IBAN otomatik maskelenir.":
        "Phone numbers, Turkish national ID numbers, email addresses and IBANs in descriptions are automatically masked.",
    "Akran zorbalığı bildirimlerinin yetkili kişilerce incelenmesi ve öğrencinin korunması. Veriler başka amaçla kullanılmaz.":
        "To enable authorised staff to review peer-bullying reports and safeguard students. Data is not used for other purposes.",
    "Otomatik sinyal yalnızca inceleme sırasına yardımcıdır; hiçbir karar otomatik verilmez.":
        "Automated signals only help prioritise reviews; no decisions are made automatically.",
    "[HUKUK DANIŞMANI BELİRLEYECEK: ör. KVKK m.5/2 ilgili bendi / açık rıza / veli onamı]":
        "[TO BE DETERMINED BY LEGAL COUNSEL: e.g. applicable provision of KVKK Article 5(2) / explicit consent / parental consent]",
    "Veriler yetkili okul personeli dışında paylaşılmaz.": "Data is not shared outside authorised school personnel.",
    "[BARINDIRMA YERİ VE YURT DIŞI AKTARIM DURUMU YAZILACAK]": "[SPECIFY HOSTING LOCATION AND WHETHER DATA IS TRANSFERRED ABROAD]",
    "Sonuçlanan kayıtlar [180] gün sonra silinir; günlük cihaz kodu özeti 1 gün sonra silinir.":
        "Closed reports are deleted after [180] days; the daily device-token hash is deleted after one day.",
    "KVKK m.11 kapsamındaki haklar için yukarıdaki adrese başvurabilirsiniz.":
        "You may contact the address above to exercise your rights under Article 11 of the Turkish Personal Data Protection Law (KVKK).",
    "Anonim bildirimlerde bildirimi size bağlamak mümkün olmadığından bazı haklar (erişim, düzeltme) teknik olarak kullanılamayabilir.":
        "For anonymous reports, it may not be technically possible to link a report to you, so certain rights (such as access and rectification) may not be exercisable.",
    "Olay açıklaması (maskelenmiş)": "Incident description (masked)", "Bildirimi incelemek": "Reviewing the report",
    "Bildirim gönderildiğinde": "When the report is submitted", "Sonuç + [180] gün": "Closure + [180] days",
    "Serbest metin; üçüncü kişilerin adı geçebilir, maskeleme adları yakalamaz.":
        "Free text; third-party names may appear and are not detected by the masking layer.",
    "Olay türü, ortam, zaman, tekrar": "Incident type, setting, time and frequency", "İstatistik ve önceliklendirme": "Statistics and prioritisation",
    "Seçmeli alanlar.": "Structured selection fields.", "Takip kodu": "Tracking code", "Durum sorgulama, ek bilgi": "Status checks and additional information",
    "Rastgele; kimlikle ilişkisiz.": "Randomly generated; not linked to an identity.", "Kayıtla birlikte": "Retained with the report",
    "Cihaz jetonu özeti (SHA-256)": "Device-token hash (SHA-256)", "Günlük bildirim hakkı": "Daily reporting limit",
    "1 gün": "1 day", "Rapora bağlanmaz.": "Not linked to the report.", "Ek bilgiler": "Additional information",
    "Aynı bildirimi tamamlamak": "Supplementing the same report", "Takip koduyla, aynı gün": "Using the tracking code, on the same day",
    "En çok 3 ek.": "Maximum of 3 entries.", "Öncelik sinyali / kategoriler": "Priority signal / categories",
    "Kayıt anında (otomatik)": "At the time of submission (automatically)", "Kural tabanlı; karar değildir.": "Rule-based; not a decision.",
    "İnceleme notları, işlem geçmişi": "Review notes and activity history", "Hesap verebilirlik": "Accountability",
    "Yönetici işlemlerinde": "During administrator actions", "Kim yaptı bilgisi içerir.": "Includes information about who performed the action.",
    "Denetim kaydı, giriş denemeleri": "Audit log and sign-in attempts", "Yönetici girişlerinde": "During administrator sign-ins",
    "Giriş denemeleri 7 gün; denetim kaydı: TANIMSIZ": "Sign-in attempts: 7 days; audit-log retention: UNDEFINED",
    "Denetim kaydı için saklama süresi karar verilmeli.": "A retention period must be defined for the audit log.",
    "Ad, soyad, sınıf (yalnızca eski kayıtlar)": "First name, last name and class (legacy records only)",
    "Formda artık istenmiyor": "No longer requested in the form", "Eski kayıtlarla birlikte": "Retained with legacy records",
    "Eski kimlikli kayıtlar varsa silinmeli veya gözden geçirilmeli.": "Legacy reports containing identifying information should be reviewed or deleted.",
    "- Formda ad, sınıf, telefon istenmez.": "- The form does not request a name, class or phone number.",
    "- Açıklamadaki T.C. no, telefon, e-posta, IBAN maskelenir; ham metin saklanmaz.":
        "- Turkish ID numbers, phone numbers, email addresses and IBANs in descriptions are masked; the unmasked text is not stored.",
    "- Anonim kayıt ve ek bilgi zamanı saate yuvarlanır.": "- Anonymous report and additional-information timestamps are recorded to the second.",
    "- Cihaz jetonu yalnızca özet olarak ve 1 gün saklanır; rapora bağlanmaz.": "- Only a hash of the device token is retained for one day; it is not linked to a report.",
    "- Öğrenci sorgusunda açıklama, not ve değerlendirme gösterilmez.": "- Student status checks do not display descriptions, notes or assessments.",
    "- Serbest metin kişileri dolaylı tanıtabilir; ‘tam anonim’ yerine ‘kimliksizleştirilmiş’ demek daha doğrudur.":
        "- Free text may indirectly identify people; 'de-identified' is more accurate than 'fully anonymous'.",
    "- Üçüncü kişilerin (şüpheli öğrenci) adı metinde geçebilir; maskeleme adları yakalamaz.":
        "- Third-party names (including a student who is the subject of a report) may appear in text; the masking layer does not detect names.",
    "- Barındırma yeri ve olası yurt dışı aktarım hukuken değerlendirilmelidir.":
        "- Hosting location and any potential international data transfer must be assessed legally.",
    "- Sonuçlanan kayıtlar: ‘Bildirim inceleme → Dışa aktarım ve saklama’ ekranından, seçilen gün sonunda notları ve ek bilgileriyle silinir (varsayılan 180).":
        "- Closed reports: deleted with their notes and additional information from 'Report review → Export and retention' after the selected retention period (default: 180 days).",
    "- Cihaz jetonu özeti: ertesi gün silinir.": "- Device-token hash: deleted the following day.",
    "- Giriş denemeleri: 7 gün.": "- Sign-in attempts: 7 days.",
    "- Denetim kaydı: saklama süresi tanımlı değil; karar verilmeli.": "- Audit log: no retention period is currently defined; one must be set.",
    "GÖNÜLLÜ KATILIM VE VELİ ONAM FORMU (TASLAK)": "VOLUNTARY PARTICIPATION AND PARENTAL CONSENT FORM (DRAFT)",
    "1. Amaç: Bildirim sisteminin kullanılabilirliğini ve kural tabanlı sinyalin başarımını değerlendirmek.":
        "1. Purpose: To evaluate the usability of the reporting system and the performance of rule-based signals.",
    "2. Katılım gönüllüdür; istediğiniz zaman, gerekçe göstermeden ayrılabilirsiniz.":
        "2. Participation is voluntary; you may withdraw at any time without giving a reason.",
    "3. Toplanan veri: Formdaki olay bilgisi (ad, soyad, telefon toplanmaz). Gerçek kişileri tanıtan bilgi yazmayınız.":
        "3. Data collected: Incident information entered in the form (names and phone numbers are not collected). Do not enter information that identifies real people.",
    "4. Saklama: [SÜRE]. Veriler yalnızca araştırma ekibi ve yetkili okul personelince görülür.":
        "4. Retention: [PERIOD]. Data is accessible only to the research team and authorised school staff.",
    "5. Riskler: Zorbalık konusu bazı öğrencileri üzebilir; bu durumda rehberlik servisine başvurabilirsiniz.":
        "5. Risks: Discussing bullying may be upsetting for some students; you may contact the school guidance service if needed.",
    "Öğrenci: Bilgilendirildim, gönüllü katılıyorum.": "Student: I have been informed and agree to participate voluntarily.",
    "Veli/Yasal temsilci: Bilgilendirildim, çocuğumun katılımına izin veriyorum.":
        "Parent/Legal guardian: I have been informed and give permission for my child's participation.",
    "18 yaşından küçük": "Under 18", "18 yaş ve üzeri": "18 or over", "Pzt": "Mon", "Sal": "Tue", "Çar": "Wed",
    "Per": "Thu", "Cum": "Fri", "Cmt": "Sat", "Paz": "Sun",
    "Tüm durumlar": "All statuses", "Öncelik (yüksekten)": "Priority (highest first)",
    "Dışa aktarım ve saklama": "Export and retention", "Denetim kaydı": "Audit log", "Kayıtlar": "Reports",
    "Yönetici:": "Administrator:", "Acil:": "Emergency:", "Sürüm 2.0": "Version 2.0",
    "Örnek": "Samples", "Tür": "Type", "Kategori": "Category", "Gerçekte sinyal var": "Signal present in ground truth",
    "Gerçekte sinyal yok": "No signal in ground truth", "Sinyal verildi": "Signal raised", "Sinyal verilmedi": "No signal raised",
    "Sinyal": "Signal", "Yanlış alarmlar": "False positives", "Kaçırılanlar": "Missed cases",
})


CATALOG.update({
    "Varsa ilgili mesaj, bağlantı ve ekran görüntülerini güvenli biçimde muhafaza edin; gereksiz kişilerle paylaşmayın.":
        "If available, preserve relevant messages, links and screenshots securely; do not share them with unnecessary parties.",
    "Öğrenciyle ayrı ve gizliliği koruyan bireysel görüşme yapın.":
        "Hold an individual meeting with the student in a way that protects their privacy.",
    "Okul prosedürüne uygun platform bildirim adımlarını ve güvenlik riskini değerlendirin.":
        "Assess the platform-reporting steps and safety risks in line with school procedures.",
    "Gerekirse veli ve okul yönetimiyle yetkili süreç üzerinden koordinasyon sağlayın.":
        "Where appropriate, coordinate with the parent or carer and school administration through authorised procedures.",
    "Öğrenciyi suçlamadan, yönlendirici olmayan sorularla bireysel olarak dinleyin.":
        "Listen to the student individually, without blame and using non-leading questions.",
    "Olayın tekrarı, güç dengesi ve farklı ortamlardaki etkisini değerlendirin.":
        "Assess recurrence, power dynamics and the impact across different settings.",
    "Sınıf ortamını ve akran ilişkilerini gözlemleyin; öğrencileri topluluk önünde etiketlemeyin.":
        "Observe the classroom environment and peer relationships; do not label students in front of others.",
    "Destek planını rehberlik servisi ve okulun ilgili ekibiyle birlikte belirleyin.":
        "Develop a support plan with the guidance service and the relevant school team.",
    "Önce öğrencilerin o anki güvenliğini değerlendirin; yakın tehlikede okulun acil durum protokolünü uygulayın.":
        "First assess the students' immediate safety; if there is imminent danger, follow the school's emergency protocol.",
    "Tarafları tek başına yüzleştirmeyin; ilgili yetişkinleri ve okul yönetimini bilgilendirin.":
        "Do not arrange a confrontation between the parties on your own; inform the relevant adults and school administration.",
    "Görüşmeleri ayrı ve gizli yürütün; beyanları yorum eklemeden kaydedin.":
        "Conduct interviews separately and confidentially; record statements without adding interpretation.",
    "Öğrenciyi bireysel ve yargılamadan dinleyin; olayın sıklığını, bağlamını ve etkisini netleştirin.":
        "Listen to the student individually and without judgement; clarify the frequency, context and impact of the incident.",
    "Tanık beyanlarını ayrı alın; otomatik sinyali tek başına kanıt kabul etmeyin.":
        "Take witness statements separately; do not treat an automated signal as evidence on its own.",
    "Güvenli sınıf iklimi ve davranış değişikliği için takip planı oluşturun.":
        "Create a follow-up plan to support a safe classroom climate and positive behaviour change.",
    "Metinde aktarma/alıntı ifadeleri var; eşleşen söz bildirimi yapanın kendi sözü olmayabilir.":
        "The text contains reported-speech or quotation markers; the matched phrase may not be the reporter's own words.",
    "Olumsuzlama ifadeleri var; eşleşme olumsuz bağlamda kullanılmış olabilir.":
        "Negation markers are present; the matched phrase may have been used in a negative context.",
    "Şaka/mizah ifadeleri var; bağlam insan tarafından değerlendirilmelidir.":
        "Humour or joking markers are present; the context should be assessed by a human reviewer.",
    "Ad soyad:": "Full name:", "Sınıf:": "Class:", "Açıklama bulunmuyor.": "No description is available.",
    "İşaretlenen test:": "Tests checked:", "Gizli takip kodun.": "Your private tracking code.",
    "Durumu ve ek bilgi eklemeyi bu kodla yaparsın.": "Use this code to check its status and add further information.",
    "Not al ya da ekran görüntüsü al; kod kaybolursa yeniden oluşturulamaz:": "Save this code or take a screenshot; it cannot be recovered if lost:",
    "ek bilgi": "additional information", "GECİKMİŞ": "OVERDUE", "24 saati aşan bekleyen": "Awaiting review for over 24 hours",
    "İlk inceleme": "Initial review", "Aktif takip": "Active follow-up", "Sonuçlandırıldı": "Closed",
    "Sinyal: ": "Signal: ", "SEÇİLİ KAYIT": "SELECTED REPORT", "TAKİP KODU": "TRACKING CODE",
    "Bu takip kodu yalnızca uygulamadaki kaydı tanımlar.": "This tracking code identifies only the report in this platform.",
    "Rehberlikle mesajlaşma yoktur; yalnızca bildirimin durumunu görürsün.": "Messaging with the guidance service is not available; you can only view the report status.",
    "Girişler, başarısız denemeler, dışa aktarımlar ve silme işlemleri burada izlenir.":
        "Sign-ins, failed attempts, exports and deletion actions are monitored here.",
    "Varsayılan olarak kapalıdır (veri minimizasyonu).": "Disabled by default (data minimisation).",
    "Küçük hücre eşiği (k)": "Small-cell threshold (k)", "Küçük hücre": "Small cell",
    "Süreler kayıt oluşturma ile ilk durum değişikliği / 'Sonuçlandırıldı' arasındaki farktır.":
        "Durations are measured from report creation to the first status change or closure.",
    "Sinyal kanıt veya karar değildir; bağlamı anlayamaz. Eşleşme olmaması da sorun olmadığı anlamına gelmez.":
        "A signal is not evidence or a decision and cannot understand context. The absence of a match does not mean there is no issue.",
    "Bu sürüm gerçek bir yapay zekâ modeli değil, kural tabanlı sinyal ve basit metin kalite kontrolü kullanır.":
        "This version is not an AI model; it uses rule-based signals and a basic text-quality check.",
    "Günlük cihaz kodu özeti 1 gün sonra silinir.": "The daily device-token hash is deleted after one day.",
    "Anonim kayıt ve ek bilgi zamanı dakika ve saniye hassasiyetinde kaydedilir.":
        "Anonymous report and additional-information timestamps are recorded to the second.",
    "- Anonim kayıt ve ek bilgi zamanı saate yuvarlanır.": "- Anonymous report and additional-information timestamps are recorded to the second.",
    "zaman saate yuvarlanır": "timestamps are recorded to the second",
    "zaman dakika ve saniye hassasiyetinde kaydedilir": "timestamps are recorded to the second",
})


CATALOG.update({
    "Bildirimin alındı. Yetkili kişi henüz incelemeye başlamadı.": "Your report has been received. An authorised reviewer has not started reviewing it yet.",
    "Bildirimin yetkili kişiler tarafından inceleniyor.": "Your report is being reviewed by authorised staff.",
    "İnceleme sürüyor; konu takip edilmeye devam ediyor.": "The review is ongoing and the matter will continue to be monitored.",
    "Bildirimin değerlendirildi ve süreç tamamlandı.": "Your report has been assessed and the process is complete.",
    "aktif yüksek/acil öncelikli kayıt var. Yetkili personel tarafından insan incelemesi gerekir.":
        "active high/urgent-priority reports require human review by authorised staff.",
    "Formda ad/soyad/sınıf istenmemeli ve kaydedilmemeli.": "The form must not request or store first name, last name or class.",
    "Her kayıt benzersiz ve tahmin edilmesi zor bir kod üretmeli.": "Each report must generate a unique, hard-to-guess code.",
    "Girişsiz, inceleme/istatistik/denetim kayıtları görünmemeli.": "Review, statistics and audit records must not be visible without signing in.",
    "Değişiklik kaydedilmeli, geçmişe işlemi yapanla birlikte eklenmeli.": "Changes must be saved and added to the activity history with the actor identified.",
    "Not kaydedilmeli; yazar bilgisiyle ilgili kayıtta görünmeli.": "Notes must be saved and displayed in the relevant report with the author's details.",
    "Açıklama veya onay yoksa kayıt oluşturulmamalı; yazılan metin silinmemeli.": "A report must not be created without a description or confirmation; entered text must not be erased.",
    "Yeni kurulumda örnek kayıt olmamalı; yeniden başlatmada kayıt silinmemeli.": "A fresh installation must not contain sample reports; restarting the app must not delete existing records.",
    "Grafik toplamları kayıt sayılarıyla uyumlu olmalı.": "Chart totals must match the report counts.",
    "Arayüz gerçek kişisel veri girilmemesi gerektiğini açıkça belirtmeli.": "The interface must clearly state that real personal data must not be entered.",
    "5 hatalı denemeden sonra giriş geçici olarak kilitlenmeli.": "Sign-in must be temporarily locked after five failed attempts.",
    "30 dakika hareketsizlikte yönetici oturumu kapanmalı.": "The administrator session must expire after 30 minutes of inactivity.",
    "Açıklamaya yazılan telefon/T.C. no/e-posta/IBAN kayıtta maskeli olmalı.": "Phone numbers, Turkish ID numbers, email addresses and IBANs entered in a description must be masked in storage.",
    "Sorgu yalnızca durum ve tarih göstermeli; açıklama/not göstermemeli.": "A status lookup must show only the status and date; it must not display the description or notes.",
    "Kimlik alanları varsayılan olarak dışarıda olmalı; işlem denetim kaydına yazılmalı.": "Identifying fields must be excluded by default; the export action must be recorded in the audit log.",
    "İncelemeyle ilgili kısa not ekleyin.": "Add a brief note about the review.",
    "Açıklama veya onay yoksa kayıt oluşturulmamalı; yazılan metin silinmemeli.": "A report must not be created without a description or confirmation; entered text must not be erased.",
    "KVKK (6698): veri sorumlusunun belirlenmesi, aydınlatma metni, hukuki sebep/veli onayı, saklama-imha politikası,":
        "KVKK (Law No. 6698): identify the data controller, prepare a privacy notice, establish the legal basis and parental-consent requirements, and define retention and deletion policies,",
    "gerekiyorsa VERBİS ve veri işleyen sözleşmeleri. Çocuk verisi ve olası yurt dışı sunucu kullanımı (ör. bulut barındırma)":
        "and, where required, VERBIS registration and data-processing agreements. Children's data and any use of servers abroad (for example, cloud hosting)",
    "ayrıca hukuki değerlendirme gerektirir.": "also require legal assessment.",
    "Yasal bildirim yükümlülükleri: çocuğa yönelik istismar/şiddet şüphesinde mevzuattaki bildirim yükümlülükleri bu":
        "Legal reporting obligations: where there is suspicion of abuse or violence against a child, statutory reporting duties apply independently of this platform's",
    "uygulamanın kayıt akışından bağımsızdır; okul yönetimi ve hukuk danışmanıyla netleştirilmelidir.":
        "reporting workflow and must be clarified with the school administration and legal counsel.",
    "Erişim: kişi bazlı hesaplar, rol ayrımı, iki aşamalı doğrulama, parola özeti (`tools/parola_hash.py`).":
        "Access: individual accounts, role-based permissions, two-factor authentication and password hashing (`tools/parola_hash.py`).",
    "Okul süreci: kayıtları kimin, ne kadar sürede inceleyeceği, acil durum protokolü ve rehberlik servisiyle iş akışı.":
        "School procedures: define who reviews reports and within what timeframe, the emergency protocol and the workflow with the guidance service.",
    "1. **Amaç:** Bildirim sürecinin anlaşılırlığını, temel işlevlerin doğruluğunu ve kural tabanlı sinyalin ölçülebilir":
        "1. **Purpose:** Evaluate the clarity of the reporting process, the correctness of core functions and the measurable performance of rule-based signals.",
    "başarımını raporlamak.": "report their performance.",
    "2. **Algılayıcı:** Makine öğrenmesi içermez; Türkçe'ye duyarlı normalleştirme (İ/ı, ASCII katlama), kelime başı sınırı,":
        "2. **Detector:** Does not use machine learning; it uses Turkish-aware normalisation (İ/ı handling and ASCII folding), word-boundary checks,",
    "harf tekrarı/ayraç/rakamla yazım çözümü ve kategori+ağırlık tabanlı öncelik kuralı kullanır.":
        "repeated-letter, separator and digit-substitution handling, and a category-and-weight-based priority rule.",
    "3. **Ölçüt:** Kesinlik, duyarlılık, F1 ve kategori bazlı yakalama; ayrıca \"zor örnek\" kümesiyle bilinen sınırlılıklar.":
        "3. **Metrics:** Precision, recall, F1 and category-level detection, alongside known limitations assessed using a 'challenging examples' set.",
    "4. **Sınırlılıklar:** Bağlam, ironi, imâ ve ima yoluyla dışlama yakalanmaz; deyimsel abartı (\"babam beni öldürecek\")":
        "4. **Limitations:** Context, irony and indirect exclusion may not be detected; figurative exaggeration may produce false positives,",
    "yanlış alarm üretir; yazım hataları (\"apdal\") kaçar; sözlük küçüktür.":
        "spelling variations may be missed, and the phrase dictionary is limited.",
    "5. **Yol haritası:** (a) etik kurul/okul izniyle, kimliksizleştirilmiş ve en az iki uzmanca etiketlenmiş veri kümesi,":
        "5. **Roadmap:** (a) an ethically approved, de-identified dataset labelled by at least two experts with school approval,",
    "(b) değerlendiriciler arası uyum (Cohen kappa), (c) eğitim/doğrulama/test ayrımı, (d) kural tabanlı yöntemin bir":
        "(b) inter-rater agreement (Cohen's kappa), (c) separate training, validation and test sets, (d) comparison of the rule-based method with a",
    "dil modeli veya sınıflandırıcı ile karşılaştırılması, (e) kullanılabilirlik testi (SUS ölçeği).":
        "language model or classifier, and (e) usability testing (System Usability Scale, SUS).",
    "6. **Etik:** Gerçek öğrenci verisi için önceden okul/veli onayı, gönüllülük, veri minimizasyonu ve güvenli saklama planı":
        "6. **Ethics:** Use of real student data requires prior school and parental approval, voluntary participation, data minimisation and a secure retention plan.",
    "gerekir. Bu uygulamada gerçek öğrenci verisi kullanmayın.": "Do not use real student data in this application.",
    "- Açıklamadaki telefon, T.C. kimlik numarası, e-posta ve IBAN'ı otomatik maskeler.":
        "- Automatically masks phone numbers, Turkish national ID numbers, email addresses and IBANs in descriptions.",
    "- Cihaz jetonu yalnızca özet olarak ve 1 gün saklanır; rapora bağlanmaz.": "- Only a hash of the device token is retained for one day; it is not linked to a report.",
    "- Öğrenci sorgusunda açıklama, not ve değerlendirme gösterilmez.": "- Student status checks do not display descriptions, notes or assessments.",
    "- Serbest metin kişileri dolaylı tanıtabilir; ‘tam anonim’ yerine ‘kimliksizleştirilmiş’ demek daha doğrudur.":
        "- Free text may indirectly identify people; 'de-identified' is more accurate than 'fully anonymous'.",
    "- Üçüncü kişilerin (şüpheli öğrenci) adı metinde geçebilir; maskeleme adları yakalamaz.":
        "- Third-party names (including a student who is the subject of a report) may appear in text; the masking layer does not detect names.",
    "- Barındırma yeri ve olası yurt dışı aktarım hukuken değerlendirilmelidir.": "- Hosting location and any potential international data transfer must be assessed legally.",
    "- Cihaz jetonu özeti: ertesi gün silinir.": "- Device-token hash: deleted the following day.",
    "- Giriş denemeleri: 7 gün.": "- Sign-in attempts: 7 days.",
    "Hakaret": "Insults", "Tehdit": "Threats", "Dışlama": "Exclusion", "Siber zorbalık": "Cyberbullying",
    "Akran dışlaması": "Peer exclusion", "Fiziksel zorbalık": "Physical bullying",
})


CATALOG.update({
    "Sınıf seçenekleri": "Class options", "Takip kodu": "Tracking code", "Yetkisiz erişim": "Unauthorised access",
    "İnceleme sırası": "Review prioritisation",
    "Durum güncelleme": "Status update", "Not geçmişi": "Note history", "Boş form": "Empty form",
    "Temiz başlangıç": "Clean installation", "Güvenli metin": "Safe text handling", "Hatalı giriş sınırı": "Failed sign-in limit",
    "Oturum zaman aşımı": "Session timeout", "Kişisel veri maskeleme": "Personal data masking",
    "Takip kodu sorgusu": "Tracking-code lookup", "CSV dışa aktarım": "CSV export", "Günlük kota": "Daily limit",
    "Ek bilgi": "Additional information", "9/A … 12/B seçenekleri görünmeli.": "Class options from 9/A to 12/B must be displayed.",
    "Proje:": "Project:", "Okul:": "School:", "Danışman öğretmen:": "Supervising teacher:",
    "[OKUL ADI]": "[SCHOOL NAME]", "[AD SOYAD]": "[FULL NAME]", "Tarih:": "Date:", "İmza:": "Signature:",
    "**Açıklama**": "**Description**", "**Olay türü**": "**Incident type**", "**Ortam**": "**Setting**",
    "**Yaklaşık zaman**": "**Approximate time**", "**Tekrarlanma**": "**Frequency**", "**Oluşturulma**": "**Created**",
    "**Bildirim türü**": "**Report type**", "**Kategoriler:**": "**Categories:**", "**Eşleşen ifadeler:**": "**Matched phrases:**",
})


CATALOG.update({
    "**KVKK (6698):**": "**KVKK (Law No. 6698):**",
    "veri sorumlusunun belirlenmesi, aydınlatma metni, hukuki sebep/veli onayı, saklama-imha politikası,":
        "identify the data controller, prepare a privacy notice, establish the legal basis and parental-consent requirements, and define retention and deletion policies,",
    "**Yasal bildirim yükümlülükleri:**": "**Statutory reporting obligations:**",
    "çocuğa yönelik istismar/şiddet şüphesinde mevzuattaki bildirim yükümlülükleri bu":
        "where there is suspicion of abuse or violence against a child, statutory reporting duties apply independently of this platform's",
    "**Erişim:**": "**Access:**", "kişi bazlı hesaplar, rol ayrımı, iki aşamalı doğrulama, parola özeti":
        "individual accounts, role-based permissions, two-factor authentication and password hashing",
    "**Okul süreci:**": "**School procedures:**",
    "kayıtları kimin, ne kadar sürede inceleyeceği, acil durum protokolü ve rehberlik servisiyle iş akışı.":
        "define who reviews reports and within what timeframe, the emergency protocol and the workflow with the guidance service.",
})


CATALOG.update({
    "saniye beklenir.": "seconds between entries.",
    "Cihaz jetonu geçersiz.": "The device token is invalid.",
    "Günlük bildirim hakkınız dolmuştur.": "You have reached the daily report limit.",
    "Bu kodla ek bilgi eklenebilecek bir bildirim bulunamadı.": "No report was found that can accept additional information with this code.",
    "Ek bilgi yalnızca bildirimin yapıldığı gün eklenebilir.": "Additional information can only be added on the day the report was submitted.",
    "Bu bildirim sonuçlandırıldığı için ek bilgi eklenemez.": "Additional information cannot be added because this report has been closed.",
    "Bugün en fazla 3 ek bilgi eklenebilir.": "You can add a maximum of three additional entries today.",
    "Yeni ek bilgi için yaklaşık": "Please wait approximately",
    "Yeni ek bilgi için yaklaşık {kalan} saniye beklemelisin.": "Please wait approximately {kalan} seconds before adding more information.",
    "Ek bilgi boş olamaz.": "Additional information cannot be empty.",
    "Ek bilgi en fazla 1000 karakter olabilir.": "Additional information must not exceed 1,000 characters.",
    "Bu kodla ek bilgi eklenebilecek bir bildirim bulunamadı.": "No report was found that can accept additional information with this code.",
    "Okul: [OKUL ADI]": "School: [SCHOOL NAME]", "Danışman öğretmen: [AD SOYAD]": "Supervising teacher: [FULL NAME]",
    "Öğrenci: Bilgilendirildim, gönüllü katılıyorum.": "Student: I have been informed and agree to participate voluntarily.",
    "Veli/Yasal temsilci: Bilgilendirildim, çocuğumun katılımına izin veriyorum.":
        "Parent/Legal guardian: I have been informed and give permission for my child's participation.",
})


CATALOG.update({
    "Proje:": "Project:", "Tarih:": "Date:", "İmza:": "Signature:",
    "telefon istenmez. Açıklamadaki": "phone numbers are not requested. The following information in descriptions",
    "Akran zorbalığı bildirimlerinin yetkili kişilerce incelenmesi ve öğrencinin korunması. Veriler başka amaçla kullanılmaz.":
        "To enable authorised staff to review peer-bullying reports and safeguard students. Data is not used for other purposes.",
    "size bağlamak mümkün olmadığından bazı haklar (erişim, düzeltme) teknik olarak kullanılamayabilir.":
        "it may not be technically possible to link a report to you, so certain rights (such as access and rectification) may not be exercisable.",
})


CATALOG.update({
    "Zaman": "Time", "Kullanıcı": "User", "İşlem": "Action", "Ayrıntı": "Details", "Yazar": "Author",
    "Yönetici girişi": "Administrator sign-in", "Başarısız giriş denemesi": "Failed sign-in attempt",
    "CSV dışa aktarım": "CSV export", "Oturum zaman aşımı": "Session timeout", "Oturum kapatıldı": "Session signed out",
    "Saklama süresi temizliği": "Retention cleanup", "Yeni bildirim oluşturuldu": "New report created",
    "Durum değiştirildi": "Status changed", "Birim ataması değiştirildi": "Team assignment changed",
    "İnceleme notu eklendi": "Review note added", "Anonim ek bilgi eklendi": "Additional information added anonymously",
})

CATALOG.update({
    "Veri yok": "No data", "Toplam bildirim": "Total reports", "Anonim oranı": "Anonymous share",
    "İlk işlem süresi (medyan)": "Time to first action (median)",
    "Sonuçlanma süresi (medyan)": "Time to closure (median)",
})

def _translate_tr_en(value: Any, language: str = EN) -> Any:
    """Translate known UI copy while leaving unknown/user-authored text intact."""
    if not isinstance(value, str) or language != EN:
        return value
    # Exact enum/label values are translated directly. For composed UI strings,
    # only longer phrases are replaced so short words such as "Acil" cannot
    # accidentally alter a student's free-text report.
    if value in CATALOG:
        return CATALOG[value]
    dynamic_patterns = (
        (r"^(\d+) saati aşan bekleyen$", lambda m: f"Awaiting review for over {m.group(1)} hours"),
        (r"^(\d+) günden eski sonuçlanmış kayıt \(silinecek\)$", lambda m: f"Closed reports older than {m.group(1)} days (to be deleted)"),
        (r"^(\d+) kayıt$", lambda m: f"{m.group(1)} reports"),
        (r"^Son (\d+) gün$", lambda m: f"Last {m.group(1)} days"),
        (r"^(\d+) kayıt silindi\.$", lambda m: f"{m.group(1)} reports deleted."),
        (r"^(\d+(?:[.,]\d+)?) saat bekliyor$", lambda m: f"waiting for {m.group(1)} hours"),
    )
    for pattern, render in dynamic_patterns:
        match = re.match(pattern, value)
        if match:
            return render(match)
    for source, target in sorted(CATALOG.items(), key=lambda item: len(item[0]), reverse=True):
        if len(source) < 9 and not (source.endswith(":") and len(source) >= 6):
            continue
        # Flexible whitespace also handles wrapped Markdown paragraphs and HTML.
        pattern = re.compile(r"\s+".join(re.escape(part) for part in source.split()))
        value = pattern.sub(lambda _m, replacement=target: replacement, value)
    return value


def _format_timestamp_tr_en(value: str | None, language: str = TR) -> str:
    """Format ISO-like database timestamps for display without changing stored values."""
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return value
    if language == EN:
        # Explicit month/AM-PM labels avoid dependence on the host OS locale.
        months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
        hour = dt.hour % 12 or 12
        meridiem = "AM" if dt.hour < 12 else "PM"
        return f"{months[dt.month - 1]} {dt.day:02d}, {dt.year} · {hour:02d}:{dt.minute:02d}:{dt.second:02d} {meridiem}"
    return f"{dt.day:02d}.{dt.month:02d}.{dt.year} · {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"


def _translate_structure_tr_en(value: Any, language: str = EN) -> Any:
    """Translate labels and known enum values in table-like structures, not free text."""
    if language != EN:
        return value
    if isinstance(value, dict):
        return {translate(k, language): translate_structure(v, language) for k, v in value.items()}
    if isinstance(value, list):
        return [translate_structure(v, language) for v in value]
    if isinstance(value, tuple):
        return tuple(translate_structure(v, language) for v in value)
    if isinstance(value, str):
        # Table cells may contain controlled audit labels/status transitions. Unknown
        # free-text values (including descriptions) remain unchanged.
        return translate(value, language)
    return value


# ---------------------------------------------------------------------------
# Multi-language catalogue (TR / EN / DE / FR / ES / AR / AZ)
# ---------------------------------------------------------------------------
LANGUAGES = {
    "Türkçe": {"code": "tr", "locale": "tr_TR", "direction": "ltr"},
    "English": {"code": "en", "locale": "en_GB", "direction": "ltr"},
    "Deutsch": {"code": "de", "locale": "de_DE", "direction": "ltr"},
    "Français": {"code": "fr", "locale": "fr_FR", "direction": "ltr"},
    "Español": {"code": "es", "locale": "es_ES", "direction": "ltr"},
    "العربية": {"code": "ar", "locale": "ar", "direction": "rtl"},
    "Azərbaycan dili": {"code": "az", "locale": "az_AZ", "direction": "ltr"},
}
CURRENT_LANGUAGE = TR

def set_language(language: str) -> None:
    """Set the language for helper calls made without an explicit language."""
    global CURRENT_LANGUAGE
    CURRENT_LANGUAGE = language if language in LANGUAGES else TR

# Reviewed core interface terminology. Keys are the canonical Turkish UI strings.
# User-authored report descriptions, notes and names are intentionally never translated.
MULTI_CATALOG: dict[str, dict[str, str]] = {
"Deutsch": {
"Genel bakış":"Übersicht","Yeni bildirim":"Neue Meldung","Bildirim sorgula":"Meldung verfolgen","Destek rehberi":"Unterstützungsleitfaden","Yönetici girişi":"Administrator-Anmeldung","Bildirim inceleme":"Meldungsprüfung","İstatistikler":"Statistiken","Trend ve ortam":"Trends und Kontext","Gizlilik ve KVKK":"Datenschutz","Araştırma ve test":"Forschung und Tests","Güvenli kullanım":"Sichere Nutzung","Oturumu kapat":"Abmelden","Kullanıcı adı":"Benutzername","Parola":"Passwort","Giriş yap":"Anmelden","Dil / Language":"Sprache / Language","Türkçe":"Türkisch","English":"Englisch","Güvenli bir okul, herkesin hakkı.":"Eine sichere Schule ist das Recht aller.","Ne oldu?":"Was ist passiert?","Nerede oldu?":"Wo ist es passiert?","Ne zaman oldu?":"Wann ist es passiert?","Bu olay kaç kez yaşandı?":"Wie oft ist das passiert?","Olayı kendi cümlelerinle anlat":"Beschreibe den Vorfall mit eigenen Worten","Bildirimi gönder":"Meldung absenden","Durumu sorgula":"Status abfragen","Durumu göster":"Status anzeigen","Ek bilgi ekle":"Weitere Informationen hinzufügen","Bildirim inceleme alanına yalnızca yetkili kullanıcılar erişebilir.":"Nur autorisierte Personen können auf den Bereich zur Meldungsprüfung zugreifen.","İnceleme bekliyor":"Wird geprüft","İnceleniyor":"In Bearbeitung","Sonuçlandırıldı":"Abgeschlossen","Acil":"Dringend","Yüksek":"Hoch","Orta":"Mittel","Düşük":"Niedrig","GECİKMİŞ":"ÜBERFÄLLIG","Günlük Durum Özeti":"Tagesübersicht","Yeni bildirim":"Neue Meldung","Toplam kayıt":"Gesamtzahl der Einträge","Açık kayıt":"Offene Meldungen","Kayıt ara":"Meldung suchen","Öncelik sinyali":"Prioritätssignal","Başlangıç tarihi":"Startdatum","Bitiş tarihi":"Enddatum","Tümü":"Alle","Son 7 gün":"Letzte 7 Tage","Son 30 gün":"Letzte 30 Tage","En yeni önce":"Neueste zuerst","En eski önce":"Älteste zuerst","Rehberlik önerisi":"Empfehlung der Beratungsstelle","Güvenlik ilkeleri":"Sicherheitsgrundsätze","Açıklama":"Beschreibung","Olay türü":"Vorfallart","Ortam":"Umgebung","Oluşturulma":"Erstellt am","Son güncelleme":"Letzte Aktualisierung","Zaman":"Zeit","Kullanıcı":"Benutzer","İşlem":"Aktion","Ayrıntı":"Details","Yazar":"Verfasser","Kaydet":"Speichern","Durumu kaydet":"Status speichern","Not ekle":"Not hinzufügen","İnceleme bilgileri kaydedildi.":"Prüfinformationen wurden gespeichert.","Kullanıcı adı veya parola yanlış.":"Benutzername oder Passwort ist falsch.","Yönetici erişimi gerekli":"Administratorzugriff erforderlich","Bu bölümü görüntülemek için yönetici oturumu açın.":"Melden Sie sich als Administrator an, um diesen Bereich anzuzeigen.","Telefon, T.C. no, e-posta ve IBAN otomatik gizlenir.":"Telefonnummern, türkische ID-Nummern, E-Mail-Adressen und IBANs werden automatisch maskiert.","Acil bir tehlike varsa beklemeyin:":"Warten Sie bei unmittelbarer Gefahr nicht:","Sinyal, karar değil":"Ein Signal ist keine Entscheidung","Yetkili kişiler kaydı inceler. Kararı makine vermez.":"Autorisierte Personen prüfen die Meldung. Das System trifft keine Entscheidung.","Güvenli kullanım":"Sichere Nutzung","Gizlilik":"Datenschutz","Hakaret":"Beleidigung","Tehdit":"Drohung","Dışlama":"Ausgrenzung","Siber zorbalık":"Cybermobbing","Akran dışlaması":"Ausgrenzung unter Gleichaltrigen","Fiziksel zorbalık":"Körperliches Mobbing","Sınıfta":"Im Klassenraum","Okul bahçesinde":"Auf dem Schulhof","Koridorda":"Im Flur","Sosyal medyada":"In sozialen Medien","Mesajlaşmada":"Beim Messaging","Bugün":"Heute","Dün":"Gestern","Bu hafta":"Diese Woche","Daha önce":"Früher","Emin değilim":"Ich bin mir nicht sicher","Bir kez":"Einmal","Birkaç kez":"Mehrmals","Birden fazla kez":"Mehr als einmal","Gizli takip kodu":"Vertraulicher Tracking-Code","Açıklama yalnızca boşluk veya noktalama işaretlerinden oluşamaz. Kısaca ne olduğunu yaz.":"Die Beschreibung darf nicht nur aus Leerzeichen oder Satzzeichen bestehen. Beschreiben Sie kurz, was passiert ist.","Lütfen onay kutusunu işaretle.":"Bitte aktivieren Sie das Bestätigungsfeld.","Bildirimin kaydedildi. Teşekkür ederiz.":"Ihre Meldung wurde gespeichert. Vielen Dank.","Bu kodla eşleşen bir kayıt bulunamadı. Kodu kontrol edip tekrar dene.":"Zu diesem Code wurde kein Eintrag gefunden. Bitte überprüfen Sie den Code.","Ek bilgi boş olamaz.":"Weitere Informationen dürfen nicht leer sein.","Acil bir durum değil, yalnızca bilgi vermek istiyorum.":"",},
"Français": {
"Genel bakış":"Vue d’ensemble","Yeni bildirim":"Nouveau signalement","Bildirim sorgula":"Suivre un signalement","Destek rehberi":"Guide d’accompagnement","Yönetici girişi":"Connexion administrateur","Bildirim inceleme":"Examen des signalements","İstatistikler":"Statistiques","Trend ve ortam":"Tendances et contexte","Gizlilik ve KVKK":"Confidentialité et protection des données","Araştırma ve test":"Recherche et tests","Güvenli kullanım":"Utilisation sûre","Oturumu kapat":"Se déconnecter","Kullanıcı adı":"Nom d’utilisateur","Parola":"Mot de passe","Giriş yap":"Se connecter","Dil / Language":"Langue / Language","Türkçe":"Turc","English":"Anglais","Güvenli bir okul, herkesin hakkı.":"Une école sûre est un droit pour toutes et tous.","Ne oldu?":"Que s’est-il passé ?","Nerede oldu?":"Où cela s’est-il passé ?","Ne zaman oldu?":"Quand cela s’est-il passé ?","Bu olay kaç kez yaşandı?":"Combien de fois cela s’est-il produit ?","Olayı kendi cümlelerinle anlat":"Décrivez les faits avec vos propres mots","Bildirimi gönder":"Envoyer le signalement","Durumu sorgula":"Consulter le statut","Durumu göster":"Afficher le statut","Ek bilgi ekle":"Ajouter des informations","Bildirim inceleme alanına yalnızca yetkili kullanıcılar erişebilir.":"Seules les personnes autorisées peuvent accéder à l’espace d’examen des signalements.","İnceleme bekliyor":"En attente d’examen","İnceleniyor":"En cours d’examen","Sonuçlandırıldı":"Clôturé","Acil":"Urgent","Yüksek":"Élevé","Orta":"Moyen","Düşük":"Faible","GECİKMİŞ":"EN RETARD","Günlük Durum Özeti":"Résumé quotidien","Toplam kayıt":"Nombre total de dossiers","Açık kayıt":"Dossiers ouverts","Kayıt ara":"Rechercher un dossier","Öncelik sinyali":"Indicateur de priorité","Başlangıç tarihi":"Date de début","Bitiş tarihi":"Date de fin","Tümü":"Tout","Son 7 gün":"7 derniers jours","Son 30 gün":"30 derniers jours","En yeni önce":"Du plus récent au plus ancien","En eski önce":"Du plus ancien au plus récent","Rehberlik önerisi":"Conseil du service d’accompagnement","Güvenlik ilkeleri":"Principes de sécurité","Açıklama":"Description","Olay türü":"Type d’incident","Ortam":"Lieu","Oluşturulma":"Créé le","Son güncelleme":"Dernière mise à jour","Zaman":"Date et heure","Kullanıcı":"Utilisateur","İşlem":"Action","Ayrıntı":"Détails","Yazar":"Auteur","Kaydet":"Enregistrer","Durumu kaydet":"Enregistrer le statut","Not ekle":"Ajouter une note","İnceleme bilgileri kaydedildi.":"Les informations d’examen ont été enregistrées.","Kullanıcı adı veya parola yanlış.":"Le nom d’utilisateur ou le mot de passe est incorrect.","Yönetici erişimi gerekli":"Accès administrateur requis","Bu bölümü görüntülemek için yönetici oturumu açın.":"Connectez-vous en tant qu’administrateur pour consulter cette section.","Telefon, T.C. no, e-posta ve IBAN otomatik gizlenir.":"Les numéros de téléphone, numéros d’identité turcs, adresses e-mail et IBAN sont automatiquement masqués.","Acil bir tehlike varsa beklemeyin:":"En cas de danger immédiat, n’attendez pas :","Sinyal, karar değil":"Un signal n’est pas une décision","Yetkili kişiler kaydı inceler. Kararı makine vermez.":"Les personnes autorisées examinent le signalement. Le système ne prend aucune décision.","Gizlilik":"Confidentialité","Hakaret":"Insultes","Tehdit":"Menaces","Dışlama":"Exclusion","Siber zorbalık":"Cyberharcèlement","Akran dışlaması":"Exclusion entre pairs","Fiziksel zorbalık":"Harcèlement physique","Sınıfta":"En classe","Okul bahçesinde":"Dans la cour de l’école","Koridorda":"Dans le couloir","Sosyal medyada":"Sur les réseaux sociaux","Mesajlaşmada":"Dans les messageries","Bugün":"Aujourd’hui","Dün":"Hier","Bu hafta":"Cette semaine","Daha önce":"Auparavant","Emin değilim":"Je ne sais pas","Bir kez":"Une fois","Birkaç kez":"Plusieurs fois","Birden fazla kez":"Plus d’une fois","Gizli takip kodu":"Code de suivi confidentiel","Lütfen onay kutusunu işaretle.":"Veuillez cocher la case de confirmation.","Bildirimin kaydedildi. Teşekkür ederiz.":"Votre signalement a été enregistré. Merci.","Bu kodla eşleşen bir kayıt bulunamadı. Kodu kontrol edip tekrar dene.":"Aucun dossier ne correspond à ce code. Vérifiez le code.","Ek bilgi boş olamaz.":"Les informations complémentaires ne peuvent pas être vides."},
"Español": {
"Genel bakış":"Resumen","Yeni bildirim":"Nuevo reporte","Bildirim sorgula":"Consultar un reporte","Destek rehberi":"Guía de apoyo","Yönetici girişi":"Acceso de administración","Bildirim inceleme":"Revisión de reportes","İstatistikler":"Estadísticas","Trend ve ortam":"Tendencias y contexto","Gizlilik ve KVKK":"Privacidad y protección de datos","Araştırma ve test":"Investigación y pruebas","Güvenli kullanım":"Uso seguro","Oturumu kapat":"Cerrar sesión","Kullanıcı adı":"Nombre de usuario","Parola":"Contraseña","Giriş yap":"Iniciar sesión","Dil / Language":"Idioma / Language","Türkçe":"Turco","English":"Inglés","Güvenli bir okul, herkesin hakkı.":"Una escuela segura es un derecho de todas las personas.","Ne oldu?":"¿Qué ocurrió?","Nerede oldu?":"¿Dónde ocurrió?","Ne zaman oldu?":"¿Cuándo ocurrió?","Bu olay kaç kez yaşandı?":"¿Cuántas veces ha ocurrido?","Olayı kendi cümlelerinle anlat":"Describe lo ocurrido con tus propias palabras","Bildirimi gönder":"Enviar reporte","Durumu sorgula":"Consultar estado","Durumu göster":"Mostrar estado","Ek bilgi ekle":"Añadir información","Bildirim inceleme alanına yalnızca yetkili kullanıcılar erişebilir.":"Solo el personal autorizado puede acceder al área de revisión de reportes.","İnceleme bekliyor":"Pendiente de revisión","İnceleniyor":"En revisión","Sonuçlandırıldı":"Cerrado","Acil":"Urgente","Yüksek":"Alta","Orta":"Media","Düşük":"Baja","GECİKMİŞ":"ATRASADO","Günlük Durum Özeti":"Resumen diario","Toplam kayıt":"Total de registros","Açık kayıt":"Reportes abiertos","Kayıt ara":"Buscar un registro","Öncelik sinyali":"Indicador de prioridad","Başlangıç tarihi":"Fecha de inicio","Bitiş tarihi":"Fecha de finalización","Tümü":"Todos","Son 7 gün":"Últimos 7 días","Son 30 gün":"Últimos 30 días","En yeni önce":"Más recientes primero","En eski önce":"Más antiguos primero","Rehberlik önerisi":"Recomendación de orientación","Güvenlik ilkeleri":"Principios de seguridad","Açıklama":"Descripción","Olay türü":"Tipo de incidente","Ortam":"Lugar","Oluşturulma":"Creado","Son güncelleme":"Última actualización","Zaman":"Fecha y hora","Kullanıcı":"Usuario","İşlem":"Acción","Ayrıntı":"Detalles","Yazar":"Autor","Kaydet":"Guardar","Durumu kaydet":"Guardar estado","Not ekle":"Añadir nota","İnceleme bilgileri kaydedildi.":"La información de revisión se ha guardado.","Kullanıcı adı veya parola yanlış.":"El nombre de usuario o la contraseña son incorrectos.","Yönetici erişimi gerekli":"Se requiere acceso de administración","Bu bölümü görüntülemek için yönetici oturumu açın.":"Inicia sesión como administrador para ver esta sección.","Telefon, T.C. no, e-posta ve IBAN otomatik gizlenir.":"Los teléfonos, números de identidad turcos, correos electrónicos e IBAN se ocultan automáticamente.","Acil bir tehlike varsa beklemeyin:":"Si existe un peligro inmediato, no esperes:","Sinyal, karar değil":"Una señal no es una decisión","Yetkili kişiler kaydı inceler. Kararı makine vermez.":"El personal autorizado revisa el reporte. El sistema no toma decisiones.","Gizlilik":"Privacidad","Hakaret":"Insultos","Tehdit":"Amenazas","Dışlama":"Exclusión","Siber zorbalık":"Ciberacoso","Akran dışlaması":"Exclusión entre compañeros","Fiziksel zorbalık":"Acoso físico","Sınıfta":"En el aula","Okul bahçesinde":"En el patio de la escuela","Koridorda":"En el pasillo","Sosyal medyada":"En redes sociales","Mesajlaşmada":"En aplicaciones de mensajería","Bugün":"Hoy","Dün":"Ayer","Bu hafta":"Esta semana","Daha önce":"Antes","Emin değilim":"No estoy seguro/a","Bir kez":"Una vez","Birkaç kez":"Varias veces","Birden fazla kez":"Más de una vez","Gizli takip kodu":"Código privado de seguimiento","Lütfen onay kutusunu işaretle.":"Marca la casilla de confirmación.","Bildirimin kaydedildi. Teşekkür ederiz.":"Tu reporte se ha guardado. Gracias.","Bu kodla eşleşen bir kayıt bulunamadı. Kodu kontrol edip tekrar dene.":"No se encontró ningún registro con este código. Comprueba el código.","Ek bilgi boş olamaz.":"La información adicional no puede estar vacía."},
"العربية": {
"Genel bakış":"نظرة عامة","Yeni bildirim":"بلاغ جديد","Bildirim sorgula":"متابعة بلاغ","Destek rehberi":"دليل الدعم","Yönetici girişi":"دخول المسؤول","Bildirim inceleme":"مراجعة البلاغات","İstatistikler":"الإحصاءات","Trend ve ortam":"الاتجاهات والسياق","Gizlilik ve KVKK":"الخصوصية وحماية البيانات","Araştırma ve test":"البحث والاختبار","Güvenli kullanım":"الاستخدام الآمن","Oturumu kapat":"تسجيل الخروج","Kullanıcı adı":"اسم المستخدم","Parola":"كلمة المرور","Giriş yap":"تسجيل الدخول","Dil / Language":"اللغة / Language","Türkçe":"التركية","English":"الإنجليزية","Güvenli bir okul, herkesin hakkı.":"المدرسة الآمنة حق للجميع.","Ne oldu?":"ماذا حدث؟","Nerede oldu?":"أين حدث ذلك؟","Ne zaman oldu?":"متى حدث ذلك؟","Bu olay kaç kez yaşandı?":"كم مرة حدث ذلك؟","Olayı kendi cümlelerinle anlat":"صف ما حدث بكلماتك الخاصة","Bildirimi gönder":"إرسال البلاغ","Durumu sorgula":"الاستعلام عن الحالة","Durumu göster":"عرض الحالة","Ek bilgi ekle":"إضافة معلومات","Bildirim inceleme alanına yalnızca yetkili kullanıcılar erişebilir.":"يقتصر الوصول إلى قسم مراجعة البلاغات على الأشخاص المخوّلين.","İnceleme bekliyor":"بانتظار المراجعة","İnceleniyor":"قيد المراجعة","Sonuçlandırıldı":"مغلق","Acil":"عاجل","Yüksek":"مرتفع","Orta":"متوسط","Düşük":"منخفض","GECİKMİŞ":"متأخر","Günlük Durum Özeti":"الملخص اليومي للحالة","Toplam kayıt":"إجمالي السجلات","Açık kayıt":"البلاغات المفتوحة","Kayıt ara":"البحث عن سجل","Öncelik sinyali":"مؤشر الأولوية","Başlangıç tarihi":"تاريخ البداية","Bitiş tarihi":"تاريخ النهاية","Tümü":"الكل","Son 7 gün":"آخر 7 أيام","Son 30 gün":"آخر 30 يومًا","En yeni önce":"الأحدث أولاً","En eski önce":"الأقدم أولاً","Rehberlik önerisi":"توصية الإرشاد","Güvenlik ilkeleri":"مبادئ السلامة","Açıklama":"الوصف","Olay türü":"نوع الحادثة","Ortam":"المكان","Oluşturulma":"تاريخ الإنشاء","Son güncelleme":"آخر تحديث","Zaman":"الوقت","Kullanıcı":"المستخدم","İşlem":"الإجراء","Ayrıntı":"التفاصيل","Yazar":"الكاتب","Kaydet":"حفظ","Durumu kaydet":"حفظ الحالة","Not ekle":"إضافة ملاحظة","İnceleme bilgileri kaydedildi.":"تم حفظ معلومات المراجعة.","Kullanıcı adı veya parola yanlış.":"اسم المستخدم أو كلمة المرور غير صحيحة.","Yönetici erişimi gerekli":"يلزم وصول المسؤول","Bu bölümü görüntülemek için yönetici oturumu açın.":"يرجى تسجيل الدخول بصفتك مسؤولاً لعرض هذا القسم.","Telefon, T.C. no, e-posta ve IBAN otomatik gizlenir.":"تُخفى أرقام الهاتف وأرقام الهوية التركية وعناوين البريد الإلكتروني وأرقام IBAN تلقائيًا.","Acil bir tehlike varsa beklemeyin:":"في حال وجود خطر فوري، لا تنتظر:","Sinyal, karar değil":"المؤشر ليس قرارًا","Yetkili kişiler kaydı inceler. Kararı makine vermez.":"يراجع الأشخاص المخوّلون البلاغ. ولا يتخذ النظام القرار.","Gizlilik":"الخصوصية","Hakaret":"إهانات","Tehdit":"تهديدات","Dışlama":"إقصاء","Siber zorbalık":"تنمّر إلكتروني","Akran dışlaması":"إقصاء الأقران","Fiziksel zorbalık":"تنمّر جسدي","Sınıfta":"في الصف","Okul bahçesinde":"في ساحة المدرسة","Koridorda":"في الممر","Sosyal medyada":"على وسائل التواصل الاجتماعي","Mesajlaşmada":"في تطبيقات المراسلة","Bugün":"اليوم","Dün":"أمس","Bu hafta":"هذا الأسبوع","Daha önce":"سابقًا","Emin değilim":"لست متأكدًا","Bir kez":"مرة واحدة","Birkaç kez":"عدة مرات","Birden fazla kez":"أكثر من مرة","Gizli takip kodu":"رمز متابعة خاص","Lütfen onay kutusunu işaretle.":"يرجى تحديد مربع التأكيد.","Bildirimin kaydedildi. Teşekkür ederiz.":"تم حفظ البلاغ. شكرًا لك.","Bu kodla eşleşen bir kayıt bulunamadı. Kodu kontrol edip tekrar dene.":"لم يتم العثور على سجل بهذا الرمز. يرجى التحقق من الرمز.","Ek bilgi boş olamaz.":"لا يمكن ترك المعلومات الإضافية فارغة."},
"Azərbaycan dili": {
"Genel bakış":"Ümumi baxış","Yeni bildirim":"Yeni bildiriş","Bildirim sorgula":"Bildirişi izlə","Destek rehberi":"Dəstək bələdçisi","Yönetici girişi":"Administrator girişi","Bildirim inceleme":"Bildirişlərin yoxlanılması","İstatistikler":"Statistika","Trend ve ortam":"Trendlər və mühit","Gizlilik ve KVKK":"Məxfilik və şəxsi məlumatların qorunması","Araştırma ve test":"Tədqiqat və sınaq","Güvenli kullanım":"Təhlükəsiz istifadə","Oturumu kapat":"Sessiyanı bağla","Kullanıcı adı":"İstifadəçi adı","Parola":"Şifrə","Giriş yap":"Daxil ol","Dil / Language":"Dil / Language","Türkçe":"Türk dili","English":"İngilis dili","Güvenli bir okul, herkesin hakkı.":"Təhlükəsiz məktəb hər kəsin haqqıdır.","Ne oldu?":"Nə baş verdi?","Nerede oldu?":"Harada baş verdi?","Ne zaman oldu?":"Nə vaxt baş verdi?","Bu olay kaç kez yaşandı?":"Bu hadisə neçə dəfə baş verib?","Olayı kendi cümlelerinle anlat":"Baş verənləri öz sözlərinlə təsvir et","Bildirimi gönder":"Bildirişi göndər","Durumu sorgula":"Statusu yoxla","Durumu göster":"Statusu göstər","Ek bilgi ekle":"Əlavə məlumat əlavə et","Bildirim inceleme alanına yalnızca yetkili kullanıcılar erişebilir.":"Bildirişlərin yoxlanılması bölməsinə yalnız səlahiyyətli şəxslər daxil ola bilər.","İnceleme bekliyor":"Yoxlanılmağı gözləyir","İnceleniyor":"Yoxlanılır","Sonuçlandırıldı":"Tamamlandı","Acil":"Təcili","Yüksek":"Yüksək","Orta":"Orta","Düşük":"Aşağı","GECİKMİŞ":"GECİKİB","Günlük Durum Özeti":"Gündəlik vəziyyət xülasəsi","Toplam kayıt":"Ümumi qeyd sayı","Açık kayıt":"Açıq bildirişlər","Kayıt ara":"Qeydi axtar","Öncelik sinyali":"Prioritet göstəricisi","Başlangıç tarihi":"Başlanğıc tarixi","Bitiş tarihi":"Bitmə tarixi","Tümü":"Hamısı","Son 7 gün":"Son 7 gün","Son 30 gün":"Son 30 gün","En yeni önce":"Əvvəlcə ən yenilər","En eski önce":"Əvvəlcə ən köhnələr","Rehberlik önerisi":"Psixoloji dəstək tövsiyəsi","Güvenlik ilkeleri":"Təhlükəsizlik prinsipləri","Açıklama":"Təsvir","Olay türü":"Hadisə növü","Ortam":"Mühit","Oluşturulma":"Yaradılma tarixi","Son güncelleme":"Son yenilənmə","Zaman":"Vaxt","Kullanıcı":"İstifadəçi","İşlem":"Əməliyyat","Ayrıntı":"Təfərrüatlar","Yazar":"Müəllif","Kaydet":"Yadda saxla","Durumu kaydet":"Statusu yadda saxla","Not ekle":"Qeyd əlavə et","İnceleme bilgileri kaydedildi.":"Yoxlama məlumatları yadda saxlanıldı.","Kullanıcı adı veya parola yanlış.":"İstifadəçi adı və ya şifrə yanlışdır.","Yönetici erişimi gerekli":"Administrator girişi tələb olunur","Bu bölümü görüntülemek için yönetici oturumu açın.":"Bu bölməyə baxmaq üçün administrator kimi daxil olun.","Telefon, T.C. no, e-posta ve IBAN otomatik gizlenir.":"Telefon nömrələri, Türkiyə şəxsiyyət nömrələri, e-poçt ünvanları və IBAN avtomatik maskalanır.","Acil bir tehlike varsa beklemeyin:":"Təcili təhlükə varsa gözləməyin:","Sinyal, karar değil":"Siqnal qərar deyil","Yetkili kişiler kaydı inceler. Kararı makine vermez.":"Qeydi səlahiyyətli şəxslər yoxlayır. Qərarı sistem vermir.","Gizlilik":"Məxfilik","Hakaret":"Təhqir","Tehdit":"Təhdid","Dışlama":"Kənarlaşdırma","Siber zorbalık":"Kiberzorakılıq","Akran dışlaması":"Həmyaşıdların kənarlaşdırılması","Fiziksel zorbalık":"Fiziki zorakılıq","Sınıfta":"Sinifdə","Okul bahçesinde":"Məktəb həyətində","Koridorda":"Dəhlizdə","Sosyal medyada":"Sosial mediada","Mesajlaşmada":"Mesajlaşmada","Bugün":"Bu gün","Dün":"Dünən","Bu hafta":"Bu həftə","Daha önce":"Əvvəllər","Emin değilim":"Əmin deyiləm","Bir kez":"Bir dəfə","Birkaç kez":"Bir neçə dəfə","Birden fazla kez":"Bir dəfədən çox","Gizli takip kodu":"Məxfi izləmə kodu","Lütfen onay kutusunu işaretle.":"Zəhmət olmasa təsdiq xanasını işarələyin.","Bildirimin kaydedildi. Teşekkür ederiz.":"Bildirişiniz yadda saxlanıldı. Təşəkkür edirik.","Bu kodla eşleşen bir kayıt bulunamadı. Kodu kontrol edip tekrar dene.":"Bu kodla uyğun qeyd tapılmadı. Kodu yoxlayın.","Ek bilgi boş olamaz.":"Əlavə məlumat boş ola bilməz."}
}

# Expanded, reviewed UI coverage: form choices, safety notices, tracking and administration.
# These entries intentionally translate interface copy only, never submitted report text.
_EXPANDED_UI = {
"Deutsch": {
"Kimliğini vermeden bildir. Ad, sınıf veya telefon istenmez.":"Melde den Vorfall, ohne deine Identität anzugeben. Name, Klasse und Telefonnummer werden nicht abgefragt.",
"Ne oldu?":"Was ist passiert?", "Nerede oldu?":"Wo ist es passiert?", "Ne zaman oldu?":"Wann ist es passiert?",
"Bu olay kaç kez yaşandı?":"Wie oft ist das passiert?", "Olayı kendi cümlelerinle anlat":"Beschreibe den Vorfall mit eigenen Worten",
"Hakaret veya alay":"Beleidigung oder Verspottung", "Tehdit":"Bedrohung", "Dışlama":"Ausgrenzung",
"Dijital zorbalık":"Cybermobbing", "Fiziksel zorbalık şüphesi":"Verdacht auf körperliches Mobbing", "Diğer":"Sonstiges",
"Sınıfta":"Im Klassenzimmer", "Okul bahçesinde":"Auf dem Schulhof", "Koridorda":"Im Flur", "Sosyal medyada":"In sozialen Medien", "Mesajlaşmada":"In Messaging-Apps",
"Bugün":"Heute", "Dün":"Gestern", "Bu hafta":"Diese Woche", "Daha önce":"Früher", "Emin değilim":"Ich bin mir nicht sicher",
"Bir kez":"Einmal", "Birkaç kez":"Mehrmals", "Birden fazla kez":"Mehr als einmal",
"Acil bir durum değil, yalnızca bilgi vermek istiyorum.":"Es handelt sich nicht um einen Notfall; ich möchte lediglich etwas mitteilen.",
"Acil bir tehlike varsa beklemeyin:":"Warten Sie bei unmittelbarer Gefahr nicht:",
"112 Acil Çağrı Merkezi":"112 Notrufzentrale", "Günde bir bildirim hakkın var.":"Du kannst eine Meldung pro Tag einreichen.",
"Bu platform gerçek bir okul sistemine bağlı değildir. Gerçek kişisel veri girmeyin.":"Diese Plattform ist nicht mit einem echten Schulsystem verbunden. Gib keine echten personenbezogenen Daten ein.",
"Bildirimi gönder":"Meldung absenden", "Gizli takip kodun.":"Dein vertraulicher Nachverfolgungscode.",
"Durumu sorgula":"Status abfragen", "Durumu göster":"Status anzeigen", "Ek bilgi ekle":"Weitere Informationen hinzufügen",
"Ek bilgi boş olamaz.":"Zusätzliche Angaben dürfen nicht leer sein.", "Lütfen olayı anlat.":"Bitte beschreibe den Vorfall.",
"Lütfen onay kutusunu işaretle.":"Bitte aktiviere das Bestätigungsfeld.", "Bildirimin kaydedildi. Teşekkür ederiz.":"Deine Meldung wurde gespeichert. Vielen Dank.",
"Bu kodla eşleşen bir kayıt bulunamadı. Kodu kontrol edip tekrar dene.":"Zu diesem Code wurde kein Eintrag gefunden. Bitte überprüfe den Code.",
"Açıklama":"Beschreibung", "Olay türü":"Vorfallart", "Ortam":"Ort", "Tekrar durumu":"Häufigkeit", "İnceleme durumu":"Prüfstatus",
"İnceleme bekliyor":"Wartet auf Prüfung", "İnceleniyor":"Wird geprüft", "Sonuçlandırıldı":"Abgeschlossen",
"Öncelik sinyali":"Prioritätssignal", "Sorumlu birim":"Zuständige Stelle", "Durumu kaydet":"Status speichern", "Not ekle":"Not hinzufügen",
"Kayıt ara":"Eintrag suchen", "Tüm durumlar":"Alle Status", "Tüm birimler":"Alle Stellen", "Sıralama":"Sortierung",
"En yeni önce":"Neueste zuerst", "En eski önce":"Älteste zuerst", "Öncelik (yüksekten)":"Priorität (absteigend)",
"İnceleme bilgileri kaydedildi.":"Prüfinformationen wurden gespeichert.", "Değişiklik yapılmadı; bilgiler zaten güncel.":"Keine Änderung vorgenommen; die Angaben sind bereits aktuell.",
"Not kaydedildi.":"Die Notiz wurde gespeichert.", "Not kaydedilemedi.":"Die Notiz konnte nicht gespeichert werden.",
"Yönetici erişimi gerekli":"Administratorzugriff erforderlich", "Bu bölümü görüntülemek için yönetici oturumu açın.":"Melde dich als Administrator an, um diesen Bereich aufzurufen.",
"Kullanıcı adı veya parola yanlış.":"Benutzername oder Passwort ist falsch.", "Yönetici bilgileri ayarlanmamış.":"Die Administrator-Zugangsdaten wurden nicht eingerichtet.",
"Günlük Durum Özeti":"Tagesübersicht", "Bugünkü yeni bildirim":"Neue Meldungen heute", "Aktif yüksek/acil":"Aktive Meldungen mit hoher/dringender Priorität",
"İnceleme bekleyen":"Ausstehende Prüfungen", "Toplam kayıt":"Gesamtzahl der Einträge", "Açık kayıt":"Offene Meldungen",
"İstatistikler":"Statistiken", "Grafikler yalnızca bu uygulamada kayıtlı bilgileri özetler; okul geneline ilişkin sonuç göstermez.":"Die Diagramme fassen nur die in dieser Anwendung gespeicherten Angaben zusammen; sie erlauben keine Rückschlüsse auf die gesamte Schule.",
"Sinyal, karar değil":"Ein Signal ist keine Entscheidung", "Yetkili kişiler kaydı inceler. Kararı makine vermez.":"Autorisierte Personen prüfen die Meldung. Das System trifft keine Entscheidung.",
"Telefon, T.C. no, e-posta ve IBAN otomatik gizlenir.":"Telefonnummern, türkische ID-Nummern, E-Mail-Adressen und IBAN werden automatisch maskiert.",
"Destek rehberi":"Unterstützungsleitfaden", "Gizlilik ve KVKK paneli":"Datenschutzbereich", "Araştırma ve kalite kontrol":"Forschung und Qualitätssicherung",
},
"Français": {
"Kimliğini vermeden bildir. Ad, sınıf veya telefon istenmez.":"Faites un signalement sans révéler votre identité. Aucun nom, classe ou numéro de téléphone n’est demandé.",
"Ne oldu?":"Que s’est-il passé ?", "Nerede oldu?":"Où cela s’est-il passé ?", "Ne zaman oldu?":"Quand cela s’est-il passé ?",
"Bu olay kaç kez yaşandı?":"Combien de fois cela s’est-il produit ?", "Olayı kendi cümlelerinle anlat":"Décrivez les faits avec vos propres mots",
"Hakaret veya alay":"Insultes ou moqueries", "Tehdit":"Menaces", "Dışlama":"Exclusion", "Dijital zorbalık":"Cyberharcèlement", "Fiziksel zorbalık şüphesi":"Suspicion de harcèlement physique", "Diğer":"Autre",
"Sınıfta":"En classe", "Okul bahçesinde":"Dans la cour de l’école", "Koridorda":"Dans le couloir", "Sosyal medyada":"Sur les réseaux sociaux", "Mesajlaşmada":"Dans les applications de messagerie",
"Bugün":"Aujourd’hui", "Dün":"Hier", "Bu hafta":"Cette semaine", "Daha önce":"Auparavant", "Emin değilim":"Je ne sais pas",
"Bir kez":"Une fois", "Birkaç kez":"Plusieurs fois", "Birden fazla kez":"Plus d’une fois",
"Acil bir durum değil, yalnızca bilgi vermek istiyorum.":"Il ne s’agit pas d’une urgence ; je souhaite simplement transmettre une information.",
"Acil bir tehlike varsa beklemeyin:":"En cas de danger immédiat, n’attendez pas :",
"Günde bir bildirim hakkın var.":"Vous pouvez envoyer un signalement par jour.",
"Bu platform gerçek bir okul sistemine bağlı değildir. Gerçek kişisel veri girmeyin.":"Cette plateforme n’est pas reliée à un véritable système scolaire. N’y saisissez aucune donnée personnelle réelle.",
"Bildirimi gönder":"Envoyer le signalement", "Gizli takip kodun.":"Votre code de suivi confidentiel.",
"Durumu sorgula":"Consulter le statut", "Durumu göster":"Afficher le statut", "Ek bilgi ekle":"Ajouter des informations",
"Ek bilgi boş olamaz.":"Les informations complémentaires ne peuvent pas être vides.", "Lütfen olayı anlat.":"Veuillez décrire les faits.",
"Lütfen onay kutusunu işaretle.":"Veuillez cocher la case de confirmation.", "Bildirimin kaydedildi. Teşekkür ederiz.":"Votre signalement a été enregistré. Merci.",
"Bu kodla eşleşen bir kayıt bulunamadı. Kodu kontrol edip tekrar dene.":"Aucun dossier ne correspond à ce code. Veuillez vérifier le code.",
"Açıklama":"Description", "Olay türü":"Type d’incident", "Ortam":"Lieu", "Tekrar durumu":"Fréquence", "İnceleme durumu":"Statut de l’examen",
"İnceleme bekliyor":"En attente d’examen", "İnceleniyor":"En cours d’examen", "Sonuçlandırıldı":"Clôturé",
"Öncelik sinyali":"Indicateur de priorité", "Sorumlu birim":"Service responsable", "Durumu kaydet":"Enregistrer le statut", "Not ekle":"Ajouter une note",
"Kayıt ara":"Rechercher un dossier", "Tüm durumlar":"Tous les statuts", "Tüm birimler":"Tous les services", "Sıralama":"Tri",
"En yeni önce":"Du plus récent au plus ancien", "En eski önce":"Du plus ancien au plus récent", "Öncelik (yüksekten)":"Priorité (de la plus élevée à la plus faible)",
"İnceleme bilgileri kaydedildi.":"Les informations d’examen ont été enregistrées.", "Değişiklik yapılmadı; bilgiler zaten güncel.":"Aucune modification : les informations sont déjà à jour.",
"Not kaydedildi.":"La note a été enregistrée.", "Not kaydedilemedi.":"La note n’a pas pu être enregistrée.",
"Yönetici erişimi gerekli":"Accès administrateur requis", "Bu bölümü görüntülemek için yönetici oturumu açın.":"Connectez-vous en tant qu’administrateur pour consulter cette rubrique.",
"Kullanıcı adı veya parola yanlış.":"Le nom d’utilisateur ou le mot de passe est incorrect.", "Yönetici bilgileri ayarlanmamış.":"Les identifiants administrateur n’ont pas été configurés.",
"Günlük Durum Özeti":"Synthèse quotidienne", "Bugünkü yeni bildirim":"Nouveaux signalements aujourd’hui", "Aktif yüksek/acil":"Signalements actifs à priorité élevée/urgente",
"İnceleme bekleyen":"En attente d’examen", "Toplam kayıt":"Nombre total de dossiers", "Açık kayıt":"Dossiers ouverts",
"İstatistikler":"Statistiques", "Grafikler yalnızca bu uygulamada kayıtlı bilgileri özetler; okul geneline ilişkin sonuç göstermez.":"Les graphiques résument uniquement les informations enregistrées dans cette application ; ils ne décrivent pas l’ensemble de l’établissement.",
"Sinyal, karar değil":"Un signal n’est pas une décision", "Yetkili kişiler kaydı inceler. Kararı makine vermez.":"Les personnes habilitées examinent le signalement. Le système ne prend aucune décision.",
"Telefon, T.C. no, e-posta ve IBAN otomatik gizlenir.":"Les numéros de téléphone, numéros d’identité turcs, adresses e-mail et IBAN sont automatiquement masqués.",
"Destek rehberi":"Guide d’accompagnement", "Gizlilik ve KVKK paneli":"Espace confidentialité et protection des données", "Araştırma ve kalite kontrol":"Recherche et assurance qualité",
},
"Español": {
"Kimliğini vermeden bildir. Ad, sınıf veya telefon istenmez.":"Envía un aviso sin revelar tu identidad. No se solicita tu nombre, curso ni número de teléfono.",
"Ne oldu?":"¿Qué ha ocurrido?", "Nerede oldu?":"¿Dónde ocurrió?", "Ne zaman oldu?":"¿Cuándo ocurrió?",
"Bu olay kaç kez yaşandı?":"¿Cuántas veces ha ocurrido?", "Olayı kendi cümlelerinle anlat":"Describe lo ocurrido con tus propias palabras",
"Hakaret veya alay":"Insultos o burlas", "Tehdit":"Amenazas", "Dışlama":"Exclusión", "Dijital zorbalık":"Ciberacoso", "Fiziksel zorbalık şüphesi":"Sospecha de acoso físico", "Diğer":"Otro",
"Sınıfta":"En el aula", "Okul bahçesinde":"En el patio del colegio", "Koridorda":"En el pasillo", "Sosyal medyada":"En las redes sociales", "Mesajlaşmada":"En aplicaciones de mensajería",
"Bugün":"Hoy", "Dün":"Ayer", "Bu hafta":"Esta semana", "Daha önce":"Anteriormente", "Emin değilim":"No estoy seguro/a",
"Bir kez":"Una vez", "Birkaç kez":"Varias veces", "Birden fazla kez":"Más de una vez",
"Acil bir durum değil, yalnızca bilgi vermek istiyorum.":"No es una emergencia; solo quiero comunicar una situación.",
"Acil bir tehlike varsa beklemeyin:":"Si existe un peligro inmediato, no esperes:",
"Günde bir bildirim hakkın var.":"Puedes enviar un aviso al día.",
"Bu platform gerçek bir okul sistemine bağlı değildir. Gerçek kişisel veri girmeyin.":"Esta plataforma no está conectada a un sistema escolar real. No introduzcas datos personales reales.",
"Bildirimi gönder":"Enviar aviso", "Gizli takip kodun.":"Tu código confidencial de seguimiento.",
"Durumu sorgula":"Consultar el estado", "Durumu göster":"Mostrar estado", "Ek bilgi ekle":"Añadir información adicional",
"Ek bilgi boş olamaz.":"La información adicional no puede estar vacía.", "Lütfen olayı anlat.":"Describe lo ocurrido, por favor.",
"Lütfen onay kutusunu işaretle.":"Marca la casilla de confirmación, por favor.", "Bildirimin kaydedildi. Teşekkür ederiz.":"Tu aviso se ha registrado. Gracias.",
"Bu kodla eşleşen bir kayıt bulunamadı. Kodu kontrol edip tekrar dene.":"No se ha encontrado ningún registro con ese código. Comprueba el código.",
"Açıklama":"Descripción", "Olay türü":"Tipo de incidente", "Ortam":"Lugar", "Tekrar durumu":"Frecuencia", "İnceleme durumu":"Estado de revisión",
"İnceleme bekliyor":"Pendiente de revisión", "İnceleniyor":"En revisión", "Sonuçlandırıldı":"Cerrado",
"Öncelik sinyali":"Indicador de prioridad", "Sorumlu birim":"Equipo responsable", "Durumu kaydet":"Guardar estado", "Not ekle":"Añadir nota",
"Kayıt ara":"Buscar registro", "Tüm durumlar":"Todos los estados", "Tüm birimler":"Todos los equipos", "Sıralama":"Ordenar",
"En yeni önce":"Más recientes primero", "En eski önce":"Más antiguos primero", "Öncelik (yüksekten)":"Prioridad (de mayor a menor)",
"İnceleme bilgileri kaydedildi.":"La información de revisión se ha guardado.", "Değişiklik yapılmadı; bilgiler zaten güncel.":"No se realizaron cambios; la información ya está actualizada.",
"Not kaydedildi.":"La nota se ha guardado.", "Not kaydedilemedi.":"No se pudo guardar la nota.",
"Yönetici erişimi gerekli":"Se requiere acceso de administración", "Bu bölümü görüntülemek için yönetici oturumu açın.":"Inicia sesión como administrador para ver esta sección.",
"Kullanıcı adı veya parola yanlış.":"El nombre de usuario o la contraseña son incorrectos.", "Yönetici bilgileri ayarlanmamış.":"No se han configurado las credenciales de administración.",
"Günlük Durum Özeti":"Resumen diario", "Bugünkü yeni bildirim":"Avisos nuevos de hoy", "Aktif yüksek/acil":"Avisos activos de prioridad alta/urgente",
"İnceleme bekleyen":"Pendientes de revisión", "Toplam kayıt":"Total de registros", "Açık kayıt":"Avisos abiertos",
"İstatistikler":"Estadísticas", "Grafikler yalnızca bu uygulamada kayıtlı bilgileri özetler; okul geneline ilişkin sonuç göstermez.":"Los gráficos resumen únicamente los datos registrados en esta aplicación; no representan a todo el centro educativo.",
"Sinyal, karar değil":"Una señal no es una decisión", "Yetkili kişiler kaydı inceler. Kararı makine vermez.":"El personal autorizado revisa el aviso. El sistema no toma decisiones.",
"Telefon, T.C. no, e-posta ve IBAN otomatik gizlenir.":"Los teléfonos, números de identidad turcos, correos electrónicos e IBAN se ocultan automáticamente.",
"Destek rehberi":"Guía de apoyo", "Gizlilik ve KVKK paneli":"Panel de privacidad y protección de datos", "Araştırma ve kalite kontrol":"Investigación y control de calidad",
},
"العربية": {
"Kimliğini vermeden bildir. Ad, sınıf veya telefon istenmez.":"قدّم بلاغًا دون الكشف عن هويتك. لا يُطلب اسمك أو صفك أو رقم هاتفك.",
"Ne oldu?":"ماذا حدث؟", "Nerede oldu?":"أين حدث ذلك؟", "Ne zaman oldu?":"متى حدث ذلك؟",
"Bu olay kaç kez yaşandı?":"كم مرة حدث ذلك؟", "Olayı kendi cümlelerinle anlat":"صِف ما حدث بكلماتك الخاصة",
"Hakaret veya alay":"إهانة أو سخرية", "Tehdit":"تهديد", "Dışlama":"إقصاء", "Dijital zorbalık":"تنمّر إلكتروني", "Fiziksel zorbalık şüphesi":"اشتباه في تنمّر جسدي", "Diğer":"أخرى",
"Sınıfta":"في الفصل الدراسي", "Okul bahçesinde":"في ساحة المدرسة", "Koridorda":"في الممر", "Sosyal medyada":"على وسائل التواصل الاجتماعي", "Mesajlaşmada":"في تطبيقات المراسلة",
"Bugün":"اليوم", "Dün":"أمس", "Bu hafta":"هذا الأسبوع", "Daha önce":"سابقًا", "Emin değilim":"لست متأكدًا",
"Bir kez":"مرة واحدة", "Birkaç kez":"عدة مرات", "Birden fazla kez":"أكثر من مرة",
"Acil bir durum değil, yalnızca bilgi vermek istiyorum.":"هذه ليست حالة طارئة؛ أريد فقط تقديم معلومة.",
"Acil bir tehlike varsa beklemeyin:":"إذا كان هناك خطر فوري، فلا تنتظر:",
"Günde bir bildirim hakkın var.":"يمكنك تقديم بلاغ واحد يوميًا.",
"Bu platform gerçek bir okul sistemine bağlı değildir. Gerçek kişisel veri girmeyin.":"هذه المنصة غير متصلة بنظام مدرسي فعلي. لا تُدخل بيانات شخصية حقيقية.",
"Bildirimi gönder":"إرسال البلاغ", "Gizli takip kodun.":"رمز المتابعة السري الخاص بك.",
"Durumu sorgula":"الاستعلام عن الحالة", "Durumu göster":"عرض الحالة", "Ek bilgi ekle":"إضافة معلومات إضافية",
"Ek bilgi boş olamaz.":"لا يمكن أن تكون المعلومات الإضافية فارغة.", "Lütfen olayı anlat.":"يرجى وصف ما حدث.",
"Lütfen onay kutusunu işaretle.":"يرجى تحديد مربع التأكيد.", "Bildirimin kaydedildi. Teşekkür ederiz.":"تم حفظ بلاغك. شكرًا لك.",
"Bu kodla eşleşen bir kayıt bulunamadı. Kodu kontrol edip tekrar dene.":"لم يتم العثور على بلاغ مطابق لهذا الرمز. يرجى التحقق من الرمز.",
"Açıklama":"الوصف", "Olay türü":"نوع الحادثة", "Ortam":"المكان", "Tekrar durumu":"معدل التكرار", "İnceleme durumu":"حالة المراجعة",
"İnceleme bekliyor":"بانتظار المراجعة", "İnceleniyor":"قيد المراجعة", "Sonuçlandırıldı":"مكتمل",
"Öncelik sinyali":"مؤشر الأولوية", "Sorumlu birim":"الجهة المسؤولة", "Durumu kaydet":"حفظ الحالة", "Not ekle":"إضافة ملاحظة",
"Kayıt ara":"البحث عن بلاغ", "Tüm durumlar":"جميع الحالات", "Tüm birimler":"جميع الجهات", "Sıralama":"الترتيب",
"En yeni önce":"الأحدث أولًا", "En eski önce":"الأقدم أولًا", "Öncelik (yüksekten)":"الأولوية (من الأعلى إلى الأقل)",
"İnceleme bilgileri kaydedildi.":"تم حفظ معلومات المراجعة.", "Değişiklik yapılmadı; bilgiler zaten güncel.":"لم يتم إجراء أي تغيير؛ المعلومات محدثة بالفعل.",
"Not kaydedildi.":"تم حفظ الملاحظة.", "Not kaydedilemedi.":"تعذّر حفظ الملاحظة.",
"Yönetici erişimi gerekli":"يلزم الوصول بصلاحية المسؤول", "Bu bölümü görüntülemek için yönetici oturumu açın.":"سجّل الدخول بصفتك مسؤولًا لعرض هذا القسم.",
"Kullanıcı adı veya parola yanlış.":"اسم المستخدم أو كلمة المرور غير صحيحة.", "Yönetici bilgileri ayarlanmamış.":"لم يتم إعداد بيانات اعتماد المسؤول.",
"Günlük Durum Özeti":"الملخص اليومي للحالة", "Bugünkü yeni bildirim":"البلاغات الجديدة اليوم", "Aktif yüksek/acil":"البلاغات النشطة ذات الأولوية العالية أو العاجلة",
"İnceleme bekleyen":"بانتظار المراجعة", "Toplam kayıt":"إجمالي البلاغات", "Açık kayıt":"البلاغات المفتوحة",
"İstatistikler":"الإحصاءات", "Grafikler yalnızca bu uygulamada kayıtlı bilgileri özetler; okul geneline ilişkin sonuç göstermez.":"تلخّص الرسوم البيانية البيانات المسجلة في هذا التطبيق فقط، ولا تمثل نتائج المدرسة بأكملها.",
"Sinyal, karar değil":"المؤشر ليس قرارًا", "Yetkili kişiler kaydı inceler. Kararı makine vermez.":"يراجع الأشخاص المخوّلون البلاغ. ولا يتخذ النظام القرار.",
"Telefon, T.C. no, e-posta ve IBAN otomatik gizlenir.":"تُخفى أرقام الهواتف وأرقام الهوية التركية وعناوين البريد الإلكتروني وأرقام IBAN تلقائيًا.",
"Destek rehberi":"دليل الدعم", "Gizlilik ve KVKK paneli":"لوحة الخصوصية وحماية البيانات", "Araştırma ve kalite kontrol":"البحث وضمان الجودة",
},
"Azərbaycan dili": {
"Kimliğini vermeden bildir. Ad, sınıf veya telefon istenmez.":"Şəxsiyyətini açıqlamadan bildiriş göndər. Ad, sinif və telefon nömrəsi tələb olunmur.",
"Ne oldu?":"Nə baş verdi?", "Nerede oldu?":"Harada baş verdi?", "Ne zaman oldu?":"Nə vaxt baş verdi?",
"Bu olay kaç kez yaşandı?":"Bu hadisə neçə dəfə baş verib?", "Olayı kendi cümlelerinle anlat":"Baş verənləri öz sözlərinlə təsvir et",
"Hakaret veya alay":"Təhqir və ya lağ", "Tehdit":"Təhdid", "Dışlama":"Kənarlaşdırma", "Dijital zorbalık":"Kiberzorakılıq", "Fiziksel zorbalık şüphesi":"Fiziki zorakılıq şübhəsi", "Diğer":"Digər",
"Sınıfta":"Sinifdə", "Okul bahçesinde":"Məktəb həyətində", "Koridorda":"Dəhlizdə", "Sosyal medyada":"Sosial mediada", "Mesajlaşmada":"Mesajlaşma tətbiqlərində",
"Bugün":"Bu gün", "Dün":"Dünən", "Bu hafta":"Bu həftə", "Daha önce":"Əvvəllər", "Emin değilim":"Əmin deyiləm",
"Bir kez":"Bir dəfə", "Birkaç kez":"Bir neçə dəfə", "Birden fazla kez":"Bir dəfədən çox",
"Acil bir durum değil, yalnızca bilgi vermek istiyorum.":"Bu təcili vəziyyət deyil; sadəcə məlumat vermək istəyirəm.",
"Acil bir tehlike varsa beklemeyin:":"Təcili təhlükə varsa gözləməyin:",
"Günde bir bildirim hakkın var.":"Gündə bir bildiriş göndərə bilərsiniz.",
"Bu platform gerçek bir okul sistemine bağlı değildir. Gerçek kişisel veri girmeyin.":"Bu platform real məktəb sisteminə qoşulmayıb. Həqiqi şəxsi məlumatları daxil etməyin.",
"Bildirimi gönder":"Bildirişi göndər", "Gizli takip kodun.":"Məxfi izləmə kodunuz.",
"Durumu sorgula":"Statusu yoxla", "Durumu göster":"Statusu göstər", "Ek bilgi ekle":"Əlavə məlumat əlavə et",
"Ek bilgi boş olamaz.":"Əlavə məlumat boş ola bilməz.", "Lütfen olayı anlat.":"Zəhmət olmasa, baş verənləri təsvir edin.",
"Lütfen onay kutusunu işaretle.":"Zəhmət olmasa, təsdiq xanasını işarələyin.", "Bildirimin kaydedildi. Teşekkür ederiz.":"Bildirişiniz yadda saxlanıldı. Təşəkkür edirik.",
"Bu kodla eşleşen bir kayıt bulunamadı. Kodu kontrol edip tekrar dene.":"Bu kodla uyğun qeyd tapılmadı. Zəhmət olmasa kodu yoxlayın.",
"Açıklama":"Təsvir", "Olay türü":"Hadisə növü", "Ortam":"Mühit", "Tekrar durumu":"Təkrarlanma tezliyi", "İnceleme durumu":"Yoxlama statusu",
"İnceleme bekliyor":"Yoxlanılmağı gözləyir", "İnceleniyor":"Yoxlanılır", "Sonuçlandırıldı":"Tamamlandı",
"Öncelik sinyali":"Prioritet göstəricisi", "Sorumlu birim":"Məsul bölmə", "Durumu kaydet":"Statusu yadda saxla", "Not ekle":"Qeyd əlavə et",
"Kayıt ara":"Qeydi axtar", "Tüm durumlar":"Bütün statuslar", "Tüm birimler":"Bütün bölmələr", "Sıralama":"Sıralama",
"En yeni önce":"Əvvəlcə ən yenilər", "En eski önce":"Əvvəlcə ən köhnələr", "Öncelik (yüksekten)":"Prioritet (yüksəkdən aşağıya)",
"İnceleme bilgileri kaydedildi.":"Yoxlama məlumatları yadda saxlanıldı.", "Değişiklik yapılmadı; bilgiler zaten güncel.":"Dəyişiklik edilmədi; məlumatlar artıq yenidir.",
"Not kaydedildi.":"Qeyd yadda saxlanıldı.", "Not kaydedilemedi.":"Qeydi yadda saxlamaq mümkün olmadı.",
"Yönetici erişimi gerekli":"Administrator girişi tələb olunur", "Bu bölümü görüntülemek için yönetici oturumu açın.":"Bu bölməyə baxmaq üçün administrator kimi daxil olun.",
"Kullanıcı adı veya parola yanlış.":"İstifadəçi adı və ya şifrə yanlışdır.", "Yönetici bilgileri ayarlanmamış.":"Administrator giriş məlumatları təyin edilməyib.",
"Günlük Durum Özeti":"Gündəlik vəziyyət xülasəsi", "Bugünkü yeni bildirim":"Bu günün yeni bildirişləri", "Aktif yüksek/acil":"Aktiv yüksək/təcili prioritetli bildirişlər",
"İnceleme bekleyen":"Yoxlanılmağı gözləyən", "Toplam kayıt":"Ümumi qeyd sayı", "Açık kayıt":"Açıq bildirişlər",
"İstatistikler":"Statistika", "Grafikler yalnızca bu uygulamada kayıtlı bilgileri özetler; okul geneline ilişkin sonuç göstermez.":"Qrafiklər yalnız bu tətbiqdə qeydə alınmış məlumatları ümumiləşdirir; bütün məktəb üzrə nəticələri göstərmir.",
"Sinyal, karar değil":"Siqnal qərar deyil", "Yetkili kişiler kaydı inceler. Kararı makine vermez.":"Bildirişi səlahiyyətli şəxslər yoxlayır. Qərarı sistem vermir.",
"Telefon, T.C. no, e-posta ve IBAN otomatik gizlenir.":"Telefon nömrələri, Türkiyə şəxsiyyət nömrələri, e-poçt ünvanları və IBAN avtomatik maskalanır.",
"Destek rehberi":"Dəstək bələdçisi", "Gizlilik ve KVKK paneli":"Məxfilik və fərdi məlumatların qorunması paneli", "Araştırma ve kalite kontrol":"Tədqiqat və keyfiyyətə nəzarət",
},
}
_ENUM_TRANSLATIONS = {
"Deutsch": {"Bir kez oldu":"Einmal passiert", "Birkaç kez oldu":"Ein paar Mal passiert", "Sık sık / sürekli oluyor":"Häufig / ständig", "Takip gerekiyor":"Weitere Beobachtung erforderlich", "Henüz atanmadı":"Noch nicht zugewiesen", "Rehberlik birimi":"Beratungsstelle", "Okul yönetimi":"Schulleitung", "Öğrenci destek ekibi":"Schüler:innen-Unterstützungsteam", "Sinyal yok":"Kein Signal", "Diğer":"Sonstiges"},
"Français": {"Bir kez oldu":"Une seule fois", "Birkaç kez oldu":"Quelques fois", "Sık sık / sürekli oluyor":"Fréquemment / continuellement", "Takip gerekiyor":"Un suivi est nécessaire", "Henüz atanmadı":"Pas encore attribué", "Rehberlik birimi":"Service d’accompagnement", "Okul yönetimi":"Direction de l’établissement", "Öğrenci destek ekibi":"Équipe de soutien aux élèves", "Sinyal yok":"Aucun indicateur", "Diğer":"Autre"},
"Español": {"Bir kez oldu":"Ha ocurrido una vez", "Birkaç kez oldu":"Ha ocurrido varias veces", "Sık sık / sürekli oluyor":"Ocurre con frecuencia o continuamente", "Takip gerekiyor":"Requiere seguimiento", "Henüz atanmadı":"Aún sin asignar", "Rehberlik birimi":"Servicio de orientación", "Okul yönetimi":"Dirección del centro", "Öğrenci destek ekibi":"Equipo de apoyo al alumnado", "Sinyal yok":"Sin indicador", "Diğer":"Otro"},
"العربية": {"Bir kez oldu":"حدث مرة واحدة", "Birkaç kez oldu":"حدث عدة مرات", "Sık sık / sürekli oluyor":"يحدث بشكل متكرر أو مستمر", "Takip gerekiyor":"يتطلب المتابعة", "Henüz atanmadı":"لم يتم التعيين بعد", "Rehberlik birimi":"وحدة الإرشاد المدرسي", "Okul yönetimi":"إدارة المدرسة", "Öğrenci destek ekibi":"فريق دعم الطلاب", "Sinyal yok":"لا يوجد مؤشر", "Diğer":"أخرى"},
"Azərbaycan dili": {"Bir kez oldu":"Bir dəfə baş verib", "Birkaç kez oldu":"Bir neçə dəfə baş verib", "Sık sık / sürekli oluyor":"Tez-tez / davamlı baş verir", "Takip gerekiyor":"İzləmə tələb olunur", "Henüz atanmadı":"Hələ təyin edilməyib", "Rehberlik birimi":"Psixoloji dəstək bölməsi", "Okul yönetimi":"Məktəb rəhbərliyi", "Öğrenci destek ekibi":"Şagirdlərə dəstək qrupu", "Sinyal yok":"Göstərici yoxdur", "Diğer":"Digər"},
}
for _language, _entries in _ENUM_TRANSLATIONS.items():
    MULTI_CATALOG[_language].update(_entries)

for _language, _entries in _EXPANDED_UI.items():
    MULTI_CATALOG[_language].update(_entries)

# Additional page-level copy for tracking, review, guidance and privacy screens.
_PAGE_COPY = {
"Deutsch": {
"İnceleme kuyruğunu aç":"Prüfwarteschlange öffnen", "Kodumu not aldım":"Ich habe meinen Code notiert", "Hazırlanıyor…":"Wird vorbereitet…",
"Günlük bildirim hakkınız dolmuştur. Yarın yeniden bildirim yapabilirsin. Bugünkü bildirimine takip koduyla ek bilgi ekleyebilirsin.":"Du hast dein tägliches Meldelimit erreicht. Morgen kannst du erneut eine Meldung einreichen. Mit deinem Tracking-Code kannst du deiner heutigen Meldung weitere Informationen hinzufügen.",
"Bildirimime ek bilgi ekle":"Meiner Meldung Informationen hinzufügen", "Ne oldu, nerede ve ne zaman oldu? Ad, telefon gibi bilgileri yazma.":"Beschreibe, was, wo und wann passiert ist. Gib keine Namen, Telefonnummern oder andere persönliche Angaben ein.",
"Ek bilgi yalnızca anonim bildirimlerde, bildirimin yapıldığı gün ve bildirim sonuçlanmadan önce eklenebilir.":"Zusätzliche Informationen können nur zu anonymen Meldungen, am Tag der Einreichung und vor Abschluss der Prüfung hinzugefügt werden.",
"Bugün için ek bilgi sınırına ulaştın.":"Du hast das heutige Limit für zusätzliche Informationen erreicht.", "Eklemek istediğin bilgi":"Welche zusätzlichen Informationen möchtest du hinzufügen?", "Ad, telefon gibi bilgileri yazma.":"Gib keine Namen, Telefonnummern oder ähnliche Angaben ein.", "Ek bilgiyi gönder":"Zusätzliche Informationen senden",
"Yönetici oturumu açık.":"Administrator-Sitzung ist aktiv.", "Sistem genelinde çok fazla hatalı giriş denemesi var. Lütfen bir süre sonra tekrar deneyin.":"Es gab systemweit zu viele fehlgeschlagene Anmeldeversuche. Bitte versuche es später erneut.",
"Otomatik sinyal ve değerlendirme notu":"Automatisches Signal und Bewertungshinweis", "Değişiklikleri kaydet":"Änderungen speichern", "İnceleme notları":"Prüfnotizen", "İşlem geçmişi":"Aktivitätsverlauf",
"Platformun işlevleri":"Funktionen der Plattform", "Sınırlar":"Grenzen", "Gerçek kullanıma geçmeden önce (kontrol listesi)":"Checkliste vor einem echten Einsatz",
"Değerlendirmeyi çalıştır":"Auswertung durchführen", "Sonucu JSON olarak indir":"Ergebnis als JSON herunterladen", "Karışıklık matrisi":"Konfusionsmatrix", "Örnek türüne göre doğruluk":"Genauigkeit nach Beispieldatentyp", "Kategoriye göre yakalama (duyarlılık)":"Erkennung nach Kategorie (Sensitivität)",
"Bildirim ayrıntıları":"Meldungsdetails", "İnceleme ve yönlendirme":"Prüfung und Weiterleitung", "İnceleme notları":"Prüfnotizen", "İşlem geçmişi":"Aktivitätsverlauf",
"Gizlilik ve KVKK paneli":"Datenschutzbereich", "Aydınlatma metni":"Datenschutzhinweis", "Veri envanteri":"Datenverzeichnis", "Saklama ve imha":"Aufbewahrung und Löschung", "Onam akışı (simülasyon)":"Einwilligungsablauf (Simulation)",
"Katılımcının yaş grubu":"Altersgruppe der teilnehmenden Person", "18 yaşından küçük":"Unter 18 Jahre", "18 yaş ve üzeri":"18 Jahre oder älter", "İleri":"Weiter", "Baştan başla":"Von vorn beginnen",
},
"Français": {
"İnceleme kuyruğunu aç":"Ouvrir la file d’examen", "Kodumu not aldım":"J’ai noté mon code", "Hazırlanıyor…":"Préparation…",
"Günlük bildirim hakkınız dolmuştur. Yarın yeniden bildirim yapabilirsin. Bugünkü bildirimine takip koduyla ek bilgi ekleyebilirsin.":"Vous avez atteint votre limite quotidienne de signalements. Vous pourrez en envoyer un nouveau demain. Vous pouvez ajouter des informations à celui d’aujourd’hui à l’aide de votre code de suivi.",
"Bildirimime ek bilgi ekle":"Ajouter des informations à mon signalement", "Ne oldu, nerede ve ne zaman oldu? Ad, telefon gibi bilgileri yazma.":"Décrivez ce qui s’est passé, où et quand. N’indiquez ni nom, ni numéro de téléphone, ni autre donnée permettant d’identifier quelqu’un.",
"Ek bilgi yalnızca anonim bildirimlerde, bildirimin yapıldığı gün ve bildirim sonuçlanmadan önce eklenebilir.":"Des informations complémentaires peuvent être ajoutées uniquement aux signalements anonymes, le jour de leur envoi et avant leur clôture.",
"Bugün için ek bilgi sınırına ulaştın.":"Vous avez atteint la limite quotidienne d’informations complémentaires.", "Eklemek istediğin bilgi":"Informations complémentaires à ajouter", "Ad, telefon gibi bilgileri yazma.":"N’indiquez pas de nom, de numéro de téléphone ni d’autres données personnelles.", "Ek bilgiyi gönder":"Envoyer les informations complémentaires",
"Yönetici oturumu açık.":"La session administrateur est ouverte.", "Sistem genelinde çok fazla hatalı giriş denemesi var. Lütfen bir süre sonra tekrar deneyin.":"Le système a enregistré trop de tentatives de connexion échouées. Veuillez réessayer plus tard.",
"Otomatik sinyal ve değerlendirme notu":"Indicateur automatique et note d’évaluation", "Değişiklikleri kaydet":"Enregistrer les modifications", "İnceleme notları":"Notes d’examen", "İşlem geçmişi":"Historique des actions",
"Platformun işlevleri":"Fonctionnalités de la plateforme", "Sınırlar":"Limites", "Gerçek kullanıma geçmeden önce (kontrol listesi)":"Liste de vérification avant toute utilisation réelle",
"Değerlendirmeyi çalıştır":"Lancer l’évaluation", "Sonucu JSON olarak indir":"Télécharger le résultat au format JSON", "Karışıklık matrisi":"Matrice de confusion", "Örnek türüne göre doğruluk":"Précision par type d’exemple", "Kategoriye göre yakalama (duyarlılık)":"Détection par catégorie (sensibilité)",
"Bildirim ayrıntıları":"Détails du signalement", "İnceleme ve yönlendirme":"Examen et orientation",
"Aydınlatma metni":"Notice d’information", "Veri envanteri":"Inventaire des données", "Saklama ve imha":"Conservation et suppression", "Onam akışı (simülasyon)":"Parcours de consentement (simulation)",
"Katılımcının yaş grubu":"Tranche d’âge de la personne participante", "18 yaşından küçük":"Moins de 18 ans", "18 yaş ve üzeri":"18 ans ou plus", "İleri":"Suivant", "Baştan başla":"Recommencer",
},
"Español": {
"İnceleme kuyruğunu aç":"Abrir la cola de revisión", "Kodumu not aldım":"He guardado mi código", "Hazırlanıyor…":"Preparando…",
"Günlük bildirim hakkınız dolmuştur. Yarın yeniden bildirim yapabilirsin. Bugünkü bildirimine takip koduyla ek bilgi ekleyebilirsin.":"Has alcanzado el límite diario de avisos. Podrás enviar otro mañana. Puedes añadir información al aviso de hoy con tu código de seguimiento.",
"Bildirimime ek bilgi ekle":"Añadir información a mi aviso", "Ne oldu, nerede ve ne zaman oldu? Ad, telefon gibi bilgileri yazma.":"Describe qué ocurrió, dónde y cuándo. No incluyas nombres, teléfonos ni otros datos que permitan identificar a alguien.",
"Ek bilgi yalnızca anonim bildirimlerde, bildirimin yapıldığı gün ve bildirim sonuçlanmadan önce eklenebilir.":"Solo se puede añadir información a avisos anónimos el mismo día en que se envían y antes de que se cierren.",
"Bugün için ek bilgi sınırına ulaştın.":"Has alcanzado el límite de información adicional de hoy.", "Eklemek istediğin bilgi":"Información adicional que deseas añadir", "Ad, telefon gibi bilgileri yazma.":"No incluyas nombres, teléfonos ni otros datos personales.", "Ek bilgiyi gönder":"Enviar información adicional",
"Yönetici oturumu açık.":"La sesión de administración está activa.", "Sistem genelinde çok fazla hatalı giriş denemesi var. Lütfen bir süre sonra tekrar deneyin.":"Se han producido demasiados intentos fallidos de acceso en el sistema. Inténtalo de nuevo más tarde.",
"Otomatik sinyal ve değerlendirme notu":"Indicador automático y nota de evaluación", "Değişiklikleri kaydet":"Guardar cambios", "İnceleme notları":"Notas de revisión", "İşlem geçmişi":"Historial de actividad",
"Platformun işlevleri":"Funciones de la plataforma", "Sınırlar":"Limitaciones", "Gerçek kullanıma geçmeden önce (kontrol listesi)":"Lista de comprobación antes de un uso real",
"Değerlendirmeyi çalıştır":"Ejecutar evaluación", "Sonucu JSON olarak indir":"Descargar resultado en JSON", "Karışıklık matrisi":"Matriz de confusión", "Örnek türüne göre doğruluk":"Precisión por tipo de ejemplo", "Kategoriye göre yakalama (duyarlılık)":"Detección por categoría (sensibilidad)",
"Bildirim ayrıntıları":"Detalles del aviso", "İnceleme ve yönlendirme":"Revisión y derivación",
"Aydınlatma metni":"Aviso de privacidad", "Veri envanteri":"Inventario de datos", "Saklama ve imha":"Conservación y eliminación", "Onam akışı (simülasyon)":"Proceso de consentimiento (simulación)",
"Katılımcının yaş grubu":"Grupo de edad de la persona participante", "18 yaşından küçük":"Menor de 18 años", "18 yaş ve üzeri":"18 años o más", "İleri":"Continuar", "Baştan başla":"Volver a empezar",
},
"العربية": {
"İnceleme kuyruğunu aç":"فتح قائمة البلاغات للمراجعة", "Kodumu not aldım":"لقد احتفظت بالرمز", "Hazırlanıyor…":"جارٍ التحضير…",
"Günlük bildirim hakkınız dolmuştur. Yarın yeniden bildirim yapabilirsin. Bugünkü bildirimine takip koduyla ek bilgi ekleyebilirsin.":"لقد وصلت إلى الحد اليومي للبلاغات. يمكنك تقديم بلاغ جديد غدًا، كما يمكنك إضافة معلومات إلى بلاغ اليوم باستخدام رمز المتابعة.",
"Bildirimime ek bilgi ekle":"إضافة معلومات إلى بلاغي", "Ne oldu, nerede ve ne zaman oldu? Ad, telefon gibi bilgileri yazma.":"وضّح ما الذي حدث وأين ومتى. لا تكتب أسماء أو أرقام هواتف أو أي معلومات تكشف الهوية.",
"Ek bilgi yalnızca anonim bildirimlerde, bildirimin yapıldığı gün ve bildirim sonuçlanmadan önce eklenebilir.":"يمكن إضافة معلومات إلى البلاغات المجهولة فقط، في يوم تقديم البلاغ وقبل إغلاقه.",
"Bugün için ek bilgi sınırına ulaştın.":"لقد وصلت إلى الحد اليومي لإضافة المعلومات.", "Eklemek istediğin bilgi":"المعلومات الإضافية التي تريد إدخالها", "Ad, telefon gibi bilgileri yazma.":"لا تكتب أسماء أو أرقام هواتف أو معلومات شخصية أخرى.", "Ek bilgiyi gönder":"إرسال المعلومات الإضافية",
"Yönetici oturumu açık.":"جلسة المسؤول مفتوحة.", "Sistem genelinde çok fazla hatalı giriş denemesi var. Lütfen bir süre sonra tekrar deneyin.":"تم تسجيل عدد كبير جدًا من محاولات الدخول الفاشلة على مستوى النظام. يرجى المحاولة لاحقًا.",
"Otomatik sinyal ve değerlendirme notu":"المؤشر الآلي وملاحظة التقييم", "Değişiklikleri kaydet":"حفظ التغييرات", "İnceleme notları":"ملاحظات المراجعة", "İşlem geçmişi":"سجل الإجراءات",
"Platformun işlevleri":"وظائف المنصة", "Sınırlar":"الحدود", "Gerçek kullanıma geçmeden önce (kontrol listesi)":"قائمة التحقق قبل الاستخدام الفعلي",
"Değerlendirmeyi çalıştır":"تشغيل التقييم", "Sonucu JSON olarak indir":"تنزيل النتيجة بصيغة JSON", "Karışıklık matrisi":"مصفوفة الالتباس", "Örnek türüne göre doğruluk":"الدقة حسب نوع العينة", "Kategoriye göre yakalama (duyarlılık)":"الكشف حسب الفئة (الحساسية)",
"Bildirim ayrıntıları":"تفاصيل البلاغ", "İnceleme ve yönlendirme":"المراجعة والإحالة",
"Aydınlatma metni":"إشعار الخصوصية", "Veri envanteri":"سجل البيانات", "Saklama ve imha":"الاحتفاظ بالبيانات وحذفها", "Onam akışı (simülasyon)":"مسار الموافقة (محاكاة)",
"Katılımcının yaş grubu":"الفئة العمرية للمشارك", "18 yaşından küçük":"أقل من 18 عامًا", "18 yaş ve üzeri":"18 عامًا فأكثر", "İleri":"متابعة", "Baştan başla":"البدء من جديد",
},
"Azərbaycan dili": {
"İnceleme kuyruğunu aç":"Yoxlama növbəsini aç", "Kodumu not aldım":"Kodumu qeyd etdim", "Hazırlanıyor…":"Hazırlanır…",
"Günlük bildirim hakkınız dolmuştur. Yarın yeniden bildirim yapabilirsin. Bugünkü bildirimine takip koduyla ek bilgi ekleyebilirsin.":"Gündəlik bildiriş limitiniz bitib. Sabah yenidən bildiriş göndərə bilərsiniz. Bugünkü bildirişə izləmə kodu ilə əlavə məlumat daxil edə bilərsiniz.",
"Bildirimime ek bilgi ekle":"Bildirişimə əlavə məlumat daxil et", "Ne oldu, nerede ve ne zaman oldu? Ad, telefon gibi bilgileri yazma.":"Nə baş verdiyini, harada və nə vaxt baş verdiyini təsvir edin. Ad, telefon nömrəsi və digər şəxsi məlumatları yazmayın.",
"Ek bilgi yalnızca anonim bildirimlerde, bildirimin yapıldığı gün ve bildirim sonuçlanmadan önce eklenebilir.":"Əlavə məlumat yalnız anonim bildirişlərə, bildiriş göndərilən gün və yoxlama tamamlanmazdan əvvəl əlavə edilə bilər.",
"Bugün için ek bilgi sınırına ulaştın.":"Bu gün üçün əlavə məlumat limitinə çatmısınız.", "Eklemek istediğin bilgi":"Əlavə etmək istədiyiniz məlumat", "Ad, telefon gibi bilgileri yazma.":"Ad, telefon nömrəsi və digər şəxsi məlumatları yazmayın.", "Ek bilgiyi gönder":"Əlavə məlumatı göndər",
"Yönetici oturumu açık.":"Administrator sessiyası aktivdir.", "Sistem genelinde çok fazla hatalı giriş denemesi var. Lütfen bir süre sonra tekrar deneyin.":"Sistem üzrə çoxsaylı uğursuz giriş cəhdi qeydə alınıb. Bir qədər sonra yenidən cəhd edin.",
"Otomatik sinyal ve değerlendirme notu":"Avtomatik göstərici və qiymətləndirmə qeydi", "Değişiklikleri kaydet":"Dəyişiklikləri yadda saxla", "İnceleme notları":"Yoxlama qeydləri", "İşlem geçmişi":"Əməliyyat tarixçəsi",
"Platformun işlevleri":"Platformun funksiyaları", "Sınırlar":"Məhdudiyyətlər", "Gerçek kullanıma geçmeden önce (kontrol listesi)":"Real istifadədən əvvəl yoxlama siyahısı",
"Değerlendirmeyi çalıştır":"Qiymətləndirməni işə sal", "Sonucu JSON olarak indir":"Nəticəni JSON formatında yüklə", "Karışıklık matrisi":"Qarışıqlıq matrisi", "Örnek türüne göre doğruluk":"Nümunə növünə görə dəqiqlik", "Kategoriye göre yakalama (duyarlılık)":"Kateqoriya üzrə aşkarlama (həssaslıq)",
"Bildirim ayrıntıları":"Bildiriş təfərrüatları", "İnceleme ve yönlendirme":"Yoxlama və yönləndirmə",
"Aydınlatma metni":"Məlumatlandırma mətni", "Veri envanteri":"Məlumatların reyestri", "Saklama ve imha":"Saxlanma və məhv edilmə", "Onam akışı (simülasyon)":"Razılıq prosesi (simulyasiya)",
"Katılımcının yaş grubu":"İştirakçının yaş qrupu", "18 yaşından küçük":"18 yaşdan kiçik", "18 yaş ve üzeri":"18 yaş və yuxarı", "İleri":"İrəli", "Baştan başla":"Yenidən başla",
},
}
for _language, _entries in _PAGE_COPY.items():
    MULTI_CATALOG[_language].update(_entries)

# Homepage copy: complete, reviewed translations for the first screen.
# These entries intentionally cover every visible sentence in the landing-page cards
# and emergency banner so languages do not fall back to Turkish or mix languages.
_HOME_COPY = {
"Deutsch": {
"Zorbalığı kimliğini vermeden bildir, gizli kodunla durumu takip et.":"Melde Mobbing, ohne deine Identität preiszugeben, und verfolge den Status mit deinem vertraulichen Code.",
"Nasıl kullanılır?":"So funktioniert es", "1 · Bildir":"1 · Melden",
"Formu doldur. Ad ve sınıf istenmez; sana gizli bir kod verilir.":"Fülle das Formular aus. Name und Klasse werden nicht abgefragt; du erhältst einen vertraulichen Code.",
"2 · Takip et":"2 · Nachverfolgen", "Kodunla durumu gör, aynı gün ek bilgi ekle.":"Prüfe den Status mit deinem Code und ergänze noch am selben Tag weitere Informationen.",
"3 · İnsan inceler":"3 · Menschliche Prüfung", "Yetkili kişiler kaydı inceler. Kararı makine vermez.":"Befugte Mitarbeitende prüfen die Meldung. Das System trifft keine Entscheidungen.",
"Acil bir tehlike varsa beklemeyin:":"Bei unmittelbarer Gefahr nicht warten:",
"Acil Çağrı Merkezi (Polis, Sağlık, Jandarma - 7/24)":"Notrufzentrale (Polizei, Rettungsdienst und Gendarmerie – rund um die Uhr)",
"ALO Sosyal Destek Hattı (7/24)":"ALO-Sozialhilfetelefon (rund um die Uhr)", "MEB İletişim Merkezi (MEBİM)":"Kontaktzentrum des türkischen Bildungsministeriums (MEBİM)",
"Rehberlik bilgi bankası":"Beratungsangebote", "Güvenlik ilkeleri":"Sicherheitsgrundsätze", "Gizlilik":"Datenschutz", "Sinyal, karar değil":"Ein Hinweis ist keine Entscheidung", "Hesap verebilirlik":"Rechenschaftspflicht",
"Yaşıyorsan":"Wenn du betroffen bist", "Kime anlatabileceğini ve neler yapabileceğini öğren.":"Erfahre, mit wem du sprechen kannst und was du tun kannst.", "Tanık olduysan":"Wenn du etwas beobachtet hast", "Sessiz kalmadan, güvenli şekilde nasıl destek olursun?":"Wie kannst du helfen, ohne zu schweigen und ohne dich zu gefährden?", "Veli ve öğretmenler":"Eltern und Lehrkräfte", "İşaretleri tanı, çocuğu dinle, doğru adımı at.":"Erkenzeichen erkennen, dem Kind zuhören und angemessen handeln.",
"Telefon, T.C. no, e-posta ve IBAN otomatik gizlenir.":"Telefonnummern, türkische Identifikationsnummern, E-Mail-Adressen und IBANs werden automatisch unkenntlich gemacht.", "Otomatik eşleşme yalnızca inceleme sırasına yardım eder.":"Automatische Treffer helfen lediglich bei der Priorisierung der Prüfung.", "Yönetici işlemleri kim yaptığıyla kayda geçer.":"Administratoraktionen werden mit Angabe der ausführenden Person protokolliert.",
},
"Français": {
"Zorbalığı kimliğini vermeden bildir, gizli kodunla durumu takip et.":"Signalez une situation de harcèlement sans révéler votre identité et suivez son état grâce à votre code confidentiel.",
"Nasıl kullanılır?":"Comment ça marche", "1 · Bildir":"1 · Signaler",
"Formu doldur. Ad ve sınıf istenmez; sana gizli bir kod verilir.":"Remplissez le formulaire. Votre nom et votre classe ne sont pas demandés ; un code confidentiel vous sera attribué.",
"2 · Takip et":"2 · Suivre", "Kodunla durumu gör, aynı gün ek bilgi ekle.":"Consultez l’état du signalement avec votre code et ajoutez des précisions le jour même.",
"3 · İnsan inceler":"3 · Examen humain", "Yetkili kişiler kaydı inceler. Kararı makine vermez.":"Le signalement est examiné par des personnes habilitées. Le système ne prend aucune décision.",
"Acil bir tehlike varsa beklemeyin:":"En cas de danger immédiat, n’attendez pas :",
"Acil Çağrı Merkezi (Polis, Sağlık, Jandarma - 7/24)":"Centre d’urgence 112 (police, secours médicaux et gendarmerie – 24 h/24)",
"ALO Sosyal Destek Hattı (7/24)":"Ligne d’aide sociale ALO 183 (24 h/24)", "MEB İletişim Merkezi (MEBİM)":"Centre de contact du ministère turc de l’Éducation (MEBİM)",
"Rehberlik bilgi bankası":"Ressources d’accompagnement", "Güvenlik ilkeleri":"Principes de sécurité", "Gizlilik":"Confidentialité", "Sinyal, karar değil":"Un signalement n’est pas une décision", "Hesap verebilirlik":"Responsabilité",
"Yaşıyorsan":"Si vous êtes concerné", "Kime anlatabileceğini ve neler yapabileceğini öğren.":"Découvrez à qui en parler et quelles démarches entreprendre.", "Tanık olduysan":"Si vous êtes témoin", "Sessiz kalmadan, güvenli şekilde nasıl destek olursun?":"Comment apporter votre soutien en toute sécurité, sans rester silencieux ?", "Veli ve öğretmenler":"Parents et personnel éducatif", "İşaretleri tanı, çocuğu dinle, doğru adımı at.":"Repérez les signes, écoutez l’enfant et adoptez la bonne démarche.",
"Telefon, T.C. no, e-posta ve IBAN otomatik gizlenir.":"Les numéros de téléphone, numéros d’identité turcs, adresses e-mail et IBAN sont automatiquement masqués.", "Otomatik eşleşme yalnızca inceleme sırasına yardım eder.":"Les correspondances automatiques aident uniquement à organiser l’ordre des examens.", "Yönetici işlemleri kim yaptığıyla kayda geçer.":"Les actions des administrateurs sont consignées avec l’identité de leur auteur.",
},
"Español": {
"Zorbalığı kimliğini vermeden bildir, gizli kodunla durumu takip et.":"Comunica una situación de acoso sin revelar tu identidad y consulta su estado con tu código privado.",
"Nasıl kullanılır?":"Cómo funciona", "1 · Bildir":"1 · Comunicar",
"Formu doldur. Ad ve sınıf istenmez; sana gizli bir kod verilir.":"Completa el formulario. No se solicitan tu nombre ni tu curso; recibirás un código privado.",
"2 · Takip et":"2 · Consultar", "Kodunla durumu gör, aynı gün ek bilgi ekle.":"Consulta el estado con tu código y añade información adicional ese mismo día.",
"3 · İnsan inceler":"3 · Revisión humana", "Yetkili kişiler kaydı inceler. Kararı makine vermez.":"El aviso es revisado por personal autorizado. El sistema no toma decisiones.",
"Acil bir tehlike varsa beklemeyin:":"Si existe un peligro inmediato, no esperes:",
"Acil Çağrı Merkezi (Polis, Sağlık, Jandarma - 7/24)":"Centro de Emergencias 112 (policía, servicios médicos y gendarmería, 24 horas)",
"ALO Sosyal Destek Hattı (7/24)":"Línea de apoyo social ALO 183 (24 horas)", "MEB İletişim Merkezi (MEBİM)":"Centro de Atención del Ministerio de Educación de Turquía (MEBİM)",
"Rehberlik bilgi bankası":"Recursos de orientación", "Güvenlik ilkeleri":"Principios de seguridad", "Gizlilik":"Privacidad", "Sinyal, karar değil":"Una señal no es una decisión", "Hesap verebilirlik":"Rendición de cuentas",
"Yaşıyorsan":"Si te está ocurriendo", "Kime anlatabileceğini ve neler yapabileceğini öğren.":"Descubre con quién puedes hablar y qué puedes hacer.", "Tanık olduysan":"Si has sido testigo", "Sessiz kalmadan, güvenli şekilde nasıl destek olursun?":"¿Cómo puedes ayudar de forma segura sin quedarte en silencio?", "Veli ve öğretmenler":"Familias y docentes", "İşaretleri tanı, çocuğu dinle, doğru adımı at.":"Reconoce las señales, escucha al menor y actúa de forma adecuada.",
"Telefon, T.C. no, e-posta ve IBAN otomatik gizlenir.":"Los teléfonos, números de identidad turcos, correos electrónicos e IBAN se ocultan automáticamente.", "Otomatik eşleşme yalnızca inceleme sırasına yardım eder.":"Las coincidencias automáticas solo ayudan a organizar la revisión.", "Yönetici işlemleri kim yaptığıyla kayda geçer.":"Las acciones administrativas quedan registradas junto con la persona que las realizó.",
},
"العربية": {
"Zorbalığı kimliğini vermeden bildir, gizli kodunla durumu takip et.":"أبلغ عن التنمّر دون الكشف عن هويتك، وتابع حالة البلاغ باستخدام رمزك الخاص.",
"Nasıl kullanılır?":"كيف تعمل الخدمة؟", "1 · Bildir":"١ · أرسل بلاغًا",
"Formu doldur. Ad ve sınıf istenmez; sana gizli bir kod verilir.":"املأ النموذج. لن يُطلب اسمك أو صفك، وستحصل على رمز متابعة خاص.",
"2 · Takip et":"٢ · تابع البلاغ", "Kodunla durumu gör, aynı gün ek bilgi ekle.":"تحقق من حالة البلاغ باستخدام الرمز، وأضف معلومات أخرى في اليوم نفسه.",
"3 · İnsan inceler":"٣ · مراجعة بشرية", "Yetkili kişiler kaydı inceler. Kararı makine vermez.":"يراجع الموظفون المخوّلون البلاغ. ولا يتخذ النظام القرارات.",
"Acil bir tehlike varsa beklemeyin:":"في حال وجود خطر فوري، لا تنتظر:",
"Acil Çağrı Merkezi (Polis, Sağlık, Jandarma - 7/24)":"مركز الطوارئ 112 (الشرطة والخدمات الطبية والدرك – على مدار الساعة)",
"ALO Sosyal Destek Hattı (7/24)":"خط الدعم الاجتماعي ALO 183 (على مدار الساعة)", "MEB İletişim Merkezi (MEBİM)":"مركز الاتصال بوزارة التعليم التركية (MEBİM)",
"Rehberlik bilgi bankası":"مصادر الإرشاد والدعم", "Güvenlik ilkeleri":"مبادئ الأمان", "Gizlilik":"الخصوصية", "Sinyal, karar değil":"المؤشر ليس قرارًا", "Hesap verebilirlik":"المساءلة",
"Yaşıyorsan":"إذا كنت تتعرض للتنمّر", "Kime anlatabileceğini ve neler yapabileceğini öğren.":"تعرّف إلى الشخص الذي يمكنك التحدث إليه والخطوات التي يمكنك اتخاذها.", "Tanık olduysan":"إذا شاهدت التنمّر", "Sessiz kalmadan, güvenli şekilde nasıl destek olursun?":"كيف تقدم الدعم بأمان دون التزام الصمت؟", "Veli ve öğretmenler":"أولياء الأمور والمعلمون", "İşaretleri tanı, çocuğu dinle, doğru adımı at.":"تعرّف إلى العلامات، واستمع إلى الطالب، واتخذ الخطوة المناسبة.",
"Telefon, T.C. no, e-posta ve IBAN otomatik gizlenir.":"تُحجب أرقام الهواتف وأرقام الهوية التركية وعناوين البريد الإلكتروني وأرقام IBAN تلقائيًا.", "Otomatik eşleşme yalnızca inceleme sırasına yardım eder.":"تساعد المطابقة الآلية في ترتيب المراجعة فقط.", "Yönetici işlemleri kim yaptığıyla kayda geçer.":"تُسجّل إجراءات المسؤول مع تحديد الشخص الذي نفّذها.",
},
"Azərbaycan dili": {
"Zorbalığı kimliğini vermeden bildir, gizli kodunla durumu takip et.":"Kimliyinizi açıqlamadan zorakılıq barədə məlumat verin və məxfi kodunuzla müraciətin vəziyyətini izləyin.",
"Nasıl kullanılır?":"Necə işləyir", "1 · Bildir":"1 · Məlumat ver",
"Formu doldur. Ad ve sınıf istenmez; sana gizli bir kod verilir.":"Formanı doldurun. Adınız və sinfiniz soruşulmur; sizə məxfi izləmə kodu verilir.",
"2 · Takip et":"2 · İzləyin", "Kodunla durumu gör, aynı gün ek bilgi ekle.":"Kodunuzla vəziyyəti yoxlayın və həmin gün əlavə məlumat daxil edin.",
"3 · İnsan inceler":"3 · İnsan yoxlaması", "Yetkili kişiler kaydı inceler. Kararı makine vermez.":"Müraciəti səlahiyyətli əməkdaşlar yoxlayır. Qərarı sistem vermir.",
"Acil bir tehlike varsa beklemeyin:":"Təcili təhlükə varsa, gözləməyin:",
"Acil Çağrı Merkezi (Polis, Sağlık, Jandarma - 7/24)":"112 Təcili Yardım Mərkəzi (polis, tibbi xidmət və jandarma – 24/7)",
"ALO Sosyal Destek Hattı (7/24)":"ALO 183 Sosial Dəstək Xətti (24/7)", "MEB İletişim Merkezi (MEBİM)":"Türkiyə Təhsil Nazirliyinin Əlaqə Mərkəzi (MEBİM)",
"Rehberlik bilgi bankası":"Dəstək və məsləhət resursları", "Güvenlik ilkeleri":"Təhlükəsizlik prinsipləri", "Gizlilik":"Məxfilik", "Sinyal, karar değil":"Siqnal qərar deyil", "Hesap verebilirlik":"Hesabatlılıq",
"Yaşıyorsan":"Əgər bunu yaşayırsınızsa", "Kime anlatabileceğini ve neler yapabileceğini öğren.":"Kimə müraciət edə biləcəyinizi və hansı addımları ata biləcəyinizi öyrənin.", "Tanık olduysan":"Əgər şahid olmusunuzsa", "Sessiz kalmadan, güvenli şekilde nasıl destek olursun?":"Susmadan və özünüzü riskə atmadan necə dəstək ola biləcəyinizi öyrənin.", "Veli ve öğretmenler":"Valideynlər və müəllimlər", "İşaretleri tanı, çocuğu dinle, doğru adımı at.":"Əlamətləri tanıyın, uşağı dinləyin və düzgün addım atın.",
"Telefon, T.C. no, e-posta ve IBAN otomatik gizlenir.":"Telefon nömrələri, Türkiyə şəxsiyyət nömrələri, e-poçt ünvanları və IBAN məlumatları avtomatik gizlədilir.", "Otomatik eşleşme yalnızca inceleme sırasına yardım eder.":"Avtomatik uyğunluqlar yalnız yoxlama ardıcıllığını müəyyənləşdirməyə kömək edir.", "Yönetici işlemleri kim yaptığıyla kayda geçer.":"Administrator əməliyyatları onları həyata keçirən şəxslə birlikdə qeydə alınır.",
}
}
for _language, _entries in _HOME_COPY.items():
    MULTI_CATALOG[_language].update(_entries)

# Shared sidebar and footer labels used across all language catalogues.
MULTI_CATALOG["Deutsch"].update({"Dil / Language":"Sprache / Language","KULLANICI":"BENUTZER","YÖNETİM":"VERWALTUNG","KURUMSAL":"INFORMATIONEN","OTURUM":"SITZUNG","Yönetici:":"Administrator:","Ziyaretçi (giriş yapılmadı)":"Gast (nicht angemeldet)","Sürüm":"Version","Algılayıcı":"Detektor","Acil:":"Notfall:","Güvenli Okul · Bildirim ve takip":"Güvenli Okul · Meldung und Nachverfolgung"})
MULTI_CATALOG["Français"].update({"Dil / Language":"Langue / Language","KULLANICI":"UTILISATEUR","YÖNETİM":"ADMINISTRATION","KURUMSAL":"INFORMATIONS","OTURUM":"SESSION","Yönetici:":"Administrateur :","Ziyaretçi (giriş yapılmadı)":"Visiteur (non connecté)","Sürüm":"Version","Algılayıcı":"Détecteur","Acil:":"Urgence :","Güvenli Okul · Bildirim ve takip":"Güvenli Okul · Signalement et suivi"})
MULTI_CATALOG["Español"].update({"Dil / Language":"Idioma / Language","KULLANICI":"USUARIO","YÖNETİM":"ADMINISTRACIÓN","KURUMSAL":"INFORMACIÓN","OTURUM":"SESIÓN","Yönetici:":"Administrador:","Ziyaretçi (giriş yapılmadı)":"Visitante (sin iniciar sesión)","Sürüm":"Versión","Algılayıcı":"Detector","Acil:":"Emergencia:","Güvenli Okul · Bildirim ve takip":"Güvenli Okul · Reportes y seguimiento"})
MULTI_CATALOG["العربية"].update({"Dil / Language":"اللغة / Language","KULLANICI":"المستخدم","YÖNETİM":"الإدارة","KURUMSAL":"معلومات","OTURUM":"الجلسة","Yönetici:":"المسؤول:","Ziyaretçi (giriş yapılmadı)":"زائر (لم يتم تسجيل الدخول)","Sürüm":"الإصدار","Algılayıcı":"الكاشف","Acil:":"طوارئ:","Güvenli Okul · Bildirim ve takip":"Güvenli Okul · البلاغات والمتابعة"})
MULTI_CATALOG["Azərbaycan dili"].update({"Dil / Language":"Dil / Language","KULLANICI":"İSTİFADƏÇİ","YÖNETİM":"İDARƏETMƏ","KURUMSAL":"MƏLUMAT","OTURUM":"SESSİYA","Yönetici:":"Administrator:","Ziyaretçi (giriş yapılmadı)":"Qonaq (daxil olmayıb)","Sürüm":"Versiya","Algılayıcı":"Aşkarlayıcı","Acil:":"Təcili:","Güvenli Okul · Bildirim ve takip":"Güvenli Okul · Bildiriş və izləmə"})


# Etki Merkezi — reviewed interface translations (all seven supported languages).
CATALOG.update({
    "Etki Merkezi": "Impact Centre", "Önleyici çalışmalar": "Preventive actions",
    "Bu bölüm demo amaçlıdır. Sorumlu öğretmen/yetkili kişi bilgisini yönetici kendisi girer. Bu sürümde gerçek öğrenci veya personel bilgisi yerine örnek veri kullanın.": "This is a demonstration feature. The administrator enters the responsible teacher or authorised staff member. Use sample data rather than real student or staff information in this version.",
    "Önleyici çalışma oluşturuldu": "Preventive action created", "Önleyici çalışma güncellendi": "Preventive action updated", "Çalışma no:": "Action no:",
    "Anonim ve toplu bildirim eğilimlerinden hareketle önleyici çalışmalar planlayın ve takip edin.": "Plan and track preventive actions using anonymous, aggregated reporting trends.",
    "Bu bölüm demo amaçlıdır. Sorumlu öğretmen/yetkili kişi bilgilerini yönetici kendisi girer. Öğrenci adı veya kişisel bilgi girmeyin.": "This is a demonstration feature. The administrator enters the responsible teacher or authorised staff member. Do not enter student names or personal information.",
    "Planlandı": "Planned", "Devam ediyor": "In progress", "Tamamlandı": "Completed", "İptal edildi": "Cancelled", "Toplam": "Total",
    "+ Yeni önleyici çalışma oluştur": "+ Create a preventive action", "Çalışma başlığı": "Action title", "Açıklama ve hedef": "Description and objective",
    "İlişkili konu": "Related topic", "Hedef ortam": "Target setting", "Planlanan tarih": "Planned date",
    "Sorumlu öğretmen / yetkili kişi": "Responsible teacher / authorised staff member", "Sorumlu birim": "Responsible team",
    "Yönetici kendisi yazar": "Entered by the administrator", "Çalışmayı kaydet": "Save action", "Önleyici çalışma kaydedildi.": "Preventive action saved.",
    "Henüz çalışma oluşturulmadı. İlk çalışmayı yukarıdaki formdan ekleyebilirsiniz.": "No actions have been created yet. You can add the first one using the form above.",
    "Çalışma durumu": "Action status", "Değerlendirme / işlem notu": "Evaluation / activity note", "Değişiklikleri kaydet": "Save changes",
    "Çalışma bilgileri güncellendi.": "Action details updated.", "İşlem geçmişi": "Activity history", "Henüz işlem geçmişi yok.": "There is no activity history yet.",
    "Çalışma oluşturuldu": "Action created", "Çalışma güncellendi": "Action updated", "Açıklama eklenmedi.": "No description provided.",
    "Belirtilmedi": "Not specified", "Öncesi / sonrası gözlemsel karşılaştırma": "Before / after observational comparison",
    "Karşılaştırma için yeterli tarih bilgisi bulunmuyor.": "There is not enough date information for a comparison.",
    "Gizlilik için her iki 30 günlük dönemde de en az": "For privacy, each 30-day period must contain at least",
    "kayıt bulunması gerekir. Sayılar gösterilmiyor.": "reports. Counts are not displayed.", "Önceki 30 gün": "Previous 30 days", "Sonraki 30 gün": "Following 30 days", "Fark": "Difference",
    "Bu karşılaştırma yalnızca bildirim sayısındaki gözlemsel değişimi gösterir; olayların gerçek sıklığını veya çalışmanın nedensel etkisini kanıtlamaz.": "This comparison shows only an observed change in report counts; it does not establish the true frequency of incidents or prove a causal effect of the action.",
    "Sorumlu:": "Responsible:", "Konu:": "Topic:", "Hedef ortam:": "Target setting:", "Planlanan tarih:": "Planned date:",
})

_ETKI_MULTI = {
"Deutsch": {"Etki Merkezi":"Wirkungszentrum","Önleyici çalışmalar":"Präventionsmaßnahmen","Anonim ve toplu bildirim eğilimlerinden hareketle önleyici çalışmalar planlayın ve takip edin.":"Planen und verfolgen Sie Präventionsmaßnahmen anhand anonymer, aggregierter Meldetrends.","Bu bölüm demo amaçlıdır. Sorumlu öğretmen/yetkili kişi bilgilerini yönetici kendisi girer. Öğrenci adı veya kişisel bilgi girmeyin.":"Dieser Bereich dient nur zur Demonstration. Die Administration trägt die verantwortliche Lehrkraft oder befugte Person selbst ein. Keine Schülernamen oder persönlichen Daten eingeben.","Planlandı":"Geplant","Devam ediyor":"In Bearbeitung","Tamamlandı":"Abgeschlossen","İptal edildi":"Abgebrochen","Toplam":"Gesamt","+ Yeni önleyici çalışma oluştur":"+ Präventionsmaßnahme erstellen","Çalışma başlığı":"Titel der Maßnahme","Açıklama ve hedef":"Beschreibung und Ziel","İlişkili konu":"Zugehöriges Thema","Hedef ortam":"Zielbereich","Planlanan tarih":"Geplantes Datum","Sorumlu öğretmen / yetkili kişi":"Verantwortliche Lehrkraft / befugte Person","Sorumlu birim":"Zuständige Stelle","Yönetici kendisi yazar":"Wird von der Administration eingetragen","Çalışmayı kaydet":"Maßnahme speichern","Önleyici çalışma kaydedildi.":"Präventionsmaßnahme gespeichert.","Henüz çalışma oluşturulmadı. İlk çalışmayı yukarıdaki formdan ekleyebilirsiniz.":"Es wurden noch keine Maßnahmen erstellt. Sie können oben die erste Maßnahme hinzufügen.","Çalışma durumu":"Status der Maßnahme","Değerlendirme / işlem notu":"Bewertung / Aktivitätsnotiz","Değişiklikleri kaydet":"Änderungen speichern","Çalışma bilgileri güncellendi.":"Maßnahmendaten aktualisiert.","İşlem geçmişi":"Aktivitätsverlauf","Henüz işlem geçmişi yok.":"Noch kein Aktivitätsverlauf vorhanden.","Çalışma oluşturuldu":"Maßnahme erstellt","Çalışma güncellendi":"Maßnahme aktualisiert","Açıklama eklenmedi.":"Keine Beschreibung angegeben.","Belirtilmedi":"Nicht angegeben","Öncesi / sonrası gözlemsel karşılaştırma":"Beobachtender Vorher-Nachher-Vergleich","Karşılaştırma için yeterli tarih bilgisi bulunmuyor.":"Für einen Vergleich liegen nicht genügend Datumsangaben vor.","Önceki 30 gün":"Vorherige 30 Tage","Sonraki 30 gün":"Nachfolgende 30 Tage","Fark":"Differenz","Bu karşılaştırma yalnızca bildirim sayısındaki gözlemsel değişimi gösterir; olayların gerçek sıklığını veya çalışmanın nedensel etkisini kanıtlamaz.":"Dieser Vergleich zeigt nur eine beobachtete Veränderung der Meldezahlen. Er belegt weder die tatsächliche Häufigkeit der Vorfälle noch eine ursächliche Wirkung der Maßnahme."},
"Français": {"Etki Merkezi":"Centre d’impact","Önleyici çalışmalar":"Actions de prévention","Anonim ve toplu bildirim eğilimlerinden hareketle önleyici çalışmalar planlayın ve takip edin.":"Planifiez et suivez des actions de prévention à partir des tendances agrégées et anonymes des signalements.","Bu bölüm demo amaçlıdır. Sorumlu öğretmen/yetkili kişi bilgilerini yönetici kendisi girer. Öğrenci adı veya kişisel bilgi girmeyin.":"Cette section est une démonstration. L’administrateur saisit lui-même le nom de l’enseignant ou du personnel responsable. Ne saisissez aucun nom d’élève ni donnée personnelle.","Planlandı":"Planifiée","Devam ediyor":"En cours","Tamamlandı":"Terminée","İptal edildi":"Annulée","Toplam":"Total","+ Yeni önleyici çalışma oluştur":"+ Créer une action de prévention","Çalışma başlığı":"Titre de l’action","Açıklama ve hedef":"Description et objectif","İlişkili konu":"Sujet associé","Hedef ortam":"Environnement cible","Planlanan tarih":"Date prévue","Sorumlu öğretmen / yetkili kişi":"Enseignant / personnel responsable","Sorumlu birim":"Service responsable","Yönetici kendisi yazar":"Saisi par l’administrateur","Çalışmayı kaydet":"Enregistrer l’action","Önleyici çalışma kaydedildi.":"Action de prévention enregistrée.","Henüz çalışma oluşturulmadı. İlk çalışmayı yukarıdaki formdan ekleyebilirsiniz.":"Aucune action n’a encore été créée. Vous pouvez ajouter la première à l’aide du formulaire ci-dessus.","Çalışma durumu":"Statut de l’action","Değerlendirme / işlem notu":"Évaluation / note d’activité","Değişiklikleri kaydet":"Enregistrer les modifications","Çalışma bilgileri güncellendi.":"Les informations de l’action ont été mises à jour.","İşlem geçmişi":"Historique des activités","Henüz işlem geçmişi yok.":"Aucun historique pour le moment.","Çalışma oluşturuldu":"Action créée","Çalışma güncellendi":"Action mise à jour","Açıklama eklenmedi.":"Aucune description fournie.","Belirtilmedi":"Non précisé","Öncesi / sonrası gözlemsel karşılaştırma":"Comparaison observationnelle avant / après","Karşılaştırma için yeterli tarih bilgisi bulunmuyor.":"Les dates disponibles ne suffisent pas pour effectuer une comparaison.","Önceki 30 gün":"30 jours précédents","Sonraki 30 gün":"30 jours suivants","Fark":"Écart","Bu karşılaştırma yalnızca bildirim sayısındaki gözlemsel değişimi gösterir; olayların gerçek sıklığını veya çalışmanın nedensel etkisini kanıtlamaz.":"Cette comparaison montre uniquement une évolution observée du nombre de signalements ; elle ne prouve ni la fréquence réelle des incidents ni un effet causal de l’action."},
"Español": {"Etki Merkezi":"Centro de impacto","Önleyici çalışmalar":"Acciones preventivas","Anonim ve toplu bildirim eğilimlerinden hareketle önleyici çalışmalar planlayın ve takip edin.":"Planifica y realiza un seguimiento de acciones preventivas a partir de tendencias agregadas y anónimas de los reportes.","Bu bölüm demo amaçlıdır. Sorumlu öğretmen/yetkili kişi bilgilerini yönetici kendisi girer. Öğrenci adı veya kişisel bilgi girmeyin.":"Esta sección es una demostración. El administrador introduce el nombre del docente o del personal responsable. No introduzcas nombres de estudiantes ni datos personales.","Planlandı":"Planificada","Devam ediyor":"En curso","Tamamlandı":"Completada","İptal edildi":"Cancelada","Toplam":"Total","+ Yeni önleyici çalışma oluştur":"+ Crear acción preventiva","Çalışma başlığı":"Título de la acción","Açıklama ve hedef":"Descripción y objetivo","İlişkili konu":"Tema relacionado","Hedef ortam":"Entorno objetivo","Planlanan tarih":"Fecha prevista","Sorumlu öğretmen / yetkili kişi":"Docente / persona autorizada responsable","Sorumlu birim":"Unidad responsable","Yönetici kendisi yazar":"Lo introduce el administrador","Çalışmayı kaydet":"Guardar acción","Önleyici çalışma kaydedildi.":"Acción preventiva guardada.","Henüz çalışma oluşturulmadı. İlk çalışmayı yukarıdaki formdan ekleyebilirsiniz.":"Todavía no se han creado acciones. Puedes añadir la primera con el formulario anterior.","Çalışma durumu":"Estado de la acción","Değerlendirme / işlem notu":"Evaluación / nota de actividad","Değişiklikleri kaydet":"Guardar cambios","Çalışma bilgileri güncellendi.":"Los datos de la acción se han actualizado.","İşlem geçmişi":"Historial de actividad","Henüz işlem geçmişi yok.":"Todavía no hay historial de actividad.","Çalışma oluşturuldu":"Acción creada","Çalışma güncellendi":"Acción actualizada","Açıklama eklenmedi.":"No se proporcionó una descripción.","Belirtilmedi":"No especificado","Öncesi / sonrası gözlemsel karşılaştırma":"Comparación observacional antes / después","Karşılaştırma için yeterli tarih bilgisi bulunmuyor.":"No hay suficientes datos de fecha para realizar una comparación.","Önceki 30 gün":"30 días anteriores","Sonraki 30 gün":"30 días posteriores","Fark":"Diferencia","Bu karşılaştırma yalnızca bildirim sayısındaki gözlemsel değişimi gösterir; olayların gerçek sıklığını veya çalışmanın nedensel etkisini kanıtlamaz.":"Esta comparación solo muestra un cambio observado en el número de reportes; no demuestra la frecuencia real de los incidentes ni un efecto causal de la acción."},
"العربية": {"Etki Merkezi":"مركز الأثر","Önleyici çalışmalar":"الإجراءات الوقائية","Anonim ve toplu bildirim eğilimlerinden hareketle önleyici çalışmalar planlayın ve takip edin.":"خطّطوا للإجراءات الوقائية وتابعوها بالاستناد إلى اتجاهات البلاغات المجمّعة والمجهولة الهوية.","Bu bölüm demo amaçlıdır. Sorumlu öğretmen/yetkili kişi bilgilerini yönetici kendisi girer. Öğrenci adı veya kişisel bilgi girmeyin.":"هذا القسم تجريبي. يُدخل المسؤول بنفسه اسم المعلم أو الموظف المخوّل المسؤول. يُرجى عدم إدخال أسماء الطلاب أو أي بيانات شخصية.","Planlandı":"مخطط له","Devam ediyor":"قيد التنفيذ","Tamamlandı":"مكتمل","İptal edildi":"ملغى","Toplam":"الإجمالي","+ Yeni önleyici çalışma oluştur":"+ إنشاء إجراء وقائي","Çalışma başlığı":"عنوان الإجراء","Açıklama ve hedef":"الوصف والهدف","İlişkili konu":"الموضوع المرتبط","Hedef ortam":"البيئة المستهدفة","Planlanan tarih":"التاريخ المخطط","Sorumlu öğretmen / yetkili kişi":"المعلم / الموظف المخوّل المسؤول","Sorumlu birim":"الوحدة المسؤولة","Yönetici kendisi yazar":"يدخله المسؤول بنفسه","Çalışmayı kaydet":"حفظ الإجراء","Önleyici çalışma kaydedildi.":"تم حفظ الإجراء الوقائي.","Henüz çalışma oluşturulmadı. İlk çalışmayı yukarıdaki formdan ekleyebilirsiniz.":"لم يتم إنشاء أي إجراءات بعد. يمكنكم إضافة الإجراء الأول من النموذج أعلاه.","Çalışma durumu":"حالة الإجراء","Değerlendirme / işlem notu":"التقييم / ملاحظة النشاط","Değişiklikleri kaydet":"حفظ التغييرات","Çalışma bilgileri güncellendi.":"تم تحديث تفاصيل الإجراء.","İşlem geçmişi":"سجل النشاط","Henüz işlem geçmişi yok.":"لا يوجد سجل نشاط بعد.","Çalışma oluşturuldu":"تم إنشاء الإجراء","Çalışma güncellendi":"تم تحديث الإجراء","Açıklama eklenmedi.":"لم يُقدَّم وصف.","Belirtilmedi":"غير محدد","Öncesi / sonrası gözlemsel karşılaştırma":"مقارنة رصدية قبل / بعد","Karşılaştırma için yeterli tarih bilgisi bulunmuyor.":"لا تتوفر معلومات تاريخ كافية لإجراء المقارنة.","Önceki 30 gün":"الثلاثون يومًا السابقة","Sonraki 30 gün":"الثلاثون يومًا التالية","Fark":"الفرق","Bu karşılaştırma yalnızca bildirim sayısındaki gözlemsel değişimi gösterir; olayların gerçek sıklığını veya çalışmanın nedensel etkisini kanıtlamaz.":"تعرض هذه المقارنة تغيرًا ملحوظًا في عدد البلاغات فقط؛ ولا تثبت المعدل الحقيقي للحوادث أو وجود تأثير سببي للإجراء."},
"Azərbaycan dili": {"Etki Merkezi":"Təsir Mərkəzi","Önleyici çalışmalar":"Profilaktik tədbirlər","Anonim ve toplu bildirim eğilimlerinden hareketle önleyici çalışmalar planlayın ve takip edin.":"Anonim və ümumiləşdirilmiş müraciət meyillərinə əsasən profilaktik tədbirləri planlaşdırın və izləyin.","Bu bölüm demo amaçlıdır. Sorumlu öğretmen/yetkili kişi bilgilerini yönetici kendisi girer. Öğrenci adı veya kişisel bilgi girmeyin.":"Bu bölmə nümayiş məqsədlidir. Məsul müəllimin və ya səlahiyyətli şəxsin məlumatlarını administrator özü daxil edir. Şagird adlarını və şəxsi məlumatları daxil etməyin.","Planlandı":"Planlaşdırılıb","Devam ediyor":"Davam edir","Tamamlandı":"Tamamlanıb","İptal edildi":"Ləğv edilib","Toplam":"Cəmi","+ Yeni önleyici çalışma oluştur":"+ Yeni profilaktik tədbir yarat","Çalışma başlığı":"Tədbirin başlığı","Açıklama ve hedef":"Təsvir və məqsəd","İlişkili konu":"Əlaqəli mövzu","Hedef ortam":"Hədəf mühit","Planlanan tarih":"Planlaşdırılan tarix","Sorumlu öğretmen / yetkili kişi":"Məsul müəllim / səlahiyyətli şəxs","Sorumlu birim":"Məsul bölmə","Yönetici kendisi yazar":"Administrator özü daxil edir","Çalışmayı kaydet":"Tədbiri yadda saxla","Önleyici çalışma kaydedildi.":"Profilaktik tədbir yadda saxlanıldı.","Henüz çalışma oluşturulmadı. İlk çalışmayı yukarıdaki formdan ekleyebilirsiniz.":"Hələ tədbir yaradılmayıb. İlk tədbiri yuxarıdakı formdan əlavə edə bilərsiniz.","Çalışma durumu":"Tədbirin vəziyyəti","Değerlendirme / işlem notu":"Qiymətləndirmə / fəaliyyət qeydi","Değişiklikleri kaydet":"Dəyişiklikləri yadda saxla","Çalışma bilgileri güncellendi.":"Tədbirin məlumatları yeniləndi.","İşlem geçmişi":"Fəaliyyət tarixçəsi","Henüz işlem geçmişi yok.":"Hələ fəaliyyət tarixçəsi yoxdur.","Çalışma oluşturuldu":"Tədbir yaradıldı","Çalışma güncellendi":"Tədbir yeniləndi","Açıklama eklenmedi.":"Təsvir əlavə edilməyib.","Belirtilmedi":"Göstərilməyib","Öncesi / sonrası gözlemsel karşılaştırma":"Əvvəl / sonra müşahidə müqayisəsi","Karşılaştırma için yeterli tarih bilgisi bulunmuyor.":"Müqayisə üçün kifayət qədər tarix məlumatı yoxdur.","Önceki 30 gün":"Əvvəlki 30 gün","Sonraki 30 gün":"Sonrakı 30 gün","Fark":"Fərq","Bu karşılaştırma yalnızca bildirim sayısındaki gözlemsel değişimi gösterir; olayların gerçek sıklığını veya çalışmanın nedensel etkisini kanıtlamaz.":"Bu müqayisə yalnız müraciət sayındakı müşahidə olunan dəyişikliyi göstərir; hadisələrin real tezliyini və ya tədbirin səbəb-nəticə təsirini sübut etmir."}
}
for _lang, _entries in _ETKI_MULTI.items():
    MULTI_CATALOG[_lang].update(_entries)

_ETKI_SHARED = {
"Deutsch": {"Bu bölüm demo amaçlıdır. Sorumlu öğretmen/yetkili kişi bilgisini yönetici kendisi girer. Bu sürümde gerçek öğrenci veya personel bilgisi yerine örnek veri kullanın.":"Dieser Bereich ist eine Demonstration. Die Administration trägt die verantwortliche Lehrkraft oder befugte Person selbst ein. Verwenden Sie in dieser Version Beispieldaten statt echter Schüler- oder Personaldaten.","Önleyici çalışma oluşturuldu":"Präventionsmaßnahme erstellt","Önleyici çalışma güncellendi":"Präventionsmaßnahme aktualisiert","Çalışma no:":"Maßnahme Nr.:","Konu:":"Thema:","Sorumlu:":"Verantwortlich:","Hedef ortam:":"Zielbereich:","Sorumlu birim:":"Zuständige Stelle:","İşlemi yapan":"Ausgeführt von","Örn. Dijital güvenlik farkındalık çalışması":"z. B. Sensibilisierung für digitale Sicherheit","Çalışmanın amacı ve planlanan adımlar...":"Ziel und geplante Schritte der Maßnahme...","Örn. Rehberlik servisi":"z. B. Beratungsstelle","Genel":"Allgemein","Tümü":"Alle","Her iki 30 günlük dönemde de en az 5 kayıt gerekir. Daha azsa sayılar gizlilik için gösterilmez.":"Aus Datenschutzgründen müssen in beiden 30-Tage-Zeiträumen mindestens 5 Meldungen vorliegen. Andernfalls werden die Zahlen nicht angezeigt.","Sonraki 30 günlük dönem henüz tamamlanmadı. Karşılaştırma için 30 günün geçmesi bekleniyor.":"Der folgende 30-Tage-Zeitraum ist noch nicht abgeschlossen. Für den Vergleich müssen 30 Tage vergehen."},
"Français": {"Bu bölüm demo amaçlıdır. Sorumlu öğretmen/yetkili kişi bilgisini yönetici kendisi girer. Bu sürümde gerçek öğrenci veya personel bilgisi yerine örnek veri kullanın.":"Cette section est une démonstration. L’administrateur saisit lui-même la personne responsable. Utilisez des données fictives plutôt que de vraies données d’élèves ou de personnel dans cette version.","Önleyici çalışma oluşturuldu":"Action de prévention créée","Önleyici çalışma güncellendi":"Action de prévention mise à jour","Çalışma no:":"Action n° :","Konu:":"Sujet :","Sorumlu:":"Responsable :","Hedef ortam:":"Environnement cible :","Sorumlu birim:":"Service responsable :","İşlemi yapan":"Effectué par","Örn. Dijital güvenlik farkındalık çalışması":"ex. Sensibilisation à la sécurité numérique","Çalışmanın amacı ve planlanan adımlar...":"Objectif et étapes prévues de l’action...","Örn. Rehberlik servisi":"ex. Service d’accompagnement","Genel":"Général","Tümü":"Tout","Her iki 30 günlük dönemde de en az 5 kayıt gerekir. Daha azsa sayılar gizlilik için gösterilmez.":"Pour protéger la confidentialité, chaque période de 30 jours doit compter au moins 5 signalements. Sinon, les nombres ne sont pas affichés.","Sonraki 30 günlük dönem henüz tamamlanmadı. Karşılaştırma için 30 günün geçmesi bekleniyor.":"La période de 30 jours suivante n’est pas encore terminée. Il faut attendre 30 jours pour effectuer la comparaison."},
"Español": {"Bu bölüm demo amaçlıdır. Sorumlu öğretmen/yetkili kişi bilgisini yönetici kendisi girer. Bu sürümde gerçek öğrenci veya personel bilgisi yerine örnek veri kullanın.":"Esta sección es una demostración. El administrador introduce a la persona responsable. En esta versión, utiliza datos ficticios en lugar de datos reales de estudiantes o personal.","Önleyici çalışma oluşturuldu":"Acción preventiva creada","Önleyici çalışma güncellendi":"Acción preventiva actualizada","Çalışma no:":"Acción n.º:","Konu:":"Tema:","Sorumlu:":"Responsable:","Hedef ortam:":"Entorno objetivo:","Sorumlu birim:":"Unidad responsable:","İşlemi yapan":"Realizado por","Örn. Dijital güvenlik farkındalık çalışması":"p. ej. Actividad de concienciación sobre seguridad digital","Çalışmanın amacı ve planlanan adımlar...":"Objetivo y pasos previstos de la actividad...","Örn. Rehberlik servisi":"p. ej. Servicio de orientación","Genel":"General","Tümü":"Todo","Her iki 30 günlük dönemde de en az 5 kayıt gerekir. Daha azsa sayılar gizlilik için gösterilmez.":"Por privacidad, cada periodo de 30 días debe incluir al menos 5 reportes. Si hay menos, no se muestran las cifras.","Sonraki 30 günlük dönem henüz tamamlanmadı. Karşılaştırma için 30 günün geçmesi bekleniyor.":"El siguiente periodo de 30 días aún no ha terminado. Hay que esperar 30 días para realizar la comparación."},
"العربية": {"Bu bölüm demo amaçlıdır. Sorumlu öğretmen/yetkili kişi bilgisini yönetici kendisi girer. Bu sürümde gerçek öğrenci veya personel bilgisi yerine örnek veri kullanın.":"هذا القسم تجريبي. يُدخل المسؤول الشخص المسؤول بنفسه. استخدموا بيانات تجريبية بدلًا من بيانات الطلاب أو الموظفين الحقيقية في هذه النسخة.","Önleyici çalışma oluşturuldu":"تم إنشاء الإجراء الوقائي","Önleyici çalışma güncellendi":"تم تحديث الإجراء الوقائي","Çalışma no:":"رقم الإجراء:","Konu:":"الموضوع:","Sorumlu:":"المسؤول:","Hedef ortam:":"البيئة المستهدفة:","Sorumlu birim:":"الوحدة المسؤولة:","İşlemi yapan":"نفّذ الإجراء","Örn. Dijital güvenlik farkındalık çalışması":"مثال: نشاط توعوي حول السلامة الرقمية","Çalışmanın amacı ve planlanan adımlar...":"هدف النشاط والخطوات المخطط لها...","Örn. Rehberlik servisi":"مثال: خدمة الإرشاد","Genel":"عام","Tümü":"الكل","Her iki 30 günlük dönemde de en az 5 kayıt gerekir. Daha azsa sayılar gizlilik için gösterilmez.":"لحماية الخصوصية، يجب أن تحتوي كل فترة من 30 يومًا على 5 بلاغات على الأقل. وإلا فلن تُعرض الأعداد.","Sonraki 30 günlük dönem henüz tamamlanmadı. Karşılaştırma için 30 günün geçmesi bekleniyor.":"لم تكتمل فترة الثلاثين يومًا التالية بعد. يجب الانتظار 30 يومًا لإجراء المقارنة."},
"Azərbaycan dili": {"Bu bölüm demo amaçlıdır. Sorumlu öğretmen/yetkili kişi bilgisini yönetici kendisi girer. Bu sürümde gerçek öğrenci veya personel bilgisi yerine örnek veri kullanın.":"Bu bölmə nümayiş üçündür. Məsul şəxsi administrator özü daxil edir. Bu versiyada real şagird və ya işçi məlumatları əvəzinə nümunə məlumatlardan istifadə edin.","Önleyici çalışma oluşturuldu":"Profilaktik tədbir yaradıldı","Önleyici çalışma güncellendi":"Profilaktik tədbir yeniləndi","Çalışma no:":"Tədbir №:","Konu:":"Mövzu:","Sorumlu:":"Məsul şəxs:","Hedef ortam:":"Hədəf mühit:","Sorumlu birim:":"Məsul bölmə:","İşlemi yapan":"İcra edən","Örn. Dijital güvenlik farkındalık çalışması":"məsələn, Rəqəmsal təhlükəsizlik maarifləndirmə tədbiri","Çalışmanın amacı ve planlanan adımlar...":"Tədbirin məqsədi və planlaşdırılan addımlar...","Örn. Rehberlik servisi":"məsələn, Məsləhət xidməti","Genel":"Ümumi","Tümü":"Hamısı","Her iki 30 günlük dönemde de en az 5 kayıt gerekir. Daha azsa sayılar gizlilik için gösterilmez.":"Məxfiliyi qorumaq üçün hər 30 günlük dövrdə ən azı 5 müraciət olmalıdır. Əks halda saylar göstərilmir.","Sonraki 30 günlük dönem henüz tamamlanmadı. Karşılaştırma için 30 günün geçmesi bekleniyor.":"Növbəti 30 günlük dövr hələ tamamlanmayıb. Müqayisə üçün 30 gün gözlənilməlidir."}
}
for _lang, _entries in _ETKI_SHARED.items():
    MULTI_CATALOG[_lang].update(_entries)
CATALOG.update({
    "Konu:":"Topic:", "Sorumlu:":"Responsible:", "Hedef ortam:":"Target setting:", "Sorumlu birim:":"Responsible team:",
    "İşlemi yapan":"Performed by", "Örn. Dijital güvenlik farkındalık çalışması":"e.g. Digital safety awareness activity",
    "Çalışmanın amacı ve planlanan adımlar...":"The purpose of the activity and planned steps...",
    "Örn. Rehberlik servisi":"e.g. Guidance service", "Genel":"General", "Tümü":"All",
    "Her iki 30 günlük dönemde de en az 5 kayıt gerekir. Daha azsa sayılar gizlilik için gösterilmez.":"For privacy, each 30-day period must contain at least 5 reports. If there are fewer, counts are not displayed.",
    "Sonraki 30 günlük dönem henüz tamamlanmadı. Karşılaştırma için 30 günün geçmesi bekleniyor.":"The following 30-day period is not yet complete. Wait 30 days before making the comparison."
})

# ---------------------------------------------------------------------------
# Deep UI coverage: review, analytics, support guide, research and privacy pages.
# These are interface/content strings authored by the application, not user data.
_DEEP_UI = {
"Deutsch": {
"Acil bir tehlike varsa beklemeyin:":"Warten Sie bei unmittelbarer Gefahr nicht:",
"Acil Çağrı Merkezi (Polis, Sağlık, Jandarma - 7/24)":"Notruf 112 (Polizei, Rettungsdienst und Gendarmerie – rund um die Uhr)",
"ALO Sosyal Destek Hattı (7/24)":"Soziale Unterstützung ALO 183 (rund um die Uhr)",
"MEB İletişim Merkezi (MEBİM)":"Kontaktzentrum des türkischen Bildungsministeriums (MEBİM)",
"Yaşıyorsan":"Wenn du betroffen bist", "Kime anlatabileceğini ve neler yapabileceğini öğren.":"Erfahre, mit wem du sprechen kannst und welche Schritte dir helfen können.",
"Tanık olduysan":"Wenn du etwas beobachtet hast", "Sessiz kalmadan, güvenli şekilde nasıl destek olursun?":"Wie kannst du sicher helfen, ohne zu schweigen?",
"Veli ve öğretmenler":"Eltern und Lehrkräfte", "İşaretleri tanı, çocuğu dinle, doğru adımı at.":"Erkenzeichen erkennen, dem Kind zuhören und angemessen handeln.",
"Zorbalık nedir, ne değildir?":"Was ist Mobbing – und was nicht?", "Yaşıyorsan ne yapabilirsin?":"Was kannst du tun, wenn du betroffen bist?",
"Kendine zarar verme düşüncen varsa":"Wenn du daran denkst, dir selbst zu schaden", "Gördüysen sessiz kalma":"Wenn du etwas beobachtet hast, schweige nicht",
"İnternette aşağılanıyor ya da tehdit ediliyorsan":"Wenn du online beleidigt oder bedroht wirst", "Çocuğunuz zorbalığa uğruyor olabilir":"Ihr Kind könnte von Mobbing betroffen sein",
"Çocuğunuzun zorbalık yaptığı söyleniyorsa":"Wenn Ihnen gesagt wird, dass Ihr Kind andere schikaniert",
"Bildirim geldiğinde":"Wenn eine Meldung eingeht", "Formu gönderirsin ve gizli takip kodunu alırsın.":"Nach dem Absenden des Formulars erhältst du einen vertraulichen Tracking-Code.",
"Kayıt, yetkili kişiler (rehberlik / okul yönetimi) tarafından incelenir; bunu bir insan yapar.":"Die Meldung wird von befugten Personen (Beratungsstelle oder Schulleitung) geprüft – immer durch Menschen.",
"Takip koduyla durumu görürsün. Sistemde mesajlaşma yoktur; bu yüzden acil durumlarda bir yetişkine ulaş.":"Mit dem Tracking-Code kannst du den Status ansehen. Es gibt keine Nachrichtenfunktion. Wende dich in dringenden Fällen an eine erwachsene Vertrauensperson.",
"Rehberlik içerikleri taslaktır; okul psikolojik danışmanı tarafından onaylanmalıdır.":"Die Inhalte des Unterstützungsleitfadens sind Entwürfe und müssen von der schulpsychologischen Beratung geprüft werden.",
"Ne zaman bildiriliyor?":"Wann werden Meldungen eingereicht?", "Saate göre (bildirimin yapıldığı saat)":"Nach Uhrzeit (Zeitpunkt der Meldung)",
"Haftanın gününe göre":"Nach Wochentag", "Haftalık eğilim":"Wöchentlicher Verlauf", "Hangi ortamda, hangi tür?":"Welche Vorfallart in welcher Umgebung?",
"Ortama göre":"Nach Umgebung", "Olay türüne göre":"Nach Vorfallart", "En çok bildirilen ortam":"Am häufigsten gemeldete Umgebung", "En çok bildirilen tür":"Am häufigsten gemeldete Vorfallart",
"Dönem":"Zeitraum", "Küçük hücre eşiği (k)":"Schwellenwert für kleine Gruppen (k)", "Kayıt sayısı":"Anzahl der Meldungen",
"Bu dönemde kayıt yok.":"Für diesen Zeitraum liegen keine Meldungen vor.", "Bu filtrelerle eşleşen kayıt bulunamadı.":"Keine Meldungen entsprechen diesen Filtern.",
"Bildirim sayısındaki artış, olayların arttığını değil bildirme isteğinin arttığını da gösterebilir; ayrım için ayrı bir ölçüm (ör. anket) gerekir. Saat, olayın değil bildirimin saatidir; anonim kayıtlarda zaman dakika ve saniye hassasiyetinde kaydedilir.":"Ein Anstieg der Meldungen kann auch auf eine höhere Bereitschaft zur Meldung statt auf mehr Vorfälle hinweisen. Zur Unterscheidung ist eine separate Messung (z. B. eine Umfrage) nötig. Die Uhrzeit bezeichnet den Eingang der Meldung, nicht den Vorfall. Bei anonymen Meldungen wird die Zeit minutengenau gespeichert.",
"Çapraz tabloda sayısı bu değerden küçük hücreler kimliksizleştirme için gizlenir.":"Zellen mit weniger Einträgen als diesem Schwellenwert werden zum Schutz der Identität ausgeblendet.",
"Gizlilik ve KVKK paneli":"Datenschutz- und KVKK-Bereich", "Hangi veri neden toplanıyor, ne kadar saklanıyor ve nasıl siliniyor. Metinler taslaktır.":"Welche Daten aus welchem Grund erhoben, wie lange gespeichert und wie gelöscht werden. Die Texte sind Entwürfe.",
"Aydınlatma metni":"Datenschutzhinweis", "Veri envanteri":"Datenverzeichnis", "Saklama ve imha":"Aufbewahrung und Löschung", "Onam akışı (simülasyon)":"Einwilligungsablauf (Simulation)",
"Köşeli parantezli alanlar doldurulmadan ve hukuk danışmanı onaylamadan yayımlanmamalıdır.":"Dieser Text darf erst veröffentlicht werden, wenn alle Angaben in eckigen Klammern ergänzt und juristisch geprüft wurden.",
"Veri minimizasyonu (sistemde uygulananlar)":"Datenminimierung (im System umgesetzt)", "Açık riskler (raporda belirtilmeli)":"Offene Risiken (im Bericht zu nennen)",
"Otomatik/elle imha kuralları":"Automatische/manuelle Löschregeln", "Önizleme: saklama süresi (gün)":"Vorschau: Aufbewahrungsdauer (Tage)",
"Canlı silinecek kayıt sayısı yalnızca yönetici oturumunda görünür.":"Die Anzahl der tatsächlich zu löschenden Meldungen ist nur während einer Administratorsitzung sichtbar.",
"SİMÜLASYON: Bu akış gerçek onam toplamaz, hiçbir veri kaydetmez ve kimseyle iletişime geçmez. Araştırmada onam, okulun resmî kanallarıyla yazılı olarak alınmalıdır.":"SIMULATION: Dieser Ablauf holt keine echte Einwilligung ein, speichert keine Daten und kontaktiert niemanden. Für Forschungszwecke muss die Einwilligung schriftlich über die offiziellen Kanäle der Schule eingeholt werden.",
"Katılımcının yaş grubu":"Altersgruppe der teilnehmenden Person", "Bilgilendirmeyi okudum, gönüllü katılıyorum (simülasyon).":"Ich habe die Informationen gelesen und nehme freiwillig teil (Simulation).",
"Veli/yasal temsilci izin verdi (simülasyon).":"Die erziehungsberechtigte Person hat zugestimmt (Simulation).", "Simülasyon tamamlandı: katılım koşulları sağlandı.":"Simulation abgeschlossen: Die Teilnahmebedingungen sind erfüllt.",
"18 yaşından küçüklerde gönüllü katılımın yanında veli/yasal temsilcinin bilgilendirilmesi ve izni gerekir.":"Bei Teilnehmenden unter 18 Jahren sind neben der freiwilligen Teilnahme die Information und Zustimmung einer erziehungsberechtigten Person erforderlich.",
"18 yaş ve üzeri katılımcı için veli izni gerekmez; kendi gönüllü onamı yeterlidir.":"Bei Teilnehmenden ab 18 Jahren ist keine Zustimmung der Eltern erforderlich; die eigene freiwillige Einwilligung genügt.",
"Bu aşamadan sonra katılımcı bildirim formunu kullanabilir. Katılımcıdan **ad, sınıf, telefon istenmez**; onay kaydı bu uygulamada tutulmaz, okulda yazılı saklanır.":"Danach kann die teilnehmende Person das Meldeformular verwenden. **Name, Klasse und Telefonnummer werden nicht erfragt**. Die Einwilligung wird nicht in dieser Anwendung gespeichert, sondern schriftlich in der Schule aufbewahrt.",
"Gönüllü katılım ve veli onam formu taslağı (.txt)":"Entwurf des Formulars zur freiwilligen Teilnahme und elterlichen Einwilligung (.txt)",
"Baştan başla":"Von vorn beginnen", "İleri":"Weiter", "Bildirim türü":"Meldungsart", "Bildirimde belirtilen kişi bilgileri":"In der Meldung genannte Personenangaben",
"Aktif takip":"Aktive Nachverfolgung", "Anonim oranı":"Anteil anonymer Meldungen", "Örnek sayısı":"Stichprobengröße",
"Grafikler yalnızca bu uygulamada kayıtlı bilgileri özetler; okul geneline ilişkin sonuç göstermez.":"Die Diagramme fassen nur die in dieser Anwendung gespeicherten Angaben zusammen und erlauben keine Rückschlüsse auf die gesamte Schule.",
"Bu karşılaştırma yalnızca bildirim sayısındaki gözlemsel değişimi gösterir; olayların gerçek sıklığını veya çalışmanın nedensel etkisini kanıtlamaz.":"Dieser Vergleich zeigt nur die beobachtete Veränderung der Meldezahl. Er beweist weder die tatsächliche Häufigkeit der Vorfälle noch eine ursächliche Wirkung der Maßnahme.",
"Öncesi / sonrası gözlemsel karşılaştırma":"Beobachtender Vergleich vor und nach der Maßnahme", "Önleyici çalışmalar":"Präventionsmaßnahmen", "Çalışma başlığı":"Titel der Maßnahme", "Sorumlu öğretmen / yetkili kişi":"Zuständige Lehrkraft / befugte Person", "Sorumlu birim":"Zuständige Stelle", "Planlanan tarih":"Geplantes Datum", "Çalışma durumu":"Status der Maßnahme", "Çalışmayı kaydet":"Maßnahme speichern", "Henüz çalışma oluşturulmadı. İlk çalışmayı yukarıdaki formdan ekleyebilirsiniz.":"Es wurde noch keine Maßnahme erstellt. Sie können oben die erste Maßnahme hinzufügen.",
"Bu bölüm demo amaçlıdır. Sorumlu öğretmen/yetkili kişi bilgisini yönetici kendisi girer. Bu sürümde gerçek öğrenci veya personel bilgisi yerine örnek veri kullanın.":"Dieser Bereich dient nur zur Demonstration. Die Administration trägt die zuständige Lehrkraft oder befugte Person selbst ein. Verwenden Sie in dieser Version Beispieldaten statt echter Schüler- oder Personaldaten.",
"Sorumlu öğretmen / yetkili kişi":"Zuständige Lehrkraft / befugte Person", "Yönetici kendisi yazar":"Wird von der Administration eingetragen",
"Açıklama kalitesi kontrolü:":"Prüfung der Beschreibung:", "Metin temel uzunluk kontrolünü geçti. Bu, bildirimin doğru olduğu anlamına gelmez.":"Der Text erfüllt die grundlegende Längenprüfung. Das bedeutet nicht, dass die Meldung zutreffend ist.",
"Metin çok kısa, yeterince açıklayıcı olmayabilir veya tekrar eden karakterler içeriyor. Bu bir spam/asılsız bildirim kanıtı değildir; otomatik silinmez, yetkili kişi bağlamı kontrol etmelidir.":"Der Text ist möglicherweise zu kurz, nicht ausreichend aussagekräftig oder enthält wiederholte Zeichen. Das ist kein Beweis für Spam oder eine falsche Meldung. Der Eintrag wird nicht automatisch gelöscht; eine befugte Person muss den Kontext prüfen.",
"Girişler, başarısız denemeler, dışa aktarımlar ve silme işlemleri burada izlenir.":"Anmeldungen, fehlgeschlagene Versuche, Exporte und Löschvorgänge werden hier protokolliert.",
"Henüz denetim kaydı yok.":"Es liegen noch keine Prüfprotokolle vor.", "Henüz işlem geçmişi yok.":"Es gibt noch keinen Aktivitätsverlauf.", "Henüz not eklenmemiş.":"Es wurden noch keine Notizen hinzugefügt.",
"Boş not eklenemez.":"Eine leere Notiz kann nicht hinzugefügt werden.", "Not kaydedilemedi.":"Die Notiz konnte nicht gespeichert werden.", "Değişiklik kaydedilemedi. Lütfen yeniden deneyin.":"Die Änderung konnte nicht gespeichert werden. Bitte versuchen Sie es erneut.",
"Kayıt oluşturulamadı. Lütfen daha sonra tekrar dene.":"Der Eintrag konnte nicht erstellt werden. Bitte versuchen Sie es später erneut.", "Notu kaydet":"Notiz speichern", "Yeni not":"Neue Notiz", "Değerlendirme / işlem notu":"Bewertungs-/Bearbeitungsnotiz",
"Kayıt sayısı çok az; yüzdeler ve karşılaştırmalar yanıltıcı olabilir, yorum yapmayın.":"Die Anzahl der Meldungen ist sehr gering. Prozentwerte und Vergleiche können irreführend sein und sollten nicht interpretiert werden.",
"Süreler kayıt oluşturma ile ilk durum değişikliği / 'Sonuçlandırıldı' arasındaki farktır. Yeni anonim kayıtlar dakika ve saniye hassasiyetinde kaydedilir; eski yuvarlanmış kayıtların geçmiş zamanı geriye dönük kesinleştirilemez.":"Die Zeitspannen werden zwischen der Erstellung und der ersten Statusänderung bzw. dem Abschluss gemessen. Neue anonyme Einträge werden minutengenau gespeichert; der genaue Zeitpunkt älterer, gerundeter Einträge lässt sich nachträglich nicht rekonstruieren.",
"Süresi dolan, sonuçlandırılmış kayıtlar notları ve geçmişiyle birlikte kalıcı olarak silinir.":"Abgelaufene, abgeschlossene Meldungen werden einschließlich Notizen und Verlauf dauerhaft gelöscht.",
"Sistem genelinde çok fazla hatalı giriş denemesi var. Lütfen bir süre sonra tekrar deneyin.":"Im gesamten System gab es zu viele fehlgeschlagene Anmeldeversuche. Bitte versuchen Sie es später erneut.",
"Yönetici bilgileri ayarlanmamış. .streamlit/secrets.toml (veya Streamlit Cloud > Settings > Secrets) içindeki [admin] bölümünü yapılandırın.":"Die Administrator-Zugangsdaten sind nicht eingerichtet. Konfigurieren Sie den Abschnitt [admin] in .streamlit/secrets.toml (oder unter Streamlit Cloud > Settings > Secrets).",
"Yazdıkların için endişeleniyoruz. Şu an güvende değilsen ya da kendini veya başkasını tehlikede hissediyorsan lütfen hemen güvendiğin bir yetişkine, okul rehber öğretmenine ya da yukarıdaki acil hatlara ulaş.":"Wir nehmen deine Angaben ernst. Wenn du gerade nicht sicher bist oder befürchtest, dass du oder jemand anderes in Gefahr ist, wende dich bitte sofort an eine erwachsene Vertrauensperson, die schulische Beratungsstelle oder eine der oben genannten Notrufstellen.",
},
"Français": {
"Acil bir tehlike varsa beklemeyin:":"En cas de danger immédiat, n’attendez pas :", "Acil Çağrı Merkezi (Polis, Sağlık, Jandarma - 7/24)":"Urgences 112 (police, services médicaux et gendarmerie – 24 h/24)", "ALO Sosyal Destek Hattı (7/24)":"Ligne d’aide sociale ALO 183 (24 h/24)", "MEB İletişim Merkezi (MEBİM)":"Centre de contact du ministère turc de l’Éducation (MEBİM)",
"Yaşıyorsan":"Si tu es concerné", "Kime anlatabileceğini ve neler yapabileceğini öğren.":"Découvre à qui en parler et quelles démarches entreprendre.", "Tanık olduysan":"Si tu as été témoin", "Sessiz kalmadan, güvenli şekilde nasıl destek olursun?":"Comment apporter ton soutien en toute sécurité sans garder le silence ?", "Veli ve öğretmenler":"Parents et enseignants", "İşaretleri tanı, çocuğu dinle, doğru adımı at.":"Repérez les signes, écoutez l’enfant et adoptez la bonne démarche.",
"Zorbalık nedir, ne değildir?":"Qu’est-ce que le harcèlement, et qu’est-ce qui ne l’est pas ?", "Yaşıyorsan ne yapabilirsin?":"Que faire si tu es concerné ?", "Kendine zarar verme düşüncen varsa":"Si tu as des pensées de te faire du mal", "Gördüysen sessiz kalma":"Si tu as été témoin, ne reste pas silencieux", "İnternette aşağılanıyor ya da tehdit ediliyorsan":"Si tu subis des humiliations ou des menaces en ligne", "Çocuğunuz zorbalığa uğruyor olabilir":"Votre enfant pourrait subir du harcèlement", "Çocuğunuzun zorbalık yaptığı söyleniyorsa":"Si l’on vous dit que votre enfant harcèle quelqu’un", "Bildirim geldiğinde":"Lorsqu’un signalement arrive",
"Formu gönderirsin ve gizli takip kodunu alırsın.":"Après l’envoi du formulaire, tu reçois un code de suivi confidentiel.", "Kayıt, yetkili kişiler (rehberlik / okul yönetimi) tarafından incelenir; bunu bir insan yapar.":"Le signalement est examiné par des personnes autorisées (service d’accompagnement ou direction de l’établissement). L’examen est toujours humain.", "Takip koduyla durumu görürsün. Sistemde mesajlaşma yoktur; bu yüzden acil durumlarda bir yetişkine ulaş.":"Tu peux consulter le statut avec ton code de suivi. La plateforme ne permet pas d’échanger des messages ; en cas d’urgence, contacte un adulte.", "Rehberlik içerikleri taslaktır; okul psikolojik danışmanı tarafından onaylanmalıdır.":"Les contenus du guide sont des projets et doivent être validés par le psychologue ou conseiller scolaire.",
"Ne zaman bildiriliyor?":"À quel moment les signalements sont-ils envoyés ?", "Saate göre (bildirimin yapıldığı saat)":"Par heure (heure d’envoi du signalement)", "Haftanın gününe göre":"Par jour de la semaine", "Haftalık eğilim":"Tendance hebdomadaire", "Hangi ortamda, hangi tür?":"Quel type d’incident, dans quel environnement ?", "Ortama göre":"Par environnement", "Olay türüne göre":"Par type d’incident", "En çok bildirilen ortam":"Environnement le plus signalé", "En çok bildirilen tür":"Type d’incident le plus signalé", "Dönem":"Période", "Küçük hücre eşiği (k)":"Seuil des petits groupes (k)", "Kayıt sayısı":"Nombre de signalements", "Bu dönemde kayıt yok.":"Aucun signalement pour cette période.", "Bu filtrelerle eşleşen kayıt bulunamadı.":"Aucun signalement ne correspond à ces filtres.",
"Bildirim sayısındaki artış, olayların arttığını değil bildirme isteğinin arttığını da gösterebilir; ayrım için ayrı bir ölçüm (ör. anket) gerekir. Saat, olayın değil bildirimin saatidir; anonim kayıtlarda zaman dakika ve saniye hassasiyetinde kaydedilir.":"Une hausse du nombre de signalements peut traduire une plus grande volonté de signaler, et non une hausse des incidents. Une mesure distincte (par exemple une enquête) est nécessaire pour faire la différence. L’heure affichée est celle de l’envoi du signalement, pas celle de l’incident. Pour les signalements anonymes, l’heure est enregistrée à la minute près.", "Çapraz tabloda sayısı bu değerden küçük hücreler kimliksizleştirme için gizlenir.":"Les cellules dont le nombre est inférieur à ce seuil sont masquées afin de protéger l’identité des personnes.",
"Gizlilik ve KVKK paneli":"Espace confidentialité et protection des données", "Hangi veri neden toplanıyor, ne kadar saklanıyor ve nasıl siliniyor. Metinler taslaktır.":"Quelles données sont collectées, pourquoi, pendant combien de temps et comment elles sont supprimées. Les textes sont des projets.", "Aydınlatma metni":"Notice d’information", "Veri envanteri":"Inventaire des données", "Saklama ve imha":"Conservation et suppression", "Onam akışı (simülasyon)":"Parcours de consentement (simulation)", "Köşeli parantezli alanlar doldurulmadan ve hukuk danışmanı onaylamadan yayımlanmamalıdır.":"Ce texte ne doit pas être publié avant que les champs entre crochets soient remplis et qu’un conseiller juridique l’ait validé.", "Veri minimizasyonu (sistemde uygulananlar)":"Minimisation des données (mesures appliquées)", "Açık riskler (raporda belirtilmeli)":"Risques à signaler dans le rapport", "Otomatik/elle imha kuralları":"Règles de suppression automatique ou manuelle", "Önizleme: saklama süresi (gün)":"Aperçu : durée de conservation (jours)", "Canlı silinecek kayıt sayısı yalnızca yönetici oturumunda görünür.":"Le nombre de signalements qui seraient réellement supprimés n’est visible que pendant une session administrateur.",
"SİMÜLASYON: Bu akış gerçek onam toplamaz, hiçbir veri kaydetmez ve kimseyle iletişime geçmez. Araştırmada onam, okulun resmî kanallarıyla yazılı olarak alınmalıdır.":"SIMULATION : ce parcours ne recueille aucun consentement réel, n’enregistre aucune donnée et ne contacte personne. Pour la recherche, le consentement doit être recueilli par écrit via les canaux officiels de l’établissement.", "Katılımcının yaş grubu":"Tranche d’âge de la personne participante", "Bilgilendirmeyi okudum, gönüllü katılıyorum (simülasyon).":"J’ai lu les informations et je participe volontairement (simulation).", "Veli/yasal temsilci izin verdi (simülasyon).":"Le parent ou représentant légal a donné son accord (simulation).", "Simülasyon tamamlandı: katılım koşulları sağlandı.":"Simulation terminée : les conditions de participation sont remplies.", "18 yaşından küçüklerde gönüllü katılımın yanında veli/yasal temsilcinin bilgilendirilmesi ve izni gerekir.":"Pour les moins de 18 ans, la participation volontaire doit s’accompagner de l’information et de l’accord du parent ou représentant légal.", "18 yaş ve üzeri katılımcı için veli izni gerekmez; kendi gönüllü onamı yeterlidir.":"Pour les personnes de 18 ans ou plus, l’accord parental n’est pas nécessaire ; leur propre consentement volontaire suffit.", "Bu aşamadan sonra katılımcı bildirim formunu kullanabilir. Katılımcıdan **ad, sınıf, telefon istenmez**; onay kaydı bu uygulamada tutulmaz, okulda yazılı saklanır.":"La personne participante peut ensuite utiliser le formulaire de signalement. **Aucun nom, classe ou numéro de téléphone n’est demandé** ; le consentement n’est pas stocké dans cette application et doit être conservé par écrit par l’établissement.", "Gönüllü katılım ve veli onam formu taslağı (.txt)":"Projet de formulaire de participation volontaire et de consentement parental (.txt)", "Baştan başla":"Recommencer", "İleri":"Suivant",
"Aktif takip":"Suivi actif", "Anonim oranı":"Part des signalements anonymes", "Örnek sayısı":"Taille de l’échantillon", "Grafikler yalnızca bu uygulamada kayıtlı bilgileri özetler; okul geneline ilişkin sonuç göstermez.":"Les graphiques résument uniquement les données enregistrées dans cette application et ne représentent pas l’ensemble de l’établissement.", "Bu karşılaştırma yalnızca bildirim sayısındaki gözlemsel değişimi gösterir; olayların gerçek sıklığını veya çalışmanın nedensel etkisini kanıtlamaz.":"Cette comparaison montre uniquement l’évolution observée du nombre de signalements. Elle ne prouve ni la fréquence réelle des incidents ni un effet causal de l’action.", "Öncesi / sonrası gözlemsel karşılaştırma":"Comparaison observationnelle avant/après", "Önleyici çalışmalar":"Actions de prévention", "Çalışma başlığı":"Titre de l’action", "Sorumlu öğretmen / yetkili kişi":"Enseignant ou personne autorisée responsable", "Sorumlu birim":"Service responsable", "Planlanan tarih":"Date prévue", "Çalışma durumu":"Statut de l’action", "Çalışmayı kaydet":"Enregistrer l’action", "Henüz çalışma oluşturulmadı. İlk çalışmayı yukarıdaki formdan ekleyebilirsiniz.":"Aucune action n’a encore été créée. Vous pouvez ajouter la première à l’aide du formulaire ci-dessus.", "Bu bölüm demo amaçlıdır. Sorumlu öğretmen/yetkili kişi bilgisini yönetici kendisi girer. Bu sürümde gerçek öğrenci veya personel bilgisi yerine örnek veri kullanın.":"Cette section est une démonstration. L’administrateur saisit lui-même le nom de l’enseignant ou de la personne autorisée responsable. Utilisez des données fictives plutôt que des données réelles d’élèves ou de personnel.", "Yönetici kendisi yazar":"Saisi par l’administrateur", "Açıklama kalitesi kontrolü:":"Vérification de la qualité de la description :", "Metin temel uzunluk kontrolünü geçti. Bu, bildirimin doğru olduğu anlamına gelmez.":"Le texte satisfait au contrôle de longueur de base. Cela ne signifie pas que le signalement est exact.", "Metin çok kısa, yeterince açıklayıcı olmayabilir veya tekrar eden karakterler içeriyor. Bu bir spam/asılsız bildirim kanıtı değildir; otomatik silinmez, yetkili kişi bağlamı kontrol etmelidir.":"Le texte est peut-être trop court, insuffisamment précis ou contient des caractères répétés. Cela ne prouve pas qu’il s’agit de spam ou d’un faux signalement. Il n’est pas supprimé automatiquement ; une personne autorisée doit examiner le contexte.", "Girişler, başarısız denemeler, dışa aktarımlar ve silme işlemleri burada izlenir.":"Les connexions, tentatives échouées, exportations et suppressions sont consignées ici.", "Henüz denetim kaydı yok.":"Aucun journal d’audit pour le moment.", "Henüz işlem geçmişi yok.":"Aucun historique d’activité pour le moment.", "Henüz not eklenmemiş.":"Aucune note n’a encore été ajoutée.", "Boş not eklenemez.":"Une note vide ne peut pas être ajoutée.", "Not kaydedilemedi.":"Impossible d’enregistrer la note.", "Değişiklik kaydedilemedi. Lütfen yeniden deneyin.":"Impossible d’enregistrer la modification. Veuillez réessayer.", "Kayıt oluşturulamadı. Lütfen daha sonra tekrar dene.":"Impossible de créer l’entrée. Veuillez réessayer plus tard.", "Notu kaydet":"Enregistrer la note", "Yeni not":"Nouvelle note", "Değerlendirme / işlem notu":"Note d’évaluation / de traitement", "Kayıt sayısı çok az; yüzdeler ve karşılaştırmalar yanıltıcı olabilir, yorum yapmayın.":"Le nombre de signalements est très faible ; les pourcentages et comparaisons peuvent être trompeurs et ne doivent pas être interprétés.", "Sistem genelinde çok fazla hatalı giriş denemesi var. Lütfen bir süre sonra tekrar deneyin.":"Le système a enregistré trop de tentatives de connexion échouées. Veuillez réessayer plus tard.", "Yönetici bilgileri ayarlanmamış. .streamlit/secrets.toml (veya Streamlit Cloud > Settings > Secrets) içindeki [admin] bölümünü yapılandırın.":"Les identifiants administrateur ne sont pas configurés. Configurez la section [admin] dans .streamlit/secrets.toml (ou dans Streamlit Cloud > Settings > Secrets).",
"Yazdıkların için endişeleniyoruz. Şu an güvende değilsen ya da kendini veya başkasını tehlikede hissediyorsan lütfen hemen güvendiğin bir yetişkine, okul rehber öğretmenine ya da yukarıdaki acil hatlara ulaş.":"Nous prenons ce que tu as écrit au sérieux. Si tu n’es pas en sécurité ou si tu crains pour toi-même ou pour quelqu’un d’autre, contacte immédiatement un adulte de confiance, le service d’accompagnement de l’école ou l’un des services d’urgence indiqués ci-dessus.",
},
"Español": {
"Acil bir tehlike varsa beklemeyin:":"Si existe un peligro inmediato, no esperes:", "Acil Çağrı Merkezi (Polis, Sağlık, Jandarma - 7/24)":"Emergencias 112 (policía, servicios médicos y gendarmería, 24 horas)", "ALO Sosyal Destek Hattı (7/24)":"Línea de apoyo social ALO 183 (24 horas)", "MEB İletişim Merkezi (MEBİM)":"Centro de Atención del Ministerio de Educación de Turquía (MEBİM)",
"Yaşıyorsan":"Si te está ocurriendo", "Kime anlatabileceğini ve neler yapabileceğini öğren.":"Descubre con quién puedes hablar y qué pasos puedes dar.", "Tanık olduysan":"Si has sido testigo", "Sessiz kalmadan, güvenli şekilde nasıl destek olursun?":"¿Cómo puedes ayudar de forma segura sin quedarte en silencio?", "Veli ve öğretmenler":"Familias y docentes", "İşaretleri tanı, çocuğu dinle, doğru adımı at.":"Reconoce las señales, escucha al menor y actúa adecuadamente.",
"Zorbalık nedir, ne değildir?":"Qué es el acoso y qué no lo es", "Yaşıyorsan ne yapabilirsin?":"Qué puedes hacer si te está ocurriendo", "Kendine zarar verme düşüncen varsa":"Si tienes pensamientos de hacerte daño", "Gördüysen sessiz kalma":"Si lo has presenciado, no guardes silencio", "İnternette aşağılanıyor ya da tehdit ediliyorsan":"Si te humillan o amenazan en internet", "Çocuğunuz zorbalığa uğruyor olabilir":"Es posible que tu hijo esté sufriendo acoso", "Çocuğunuzun zorbalık yaptığı söyleniyorsa":"Si te dicen que tu hijo está acosando a alguien", "Bildirim geldiğinde":"Cuando llega un aviso",
"Formu gönderirsin ve gizli takip kodunu alırsın.":"Al enviar el formulario, recibirás un código privado de seguimiento.", "Kayıt, yetkili kişiler (rehberlik / okul yönetimi) tarafından incelenir; bunu bir insan yapar.":"El aviso lo revisa personal autorizado (orientación o dirección del centro); siempre lo hace una persona.", "Takip koduyla durumu görürsün. Sistemde mesajlaşma yoktur; bu yüzden acil durumlarda bir yetişkine ulaş.":"Puedes consultar el estado con tu código. La plataforma no permite enviar mensajes; en una emergencia, contacta con una persona adulta.", "Rehberlik içerikleri taslaktır; okul psikolojik danışmanı tarafından onaylanmalıdır.":"Los contenidos de orientación son borradores y deben ser aprobados por el profesional de orientación escolar.",
"Ne zaman bildiriliyor?":"¿Cuándo se envían los avisos?", "Saate göre (bildirimin yapıldığı saat)":"Por hora (hora de envío del aviso)", "Haftanın gününe göre":"Por día de la semana", "Haftalık eğilim":"Tendencia semanal", "Hangi ortamda, hangi tür?":"¿Qué tipo de incidente y en qué entorno?", "Ortama göre":"Por entorno", "Olay türüne göre":"Por tipo de incidente", "En çok bildirilen ortam":"Entorno con más avisos", "En çok bildirilen tür":"Tipo de incidente más comunicado", "Dönem":"Periodo", "Küçük hücre eşiği (k)":"Umbral para grupos pequeños (k)", "Kayıt sayısı":"Número de avisos", "Bu dönemde kayıt yok.":"No hay avisos en este periodo.", "Bu filtrelerle eşleşen kayıt bulunamadı.":"No hay avisos que coincidan con estos filtros.",
"Bildirim sayısındaki artış, olayların arttığını değil bildirme isteğinin arttığını da gösterebilir; ayrım için ayrı bir ölçüm (ör. anket) gerekir. Saat, olayın değil bildirimin saatidir; anonim kayıtlarda zaman dakika ve saniye hassasiyetinde kaydedilir.":"Un aumento de los avisos también puede indicar una mayor disposición a comunicar situaciones, no necesariamente más incidentes. Para distinguirlo se necesita otra medición, como una encuesta. La hora mostrada es la del envío del aviso, no la del incidente. En los avisos anónimos se registra la hora con precisión de minutos.", "Çapraz tabloda sayısı bu değerden küçük hücreler kimliksizleştirme için gizlenir.":"Las celdas con menos registros que este umbral se ocultan para proteger la identidad.",
"Gizlilik ve KVKK paneli":"Panel de privacidad y protección de datos", "Hangi veri neden toplanıyor, ne kadar saklanıyor ve nasıl siliniyor. Metinler taslaktır.":"Qué datos se recogen, con qué finalidad, durante cuánto tiempo y cómo se eliminan. Los textos son borradores.", "Aydınlatma metni":"Aviso de privacidad", "Veri envanteri":"Inventario de datos", "Saklama ve imha":"Conservación y eliminación", "Onam akışı (simülasyon)":"Proceso de consentimiento (simulación)", "Köşeli parantezli alanlar doldurulmadan ve hukuk danışmanı onaylamadan yayımlanmamalıdır.":"No publiques este texto hasta completar los campos entre corchetes y obtener la revisión de un asesor jurídico.", "Veri minimizasyonu (sistemde uygulananlar)":"Minimización de datos (medidas aplicadas)", "Açık riskler (raporda belirtilmeli)":"Riesgos pendientes (deben indicarse en el informe)", "Otomatik/elle imha kuralları":"Reglas de eliminación automática o manual", "Önizleme: saklama süresi (gün)":"Vista previa: periodo de conservación (días)", "Canlı silinecek kayıt sayısı yalnızca yönetici oturumunda görünür.":"El número de avisos que se eliminarían realmente solo es visible durante una sesión de administración.",
"SİMÜLASYON: Bu akış gerçek onam toplamaz, hiçbir veri kaydetmez ve kimseyle iletişime geçmez. Araştırmada onam, okulun resmî kanallarıyla yazılı olarak alınmalıdır.":"SIMULACIÓN: este proceso no recoge consentimiento real, no guarda datos ni contacta con nadie. Para la investigación, el consentimiento debe obtenerse por escrito mediante los canales oficiales del centro.", "Katılımcının yaş grubu":"Grupo de edad de la persona participante", "Bilgilendirmeyi okudum, gönüllü katılıyorum (simülasyon).":"He leído la información y participo voluntariamente (simulación).", "Veli/yasal temsilci izin verdi (simülasyon).":"El padre, madre o representante legal ha dado su autorización (simulación).", "Simülasyon tamamlandı: katılım koşulları sağlandı.":"Simulación completada: se cumplen las condiciones de participación.", "18 yaşından küçüklerde gönüllü katılımın yanında veli/yasal temsilcinin bilgilendirilmesi ve izni gerekir.":"Para menores de 18 años, además de la participación voluntaria, se requiere informar y obtener el permiso del padre, madre o representante legal.", "18 yaş ve üzeri katılımcı için veli izni gerekmez; kendi gönüllü onamı yeterlidir.":"Las personas de 18 años o más no necesitan autorización parental; basta con su propio consentimiento voluntario.", "Bu aşamadan sonra katılımcı bildirim formunu kullanabilir. Katılımcıdan **ad, sınıf, telefon istenmez**; onay kaydı bu uygulamada tutulmaz, okulda yazılı saklanır.":"Después, la persona participante puede utilizar el formulario. **No se solicitan nombre, curso ni teléfono**; el consentimiento no se almacena en esta aplicación, sino que se conserva por escrito en el centro.", "Gönüllü katılım ve veli onam formu taslağı (.txt)":"Borrador del formulario de participación voluntaria y consentimiento familiar (.txt)", "Baştan başla":"Empezar de nuevo", "İleri":"Siguiente",
"Aktif takip":"Seguimiento activo", "Anonim oranı":"Porcentaje de avisos anónimos", "Örnek sayısı":"Tamaño de la muestra", "Grafikler yalnızca bu uygulamada kayıtlı bilgileri özetler; okul geneline ilişkin sonuç göstermez.":"Los gráficos resumen únicamente los datos guardados en esta aplicación y no representan a todo el centro educativo.", "Bu karşılaştırma yalnızca bildirim sayısındaki gözlemsel değişimi gösterir; olayların gerçek sıklığını veya çalışmanın nedensel etkisini kanıtlamaz.":"Esta comparación solo muestra el cambio observado en el número de avisos. No demuestra la frecuencia real de los incidentes ni un efecto causal de la actividad.", "Öncesi / sonrası gözlemsel karşılaştırma":"Comparación observacional antes y después", "Önleyici çalışmalar":"Acciones preventivas", "Çalışma başlığı":"Título de la actividad", "Sorumlu öğretmen / yetkili kişi":"Docente o persona autorizada responsable", "Sorumlu birim":"Unidad responsable", "Planlanan tarih":"Fecha prevista", "Çalışma durumu":"Estado de la actividad", "Çalışmayı kaydet":"Guardar actividad", "Henüz çalışma oluşturulmadı. İlk çalışmayı yukarıdaki formdan ekleyebilirsiniz.":"Todavía no se ha creado ninguna actividad. Puedes añadir la primera mediante el formulario anterior.", "Bu bölüm demo amaçlıdır. Sorumlu öğretmen/yetkili kişi bilgisini yönetici kendisi girer. Bu sürümde gerçek öğrenci veya personel bilgisi yerine örnek veri kullanın.":"Esta sección es una demostración. El administrador introduce el nombre del docente o de la persona autorizada responsable. En esta versión, utiliza datos ficticios en lugar de datos reales de estudiantes o personal.", "Yönetici kendisi yazar":"Lo introduce el administrador", "Açıklama kalitesi kontrolü:":"Comprobación de la calidad de la descripción:", "Metin temel uzunluk kontrolünü geçti. Bu, bildirimin doğru olduğu anlamına gelmez.":"El texto ha superado la comprobación básica de longitud. Esto no significa que el aviso sea correcto.", "Metin çok kısa, yeterince açıklayıcı olmayabilir veya tekrar eden karakterler içeriyor. Bu bir spam/asılsız bildirim kanıtı değildir; otomatik silinmez, yetkili kişi bağlamı kontrol etmelidir.":"El texto puede ser demasiado corto, poco claro o contener caracteres repetidos. Esto no demuestra que sea spam o un aviso falso. No se elimina automáticamente; una persona autorizada debe revisar el contexto.", "Girişler, başarısız denemeler, dışa aktarımlar ve silme işlemleri burada izlenir.":"Aquí se registran los accesos, intentos fallidos, exportaciones y eliminaciones.", "Henüz denetim kaydı yok.":"Todavía no hay registros de auditoría.", "Henüz işlem geçmişi yok.":"Todavía no hay historial de actividad.", "Henüz not eklenmemiş.":"Todavía no se han añadido notas.", "Boş not eklenemez.":"No se puede añadir una nota vacía.", "Not kaydedilemedi.":"No se ha podido guardar la nota.", "Değişiklik kaydedilemedi. Lütfen yeniden deneyin.":"No se han podido guardar los cambios. Inténtalo de nuevo.", "Kayıt oluşturulamadı. Lütfen daha sonra tekrar dene.":"No se ha podido crear el registro. Inténtalo más tarde.", "Notu kaydet":"Guardar nota", "Yeni not":"Nueva nota", "Değerlendirme / işlem notu":"Nota de evaluación / actuación", "Kayıt sayısı çok az; yüzdeler ve karşılaştırmalar yanıltıcı olabilir, yorum yapmayın.":"Hay muy pocos avisos; los porcentajes y las comparaciones pueden inducir a error y no deben interpretarse.", "Sistem genelinde çok fazla hatalı giriş denemesi var. Lütfen bir süre sonra tekrar deneyin.":"Se han producido demasiados intentos fallidos de acceso en todo el sistema. Inténtalo de nuevo más tarde.", "Yönetici bilgileri ayarlanmamış. .streamlit/secrets.toml (veya Streamlit Cloud > Settings > Secrets) içindeki [admin] bölümünü yapılandırın.":"Las credenciales de administración no están configuradas. Configura la sección [admin] en .streamlit/secrets.toml (o en Streamlit Cloud > Settings > Secrets).",
"Yazdıkların için endişeleniyoruz. Şu an güvende değilsen ya da kendini veya başkasını tehlikede hissediyorsan lütfen hemen güvendiğin bir yetişkine, okul rehber öğretmenine ya da yukarıdaki acil hatlara ulaş.":"Nos preocupa lo que has escrito. Si ahora no estás a salvo o crees que tú u otra persona estáis en peligro, contacta de inmediato con una persona adulta de confianza, el servicio de orientación del centro o los servicios de emergencia indicados arriba.",
},
"العربية": {
"Acil bir tehlike varsa beklemeyin:":"إذا كان هناك خطر فوري، فلا تنتظر:", "Acil Çağrı Merkezi (Polis, Sağlık, Jandarma - 7/24)":"الطوارئ 112 (الشرطة والخدمات الطبية والدرك – على مدار الساعة)", "ALO Sosyal Destek Hattı (7/24)":"خط الدعم الاجتماعي ALO 183 (على مدار الساعة)", "MEB İletişim Merkezi (MEBİM)":"مركز الاتصال بوزارة التعليم التركية (MEBİM)",
"Yaşıyorsan":"إذا كنت تتعرض للتنمّر", "Kime anlatabileceğini ve neler yapabileceğini öğren.":"تعرّف إلى الشخص الذي يمكنك التحدث إليه والخطوات التي يمكنك اتخاذها.", "Tanık olduysan":"إذا شاهدت التنمّر", "Sessiz kalmadan, güvenli şekilde nasıl destek olursun?":"كيف تقدم الدعم بأمان دون التزام الصمت؟", "Veli ve öğretmenler":"أولياء الأمور والمعلمون", "İşaretleri tanı, çocuğu dinle, doğru adımı at.":"تعرّف إلى العلامات، واستمع إلى الطالب، واتخذ الخطوة المناسبة.",
"Zorbalık nedir, ne değildir?":"ما التنمّر وما الذي لا يُعدّ تنمّرًا؟", "Yaşıyorsan ne yapabilirsin?":"ماذا يمكنك أن تفعل إذا كنت تتعرض للتنمّر؟", "Kendine zarar verme düşüncen varsa":"إذا راودتك أفكار بإيذاء نفسك", "Gördüysen sessiz kalma":"إذا شاهدت موقفًا، فلا تلتزم الصمت", "İnternette aşağılanıyor ya da tehdit ediliyorsan":"إذا تعرضت للإهانة أو التهديد عبر الإنترنت", "Çocuğunuz zorbalığa uğruyor olabilir":"قد يكون طفلك يتعرض للتنمّر", "Çocuğunuzun zorbalık yaptığı söyleniyorsa":"إذا أُبلغت بأن طفلك يتنمّر على شخص آخر", "Bildirim geldiğinde":"عند وصول بلاغ",
"Formu gönderirsin ve gizli takip kodunu alırsın.":"بعد إرسال النموذج، ستحصل على رمز متابعة سري.", "Kayıt, yetkili kişiler (rehberlik / okul yönetimi) tarafından incelenir; bunu bir insan yapar.":"يراجع البلاغ أشخاص مخوّلون (قسم الإرشاد أو إدارة المدرسة)، وتتم المراجعة بواسطة إنسان.", "Takip koduyla durumu görürsün. Sistemde mesajlaşma yoktur; bu yüzden acil durumlarda bir yetişkine ulaş.":"يمكنك متابعة الحالة باستخدام الرمز. لا توجد خدمة مراسلة في النظام؛ لذلك تواصل مع شخص بالغ في الحالات العاجلة.", "Rehberlik içerikleri taslaktır; okul psikolojik danışmanı tarafından onaylanmalıdır.":"محتويات دليل الدعم مسودات ويجب اعتمادها من المرشد النفسي المدرسي.",
"Ne zaman bildiriliyor?":"متى تُرسل البلاغات؟", "Saate göre (bildirimin yapıldığı saat)":"حسب الساعة (وقت إرسال البلاغ)", "Haftanın gününe göre":"حسب يوم الأسبوع", "Haftalık eğilim":"الاتجاه الأسبوعي", "Hangi ortamda, hangi tür?":"ما نوع الحادثة وفي أي بيئة؟", "Ortama göre":"حسب البيئة", "Olay türüne göre":"حسب نوع الحادثة", "En çok bildirilen ortam":"البيئة الأكثر ورودًا في البلاغات", "En çok bildirilen tür":"نوع الحادثة الأكثر ورودًا", "Dönem":"الفترة", "Küçük hücre eşiği (k)":"حدّ إخفاء المجموعات الصغيرة (k)", "Kayıt sayısı":"عدد البلاغات", "Bu dönemde kayıt yok.":"لا توجد بلاغات خلال هذه الفترة.", "Bu filtrelerle eşleşen kayıt bulunamadı.":"لم يتم العثور على بلاغات تطابق عوامل التصفية هذه.",
"Bildirim sayısındaki artış, olayların arttığını değil bildirme isteğinin arttığını da gösterebilir; ayrım için ayrı bir ölçüm (ör. anket) gerekir. Saat, olayın değil bildirimin saatidir; anonim kayıtlarda zaman dakika ve saniye hassasiyetinde kaydedilir.":"قد تشير زيادة عدد البلاغات إلى زيادة الرغبة في الإبلاغ، وليس بالضرورة إلى زيادة الحوادث. ويلزم قياس منفصل، مثل استبيان، للتمييز بين الأمرين. الوقت المعروض هو وقت إرسال البلاغ وليس وقت الحادثة. ويُسجّل وقت البلاغات المجهولة بدقة الدقائق.", "Çapraz tabloda sayısı bu değerden küçük hücreler kimliksizleştirme için gizlenir.":"تُخفى الخلايا التي يقل عددها عن هذا الحد لحماية الهوية.",
"Gizlilik ve KVKK paneli":"لوحة الخصوصية وحماية البيانات", "Hangi veri neden toplanıyor, ne kadar saklanıyor ve nasıl siliniyor. Metinler taslaktır.":"ما البيانات التي تُجمع ولماذا، ومدة الاحتفاظ بها، وكيفية حذفها. النصوص مسودات.", "Aydınlatma metni":"إشعار الخصوصية", "Veri envanteri":"سجل البيانات", "Saklama ve imha":"الاحتفاظ بالبيانات وحذفها", "Onam akışı (simülasyon)":"مسار الموافقة (محاكاة)", "Köşeli parantezli alanlar doldurulmadan ve hukuk danışmanı onaylamadan yayımlanmamalıdır.":"لا يجوز نشر هذا النص قبل استكمال الحقول بين الأقواس المربعة ومراجعته من مستشار قانوني.", "Veri minimizasyonu (sistemde uygulananlar)":"تقليل البيانات (الإجراءات المطبقة في النظام)", "Açık riskler (raporda belirtilmeli)":"المخاطر القائمة (يجب ذكرها في التقرير)", "Otomatik/elle imha kuralları":"قواعد الحذف التلقائي أو اليدوي", "Önizleme: saklama süresi (gün)":"معاينة: مدة الاحتفاظ (بالأيام)", "Canlı silinecek kayıt sayısı yalnızca yönetici oturumunda görünür.":"لا يظهر عدد البلاغات التي ستُحذف فعليًا إلا أثناء جلسة المسؤول.",
"SİMÜLASYON: Bu akış gerçek onam toplamaz, hiçbir veri kaydetmez ve kimseyle iletişime geçmez. Araştırmada onam, okulun resmî kanallarıyla yazılı olarak alınmalıdır.":"محاكاة: لا تجمع هذه الخطوات موافقة حقيقية، ولا تحفظ أي بيانات، ولا تتواصل مع أي شخص. في البحث، يجب الحصول على الموافقة كتابيًا عبر القنوات الرسمية للمدرسة.", "Katılımcının yaş grubu":"الفئة العمرية للمشارك", "Bilgilendirmeyi okudum, gönüllü katılıyorum (simülasyon).":"قرأت المعلومات وأوافق على المشاركة طوعًا (محاكاة).", "Veli/yasal temsilci izin verdi (simülasyon).":"وافق ولي الأمر أو الممثل القانوني (محاكاة).", "Simülasyon tamamlandı: katılım koşulları sağlandı.":"اكتملت المحاكاة: تم استيفاء شروط المشاركة.", "18 yaşından küçüklerde gönüllü katılımın yanında veli/yasal temsilcinin bilgilendirilmesi ve izni gerekir.":"بالنسبة لمن هم دون 18 عامًا، يجب إلى جانب المشاركة الطوعية إبلاغ ولي الأمر أو الممثل القانوني والحصول على موافقته.", "18 yaş ve üzeri katılımcı için veli izni gerekmez; kendi gönüllü onamı yeterlidir.":"لا يحتاج المشاركون الذين تبلغ أعمارهم 18 عامًا أو أكثر إلى موافقة الوالدين؛ تكفي موافقتهم الطوعية.", "Bu aşamadan sonra katılımcı bildirim formunu kullanabilir. Katılımcıdan **ad, sınıf, telefon istenmez**; onay kaydı bu uygulamada tutulmaz, okulda yazılı saklanır.":"بعد هذه الخطوة، يمكن للمشارك استخدام نموذج الإبلاغ. **لا يُطلب الاسم أو الصف أو رقم الهاتف**؛ ولا يُحفظ سجل الموافقة في هذا التطبيق، بل يُحتفظ به كتابيًا في المدرسة.", "Gönüllü katılım ve veli onam formu taslağı (.txt)":"مسودة نموذج المشاركة الطوعية وموافقة ولي الأمر (.txt)", "Baştan başla":"ابدأ من جديد", "İleri":"التالي",
"Aktif takip":"المتابعة النشطة", "Anonim oranı":"نسبة البلاغات المجهولة", "Örnek sayısı":"حجم العينة", "Grafikler yalnızca bu uygulamada kayıtlı bilgileri özetler; okul geneline ilişkin sonuç göstermez.":"تلخّص الرسوم البيانات المسجلة في هذا التطبيق فقط، ولا تمثل نتائج المدرسة بأكملها.", "Bu karşılaştırma yalnızca bildirim sayısındaki gözlemsel değişimi gösterir; olayların gerçek sıklığını veya çalışmanın nedensel etkisini kanıtlamaz.":"تعرض هذه المقارنة التغير الملحوظ في عدد البلاغات فقط. ولا تثبت المعدل الفعلي للحوادث أو وجود تأثير سببي للنشاط.", "Öncesi / sonrası gözlemsel karşılaştırma":"مقارنة رصدية قبل الإجراء وبعده", "Önleyici çalışmalar":"الإجراءات الوقائية", "Çalışma başlığı":"عنوان النشاط", "Sorumlu öğretmen / yetkili kişi":"المعلم أو الشخص المخوّل المسؤول", "Sorumlu birim":"الجهة المسؤولة", "Planlanan tarih":"التاريخ المخطط", "Çalışma durumu":"حالة النشاط", "Çalışmayı kaydet":"حفظ النشاط", "Henüz çalışma oluşturulmadı. İlk çalışmayı yukarıdaki formdan ekleyebilirsiniz.":"لم يتم إنشاء أي نشاط بعد. يمكنك إضافة النشاط الأول باستخدام النموذج أعلاه.", "Bu bölüm demo amaçlıdır. Sorumlu öğretmen/yetkili kişi bilgisini yönetici kendisi girer. Bu sürümde gerçek öğrenci veya personel bilgisi yerine örnek veri kullanın.":"هذا القسم تجريبي. يُدخل المسؤول بنفسه اسم المعلم أو الشخص المخوّل المسؤول. استخدم بيانات تجريبية بدلًا من بيانات الطلاب أو الموظفين الحقيقية في هذه النسخة.", "Yönetici kendisi yazar":"يُدخله المسؤول بنفسه", "Açıklama kalitesi kontrolü:":"التحقق من جودة الوصف:", "Metin temel uzunluk kontrolünü geçti. Bu, bildirimin doğru olduğu anlamına gelmez.":"اجتاز النص فحص الطول الأساسي. ولا يعني ذلك أن البلاغ صحيح.", "Metin çok kısa, yeterince açıklayıcı olmayabilir veya tekrar eden karakterler içeriyor. Bu bir spam/asılsız bildirim kanıtı değildir; otomatik silinmez, yetkili kişi bağlamı kontrol etmelidir.":"قد يكون النص قصيرًا جدًا أو غير واضح بما يكفي أو يحتوي على أحرف متكررة. وهذا لا يثبت أنه بريد مزعج أو بلاغ كاذب. لن يُحذف تلقائيًا؛ بل يجب على شخص مخوّل مراجعة السياق.", "Girişler, başarısız denemeler, dışa aktarımlar ve silme işlemleri burada izlenir.":"تُسجّل هنا عمليات الدخول والمحاولات الفاشلة والتصدير والحذف.", "Henüz denetim kaydı yok.":"لا توجد سجلات تدقيق بعد.", "Henüz işlem geçmişi yok.":"لا يوجد سجل للعمليات بعد.", "Henüz not eklenmemiş.":"لم تتم إضافة أي ملاحظات بعد.", "Boş not eklenemez.":"لا يمكن إضافة ملاحظة فارغة.", "Not kaydedilemedi.":"تعذّر حفظ الملاحظة.", "Değişiklik kaydedilemedi. Lütfen yeniden deneyin.":"تعذّر حفظ التغيير. يُرجى المحاولة مرة أخرى.", "Kayıt oluşturulamadı. Lütfen daha sonra tekrar dene.":"تعذّر إنشاء السجل. يُرجى المحاولة لاحقًا.", "Notu kaydet":"حفظ الملاحظة", "Yeni not":"ملاحظة جديدة", "Değerlendirme / işlem notu":"ملاحظة التقييم / الإجراء", "Kayıt sayısı çok az; yüzdeler ve karşılaştırmalar yanıltıcı olabilir, yorum yapmayın.":"عدد البلاغات قليل جدًا؛ وقد تكون النسب والمقارنات مضللة، لذا لا ينبغي تفسيرها.", "Sistem genelinde çok fazla hatalı giriş denemesi var. Lütfen bir süre sonra tekrar deneyin.":"حدث عدد كبير جدًا من محاولات تسجيل الدخول الفاشلة على مستوى النظام. يُرجى المحاولة لاحقًا.", "Yönetici bilgileri ayarlanmamış. .streamlit/secrets.toml (veya Streamlit Cloud > Settings > Secrets) içindeki [admin] bölümünü yapılandırın.":"لم يتم إعداد بيانات دخول المسؤول. يرجى ضبط القسم [admin] في الملف .streamlit/secrets.toml (أو في Streamlit Cloud > Settings > Secrets).",
"Yazdıkların için endişeleniyoruz. Şu an güvende değilsen ya da kendini veya başkasını tehlikede hissediyorsan lütfen hemen güvendiğin bir yetişkine, okul rehber öğretmenine ya da yukarıdaki acil hatlara ulaş.":"نحن نهتم بما كتبته. إذا لم تكن آمنًا الآن أو شعرت بأنك أو شخصًا آخر في خطر، فتواصل فورًا مع شخص بالغ تثق به أو المرشد المدرسي أو إحدى جهات الطوارئ المذكورة أعلاه.",
},
"Azərbaycan dili": {
"Acil bir tehlike varsa beklemeyin:":"Təcili təhlükə varsa, gözləməyin:", "Acil Çağrı Merkezi (Polis, Sağlık, Jandarma - 7/24)":"112 Təcili Yardım Mərkəzi (polis, tibbi xidmət və jandarma – 24/7)", "ALO Sosyal Destek Hattı (7/24)":"ALO 183 Sosial Dəstək Xətti (24/7)", "MEB İletişim Merkezi (MEBİM)":"Türkiyə Təhsil Nazirliyinin Əlaqə Mərkəzi (MEBİM)",
"Yaşıyorsan":"Əgər bunu yaşayırsınızsa", "Kime anlatabileceğini ve neler yapabileceğini öğren.":"Kimə müraciət edə biləcəyinizi və hansı addımları ata biləcəyinizi öyrənin.", "Tanık olduysan":"Əgər şahid olmusunuzsa", "Sessiz kalmadan, güvenli şekilde nasıl destek olursun?":"Susmadan və özünüzü riskə atmadan necə dəstək ola biləcəyinizi öyrənin.", "Veli ve öğretmenler":"Valideynlər və müəllimlər", "İşaretleri tanı, çocuğu dinle, doğru adımı at.":"Əlamətləri tanıyın, uşağı dinləyin və düzgün addım atın.",
"Zorbalık nedir, ne değildir?":"Zorakılıq nədir, nə deyil?", "Yaşıyorsan ne yapabilirsin?":"Bunu yaşayırsınızsa nə edə bilərsiniz?", "Kendine zarar verme düşüncen varsa":"Özünüzə zərər vermək barədə düşüncələriniz varsa", "Gördüysen sessiz kalma":"Şahid olmusunuzsa, susmayın", "İnternette aşağılanıyor ya da tehdit ediliyorsan":"İnternetdə təhqir və ya təhdid olunursunuzsa", "Çocuğunuz zorbalığa uğruyor olabilir":"Uşağınız zorakılığa məruz qala bilər", "Çocuğunuzun zorbalık yaptığı söyleniyorsa":"Uşağınızın başqasına zorakılıq etdiyi deyilirsə", "Bildirim geldiğinde":"Bildiriş daxil olduqda",
"Formu gönderirsin ve gizli takip kodunu alırsın.":"Formanı göndərdikdən sonra məxfi izləmə kodu alırsınız.", "Kayıt, yetkili kişiler (rehberlik / okul yönetimi) tarafından incelenir; bunu bir insan yapar.":"Müraciət səlahiyyətli şəxslər (psixoloji dəstək xidməti və ya məktəb rəhbərliyi) tərəfindən yoxlanılır; bunu insan həyata keçirir.", "Takip koduyla durumu görürsün. Sistemde mesajlaşma yoktur; bu yüzden acil durumlarda bir yetişkine ulaş.":"İzləmə kodu ilə vəziyyəti görə bilərsiniz. Sistemdə mesajlaşma yoxdur; təcili vəziyyətdə böyüklərdən birinə müraciət edin.", "Rehberlik içerikleri taslaktır; okul psikolojik danışmanı tarafından onaylanmalıdır.":"Dəstək bələdçisinin məzmunu layihədir və məktəb psixoloqu tərəfindən təsdiqlənməlidir.",
"Ne zaman bildiriliyor?":"Bildirişlər nə vaxt göndərilir?", "Saate göre (bildirimin yapıldığı saat)":"Saata görə (bildirişin göndərildiyi vaxt)", "Haftanın gününe göre":"Həftənin gününə görə", "Haftalık eğilim":"Həftəlik dinamika", "Hangi ortamda, hangi tür?":"Hansı mühitdə hansı hadisə növü?", "Ortama göre":"Mühitə görə", "Olay türüne göre":"Hadisə növünə görə", "En çok bildirilen ortam":"Ən çox bildirilən mühit", "En çok bildirilen tür":"Ən çox bildirilən hadisə növü", "Dönem":"Dövr", "Küçük hücre eşiği (k)":"Kiçik qruplar üçün hədd (k)", "Kayıt sayısı":"Müraciətlərin sayı", "Bu dönemde kayıt yok.":"Bu dövr üçün müraciət yoxdur.", "Bu filtrelerle eşleşen kayıt bulunamadı.":"Bu filtrlərə uyğun müraciət tapılmadı.",
"Bildirim sayısındaki artış, olayların arttığını değil bildirme isteğinin arttığını da gösterebilir; ayrım için ayrı bir ölçüm (ör. anket) gerekir. Saat, olayın değil bildirimin saatidir; anonim kayıtlarda zaman dakika ve saniye hassasiyetinde kaydedilir.":"Bildirişlərin sayının artması hadisələrin çoxalmasını deyil, məlumat vermək istəyinin artmasını da göstərə bilər. Bunları ayırd etmək üçün ayrıca ölçmə, məsələn, sorğu lazımdır. Göstərilən vaxt hadisənin deyil, bildirişin göndərildiyi vaxtdır. Anonim müraciətlərdə vaxt dəqiqə dəqiqliyi ilə qeydə alınır.", "Çapraz tabloda sayısı bu değerden küçük hücreler kimliksizleştirme için gizlenir.":"Sayı bu həddən az olan xanalar məxfiliyi qorumaq üçün gizlədilir.",
"Gizlilik ve KVKK paneli":"Məxfilik və fərdi məlumatların qorunması paneli", "Hangi veri neden toplanıyor, ne kadar saklanıyor ve nasıl siliniyor. Metinler taslaktır.":"Hansı məlumatların nə üçün toplandığı, nə qədər saxlandığı və necə silindiyi. Mətnlər layihədir.", "Aydınlatma metni":"Məlumatlandırma mətni", "Veri envanteri":"Məlumat reyestri", "Saklama ve imha":"Saxlanma və məhv etmə", "Onam akışı (simülasyon)":"Razılıq prosesi (simulyasiya)", "Köşeli parantezli alanlar doldurulmadan ve hukuk danışmanı onaylamadan yayımlanmamalıdır.":"Kvadrat mötərizədəki sahələr doldurulmadan və hüquq məsləhətçisi təsdiqləmədən bu mətn dərc edilməməlidir.", "Veri minimizasyonu (sistemde uygulananlar)":"Məlumatların minimumlaşdırılması (sistemdə tətbiq edilənlər)", "Açık riskler (raporda belirtilmeli)":"Açıq risklər (hesabatda göstərilməlidir)", "Otomatik/elle imha kuralları":"Avtomatik və əl ilə silinmə qaydaları", "Önizleme: saklama süresi (gün)":"Önizləmə: saxlanma müddəti (gün)", "Canlı silinecek kayıt sayısı yalnızca yönetici oturumunda görünür.":"Faktiki silinəcək müraciətlərin sayı yalnız administrator sessiyasında görünür.",
"SİMÜLASYON: Bu akış gerçek onam toplamaz, hiçbir veri kaydetmez ve kimseyle iletişime geçmez. Araştırmada onam, okulun resmî kanallarıyla yazılı olarak alınmalıdır.":"SİMULYASİYA: Bu proses real razılıq toplamır, heç bir məlumat saxlamır və heç kimlə əlaqə yaratmır. Tədqiqat üçün razılıq məktəbin rəsmi kanalları vasitəsilə yazılı alınmalıdır.", "Katılımcının yaş grubu":"İştirakçının yaş qrupu", "Bilgilendirmeyi okudum, gönüllü katılıyorum (simülasyon).":"Məlumatlandırmanı oxudum və könüllü iştirak edirəm (simulyasiya).", "Veli/yasal temsilci izin verdi (simülasyon).":"Valideyn/qanuni nümayəndə icazə verdi (simulyasiya).", "Simülasyon tamamlandı: katılım koşulları sağlandı.":"Simulyasiya tamamlandı: iştirak şərtləri yerinə yetirildi.", "18 yaşından küçüklerde gönüllü katılımın yanında veli/yasal temsilcinin bilgilendirilmesi ve izni gerekir.":"18 yaşdan kiçik iştirakçılar üçün könüllü iştirakla yanaşı valideynin və ya qanuni nümayəndənin məlumatlandırılması və razılığı tələb olunur.", "18 yaş ve üzeri katılımcı için veli izni gerekmez; kendi gönüllü onamı yeterlidir.":"18 yaş və yuxarı iştirakçılar üçün valideyn icazəsi tələb olunmur; şəxsin öz könüllü razılığı kifayətdir.", "Bu aşamadan sonra katılımcı bildirim formunu kullanabilir. Katılımcıdan **ad, sınıf, telefon istenmez**; onay kaydı bu uygulamada tutulmaz, okulda yazılı saklanır.":"Bu mərhələdən sonra iştirakçı bildiriş formasından istifadə edə bilər. İştirakçıdan **ad, sinif və telefon tələb olunmur**; razılıq qeydi bu tətbiqdə saxlanmır, məktəbdə yazılı şəkildə qorunur.", "Gönüllü katılım ve veli onam formu taslağı (.txt)":"Könüllü iştirak və valideyn razılığı formasının layihəsi (.txt)", "Baştan başla":"Yenidən başla", "İleri":"İrəli",
"Aktif takip":"Aktiv izləmə", "Anonim oranı":"Anonim müraciətlərin payı", "Örnek sayısı":"Nümunə sayı", "Grafikler yalnızca bu uygulamada kayıtlı bilgileri özetler; okul geneline ilişkin sonuç göstermez.":"Qrafiklər yalnız bu tətbiqdə qeydə alınmış məlumatları ümumiləşdirir və bütün məktəb üzrə nəticə göstərmir.", "Bu karşılaştırma yalnızca bildirim sayısındaki gözlemsel değişimi gösterir; olayların gerçek sıklığını veya çalışmanın nedensel etkisini kanıtlamaz.":"Bu müqayisə yalnız bildiriş sayındakı müşahidə olunan dəyişikliyi göstərir. Hadisələrin real tezliyini və ya tədbirin səbəb-nəticə təsirini sübut etmir.", "Öncesi / sonrası gözlemsel karşılaştırma":"Tədbirdən əvvəl və sonra müşahidə müqayisəsi", "Önleyici çalışmalar":"Profilaktik tədbirlər", "Çalışma başlığı":"Tədbirin başlığı", "Sorumlu öğretmen / yetkili kişi":"Məsul müəllim / səlahiyyətli şəxs", "Sorumlu öğretmen / yetkili kişi":"Məsul müəllim / səlahiyyətli şəxs", "Sorumlu birim":"Məsul bölmə", "Planlanan tarih":"Planlaşdırılan tarix", "Çalışma durumu":"Tədbirin statusu", "Çalışmayı kaydet":"Tədbiri yadda saxla", "Henüz çalışma oluşturulmadı. İlk çalışmayı yukarıdaki formdan ekleyebilirsiniz.":"Hələ heç bir tədbir yaradılmayıb. İlk tədbiri yuxarıdakı formdan əlavə edə bilərsiniz.", "Bu bölüm demo amaçlıdır. Sorumlu öğretmen/yetkili kişi bilgisini yönetici kendisi girer. Bu sürümde gerçek öğrenci veya personel bilgisi yerine örnek veri kullanın.":"Bu bölmə nümayiş üçündür. Məsul müəllimin və ya səlahiyyətli şəxsin məlumatını administrator özü daxil edir. Bu versiyada real şagird və ya işçi məlumatları əvəzinə nümunə məlumatlardan istifadə edin.", "Yönetici kendisi yazar":"Administrator özü daxil edir", "Açıklama kalitesi kontrolü:":"Təsvirin keyfiyyətinin yoxlanması:", "Metin temel uzunluk kontrolünü geçti. Bu, bildirimin doğru olduğu anlamına gelmez.":"Mətn əsas uzunluq yoxlamasından keçdi. Bu, müraciətin doğru olduğu demək deyil.", "Metin çok kısa, yeterince açıklayıcı olmayabilir veya tekrar eden karakterler içeriyor. Bu bir spam/asılsız bildirim kanıtı değildir; otomatik silinmez, yetkili kişi bağlamı kontrol etmelidir.":"Mətn çox qısa, kifayət qədər aydın olmayan və ya təkrarlanan simvollardan ibarət ola bilər. Bu, spam və ya əsassız müraciət sübutu deyil. Avtomatik silinmir; səlahiyyətli şəxs konteksti yoxlamalıdır.", "Girişler, başarısız denemeler, dışa aktarımlar ve silme işlemleri burada izlenir.":"Daxilolmalar, uğursuz cəhdlər, ixraclar və silmə əməliyyatları burada izlənir.", "Henüz denetim kaydı yok.":"Hələ audit qeydi yoxdur.", "Henüz işlem geçmişi yok.":"Hələ əməliyyat tarixçəsi yoxdur.", "Henüz not eklenmemiş.":"Hələ qeyd əlavə edilməyib.", "Boş not eklenemez.":"Boş qeyd əlavə edilə bilməz.", "Not kaydedilemedi.":"Qeydi yadda saxlamaq mümkün olmadı.", "Değişiklik kaydedilemedi. Lütfen yeniden deneyin.":"Dəyişikliyi yadda saxlamaq mümkün olmadı. Yenidən cəhd edin.", "Kayıt oluşturulamadı. Lütfen daha sonra tekrar dene.":"Qeyd yaratmaq mümkün olmadı. Daha sonra yenidən cəhd edin.", "Notu kaydet":"Qeydi yadda saxla", "Yeni not":"Yeni qeyd", "Değerlendirme / işlem notu":"Qiymətləndirmə / əməliyyat qeydi", "Kayıt sayısı çok az; yüzdeler ve karşılaştırmalar yanıltıcı olabilir, yorum yapmayın.":"Müraciətlərin sayı çox azdır; faizlər və müqayisələr yanıltıcı ola bilər, şərh edilməməlidir.", "Sistem genelinde çok fazla hatalı giriş denemesi var. Lütfen bir süre sonra tekrar deneyin.":"Sistem üzrə çox sayda uğursuz giriş cəhdi olub. Bir müddət sonra yenidən cəhd edin.", "Yönetici bilgileri ayarlanmamış. .streamlit/secrets.toml (veya Streamlit Cloud > Settings > Secrets) içindeki [admin] bölümünü yapılandırın.":"Administrator giriş məlumatları təyin edilməyib. .streamlit/secrets.toml faylındakı (və ya Streamlit Cloud > Settings > Secrets bölməsindəki) [admin] hissəsini konfiqurasiya edin.",
"Yazdıkların için endişeleniyoruz. Şu an güvende değilsen ya da kendini veya başkasını tehlikede hissediyorsan lütfen hemen güvendiğin bir yetişkine, okul rehber öğretmenine ya da yukarıdaki acil hatlara ulaş.":"Yazdıqlarınız bizi narahat edir. Hazırda təhlükəsiz deyilsinizsə və ya özünüzün, yaxud başqasının təhlükədə olduğunu düşünürsünüzsə, dərhal etibar etdiyiniz böyüyə, məktəb psixoloquna və ya yuxarıda göstərilən təcili yardım xətlərinə müraciət edin.",
},
}
for _language, _entries in _DEEP_UI.items():
    MULTI_CATALOG[_language].update(_entries)

# Full support-guide prose. Only application-authored guide copy is translated;
# report descriptions, notes and names remain untouched.
_GUIDE_COPY = {
"Deutsch": {
"Zorbalık; bilerek yapılan, tekrar eden ve güç dengesizliği olan davranıştır (alay, tehdit, dışlama, fiziksel saldırı, internette aşağılama).":"Mobbing ist ein absichtlich wiederholtes Verhalten, bei dem ein Machtungleichgewicht besteht (Verspotten, Drohen, Ausgrenzen, körperliche Angriffe oder Demütigung im Internet).",
"Arkadaşlar arasındaki tek seferlik tartışma genellikle zorbalık sayılmaz; ama seni korkutuyor ya da üzüyorsa yine de anlatmaya değer.":"Ein einmaliger Streit unter Freunden gilt normalerweise nicht als Mobbing. Wenn er dir jedoch Angst macht oder dich belastet, ist es trotzdem wichtig, darüber zu sprechen.",
"Olanlar senin suçun değildir.":"Was passiert ist, ist nicht deine Schuld.",
"Güvendiğin bir yetişkine (rehber öğretmen, sınıf öğretmeni, aile) olanı anlat.":"Erzähle einer erwachsenen Vertrauensperson davon, zum Beispiel einer Beratungslehrkraft, deiner Klassenleitung oder deiner Familie.",
"Cevap vermek zorunda değilsin; güvenli bir yere git, yanında birileriyle ol.":"Du musst nicht antworten. Geh an einen sicheren Ort und bleib bei anderen Menschen.",
"Mesaj ve ekran görüntülerini sakla, silme; yetişkine gösterirsin.":"Bewahre Nachrichten und Screenshots auf, statt sie zu löschen, und zeige sie einer erwachsenen Vertrauensperson.",
"Bu sitedeki anonim formu kullanabilirsin; ama form acil durum hattı değildir.":"Du kannst das anonyme Formular auf dieser Website verwenden. Es ist jedoch kein Notfalldienst.",
"Bu düşünceleri tek başına taşımak zorunda değilsin. Hemen güvendiğin bir yetişkine söyle.":"Du musst mit diesen Gedanken nicht allein bleiben. Sprich sofort mit einer erwachsenen Vertrauensperson.",
"Acil tehlikede 112'yi, destek için 183'ü arayabilirsin.":"Bei unmittelbarer Gefahr kannst du 112 wählen; Unterstützung erhältst du unter 183.",
"Zorbalığa gülmek ya da paylaşmak onu büyütür. Katılmamak bile bir destektir.":"Über Mobbing zu lachen oder es weiterzuverbreiten, verstärkt es. Nicht mitzumachen ist bereits eine Form der Unterstützung.",
"Güvenliysen mağdurun yanına git, yalnız olmadığını hissettir.":"Wenn es sicher ist, geh zu der betroffenen Person und zeige ihr, dass sie nicht allein ist.",
"Müdahale etmek tehlikeliyse bir yetişkine haber ver. Bu ‘çaksıl’ değil, arkadaşını korumaktır.":"Wenn ein Eingreifen gefährlich wäre, informiere eine erwachsene Person. Das ist kein Petzen, sondern schützt andere.",
"Anonim form ile adını vermeden bildirebilirsin.":"Du kannst den Vorfall über das anonyme Formular melden, ohne deinen Namen anzugeben.",
"Cevap verme, kişiyi engelle, platformda şikâyet et.":"Antworte nicht, blockiere die Person und melde sie auf der Plattform.",
"Kanıtları (ekran görüntüsü, tarih, hesap adı) sakla.":"Bewahre Belege auf, zum Beispiel Screenshots, Datum und Kontonamen.",
"Özel fotoğrafın izinsiz paylaşılıyorsa ya da paylaşılmakla tehdit ediliyorsan hemen bir yetişkine söyle; bu ciddi bir durumdur ve suç oluşturabilir.":"Wenn ein privates Foto ohne deine Zustimmung geteilt wird oder jemand damit droht, informiere sofort eine erwachsene Vertrauensperson. Das ist ernst und kann strafbar sein.",
"Şifrelerini kimseyle paylaşma, gizlilik ayarlarını gözden geçir.":"Teile deine Passwörter mit niemandem und überprüfe deine Datenschutzeinstellungen.",
"Sık görülen işaretler: okula gitmek istememe, uyku/iştah değişikliği, eşya kaybı, çekingenlik, telefona karşı aşırı tedirginlik. Bunlar tek başına kanıt değildir.":"Mögliche Anzeichen sind: nicht zur Schule gehen wollen, Veränderungen bei Schlaf oder Appetit, verlorene Gegenstände, Rückzug oder starke Anspannung beim Blick aufs Telefon. Für sich allein sind diese Anzeichen kein Beweis.",
"Önce sakin kalın, dinleyin; suçlamayın, ‘sen de karşılık ver’ demeyin.":"Bleiben Sie zunächst ruhig und hören Sie zu. Machen Sie keine Vorwürfe und sagen Sie nicht: „Wehr dich einfach“.",
"Olayı tarih ve ayrıntılarıyla yazın; okul rehberlik servisiyle görüşün.":"Notieren Sie den Vorfall mit Datum und Einzelheiten und wenden Sie sich an die schulische Beratungsstelle.",
"Çocuğunuzun kendine zarar verme düşüncesi olabileceğinden endişeleniyorsanız 112'yi arayın.":"Wenn Sie befürchten, dass Ihr Kind daran denkt, sich selbst zu verletzen, rufen Sie 112 an.",
"Savunmaya geçmeden dinleyin; davranışın başkasına verdiği zararı konuşun.":"Hören Sie zu, ohne sofort in die Defensive zu gehen, und sprechen Sie darüber, welchen Schaden das Verhalten verursacht hat.",
"Okul rehberlik servisiyle birlikte çalışın; cezadan çok davranış değişikliğini hedefleyin.":"Arbeiten Sie mit der schulischen Beratungsstelle zusammen und konzentrieren Sie sich auf Verhaltensänderungen statt nur auf Bestrafung.",
"Kaydı yalnızca insan olarak değerlendirin; otomatik sinyal kanıt veya karar değildir.":"Bewerten Sie die Meldung ausschließlich durch menschliche Prüfung. Ein automatisches Signal ist weder Beweis noch Entscheidung.",
"Kaynağı belirlemeye çalışmayın; bildirimin anonimliğini koruyun.":"Versuchen Sie nicht, die meldende Person zu identifizieren. Schützen Sie die Anonymität der Meldung.",
"Şüpheli öğrencinin yanlış suçlanma riskini gözetin; süreci rehberlik servisi ve okul yönetimiyle yürütün.":"Berücksichtigen Sie das Risiko einer ungerechtfertigten Beschuldigung und stimmen Sie das Vorgehen mit der Beratungsstelle und der Schulleitung ab.",
"Acil sinyal veya doğrudan zarar riski varsa okulun acil durum protokolünü uygulayın.":"Bei einem dringenden Signal oder unmittelbarer Gefahr wenden Sie das schulische Notfallverfahren an.",
},
"Français": {
"Zorbalık; bilerek yapılan, tekrar eden ve güç dengesizliği olan davranıştır (alay, tehdit, dışlama, fiziksel saldırı, internette aşağılama).":"Le harcèlement est un comportement intentionnel et répété, marqué par un déséquilibre de pouvoir (moqueries, menaces, exclusion, agressions physiques ou humiliations en ligne).",
"Arkadaşlar arasındaki tek seferlik tartışma genellikle zorbalık sayılmaz; ama seni korkutuyor ya da üzüyorsa yine de anlatmaya değer.":"Une dispute isolée entre amis n’est généralement pas du harcèlement. Mais si elle te fait peur ou te bouleverse, cela vaut quand même la peine d’en parler.",
"Olanlar senin suçun değildir.":"Ce qui s’est passé n’est pas de ta faute.", "Güvendiğin bir yetişkine (rehber öğretmen, sınıf öğretmeni, aile) olanı anlat.":"Parle de ce qui s’est passé à un adulte de confiance : conseiller scolaire, professeur principal ou membre de ta famille.",
"Cevap vermek zorunda değilsin; güvenli bir yere git, yanında birileriyle ol.":"Tu n’es pas obligé de répondre. Mets-toi dans un endroit sûr et reste avec d’autres personnes.", "Mesaj ve ekran görüntülerini sakla, silme; yetişkine gösterirsin.":"Conserve les messages et les captures d’écran au lieu de les supprimer, puis montre-les à un adulte de confiance.", "Bu sitedeki anonim formu kullanabilirsin; ama form acil durum hattı değildir.":"Tu peux utiliser le formulaire anonyme de ce site, mais ce formulaire ne remplace pas les services d’urgence.",
"Bu düşünceleri tek başına taşımak zorunda değilsin. Hemen güvendiğin bir yetişkine söyle.":"Tu n’as pas à porter ces pensées seul. Parle immédiatement à un adulte de confiance.", "Acil tehlikede 112'yi, destek için 183'ü arayabilirsin.":"En cas de danger immédiat, appelle le 112 ; pour obtenir du soutien, tu peux appeler le 183.",
"Zorbalığa gülmek ya da paylaşmak onu büyütür. Katılmamak bile bir destektir.":"Rire du harcèlement ou le partager ne fait que l’amplifier. Refuser d’y participer est déjà une forme de soutien.", "Güvenliysen mağdurun yanına git, yalnız olmadığını hissettir.":"Si tu peux le faire sans danger, va vers la personne ciblée et montre-lui qu’elle n’est pas seule.", "Müdahale etmek tehlikeliyse bir yetişkine haber ver. Bu ‘çaksıl’ değil, arkadaşını korumaktır.":"Si intervenir est dangereux, préviens un adulte. Ce n’est pas de la délation : c’est protéger quelqu’un.", "Anonim form ile adını vermeden bildirebilirsin.":"Tu peux faire un signalement anonyme sans donner ton nom.",
"Cevap verme, kişiyi engelle, platformda şikâyet et.":"Ne réponds pas, bloque la personne et signale son compte sur la plateforme.", "Kanıtları (ekran görüntüsü, tarih, hesap adı) sakla.":"Conserve les preuves : captures d’écran, dates et nom du compte.", "Özel fotoğrafın izinsiz paylaşılıyorsa ya da paylaşılmakla tehdit ediliyorsan hemen bir yetişkine söyle; bu ciddi bir durumdur ve suç oluşturabilir.":"Si une photo intime est partagée sans ton accord ou si quelqu’un menace de le faire, parle immédiatement à un adulte. C’est une situation grave qui peut constituer une infraction.", "Şifrelerini kimseyle paylaşma, gizlilik ayarlarını gözden geçir.":"Ne partage tes mots de passe avec personne et vérifie tes paramètres de confidentialité.",
"Sık görülen işaretler: okula gitmek istememe, uyku/iştah değişikliği, eşya kaybı, çekingenlik, telefona karşı aşırı tedirginlik. Bunlar tek başına kanıt değildir.":"Parmi les signes possibles : refus d’aller à l’école, changements de sommeil ou d’appétit, objets perdus, retrait ou forte anxiété liée au téléphone. Ces signes ne constituent pas une preuve à eux seuls.", "Önce sakin kalın, dinleyin; suçlamayın, ‘sen de karşılık ver’ demeyin.":"Restez d’abord calme et écoutez. Ne blâmez pas l’enfant et ne lui dites pas de riposter.", "Olayı tarih ve ayrıntılarıyla yazın; okul rehberlik servisiyle görüşün.":"Notez les faits, les dates et les détails, puis contactez le service d’accompagnement de l’établissement.", "Çocuğunuzun kendine zarar verme düşüncesi olabileceğinden endişeleniyorsanız 112'yi arayın.":"Si vous craignez que votre enfant envisage de se faire du mal, appelez le 112.", "Savunmaya geçmeden dinleyin; davranışın başkasına verdiği zararı konuşun.":"Écoutez sans vous mettre immédiatement sur la défensive et discutez du tort causé à autrui.", "Okul rehberlik servisiyle birlikte çalışın; cezadan çok davranış değişikliğini hedefleyin.":"Travaillez avec le service d’accompagnement scolaire et privilégiez le changement de comportement plutôt que la seule punition.", "Kaydı yalnızca insan olarak değerlendirin; otomatik sinyal kanıt veya karar değildir.":"Le signalement doit être évalué par une personne. Un indicateur automatique n’est ni une preuve ni une décision.", "Kaynağı belirlemeye çalışmayın; bildirimin anonimliğini koruyun.":"Ne cherchez pas à identifier la personne qui a signalé les faits ; préservez l’anonymat du signalement.", "Şüpheli öğrencinin yanlış suçlanma riskini gözetin; süreci rehberlik servisi ve okul yönetimiyle yürütün.":"Tenez compte du risque d’accuser injustement l’élève concerné et coordonnez la démarche avec le service d’accompagnement et la direction.", "Acil sinyal veya doğrudan zarar riski varsa okulun acil durum protokolünü uygulayın.":"En présence d’un signal urgent ou d’un risque de préjudice immédiat, appliquez le protocole d’urgence de l’établissement.",
},
"Español": {
"Zorbalık; bilerek yapılan, tekrar eden ve güç dengesizliği olan davranıştır (alay, tehdit, dışlama, fiziksel saldırı, internette aşağılama).":"El acoso es una conducta intencionada y repetida en la que existe un desequilibrio de poder (burlas, amenazas, exclusión, agresiones físicas o humillaciones en internet).", "Arkadaşlar arasındaki tek seferlik tartışma genellikle zorbalık sayılmaz; ama seni korkutuyor ya da üzüyorsa yine de anlatmaya değer.":"Una discusión aislada entre amigos normalmente no se considera acoso. Aun así, si te asusta o te hace sentir mal, merece la pena contarlo.", "Olanlar senin suçun değildir.":"Lo que ha ocurrido no es culpa tuya.", "Güvendiğin bir yetişkine (rehber öğretmen, sınıf öğretmeni, aile) olanı anlat.":"Cuéntaselo a una persona adulta de confianza, como el orientador, tu tutor o alguien de tu familia.", "Cevap vermek zorunda değilsin; güvenli bir yere git, yanında birileriyle ol.":"No tienes que responder. Ve a un lugar seguro y procura estar acompañado.", "Mesaj ve ekran görüntülerini sakla, silme; yetişkine gösterirsin.":"Guarda los mensajes y las capturas de pantalla; no los borres y enséñaselos a una persona adulta de confianza.", "Bu sitedeki anonim formu kullanabilirsin; ama form acil durum hattı değildir.":"Puedes utilizar el formulario anónimo de esta web, pero no es un servicio de emergencias.", "Bu düşünceleri tek başına taşımak zorunda değilsin. Hemen güvendiğin bir yetişkine söyle.":"No tienes que afrontar estos pensamientos a solas. Cuéntaselo ahora mismo a una persona adulta de confianza.", "Acil tehlikede 112'yi, destek için 183'ü arayabilirsin.":"Si hay peligro inmediato, llama al 112; para recibir apoyo, puedes llamar al 183.", "Zorbalığa gülmek ya da paylaşmak onu büyütür. Katılmamak bile bir destektir.":"Reírse del acoso o compartirlo lo agrava. No participar ya es una forma de apoyar.", "Güvenliysen mağdurun yanına git, yalnız olmadığını hissettir.":"Si es seguro hacerlo, acércate a la persona afectada y hazle saber que no está sola.", "Müdahale etmek tehlikeliyse bir yetişkine haber ver. Bu ‘çaksıl’ değil, arkadaşını korumaktır.":"Si intervenir puede ser peligroso, avisa a una persona adulta. No es chivarse: es proteger a alguien.", "Anonim form ile adını vermeden bildirebilirsin.":"Puedes comunicarlo mediante el formulario anónimo sin dar tu nombre.", "Cevap verme, kişiyi engelle, platformda şikâyet et.":"No respondas, bloquea a la persona y denúnciala en la plataforma.", "Kanıtları (ekran görüntüsü, tarih, hesap adı) sakla.":"Guarda las pruebas, como capturas de pantalla, fechas y nombre de la cuenta.", "Özel fotoğrafın izinsiz paylaşılıyorsa ya da paylaşılmakla tehdit ediliyorsan hemen bir yetişkine söyle; bu ciddi bir durumdur ve suç oluşturabilir.":"Si alguien comparte una foto privada tuya sin permiso o amenaza con hacerlo, díselo inmediatamente a una persona adulta. Es una situación grave y puede constituir un delito.", "Şifrelerini kimseyle paylaşma, gizlilik ayarlarını gözden geçir.":"No compartas tus contraseñas y revisa la configuración de privacidad.", "Sık görülen işaretler: okula gitmek istememe, uyku/iştah değişikliği, eşya kaybı, çekingenlik, telefona karşı aşırı tedirginlik. Bunlar tek başına kanıt değildir.":"Algunas señales posibles son: no querer ir al colegio, cambios en el sueño o el apetito, pérdida de objetos, aislamiento o nerviosismo intenso con el teléfono. Por sí solas, no son una prueba.", "Önce sakin kalın, dinleyin; suçlamayın, ‘sen de karşılık ver’ demeyin.":"Mantén la calma y escucha primero. No culpes al menor ni le digas que responda con la misma conducta.", "Olayı tarih ve ayrıntılarıyla yazın; okul rehberlik servisiyle görüşün.":"Anota lo ocurrido con fechas y detalles y ponte en contacto con el servicio de orientación del centro.", "Çocuğunuzun kendine zarar verme düşüncesi olabileceğinden endişeleniyorsanız 112'yi arayın.":"Si te preocupa que tu hijo pueda estar pensando en hacerse daño, llama al 112.", "Savunmaya geçmeden dinleyin; davranışın başkasına verdiği zararı konuşun.":"Escucha sin ponerte a la defensiva y habla del daño que esa conducta ha causado a otra persona.", "Okul rehberlik servisiyle birlikte çalışın; cezadan çok davranış değişikliğini hedefleyin.":"Colabora con el servicio de orientación del centro y céntrate en cambiar la conducta, no solo en castigar.", "Kaydı yalnızca insan olarak değerlendirin; otomatik sinyal kanıt veya karar değildir.":"El aviso debe ser evaluado por una persona. Una señal automática no es una prueba ni una decisión.", "Kaynağı belirlemeye çalışmayın; bildirimin anonimliğini koruyun.":"No intentes identificar quién envió el aviso; protege su anonimato.", "Şüpheli öğrencinin yanlış suçlanma riskini gözetin; süreci rehberlik servisi ve okul yönetimiyle yürütün.":"Ten en cuenta el riesgo de acusar injustamente al estudiante señalado y coordina el proceso con orientación y la dirección del centro.", "Acil sinyal veya doğrudan zarar riski varsa okulun acil durum protokolünü uygulayın.":"Si hay una señal urgente o riesgo de daño inmediato, aplica el protocolo de emergencia del centro.",
},
"العربية": {
"Zorbalık; bilerek yapılan, tekrar eden ve güç dengesizliği olan davranıştır (alay, tehdit, dışlama, fiziksel saldırı, internette aşağılama).":"التنمّر سلوك متعمّد ومتكرر ينطوي على اختلال في توازن القوة، مثل السخرية والتهديد والإقصاء والاعتداء الجسدي والإذلال عبر الإنترنت.", "Arkadaşlar arasındaki tek seferlik tartışma genellikle zorbalık sayılmaz; ama seni korkutuyor ya da üzüyorsa yine de anlatmaya değer.":"لا يُعدّ الخلاف الذي يحدث مرة واحدة بين الأصدقاء تنمّرًا في العادة، لكن إذا أخافك أو أزعجك فمن المهم التحدث عنه.", "Olanlar senin suçun değildir.":"ما حدث ليس خطأك.", "Güvendiğin bir yetişkine (rehber öğretmen, sınıf öğretmeni, aile) olanı anlat.":"أخبر شخصًا بالغًا تثق به، مثل المرشد المدرسي أو معلم الصف أو أحد أفراد أسرتك.", "Cevap vermek zorunda değilsin; güvenli bir yere git, yanında birileriyle ol.":"لست مضطرًا إلى الرد. اذهب إلى مكان آمن وابقَ مع أشخاص آخرين.", "Mesaj ve ekran görüntülerini sakla, silme; yetişkine gösterirsin.":"احتفظ بالرسائل ولقطات الشاشة ولا تحذفها، ثم اعرضها على شخص بالغ تثق به.", "Bu sitedeki anonim formu kullanabilirsin; ama form acil durum hattı değildir.":"يمكنك استخدام النموذج المجهول في هذا الموقع، لكنه ليس خدمة للطوارئ.", "Bu düşünceleri tek başına taşımak zorunda değilsin. Hemen güvendiğin bir yetişkine söyle.":"لست مضطرًا إلى مواجهة هذه الأفكار وحدك. أخبر فورًا شخصًا بالغًا تثق به.", "Acil tehlikede 112'yi, destek için 183'ü arayabilirsin.":"في حالة الخطر الفوري اتصل بالرقم 112، وللحصول على الدعم يمكنك الاتصال بالرقم 183.", "Zorbalığa gülmek ya da paylaşmak onu büyütür. Katılmamak bile bir destektir.":"الضحك على التنمّر أو نشره يزيده سوءًا. وعدم المشاركة فيه شكل من أشكال الدعم.", "Güvenliysen mağdurun yanına git, yalnız olmadığını hissettir.":"إذا كان ذلك آمنًا، اقترب من الشخص المتضرر وأشعره بأنه ليس وحده.", "Müdahale etmek tehlikeliyse bir yetişkine haber ver. Bu ‘çaksıl’ değil, arkadaşını korumaktır.":"إذا كان التدخل خطرًا، فأخبر شخصًا بالغًا. هذا ليس وشاية، بل حماية لشخص آخر.", "Anonim form ile adını vermeden bildirebilirsin.":"يمكنك الإبلاغ عبر النموذج المجهول دون ذكر اسمك.", "Cevap verme, kişiyi engelle, platformda şikâyet et.":"لا ترد، واحظر الشخص، وأبلغ عنه عبر المنصة.", "Kanıtları (ekran görüntüsü, tarih, hesap adı) sakla.":"احتفظ بالأدلة، مثل لقطات الشاشة والتواريخ وأسماء الحسابات.", "Özel fotoğrafın izinsiz paylaşılıyorsa ya da paylaşılmakla tehdit ediliyorsan hemen bir yetişkine söyle; bu ciddi bir durumdur ve suç oluşturabilir.":"إذا نُشرت صورة خاصة بك دون إذنك أو هُددت بنشرها، فأخبر شخصًا بالغًا فورًا. هذه مسألة خطيرة وقد تشكل جريمة.", "Şifrelerini kimseyle paylaşma, gizlilik ayarlarını gözden geçir.":"لا تشارك كلمات المرور مع أي شخص وراجع إعدادات الخصوصية.", "Sık görülen işaretler: okula gitmek istememe, uyku/iştah değişikliği, eşya kaybı, çekingenlik, telefona karşı aşırı tedirginlik. Bunlar tek başına kanıt değildir.":"من العلامات المحتملة: عدم الرغبة في الذهاب إلى المدرسة، تغير النوم أو الشهية، فقدان الأغراض، الانعزال أو القلق الشديد عند استخدام الهاتف. ولا تُعد هذه العلامات وحدها دليلًا قاطعًا.", "Önce sakin kalın, dinleyin; suçlamayın, ‘sen de karşılık ver’ demeyin.":"حافظوا على الهدوء واستمعوا أولًا. لا تلوموا الطفل ولا تطلبوا منه الرد بالمثل.", "Olayı tarih ve ayrıntılarıyla yazın; okul rehberlik servisiyle görüşün.":"دوّنوا ما حدث مع التواريخ والتفاصيل، وتواصلوا مع قسم الإرشاد المدرسي.", "Çocuğunuzun kendine zarar verme düşüncesi olabileceğinden endişeleniyorsanız 112'yi arayın.":"إذا كنتم قلقين من أن طفلكم يفكر في إيذاء نفسه، فاتصلوا بالرقم 112.", "Savunmaya geçmeden dinleyin; davranışın başkasına verdiği zararı konuşun.":"استمعوا دون اتخاذ موقف دفاعي، وتحدثوا عن الضرر الذي سببه السلوك للآخرين.", "Okul rehberlik servisiyle birlikte çalışın; cezadan çok davranış değişikliğini hedefleyin.":"تعاونوا مع قسم الإرشاد المدرسي، وركزوا على تغيير السلوك بدلًا من العقاب وحده.", "Kaydı yalnızca insan olarak değerlendirin; otomatik sinyal kanıt veya karar değildir.":"يجب أن يقيّم شخص مختص البلاغ. فالمؤشر الآلي ليس دليلًا ولا قرارًا.", "Kaynağı belirlemeye çalışmayın; bildirimin anonimliğini koruyun.":"لا تحاولوا تحديد هوية مُرسل البلاغ؛ حافظوا على سرية البلاغ.", "Şüpheli öğrencinin yanlış suçlanma riskini gözetin; süreci rehberlik servisi ve okul yönetimiyle yürütün.":"راعوا خطر اتهام الطالب المعني ظلمًا، ونسّقوا الإجراءات مع قسم الإرشاد وإدارة المدرسة.", "Acil sinyal veya doğrudan zarar riski varsa okulun acil durum protokolünü uygulayın.":"عند وجود مؤشر عاجل أو خطر مباشر، اتبعوا بروتوكول الطوارئ المعتمد في المدرسة.",
},
"Azərbaycan dili": {
"Zorbalık; bilerek yapılan, tekrar eden ve güç dengesizliği olan davranıştır (alay, tehdit, dışlama, fiziksel saldırı, internette aşağılama).":"Zorakılıq qəsdən edilən, təkrarlanan və güc balanssızlığı olan davranışdır (lağ etmək, hədələmək, kənarlaşdırmaq, fiziki hücum və internetdə alçaltmaq).", "Arkadaşlar arasındaki tek seferlik tartışma genellikle zorbalık sayılmaz; ama seni korkutuyor ya da üzüyorsa yine de anlatmaya değer.":"Dostlar arasında bir dəfə baş verən mübahisə adətən zorakılıq sayılmır. Lakin sizi qorxudursa və ya narahat edirsə, bu barədə danışmaq vacibdir.", "Olanlar senin suçun değildir.":"Baş verənlər sizin günahınız deyil.", "Güvendiğin bir yetişkine (rehber öğretmen, sınıf öğretmeni, aile) olanı anlat.":"Baş verənləri etibar etdiyiniz böyüyə, məsələn, məktəb psixoloquna, sinif rəhbərinə və ya ailə üzvünə danışın.", "Cevap vermek zorunda değilsin; güvenli bir yere git, yanında birileriyle ol.":"Cavab verməyə məcbur deyilsiniz. Təhlükəsiz yerə gedin və başqalarının yanında olun.", "Mesaj ve ekran görüntülerini sakla, silme; yetişkine gösterirsin.":"Mesajları və ekran görüntülərini silməyin, saxlayın və etibar etdiyiniz böyüyə göstərin.", "Bu sitedeki anonim formu kullanabilirsin; ama form acil durum hattı değildir.":"Bu saytdakı anonim formadan istifadə edə bilərsiniz, lakin bu forma təcili yardım xidməti deyil.", "Bu düşünceleri tek başına taşımak zorunda değilsin. Hemen güvendiğin bir yetişkine söyle.":"Bu düşüncələrlə təkbaşına qalmalı deyilsiniz. Dərhal etibar etdiyiniz böyüyə danışın.", "Acil tehlikede 112'yi, destek için 183'ü arayabilirsin.":"Təcili təhlükə zamanı 112-yə, dəstək üçün 183-ə zəng edə bilərsiniz.", "Zorbalığa gülmek ya da paylaşmak onu büyütür. Katılmamak bile bir destektir.":"Zorakılığa gülmək və ya onu paylaşmaq vəziyyəti ağırlaşdırır. İştirak etməmək belə dəstəkdir.", "Güvenliysen mağdurun yanına git, yalnız olmadığını hissettir.":"Təhlükəsizdirsə, zərər çəkən şəxsin yanına gedin və ona tək olmadığını hiss etdirin.", "Müdahale etmek tehlikeliyse bir yetişkine haber ver. Bu ‘çaksıl’ değil, arkadaşını korumaktır.":"Müdaxilə etmək təhlükəlidirsə, böyüyə xəbər verin. Bu, xəbərçilik deyil, dostunuzu qorumaqdır.", "Anonim form ile adını vermeden bildirebilirsin.":"Anonim forma vasitəsilə adınızı bildirmədən məlumat verə bilərsiniz.", "Cevap verme, kişiyi engelle, platformda şikâyet et.":"Cavab verməyin, həmin şəxsi bloklayın və platformada şikayət edin.", "Kanıtları (ekran görüntüsü, tarih, hesap adı) sakla.":"Sübutları, məsələn, ekran görüntülərini, tarixləri və hesab adını saxlayın.", "Özel fotoğrafın izinsiz paylaşılıyorsa ya da paylaşılmakla tehdit ediliyorsan hemen bir yetişkine söyle; bu ciddi bir durumdur ve suç oluşturabilir.":"Şəxsi şəkliniz icazəsiz paylaşılırsa və ya paylaşılacağı ilə hədələnirsinizsə, dərhal böyüyə xəbər verin. Bu ciddi haldır və cinayət ola bilər.", "Şifrelerini kimseyle paylaşma, gizlilik ayarlarını gözden geçir.":"Şifrələrinizi heç kimlə paylaşmayın və məxfilik parametrlərini yoxlayın.", "Sık görülen işaretler: okula gitmek istememe, uyku/iştah değişikliği, eşya kaybı, çekingenlik, telefona karşı aşırı tedirginlik. Bunlar tek başına kanıt değildir.":"Mümkün əlamətlərə məktəbə getmək istəməmək, yuxu və iştah dəyişiklikləri, əşyaların itməsi, özünə qapanma və telefona qarşı güclü narahatlıq daxildir. Bunlar təkbaşına sübut deyil.", "Önce sakin kalın, dinleyin; suçlamayın, ‘sen de karşılık ver’ demeyin.":"Əvvəlcə sakit qalın və dinləyin. Uşağı günahlandırmayın və ona qarşılıq verməyi məsləhət görməyin.", "Olayı tarih ve ayrıntılarıyla yazın; okul rehberlik servisiyle görüşün.":"Hadisəni tarix və təfərrüatlarla qeyd edin, məktəbin psixoloji dəstək xidməti ilə danışın.", "Çocuğunuzun kendine zarar verme düşüncesi olabileceğinden endişeleniyorsanız 112'yi arayın.":"Uşağınızın özünə zərər vermək barədə düşündüyündən narahatsınızsa, 112-yə zəng edin.", "Savunmaya geçmeden dinleyin; davranışın başkasına verdiği zararı konuşun.":"Özünüzü müdafiə etməyə tələsmədən dinləyin və davranışın başqasına vurduğu zərər barədə danışın.", "Okul rehberlik servisiyle birlikte çalışın; cezadan çok davranış değişikliğini hedefleyin.":"Məktəbin psixoloji dəstək xidməti ilə əməkdaşlıq edin; yalnız cəzaya deyil, davranışın dəyişməsinə fokuslanın.", "Kaydı yalnızca insan olarak değerlendirin; otomatik sinyal kanıt veya karar değildir.":"Müraciəti yalnız insan qiymətləndirməlidir. Avtomatik siqnal sübut və ya qərar deyil.", "Kaynağı belirlemeye çalışmayın; bildirimin anonimliğini koruyun.":"Məlumatı göndərən şəxsi müəyyən etməyə çalışmayın; müraciətin anonimliyini qoruyun.", "Şüpheli öğrencinin yanlış suçlanma riskini gözetin; süreci rehberlik servisi ve okul yönetimiyle yürütün.":"Şübhəli şagirdin haqsız yerə ittiham olunması riskini nəzərə alın və prosesi məktəbin psixoloji dəstək xidməti və rəhbərliyi ilə aparın.", "Acil sinyal veya doğrudan zarar riski varsa okulun acil durum protokolünü uygulayın.":"Təcili siqnal və ya birbaşa zərər riski varsa, məktəbin fövqəladə hal protokolunu tətbiq edin.",
},
}
for _language, _entries in _GUIDE_COPY.items():
    MULTI_CATALOG[_language].update(_entries)

# Final pass for short labels, headings, status messages and remaining page controls.
_FINAL_UI = {
"Deutsch": {
"Anonim":"Anonym", "Ad soyad:":"Vor- und Nachname:", "Belirgin eşleşme yok":"Keine eindeutige Übereinstimmung", "Bildirim türü":"Meldungsart", "Bildirimde belirtilen kişi bilgileri":"In der Meldung genannte Personenangaben", "Bu senaryoyu test ettim":"Ich habe dieses Szenario getestet", "CSV indir":"CSV herunterladen", "Destek rehberini aç":"Unterstützungsleitfaden öffnen", "Doğruluk":"Genauigkeit", "Durum dağılımı":"Statusverteilung", "Duyarlılık (recall)":"Sensitivität (Recall)", "Dışa aktarım":"Export", "Ek bilgi kaydedilemedi. Lütfen daha sonra tekrar dene.":"Zusätzliche Informationen konnten nicht gespeichert werden. Bitte versuche es später erneut.", "Eşleşen ifadeler:":"Übereinstimmende Ausdrücke:", "F1":"F1-Wert", "Genel kontrol listesidir; okul psikolojik danışmanı ve kurum protokolü tarafından uyarlanmalıdır.":"Dies ist eine allgemeine Checkliste und muss von der schulpsychologischen Beratung und gemäß den Schulrichtlinien angepasst werden.", "Güvenli Okul · Bildirim ve takip sistemi · Kural tabanlı sinyaller karar değildir.":"Güvenli Okul · Melde- und Nachverfolgungssystem · Regelbasierte Signale sind keine Entscheidungen.", "Henüz kayıt yok. Yeni bir bildirim oluşturulduğunda burada görünür.":"Noch keine Meldungen vorhanden. Neue Meldungen werden hier angezeigt.", "Henüz kayıt yok. Yeni kayıtlar eklendikçe istatistikler burada görüntülenir.":"Noch keine Meldungen vorhanden. Statistiken werden angezeigt, sobald neue Einträge hinzukommen.", "Kayıt seç":"Meldung auswählen", "Kesinlik (precision)":"Präzision", "Kimlik bilgilerini (ad, soyad, sınıf) dahil et":"Identitätsangaben (Vorname, Nachname, Klasse) einbeziehen", "Olay türü dağılımı":"Verteilung der Vorfallarten", "Planlanan tarih:":"Geplantes Datum:", "Rehberlik için önerilen adımlar":"Empfohlene Schritte der Beratungsstelle", "Saklama süresi":"Aufbewahrungsdauer", "Saklama süresi (gün)":"Aufbewahrungsdauer (Tage)", "Silmenin geri alınamayacağını anlıyorum":"Ich verstehe, dass die Löschung nicht rückgängig gemacht werden kann", "Sinyal:":"Signal:", "Son 30 gün: günlük bildirim":"Letzte 30 Tage: tägliche Meldungen", "Sonuçlanma süresi (medyan)":"Zeit bis zum Abschluss (Median)", "Süresi dolan kayıtları sil":"Abgelaufene Meldungen löschen", "Süresi dolan, sonuçlandırılmış kayıtlar notları ve geçmişiyle birlikte kalıcı olarak silinir.":"Abgelaufene, abgeschlossene Meldungen werden einschließlich Notizen und Verlauf dauerhaft gelöscht.", "Sınıf:":"Klasse:", "Takip kodu, olay türü, ortam veya birim":"Tracking-Code, Vorfallart, Umgebung oder zuständige Stelle", "Toplam bildirim":"Meldungen insgesamt", "Varsayılan olarak kapalıdır (veri minimizasyonu).":"Standardmäßig deaktiviert (Datenminimierung).", "Veri yok":"Keine Daten", "Yönetici girişine git":"Zur Administrator-Anmeldung", "Yüksek veya acil sinyal (açık)":"Hohe oder dringende Signale (offen)", "aktif yüksek/acil öncelikli kayıt var. Yetkili personel tarafından insan incelemesi gerekir.":"aktive Meldungen mit hoher/dringender Priorität. Eine menschliche Prüfung durch befugtes Personal ist erforderlich.", "ek bilgi":"Zusatzinformation", "saat bekliyor":"Stunden ausstehend", "Öncelik sinyali dağılımı":"Verteilung der Prioritätssignale", "İlk inceleme":"Erste Prüfung", "İlk işlem süresi (medyan)":"Zeit bis zur ersten Bearbeitung (Median)", "İncelemeyle ilgili kısa not ekleyin.":"Fügen Sie eine kurze Notiz zur Prüfung hinzu.", "İnsan incelemesi":"Menschliche Prüfung", "İşaretler yalnızca bu oturumda tutulur; resmi test raporu veya bilimsel doğrulama yerine geçmez.":"Markierungen bleiben nur in dieser Sitzung erhalten und ersetzen weder einen offiziellen Testbericht noch eine wissenschaftliche Validierung.",
"#### Bildirim ayrıntıları":"#### Meldungsdetails", "#### Ek bilgi ekle":"#### Zusätzliche Informationen hinzufügen", "#### Kayıt kuyruğu":"#### Meldungswarteschlange", "#### İnceleme notları":"#### Prüfnotizen", "#### İnceleme ve yönlendirme":"#### Prüfung und Weiterleitung", "#### İşlem geçmişi":"#### Aktivitätsverlauf", "**Açıklama**":"**Beschreibung**", "**Karışıklık matrisi**":"**Konfusionsmatrix**", "**Kategoriye göre yakalama (duyarlılık)**":"**Erkennung nach Kategorie (Sensitivität)**", "**Kaçırılan:**":"**Nicht erkannte Fälle:**", "**Tarih aralığı**":"**Datumsbereich**", "**Yanlış alarm:**":"**Falschmeldungen:**", "**Öncesi / sonrası gözlemsel karşılaştırma**":"**Beobachtender Vorher-Nachher-Vergleich**", "**Örnek türüne göre doğruluk**":"**Genauigkeit nach Beispieltyp**", "**İşlem geçmişi**":"**Aktivitätsverlauf**", "**Gizli takip kodun.** Durumu ve ek bilgi eklemeyi bu kodla yaparsın. Not al ya da ekran görüntüsü al; kod kaybolursa yeniden oluşturulamaz:":"**Dein vertraulicher Tracking-Code.** Mit diesem Code kannst du den Status prüfen und zusätzliche Informationen hinzufügen. Notiere ihn oder mache einen Screenshot. Bei Verlust kann er nicht wiederhergestellt werden:",
},
"Français": {
"Anonim":"Anonyme", "Ad soyad:":"Nom et prénom :", "Belirgin eşleşme yok":"Aucune correspondance notable", "Bildirim türü":"Type de signalement", "Bildirimde belirtilen kişi bilgileri":"Informations sur les personnes mentionnées dans le signalement", "Bu senaryoyu test ettim":"J’ai testé ce scénario", "CSV indir":"Télécharger le CSV", "Destek rehberini aç":"Ouvrir le guide d’accompagnement", "Doğruluk":"Exactitude", "Durum dağılımı":"Répartition des statuts", "Duyarlılık (recall)":"Rappel (sensibilité)", "Dışa aktarım":"Exportation", "Ek bilgi kaydedilemedi. Lütfen daha sonra tekrar dene.":"Impossible d’enregistrer les informations complémentaires. Veuillez réessayer plus tard.", "Eşleşen ifadeler:":"Expressions correspondantes :", "F1":"Score F1", "Genel kontrol listesidir; okul psikolojik danışmanı ve kurum protokolü tarafından uyarlanmalıdır.":"Il s’agit d’une liste de contrôle générale à adapter par le psychologue scolaire et selon le protocole de l’établissement.", "Güvenli Okul · Bildirim ve takip sistemi · Kural tabanlı sinyaller karar değildir.":"Güvenli Okul · Plateforme de signalement et de suivi · Les indicateurs fondés sur des règles ne sont pas des décisions.", "Henüz kayıt yok. Yeni bir bildirim oluşturulduğunda burada görünür.":"Aucun signalement pour le moment. Les nouveaux signalements apparaîtront ici.", "Henüz kayıt yok. Yeni kayıtlar eklendikçe istatistikler burada görüntülenir.":"Aucun signalement pour le moment. Les statistiques apparaîtront à mesure que de nouveaux dossiers seront ajoutés.", "Kayıt seç":"Sélectionner un dossier", "Kesinlik (precision)":"Précision", "Kimlik bilgilerini (ad, soyad, sınıf) dahil et":"Inclure les informations d’identité (nom, prénom, classe)", "Olay türü dağılımı":"Répartition par type d’incident", "Planlanan tarih:":"Date prévue :", "Rehberlik için önerilen adımlar":"Étapes recommandées par le service d’accompagnement", "Saklama süresi":"Durée de conservation", "Saklama süresi (gün)":"Durée de conservation (jours)", "Silmenin geri alınamayacağını anlıyorum":"Je comprends que la suppression est irréversible", "Sinyal:":"Indicateur :", "Son 30 gün: günlük bildirim":"30 derniers jours : signalements quotidiens", "Sonuçlanma süresi (medyan)":"Délai de clôture (médiane)", "Süresi dolan kayıtları sil":"Supprimer les dossiers arrivés à échéance", "Süresi dolan, sonuçlandırılmış kayıtlar notları ve geçmişiyle birlikte kalıcı olarak silinir.":"Les signalements clôturés arrivés à échéance sont supprimés définitivement, avec leurs notes et leur historique.", "Sınıf:":"Classe :", "Takip kodu, olay türü, ortam veya birim":"Code de suivi, type d’incident, environnement ou service", "Toplam bildirim":"Nombre total de signalements", "Varsayılan olarak kapalıdır (veri minimizasyonu).":"Désactivé par défaut (minimisation des données).", "Veri yok":"Aucune donnée", "Yönetici girişine git":"Accéder à la connexion administrateur", "Yüksek veya acil sinyal (açık)":"Indicateurs élevés ou urgents (ouverts)", "aktif yüksek/acil öncelikli kayıt var. Yetkili personel tarafından insan incelemesi gerekir.":"signalements actifs de priorité élevée ou urgente. Un examen humain par une personne autorisée est nécessaire.", "ek bilgi":"information complémentaire", "saat bekliyor":"heures en attente", "Öncelik sinyali dağılımı":"Répartition des indicateurs de priorité", "İlk inceleme":"Premier examen", "İlk işlem süresi (medyan)":"Délai avant la première action (médiane)", "İncelemeyle ilgili kısa not ekleyin.":"Ajoutez une brève note sur l’examen.", "İnsan incelemesi":"Examen humain", "İşaretler yalnızca bu oturumda tutulur; resmi test raporu veya bilimsel doğrulama yerine geçmez.":"Les coches sont conservées uniquement pendant cette session et ne remplacent ni un rapport de test officiel ni une validation scientifique.",
"#### Bildirim ayrıntıları":"#### Détails du signalement", "#### Ek bilgi ekle":"#### Ajouter des informations complémentaires", "#### Kayıt kuyruğu":"#### File des signalements", "#### İnceleme notları":"#### Notes d’examen", "#### İnceleme ve yönlendirme":"#### Examen et orientation", "#### İşlem geçmişi":"#### Historique des actions", "**Açıklama**":"**Description**", "**Karışıklık matrisi**":"**Matrice de confusion**", "**Kategoriye göre yakalama (duyarlılık)**":"**Détection par catégorie (sensibilité)**", "**Kaçırılan:**":"**Cas manqués :**", "**Tarih aralığı**":"**Période**", "**Yanlış alarm:**":"**Fausses alertes :**", "**Öncesi / sonrası gözlemsel karşılaştırma**":"**Comparaison observationnelle avant/après**", "**Örnek türüne göre doğruluk**":"**Exactitude par type d’exemple**", "**İşlem geçmişi**":"**Historique des actions**", "**Gizli takip kodun.** Durumu ve ek bilgi eklemeyi bu kodla yaparsın. Not al ya da ekran görüntüsü al; kod kaybolursa yeniden oluşturulamaz:":"**Votre code de suivi confidentiel.** Utilisez-le pour consulter le statut et ajouter des informations. Notez-le ou faites une capture d’écran ; il ne pourra pas être recréé en cas de perte :",
},
"Español": {
"Anonim":"Anónimo", "Ad soyad:":"Nombre y apellidos:", "Belirgin eşleşme yok":"No se han encontrado coincidencias claras", "Bildirim türü":"Tipo de aviso", "Bildirimde belirtilen kişi bilgileri":"Datos de personas mencionadas en el aviso", "Bu senaryoyu test ettim":"He probado este escenario", "CSV indir":"Descargar CSV", "Destek rehberini aç":"Abrir la guía de apoyo", "Doğruluk":"Exactitud", "Durum dağılımı":"Distribución de estados", "Duyarlılık (recall)":"Sensibilidad (recall)", "Dışa aktarım":"Exportación", "Ek bilgi kaydedilemedi. Lütfen daha sonra tekrar dene.":"No se ha podido guardar la información adicional. Inténtalo más tarde.", "Eşleşen ifadeler:":"Expresiones coincidentes:", "F1":"Puntuación F1", "Genel kontrol listesidir; okul psikolojik danışmanı ve kurum protokolü tarafından uyarlanmalıdır.":"Es una lista de comprobación general que debe adaptar el profesional de orientación escolar y ajustarse al protocolo del centro.", "Güvenli Okul · Bildirim ve takip sistemi · Kural tabanlı sinyaller karar değildir.":"Güvenli Okul · Plataforma de avisos y seguimiento · Las señales basadas en reglas no son decisiones.", "Henüz kayıt yok. Yeni bir bildirim oluşturulduğunda burada görünür.":"Todavía no hay avisos. Los nuevos avisos aparecerán aquí.", "Henüz kayıt yok. Yeni kayıtlar eklendikçe istatistikler burada görüntülenir.":"Todavía no hay avisos. Las estadísticas aparecerán a medida que se añadan nuevos registros.", "Kayıt seç":"Seleccionar registro", "Kesinlik (precision)":"Precisión", "Kimlik bilgilerini (ad, soyad, sınıf) dahil et":"Incluir datos de identidad (nombre, apellidos y curso)", "Olay türü dağılımı":"Distribución por tipo de incidente", "Planlanan tarih:":"Fecha prevista:", "Rehberlik için önerilen adımlar":"Pasos recomendados por orientación", "Saklama süresi":"Periodo de conservación", "Saklama süresi (gün)":"Periodo de conservación (días)", "Silmenin geri alınamayacağını anlıyorum":"Entiendo que la eliminación es irreversible", "Sinyal:":"Señal:", "Son 30 gün: günlük bildirim":"Últimos 30 días: avisos diarios", "Sonuçlanma süresi (medyan)":"Tiempo hasta el cierre (mediana)", "Süresi dolan kayıtları sil":"Eliminar registros caducados", "Süresi dolan, sonuçlandırılmış kayıtlar notları ve geçmişiyle birlikte kalıcı olarak silinir.":"Los avisos cerrados cuyo plazo haya vencido se eliminarán permanentemente, incluidas sus notas e historial.", "Sınıf:":"Curso:", "Takip kodu, olay türü, ortam veya birim":"Código de seguimiento, tipo de incidente, entorno o unidad", "Toplam bildirim":"Total de avisos", "Varsayılan olarak kapalıdır (veri minimizasyonu).":"Está desactivado de forma predeterminada (minimización de datos).", "Veri yok":"No hay datos", "Yönetici girişine git":"Ir al acceso de administración", "Yüksek veya acil sinyal (açık)":"Señales altas o urgentes (abiertas)", "aktif yüksek/acil öncelikli kayıt var. Yetkili personel tarafından insan incelemesi gerekir.":"avisos activos de prioridad alta o urgente. Es necesaria una revisión humana por parte de personal autorizado.", "ek bilgi":"información adicional", "saat bekliyor":"horas en espera", "Öncelik sinyali dağılımı":"Distribución de señales de prioridad", "İlk inceleme":"Primera revisión", "İlk işlem süresi (medyan)":"Tiempo hasta la primera actuación (mediana)", "İncelemeyle ilgili kısa not ekleyin.":"Añade una nota breve sobre la revisión.", "İnsan incelemesi":"Revisión humana", "İşaretler yalnızca bu oturumda tutulur; resmi test raporu veya bilimsel doğrulama yerine geçmez.":"Las marcas solo se conservan durante esta sesión y no sustituyen un informe de pruebas oficial ni una validación científica.",
"#### Bildirim ayrıntıları":"#### Detalles del aviso", "#### Ek bilgi ekle":"#### Añadir información adicional", "#### Kayıt kuyruğu":"#### Cola de avisos", "#### İnceleme notları":"#### Notas de revisión", "#### İnceleme ve yönlendirme":"#### Revisión y derivación", "#### İşlem geçmişi":"#### Historial de actividad", "**Açıklama**":"**Descripción**", "**Karışıklık matrisi**":"**Matriz de confusión**", "**Kategoriye göre yakalama (duyarlılık)**":"**Detección por categoría (sensibilidad)**", "**Kaçırılan:**":"**Casos no detectados:**", "**Tarih aralığı**":"**Intervalo de fechas**", "**Yanlış alarm:**":"**Falsas alarmas:**", "**Öncesi / sonrası gözlemsel karşılaştırma**":"**Comparación observacional antes/después**", "**Örnek türüne göre doğruluk**":"**Exactitud por tipo de ejemplo**", "**İşlem geçmişi**":"**Historial de actividad**", "**Gizli takip kodun.** Durumu ve ek bilgi eklemeyi bu kodla yaparsın. Not al ya da ekran görüntüsü al; kod kaybolursa yeniden oluşturulamaz:":"**Tu código privado de seguimiento.** Úsalo para consultar el estado y añadir información. Anótalo o haz una captura de pantalla; no se puede recuperar si se pierde:",
},
"العربية": {
"Anonim":"مجهول", "Ad soyad:":"الاسم الكامل:", "Belirgin eşleşme yok":"لا توجد مطابقات واضحة", "Bildirim türü":"نوع البلاغ", "Bildirimde belirtilen kişi bilgileri":"بيانات الأشخاص المذكورين في البلاغ", "Bu senaryoyu test ettim":"لقد اختبرت هذا السيناريو", "CSV indir":"تنزيل CSV", "Destek rehberini aç":"فتح دليل الدعم", "Doğruluk":"الدقة", "Durum dağılımı":"توزيع الحالات", "Duyarlılık (recall)":"الاسترجاع (الحساسية)", "Dışa aktarım":"تصدير", "Ek bilgi kaydedilemedi. Lütfen daha sonra tekrar dene.":"تعذّر حفظ المعلومات الإضافية. يُرجى المحاولة لاحقًا.", "Eşleşen ifadeler:":"العبارات المطابقة:", "F1":"مقياس F1", "Genel kontrol listesidir; okul psikolojik danışmanı ve kurum protokolü tarafından uyarlanmalıdır.":"هذه قائمة تحقق عامة ويجب أن يعدّلها المرشد النفسي المدرسي وفقًا لإجراءات المؤسسة.", "Güvenli Okul · Bildirim ve takip sistemi · Kural tabanlı sinyaller karar değildir.":"Güvenli Okul · منصة البلاغات والمتابعة · المؤشرات القائمة على القواعد ليست قرارات.", "Henüz kayıt yok. Yeni bir bildirim oluşturulduğunda burada görünür.":"لا توجد بلاغات بعد. ستظهر البلاغات الجديدة هنا.", "Henüz kayıt yok. Yeni kayıtlar eklendikçe istatistikler burada görüntülenir.":"لا توجد بلاغات بعد. ستظهر الإحصاءات عند إضافة سجلات جديدة.", "Kayıt seç":"اختيار بلاغ", "Kesinlik (precision)":"الإحكام (Precision)", "Kimlik bilgilerini (ad, soyad, sınıf) dahil et":"تضمين بيانات الهوية (الاسم واللقب والصف)", "Olay türü dağılımı":"توزيع أنواع الحوادث", "Planlanan tarih:":"التاريخ المخطط:", "Rehberlik için önerilen adımlar":"الخطوات المقترحة من قسم الإرشاد", "Saklama süresi":"مدة الاحتفاظ", "Saklama süresi (gün)":"مدة الاحتفاظ (بالأيام)", "Silmenin geri alınamayacağını anlıyorum":"أفهم أن الحذف لا يمكن التراجع عنه", "Sinyal:":"المؤشر:", "Son 30 gün: günlük bildirim":"آخر 30 يومًا: البلاغات اليومية", "Sonuçlanma süresi (medyan)":"المدة حتى الإغلاق (الوسيط)", "Süresi dolan kayıtları sil":"حذف البلاغات منتهية المدة", "Süresi dolan, sonuçlandırılmış kayıtlar notları ve geçmişiyle birlikte kalıcı olarak silinir.":"تُحذف البلاغات المغلقة التي انتهت مدة الاحتفاظ بها نهائيًا، بما في ذلك الملاحظات وسجل الإجراءات.", "Sınıf:":"الصف:", "Takip kodu, olay türü, ortam veya birim":"رمز المتابعة أو نوع الحادثة أو البيئة أو الجهة", "Toplam bildirim":"إجمالي البلاغات", "Varsayılan olarak kapalıdır (veri minimizasyonu).":"معطّل افتراضيًا (تقليل البيانات).", "Veri yok":"لا توجد بيانات", "Yönetici girişine git":"الانتقال إلى تسجيل دخول المسؤول", "Yüksek veya acil sinyal (açık)":"المؤشرات العالية أو العاجلة (المفتوحة)", "aktif yüksek/acil öncelikli kayıt var. Yetkili personel tarafından insan incelemesi gerekir.":"بلاغات نشطة ذات أولوية عالية أو عاجلة. يلزم أن يراجعها شخص مخوّل.", "ek bilgi":"معلومات إضافية", "saat bekliyor":"ساعة قيد الانتظار", "Öncelik sinyali dağılımı":"توزيع مؤشرات الأولوية", "İlk inceleme":"المراجعة الأولى", "İlk işlem süresi (medyan)":"المدة حتى أول إجراء (الوسيط)", "İncelemeyle ilgili kısa not ekleyin.":"أضف ملاحظة موجزة حول المراجعة.", "İnsan incelemesi":"مراجعة بشرية", "İşaretler yalnızca bu oturumda tutulur; resmi test raporu veya bilimsel doğrulama yerine geçmez.":"تُحفظ علامات الاختيار خلال هذه الجلسة فقط، ولا تحل محل تقرير اختبار رسمي أو تحقق علمي.",
"#### Bildirim ayrıntıları":"#### تفاصيل البلاغ", "#### Ek bilgi ekle":"#### إضافة معلومات أخرى", "#### Kayıt kuyruğu":"#### قائمة البلاغات", "#### İnceleme notları":"#### ملاحظات المراجعة", "#### İnceleme ve yönlendirme":"#### المراجعة والإحالة", "#### İşlem geçmişi":"#### سجل الإجراءات", "**Açıklama**":"**الوصف**", "**Karışıklık matrisi**":"**مصفوفة الالتباس**", "**Kategoriye göre yakalama (duyarlılık)**":"**الكشف حسب الفئة (الحساسية)**", "**Kaçırılan:**":"**الحالات التي لم تُكتشف:**", "**Tarih aralığı**":"**النطاق الزمني**", "**Yanlış alarm:**":"**الإنذارات الخاطئة:**", "**Öncesi / sonrası gözlemsel karşılaştırma**":"**مقارنة رصدية قبل الإجراء وبعده**", "**Örnek türüne göre doğruluk**":"**الدقة حسب نوع المثال**", "**İşlem geçmişi**":"**سجل الإجراءات**", "**Gizli takip kodun.** Durumu ve ek bilgi eklemeyi bu kodla yaparsın. Not al ya da ekran görüntüsü al; kod kaybolursa yeniden oluşturulamaz:":"**رمز المتابعة السري الخاص بك.** استخدمه للتحقق من الحالة وإضافة معلومات أخرى. دوّنه أو التقط له صورة للشاشة؛ لا يمكن استعادته إذا فُقد:",
},
"Azərbaycan dili": {
"Anonim":"Anonim", "Ad soyad:":"Ad və soyad:", "Belirgin eşleşme yok":"Aydın uyğunluq tapılmadı", "Bildirim türü":"Bildiriş növü", "Bildirimde belirtilen kişi bilgileri":"Bildirişdə qeyd olunan şəxslər haqqında məlumat", "Bu senaryoyu test ettim":"Bu ssenarini yoxladım", "CSV indir":"CSV-ni yüklə", "Destek rehberini aç":"Dəstək bələdçisini aç", "Doğruluk":"Dəqiqlik", "Durum dağılımı":"Status bölgüsü", "Duyarlılık (recall)":"Həssaslıq (recall)", "Dışa aktarım":"İxrac", "Ek bilgi kaydedilemedi. Lütfen daha sonra tekrar dene.":"Əlavə məlumatı yadda saxlamaq mümkün olmadı. Daha sonra yenidən cəhd edin.", "Eşleşen ifadeler:":"Uyğun gələn ifadələr:", "F1":"F1 göstəricisi", "Genel kontrol listesidir; okul psikolojik danışmanı ve kurum protokolü tarafından uyarlanmalıdır.":"Bu ümumi yoxlama siyahısıdır; məktəb psixoloqu və müəssisənin qaydalarına uyğunlaşdırılmalıdır.", "Güvenli Okul · Bildirim ve takip sistemi · Kural tabanlı sinyaller karar değildir.":"Güvenli Okul · Bildiriş və izləmə platforması · Qayda əsaslı siqnallar qərar deyil.", "Henüz kayıt yok. Yeni bir bildirim oluşturulduğunda burada görünür.":"Hələ müraciət yoxdur. Yeni bildirişlər burada görünəcək.", "Henüz kayıt yok. Yeni kayıtlar eklendikçe istatistikler burada görüntülenir.":"Hələ müraciət yoxdur. Yeni qeydlər əlavə olunduqca statistika burada görünəcək.", "Kayıt seç":"Müraciəti seçin", "Kesinlik (precision)":"Dəqiqlik (precision)", "Kimlik bilgilerini (ad, soyad, sınıf) dahil et":"Şəxsiyyət məlumatlarını (ad, soyad, sinif) daxil et", "Olay türü dağılımı":"Hadisə növlərinin bölgüsü", "Planlanan tarih:":"Planlaşdırılan tarix:", "Rehberlik için önerilen adımlar":"Psixoloji dəstək üçün tövsiyə olunan addımlar", "Saklama süresi":"Saxlanma müddəti", "Saklama süresi (gün)":"Saxlanma müddəti (gün)", "Silmenin geri alınamayacağını anlıyorum":"Silinmənin geri qaytarılmayacağını başa düşürəm", "Sinyal:":"Siqnal:", "Son 30 gün: günlük bildirim":"Son 30 gün: gündəlik bildirişlər", "Sonuçlanma süresi (medyan)":"Tamamlanma müddəti (median)", "Süresi dolan kayıtları sil":"Müddəti bitmiş müraciətləri sil", "Süresi dolan, sonuçlandırılmış kayıtlar notları ve geçmişiyle birlikte kalıcı olarak silinir.":"Müddəti bitmiş və tamamlanmış müraciətlər qeydləri və tarixçəsi ilə birlikdə həmişəlik silinir.", "Sınıf:":"Sinif:", "Takip kodu, olay türü, ortam veya birim":"İzləmə kodu, hadisə növü, mühit və ya bölmə", "Toplam bildirim":"Ümumi bildiriş sayı", "Varsayılan olarak kapalıdır (veri minimizasyonu).":"Standart olaraq deaktivdir (məlumatların minimumlaşdırılması).", "Veri yok":"Məlumat yoxdur", "Yönetici girişine git":"Administrator girişinə keç", "Yüksek veya acil sinyal (açık)":"Yüksək və ya təcili siqnallar (açıq)", "aktif yüksek/acil öncelikli kayıt var. Yetkili personel tarafından insan incelemesi gerekir.":"aktiv yüksək/təcili prioritetli müraciət var. Səlahiyyətli əməkdaş tərəfindən insan yoxlaması tələb olunur.", "ek bilgi":"əlavə məlumat", "saat bekliyor":"saatdır gözləyir", "Öncelik sinyali dağılımı":"Prioritet siqnallarının bölgüsü", "İlk inceleme":"İlk yoxlama", "İlk işlem süresi (medyan)":"İlk əməliyyata qədər müddət (median)", "İncelemeyle ilgili kısa not ekleyin.":"Yoxlama ilə bağlı qısa qeyd əlavə edin.", "İnsan incelemesi":"İnsan yoxlaması", "İşaretler yalnızca bu oturumda tutulur; resmi test raporu veya bilimsel doğrulama yerine geçmez.":"İşarələr yalnız bu sessiyada saxlanılır; rəsmi test hesabatını və ya elmi təsdiqi əvəz etmir.",
"#### Bildirim ayrıntıları":"#### Bildirişin təfərrüatları", "#### Ek bilgi ekle":"#### Əlavə məlumat əlavə et", "#### Kayıt kuyruğu":"#### Müraciət növbəsi", "#### İnceleme notları":"#### Yoxlama qeydləri", "#### İnceleme ve yönlendirme":"#### Yoxlama və yönləndirmə", "#### İşlem geçmişi":"#### Əməliyyat tarixçəsi", "**Açıklama**":"**Təsvir**", "**Karışıklık matrisi**":"**Qarışıqlıq matrisi**", "**Kategoriye göre yakalama (duyarlılık)**":"**Kateqoriyaya görə aşkarlama (həssaslıq)**", "**Kaçırılan:**":"**Aşkarlanmayanlar:**", "**Tarih aralığı**":"**Tarix aralığı**", "**Yanlış alarm:**":"**Yanlış siqnallar:**", "**Öncesi / sonrası gözlemsel karşılaştırma**":"**Əvvəl/sonra müşahidə müqayisəsi**", "**Örnek türüne göre doğruluk**":"**Nümunə növünə görə dəqiqlik**", "**İşlem geçmişi**":"**Əməliyyat tarixçəsi**", "**Gizli takip kodun.** Durumu ve ek bilgi eklemeyi bu kodla yaparsın. Not al ya da ekran görüntüsü al; kod kaybolursa yeniden oluşturulamaz:":"**Məxfi izləmə kodunuz.** Statusu yoxlamaq və əlavə məlumat daxil etmək üçün bu koddan istifadə edin. Onu qeyd edin və ya ekran görüntüsünü saxlayın; itirildikdə bərpa edilə bilməz:",
},
}
for _language, _entries in _FINAL_UI.items():
    MULTI_CATALOG[_language].update(_entries)

# Application-authored long-form help copy used on the Safe Use, Research and Privacy pages.
_DOC_EN = {
"Tam anonim bildirim alır (ad, sınıf, telefon istenmez; zaman dakika ve saniye hassasiyetinde kaydedilir); günde bir bildirim hakkı vardır.":"Accepts anonymous reports without requesting a name, class or phone number; timestamps are recorded to the second. One report may be submitted per day.",
"Açıklamadaki telefon, T.C. kimlik numarası, e-posta ve IBAN'ı otomatik maskeler.":"Automatically masks phone numbers, Turkish identity numbers, email addresses and IBANs in descriptions.",
"Takip koduyla durum sorgulamaya ve (anonim kayıtlarda, aynı gün) ek bilgi eklemeye izin verir.":"Allows users to check a report using its tracking code and, for anonymous reports, add information on the same day.",
"Yönetici girişinden sonra kayıtları listeler; durum/birim günceller; not ve işlem geçmişi tutar.":"After administrator sign-in, displays reports, allows status and team updates, and keeps notes and an activity history.",
"Girişleri ve yönetici işlemlerini denetim kaydında saklar; CSV dışa aktarım ve saklama süresi temizliği sunar.":"Keeps an audit log of sign-ins and administrator actions, supports CSV export and retention-based deletion.",
"İfade eşleşmelerini yalnızca insan incelemesi için öncelik sinyali olarak gösterir.":"Shows phrase matches only as prioritisation signals for human review.",
"Gerçek bir okul veya rehberlik servisine bağlı değildir; acil yardım ya da resmi bildirim hizmeti değildir.":"It is not connected to a real school or guidance service and is not an emergency or official reporting service.",
"Zorbalık hakkında otomatik kesin karar vermez; sinyaller yanlış alarm üretebilir ve olayları kaçırabilir.":"It does not make definitive automated decisions about bullying. Signals may produce false positives or miss incidents.",
"Tek yönetici hesabı kurumsal kimlik doğrulamanın (SSO/2FA) yerini tutmaz.":"A single administrator account is not a substitute for institutional authentication (SSO/2FA).",
"Yerel SQLite dosyasının bulut ortamında kalıcı olacağı garanti edilmez; yedekleme planı gerekir.":"Persistence of a local SQLite file in a cloud environment is not guaranteed; a backup plan is required.",
"Hatalı giriş ve zaman aşımı korumaları vardır, ancak bu bir güvenlik denetiminden geçmemiştir.":"Failed-login and session-timeout protections are present, but the system has not undergone a security audit.",
"Genel kontrol listesidir; okul psikolojik danışmanı ve kurum protokolü tarafından uyarlanmalıdır.":"This is a general checklist and must be adapted by the school counsellor and in accordance with institutional procedures.",
"Algılayıcının sentetik (elle yazılmış, gerçek veri içermeyen) örnek kümesindeki performansını ölçer. Aynı ölçüm komut satırından `python -m unittest discover -s testler` ile de çalışır.":"Measures the detector on a synthetic, manually written sample set that contains no real data. The same tests can also be run from the command line with `python -m unittest discover -s testler`.",
"Küme küçüktür, araştırmacılar tarafından yazılmıştır ve sözlük bu kümeye bakılarak iyileştirilmiştir; sonuçlar iyimserdir ve genellenemez. Bilimsel geçerlik için bağımsız, etik onaylı ve en az iki değerlendiricinin etiketlediği bir veri kümesi gerekir.":"The sample set is small, was written by the researchers, and was used to improve the phrase dictionary; results may therefore be optimistic and cannot be generalised. Scientific validity requires an independent, ethically approved dataset labelled by at least two evaluators.",
"- Formda ad, sınıf, telefon istenmez.\n- Açıklamadaki T.C. no, telefon, e-posta, IBAN maskelenir; ham metin saklanmaz.\n- Anonim kayıt ve ek bilgi zamanı dakika ve saniye hassasiyetinde kaydedilir.\n- Cihaz jetonu yalnızca özet olarak ve 1 gün saklanır; rapora bağlanmaz.\n- Öğrenci sorgusunda açıklama, not ve değerlendirme gösterilmez.":"- The form does not request a name, class or phone number.\n- Turkish identity numbers, phone numbers, email addresses and IBANs in descriptions are masked; the unmasked text is not stored.\n- The timestamps of anonymous reports and additional information are recorded to the second.\n- Only a hash of the device token is retained for one day and it is not linked to a report.\n- Report descriptions, notes and assessments are not shown in the student tracking view.",
"- Serbest metin kişileri dolaylı tanıtabilir; ‘tam anonim’ yerine ‘kimliksizleştirilmiş’ demek daha doğrudur.\n- Üçüncü kişilerin (şüpheli öğrenci) adı metinde geçebilir; maskeleme adları yakalamaz.\n- Barındırma yeri ve olası yurt dışı aktarım hukuken değerlendirilmelidir.":"- Free text may indirectly identify people; ‘de-identified’ is more accurate than ‘fully anonymous’.\n- A third party’s name (for example, a student mentioned in a report) may appear in the text; the masking feature does not detect names.\n- The hosting location and any possible international data transfers require legal review.",
"- Sonuçlanan kayıtlar: ‘Bildirim inceleme → Dışa aktarım ve saklama’ ekranından, seçilen gün sonunda notları ve ek bilgileriyle silinir (varsayılan 180).\n- Cihaz jetonu özeti: ertesi gün silinir.\n- Giriş denemeleri: 7 gün.\n- Denetim kaydı: saklama süresi tanımlı değil; karar verilmeli.":"- Closed reports are deleted with their notes and additional information after the selected retention period via ‘Report review → Export and retention’ (default: 180 days).\n- The device-token hash is deleted the following day.\n- Sign-in attempts are retained for 7 days.\n- The retention period for audit logs has not been defined and must be decided.",
"**Katılımcı bilgilendirmesi:** amaç, gönüllülük, toplanan veri (ad/telefon yok), saklama süresi, ayrılma hakkı ve rehberlik desteği.":"**Participant information:** purpose, voluntary participation, collected data (no name or phone number), retention period, right to withdraw and access to guidance support.",
"**Veli/yasal temsilci bilgilendirmesi ve izni.** Gerçek sistemde bu adım, okulun resmî iletişim kanalıyla ve yazılı olarak yürütülür; bu uygulama veli iletişim bilgisi toplamaz.":"**Information and consent for a parent/legal guardian.** In a real system, this step must be handled in writing through the school’s official communication channel; this application does not collect parent contact details.",
}
CATALOG.update(_DOC_EN)
_DOC_TRANSLATIONS = {
"Deutsch": {
"Tam anonim bildirim alır (ad, sınıf, telefon istenmez; zaman dakika ve saniye hassasiyetinde kaydedilir); günde bir bildirim hakkı vardır.":"Ermöglicht anonyme Meldungen ohne Name, Klasse oder Telefonnummer; Zeitstempel werden sekundengenau gespeichert. Pro Tag ist eine Meldung möglich.",
"Açıklamadaki telefon, T.C. kimlik numarası, e-posta ve IBAN'ı otomatik maskeler.":"Maskiert Telefonnummern, türkische Identitätsnummern, E-Mail-Adressen und IBANs in Beschreibungen automatisch.",
"Takip koduyla durum sorgulamaya ve (anonim kayıtlarda, aynı gün) ek bilgi eklemeye izin verir.":"Ermöglicht die Statusabfrage mit einem Tracking-Code und bei anonymen Meldungen das Hinzufügen weiterer Informationen am selben Tag.",
"Yönetici girişinden sonra kayıtları listeler; durum/birim günceller; not ve işlem geçmişi tutar.":"Nach der Administrator-Anmeldung werden Meldungen angezeigt; Status und zuständige Stelle können geändert werden. Notizen und ein Aktivitätsverlauf werden gespeichert.",
"Girişleri ve yönetici işlemlerini denetim kaydında saklar; CSV dışa aktarım ve saklama süresi temizliği sunar.":"Anmeldungen und Administratoraktionen werden protokolliert. CSV-Export und Löschung nach Ablauf der Aufbewahrungsfrist sind verfügbar.",
"İfade eşleşmelerini yalnızca insan incelemesi için öncelik sinyali olarak gösterir.":"Phrasenübereinstimmungen dienen ausschließlich als Prioritätssignale für die menschliche Prüfung.",
"Gerçek bir okul veya rehberlik servisine bağlı değildir; acil yardım ya da resmi bildirim hizmeti değildir.":"Das System ist weder mit einer realen Schule noch mit einer Beratungsstelle verbunden und ist kein Notfall- oder offizieller Meldedienst.",
"Zorbalık hakkında otomatik kesin karar vermez; sinyaller yanlış alarm üretebilir ve olayları kaçırabilir.":"Es trifft keine endgültigen automatischen Entscheidungen über Mobbing. Signale können Fehlalarme auslösen oder Vorfälle übersehen.",
"Tek yönetici hesabı kurumsal kimlik doğrulamanın (SSO/2FA) yerini tutmaz.":"Ein einzelnes Administratorkonto ersetzt keine institutionelle Authentifizierung (SSO/2FA).",
"Yerel SQLite dosyasının bulut ortamında kalıcı olacağı garanti edilmez; yedekleme planı gerekir.":"Die dauerhafte Speicherung einer lokalen SQLite-Datei in einer Cloud-Umgebung ist nicht garantiert; ein Sicherungsplan ist erforderlich.",
"Hatalı giriş ve zaman aşımı korumaları vardır, ancak bu bir güvenlik denetiminden geçmemiştir.":"Es gibt Schutzmaßnahmen gegen fehlgeschlagene Anmeldungen und Sitzungszeitüberschreitungen; ein Sicherheitsaudit wurde jedoch nicht durchgeführt.",
"Genel kontrol listesidir; okul psikolojik danışmanı ve kurum protokolü tarafından uyarlanmalıdır.":"Dies ist eine allgemeine Checkliste und muss von der schulpsychologischen Beratung sowie gemäß den institutionellen Verfahren angepasst werden.",
"Algılayıcının sentetik (elle yazılmış, gerçek veri içermeyen) örnek kümesindeki performansını ölçer. Aynı ölçüm komut satırından `python -m unittest discover -s testler` ile de çalışır.":"Misst die Leistung des Detektors anhand eines synthetischen, manuell erstellten Beispieldatensatzes ohne echte Daten. Dieselben Tests können auch über `python -m unittest discover -s testler` ausgeführt werden.",
"Küme küçüktür, araştırmacılar tarafından yazılmıştır ve sözlük bu kümeye bakılarak iyileştirilmiştir; sonuçlar iyimserdir ve genellenemez. Bilimsel geçerlik için bağımsız, etik onaylı ve en az iki değerlendiricinin etiketlediği bir veri kümesi gerekir.":"Der Datensatz ist klein, wurde von den Forschenden erstellt und zur Verbesserung des Wörterbuchs verwendet. Die Ergebnisse können daher zu optimistisch sein und sind nicht verallgemeinerbar. Wissenschaftliche Aussagekraft erfordert einen unabhängigen, ethisch genehmigten Datensatz, der von mindestens zwei Personen annotiert wurde.",
"**Katılımcı bilgilendirmesi:** amaç, gönüllülük, toplanan veri (ad/telefon yok), saklama süresi, ayrılma hakkı ve rehberlik desteği.":"**Informationen für Teilnehmende:** Zweck, Freiwilligkeit, erhobene Daten (kein Name/Telefon), Aufbewahrungsdauer, Widerrufsrecht und Beratungsunterstützung.",
"**Veli/yasal temsilci bilgilendirmesi ve izni.** Gerçek sistemde bu adım, okulun resmî iletişim kanalıyla ve yazılı olarak yürütülür; bu uygulama veli iletişim bilgisi toplamaz.":"**Information und Einwilligung der Eltern/gesetzlichen Vertretung.** In einem realen System muss dies schriftlich über die offiziellen Kommunikationswege der Schule erfolgen. Diese Anwendung erhebt keine Kontaktdaten der Eltern.",
},
"Français": {
"Tam anonim bildirim alır (ad, sınıf, telefon istenmez; zaman dakika ve saniye hassasiyetinde kaydedilir); günde bir bildirim hakkı vardır.":"Accepte des signalements anonymes sans demander de nom, de classe ou de numéro de téléphone ; les horodatages sont enregistrés à la seconde près. Un signalement par jour est autorisé.",
"Açıklamadaki telefon, T.C. kimlik numarası, e-posta ve IBAN'ı otomatik maskeler.":"Masque automatiquement les numéros de téléphone, numéros d’identité turcs, adresses e-mail et IBAN dans les descriptions.",
"Takip koduyla durum sorgulamaya ve (anonim kayıtlarda, aynı gün) ek bilgi eklemeye izin verir.":"Permet de consulter le statut avec un code de suivi et, pour les signalements anonymes, d’ajouter des informations le jour même.",
"Yönetici girişinden sonra kayıtları listeler; durum/birim günceller; not ve işlem geçmişi tutar.":"Après connexion de l’administrateur, les signalements sont affichés ; leur statut et leur service responsable peuvent être modifiés. Les notes et l’historique des actions sont conservés.",
"Girişleri ve yönetici işlemlerini denetim kaydında saklar; CSV dışa aktarım ve saklama süresi temizliği sunar.":"Les connexions et actions administratives sont consignées. L’export CSV et la suppression à l’expiration de la durée de conservation sont disponibles.",
"İfade eşleşmelerini yalnızca insan incelemesi için öncelik sinyali olarak gösterir.":"Les correspondances de termes servent uniquement d’indicateurs de priorité pour l’examen humain.",
"Gerçek bir okul veya rehberlik servisine bağlı değildir; acil yardım ya da resmi bildirim hizmeti değildir.":"La plateforme n’est reliée à aucun établissement ni service d’accompagnement réel ; elle ne constitue ni un service d’urgence ni un service officiel de signalement.",
"Zorbalık hakkında otomatik kesin karar vermez; sinyaller yanlış alarm üretebilir ve olayları kaçırabilir.":"Elle ne prend aucune décision définitive automatisée sur le harcèlement. Les indicateurs peuvent générer de fausses alertes ou ne pas détecter certains incidents.",
"Tek yönetici hesabı kurumsal kimlik doğrulamanın (SSO/2FA) yerini tutmaz.":"Un seul compte administrateur ne remplace pas une authentification institutionnelle (SSO/2FA).",
"Yerel SQLite dosyasının bulut ortamında kalıcı olacağı garanti edilmez; yedekleme planı gerekir.":"La persistance d’un fichier SQLite local dans un environnement cloud n’est pas garantie ; un plan de sauvegarde est nécessaire.",
"Hatalı giriş ve zaman aşımı korumaları vardır, ancak bu bir güvenlik denetiminden geçmemiştir.":"Des protections contre les échecs de connexion et l’expiration des sessions existent, mais le système n’a pas fait l’objet d’un audit de sécurité.",
"Genel kontrol listesidir; okul psikolojik danışmanı ve kurum protokolü tarafından uyarlanmalıdır.":"Cette liste de contrôle générale doit être adaptée par le psychologue scolaire et conformément au protocole de l’établissement.",
"Algılayıcının sentetik (elle yazılmış, gerçek veri içermeyen) örnek kümesindeki performansını ölçer. Aynı ölçüm komut satırından `python -m unittest discover -s testler` ile de çalışır.":"Mesure les performances du détecteur sur un ensemble synthétique rédigé manuellement, sans données réelles. Les mêmes tests peuvent également être exécutés avec `python -m unittest discover -s testler`.",
"Küme küçüktür, araştırmacılar tarafından yazılmıştır ve sözlük bu kümeye bakılarak iyileştirilmiştir; sonuçlar iyimserdir ve genellenemez. Bilimsel geçerlik için bağımsız, etik onaylı ve en az iki değerlendiricinin etiketlediği bir veri kümesi gerekir.":"L’ensemble est réduit, rédigé par les chercheurs et a servi à améliorer le dictionnaire ; les résultats peuvent donc être optimistes et ne sont pas généralisables. Une validation scientifique nécessite un jeu de données indépendant, approuvé sur le plan éthique et annoté par au moins deux évaluateurs.",
"**Katılımcı bilgilendirmesi:** amaç, gönüllülük, toplanan veri (ad/telefon yok), saklama süresi, ayrılma hakkı ve rehberlik desteği.":"**Information des participants :** objectif, participation volontaire, données collectées (sans nom ni téléphone), durée de conservation, droit de retrait et soutien du service d’accompagnement.",
"**Veli/yasal temsilci bilgilendirmesi ve izni.** Gerçek sistemde bu adım, okulun resmî iletişim kanalıyla ve yazılı olarak yürütülür; bu uygulama veli iletişim bilgisi toplamaz.":"**Information et accord du parent ou représentant légal.** Dans un système réel, cette étape doit être réalisée par écrit via les canaux officiels de l’établissement ; cette application ne collecte pas les coordonnées des parents.",
},
"Español": {
"Tam anonim bildirim alır (ad, sınıf, telefon istenmez; zaman dakika ve saniye hassasiyetinde kaydedilir); günde bir bildirim hakkı vardır.":"Acepta avisos anónimos sin solicitar nombre, curso ni teléfono; las marcas de tiempo se registran con precisión de segundos. Se permite un aviso al día.",
"Açıklamadaki telefon, T.C. kimlik numarası, e-posta ve IBAN'ı otomatik maskeler.":"Oculta automáticamente en las descripciones los teléfonos, números de identidad turcos, correos electrónicos e IBAN.",
"Takip koduyla durum sorgulamaya ve (anonim kayıtlarda, aynı gün) ek bilgi eklemeye izin verir.":"Permite consultar el estado con un código de seguimiento y añadir información el mismo día en los avisos anónimos.",
"Yönetici girişinden sonra kayıtları listeler; durum/birim günceller; not ve işlem geçmişi tutar.":"Tras iniciar sesión como administrador, muestra los avisos, permite actualizar su estado y unidad responsable, y conserva notas e historial de actividad.",
"Girişleri ve yönetici işlemlerini denetim kaydında saklar; CSV dışa aktarım ve saklama süresi temizliği sunar.":"Registra los accesos y las acciones administrativas, permite exportar a CSV y eliminar datos al vencer el periodo de conservación.",
"İfade eşleşmelerini yalnızca insan incelemesi için öncelik sinyali olarak gösterir.":"Muestra las coincidencias de expresiones únicamente como señales de prioridad para la revisión humana.",
"Gerçek bir okul veya rehberlik servisine bağlı değildir; acil yardım ya da resmi bildirim hizmeti değildir.":"No está conectado a un centro educativo ni a un servicio de orientación real; no es un servicio de emergencia ni de notificación oficial.",
"Zorbalık hakkında otomatik kesin karar vermez; sinyaller yanlış alarm üretebilir ve olayları kaçırabilir.":"No toma decisiones definitivas automatizadas sobre el acoso. Las señales pueden generar falsas alarmas o no detectar algunos incidentes.",
"Tek yönetici hesabı kurumsal kimlik doğrulamanın (SSO/2FA) yerini tutmaz.":"Una única cuenta de administración no sustituye la autenticación institucional (SSO/2FA).",
"Yerel SQLite dosyasının bulut ortamında kalıcı olacağı garanti edilmez; yedekleme planı gerekir.":"No se garantiza que un archivo SQLite local permanezca en un entorno en la nube; se necesita un plan de copias de seguridad.",
"Hatalı giriş ve zaman aşımı korumaları vardır, ancak bu bir güvenlik denetiminden geçmemiştir.":"Existen protecciones frente a intentos fallidos de acceso y caducidad de sesión, pero el sistema no ha pasado una auditoría de seguridad.",
"Genel kontrol listesidir; okul psikolojik danışmanı ve kurum protokolü tarafından uyarlanmalıdır.":"Es una lista de comprobación general que debe adaptar el profesional de orientación escolar conforme al protocolo del centro.",
"Algılayıcının sentetik (elle yazılmış, gerçek veri içermeyen) örnek kümesindeki performansını ölçer. Aynı ölçüm komut satırından `python -m unittest discover -s testler` ile de çalışır.":"Mide el rendimiento del detector con un conjunto sintético, redactado manualmente y sin datos reales. Las mismas pruebas también pueden ejecutarse desde la línea de comandos con `python -m unittest discover -s testler`.",
"Küme küçüktür, araştırmacılar tarafından yazılmıştır ve sözlük bu kümeye bakılarak iyileştirilmiştir; sonuçlar iyimserdir ve genellenemez. Bilimsel geçerlik için bağımsız, etik onaylı ve en az iki değerlendiricinin etiketlediği bir veri kümesi gerekir.":"El conjunto es pequeño, lo redactaron los investigadores y se utilizó para mejorar el diccionario; por ello, los resultados pueden ser optimistas y no son generalizables. La validez científica requiere un conjunto de datos independiente, aprobado éticamente y etiquetado por al menos dos evaluadores.",
"**Katılımcı bilgilendirmesi:** amaç, gönüllülük, toplanan veri (ad/telefon yok), saklama süresi, ayrılma hakkı ve rehberlik desteği.":"**Información para participantes:** finalidad, participación voluntaria, datos recogidos (sin nombre ni teléfono), periodo de conservación, derecho a retirarse y apoyo del servicio de orientación.",
"**Veli/yasal temsilci bilgilendirmesi ve izni.** Gerçek sistemde bu adım, okulun resmî iletişim kanalıyla ve yazılı olarak yürütülür; bu uygulama veli iletişim bilgisi toplamaz.":"**Información y autorización del padre, madre o representante legal.** En un sistema real, este paso debe realizarse por escrito a través de los canales oficiales del centro; esta aplicación no recoge datos de contacto familiares.",
},
"العربية": {
"Tam anonim bildirim alır (ad, sınıf, telefon istenmez; zaman dakika ve saniye hassasiyetinde kaydedilir); günde bir bildirim hakkı vardır.":"يستقبل بلاغات مجهولة دون طلب الاسم أو الصف أو رقم الهاتف؛ وتُسجّل الطوابع الزمنية بدقة الثواني. يُسمح ببلاغ واحد يوميًا.",
"Açıklamadaki telefon, T.C. kimlik numarası, e-posta ve IBAN'ı otomatik maskeler.":"يحجب تلقائيًا أرقام الهواتف وأرقام الهوية التركية وعناوين البريد الإلكتروني وأرقام IBAN الواردة في الأوصاف.",
"Takip koduyla durum sorgulamaya ve (anonim kayıtlarda, aynı gün) ek bilgi eklemeye izin verir.":"يتيح الاستعلام عن الحالة باستخدام رمز المتابعة وإضافة معلومات في اليوم نفسه للبلاغات المجهولة.",
"Yönetici girişinden sonra kayıtları listeler; durum/birim günceller; not ve işlem geçmişi tutar.":"بعد تسجيل دخول المسؤول، يعرض البلاغات ويتيح تحديث الحالة والجهة المسؤولة، مع الاحتفاظ بالملاحظات وسجل الإجراءات.",
"Girişleri ve yönetici işlemlerini denetim kaydında saklar; CSV dışa aktarım ve saklama süresi temizliği sunar.":"يحتفظ بسجل لتسجيلات الدخول وإجراءات المسؤول، ويوفر تصدير CSV والحذف عند انتهاء مدة الاحتفاظ.",
"İfade eşleşmelerini yalnızca insan incelemesi için öncelik sinyali olarak gösterir.":"يعرض تطابق العبارات كمؤشرات للأولوية من أجل المراجعة البشرية فقط.",
"Gerçek bir okul veya rehberlik servisine bağlı değildir; acil yardım ya da resmi bildirim hizmeti değildir.":"هذا النظام غير متصل بمدرسة فعلية أو قسم إرشاد، ولا يُعد خدمة طوارئ أو خدمة بلاغات رسمية.",
"Zorbalık hakkında otomatik kesin karar vermez; sinyaller yanlış alarm üretebilir ve olayları kaçırabilir.":"لا يتخذ قرارات آلية نهائية بشأن التنمّر؛ فقد تنتج المؤشرات إنذارات خاطئة أو لا تكتشف بعض الحوادث.",
"Tek yönetici hesabı kurumsal kimlik doğrulamanın (SSO/2FA) yerini tutmaz.":"لا يحل حساب مسؤول واحد محل نظام المصادقة المؤسسية (SSO/2FA).",
"Yerel SQLite dosyasının bulut ortamında kalıcı olacağı garanti edilmez; yedekleme planı gerekir.":"لا يوجد ضمان لاستمرار ملف SQLite المحلي في بيئة سحابية؛ لذلك يلزم وضع خطة نسخ احتياطي.",
"Hatalı giriş ve zaman aşımı korumaları vardır, ancak bu bir güvenlik denetiminden geçmemiştir.":"توجد وسائل حماية من محاولات الدخول الفاشلة وانتهاء الجلسة، لكن النظام لم يخضع لتدقيق أمني.",
"Genel kontrol listesidir; okul psikolojik danışmanı ve kurum protokolü tarafından uyarlanmalıdır.":"هذه قائمة تحقق عامة ويجب أن يعدّلها المرشد النفسي المدرسي وفق إجراءات المؤسسة.",
"Algılayıcının sentetik (elle yazılmış, gerçek veri içermeyen) örnek kümesindeki performansını ölçer. Aynı ölçüm komut satırından `python -m unittest discover -s testler` ile de çalışır.":"يقيس أداء الكاشف باستخدام مجموعة أمثلة اصطناعية مكتوبة يدويًا ولا تحتوي على بيانات حقيقية. ويمكن تشغيل الاختبارات نفسها من سطر الأوامر باستخدام `python -m unittest discover -s testler`.",
"Küme küçüktür, araştırmacılar tarafından yazılmıştır ve sözlük bu kümeye bakılarak iyileştirilmiştir; sonuçlar iyimserdir ve genellenemez. Bilimsel geçerlik için bağımsız, etik onaylı ve en az iki değerlendiricinin etiketlediği bir veri kümesi gerekir.":"مجموعة الأمثلة صغيرة وأعدّها الباحثون واستُخدمت لتحسين قاموس العبارات؛ لذلك قد تكون النتائج متفائلة ولا يمكن تعميمها. تتطلب الصلاحية العلمية مجموعة بيانات مستقلة ومعتمدة أخلاقيًا وموسومة بواسطة مقيّمين اثنين على الأقل.",
"**Katılımcı bilgilendirmesi:** amaç, gönüllülük, toplanan veri (ad/telefon yok), saklama süresi, ayrılma hakkı ve rehberlik desteği.":"**معلومات المشاركين:** الغرض، وطوعية المشاركة، والبيانات التي تُجمع (دون اسم أو هاتف)، ومدة الاحتفاظ، وحق الانسحاب، ودعم الإرشاد.",
"**Veli/yasal temsilci bilgilendirmesi ve izni.** Gerçek sistemde bu adım, okulun resmî iletişim kanalıyla ve yazılı olarak yürütülür؛ bu uygulama veli iletişim bilgisi toplamaz.":"**إبلاغ ولي الأمر أو الممثل القانوني والحصول على موافقته.** في النظام الفعلي، يجب تنفيذ هذه الخطوة كتابيًا عبر قنوات المدرسة الرسمية؛ ولا يجمع هذا التطبيق بيانات الاتصال بأولياء الأمور.",
},
"Azərbaycan dili": {
"Tam anonim bildirim alır (ad, sınıf, telefon istenmez; zaman dakika ve saniye hassasiyetinde kaydedilir); günde bir bildirim hakkı vardır.":"Ad, sinif və telefon nömrəsi tələb etmədən anonim müraciətlər qəbul edir; vaxt saniyə dəqiqliyi ilə qeydə alınır. Gündə bir müraciət göndərmək mümkündür.",
"Açıklamadaki telefon, T.C. kimlik numarası, e-posta ve IBAN'ı otomatik maskeler.":"Təsvirlərdəki telefon nömrələrini, Türkiyə şəxsiyyət nömrələrini, e-poçt ünvanlarını və IBAN-ları avtomatik maskalayır.",
"Takip koduyla durum sorgulamaya ve (anonim kayıtlarda, aynı gün) ek bilgi eklemeye izin verir.":"İzləmə kodu ilə statusu yoxlamağa və anonim müraciətlərə həmin gün əlavə məlumat daxil etməyə imkan verir.",
"Yönetici girişinden sonra kayıtları listeler; durum/birim günceller; not ve işlem geçmişi tutar.":"Administrator daxil olduqdan sonra müraciətləri siyahıya alır, statusu və məsul bölməni yeniləməyə imkan verir, qeydləri və əməliyyat tarixçəsini saxlayır.",
"Girişleri ve yönetici işlemlerini denetim kaydında saklar; CSV dışa aktarım ve saklama süresi temizliği sunar.":"Girişləri və administrator əməliyyatlarını audit jurnalında saxlayır, CSV ixracını və saxlama müddəti bitdikdə silinməni dəstəkləyir.",
"İfade eşleşmelerini yalnızca insan incelemesi için öncelik sinyali olarak gösterir.":"İfadə uyğunluqlarını yalnız insan yoxlaması üçün prioritet göstəricisi kimi təqdim edir.",
"Gerçek bir okul veya rehberlik servisine bağlı değildir; acil yardım ya da resmi bildirim hizmeti değildir.":"Real məktəbə və ya psixoloji dəstək xidmətinə qoşulmayıb; təcili yardım və ya rəsmi bildiriş xidməti deyil.",
"Zorbalık hakkında otomatik kesin karar vermez; sinyaller yanlış alarm üretebilir ve olayları kaçırabilir.":"Zorakılıq barədə avtomatik qəti qərar vermir. Siqnallar yanlış xəbərdarlıq yarada və bəzi hadisələri aşkarlamaya bilər.",
"Tek yönetici hesabı kurumsal kimlik doğrulamanın (SSO/2FA) yerini tutmaz.":"Tək administrator hesabı müəssisə səviyyəli autentifikasiyanı (SSO/2FA) əvəz etmir.",
"Yerel SQLite dosyasının bulut ortamında kalıcı olacağı garanti edilmez; yedekleme planı gerekir.":"Bulud mühitində yerli SQLite faylının daimi saxlanmasına zəmanət verilmir; ehtiyat nüsxə planı lazımdır.",
"Hatalı giriş ve zaman aşımı korumaları vardır, ancak bu bir güvenlik denetiminden geçmemiştir.":"Uğursuz giriş cəhdləri və sessiya vaxtı aşımı üçün qoruma mövcuddur, lakin sistem təhlükəsizlik auditindən keçməyib.",
"Genel kontrol listesidir; okul psikolojik danışmanı ve kurum protokolü tarafından uyarlanmalıdır.":"Bu ümumi yoxlama siyahısıdır; məktəb psixoloqu və müəssisənin qaydalarına uyğunlaşdırılmalıdır.",
"Algılayıcının sentetik (elle yazılmış, gerçek veri içermeyen) örnek kümesindeki performansını ölçer. Aynı ölçüm komut satırından `python -m unittest discover -s testler` ile de çalışır.":"Aşkarlayıcının real məlumat ehtiva etməyən, əl ilə hazırlanmış sintetik nümunələr üzərindəki performansını ölçür. Eyni testləri komanda sətrindən `python -m unittest discover -s testler` ilə də işlətmək olar.",
"Küme küçüktür, araştırmacılar tarafından yazılmıştır ve sözlük bu kümeye bakılarak iyileştirilmiştir; sonuçlar iyimserdir ve genellenemez. Bilimsel geçerlik için bağımsız, etik onaylı ve en az iki değerlendiricinin etiketlediği bir veri kümesi gerekir.":"Nümunə toplusu kiçikdir, tədqiqatçılar tərəfindən hazırlanıb və ifadələr lüğəti bu topluya əsasən təkmilləşdirilib; buna görə nəticələr nikbin ola və ümumiləşdirilə bilməz. Elmi etibarlılıq üçün müstəqil, etik təsdiqli və ən azı iki qiymətləndirici tərəfindən işarələnmiş məlumat toplusu lazımdır.",
"**Katılımcı bilgilendirmesi:** amaç, gönüllülük, toplanan veri (ad/telefon yok), saklama süresi, ayrılma hakkı ve rehberlik desteği.":"**İştirakçı məlumatlandırması:** məqsəd, könüllülük, toplanan məlumatlar (ad və telefon yoxdur), saxlanma müddəti, iştirakdan imtina hüququ və psixoloji dəstək.",
"**Veli/yasal temsilci bilgilendirmesi ve izni.** Gerçek sistemde bu adım, okulun resmî iletişim kanalıyla ve yazılı olarak yürütülür; bu uygulama veli iletişim bilgisi toplamaz.":"**Valideynin/qanuni nümayəndənin məlumatlandırılması və razılığı.** Real sistemdə bu addım məktəbin rəsmi əlaqə kanalı ilə yazılı aparılmalıdır; bu tətbiq valideynlərin əlaqə məlumatlarını toplamır.",
},
}
for _language, _entries in _DOC_TRANSLATIONS.items():
    MULTI_CATALOG[_language].update(_entries)

# Privacy inventory bullets and remaining research headings, localised phrase by phrase.
_PRIVACY_COPY = {
"Deutsch": {
"Formda ad, sınıf, telefon istenmez.":"Das Formular fragt weder Name noch Klasse oder Telefonnummer ab.",
"Açıklamadaki T.C. no, telefon, e-posta, IBAN maskelenir; ham metin saklanmaz.":"Identitätsnummern, Telefonnummern, E-Mail-Adressen und IBANs in Beschreibungen werden maskiert; der unmaskierte Text wird nicht gespeichert.",
"Anonim kayıt ve ek bilgi zamanı dakika ve saniye hassasiyetinde kaydedilir.":"Zeitangaben anonymer Meldungen und zusätzlicher Informationen werden sekundengenau gespeichert.",
"Cihaz jetonu yalnızca özet olarak ve 1 gün saklanır; rapora bağlanmaz.":"Der Geräte-Token wird nur als Hash gespeichert, nach einem Tag gelöscht und nicht mit einer Meldung verknüpft.",
"Öğrenci sorgusunda açıklama, not ve değerlendirme gösterilmez.":"In der Schüleransicht werden weder Beschreibungen noch Notizen oder Bewertungen angezeigt.",
"Serbest metin kişileri dolaylı tanıtabilir; ‘tam anonim’ yerine ‘kimliksizleştirilmiş’ demek daha doğrudur.":"Freitext kann Personen indirekt identifizierbar machen; daher ist „de-identifiziert“ genauer als „vollständig anonym“.",
"Üçüncü kişilerin (şüpheli öğrenci) adı metinde geçebilir; maskeleme adları yakalamaz.":"Im Text kann der Name einer dritten Person (z. B. eines beschuldigten Schülers) vorkommen; die Maskierung erkennt keine Namen.",
"Barındırma yeri ve olası yurt dışı aktarım hukuken değerlendirilmelidir.":"Der Hosting-Standort und mögliche Datenübermittlungen ins Ausland müssen rechtlich geprüft werden.",
"Cihaz jetonu özeti: ertesi gün silinir.":"Der Hash des Geräte-Tokens wird am folgenden Tag gelöscht.",
"Giriş denemeleri: 7 gün.":"Anmeldeversuche: 7 Tage.",
"Denetim kaydı: saklama süresi tanımlı değil; karar verilmeli.":"Audit-Protokoll: Die Aufbewahrungsdauer ist noch nicht festgelegt und muss beschlossen werden.",
"**Ortam haritası (ısı tablosu)**":"**Umgebungskarte (Heatmap)**",
"1. **Amaç:** Bildirim sürecinin anlaşılırlığını, temel işlevlerin doğruluğunu ve kural tabanlı sinyalin ölçülebilir başarımını raporlamak.":"1. **Ziel:** Verständlichkeit des Meldeprozesses, Korrektheit der Kernfunktionen und messbare Leistung der regelbasierten Signale bewerten.",
"2. **Algılayıcı:** Makine öğrenmesi içermez; Türkçe'ye duyarlı normalleştirme (İ/ı, ASCII katlama), kelime başı sınırı, harf tekrarı/ayraç/rakamla yazım çözümü ve kategori+ağırlık tabanlı öncelik kuralı kullanır.":"2. **Detektor:** Verwendet kein maschinelles Lernen. Er nutzt türkischsensitive Normalisierung, Wortgrenzen, Erkennung wiederholter Buchstaben und verschleierter Schreibweisen sowie eine kategorien- und gewichtungsbasierte Prioritätsregel.",
"3. **Ölçüt:** Kesinlik, duyarlılık, F1 ve kategori bazlı yakalama; ayrıca \"zor örnek\" kümesiyle bilinen sınırlılıklar.":"3. **Metriken:** Präzision, Sensitivität, F1 und Erkennung nach Kategorie; bekannte Grenzen werden zusätzlich anhand schwieriger Beispiele geprüft.",
"4. **Sınırlılıklar:** Bağlam, ironi, imâ ve ima yoluyla dışlama yakalanmaz; deyimsel abartı yanlış alarm üretir; yazım hataları kaçabilir; sözlük küçüktür.":"4. **Grenzen:** Kontext, Ironie und indirekte Ausgrenzung werden nicht zuverlässig erkannt. Übertreibungen können Fehlalarme auslösen, Tippfehler können übersehen werden und das Wörterbuch ist begrenzt.",
"5. **Yol haritası:** Etik izinli ve kimliksizleştirilmiş veri, en az iki değerlendirici, eğitim/doğrulama/test ayrımı, Vergleich mit einem Klassifikator und ein Usability-Test.":"5. **Weiterentwicklung:** Ethisch genehmigte, de-identifizierte Daten; mindestens zwei Bewertende; Trennung in Trainings-, Validierungs- und Testdaten; Vergleich mit einem Klassifikator und ein Usability-Test.",
"6. **Etik:** Gerçek öğrenci verisi için önceden okul/veli onayı, gönüllülük, veri minimizasyonu ve güvenli saklama planı gerekir. Bu uygulamada gerçek öğrenci verisi kullanmayın.":"6. **Ethik:** Für echte Schülerdaten sind vorab die Zustimmung der Schule und gegebenenfalls der Eltern, Freiwilligkeit, Datenminimierung und sichere Speicherung erforderlich. Verwenden Sie in dieser Anwendung keine echten Schülerdaten.",
},
"Français": {
"Formda ad, sınıf, telefon istenmez.":"Le formulaire ne demande ni nom, ni classe, ni numéro de téléphone.",
"Açıklamadaki T.C. no, telefon, e-posta, IBAN maskelenir; ham metin saklanmaz.":"Les numéros d’identité turcs, téléphones, e-mails et IBAN présents dans les descriptions sont masqués ; le texte non masqué n’est pas conservé.",
"Anonim kayıt ve ek bilgi zamanı dakika ve saniye hassasiyetinde kaydedilir.":"L’heure des signalements anonymes et des informations complémentaires est enregistrée à la seconde près.",
"Cihaz jetonu yalnızca özet olarak ve 1 gün saklanır; rapora bağlanmaz.":"Le jeton de l’appareil est conservé uniquement sous forme de hachage pendant un jour et n’est pas associé à un signalement.",
"Öğrenci sorgusunda açıklama, not ve değerlendirme gösterilmez.":"La vue de suivi destinée aux élèves n’affiche ni descriptions, ni notes, ni évaluations.",
"Serbest metin kişileri dolaylı tanıtabilir; ‘tam anonim’ yerine ‘kimliksizleştirilmiş’ demek daha doğrudur.":"Un texte libre peut permettre d’identifier indirectement une personne ; « désidentifié » est donc plus juste que « totalement anonyme ».",
"Üçüncü kişilerin (şüpheli öğrenci) adı metinde geçebilir; maskeleme adları yakalamaz.":"Le nom d’un tiers (par exemple, un élève mis en cause) peut apparaître dans le texte ; le masquage ne détecte pas les noms.",
"Barındırma yeri ve olası yurt dışı aktarım hukuken değerlendirilmelidir.":"Le lieu d’hébergement et tout éventuel transfert de données à l’étranger doivent faire l’objet d’une analyse juridique.",
"Cihaz jetonu özeti: ertesi gün silinir.":"Le hachage du jeton de l’appareil est supprimé le lendemain.", "Giriş denemeleri: 7 gün.":"Tentatives de connexion : 7 jours.", "Denetim kaydı: saklama süresi tanımlı değil; karar verilmeli.":"Journal d’audit : la durée de conservation n’est pas définie et doit être décidée.", "**Ortam haritası (ısı tablosu)**":"**Carte des environnements (carte thermique)**",
"1. **Amaç:** Bildirim sürecinin anlaşılırlığını, temel işlevlerin doğruluğunu ve kural tabanlı sinyalin ölçülebilir başarımını raporlamak.":"1. **Objectif :** évaluer la compréhension du processus de signalement, l’exactitude des fonctions essentielles et les performances mesurables des indicateurs fondés sur des règles.",
"2. **Algılayıcı:** Makine öğrenmesi içermez; Türkçe'ye duyarlı normalleştirme (İ/ı, ASCII katlama), kelime başı sınırı, harf tekrarı/ayraç/rakamla yazım çözümü ve kategori+ağırlık tabanlı öncelik kuralı kullanır.":"2. **Détecteur :** il n’utilise pas d’apprentissage automatique. Il applique une normalisation adaptée au turc, des limites de mots, la détection de répétitions et d’écritures masquées, ainsi qu’une règle de priorité fondée sur les catégories et leur pondération.",
"3. **Ölçüt:** Kesinlik, duyarlılık, F1 ve kategori bazlı yakalama; ayrıca \"zor örnek\" kümesiyle bilinen sınırlılıklar.":"3. **Mesures :** précision, rappel, score F1 et détection par catégorie ; les limites connues sont également évaluées sur des exemples difficiles.",
"4. **Sınırlılıklar:** Bağlam, ironi, imâ ve ima yoluyla dışlama yakalanmaz; deyimsel abartı yanlış alarm üretir; yazım hataları kaçabilir; sözlük küçüktür.":"4. **Limites :** le contexte, l’ironie et l’exclusion indirecte ne sont pas détectés de manière fiable. Les exagérations peuvent provoquer de fausses alertes, les fautes de frappe peuvent passer inaperçues et le dictionnaire reste limité.",
"5. **Yol haritası:** Etik izinli ve kimliksizleştirilmiş veri, en az iki değerlendirici, eğitim/doğrulama/test ayrımı, karşılaştırmalı sınıflandırıcı ve kullanılabilirlik testi.":"5. **Perspectives :** données désidentifiées et autorisées sur le plan éthique, au moins deux évaluateurs, séparation entraînement/validation/test, comparaison avec un classificateur et test d’utilisabilité.",
"6. **Etik:** Gerçek öğrenci verisi için önceden okul/veli onayı, gönüllülük, veri minimizasyonu ve güvenli saklama planı gerekir. Bu uygulamada gerçek öğrenci verisi kullanmayın.":"6. **Éthique :** l’utilisation de données réelles d’élèves exige l’accord préalable de l’établissement et, si nécessaire, des parents, une participation volontaire, la minimisation des données et un stockage sécurisé. N’utilisez pas de données réelles d’élèves dans cette application.",
},
"Español": {
"Formda ad, sınıf, telefon istenmez.":"El formulario no solicita nombre, curso ni número de teléfono.", "Açıklamadaki T.C. no, telefon, e-posta, IBAN maskelenir; ham metin saklanmaz.":"Se ocultan los números de identidad turcos, teléfonos, correos e IBAN incluidos en las descripciones; no se conserva el texto sin ocultar.", "Anonim kayıt ve ek bilgi zamanı dakika ve saniye hassasiyetinde kaydedilir.":"La hora de los avisos anónimos y de la información adicional se registra con precisión de segundos.", "Cihaz jetonu yalnızca özet olarak ve 1 gün saklanır; rapora bağlanmaz.":"El identificador del dispositivo se conserva únicamente como hash durante un día y no se vincula a ningún aviso.", "Öğrenci sorgusunda açıklama, not ve değerlendirme gösterilmez.":"La vista de consulta del alumnado no muestra descripciones, notas ni evaluaciones.", "Serbest metin kişileri dolaylı tanıtabilir; ‘tam anonim’ yerine ‘kimliksizleştirilmiş’ demek daha doğrudur.":"El texto libre puede permitir identificar indirectamente a una persona; por eso es más preciso decir «desidentificado» que «totalmente anónimo».", "Üçüncü kişilerin (şüpheli öğrenci) adı metinde geçebilir; maskeleme adları yakalamaz.":"El texto puede incluir el nombre de una tercera persona (por ejemplo, un estudiante señalado); el sistema de ocultación no detecta nombres.", "Barındırma yeri ve olası yurt dışı aktarım hukuken değerlendirilmelidir.":"La ubicación del alojamiento y cualquier posible transferencia internacional de datos deben revisarse jurídicamente.", "Cihaz jetonu özeti: ertesi gün silinir.":"El hash del identificador del dispositivo se elimina al día siguiente.", "Giriş denemeleri: 7 gün.":"Intentos de acceso: 7 días.", "Denetim kaydı: saklama süresi tanımlı değil; karar verilmeli.":"Registro de auditoría: el periodo de conservación aún no está definido y debe decidirse.", "**Ortam haritası (ısı tablosu)**":"**Mapa de entornos (mapa de calor)**",
"1. **Amaç:** Bildirim sürecinin anlaşılırlığını, temel işlevlerin doğruluğunu ve kural tabanlı sinyalin ölçülebilir başarımını raporlamak.":"1. **Objetivo:** evaluar la comprensión del proceso de aviso, la corrección de las funciones esenciales y el rendimiento medible de las señales basadas en reglas.",
"2. **Algılayıcı:** Makine öğrenmesi içermez; Türkçe'ye duyarlı normalleştirme (İ/ı, ASCII katlama), kelime başı sınırı, harf tekrarı/ayraç/rakamla yazım çözümü ve kategori+ağırlık tabanlı öncelik kuralı kullanır.":"2. **Detector:** no utiliza aprendizaje automático. Aplica normalización adaptada al turco, límites de palabra, detección de letras repetidas y escrituras ofuscadas, y una regla de prioridad basada en categorías y ponderaciones.",
"3. **Ölçüt:** Kesinlik, duyarlılık, F1 ve kategori bazlı yakalama; ayrıca \"zor örnek\" kümesiyle bilinen sınırlılıklar.":"3. **Métricas:** precisión, sensibilidad, F1 y detección por categoría; las limitaciones conocidas también se comprueban con ejemplos difíciles.",
"4. **Sınırlılıklar:** Bağlam, ironi, imâ ve ima yoluyla dışlama yakalanmaz; deyimsel abartı yanlış alarm üretir; yazım hataları kaçabilir; sözlük küçüktür.":"4. **Limitaciones:** el contexto, la ironía y la exclusión indirecta no se detectan de forma fiable. Las exageraciones pueden generar falsas alarmas, los errores tipográficos pueden pasar inadvertidos y el diccionario es limitado.",
"5. **Yol haritası:** Etik izinli ve kimliksizleştirilmiş veri, en az iki değerlendirici, eğitim/doğrulama/test ayrımı, karşılaştırmalı sınıflandırıcı ve kullanılabilirlik testi.":"5. **Próximos pasos:** datos desidentificados y aprobados éticamente, al menos dos evaluadores, separación de entrenamiento/validación/prueba, comparación con un clasificador y prueba de usabilidad.",
"6. **Etik:** Gerçek öğrenci verisi için önceden okul/veli onayı, gönüllülük, veri minimizasyonu ve güvenli saklama planı gerekir. Bu uygulamada gerçek öğrenci verisi kullanmayın.":"6. **Ética:** el uso de datos reales del alumnado requiere autorización previa del centro y, cuando corresponda, de las familias, participación voluntaria, minimización de datos y almacenamiento seguro. No utilices datos reales de estudiantes en esta aplicación.",
},
"العربية": {
"Formda ad, sınıf, telefon istenmez.":"لا يطلب النموذج الاسم أو الصف أو رقم الهاتف.", "Açıklamadaki T.C. no, telefon, e-posta, IBAN maskelenir; ham metin saklanmaz.":"تُحجب أرقام الهوية التركية وأرقام الهواتف والبريد الإلكتروني وأرقام IBAN الواردة في الأوصاف، ولا يُحتفظ بالنص غير المحجوب.", "Anonim kayıt ve ek bilgi zamanı dakika ve saniye hassasiyetinde kaydedilir.":"يُسجّل وقت البلاغات المجهولة والمعلومات الإضافية بدقة الثواني.", "Cihaz jetonu yalnızca özet olarak ve 1 gün saklanır; rapora bağlanmaz.":"يُحتفظ بمعرّف الجهاز في صورة قيمة مُجزّأة لمدة يوم واحد فقط، ولا يُربط بأي بلاغ.", "Öğrenci sorgusunda açıklama, not ve değerlendirme gösterilmez.":"لا تعرض صفحة استعلام الطالب الأوصاف أو الملاحظات أو التقييمات.", "Serbest metin kişileri dolaylı tanıtabilir; ‘tam anonim’ yerine ‘kimliksizleştirilmiş’ demek daha doğrudur.":"قد يكشف النص الحر عن هوية الأشخاص بصورة غير مباشرة؛ لذا فإن وصف البيانات بأنها «منزوعة الهوية» أدق من وصفها بأنها «مجهولة تمامًا».", "Üçüncü kişilerin (şüpheli öğrenci) adı metinde geçebilir; maskeleme adları yakalamaz.":"قد يظهر اسم طرف ثالث (مثل طالب ورد ذكره في البلاغ) في النص؛ ولا تستطيع آلية الإخفاء اكتشاف الأسماء.", "Barındırma yeri ve olası yurt dışı aktarım hukuken değerlendirilmelidir.":"يجب تقييم موقع الاستضافة وأي نقل محتمل للبيانات إلى خارج البلاد من الناحية القانونية.", "Cihaz jetonu özeti: ertesi gün silinir.":"يُحذف ملخص معرّف الجهاز في اليوم التالي.", "Giriş denemeleri: 7 gün.":"محاولات تسجيل الدخول: 7 أيام.", "Denetim kaydı: saklama süresi tanımlı değil; karar verilmeli.":"سجل التدقيق: لم تُحدّد مدة الاحتفاظ به بعد ويجب اتخاذ قرار بشأنها.", "**Ortam haritası (ısı tablosu)**":"**خريطة البيئات (خريطة حرارية)**",
"1. **Amaç:** Bildirim sürecinin anlaşılırlığını, temel işlevlerin doğruluğunu ve kural tabanlı sinyalin ölçülebilir başarımını raporlamak.":"1. **الهدف:** تقييم وضوح عملية الإبلاغ، وصحة الوظائف الأساسية، والأداء القابل للقياس للمؤشرات القائمة على القواعد.",
"2. **Algılayıcı:** Makine öğrenmesi içermez; Türkçe'ye duyarlı normalleştirme (İ/ı, ASCII katlama), kelime başı sınırı, harf tekrarı/ayraç/rakamla yazım çözümü ve kategori+ağırlık tabanlı öncelik kuralı kullanır.":"2. **الكاشف:** لا يستخدم التعلم الآلي. بل يعتمد على تطبيع يراعي اللغة التركية، وحدود الكلمات، واكتشاف تكرار الحروف والكتابة المموهة، وقاعدة أولوية تعتمد على الفئات والأوزان.",
"3. **Ölçüt:** Kesinlik, duyarlılık, F1 ve kategori bazlı yakalama; ayrıca \"zor örnek\" kümesiyle bilinen sınırlılıklar.":"3. **المقاييس:** الدقة والاسترجاع ومقياس F1 والكشف حسب الفئة؛ كما تُختبر القيود المعروفة باستخدام أمثلة صعبة.",
"4. **Sınırlılıklar:** Bağlam, ironi, imâ ve ima yoluyla dışlama yakalanmaz; deyimsel abartı yanlış alarm üretir; yazım hataları kaçabilir; sözlük küçüktür.":"4. **القيود:** لا يمكن اكتشاف السياق أو السخرية أو الإقصاء غير المباشر بشكل موثوق. وقد تؤدي المبالغة إلى إنذارات خاطئة، وقد لا تُكتشف الأخطاء الإملائية، كما أن القاموس محدود.",
"5. **Yol haritası:** Etik izinli ve kimliksizleştirilmiş veri, en az iki değerlendirici, eğitim/doğrulama/test ayrımı, karşılaştırmalı sınıflandırıcı ve kullanılabilirlik testi.":"5. **خطوات التطوير:** بيانات منزوعة الهوية ومعتمدة أخلاقيًا، ومقيّمان على الأقل، وتقسيم بيانات التدريب والتحقق والاختبار، ومقارنة مع مصنّف آخر، واختبار سهولة الاستخدام.",
"6. **Etik:** Gerçek öğrenci verisi için önceden okul/veli onayı, gönüllülük, veri minimizasyonu ve güvenli saklama planı gerekir. Bu uygulamada gerçek öğrenci verisi kullanmayın.":"6. **الأخلاقيات:** يتطلب استخدام بيانات الطلاب الحقيقية موافقة مسبقة من المدرسة وأولياء الأمور عند اللزوم، ومشاركة طوعية، وتقليل البيانات، وخطة تخزين آمنة. لا تستخدم بيانات طلاب حقيقية في هذا التطبيق.",
},
"Azərbaycan dili": {
"Formda ad, sınıf, telefon istenmez.":"Formada ad, sinif və telefon nömrəsi tələb olunmur.", "Açıklamadaki T.C. no, telefon, e-posta, IBAN maskelenir; ham metin saklanmaz.":"Təsvirlərdəki Türkiyə şəxsiyyət nömrələri, telefonlar, e-poçt ünvanları və IBAN-lar maskalanır; ilkin mətn saxlanılmır.", "Anonim kayıt ve ek bilgi zamanı dakika ve saniye hassasiyetinde kaydedilir.":"Anonim müraciətlərin və əlavə məlumatların vaxtı saniyə dəqiqliyi ilə qeydə alınır.", "Cihaz jetonu yalnızca özet olarak ve 1 gün saklanır; rapora bağlanmaz.":"Cihaz identifikatoru yalnız heşlənmiş formada bir gün saxlanılır və heç bir müraciətlə əlaqələndirilmir.", "Öğrenci sorgusunda açıklama, not ve değerlendirme gösterilmez.":"Şagirdin sorğu görünüşündə təsvirlər, qeydlər və qiymətləndirmələr göstərilmir.", "Serbest metin kişileri dolaylı tanıtabilir; ‘tam anonim’ yerine ‘kimliksizleştirilmiş’ demek daha doğrudur.":"Sərbəst mətn şəxsləri dolayı yolla tanıda bilər; buna görə ‘tam anonim’ əvəzinə ‘şəxsiyyətsizləşdirilmiş’ ifadəsi daha düzgündür.", "Üçüncü kişilerin (şüpheli öğrenci) adı metinde geçebilir; maskeleme adları yakalamaz.":"Mətndə üçüncü şəxsin (məsələn, adı çəkilən şagirdin) adı ola bilər; maskalama adları aşkarlamır.", "Barındırma yeri ve olası yurt dışı aktarım hukuken değerlendirilmelidir.":"Hostinqin yerləşdiyi yer və mümkün xarici məlumat ötürülməsi hüquqi baxımdan qiymətləndirilməlidir.", "Cihaz jetonu özeti: ertesi gün silinir.":"Cihaz identifikatorunun heşi növbəti gün silinir.", "Giriş denemeleri: 7 gün.":"Giriş cəhdləri: 7 gün.", "Denetim kaydı: saklama süresi tanımlı değil; karar verilmeli.":"Audit qeydi: saxlanma müddəti hələ müəyyən edilməyib və qərar verilməlidir.", "**Ortam haritası (ısı tablosu)**":"**Mühit xəritəsi (istilik cədvəli)**",
"1. **Amaç:** Bildirim sürecinin anlaşılırlığını, temel işlevlerin doğruluğunu ve kural tabanlı sinyalin ölçülebilir başarımını raporlamak.":"1. **Məqsəd:** Müraciət prosesinin anlaşıqlılığını, əsas funksiyaların düzgünlüyünü və qayda əsaslı siqnalların ölçülə bilən performansını qiymətləndirmək.",
"2. **Algılayıcı:** Makine öğrenmesi içermez; Türkçe'ye duyarlı normalleştirme (İ/ı, ASCII katlama), kelime başı sınırı, harf tekrarı/ayraç/rakamla yazım çözümü ve kategori+ağırlık tabanlı öncelik kuralı kullanır.":"2. **Aşkarlayıcı:** Maşın öyrənməsindən istifadə etmir. Türk dilinə uyğun normallaşdırma, söz sərhədləri, təkrarlanan hərflərin və gizlədilmiş yazılışların aşkarlanması, kateqoriya və çəki əsaslı prioritet qaydası tətbiq edir.",
"3. **Ölçüt:** Kesinlik, duyarlılık, F1 ve kategori bazlı yakalama; ayrıca \"zor örnek\" kümesiyle bilinen sınırlılıklar.":"3. **Ölçülər:** Dəqiqlik, həssaslıq, F1 və kateqoriya üzrə aşkarlama; məlum məhdudiyyətlər çətin nümunələrlə də yoxlanılır.",
"4. **Sınırlılıklar:** Bağlam, ironi, imâ ve ima yoluyla dışlama yakalanmaz; deyimsel abartı yanlış alarm üretir; yazım hataları kaçabilir; sözlük küçüktür.":"4. **Məhdudiyyətlər:** Kontekst, ironiya və dolayı kənarlaşdırma etibarlı şəkildə aşkarlanmır. Mübaliğə yanlış siqnal yarada, yazı səhvləri gözdən qaça bilər və lüğət məhduddur.",
"5. **Yol haritası:** Etik izinli ve kimliksizleştirilmiş veri, en az iki değerlendirici, eğitim/doğrulama/test ayrımı, karşılaştırmalı sınıflandırıcı ve kullanılabilirlik testi.":"5. **İnkişaf planı:** Etik təsdiqli və şəxsiyyətsizləşdirilmiş məlumatlar, ən azı iki qiymətləndirici, təlim/yoxlama/test bölgüsü, təsnifatçı ilə müqayisə və istifadə rahatlığı testi.",
"6. **Etik:** Gerçek öğrenci verisi için önceden okul/veli onayı, gönüllülük, veri minimizasyonu ve güvenli saklama planı gerekir. Bu uygulamada gerçek öğrenci verisi kullanmayın.":"6. **Etika:** Real şagird məlumatlarından istifadə üçün məktəbin və lazım olduqda valideynlərin əvvəlcədən razılığı, könüllülük, məlumatların minimumlaşdırılması və təhlükəsiz saxlanma planı tələb olunur. Bu tətbiqdə real şagird məlumatlarından istifadə etməyin.",
},
}
for _language, _entries in _PRIVACY_COPY.items():
    MULTI_CATALOG[_language].update(_entries)

# Last two review-quality warnings and the timing metric explanation.
_REVIEW_COPY = {
"Deutsch": {
"**Açıklama kalitesi kontrolü:** Metin temel uzunluk kontrolünü geçti. Bu, bildirimin doğru olduğu anlamına gelmez.":"**Prüfung der Beschreibungsqualität:** Der Text hat die grundlegende Längenprüfung bestanden. Das bedeutet nicht, dass die Meldung zutreffend ist.",
"**Açıklama kalitesi kontrolü:** Metin çok kısa, yeterince açıklayıcı olmayabilir veya tekrar eden karakterler içeriyor. Bu bir spam/asılsız bildirim kanıtı değildir; otomatik silinmez, yetkili kişi bağlamı kontrol etmelidir.":"**Prüfung der Beschreibungsqualität:** Der Text ist möglicherweise zu kurz, nicht aussagekräftig genug oder enthält wiederholte Zeichen. Das ist kein Beweis für Spam oder eine falsche Meldung. Er wird nicht automatisch gelöscht; eine befugte Person muss den Kontext prüfen.",
"Süreler kayıt oluşturma ile ilk durum değişikliği / 'Sonuçlandırıldı' arasındaki farktır. Yeni anonim kayıtlar dakika ve saniye hassasiyetinde kaydedilir; eski yuvarlanmış kayıtların geçmiş zamanı geriye dönük kesinleştirilemez.":"Die Zeitspannen messen den Abstand zwischen der Erstellung und der ersten Statusänderung bzw. dem Abschluss. Neue anonyme Meldungen werden sekundengenau gespeichert; der genaue Zeitpunkt älterer, gerundeter Einträge lässt sich nachträglich nicht rekonstruieren.",
},
"Français": {
"**Açıklama kalitesi kontrolü:** Metin temel uzunluk kontrolünü geçti. Bu, bildirimin doğru olduğu anlamına gelmez.":"**Contrôle de la qualité de la description :** le texte satisfait au contrôle de longueur de base. Cela ne signifie pas que le signalement est exact.",
"**Açıklama kalitesi kontrolü:** Metin çok kısa, yeterince açıklayıcı olmayabilir veya tekrar eden karakterler içeriyor. Bu bir spam/asılsız bildirim kanıtı değildir; otomatik silinmez, yetkili kişi bağlamı kontrol etmelidir.":"**Contrôle de la qualité de la description :** le texte est peut-être trop court, insuffisamment explicite ou contient des caractères répétés. Cela ne prouve pas qu’il s’agit de spam ou d’un faux signalement. Il n’est pas supprimé automatiquement ; une personne autorisée doit examiner le contexte.",
"Süreler kayıt oluşturma ile ilk durum değişikliği / 'Sonuçlandırıldı' arasındaki farktır. Yeni anonim kayıtlar dakika ve saniye hassasiyetinde kaydedilir; eski yuvarlanmış kayıtların geçmiş zamanı geriye dönük kesinleştirilemez.":"Les durées mesurent le temps entre la création du dossier et le premier changement de statut ou sa clôture. Les nouveaux signalements anonymes sont horodatés à la seconde près ; l’heure exacte des anciens dossiers arrondis ne peut pas être reconstituée rétroactivement.",
},
"Español": {
"**Açıklama kalitesi kontrolü:** Metin temel uzunluk kontrolünü geçti. Bu, bildirimin doğru olduğu anlamına gelmez.":"**Comprobación de la calidad de la descripción:** el texto ha superado la comprobación básica de longitud. Esto no significa que el aviso sea correcto.",
"**Açıklama kalitesi kontrolü:** Metin çok kısa, yeterince açıklayıcı olmayabilir veya tekrar eden karakterler içeriyor. Bu bir spam/asılsız bildirim kanıtı değildir; otomatik silinmez, yetkili kişi bağlamı kontrol etmelidir.":"**Comprobación de la calidad de la descripción:** el texto puede ser demasiado corto, poco claro o contener caracteres repetidos. Esto no demuestra que sea spam ni que el aviso sea falso. No se elimina automáticamente; una persona autorizada debe revisar el contexto.",
"Süreler kayıt oluşturma ile ilk durum değişikliği / 'Sonuçlandırıldı' arasındaki farktır. Yeni anonim kayıtlar dakika ve saniye hassasiyetinde kaydedilir; eski yuvarlanmış kayıtların geçmiş zamanı geriye dönük kesinleştirilemez.":"Los intervalos miden el tiempo entre la creación del registro y el primer cambio de estado o su cierre. Los nuevos avisos anónimos se registran con precisión de segundos; no es posible reconstruir retroactivamente la hora exacta de los registros antiguos redondeados.",
},
"العربية": {
"**Açıklama kalitesi kontrolü:** Metin temel uzunluk kontrolünü geçti. Bu, bildirimin doğru olduğu anlamına gelmez.":"**التحقق من جودة الوصف:** اجتاز النص فحص الطول الأساسي. ولا يعني ذلك أن البلاغ صحيح.",
"**Açıklama kalitesi kontrolü:** Metin çok kısa, yeterince açıklayıcı olmayabilir veya tekrar eden karakterler içeriyor. Bu bir spam/asılsız bildirim kanıtı değildir; otomatik silinmez, yetkili kişi bağlamı kontrol etmelidir.":"**التحقق من جودة الوصف:** قد يكون النص قصيرًا جدًا أو غير واضح بما يكفي أو يحتوي على أحرف متكررة. وهذا لا يثبت أنه بريد مزعج أو بلاغ كاذب. لن يُحذف تلقائيًا؛ بل يجب على شخص مخوّل مراجعة السياق.",
"Süreler kayıt oluşturma ile ilk durum değişikliği / 'Sonuçlandırıldı' arasındaki farktır. Yeni anonim kayıtlar dakika ve saniye hassasiyetinde kaydedilir; eski yuvarlanmış kayıtların geçmiş zamanı geriye dönük kesinleştirilemez.":"تقيس المدد الزمن بين إنشاء البلاغ وأول تغيير في حالته أو إغلاقه. تُسجّل البلاغات المجهولة الجديدة بدقة الثواني؛ ولا يمكن استعادة الوقت الدقيق للبلاغات القديمة التي قُرّبت أوقاتها بأثر رجعي.",
},
"Azərbaycan dili": {
"**Açıklama kalitesi kontrolü:** Metin temel uzunluk kontrolünü geçti. Bu, bildirimin doğru olduğu anlamına gelmez.":"**Təsvirin keyfiyyətinin yoxlanması:** Mətn əsas uzunluq yoxlamasından keçib. Bu, müraciətin doğru olduğu demək deyil.",
"**Açıklama kalitesi kontrolü:** Metin çok kısa, yeterince açıklayıcı olmayabilir veya tekrar eden karakterler içeriyor. Bu bir spam/asılsız bildirim kanıtı değildir; otomatik silinmez, yetkili kişi bağlamı kontrol etmelidir.":"**Təsvirin keyfiyyətinin yoxlanması:** Mətn çox qısa, kifayət qədər aydın olmayan və ya təkrarlanan simvollardan ibarət ola bilər. Bu, spam və ya əsassız müraciət sübutu deyil. Avtomatik silinmir; səlahiyyətli şəxs konteksti yoxlamalıdır.",
"Süreler kayıt oluşturma ile ilk durum değişikliği / 'Sonuçlandırıldı' arasındaki farktır. Yeni anonim kayıtlar dakika ve saniye hassasiyetinde kaydedilir; eski yuvarlanmış kayıtların geçmiş zamanı geriye dönük kesinleştirilemez.":"Müddətlər qeydin yaradılması ilə ilk status dəyişikliyi və ya tamamlanması arasındakı vaxtı göstərir. Yeni anonim müraciətlər saniyə dəqiqliyi ilə qeydə alınır; köhnə yuvarlaqlaşdırılmış qeydlərin dəqiq vaxtını sonradan bərpa etmək mümkün deyil.",
},
}
for _language, _entries in _REVIEW_COPY.items():
    MULTI_CATALOG[_language].update(_entries)

# Localised privacy-notice wording (including its legal placeholders).
_NOTICE_COPY = {
"Deutsch": {
"**Veri sorumlusu:**":"**Verantwortlicher:**", "**İletişim:**":"**Kontakt:**", "**İşlenen veriler:**":"**Verarbeitete Daten:**", "**Amaç:**":"**Zweck:**", "**Hukuki sebep:**":"**Rechtsgrundlage:**", "**Aktarım:**":"**Datenübermittlung:**", "**Saklama ve imha:**":"**Aufbewahrung und Löschung:**", "**Haklarınız:**":"**Ihre Rechte:**",
"Bildirim formunda yazdığınız olay bilgisi (tür, ortam, zaman, açıklama). Ad, soyad, sınıf, telefon istenmez.":"Die im Meldeformular eingegebenen Vorfallangaben (Art, Umgebung, Zeitpunkt und Beschreibung). Name, Nachname, Klasse und Telefonnummer werden nicht abgefragt.",
"Otomatik sinyal yalnızca inceleme sırasına yardımcıdır; hiçbir karar otomatik verilmez.":"Automatische Signale helfen nur bei der Priorisierung der Prüfung; es werden keine Entscheidungen automatisiert getroffen.",
"[HUKUK DANIŞMANI BELİRLEYECEK: ör. KVKK m.5/2 ilgili bendi / açık rıza / veli onamı]":"[VON DER RECHTSBERATUNG FESTZULEGEN: z. B. einschlägige Bestimmung aus Art. 5 Abs. 2 KVKK / ausdrückliche Einwilligung / Zustimmung der Eltern]",
"Veriler yetkili okul personeli dışında paylaşılmaz.":"Die Daten werden nicht an Personen außerhalb des befugten Schulpersonals weitergegeben.",
"[BARINDIRMA YERİ VE YURT DIŞI AKTARIM DURUMU YAZILACAK]":"[HOSTING-STANDORT UND MÖGLICHE DATENÜBERMITTLUNG INS AUSLAND ANGEBEN]",
"KVKK m.11 kapsamındaki haklar için yukarıdaki adrese başvurabilirsiniz.":"Zur Ausübung Ihrer Rechte nach Artikel 11 des türkischen Datenschutzgesetzes (KVKK) können Sie sich an die oben genannte Adresse wenden.",
"Anonim bildirimlerde bildirimi size bağlamak mümkün olmadığından bazı haklar (erişim, düzeltme) teknik olarak kullanılamayabilir.":"Bei anonymen Meldungen ist eine Zuordnung zu Ihrer Person möglicherweise technisch nicht möglich; daher können bestimmte Rechte (z. B. Auskunft und Berichtigung) eventuell nicht ausgeübt werden.",
"[OKUL ADI / KURUM]":"[NAME DER SCHULE / EINRICHTUNG]", "[KVKK İLETİŞİM ADRESİ]":"[KONTAKTADRESSE FÜR DATENSCHUTZ]",
},
"Français": {
"**Veri sorumlusu:**":"**Responsable du traitement :**", "**İletişim:**":"**Contact :**", "**İşlenen veriler:**":"**Données traitées :**", "**Amaç:**":"**Finalité :**", "**Hukuki sebep:**":"**Base juridique :**", "**Aktarım:**":"**Transferts de données :**", "**Saklama ve imha:**":"**Conservation et suppression :**", "**Haklarınız:**":"**Vos droits :**",
"Bildirim formunda yazdığınız olay bilgisi (tür, ortam, zaman, açıklama). Ad, soyad, sınıf, telefon istenmez.":"Les informations sur l’incident saisies dans le formulaire (type, environnement, moment et description). Le nom, le prénom, la classe et le numéro de téléphone ne sont pas demandés.",
"Otomatik sinyal yalnızca inceleme sırasına yardımcıdır; hiçbir karar otomatik verilmez.":"Les indicateurs automatiques servent uniquement à prioriser les examens ; aucune décision n’est prise automatiquement.",
"[HUKUK DANIŞMANI BELİRLEYECEK: ör. KVKK m.5/2 ilgili bendi / açık rıza / veli onamı]":"[À DÉTERMINER PAR LE CONSEIL JURIDIQUE : par exemple, disposition applicable de l’article 5(2) de la KVKK / consentement explicite / accord parental]",
"Veriler yetkili okul personeli dışında paylaşılmaz.":"Les données ne sont pas communiquées en dehors du personnel autorisé de l’établissement.",
"[BARINDIRMA YERİ VE YURT DIŞI AKTARIM DURUMU YAZILACAK]":"[PRÉCISER LE LIEU D’HÉBERGEMENT ET LES ÉVENTUELS TRANSFERTS À L’ÉTRANGER]",
"KVKK m.11 kapsamındaki haklar için yukarıdaki adrese başvurabilirsiniz.":"Vous pouvez contacter l’adresse ci-dessus pour exercer vos droits prévus à l’article 11 de la loi turque sur la protection des données personnelles (KVKK).",
"Anonim bildirimlerde bildirimi size bağlamak mümkün olmadığından bazı haklar (erişim, düzeltme) teknik olarak kullanılamayabilir.":"Pour les signalements anonymes, il peut être techniquement impossible de relier le signalement à votre identité ; certains droits (accès, rectification) peuvent donc ne pas être applicables.",
"[OKUL ADI / KURUM]":"[NOM DE L’ÉTABLISSEMENT / ORGANISME]", "[KVKK İLETİŞİM ADRESİ]":"[ADRES DE CONTACT POUR LA PROTECTION DES DONNÉES]",
},
"Español": {
"**Veri sorumlusu:**":"**Responsable del tratamiento:**", "**İletişim:**":"**Contacto:**", "**İşlenen veriler:**":"**Datos tratados:**", "**Amaç:**":"**Finalidad:**", "**Hukuki sebep:**":"**Base jurídica:**", "**Aktarım:**":"**Transferencias de datos:**", "**Saklama ve imha:**":"**Conservación y eliminación:**", "**Haklarınız:**":"**Tus derechos:**",
"Bildirim formunda yazdığınız olay bilgisi (tür, ortam, zaman, açıklama). Ad, soyad, sınıf, telefon istenmez.":"La información del incidente introducida en el formulario (tipo, entorno, momento y descripción). No se solicitan nombre, apellidos, curso ni teléfono.",
"Otomatik sinyal yalnızca inceleme sırasına yardımcıdır; hiçbir karar otomatik verilmez.":"Las señales automáticas solo ayudan a priorizar la revisión; no se toma ninguna decisión de forma automática.",
"[HUKUK DANIŞMANI BELİRLEYECEK: ör. KVKK m.5/2 ilgili bendi / açık rıza / veli onamı]":"[A DETERMINAR POR ASESORÍA JURÍDICA: por ejemplo, disposición aplicable del artículo 5(2) de la KVKK / consentimiento explícito / autorización familiar]",
"Veriler yetkili okul personeli dışında paylaşılmaz.":"Los datos no se comparten con personas ajenas al personal autorizado del centro.",
"[BARINDIRMA YERİ VE YURT DIŞI AKTARIM DURUMU YAZILACAK]":"[INDICAR LA UBICACIÓN DEL ALOJAMIENTO Y LOS POSIBLES ENVÍOS DE DATOS AL EXTRANJERO]",
"KVKK m.11 kapsamındaki haklar için yukarıdaki adrese başvurabilirsiniz.":"Puedes dirigirte a la dirección anterior para ejercer los derechos contemplados en el artículo 11 de la ley turca de protección de datos personales (KVKK).",
"Anonim bildirimlerde bildirimi size bağlamak mümkün olmadığından bazı haklar (erişim, düzeltme) teknik olarak kullanılamayabilir.":"En los avisos anónimos puede ser técnicamente imposible vincular el aviso contigo, por lo que quizá no puedan ejercerse algunos derechos, como el acceso o la rectificación.",
"[OKUL ADI / KURUM]":"[NOMBRE DEL CENTRO / INSTITUCIÓN]", "[KVKK İLETİŞİM ADRESİ]":"[DIRECCIÓN DE CONTACTO DE PROTECCIÓN DE DATOS]",
},
"العربية": {
"**Veri sorumlusu:**":"**مسؤول معالجة البيانات:**", "**İletişim:**":"**معلومات الاتصال:**", "**İşlenen veriler:**":"**البيانات التي تتم معالجتها:**", "**Amaç:**":"**الغرض:**", "**Hukuki sebep:**":"**الأساس القانوني:**", "**Aktarım:**":"**نقل البيانات:**", "**Saklama ve imha:**":"**الاحتفاظ بالبيانات وحذفها:**", "**Haklarınız:**":"**حقوقك:**",
"Bildirim formunda yazdığınız olay bilgisi (tür, ortam, zaman, açıklama). Ad, soyad, sınıf, telefon istenmez.":"معلومات الحادثة التي تدخلها في نموذج البلاغ (النوع والبيئة والوقت والوصف). لا يُطلب الاسم أو اللقب أو الصف أو رقم الهاتف.",
"Otomatik sinyal yalnızca inceleme sırasına yardımcıdır; hiçbir karar otomatik verilmez.":"تساعد المؤشرات الآلية في ترتيب أولوية المراجعة فقط؛ ولا تُتخذ أي قرارات آليًا.",
"[HUKUK DANIŞMANI BELİRLEYECEK: ör. KVKK m.5/2 ilgili bendi / açık rıza / veli onamı]":"[يحدده المستشار القانوني: مثل البند ذي الصلة من المادة 5(2) من قانون KVKK / الموافقة الصريحة / موافقة ولي الأمر]",
"Veriler yetkili okul personeli dışında paylaşılmaz.":"لا تتم مشاركة البيانات مع أي جهة خارج موظفي المدرسة المخوّلين.",
"[BARINDIRMA YERİ VE YURT DIŞI AKTARIM DURUMU YAZILACAK]":"[يُذكر موقع الاستضافة وما إذا كان هناك نقل للبيانات إلى خارج البلاد]",
"KVKK m.11 kapsamındaki haklar için yukarıdaki adrese başvurabilirsiniz.":"يمكنك التواصل مع العنوان أعلاه لممارسة حقوقك بموجب المادة 11 من قانون حماية البيانات الشخصية التركي (KVKK).",
"Anonim bildirimlerde bildirimi size bağlamak mümkün olmadığından bazı haklar (erişim, düzeltme) teknik olarak kullanılamayabilir.":"في البلاغات المجهولة، قد يتعذر تقنيًا ربط البلاغ بك؛ لذلك قد لا يكون من الممكن ممارسة بعض الحقوق، مثل الاطلاع والتصحيح.",
"[OKUL ADI / KURUM]":"[اسم المدرسة / المؤسسة]", "[KVKK İLETİŞİM ADRESİ]":"[عنوان التواصل بشأن حماية البيانات]",
},
"Azərbaycan dili": {
"**Veri sorumlusu:**":"**Məlumatlara nəzarət edən:**", "**İletişim:**":"**Əlaqə:**", "**İşlenen veriler:**":"**Emal olunan məlumatlar:**", "**Amaç:**":"**Məqsəd:**", "**Hukuki sebep:**":"**Hüquqi əsas:**", "**Aktarım:**":"**Məlumatların ötürülməsi:**", "**Saklama ve imha:**":"**Saxlanma və silinmə:**", "**Haklarınız:**":"**Hüquqlarınız:**",
"Bildirim formunda yazdığınız olay bilgisi (tür, ortam, zaman, açıklama). Ad, soyad, sınıf, telefon istenmez.":"Bildiriş formasına daxil etdiyiniz hadisə məlumatları (növ, mühit, vaxt və təsvir). Ad, soyad, sinif və telefon nömrəsi tələb olunmur.",
"Otomatik sinyal yalnızca inceleme sırasına yardımcıdır; hiçbir karar otomatik verilmez.":"Avtomatik siqnallar yalnız yoxlama ardıcıllığını müəyyənləşdirməyə kömək edir; heç bir qərar avtomatik verilmir.",
"[HUKUK DANIŞMANI BELİRLEYECEK: ör. KVKK m.5/2 ilgili bendi / açık rıza / veli onamı]":"[Hüquq məsləhətçisi müəyyən etməlidir: məsələn, KVKK-nın 5(2)-ci maddəsinin müvafiq bəndi / açıq razılıq / valideyn razılığı]",
"Veriler yetkili okul personeli dışında paylaşılmaz.":"Məlumatlar səlahiyyətli məktəb əməkdaşlarından başqa şəxslərlə paylaşılmır.",
"[BARINDIRMA YERİ VE YURT DIŞI AKTARIM DURUMU YAZILACAK]":"[Hostinqin yerləşdiyi yer və məlumatların xaricə ötürülüb-ötürülmədiyi qeyd edilməlidir]",
"KVKK m.11 kapsamındaki haklar için yukarıdaki adrese başvurabilirsiniz.":"Türkiyənin fərdi məlumatların qorunması haqqında qanununun (KVKK) 11-ci maddəsindəki hüquqlarınızı həyata keçirmək üçün yuxarıdakı ünvana müraciət edə bilərsiniz.",
"Anonim bildirimlerde bildirimi size bağlamak mümkün olmadığından bazı haklar (erişim, düzeltme) teknik olarak kullanılamayabilir.":"Anonim müraciətlərdə bildirişi sizinlə əlaqələndirmək texniki baxımdan mümkün olmaya bilər; buna görə məlumat əldə etmək və düzəliş tələb etmək kimi bəzi hüquqlardan istifadə mümkün olmaya bilər.",
"[OKUL ADI / KURUM]":"[MƏKTƏBİN / MÜƏSSİSƏNİN ADI]", "[KVKK İLETİŞİM ADRESİ]":"[MƏLUMATLARIN QORUNMASI ÜZRƏ ƏLAQƏ ÜNVANI]",
},
}
for _language, _entries in _NOTICE_COPY.items():
    MULTI_CATALOG[_language].update(_entries)

# Localised consent-form download. The project name itself remains unchanged.
_CONSENT_COPY = {
"Deutsch": {
"GÖNÜLLÜ KATILIM VE VELİ ONAM FORMU (TASLAK)":"FORMULAR FÜR FREIWILLIGE TEILNAHME UND ELTERLICHE EINWILLIGUNG (ENTWURF)",
"Proje: Güvenli Okul — Akran Zorbalığı Bildirim ve Takip Platformu":"Projekt: Güvenli Okul — Plattform zur Meldung und Nachverfolgung von Peer-Mobbing",
"Okul: [OKUL ADI]   Danışman öğretmen: [AD SOYAD]":"Schule: [SCHULNAME]   Betreuende Lehrkraft: [VOR- UND NACHNAME]",
"1. Amaç: Bildirim sisteminin kullanılabilirliğini ve kural tabanlı sinyalin başarımını değerlendirmek.":"1. Zweck: Bewertung der Benutzerfreundlichkeit des Meldesystems und der Leistung regelbasierter Signale.",
"2. Katılım gönüllüdür; istediğiniz zaman, gerekçe göstermeden ayrılabilirsiniz.":"2. Die Teilnahme ist freiwillig. Sie können jederzeit ohne Angabe von Gründen zurücktreten.",
"3. Toplanan veri: Formdaki olay bilgisi (ad, soyad, telefon toplanmaz). Gerçek kişileri tanıtan bilgi yazmayınız.":"3. Erhobene Daten: Vorfallangaben aus dem Formular (Name und Telefonnummer werden nicht erhoben). Geben Sie keine Informationen ein, die reale Personen identifizieren.",
"4. Saklama: [SÜRE]. Veriler yalnızca araştırma ekibi ve yetkili okul personelince görülür.":"4. Aufbewahrung: [DAUER]. Die Daten sind nur für das Forschungsteam und befugtes Schulpersonal zugänglich.",
"5. Riskler: Zorbalık konusu bazı öğrencileri üzebilir; bu durumda rehberlik servisine başvurabilirsiniz.":"5. Risiken: Das Thema Mobbing kann manche Schülerinnen und Schüler belasten. In diesem Fall können Sie sich an die schulische Beratungsstelle wenden.",
"Öğrenci: Bilgilendirildim, gönüllü katılıyorum.        Tarih: ____  İmza: ________":"Schüler/in: Ich wurde informiert und nehme freiwillig teil.        Datum: ____  Unterschrift: ________",
"Veli/Yasal temsilci: Bilgilendirildim, çocuğumun katılımına izin veriyorum.   Tarih: ____  İmza: ________":"Elternteil/gesetzliche Vertretung: Ich wurde informiert und stimme der Teilnahme meines Kindes zu.   Datum: ____  Unterschrift: ________",
},
"Français": {
"GÖNÜLLÜ KATILIM VE VELİ ONAM FORMU (TASLAK)":"FORMULAIRE DE PARTICIPATION VOLONTAIRE ET DE CONSENTEMENT PARENTAL (PROJET)",
"Proje: Güvenli Okul — Akran Zorbalığı Bildirim ve Takip Platformu":"Projet : Güvenli Okul — Plateforme de signalement et de suivi du harcèlement entre pairs",
"Okul: [OKUL ADI]   Danışman öğretmen: [AD SOYAD]":"Établissement : [NOM DE L’ÉTABLISSEMENT]   Enseignant référent : [NOM ET PRÉNOM]",
"1. Amaç: Bildirim sisteminin kullanılabilirliğini ve kural tabanlı sinyalin başarımını değerlendirmek.":"1. Objectif : évaluer la facilité d’utilisation du système de signalement et les performances des indicateurs fondés sur des règles.",
"2. Katılım gönüllüdür; istediğiniz zaman, gerekçe göstermeden ayrılabilirsiniz.":"2. La participation est volontaire ; vous pouvez vous retirer à tout moment, sans justification.",
"3. Toplanan veri: Formdaki olay bilgisi (ad, soyad, telefon toplanmaz). Gerçek kişileri tanıtan bilgi yazmayınız.":"3. Données collectées : informations sur l’incident saisies dans le formulaire (aucun nom ni numéro de téléphone n’est collecté). N’indiquez aucune information permettant d’identifier une personne réelle.",
"4. Saklama: [SÜRE]. Veriler yalnızca araştırma ekibi ve yetkili okul personelince görülür.":"4. Conservation : [DURÉE]. Les données ne sont accessibles qu’à l’équipe de recherche et au personnel autorisé de l’établissement.",
"5. Riskler: Zorbalık konusu bazı öğrencileri üzebilir; bu durumda rehberlik servisine başvurabilirsiniz.":"5. Risques : le sujet du harcèlement peut bouleverser certains élèves. Dans ce cas, vous pouvez contacter le service d’accompagnement scolaire.",
"Öğrenci: Bilgilendirildim, gönüllü katılıyorum.        Tarih: ____  İmza: ________":"Élève : J’ai été informé(e) et je participe volontairement.        Date : ____  Signature : ________",
"Veli/Yasal temsilci: Bilgilendirildim, çocuğumun katılımına izin veriyorum.   Tarih: ____  İmza: ________":"Parent/représentant légal : J’ai été informé(e) et j’autorise la participation de mon enfant.   Date : ____  Signature : ________",
},
"Español": {
"GÖNÜLLÜ KATILIM VE VELİ ONAM FORMU (TASLAK)":"FORMULARIO DE PARTICIPACIÓN VOLUNTARIA Y CONSENTIMIENTO FAMILIAR (BORRADOR)",
"Proje: Güvenli Okul — Akran Zorbalığı Bildirim ve Takip Platformu":"Proyecto: Güvenli Okul — Plataforma de avisos y seguimiento del acoso entre iguales",
"Okul: [OKUL ADI]   Danışman öğretmen: [AD SOYAD]":"Centro: [NOMBRE DEL CENTRO]   Docente asesor: [NOMBRE Y APELLIDOS]",
"1. Amaç: Bildirim sisteminin kullanılabilirliğini ve kural tabanlı sinyalin başarımını değerlendirmek.":"1. Objetivo: evaluar la facilidad de uso del sistema de avisos y el rendimiento de las señales basadas en reglas.",
"2. Katılım gönüllüdür; istediğiniz zaman, gerekçe göstermeden ayrılabilirsiniz.":"2. La participación es voluntaria; puedes retirarte en cualquier momento y sin dar explicaciones.",
"3. Toplanan veri: Formdaki olay bilgisi (ad, soyad, telefon toplanmaz). Gerçek kişileri tanıtan bilgi yazmayınız.":"3. Datos recogidos: información del incidente incluida en el formulario (no se recogen nombre, apellidos ni teléfono). No introduzcas información que identifique a personas reales.",
"4. Saklama: [SÜRE]. Veriler yalnızca araştırma ekibi ve yetkili okul personelince görülür.":"4. Conservación: [PLAZO]. Solo el equipo de investigación y el personal autorizado del centro pueden consultar los datos.",
"5. Riskler: Zorbalık konusu bazı öğrencileri üzebilir; bu durumda rehberlik servisine başvurabilirsiniz.":"5. Riesgos: el tema del acoso puede afectar emocionalmente a algunos estudiantes. En ese caso, puedes acudir al servicio de orientación del centro.",
"Öğrenci: Bilgilendirildim, gönüllü katılıyorum.        Tarih: ____  İmza: ________":"Estudiante: He recibido la información y participo voluntariamente.        Fecha: ____  Firma: ________",
"Veli/Yasal temsilci: Bilgilendirildim, çocuğumun katılımına izin veriyorum.   Tarih: ____  İmza: ________":"Padre, madre o representante legal: He recibido la información y autorizo la participación de mi hijo/a.   Fecha: ____  Firma: ________",
},
"العربية": {
"GÖNÜLLÜ KATILIM VE VELİ ONAM FORMU (TASLAK)":"نموذج المشاركة الطوعية وموافقة ولي الأمر (مسودة)",
"Proje: Güvenli Okul — Akran Zorbalığı Bildirim ve Takip Platformu":"المشروع: Güvenli Okul — منصة الإبلاغ عن التنمّر بين الأقران ومتابعته",
"Okul: [OKUL ADI]   Danışman öğretmen: [AD SOYAD]":"المدرسة: [اسم المدرسة]   المعلم المشرف: [الاسم الكامل]",
"1. Amaç: Bildirim sisteminin kullanılabilirliğini ve kural tabanlı sinyalin başarımını değerlendirmek.":"1. الهدف: تقييم سهولة استخدام نظام الإبلاغ وأداء المؤشرات القائمة على القواعد.",
"2. Katılım gönüllüdür; istediğiniz zaman, gerekçe göstermeden ayrılabilirsiniz.":"2. المشاركة طوعية؛ ويمكنك الانسحاب في أي وقت دون إبداء الأسباب.",
"3. Toplanan veri: Formdaki olay bilgisi (ad, soyad, telefon toplanmaz). Gerçek kişileri tanıtan bilgi yazmayınız.":"3. البيانات التي تُجمع: معلومات الحادثة الواردة في النموذج (لا يُجمع الاسم أو اللقب أو رقم الهاتف). لا تُدخل معلومات تكشف هوية أشخاص حقيقيين.",
"4. Saklama: [SÜRE]. Veriler yalnızca araştırma ekibi ve yetkili okul personelince görülür.":"4. مدة الاحتفاظ: [المدة]. لا يمكن الاطلاع على البيانات إلا لفريق البحث وموظفي المدرسة المخوّلين.",
"5. Riskler: Zorbalık konusu bazı öğrencileri üzebilir; bu durumda rehberlik servisine başvurabilirsiniz.":"5. المخاطر: قد يسبب موضوع التنمّر ضيقًا لبعض الطلاب. في هذه الحالة، يمكنكم التواصل مع قسم الإرشاد المدرسي.",
"Öğrenci: Bilgilendirildim, gönüllü katılıyorum.        Tarih: ____  İmza: ________":"الطالب: تم إبلاغي وأوافق على المشاركة طوعًا.        التاريخ: ____  التوقيع: ________",
"Veli/Yasal temsilci: Bilgilendirildim, çocuğumun katılımına izin veriyorum.   Tarih: ____  İmza: ________":"ولي الأمر/الممثل القانوني: تم إبلاغي وأوافق على مشاركة طفلي.   التاريخ: ____  التوقيع: ________",
},
"Azərbaycan dili": {
"GÖNÜLLÜ KATILIM VE VELİ ONAM FORMU (TASLAK)":"KÖNÜLLÜ İŞTİRAK VƏ VALİDEYN RAZILIĞI FORMASI (LAYİHƏ)",
"Proje: Güvenli Okul — Akran Zorbalığı Bildirim ve Takip Platformu":"Layihə: Güvenli Okul — Həmyaşıd zorakılığı barədə məlumatvermə və izləmə platforması",
"Okul: [OKUL ADI]   Danışman öğretmen: [AD SOYAD]":"Məktəb: [MƏKTƏBİN ADI]   Məsləhətçi müəllim: [AD SOYAD]",
"1. Amaç: Bildirim sisteminin kullanılabilirliğini ve kural tabanlı sinyalin başarımını değerlendirmek.":"1. Məqsəd: Məlumatvermə sisteminin istifadəyə yararlılığını və qayda əsaslı siqnalların performansını qiymətləndirmək.",
"2. Katılım gönüllüdür; istediğiniz zaman, gerekçe göstermeden ayrılabilirsiniz.":"2. İştirak könüllüdür; istənilən vaxt səbəb göstərmədən iştirakdan imtina edə bilərsiniz.",
"3. Toplanan veri: Formdaki olay bilgisi (ad, soyad, telefon toplanmaz). Gerçek kişileri tanıtan bilgi yazmayınız.":"3. Toplanan məlumat: Formada qeyd olunan hadisə məlumatları (ad, soyad və telefon toplanmır). Real şəxsləri tanıdan məlumatları daxil etməyin.",
"4. Saklama: [SÜRE]. Veriler yalnızca araştırma ekibi ve yetkili okul personelince görülür.":"4. Saxlanma: [MÜDDƏT]. Məlumatları yalnız tədqiqat qrupu və səlahiyyətli məktəb əməkdaşları görə bilər.",
"5. Riskler: Zorbalık konusu bazı öğrencileri üzebilir; bu durumda rehberlik servisine başvurabilirsiniz.":"5. Risklər: Zorakılıq mövzusu bəzi şagirdləri narahat edə bilər. Belə halda məktəbin psixoloji dəstək xidmətinə müraciət edə bilərsiniz.",
"Öğrenci: Bilgilendirildim, gönüllü katılıyorum.        Tarih: ____  İmza: ________":"Şagird: Məlumatlandırıldım və könüllü iştirak edirəm.        Tarix: ____  İmza: ________",
"Veli/Yasal temsilci: Bilgilendirildim, çocuğumun katılımına izin veriyorum.   Tarih: ____  İmza: ________":"Valideyn/qanuni nümayəndə: Məlumatlandırıldım və övladımın iştirakına razılıq verirəm.   Tarix: ____  İmza: ________",
},
}
for _language, _entries in _CONSENT_COPY.items():
    MULTI_CATALOG[_language].update(_entries)

for _language, _entries in {
    "Deutsch": {"Güvenlik": "Sicherheit", "[AD SOYAD]": "[VOR- UND NACHNAME]"},
    "Français": {"Güvenlik": "Sécurité", "[AD SOYAD]": "[NOM ET PRÉNOM]"},
    "Español": {"Güvenlik": "Seguridad", "[AD SOYAD]": "[NOMBRE Y APELLIDOS]"},
    "العربية": {"Güvenlik": "الأمان", "[AD SOYAD]": "[الاسم الكامل]"},
    "Azərbaycan dili": {"Güvenlik": "Təhlükəsizlik", "[AD SOYAD]": "[AD SOYAD]"},
}.items():
    MULTI_CATALOG[_language].update(_entries)

# v3.1 feature labels. Unknown user-authored content remains untouched.
_NEW_UI_EN = {
"Önleyici çalışma takvimi":"Preventive activity calendar", "Farkındalık ve eğitim":"Awareness and education",
"Yardım merkezi":"Help center", "Dil ve erişilebilirlik":"Language and accessibility",
"Yönetici bildirim merkezi":"Administrator notification center", "Yönetim günlüğü":"Administration log",
"PDF proje raporu":"PDF project report", "Yedekleme ve geri yükleme":"Backup and restore",
"Farkındalık ve eğitim merkezi":"Awareness and education center", "Dil ve erişilebilirlik merkezi":"Language and accessibility center",
"Gelişmiş yönetim işlem günlüğü":"Advanced administration activity log", "Otomatik proje raporu":"Automatic project report",
"Yönetici bildirim merkezi":"Administrator notification center", "Kalıcı veri saklama":"Permanent data retention",
"Bildirimler, inceleme notları, ek bilgiler, önleyici çalışmalar ve işlem geçmişi için 180/360 günlük otomatik silme yoktur. Süre dolduğu için kayıt silinmez.":"Reports, review notes, additional information, preventive activities and audit history are not automatically deleted after 180 or 360 days. Records are not deleted merely because time has passed.",
"Bu sürümde bildirimler, ek bilgiler, inceleme notları, önleyici çalışma kayıtları ve denetim günlüğü 180/360 gün gibi bir süre sonunda otomatik silinmez.":"In this version, reports, additional information, review notes, preventive activity records and audit logs are not automatically deleted after 180 or 360 days.",
"Kayıt silme arayüzü devre dışıdır. Veri kaybı riskine karşı Yönetim → Yedekleme ve geri yükleme bölümünden düzenli yedek alın.":"Record deletion is disabled. To reduce data-loss risk, create regular backups in Administration → Backup and restore.",
"Bildirimler, inceleme notları, ek bilgiler, önleyici çalışmalar ve işlem geçmişi için 180/360 günlük otomatik silme yoktur. Süre dolduğu için kayıt silinmez.":"Reports, review notes, additional information, preventive activities and audit history are not automatically deleted after 180 or 360 days.",
"Yaklaşan veya gecikmiş çalışma görünmüyor.":"No upcoming or overdue activities.", "Gecikmiş:":"Overdue:", "Yaklaşıyor:":"Upcoming:",
"Şimdi yedek oluştur":"Create backup now", "Yedeği geri yükle":"Restore backup", "PDF raporunu oluştur":"Generate PDF report",
"Yazıları büyüt":"Increase text size", "Yüksek kontrastı aç":"Enable high contrast",
"İşlem veya kullanıcı ara":"Search activity or user", "Gösterilen işlem":"Activities shown",
"Geri yükleme sonrasında yedekte bulunmayan yeni kayıtlar görünmez. İşlemden önce mevcut veritabanının da yedeğini indirin.":"After restoring, records not present in the backup will no longer appear. Download a backup of the current database before restoring.",
"Bu içerikler genel bilgilendirmedir; profesyonel destek veya okulun resmî prosedürlerinin yerine geçmez.":"This content is general information and does not replace professional support or official school procedures.",
"Güvenli Okul bu aşamada demo/prototiptir. Gerçek okul sistemine bağlı değildir ve acil yardım hattı değildir.":"Güvenli Okul is currently a demonstration prototype. It is not connected to a real school system and is not an emergency service.",
"Kişisel bildirim açıklamaları ve takip kodları rapora eklenmez; yalnızca toplu sayılar kullanılır.":"Personal report descriptions and tracking codes are excluded; the report uses aggregate counts only.",
"Bu aşamada demo/prototiptir.":"This is currently a demonstration prototype.",
"Öğrenciler, veliler ve okul topluluğu için güvenli, yargılayıcı olmayan bilgilendirme.":"Safe, non-judgmental information for students, families and the school community.",
"Platformu güvenli biçimde kullanmak için kısa adımlar.":"Short steps for using the platform safely.",
"Arayüz dilini sol menüden değiştirebilirsiniz. Kullanıcı tarafından yazılan bildirimler ve yönetici notları özgün dilinde korunur.":"Change the interface language in the sidebar. User-submitted reports and administrator notes remain in their original language.",
"Desteklenen arayüz dilleri":"Supported interface languages", "Arapça seçildiğinde sağdan sola yazım yönü etkinleştirilir. Takip kodları soldan sağa korunur.":"Right-to-left layout is enabled for Arabic. Tracking codes remain left-to-right.",
"Okulun ve projenin özel adları çevrilmez. Otomatik çeviri kullanıcı metinlerine uygulanmaz.":"School and project proper names are not translated. User-authored text is never machine-translated.",
"Etki Merkezi'nde oluşturulan çalışmaların yaklaşan tarihleri ve gecikme durumları.":"Upcoming dates and overdue status for activities created in the Impact Center.",
"Takvim, Etki Merkezi'ndeki kayıtları kullanır; burada ikinci bir çalışma kaydı oluşturulmaz.":"The calendar uses existing Impact Center records; it does not create duplicate activities.",
"Bekleyen bildirimler, SLA uyarıları ve yaklaşan önleyici çalışmalar için yönetim özeti.":"An overview of pending reports, SLA alerts and upcoming preventive activities.",
"İlk inceleme süresi 24 saati aşan kayıtlar var. Bu yalnızca takip uyarısıdır; acil müdahale hizmeti değildir.":"Some reports have been waiting more than 24 hours for initial review. This is a tracking alert, not an emergency response service.",
"24 saati aşan bekleyen kayıt görünmüyor.":"No pending reports have exceeded 24 hours.",
"Yönetici girişleri, kayıt değişiklikleri, dışa aktarımlar ve sistem işlemleri. Günlük kayıtları otomatik temizlenmez.":"Administrator sign-ins, record changes, exports and system activities. Logs are not automatically purged.",
"Aramayla eşleşen işlem bulunamadı.":"No activities matched your search.",
"Kişisel bildirim açıklamaları ve takip kodları rapora eklenmez; yalnızca toplu sayılar kullanılır.":"Personal report descriptions and tracking codes are excluded; only aggregate counts are used.",
"Rapor, bildirim sayısındaki değişimin tek başına zorbalık sıklığını veya önleyici çalışmanın nedensel etkisini kanıtlamadığını açıkça belirtir.":"The report explains that changes in report counts alone do not prove bullying prevalence or a causal effect of prevention activities.",
"Veri kaybına karşı veritabanının tutarlı yedeğini alın. Geri yükleme mevcut veritabanının üzerine yazar.":"Create a consistent database backup to reduce data-loss risk. Restoring overwrites the current database.",
"Bütünlük kontrolü:":"Integrity check:", "Güvenli Okul .db yedek dosyası":"Güvenli Okul .db backup file",
"Mevcut veritabanının seçtiğim yedekle değiştirileceğini anlıyorum":"I understand that the selected backup will replace the current database.",
"Yedek dosyası boş veya 100 MB sınırını aşıyor.":"The backup file is empty or exceeds the 100 MB limit.",
"Yedek dosyası sağlam değil; geri yükleme iptal edildi.":"The backup file is invalid; restoration was cancelled.",
"Dosya Güvenli Okul veritabanı yedeği değil.":"This file is not a Güvenli Okul database backup.",
"Geri yükleme yapılmadı.":"No restoration was performed.", "Yaklaşan çalışma":"Upcoming activity", "Bekleyen bildirim":"Pending reports", "24 saati aşan":"Over 24 hours",
"Sorumlu öğretmen / yetkili kişi":"Responsible teacher / authorized person", "Çalışma başlığı":"Activity title", "Açıklama ve hedef":"Description and objective", "İlişkili konu":"Related topic", "Hedef ortam":"Target setting", "Planlanan tarih":"Planned date", "Sorumlu birim":"Responsible unit", "Çalışmayı kaydet":"Save activity", "Çalışma durumu":"Activity status", "Değerlendirme / işlem notu":"Evaluation / activity note", "Değişiklikleri kaydet":"Save changes", "Önleyici çalışmalar":"Preventive activities", "İşlem geçmişi":"Activity history", "Henüz çalışma oluşturulmadı. İlk çalışmayı yukarıdaki formdan ekleyebilirsiniz.":"No activities have been created yet. You can add the first one using the form above.",
"Günlük Durum Özeti":"Daily status summary", "Denetim kaydı":"Audit log", "Dışa aktarım":"Export", "Saklama politikası":"Retention policy", "CSV indir":"Download CSV", "Kimlik bilgilerini (ad, soyad, sınıf) dahil et":"Include identity details (first name, last name, class)",
"Kayıt silme arayüzü devre dışıdır.":"Record deletion is disabled.", "Düzenli SQLite yedeği alın.":"Create regular SQLite backups.",
"Akran zorbalığını tanımak":"Understanding peer bullying", "Dijital güvenlik":"Digital safety", "Tanık olanlar ne yapabilir?":"What can witnesses do?", "Destek istemek":"Seeking support",
"Tekrarlayan, güç dengesizliği içeren davranışları; tek seferlik anlaşmazlıklardan ayırt etmeye yardımcı bilgiler.":"Information to help distinguish repeated behavior involving a power imbalance from a one-time disagreement.",
"Çevrim içi ortamda saygı, mahremiyet ve güvenli destek arama yolları.":"Respect, privacy and safe ways to seek support online.", "Güvenli ve destekleyici müdahale yolları.":"Safe and supportive ways to respond as a witness.",
"Yardım istemek güçsüzlük değildir; güvenilir yetişkinler ve okul destek birimleriyle konuşun.":"Asking for help is not weakness. Talk to a trusted adult or school support staff.",
"Davranışın tekrar edip etmediğine bakın.":"Consider whether the behavior is repeated.", "Taraflar arasındaki güç dengesizliğini değerlendirin.":"Consider whether there is a power imbalance between the people involved.", "Etiket koymadan, somut davranışı ve etkisini anlatın.":"Describe the specific behavior and its impact without labeling anyone.",
"Kişisel bilgileri ve başkalarının özel içeriklerini paylaşmayın.":"Do not share personal information or other people's private content.", "Rahatsız edici iletişime yanıt vermek zorunda değilsiniz.":"You do not have to respond to upsetting messages.", "Güvendiğiniz bir yetişkinden destek isteyin.":"Ask a trusted adult for support.",
"Güvenli değilse doğrudan müdahale etmeyin.":"Do not intervene directly if it is unsafe.", "Dışlamaya katılmayın; destekleyici bir tutum gösterin.":"Do not join in exclusion; show support instead.", "Durumu güvenilir bir yetişkine bildirin.":"Tell a trusted adult about the situation.",
"Kendinizi güvende hissettiğiniz yetişkini seçin.":"Choose an adult with whom you feel safe.", "Ne olduğunu ve nasıl etkilendiğinizi anlatın.":"Explain what happened and how it affected you.", "Acil tehlikede yerel acil yardım hizmetlerine başvurun.":"In an emergency, contact local emergency services.",
"1. Bildirim gönder":"1. Submit a report", "2. Takip kodunu sakla":"2. Keep your tracking code", "3. Durumu takip et":"3. Track the status", "4. Yetkili incelemesi":"4. Authorized review",
"Yeni bildirim sayfasında olay türü, ortam ve zaman bilgilerini seçin. Gerçek ad, telefon veya başka kişisel bilgi yazmayın.":"On the New report page, select the incident type, setting and time. Do not enter real names, phone numbers or other personal information.",
"Gönderimden sonra oluşan kodu güvenli bir yerde saklayın. Kod, bildirimin durumunu sorgulamak içindir.":"Keep the code generated after submission in a safe place. It is used to check the report status.",
"Bildirim sorgula alanında takip kodunu girin. Öğrenci ekranında açıklama ve inceleme notları gösterilmez.":"Enter your tracking code in Track a report. Descriptions and review notes are not shown on the student-facing screen.",
"Yetkili personel bildirimi insan değerlendirmesiyle inceler. Otomatik sinyaller tek başına karar vermez.":"Authorized staff review reports through human assessment. Automated signals do not make decisions on their own.",
"Sorumlu öğretmen / yetkili kişi":"Responsible teacher / authorized person", "Önleyici çalışmalar":"Preventive activities", "İşlem geçmişi":"Activity history",
"Çalışma başlığı":"Activity title", "Açıklama ve hedef":"Description and objective", "İlişkili konu":"Related topic", "Hedef ortam":"Target setting", "Planlanan tarih":"Planned date", "Sorumlu birim":"Responsible unit", "Çalışmayı kaydet":"Save activity", "Çalışma durumu":"Activity status", "Değerlendirme / işlem notu":"Evaluation / activity note", "Değişiklikleri kaydet":"Save changes",
"Güvenli Okul · Aşama 2 demo sürümü · Gerçek okul sistemi değildir.":"Güvenli Okul · Demonstration prototype · Not a real school system.",
}
CATALOG.update(_NEW_UI_EN)
for _lang, _entries in {
"Deutsch": {"Önleyici çalışma takvimi":"Kalender für Präventionsmaßnahmen","Farkındalık ve eğitim":"Aufklärung und Bildung","Yardım merkezi":"Hilfezentrum","Dil ve erişilebilirlik":"Sprache und Barrierefreiheit","Yönetici bildirim merkezi":"Admin-Benachrichtigungen","Yönetim günlüğü":"Administrationsprotokoll","PDF proje raporu":"Projektbericht als PDF","Yedekleme ve geri yükleme":"Sicherung und Wiederherstellung","Farkındalık ve eğitim merkezi":"Zentrum für Aufklärung und Bildung","Dil ve erişilebilirlik merkezi":"Sprach- und Barrierefreiheitszentrum","Kalıcı veri saklama":"Dauerhafte Datenspeicherung","Şimdi yedek oluştur":"Jetzt Sicherung erstellen","Yedeği geri yükle":"Sicherung wiederherstellen","PDF raporunu oluştur":"PDF-Bericht erstellen","Yazıları büyüt":"Text vergrößern","Yüksek kontrastı aç":"Hohe Kontraste aktivieren"},
"Français": {"Önleyici çalışma takvimi":"Calendrier des actions préventives","Farkındalık ve eğitim":"Sensibilisation et éducation","Yardım merkezi":"Centre d’aide","Dil ve erişilebilirlik":"Langue et accessibilité","Yönetici bildirim merkezi":"Centre de notifications administrateur","Yönetim günlüğü":"Journal d’administration","PDF proje raporu":"Rapport de projet PDF","Yedekleme ve geri yükleme":"Sauvegarde et restauration","Farkındalık ve eğitim merkezi":"Centre de sensibilisation et d’éducation","Dil ve erişilebilirlik merkezi":"Centre de langue et d’accessibilité","Kalıcı veri saklama":"Conservation permanente des données","Şimdi yedek oluştur":"Créer une sauvegarde","Yedeği geri yükle":"Restaurer la sauvegarde","PDF raporunu oluştur":"Générer le rapport PDF","Yazıları büyüt":"Agrandir le texte","Yüksek kontrastı aç":"Activer le contraste élevé"},
"Español": {"Önleyici çalışma takvimi":"Calendario de actividades preventivas","Farkındalık ve eğitim":"Sensibilización y educación","Yardım merkezi":"Centro de ayuda","Dil ve erişilebilirlik":"Idioma y accesibilidad","Yönetici bildirim merkezi":"Centro de notificaciones de administración","Yönetim günlüğü":"Registro de administración","PDF proje raporu":"Informe del proyecto en PDF","Yedekleme ve geri yükleme":"Copia de seguridad y restauración","Farkındalık ve eğitim merkezi":"Centro de sensibilización y educación","Dil ve erişilebilirlik merkezi":"Centro de idioma y accesibilidad","Kalıcı veri saklama":"Conservación permanente de datos","Şimdi yedek oluştur":"Crear copia de seguridad","Yedeği geri yükle":"Restaurar copia de seguridad","PDF raporunu oluştur":"Generar informe PDF","Yazıları büyüt":"Aumentar el tamaño del texto","Yüksek kontrastı aç":"Activar alto contraste"},
"العربية": {"Önleyici çalışma takvimi":"تقويم الأنشطة الوقائية","Farkındalık ve eğitim":"التوعية والتعليم","Yardım merkezi":"مركز المساعدة","Dil ve erişilebilirlik":"اللغة وإمكانية الوصول","Yönetici bildirim merkezi":"مركز إشعارات المسؤول","Yönetim günlüğü":"سجل الإدارة","PDF proje raporu":"تقرير المشروع PDF","Yedekleme ve geri yükleme":"النسخ الاحتياطي والاستعادة","Farkındalık ve eğitim merkezi":"مركز التوعية والتعليم","Dil ve erişilebilirlik merkezi":"مركز اللغة وإمكانية الوصول","Kalıcı veri saklama":"الاحتفاظ الدائم بالبيانات","Şimdi yedek oluştur":"إنشاء نسخة احتياطية الآن","Yedeği geri yükle":"استعادة النسخة الاحتياطية","PDF raporunu oluştur":"إنشاء تقرير PDF","Yazıları büyüt":"تكبير النص","Yüksek kontrastı aç":"تفعيل التباين العالي"},
"Azərbaycan dili": {"Önleyici çalışma takvimi":"Profilaktik tədbirlər təqvimi","Farkındalık ve eğitim":"Maarifləndirmə və təhsil","Yardım merkezi":"Yardım mərkəzi","Dil ve erişilebilirlik":"Dil və əlçatanlıq","Yönetici bildirim merkezi":"Administrator bildiriş mərkəzi","Yönetim günlüğü":"İdarəetmə jurnalı","PDF proje raporu":"PDF layihə hesabatı","Yedekleme ve geri yükleme":"Ehtiyat nüsxə və bərpa","Farkındalık ve eğitim merkezi":"Maarifləndirmə və təhsil mərkəzi","Dil ve erişilebilirlik merkezi":"Dil və əlçatanlıq mərkəzi","Kalıcı veri saklama":"Məlumatların daimi saxlanması","Şimdi yedek oluştur":"İndi ehtiyat nüsxə yarat","Yedeği geri yükle":"Ehtiyat nüsxəni bərpa et","PDF raporunu oluştur":"PDF hesabatı yarat","Yazıları büyüt":"Mətni böyüt","Yüksek kontrastı aç":"Yüksək kontrastı aktivləşdir"}
}.items():
    MULTI_CATALOG[_lang].update(_entries)

# Keep explicit source-language semantics. Unknown/user-authored content is never
# machine-translated or guessed; untranslated UI strings remain Turkish.
def translate(value: Any, language: str | None = None) -> Any:
    lang = language or CURRENT_LANGUAGE
    if not isinstance(value, str) or lang == TR:
        return value
    if lang == EN:
        return _translate_tr_en(value, EN)
    table = MULTI_CATALOG.get(lang, {})
    if value in table:
        return table[value]
    # If an application-authored interface string has an English source entry
    # but no reviewed translation for the selected locale yet, show the complete
    # English phrase rather than leaking Turkish into the interface. Unknown
    # free text is still preserved verbatim and is never machine-translated.
    if value in CATALOG:
        return CATALOG[value]
    dynamic = re.match(r"^(\d+) kayıt$", value)
    if dynamic:
        n = dynamic.group(1)
        return {"Deutsch": f"{n} Meldungen", "Français": f"{n} signalements", "Español": f"{n} reportes", "العربية": f"{n} بلاغات", "Azərbaycan dili": f"{n} bildiriş"}.get(lang, value)
    dynamic = re.match(r"^Son (\d+) gün$", value)
    if dynamic:
        n = dynamic.group(1)
        return {"Deutsch": f"Letzte {n} Tage", "Français": f"{n} derniers jours", "Español": f"Últimos {n} días", "العربية": f"آخر {n} أيام", "Azərbaycan dili": f"Son {n} gün"}.get(lang, value)
    dynamic = re.match(r"^(\d+(?:[.,]\d+)?) saat bekliyor$", value)
    if dynamic:
        n = dynamic.group(1)
        return {"Deutsch": f"wartet seit {n} Stunden", "Français": f"en attente depuis {n} heures", "Español": f"en espera durante {n} horas", "العربية": f"بانتظار المراجعة منذ {n} ساعة", "Azərbaycan dili": f"{n} saatdır gözləyir"}.get(lang, value)
    # Exact, reviewed UI phrases may also occur inside longer Markdown copy.
    # Longer phrases are replaced first; short tokens are restricted to exact
    # values to avoid altering unrelated words or user-authored text.
    result = value
    # Native translations take precedence. English catalogue entries act only
    # as a safe fallback for known application UI copy, never as a translator
    # for arbitrary user-authored text.
    combined = dict(CATALOG)
    combined.update(table)
    for source, target in sorted(combined.items(), key=lambda item: len(item[0]), reverse=True):
        if len(source) < 7 or not target:
            continue
        pattern = re.compile(r"\s+".join(re.escape(part) for part in source.split()))
        result = pattern.sub(lambda _m, replacement=target: replacement, result)
    return result


def format_timestamp(value: str | None, language: str | None = None) -> str:
    lang = language or CURRENT_LANGUAGE
    if lang in (TR, EN):
        return _format_timestamp_tr_en(value, lang)
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return value
    months = {
      "Deutsch":("Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"),
      "Français":("janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."),
      "Español":("ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"),
      "العربية":("يناير","فبراير","مارس","أبريل","مايو","يونيو","يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"),
      "Azərbaycan dili":("yan","fev","mar","apr","may","iyn","iyl","avq","sen","okt","noy","dek")}
    if lang == "Deutsch":
        return f"{dt.day:02d}.{dt.month:02d}.{dt.year} · {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"
    if lang == "Français":
        return f"{dt.day:02d} {months[lang][dt.month-1]} {dt.year} · {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"
    if lang == "Español":
        return f"{dt.day:02d} {months[lang][dt.month-1]} {dt.year} · {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"
    if lang == "العربية":
        return f"{dt.day:02d} {months[lang][dt.month-1]} {dt.year} · {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"
    return f"{dt.day:02d} {months[lang][dt.month-1]} {dt.year} · {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"


def translate_structure(value: Any, language: str | None = None) -> Any:
    lang = language or CURRENT_LANGUAGE
    if isinstance(value, dict):
        return {translate(k, lang): translate_structure(v, lang) for k, v in value.items()}
    if isinstance(value, list):
        return [translate_structure(v, lang) for v in value]
    if isinstance(value, tuple):
        return tuple(translate_structure(v, lang) for v in value)
    if isinstance(value, str):
        return translate(value, lang)
    return value


def text_direction(language: str | None = None) -> str:
    lang = language or CURRENT_LANGUAGE
    return LANGUAGES.get(lang, LANGUAGES[TR])["direction"]


def locale_code(language: str | None = None) -> str:
    lang = language or CURRENT_LANGUAGE
    return LANGUAGES.get(lang, LANGUAGES[TR])["locale"]
