import nidaqmx
import os
import matplotlib.pyplot as plt
import numpy as np

from ..uis.ui_PYDAQ_Digital_filterss_NIDAQ_widget import Ui_Digitalfilters_NIDAQ_widget

from ..guis.fir_window_widget import FirWindow
from ..guis.iir_window_widget import IrrWindow
from PySide6.QtWidgets import QFileDialog, QWidget

from ..get_data import GetData
from .error_window_gui import Error_window
from .warning_window_digital import Warning_window
from pydaq.utils.signals import GuiSignals
from PySide6.QtCore import Signal

class Digital_Filters_NIDAQ_Widget(QWidget, Ui_Digitalfilters_NIDAQ_widget):
    dataEntered = Signal(dict)
    def __init__(self, *args):
        super(Digital_Filters_NIDAQ_Widget, self).__init__()
        self.setupUi(self)
        self.signals = GuiSignals()
        self.iir_widget.hide()
        self.fir_widget.show()
        # Signals 
        self.type_filter.currentTextChanged.connect(self.check_filter)
        
        self.save_button.clicked.connect(self.send_data)
        
        self.yes_rt.toggled.connect(self.openWarningWindow)
        self.signals.returned.connect(self.frequency_response)
    
    def openWarningWindow(self):
        if self.yes_rt.isChecked():
            self.warningwindow = Warning_window(self)
            self.warningwindow.exec()
            
    def select_no(self):
        self.no_rt.setChecked(True)     
    
    def send_data(self):
        data = {
            "1": self.numtaps_fir.text()
        }
        self.dataEntered.emit(data)
        self.close()
       
    def check_filter(self, text):
        if text == 'FIR':
            self.fir_widget.show()
            self.iir_widget.hide()
        if text == 'IIR':
            self.iir_widget.show()
            self.fir_widget.hide()
    
    
    def frequency_response(self):
        if self.yes_fr.isChecked():
            # open the data.dat and time.dat and make the fft
            self.time_way = self.path_line.text() + '\\' + 'time.dat'
            self.data_way = self.path_line.text() + '\\' + 'data.dat'
            
            # load the archive
            self.time = np.loadtxt(self.time_way)
            self.data = np.loadtxt(self.data_way)
            
            # tests
            self.T = np.mean(np.diff(self.time))
            self.Fs = 1/self.T 
            
            self.N = len(self.data)
            
            self.fft_sinal = np.fft.fft(self.data)
            self.fft_sinal = np.abs(self.fft_sinal[:self.N//2])
            self.freqs = np.fft.fftfreq(self.N, self.T)[:self.N//2]
            
            plt.figure()
            plt.plot(self.freqs, self.fft_sinal)
            plt.plot(self.time, self.data)
            plt.xlabel('Frequency [Hz]')
            plt.ylabel('Amplitude')
            plt.title('Frequency Response')
            plt.grid()
            plt.show()
            
        else:
            return
    
            

