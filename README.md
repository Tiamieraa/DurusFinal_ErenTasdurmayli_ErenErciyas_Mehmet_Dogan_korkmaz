````markdown
# 🎯 Akıllı Duruş Analiz Sistemi

Bu proje, **Proje Uygulamaları** kapsamında geliştirilen *Akıllı Duruş Analiz Sistemi*’nin final sürümünü ve sahip olduğu özellikleri kapsamlı biçimde tanıtmaktadır.

## 🌟 Proje Amacı

Modern yaşam tarzı ile yaygınlaşan uzun süreli hareketsizlik ve yanlış oturma alışkanlıkları; skolyoz, kifoz (kamburluk), boyun düzleşmesi gibi omurga rahatsızlıklarına yol açabilmektedir. Bu proje, özellikle **ofis çalışanları**, **öğrenciler** ve **oyuncular** gibi uzun süre oturarak çalışan bireylerin, **gerçek zamanlı duruş analizi** ile duruşlarını düzeltmelerine yardımcı olmayı hedefler.

📌 **Amaç:**  
Kullanıcıların duruşlarını kamera üzerinden analiz ederek, anlık geri bildirimlerle kötü duruş alışkanlıklarını engellemek ve omurga sağlığını korumak.

---

## 🚀 Uygulama Genel Bakışı

- **MediaPipe** ile vücut iskelet noktaları izlenir.
- **Omuz hizası**, **sırt açısı** ve **boyun açısı** temel parametrelerdir.
- **Gerçek zamanlı sesli ve görsel uyarılar** ile kullanıcı bilgilendirilir.
- **Modern PyQt5 GUI** ile sezgisel bir arayüz sunar.

---

## 🆕 Final Sürümde Eklenen Özellikler

- ✅ **Boyun Açısı Kontrolü:** Eğik boyun duruşları için uyarı sistemi.
- ✅ **Gelişmiş Kalibrasyon:** Başlangıç eşik değerleri ile daha hassas ölçüm.
- ✅ **Duraklat / Devam Et Butonu:** Kamera ve analiz işlemleri kontrol edilebilir.
- ✅ **Modern PyQt5 Arayüzü:** Kullanıcı dostu ve estetik tasarım.
- ✅ **Zaman Serisi Raporlama:** Günlük grafiksel duruş verileri.
- ✅ **Bildirim Esnekliği:** Sesli/masaüstü uyarılar özelleştirilebilir.

---

## 🛠️ Kullanılan Teknolojiler

| Kütüphane         | Açıklama                                                                 |
|-------------------|--------------------------------------------------------------------------|
| `mediapipe`       | Vücut iskeleti ve poz tahmini                                            |
| `opencv-python`   | Kamera akışı ve görüntü işleme (CLAHE dahil)                             |
| `PyQt5`           | Grafik arayüz                                                            |
| `Pillow`          | Görüntü işleme                                                           |
| `plyer`           | Platform bağımsız masaüstü bildirim sistemi                              |
| `matplotlib`      | Grafiksel raporlama                                                      |
| `numpy`           | Açı ve mesafe hesaplamaları                                              |
| `pyttsx3`         | Metinden sese dönüştürme (text-to-speech)                                |
| `pandas`          | Veri işleme ve CSV log okuma/yazma işlemleri                             |

---
````
## ⚙️ Kurulum ve Başlatma

1. Gerekli kütüphaneleri yükleyin:

   ```bash
   pip install -r requirements.txt


2. Uygulamayı başlatın:

   ```bash
   python main.py
   ```

3. Başlangıçta bir kullanıcı adı girmeniz istenir.

---

## 📏 Özellikler

* 🎥 **Gerçek Zamanlı Kamera Görüntüsü**
  Webcam üzerinden iskelet takibi ve duruş çizimi.

* 📊 **Detaylı Duruş Analizi**

  * **Omuz Farkı:** Dikey fark tespiti.
  * **Sırt Açısı:** Omuz-kalça-diz hattı ile sırt sınıflandırması.
  * **Boyun Açısı:** Kulak-omuz-kalça hattı ile boyun durumu sınıflandırması.

* ⚙️ **Kişiselleştirilebilir Eşikler**

* 🌙 **Düşük Işık Modu** (CLAHE)

* 🔊 **Sesli ve Görsel Uyarılar**

* ⏯️ **Duraklat / Devam Et Butonu**

* 📈 **Zaman Serisi Grafikleriyle Raporlama**

---

## 📁 Log Dosyaları

Tüm analiz verileri `logs/` klasörüne kullanıcı adına göre kaydedilir.

* **Format:** `posture_log_<username>.csv`
* **Sütunlar:** `timestamp`, `status`, `value`

---

## 👨‍💻 Katkıda Bulunanlar

| İsim                     | Görevler                                    |
| ------------------------ | ------------------------------------------- |
| **Eren Taşdurmaylı**     | Proje Yönetimi, Kodlama, Ekran Kaydı        |
| **Eren Erciyas**         | PyQt5 Arayüz Tasarımı, Kodlama              |
| **Mehmet Doğan Korkmaz** | Duruş Algoritmaları, Kodlama Raporlama |

---



## 📌 Lisans

Bu proje eğitim amaçlı geliştirilmiştir. Tüm hakları proje geliştiricilerine aittir.

```

