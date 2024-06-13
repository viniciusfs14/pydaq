import sys
import serial.tools.list_ports
import matplotlib.pyplot as plt
import matplotlib.animation as aplt
from PySide6 import QtWidgets
from ui.ui_main import Ui_DigitalFilters
from ui.ui_graphwindow import Ui_GraphWindow
from ui.imgs.recursos_rc import *
from PySide6.QtCore import QTimer


class MainWindow(QtWidgets.QMainWindow, Ui_DigitalFilters):
    def __init__(self):
        super(MainWindow, self).__init__()
        
        self.setupUi(self)
        self.setWindowTitle("PYDAQ - Digital Filters")
        
        self.reload() # call the reload function
        
        self.firButton.clicked.connect(self.filters)
        self.iirButton.clicked.connect(self.filters)
        
        self.locate_arduino() # call the locate arduino funcion
        self.closeButton.clicked.connect(self.close)
        self.filterButton.clicked.connect(self.graphic)
        
        
        
    def locate_arduino(self):  # function that locate arduino 
        self.comboBox.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.comboBox.addItem(f"{port.device} - {port.description}")
        return ports
    
    
    def filters(self):
        if self.firButton.isChecked():
            print("You selected FIR")
      
        if self.iirButton.isChecked():
            print("You selected IIR")
            
    def reload(self): # Call QTimer to search arduino in every 1 second
        self.timer = QTimer()
        self.timer.timeout.connect(self.locate_arduino)
        self.timer.start(1000)
        
    def graphic(self):
       
        x = [1, 2, 3, 4, 5]
        y = [10, 15, 13, 18, 16]

        # Criar o gráfico
        plt.plot(x, y, marker='o')

        # Adicionar título e rótulos aos eixos
        plt.title('Exemplo de Gráfico de Linha')
        plt.xlabel('Eixo X')
        plt.ylabel('Eixo Y')

        # Exibir o gráfico
        plt.show()
        
    
    
app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())

  