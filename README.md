# Telegram Haber Botu

![Logo](tt1.png)

Telegram Haber Botu, haber kaynaklarından RSS beslemelerini çekip rastgele makaleleri belirli aralıklarla Telegram kanalınıza gönderen bir bottur. Bu bot, PyQt5 ve APScheduler kullanılarak oluşturulmuştur ve async/await destekleyen Telegram Bot API ile entegre edilmiştir.

## İçerik
- [Özellikler](#özellikler)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [Gereksinimler](#gereksinimler)
- [Katkıda Bulunma](#katkıda-bulunma)
- [Lisans](#lisans)
- [Örnek Resim](#örnek-resim)

## Özellikler 🌟

- 📄 **Makale Çekme**: RSS beslemelerinden makale çekme.
- ✉️ **Makale Paylaşma**: Rastgele makaleleri belirli aralıklarla Telegram kanalına gönderme.
- 🖥️ **Kullanıcı Dostu Arayüz**: Kullanıcı dostu arayüz ile botunuzu kolayca yönetme.
- 🚀 **Bot Yönetimi**: Bot başlatma ve durdurma işlemleri.
- 📊 **Log Takibi**: Renkli loglama sistemi ile bot aktivitelerini takip etme.

## Kurulum 🛠️

Bu projeyi çalıştırmak için aşağıdaki adımları izleyin:

1. Bu projeyi klonlayın:
    ```sh
    git clone https://github.com/Fridibuck/telegram-news-bot.git
    cd telegramhaberbotu
    ```


2. Telegram Bot API anahtarınızı `telegramhaber.py` dosyasına ekleyin:
    ```python
    bot_token = 'YOUR_BOT_TOKEN'
    ```

3. RSS beslemelerini içeren `rss.txt` dosyasını oluşturun ve içerisine RSS URL'lerini ekleyin.
    ```txt
    http://example.com/rss
    http://anotherexample.com/rss
    ```

## Kullanım 📚

1. Uygulamayı çalıştırın:
    ```sh
    python telegramhaber.py
    ```

2. Arayüz üzerinden botu başlatın ve durdurun, makale çekme ve paylaşma işlemlerini gerçekleştirin.

## Gereksinimler 📦

- Python 3.7 veya daha üstü
- Aşağıdaki Python kütüphaneleri:
  - PyQt5
  - python-telegram-bot
  - APScheduler
  - feedparser
  - requests

## Katkıda Bulunma 🤝

Eğer katkıda bulunmak isterseniz, lütfen bir pull request gönderin. Tüm katkılar ve geri bildirimler memnuniyetle karşılanır.



## Örnek Resim 🌠

![Örnek Görüntü](https://imgur.com/hjJaBd2.png)

---

**Made with 💖 by @Fridibuck**

---
