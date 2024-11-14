import os
import nidaqmx

import numpy as np
import matplotlib.pyplot as plt


from PySide6.QtWidgets import QFileDialog, QWidget
from pydaq.utils.signals import GuiSignals
from scipy.signal import firwin, lfilter, freqz

from ..uis.ui_PyDAQ_get_data_NIDAQ_widget import Ui_NIDAQ_GetData_W
from ..guis.digital_filters_nidaq_widget import Digital_Filters_NIDAQ_Widget

from .error_window_gui import Error_window
from ..get_data import GetData

class GetData_NIDAQ_Widget(QWidget, Ui_NIDAQ_GetData_W):
    def __init__(self, *args):
        super(GetData_NIDAQ_Widget, self).__init__()
        self.setupUi(self)

        # Gathering nidaq info
        self._nidaq_info()

        try:
            chan = nidaqmx.system.device.Device(
                self.device_names[0]
            ).ai_physical_chans.channel_names
            defchan = chan[0]

        except BaseException:
            chan = ""
            defchan = ""

        # Setting the starting values for some widgets
        self.device_combo.addItems(self.device_type)
        self.channel_combo.addItems(chan)
        self.path_line_edit.setText(
            os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")
        )
        self.terminal_config_combo.addItems(["Diff", "RSE", "NRSE"])

        defchan_index = self.channel_combo.findText(defchan)

        if defchan_index == -1:
            pass
        else:
            self.channel_combo.setCurrentIndex(defchan_index)

        # Connecting Signals
        self.path_folder_browse.released.connect(self.locate_path)
        self.start_get_data.released.connect(self.start_func_get_data)
        self.device_combo.currentIndexChanged.connect(self.update_channels)
        self.reload_devices.released.connect(self.reload_devices_handler)
        self.filter_button.released.connect(self.fir_project)
        self.yes_radio.toggled.connect(self.openFilterWindow)
        #self.teste.released.connect(self.update_values)
        self.signals = GuiSignals()
        
        
    def openFilterWindow(self):
        if self.yes_radio.isChecked(): 
            self.filterWindow = Digital_Filters_NIDAQ_Widget()
            self.filterWindow.dataEntered.connect(self.update_values)
            self.filterWindow.show()
            
    def update_values(self, data):
        self.numtapsfir = data['numtaps_fir']
        self.numtapsfir = int(self.numtapsfir)
        self.fsfir = data['fs_fir']
        self.fsfir = float(self.fsfir)
        self.cutofffir = data['Cutoff']
        self.cutofffir = float(self.cutofffir)
        self.type = data['Type']
        self.path = data['Path']
        
        
    def fir_project(self):
        self.time_way = self.path + "\\" + "time.dat"
        self.data_way = self.path + "\\" + "data.dat"
        
        self.time = np.loadtxt(self.time_way)
        self.data = np.loadtxt(self.data_way)
        
        self.fs = 1/np.mean(np.diff(self.time))
        
        fir_coeff = firwin(self.numtapsfir, self.cutofffir, window='hamming', fs=self.fs)
        filtered_signal = lfilter(fir_coeff, 1.0, self.data)

        plt.figure(figsize=(10,6))
        plt.subplot(2,1,1)
        plt.plot(self.time, self.data, label = 'Sinal original')
        plt.title('Sinal Original')
        plt.xlabel('Tempo [s]')
        plt.ylabel('Amplitude')
        plt.grid()

        plt.subplot(2,1,2)
        plt.plot(self.time, filtered_signal, label='Sinal Filtrado', color='r')
        plt.grid()

        plt.tight_layout()
        plt.show()
        
     
    def locate_path(self):  # Calling the Folder Browser Widget
        output_folder_path = QFileDialog.getExistingDirectory(
            self, caption="Choose a folder to save the data file"
        )
        if output_folder_path == "":
            pass
        else:
            self.path_line_edit.setText(output_folder_path.replace("/", "\\"))

   
    
    def start_func_get_data(self):  # Start getting data
        try:
            # Instantiating the GetData class
            g = GetData()

            # Separating variables
            g.device = self.channel_combo.currentText().split("/")[0]
            g.channel = self.channel_combo.currentText().split("/")[1]
            g.terminal = g.term_map[self.terminal_config_combo.currentText()]
            g.ts = self.Ts_in.value()
            g.session_duration = self.sesh_dur_in.value()
            g.plot = True if self.plot_radio_group.checkedId() == -2 else False
            g.save = True if self.save_radio_group.checkedId() == -2 else False
            g.path = self.path_line_edit.text()

            # Checking if a path was set
            if self.path_line_edit.text() == "":
                raise BaseException

            # Restarting variables
            g.data = []
            g.time_var = []
            g.error_path = False

        except BaseException:
            error_w = Error_window()
            error_w.exec()
            g.error_path = True

        if not g.error_path:
            # Calling data aquisition method
            g.get_data_nidaq()
            self.signals.returned.emit(g)

    def _nidaq_info(self):
        """Gathering NIDAQ info"""

        # Getting all available devices
        self.device_names = []
        self.device_categories = []
        self.device_type = []
        self.local_system = nidaqmx.system.System.local()

        for device in self.local_system.devices:
            self.device_names.append(device.name)
            self.device_categories.append(device.product_category)
            self.device_type.append(device.product_type)

    def update_channels(self):
        # Changing availables channels if device changes
        new_ai_channels = nidaqmx.system.device.Device(
            self.device_names[self.device_type.index(self.device_combo.currentText())]
        ).ai_physical_chans.channel_names

        # Default channel
        try:
            default_channel = new_ai_channels[0]
        except BaseException:
            default_channel = "There is no analog input in this board"

        # Rewriting new ai channels into the right place
        self.channel_combo.clear()
        self.channel_combo.addItems(new_ai_channels)
        defchan_index = self.channel_combo.findText(default_channel)

        if defchan_index == -1:
            pass
        else:
            self.channel_combo.setCurrentIndex(defchan_index)

    def reload_devices_handler(self):
        """Updates the devices combo box"""
        self._nidaq_info()

        # If the signal is not disconnect, it will run into a warning
        self.device_combo.currentIndexChanged.disconnect(self.update_channels)

        # Updating items on combo box
        self.device_combo.clear()
        self.device_combo.addItems(self.device_type)

        # Reconnecting the signal
        self.device_combo.currentIndexChanged.connect(self.update_channels)

    