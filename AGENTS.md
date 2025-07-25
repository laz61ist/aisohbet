# AI Danışmanlar Kurulu v4.0 - Agent Talimatları

Bu belge, "AI Danışmanlar Kurulu v4.0" projesinin teknik mimarisini, bileşenler arası etkileşimi ve geliştirme prensiplerini açıklamaktadır. Bu projede değişiklik yapacak olan AI agent'ların bu talimatlara uyması beklenmektedir.

## 1. Sistem Mimarisi ve Felsefesi

Proje, 4 ana bileşenden oluşan ayrıştırılmış (decoupled) bir mimari üzerine kuruludur:

1.  **Frontend (Vanilla JS):** Kullanıcı arayüzünü yönetir ve `api.php` ile etkileşime girer. Durum (state) yönetimi minimaldir ve büyük ölçüde sunucudan gelen yanıtlara dayanır.
2.  **Backend (PHP Web Sunucusu):** Orkestratör görevi görür. Frontend'den gelen istekleri alır, veritabanı işlemlerini (okuma/yazma) yapar ve AI servisini tetikler.
3.  **Veritabanı (MySQL):** Tüm sohbet oturumlarını ve mesajları kalıcı olarak depolar. `chats` ve `messages` tabloları arasındaki `FOREIGN KEY` ilişkisi sistemin temelini oluşturur.
4.  **AI Servisi (Python):** Durumsuz (stateless) bir komut satırı uygulamasıdır. PHP tarafından çağrılır, görevini yapar (LLM'lerle iletişim kurar), sonucunu JSON olarak standart çıktıya basar ve sonlanır.

**Felsefe:** Bileşenler arasındaki sorumluluklar nettir. PHP, AI mantığı bilmez; sadece bir Python script'ini çağırır. Python, veritabanı veya HTTP istekleri hakkında bilgi sahibi değildir; sadece argüman olarak aldığı veriyi işler ve sonuç döndürür. Bu ayrım korunmalıdır.

## 2. Geliştirme Prensipleri

- **Genişletilebilirlik Merkezdedir:** `ai_service.py` içindeki mantık, `experts.json` dosyası tarafından yönlendirilir. Yeni bir uzman eklemek veya bir uzmanın modelini/prompt'unu değiştirmek için **asla** `ai_service.py` kodunu doğrudan değiştirmeyin. Yalnızca `experts.json` dosyasını güncelleyin.
- **Güvenlik:**
    - API anahtarları **asla** koda hard-code edilmemelidir. Her zaman `.env` dosyasından `python-dotenv` kütüphanesi ile okunmalıdır.
    - PHP'den Python'a veri aktarırken, karmaşık JSON yapılarının komut satırında bozulmasını önlemek için veri `base64` ile kodlanmıştır. Bu pratik sürdürülmelidir.
- **Dayanıklılık:** PHP'deki `proc_open` ile sağlanan `timeout` mekanizması, AI servisinin yanıt vermemesi durumunda sistemin kilitlenmesini önler. AI servisine yapılan çağrılar her zaman bu tür bir koruma mekanizması içinde olmalıdır.
- **Veritabanı Şeması:** Veritabanı şeması basittir ve öyle kalmalıdır. Eğer yeni bir özellik karmaşık ek tablolar veya ilişkiler gerektiriyorsa, bu durumun mimari üzerindeki etkisi dikkatlice değerlendirilmelidir. `messages` tablosundaki `content` sütununun JSON metin olarak saklanması, esneklik için kasıtlı bir tercihtir.

## 3. Kodlama Kontrolleri ve Doğrulama

Bu projede bir değişiklik yaptıktan sonra, aşağıdaki kontrolleri gerçekleştirdiğinizden emin olun:

1.  **Moderatör Modu Testi:** Herhangi bir `@` etiketi olmadan genel bir soru sorun. Sistemin `experts.json`'da tanımlı tüm uzmanları (moderatör hariç) çalıştırdığını ve ardından moderatörün bir özet oluşturduğunu doğrulayın. Dönen JSON yanıtının `{"summary": "...", "details": {...}}` yapısında olduğunu kontrol edin.
2.  **Doğrudan Uzman Testi:** `experts.json`'daki her bir uzman için `@<uzman_adi>` formatında bir soru sorun. Örneğin: `@teknik ...`. Sistemin sadece ilgili uzmanı tetiklediğini ve yanıtın `{"direct_response": "..."}` formatında olduğunu doğrulayın.
3.  **Yeni Uzman Ekleme Testi:**
    - `experts.json` dosyasına "pazarlama" gibi yeni bir uzman ekleyin.
    - Hiçbir Python veya PHP kodunu değiştirmeden, `@pazarlama ...` sorgusunun doğru şekilde çalıştığını test edin.
    - Ardından genel bir soru sorarak yeni eklenen pazarlama uzmanının da moderatör özetine dahil edildiğini doğrulayın.
4.  **Kurulum Testi:** `README.md`'deki kurulum adımlarının hala geçerli ve çalışır durumda olduğunu kontrol edin. `requirements.txt` dosyasının güncel olduğundan emin olun.

Bu talimatlar, projenin tutarlı, sağlam ve bakımı kolay bir şekilde geliştirilmesini sağlamak için vardır.
