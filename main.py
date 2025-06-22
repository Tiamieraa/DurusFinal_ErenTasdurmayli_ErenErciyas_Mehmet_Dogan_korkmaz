import sys
from PyQt5 import QtWidgets
from gui_qt import MainWindow

def main():
    app = QtWidgets.QApplication(sys.argv)
    # Basit kullanıcı girişi
    username, ok = QtWidgets.QInputDialog.getText(
        None, "Kullanıcı Girişi", "Kullanıcı adınızı girin:")
    if not ok or not username.strip():
        sys.exit(0)

    window = MainWindow(username.strip())
    window.start()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
input("Program kapandı. Devam etmek için Enter'a bas...")
