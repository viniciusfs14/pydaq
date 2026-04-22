import sys
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtGui import QPixmap

# Se isso falhar, o arquivo rc não está na mesma pasta
import resources_1_rc 

app = QApplication(sys.argv)
label = QLabel()

# Tenta carregar a imagem da memória
pixmap = QPixmap(":/imgs/imgs/logo.png")

if pixmap.isNull():
    label.setText("FALHOU: A imagem não está na memória. O prefixo ou caminho estão errados no .qrc.")
else:
    label.setPixmap(pixmap)
    label.setWindowTitle("SUCESSO!")

label.show()
sys.exit(app.exec())