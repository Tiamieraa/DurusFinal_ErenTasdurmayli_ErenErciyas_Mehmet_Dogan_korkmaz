import sys
import os
import cv2
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import time # Kalibrasyon için time modülünü içe aktar

# Bu modüllerin ortamınızda mevcut olduğu varsayılıyor
# Eğer bu modüller aynı dizinde değilse, PYTHONPATH'inizi ayarlamanız
# veya onları uygun yere yerleştirmeniz gerekecektir.
try:
    from posturedetector import PoseDetector
    from notifier import send_notification
    from logger import set_user, log_posture
except ImportError as e:
    print(f"Özel modüller içe aktarılırken hata oluştu: {e}")
    print("'posturedetector.py', 'notifier.py' ve 'logger.py' dosyalarının aynı dizinde olduğundan emin olun.")
    sys.exit(1)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, username: str):
        super().__init__()
        self.username = username
        set_user(username) # Loglama için kullanıcıyı ayarla

        self.setWindowTitle(f"Duruş Analiz Sistemi — Kullanıcı: {username}")
        self.resize(1000, 750) # Daha iyi estetik için biraz daha büyük pencere

        # Varsayılan eşikler
        # Bu değerler UI döndürme kutuları (spin box) tarafından güncellenecektir
        self.shoulder_thresh = 26 # Kullanıcı tarafından sağlanan değer: 26 px
        self.angle_lower = 160 # Kullanıcı tarafından sağlanan değer: 160 °
        self.angle_upper = 180 # Kullanıcı tarafından sağlanan değer: 180 °
        self.neck_angle_lower = 140 # Kullanıcı tarafından sağlanan değer: 140 °
        self.neck_angle_upper = 180 # Kullanıcı tarafından sağlanan değer: 180 °
        self.low_light_mode = False
        self.paused = False  # Duraklatma durumu eklendi

        self.detector = PoseDetector() # Duruş dedektörünüzü başlat
        self.cap = None # Video yakalama nesnesi

        # Düşük ışık için CLAHE (Kontrast Sınırlı Adaptif Histogram Eşitleme)
        self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))

        self.init_ui() # Kullanıcı arayüzünü başlat
        self.apply_stylesheet() # Özel stil uygulamasını çağır
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame) # Zamanlayıcıyı kare güncellemeye bağla

    def apply_stylesheet(self):
        """Uygulamaya modern ve temiz bir QSS stil sayfası uygular."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5; /* Açık gri arka plan */
            }
            QTabWidget::pane {
                border: 1px solid #d3d3d3;
                background-color: #ffffff; /* Beyaz içerik alanı */
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #e0e0e0; /* Etkin olmayan sekmeler için biraz daha koyu gri */
                border: 1px solid #d3d3d3;
                border-bottom-color: #c2c2c2; /* Sorunsuz bir görünüm için bölme kenarlığıyla eşleşir */
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 120px; /* Daha geniş sekmeler */
                padding: 10px;
                font-weight: bold;
                color: #555555; /* Etkin olmayan sekmeler için daha koyu metin */
                margin-right: 2px; /* Sekmeler arasında küçük boşluk */
            }
            QTabBar::tab:selected {
                background: #ffffff; /* Seçili sekme için beyaz */
                border-color: #d3d3d3;
                border-bottom-color: #ffffff; /* Seçili sekme için alt kenarlığı gizle */
                color: #2c3e50; /* Seçili sekme için daha koyu metin */
            }
            QLabel#video_label { /* Özel stil için nesne adını kullanma */
                border: 2px solid #cccccc;
                border-radius: 8px;
                background-color: #1a1a1a; /* Video akışı alanı için daha koyu arka plan */
                qproperty-alignment: AlignCenter; /* İçeriğin ortalanmasını sağla */
            }
            QLabel#status_label {
                font-size: 24px; /* Durum için daha büyük yazı tipi */
                font-weight: bold;
                padding: 10px;
                border-radius: 8px;
                margin-top: 15px; /* Durum etiketinin üstünde daha fazla boşluk */
                color: white; /* Durum için varsayılan metin rengi */
                min-height: 40px; /* Minimum yükseklik sağla */
            }
            QSpinBox, QCheckBox {
                padding: 8px; /* Girişler için daha fazla dolgu */
                border: 1px solid #cccccc;
                border-radius: 5px;
                font-size: 15px; /* Biraz daha büyük yazı tipi */
                min-height: 30px; /* Tutarlı yükseklik sağla */
            }
            QPushButton {
                background-color: #3498db; /* Düğmeler için mavi */
                color: white;
                border: none;
                padding: 12px 20px; /* Düğmeler için daha büyük dolgu */
                border-radius: 8px;
                font-size: 16px; /* Düğmeler için daha büyük yazı tipi */
                font-weight: bold;
                margin-top: 10px; /* Düğmelerin üstünde boşluk */
            }
            QPushButton:hover {
                background-color: #2980b9; /* Üzerine gelince daha koyu mavi */
            }
            QPushButton:pressed {
                background-color: #2471a3; /* Basıldığında daha da koyu */
            }
            QMessageBox {
                background-color: #f0f2f5;
                font-size: 14px;
            }
            /* Form düzeni etiketleri için stil */
            QFormLayout QLabel {
                font-size: 15px;
                font-weight: bold;
                color: #333333;
            }
        """)

    def init_ui(self):
        """Ana kullanıcı arayüzü bileşenlerini başlatır."""
        tabs = QtWidgets.QTabWidget()
        self.setCentralWidget(tabs)

        # --- Canlı İzleme Sekmesi ---
        live_tab = QtWidgets.QWidget()
        live_layout = QtWidgets.QVBoxLayout(live_tab)
        live_layout.setContentsMargins(20, 20, 20, 20) # İçerik etrafına dolgu ekle
        live_layout.setAlignment(QtCore.Qt.AlignCenter) # İçeriği dikey olarak ortala

        self.video_label = QtWidgets.QLabel()
        self.video_label.setObjectName("video_label") # QSS için nesne adını ayarla
        self.video_label.setFixedSize(640, 480) # Video akışı için sabit boyut
        live_layout.addWidget(self.video_label, alignment=QtCore.Qt.AlignCenter)

        self.status_label = QtWidgets.QLabel("Bekleniyor...")
        self.status_label.setObjectName("status_label") # QSS için nesne adını ayarla
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        live_layout.addWidget(self.status_label)

        # Duraklatma butonu eklendi
        self.btn_pause = QtWidgets.QPushButton("Duraklat")
        self.btn_pause.clicked.connect(self.toggle_pause)
        live_layout.addWidget(self.btn_pause, alignment=QtCore.Qt.AlignCenter)

        tabs.addTab(live_tab, "Canlı İzleme")

        # --- Ayarlar Sekmesi ---
        settings_tab = QtWidgets.QWidget()
        settings_layout = QtWidgets.QFormLayout(settings_tab)
        settings_layout.setContentsMargins(50, 40, 50, 40) # Ayarlar için daha fazla dolgu
        settings_layout.setVerticalSpacing(20) # Form satırları arasında daha fazla boşluk

        # Omuz Eşiği Döndürme Kutusu (SpinBox)
        self.sb_sh = QtWidgets.QSpinBox()
        self.sb_sh.setRange(0, 1000)
        self.sb_sh.setValue(int(self.shoulder_thresh))
        self.sb_sh.setSuffix(" px") # Birim son eki ekle
        settings_layout.addRow("Omuz Farkı Eşiği:", self.sb_sh)

        # Sırt Açı Alt Eşiği Döndürme Kutusu (SpinBox)
        self.sb_lo = QtWidgets.QSpinBox()
        self.sb_lo.setRange(0, 180)
        self.sb_lo.setValue(self.angle_lower)
        self.sb_lo.setSuffix(" °") # Birim son eki ekle
        settings_layout.addRow("Sırt Açı Alt Eşiği:", self.sb_lo)

        # Sırt Açı Üst Eşiği Döndürme Kutusu (SpinBox)
        self.sb_hi = QtWidgets.QSpinBox()
        self.sb_hi.setRange(0, 180)
        self.sb_hi.setValue(self.angle_upper)
        self.sb_hi.setSuffix(" °") # Birim son eki ekle
        settings_layout.addRow("Sırt Açı Üst Eşiği:", self.sb_hi)

        # Yeni: Boyun Açı Alt Eşiği SpinBox
        self.sb_na_lo = QtWidgets.QSpinBox()
        self.sb_na_lo.setRange(0, 180)
        self.sb_na_lo.setValue(self.neck_angle_lower)
        self.sb_na_lo.setSuffix(" °") # Birim son eki ekle
        settings_layout.addRow("Boyun Açı Alt Eşiği:", self.sb_na_lo)

        # Yeni: Boyun Açı Üst Eşiği SpinBox
        self.sb_na_hi = QtWidgets.QSpinBox()
        self.sb_na_hi.setRange(0, 180)
        self.sb_na_hi.setValue(self.neck_angle_upper)
        self.sb_na_hi.setSuffix(" °") # Birim son eki ekle
        settings_layout.addRow("Boyun Açı Üst Eşiği:", self.sb_na_hi)

        # Düşük Işık Modu Onay Kutusu (Checkbox)
        self.chk_ll = QtWidgets.QCheckBox("Düşük Işık Modu")
        settings_layout.addRow(self.chk_ll)

        # Kalibre Et Butonu
        btn_cal = QtWidgets.QPushButton("Kalibre Et (5s)")
        btn_cal.clicked.connect(self.calibrate)
        settings_layout.addRow(btn_cal)

        tabs.addTab(settings_tab, "Ayarlar")

        # --- Rapor Sekmesi ---
        report_tab = QtWidgets.QWidget()
        report_layout = QtWidgets.QVBoxLayout(report_tab)
        report_layout.setContentsMargins(20, 20, 20, 20) # Rapor sekmesi için dolgu

        self.canvas = FigureCanvas(Figure(figsize=(8, 6))) # Daha iyi detay için daha büyük şekil
        self.canvas.figure.patch.set_facecolor('#f0f2f5') # Arka planla uyum için arka plan rengini eşleştir
        report_layout.addWidget(self.canvas)

        btn_plot = QtWidgets.QPushButton("Grafiği Yenile")
        btn_plot.clicked.connect(self.plot_report)
        report_layout.addWidget(btn_plot, alignment=QtCore.Qt.AlignCenter)
        tabs.addTab(report_tab, "Rapor")

    def toggle_pause(self):
        """Kamera akışını duraklatır veya devam ettirir."""
        self.paused = not self.paused
        if self.paused:
            self.btn_pause.setText("Devam Et")
            self.status_label.setText("Duraklatıldı.")
            self.status_label.setStyleSheet(
                "font-size:24px; font-weight:bold; padding:10px; border-radius:8px; "
                "margin-top:15px; color:white; background-color:#6c757d;" # Gri renk
            )
        else:
            self.btn_pause.setText("Duraklat")
            # Duraklatma bitince, status_label'ın stilini update_frame'in ayarlamasına bırak
            # İlk karede doğru stil tekrar uygulanacaktır.

    def start(self):
        """Video yakalamayı ve güncelleme zamanlayıcısını başlatır."""
        self.cap = cv2.VideoCapture(0) # Varsayılan kamerayı aç
        if not self.cap.isOpened():
            QtWidgets.QMessageBox.critical(self, "Kamera Hatası", "Kamera açılamadı. Lütfen kameranın bağlı ve başka bir uygulama tarafından kullanılmadığından emin olun.")
            sys.exit(1) # Kamera açılamazsa çık
        self.timer.start(30) # Her 30 milisaniyede bir güncelle (~33 FPS)
        self.show() # Ana pencereyi göster

    def update_frame(self):
        """Bir kare yakalar, işler ve UI'yı günceller."""
        if self.paused: # Duraklatılmışsa çerçeveyi güncelleme
            return

        ret, frame = self.cap.read()
        if not ret:
            # Kare okunamadığında durumu ele al (örn. kamera bağlantısı kesildi)
            self.status_label.setText("Kamera hatası: Görüntü alınamıyor.")
            self.status_label.setStyleSheet("font-size:24px; font-weight:bold; padding:10px; border-radius:8px; margin-top:15px; color:white; background-color:#dc3545;") # Kırmızı hata durumu
            return

        # UI kontrollerinden eşikleri ve düşük ışık modunu güncelle
        self.shoulder_thresh = self.sb_sh.value()
        self.angle_lower = self.sb_lo.value()
        self.angle_upper = self.sb_hi.value()
        self.neck_angle_lower = self.sb_na_lo.value() # Yeni: Boyun eşiğini al
        self.neck_angle_upper = self.sb_na_hi.value() # Yeni: Boyun eşiğini al
        self.low_light_mode = self.chk_ll.isChecked()

        # Düşük ışıkta kontrast artırma için CLAHE uygula
        if self.low_light_mode:
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            cl = self.clahe.apply(l)
            frame = cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2BGR)

        # PoseDetector ile kareyi işle
        # Yeni: Boyun eşiklerini de process metoduna gönder
        status, needs_correction, color_hex, val, landmarks = self.detector.process(
            frame, self.shoulder_thresh, self.angle_lower, self.angle_upper,
            self.neck_angle_lower, self.neck_angle_upper)

        # Durum arka plan renklerini tanımla
        status_bg_color_map = {
            "#28a745": "background-color: #28a745;", # İyi için Yeşil
            "#ffc107": "background-color: #ffc107;", # Uyarı için Sarı
            "#dc3545": "background-color: #dc3545;", # Kötü için Kırmızı
            "#6c757d": "background-color: #6c757d;"  # Bekleme/Algılama yok için Gri
        }
        status_bg_style = status_bg_color_map.get(color_hex, "background-color: #6c757d;") # Varsayılan olarak gri

        # Görüntülenecek resmi oluştur (iskelet kaplaması ile)
        img_display = frame.copy()
        if landmarks:
            try:
                mp_draw = __import__('mediapipe').solutions.drawing_utils
                mp_pose = __import__('mediapipe').solutions.pose
                mp_draw.draw_landmarks(
                    img_display, landmarks, mp_pose.POSE_CONNECTIONS,
                    mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2), # İskelet noktaları için yeşil noktalar
                    mp_draw.DrawingSpec(color=(255, 0, 0), thickness=2) # Bağlantılar için kırmızı çizgiler
                )
            except ImportError:
                print("MediaPipe kütüphanesi bulunamadı. İskelet çizimi atlanıyor.")
                # MediaPipe yüklü değilse iskelet çizmeden devam et
                pass

        # OpenCV görüntüsünü QLabel'da görüntülemek için QPixmap'e dönüştür
        rgb = cv2.cvtColor(img_display, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        q_img = QtGui.QImage(rgb.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(q_img).scaled(
            self.video_label.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation) # Yumuşak ölçeklendirme
        self.video_label.setPixmap(pixmap)

        # Durum metnini ve stilini güncelle
        unit = "px" if "Omuz" in status else "°"
        self.status_label.setText(f"{status}: {val:.1f} {unit}")
        self.status_label.setStyleSheet(f"font-size:24px; font-weight:bold; padding:10px; border-radius:8px; margin-top:15px; color:white; {status_bg_style}")

        # Düzeltme gerekiyorsa bildirim gönder
        if needs_correction:
            send_notification("Duruş Uyarısı", status)

        # Duruş verilerini logla
        log_posture(status, val)

    def calibrate(self):
        """
        Optimal eşikleri ayarlamak için 5 saniyelik bir kalibrasyon yapar.
        Bu kalibrasyon özellikle sırt açısı ve omuz farkı için tasarlanmıştır.
        Boyun açısı için manuel ayarlama gerekebilir veya ayrı bir kalibrasyon modu eklenebilir.
        """
        QtWidgets.QMessageBox.information(self, "Kalibrasyon Başladı", "Lütfen 5 saniye boyunca doğal duruşunuzu koruyun. Kamera verileriniz analiz ediliyor...")

        vals_angle = [] # Sırt açısı değerleri
        vals_shoulder = [] # Omuz farkı değerleri
        vals_neck = [] # Boyun açısı değerleri

        start_time = time.time()

        while time.time() - start_time < 5:
            ret, frm = self.cap.read()
            if not ret:
                QtWidgets.QMessageBox.warning(self, "Kalibrasyon Hatası", "Kameradan görüntü alınamadı. Kalibrasyon iptal edildi.")
                return # Kalibrasyon sırasında kamera arızalanırsa çık
            
            # Kalibrasyon için kareyi işle. Tüm eşikler geniş tutulur.
            # Burada dummy değerler yerine geniş aralıklar gönderiyoruz (0-180 derece, 0-1000 px)
            status, _, _, val, _ = self.detector.process(
                frm, 0, 0, 180, 0, 180) # Ham değerleri almak için çok gevşek eşikler kullanın
            
            # Gelen duruma göre değeri ilgili listeye ekle
            if val is not None and val >= 0: # Sadece geçerli, pozitif/sıfır değerleri dikkate al
                if "Omuz" in status:
                    vals_shoulder.append(val)
                elif "Sırt" in status or "Eğilme" in status or "Dik" in status or "Yaslanma" in status:
                    vals_angle.append(val)
                elif "Boyun" in status: # "Boyun Öne Eğik" veya "Boyun Arkaya Eğik" durumları için
                    vals_neck.append(val)

            QtWidgets.QApplication.processEvents() # Kalibrasyon döngüsü sırasında UI'yı yanıt vermeye devam ettir

        # Sırt Açısı Kalibrasyonu
        if vals_angle:
            avg_angle = sum(vals_angle) / len(vals_angle)
            self.sb_lo.setValue(max(0, int(avg_angle - 7))) # 7 derece alt tampon
            self.sb_hi.setValue(min(180, int(avg_angle + 7))) # 7 derece üst tampon
            QtWidgets.QMessageBox.information(self, "Kalibrasyon Tamamlandı", f"Sırt Açı eşikleri {self.sb_lo.value()}° - {self.sb_hi.value()}° aralığına ayarlandı.")
        else:
            QtWidgets.QMessageBox.warning(self, "Kalibrasyon Uyarısı", "Sırt açısı için yeterli veri toplanamadı. Lütfen kameranın düzgün çalıştığından ve vücudunuzun görünür olduğundan emin olun.")
        
        # Omuz Farkı Kalibrasyonu (Opsiyonel - genelde manuel ayar tercih edilir)
        if vals_shoulder:
            avg_shoulder = sum(vals_shoulder) / len(vals_shoulder)
            # Omuz eşiğini biraz yüksek tutarak hata payı bırak
            self.sb_sh.setValue(min(1000, int(avg_shoulder * 1.2) + 5)) # %20 tampon ve 5 px ek pay
            QtWidgets.QMessageBox.information(self, "Kalibrasyon Uyarısı", f"Omuz Farkı eşiği yaklaşık {self.sb_sh.value()} px olarak önerildi. İnce ayar için Ayarlar sekmesini kullanın.")
        else:
             QtWidgets.QMessageBox.warning(self, "Kalibrasyon Uyarısı", "Omuz farkı için yeterli veri toplanamadı.")

        # Boyun Açısı Kalibrasyonu (Manuel Ayar İpuçları)
        if vals_neck:
            avg_neck = sum(vals_neck) / len(vals_neck)
            # Boyun için varsayılan eşiklerin ortalamanın etrafında olmasını öner
            self.sb_na_lo.setValue(max(0, int(avg_neck - 5))) # 5 derece alt tampon
            self.sb_na_hi.setValue(min(180, int(avg_neck + 5))) # 5 derece üst tampon
            QtWidgets.QMessageBox.information(self, "Kalibrasyon Uyarısı", f"Boyun Açı eşikleri yaklaşık {self.sb_na_lo.value()}° - {self.sb_na_hi.value()}° aralığına önerildi. Lütfen Ayarlar sekmesinden bu değerleri manuel olarak kontrol edin ve kendi ideal duruşunuza göre ayarlayın.")
        else:
             QtWidgets.QMessageBox.warning(self, "Kalibrasyon Uyarısı", "Boyun açısı için yeterli veri toplanamadı.")


    def plot_report(self):
        """Duruş günlüğü verilerini okur ve rapor sekmesinde çizer, her zaman sadece güncel günün verilerini gösterir."""
        path = os.path.join("logs", f"posture_log_{self.username}.csv")

        # Çizim yapmadan veya hata göstermeden önce tuvali temizle
        self.canvas.figure.clear() 
        ax = self.canvas.figure.add_subplot(111) # Alt çizimi ekle, boş olsa bile
        ax.set_title("Günlük Duruş Zaman Serisi", fontsize=16, color='#2c3e50') # Varsayılan başlık
        ax.set_ylabel("Ölçülen Değer (Açı veya Piksel)", fontsize=12, color='#333333') # Etiket güncellendi
        ax.set_xlabel("Zaman Damgası", fontsize=12, color='#333333')
        ax.grid(True, linestyle='--', alpha=0.7)
        self.canvas.draw() # İlk boş çizimi çiz veya eski çizimi temizle

        if not os.path.isfile(path):
            QtWidgets.QMessageBox.information(self, "Rapor Yok", "Bugüne ait duruş verisi bulunamadı. Lütfen canlı izlemeyi başlatın ve bir süre kullanın.")
            return
        
        try:
            df = pd.read_csv(
                path,
                parse_dates=["timestamp"],
                encoding='utf-8', # Genellikle utf-8 daha yaygındır, latin1 yerine bunu deneyin.
                on_bad_lines='skip' # Hatalı biçimlendirilmiş satırları atla
            )
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Rapor Hatası", f"CSV okunurken hata oluştu: {e}\nDosyanın bozuk olmadığından veya kodlamasının doğru olduğundan emin olun (örn. UTF-8).")
            return

        # 'value' sütununun var olduğundan emin olun ve hataları NaN'a dönüştürerek sayısal değere çevirin
        if 'value' not in df.columns:
            QtWidgets.QMessageBox.warning(self, "Rapor Hatası", "Log dosyasında 'value' sütunu bulunamadı. Veri formatını kontrol edin.")
            return

        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df.dropna(subset=['value'], inplace=True) # 'value' NaN olan satırları (eksik veya sayısal olmayan) kaldır

        if df.empty:
            QtWidgets.QMessageBox.information(self, "Rapor Yok", "Bugüne ait çizilebilir veri bulunamadı.")
            return

        # Verileri güncel gün için filtrele
        today = pd.Timestamp.today().normalize()
        df_today = df[df['timestamp'].dt.date == today.date()]

        if df_today.empty:
            QtWidgets.QMessageBox.information(self, "Rapor Yok", "Bugüne ait çizilebilir veri bulunamadı.")
            return

        self.canvas.figure.clear() # Veri geçerliyse tekrar temizlemek için temizle
        ax = self.canvas.figure.add_subplot(111) # Alt çizimi ekle
        
        # 'value' değerini zamanla birlikte çizme
        ax.plot(df_today['timestamp'], df_today['value'], color='#3498db', linewidth=1.5)

        # Eşik çizgilerini duruma göre ekle
        if 'status' in df_today.columns:
            # Hangi eşiklerin gösterileceğine karar vermek için logdaki durum türlerini kontrol et
            has_shoulder_data = any("Omuz" in str(s) for s in df_today['status'].unique())
            has_angle_data = any("Sırt" in str(s) for s in df_today['status'].unique()) or any("Eğilme" in str(s) for s in df_today['status'].unique())
            has_neck_data = any("Boyun" in str(s) for s in df_today['status'].unique())

            if has_shoulder_data and self.shoulder_thresh is not None:
                ax.axhline(y=self.shoulder_thresh, color='red', linestyle='--', label='Omuz Eşiği')
            
            if has_angle_data:
                if self.angle_lower is not None:
                    ax.axhline(y=self.angle_lower, color='orange', linestyle=':', label='Sırt Açı Alt Eşiği')
                if self.angle_upper is not None:
                    ax.axhline(y=self.angle_upper, color='orange', linestyle=':', label='Sırt Açı Üst Eşiği')

            if has_neck_data:
                if self.neck_angle_lower is not None:
                    ax.axhline(y=self.neck_angle_lower, color='purple', linestyle='--', label='Boyun Açı Alt Eşiği')
                if self.neck_angle_upper is not None: # Üst eşiği de göstermek isterseniz
                     ax.axhline(y=self.neck_angle_upper, color='blue', linestyle=':', label='Boyun Açı Üst Eşiği')


        ax.set_title("Günlük Duruş Zaman Serisi", fontsize=16, color='#2c3e50')
        ax.set_ylabel("Ölçülen Değer (Açı veya Piksel)", fontsize=12, color='#333333')
        ax.set_xlabel("Zaman Damgası", fontsize=12, color='#333333')
        ax.tick_params(axis='x', rotation=45, labelbottom=True) # X ekseni etiketlerini döndür ve görünürlüğünü sağla
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend() # Eşik çizgileri için lejantı göster
        self.canvas.figure.tight_layout() # Etiketlerin/başlıkların çakışmasını önlemek için düzeni ayarla
        self.canvas.draw() # Yeni çizimle tuvali yeniden çiz

    def closeEvent(self, event):
        """Pencere kapanış olayını ele alır, zamanlayıcıyı durdurur ve kamerayı serbest bırakır."""
        self.timer.stop() # Güncelleme zamanlayıcısını durdur
        if self.cap:
            self.cap.release() # Kamerayı serbest bırak
        cv2.destroyAllWindows() # Herhangi bir OpenCV penceresini kapat (varsa)
        event.accept() # Kapanış olayını kabul et


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    # Kullanıcı adı için basit giriş iletişim kutusu
    # os.getenv("USERNAME") kolaylık sağlamak için sistemin kullanıcı adıyla önceden doldurmayı dener
    username, ok = QtWidgets.QInputDialog.getText(
        None, "Kullanıcı Girişi", "Lütfen kullanıcı adınızı girin:",
        QtWidgets.QLineEdit.Normal, os.getenv("USERNAME", "Kullanıcı") 
    )
    
    if not ok or not username:
        QtWidgets.QMessageBox.warning(None, "Giriş Hatası", "Kullanıcı adı girmeden devam edemezsiniz.")
        sys.exit(0) # Kullanıcı adı sağlanmazsa çık

    # Ana pencereyi oluştur ve göster
    main_window = MainWindow(username)
    main_window.start() # Uygulamayı başlat (kamera akışı ve UI)
    
    sys.exit(app.exec_()) # PyQt olay döngüsünü başlat
