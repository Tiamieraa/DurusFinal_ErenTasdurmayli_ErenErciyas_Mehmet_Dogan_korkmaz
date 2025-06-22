import csv
import os
from datetime import datetime

LOG_DIR = "logs"
if not os.path.isdir(LOG_DIR):
    os.makedirs(LOG_DIR)

# varsayılan kullanıcı dışı çağrı için
LOG_FILE = os.path.join(LOG_DIR, "posture_log.csv")

def set_user(username: str):
    """Aktif kullanıcının log dosyasını ayarlar."""
    global LOG_FILE
    # geçerli kullanıcı adı geçerli dosya adı olarak ayarlanır
    LOG_FILE = os.path.join(LOG_DIR, f"posture_log_{username}.csv")

def log_posture(status: str, value: float):
    """Status ve değeri (angle veya px diff) LOG_FILE'a yazar."""
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "status", "value"])
        writer.writerow([datetime.now().isoformat(), status, f"{value:.2f}"])
