import sys
import serial.tools.list_ports
import matplotlib.pyplot as plt
import matplotlib.animation as aplt
import numpy as np
import serial
from scipy import signal, fftpack
from PySide6 import QtWidgets
from ui.ui_main import Ui_DigitalFilters
from ui.ui_graphwindow import Ui_GraphWindow
from ui.imgs.recursos_rc import *
from PySide6.QtCore import QTimer


# O que fazer:
# Identificar qual porta está selecionada no combo-box

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
                
        if self.iirButton.isChecked():
            
            self.order = self.firOrder.text()
            self.fs = self.Fs.text()
            self.low_irr = self.lowfrequency.text()
            self.high_irr = self.highfrequency.text()
            self.type = self.comboBox_2.currentText()
            self.nyq = 0.5 * self.fs
            self.low = self.low_irr/self.nyq
            self.high = self.high_irr/self.nyq
            
            b, a = signal.iirfilter(self.order, [self.low, self.high], btype="band", analog=False, ftype=self.type)
            
    
            
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

        fig, (ax1, ax2) = plt.subplots(2,1)
        
        xs = []
        accel_x = []
        accel_y = []
        
        def animate(i, xs, accel_x, accel_y):
            line = ser.readline().decode('utf-8').strip()
            
            try: 
                ax_g, ay_g = map(float, line.split(','))
                
            except ValueError:
                print("dados invalidos")
                return
            
            xs.append(i)
            accel_x.append(ax_g)
            accel_y.append(ay_g)

            xs[:] = xs[-50:]
            accel_x[:] = accel_x[-50:]
            accel_y[:] = accel_y[-50:]

            ax1.clear()
            ax1.plot(xs, accel_x, label='Aceleração em X (g)')
            ax1.legend(loc='upper right')
            
            ax2.clear()
            ax2.plot(xs, accel_y, label='Aceleração em Y (g)')
            ax2.legend(loc='upper right')

            plt.xlabel('Tempo')
            ax1.set_ylabel('Aceleração em X (g)')
            ax2.set_ylabel('Aceleração em Y (g)')
            
        self.ani = aplt.FuncAnimation(fig, animate, fargs=(xs, accel_x, accel_y), interval=100, cache_frame_data=False)

        plt.tight_layout()
        plt.show()
        
            
app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())

  