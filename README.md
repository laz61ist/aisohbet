# AI Danışmanlar Kurulu v4.0

Bu proje, bir proje fikrini veya soruyu, farklı alanlarda uzmanlaşmış (Teknik, Strateji, Finans) yapay zeka modellerinin kolektif zekasını kullanarak analiz eden bir full-stack web uygulamasıdır. Sistem, bir "Moderatör AI" tarafından yönetilen sanal bir danışmanlar kurulu gibi çalışır.

## Özellikler

- **Çoklu Perspektif:** Tek bir AI'ın yankı odasından kaçınarak, GPT-4o (Teknik), Claude 3 Opus (Strateji) ve Gemini 1.5 Pro (Finans) modellerinden dengeli bir analiz alın.
- **Moderatör Özeti:** Tüm uzman görüşleri, Gemini 1.5 Pro tarafından sentezlenerek size bütünsel bir özet olarak sunulur.
- **Doğrudan Erişim:** `@teknik`, `@strateji` veya `@finans` gibi etiketler kullanarak doğrudan ilgilendiğiniz uzmana soru sorun.
- **Kalıcı Hafıza:** Tüm sohbetleriniz veritabanında saklanır, böylece konuşmalarınıza kaldığınız yerden devam edebilirsiniz.
- **Genişletilebilir Mimari:** `experts.json` dosyası sayesinde yeni uzmanlar eklemek veya mevcutları değiştirmek son derece kolaydır.
- **Kolay Kurulum:** Otomatik veritabanı ve tablo oluşturma özelliği ile hızlı başlangıç.

## Kurulum ve Çalıştırma

Bu projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları izleyin.

### 1. Ön Gereksinimler

- **XAMPP:** Apache ve MySQL sunucularını kolayca çalıştırmak için gereklidir. [XAMPP'yi İndirin](https://www.apachefriends.org/tr/index.html).
- **Python:** AI servisi Python ile çalışmaktadır. [Python'u İndirin](https://www.python.org/downloads/).
- **Git:** Projeyi klonlamak için gereklidir. [Git'i İndirin](https://git-scm.com/downloads).

### 2. Projeyi Klonlama

Proje dosyalarını bilgisayarınızdaki XAMPP kurulumunun `htdocs` klasörüne klonlayın.

```bash
# XAMPP'nin htdocs klasörüne gidin
cd /path/to/xampp/htdocs

# Projeyi klonlayın
git clone <bu-projenin-git-adresi> aisohbet
cd aisohbet
```

### 3. PHP ve Veritabanı Yapılandırması

1.  **XAMPP Kontrol Panelini** açın ve **Apache** ile **MySQL** modüllerini başlatın.
2.  Uygulama, ilk çalıştırmada `aisohbet_db` adında bir veritabanı ve gerekli tabloları otomatik olarak oluşturacaktır. Herhangi bir manuel veritabanı işlemi yapmanıza gerek yoktur.

### 4. Python Bağımlılıklarını Kurma

Proje dizininde bir terminal veya komut istemi açın ve `requirements.txt` dosyasında listelenen Python kütüphanelerini kurun.

```bash
pip install -r requirements.txt
```

### 5. API Anahtarlarını Ayarlama

Projenin AI modelleriyle iletişim kurabilmesi için API anahtarlarınıza ihtiyacı var.

1.  Proje kök dizinindeki `.env.example` dosyasının bir kopyasını oluşturun ve adını `.env` olarak değiştirin.
2.  `.env` dosyasını bir metin düzenleyici ile açın ve kendi OpenAI, Google (Gemini) ve Anthropic (Claude) API anahtarlarınızı ilgili alanlara yapıştırın.

    ```
    OPENAI_API_KEY="sk-xxx..."
    GOOGLE_API_KEY="AIzaSy..."
    ANTHROPIC_API_KEY="sk-ant-api03-xxx..."
    ```

### 6. Uygulamayı Çalıştırma

Tüm adımları tamamladıktan sonra, web tarayıcınızı açın ve aşağıdaki adrese gidin:

`http://localhost/aisohbet/`

Uygulama artık kullanıma hazırdır! Yeni bir sohbet oluşturabilir veya mevcut sohbetlerinize devam edebilirsiniz.

## Nasıl Kullanılır?

- **Genel Analiz (Moderatör Modu):** Bir proje fikri veya soru yazdığınızda, sistem otomatik olarak tüm uzmanlardan görüş alır ve size bir özet sunar.
- **Uzman Sorgulama:** Mesajınızın başına `@teknik`, `@strateji` veya `@finans` etiketlerinden birini ekleyerek doğrudan o uzmanın görüşünü alabilirsiniz.
  - Örnek: `@teknik Yeni projem için hangi veritabanını önerirsin?`
