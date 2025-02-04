from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton


class Example(QWidget):
    def __init__(self):
        super().__init__()
        # Criar um layout vertical
        self.layout = QVBoxLayout()

        # Adicionar widgets ao layout
        self.label1 = QLabel("Widget 1")
        self.label2 = QLabel("Widget 2")
        self.label3 = QLabel("Widget 3")

        self.layout.addWidget(self.label1)
        self.layout.addWidget(self.label2)
        self.layout.addWidget(self.label3)

        # Botão para ocultar um widget
        self.button = QPushButton("Ocultar Widget 2")
        self.button.clicked.connect(self.hide_widget)
        self.layout.addWidget(self.button)

        # Configurar o layout no widget principal
        self.setLayout(self.layout)

    def hide_widget(self):
        # Ocultar o widget
        self.label2.hide()
        # Garantir que o layout seja atualizado
        self.layout.invalidate()


if __name__ == "__main__":
    app = QApplication([])
    window = Example()
    window.show()
    app.exec()
