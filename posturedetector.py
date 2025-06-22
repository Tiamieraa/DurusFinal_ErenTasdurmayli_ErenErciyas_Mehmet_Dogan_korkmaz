import cv2
import mediapipe as mp
import numpy as np

class PoseDetector:
    def __init__(self,
                 min_detection_confidence=0.5,
                 min_tracking_confidence=0.5):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

    @staticmethod
    def calculate_angle(a, b, c):
        """Üç nokta arasındaki açıyı hesaplar (b noktası ortadaki köşe noktasıdır)."""
        a = np.array(a); b = np.array(b); c = np.array(c)
        ba = a - b; bc = c - b
        cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        return np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))

    def process(self, frame, shoulder_thresh, angle_lower, angle_upper, neck_angle_lower, neck_angle_upper):
        """
        Bir kareyi işler, duruşu analiz eder ve sonuçları döndürür.

        Args:
            frame (numpy.ndarray): İşlenecek video karesi.
            shoulder_thresh (float): Omuz farkı eşiği (piksel).
            angle_lower (int): Kalça-diz açısı alt eşiği (derece).
            angle_upper (int): Kalça-diz açısı üst eşiği (derece).
            neck_angle_lower (int): Boyun açısı alt eşiği (derece).
            neck_angle_upper (int): Boyun açısı üst eşiği (derece).

        Returns:
            tuple: (durum metni, düzeltme gerekli mi, renk kodu, ölçülen değer, iskelet noktaları)
        """
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image_rgb)

        # Eğer kişi algılanamazsa
        if not results.pose_landmarks:
            return "Kişi Algılanamadı", False, "#6c757d", 0, None # Gri renk, nötr durum

        lm = results.pose_landmarks.landmark
        h, w, _ = frame.shape # Kare boyutlarını al

        # Omuz Y koordinatlarını al
        yL_shoulder = lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y * h
        yR_shoulder = lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].y * h
        shoulder_diff = abs(yL_shoulder - yR_shoulder)

        # 1. Omuz Hizası Kontrolü (öncelikli)
        if shoulder_diff > shoulder_thresh:
            return "Omuz Hizası Bozuk", True, "#dc3545", shoulder_diff, results.pose_landmarks # Kırmızı renk

        # 2. Boyun Açısı Kontrolü (kulak-omuz-kalça hattı)
        # Sol taraf landmarklarını al (sağ taraf da kullanılabilir, simetri önemlidir)
        try:
            left_ear_coords = [lm[self.mp_pose.PoseLandmark.LEFT_EAR].x * w, lm[self.mp_pose.PoseLandmark.LEFT_EAR].y * h]
            left_shoulder_coords = [lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER].x * w, lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y * h]
            left_hip_coords = [lm[self.mp_pose.PoseLandmark.LEFT_HIP].x * w, lm[self.mp_pose.PoseLandmark.LEFT_HIP].y * h]

            # Landmarkların algılanıp algılanmadığını basitçe kontrol et (sıfır olmayan koordinatlar)
            # MediaPipe genellikle landmarkları bulamayınca 0 döndürmez, ancak görünürlük kontrolü daha sağlamdır.
            # Burada basit bir sıfır kontrolü yapıyoruz.
            if (left_ear_coords[0] != 0 or left_ear_coords[1] != 0) and \
               (left_shoulder_coords[0] != 0 or left_shoulder_coords[1] != 0) and \
               (left_hip_coords[0] != 0 or left_hip_coords[1] != 0):
                
                neck_angle = self.calculate_angle(left_ear_coords, left_shoulder_coords, left_hip_coords)

                # Boyun öne eğik ise (açı alt eşikten küçükse)
                if neck_angle < neck_angle_lower:
                    return "Boyun Öne Eğik", True, "#dc3545", neck_angle, results.pose_landmarks # Kırmızı renk
                # Boyun çok fazla geriye eğik ise (istenen üst eşiğin üzerindeyse)
                elif neck_angle > neck_angle_upper:
                    return "Boyun Arkaya Eğik", True, "#ffc107", neck_angle, results.pose_landmarks # Sarı renk
                # Boyun ideal aralıktaysa, diğer kontrolleri atlamamak için pas geçilir
                # ve sonraki sırt açısı kontrolüne bırakılır.
                # Aksi takdirde, sürekli "Dik Durma" veya benzeri bir boyun durumu mesajı gönderilebilir,
                # ancak genel duruş değerlendirmesini sırt açısı belirlesin istiyoruz.
                pass

        except Exception as e:
            # Landmarkların bulunamaması veya hesaplama hatası durumunda, boyun kontrolünü atla
            # print(f"Boyun açısı hesaplanırken hata oluştu: {e}. Landmarklar bulunamadı.")
            pass # Diğer kontrollere devam et

        # 3. Sırt Açısı Kontrolü (kalça-diz açısı)
        # Sol taraf landmarklarını kullanarak açıyı hesapla
        shoulder_hip_knee_angle = 0 # Varsayılan değer, eğer landmarklar bulunamazsa
        try:
            shoulder_coords = [lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER].x * w, yL_shoulder]
            hip_coords = [lm[self.mp_pose.PoseLandmark.LEFT_HIP].x * w, lm[self.mp_pose.PoseLandmark.LEFT_HIP].y * h]
            knee_coords = [lm[self.mp_pose.PoseLandmark.LEFT_KNEE].x * w, lm[self.mp_pose.PoseLandmark.LEFT_KNEE].y * h]

            if (shoulder_coords[0] != 0 or shoulder_coords[1] != 0) and \
               (hip_coords[0] != 0 or hip_coords[1] != 0) and \
               (knee_coords[0] != 0 or knee_coords[1] != 0):
                
                shoulder_hip_knee_angle = self.calculate_angle(shoulder_coords, hip_coords, knee_coords)

                if shoulder_hip_knee_angle < angle_lower:
                    return "Öne Eğilme (Sırt)", True, "#dc3545", shoulder_hip_knee_angle, results.pose_landmarks # Kırmızı renk
                elif shoulder_hip_knee_angle > angle_upper:
                    return "Arkaya Yaslanma (Sırt)", True, "#ffc107", shoulder_hip_knee_angle, results.pose_landmarks # Sarı renk
                else:
                    return "Dik Durma", False, "#28a745", shoulder_hip_knee_angle, results.pose_landmarks # Yeşil renk

        except Exception as e:
            # print(f"Kalça-Diz açısı hesaplanırken hata oluştu: {e}. Landmarklar bulunamadı.")
            pass # Varsayılan olarak "Bekleniyor" veya diğer kontrolleri bekle

        # Hiçbir problem tespit edilmezse veya tüm gerekli landmarklar bulunamazsa varsayılan durum
        return "Bekleniyor", False, "#6c757d", 0, results.pose_landmarks # Gri renk
