import sys
import serial.tools.list_ports
import matplotlib.pyplot as plt
import matplotlib.animation as aplt
import numpy as np
from PySide6 import QtWidgets
from ui.ui_main import Ui_DigitalFilters
from ui.ui_graphwindow import Ui_GraphWindow
from ui.imgs.recursos_rc import *
from PySide6.QtCore import QTimer


# O que fazer:
# Identificar qual porta está selecionada no combo-box
# 

class MainWindow(QtWidgets.QMainWindow, Ui_DigitalFilters):
    def __init__(self):
        super(MainWindow, self).__init__()
        
        self.setupUi(self)
        self.setWindowTitle("PYDAQ - Digital Filters")
        
        self.reload() # call the reload function
        
        # IIR and FIR checkbox funtions
        self.firButton.clicked.connect(self.filters)
        self.iirButton.clicked.connect(self.filters)
        
        self.locate_arduino() # call the locate arduino funcion
        
        # Close and Filter Button functions
        self.closeButton.clicked.connect(self.close)
        self.filterButton.clicked.connect(self.graphic)
        
        # Update the current text on the comboBox
        self.comboBox.currentTextChanged.connect(self.update_current_selection)
        
        self.porta = None
        
        self.ani = None
        
        
    def locate_arduino(self):  # function that locate arduino 
        current_selection = self.comboBox.currentText()
        self.comboBox.clear()
        ports = serial.tools.list_ports.comports()

        for port in ports:
            self.comboBox.addItem(f"{port.device} - {port.description}")
        
        if current_selection:
            index = self.comboBox.findText(current_selection)
            if index != -1:
                self.comboBox.setCurrentIndex(index)
        
        
    def filters(self):
        self.update_current_selection()
        
        if self.firButton.isChecked():
            print("You selected FIR")
            print(self.porta)
                  
        if self.iirButton.isChecked():
            print("You selected IIR")
            print(self.porta)
            
    def reload(self): # Call QTimer to search arduino in every 1 second
        self.timer = QTimer()
        self.timer.timeout.connect(self.locate_arduino)
        self.timer.start(1000)
        
    def update_current_selection(self):
        current_text = self.comboBox.currentText()
        if current_text:
            self.porta = current_text.split(' - ')[0]
            
    def graphic(self):
        self.update_current_selection()
        ser = serial.Serial(self.porta, 9600)
        # Inicialização da figura do matplotlib
        
        x = np.linspace(0, 2 * np.pi, 100)
        y = np.sin(x)

        # Criando o gráfico
        plt.figure(figsize=(8, 4))
        plt.plot(x, y, label='Seno')
        plt.title('Gráfico de uma Função Senoide')
        plt.xlabel('Eixo X')
        plt.ylabel('Eixo Y')
        plt.legend()
        plt.grid(True)

        # Mostrando o gráfico
        plt.show()
        
    
app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())

  