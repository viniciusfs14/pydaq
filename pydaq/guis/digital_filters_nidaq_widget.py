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

    # Function to send the variables to get data window
    def send_data(self):
        data = {
            "numtaps_fir": self.order_fir.text(),
            "Cutoff": self.cutoff_fir.text(),
            "Type": self.comboBox.currentText(),
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
    

    
            

