import os
import warnings

import numpy as np
import matplotlib.pyplot as plt

from PySide6.QtWidgets import QFileDialog, QWidget, QMenu
from PySide6.QtGui import QAction
from pydaq.utils.base import Base, NIDAQ_AVAILABLE, TerminalConfiguration, nidaqmx, System

from pydaq.utils.signals import GuiSignals
from scipy.signal import firwin, lfilter, freqz
import scipy.signal as signal

from ..uis.ui_PyDAQ_get_data_NIDAQ_widget import Ui_NIDAQ_GetData_W
from ..guis.digital_filters_nidaq_widget import Digital_Filters_NIDAQ_Widget

from .error_window_gui import Error_window
from ..get_data import GetData

from scipy.signal import lfilter, butter, firwin, cheby1, cheby2, ellip

class GetData_NIDAQ_Widget(QWidget, Ui_NIDAQ_GetData_W):
    def __init__(self, *args):
        super(GetData_NIDAQ_Widget, self).__init__()
        self.setupUi(self)

        # Gathering nidaq info
        self._nidaq_info()

        try:
            if NIDAQ_AVAILABLE and len(self.device_names) > 0:
                chan = nidaqmx.system.device.Device(
                    self.device_names[0]
                ).ai_physical_chans.channel_names
                defchan = chan[0]
            else:
                chan = []
                defchan = ""
        except BaseException:
            chan = []
            defchan = ""

        except BaseException:
            chan = ""
            defchan = ""

        # Setting the starting values for some widgets
        self.device_combo.addItems(self.device_type)
        self.available_channels = chan
        self._setup_channel_selector()

        self.path_line_edit.setText(
            os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")
        )
        self.terminal_config_combo.addItems(["Diff", "RSE", "NRSE"])

        # Connecting Signals
        self.path_folder_browse.released.connect(self.locate_path)
        self.start_get_data.released.connect(self.start_func_get_data)
        self.device_combo.currentIndexChanged.connect(self.update_channels)
        self.reload_devices.released.connect(self.reload_devices_handler)
        self.yes_radio.clicked.connect(self.openFilterWindow)
        self.signals = GuiSignals()
        self.label_warning.hide()
        self.plot_radio_group.buttonToggled.connect(self._update_warning_label)

    def _update_warning_label(self):
        if self.yes_rt_plot_radio.isChecked():
            self.label_warning.show()
        else:
            self.label_warning.hide()
    
    def _setup_channel_selector(self):
        self.channel_combo.setEditable(True)
        self.channel_combo.lineEdit().setReadOnly(True)
        self.channel_combo.lineEdit().setPlaceholderText("No channels available")

        self.channel_menu = QMenu(self)
        self.channel_actions = []

        for ch in self.available_channels:
            action = QAction(ch, self)
            action.setCheckable(True)
            action.toggled.connect(self._update_channel_text)
            self.channel_menu.addAction(action)
            self.channel_actions.append(action)

        self.channel_combo.showPopup = self._show_channel_menu

        if self.channel_actions:
            self.channel_actions[0].setChecked(True)
        else:
            self.channel_combo.lineEdit().clear()
                
    def _show_channel_menu(self):
        self.channel_menu.exec(
            self.channel_combo.mapToGlobal(
                self.channel_combo.rect().bottomLeft()
            )
        )

    def _update_channel_text(self):
        selected = self.get_selected_channels()

        # Garante que ao menos 1 canal fique marcado
        if not any(a.isChecked() for a in self.channel_actions):
            self.channel_actions[0].setChecked(True)
            selected = [self.channel_actions[0].text()]

        self.channel_combo.lineEdit().setText(", ".join(selected))


    def get_selected_channels(self):
        selected = [a.text() for a in self.channel_actions if a.isChecked()]
        return selected if selected else [self.available_channels[0]]
            
    def openFilterWindow(self):
        self.filterWindow = Digital_Filters_NIDAQ_Widget()
        self.filterWindow.dataEntered.connect(self.update_values)
        self.filterWindow.show()
            
    def update_values(self, data):
        # type of filter
        self.filter = data['filter']
        
        # FIR values
        self.orderfir = data['numtaps_fir']
        self.orderfir = int(self.orderfir)
        
        self.cutofffir = data['Cutoff']
        self.cutofffir = float(self.cutofffir)
        
        self.fc1 = data['Fc1']
        self.fc1 = float(self.fc1)
        
        self.fc2 = data['Fc2']
        self.fc2 = float(self.fc2)
        
        self.design = data['design']
        self.type = data['type']
        self.fr = data['fr']
        
        # IIR values
        self.orderiir = data['numtaps_iir']
        self.orderiir = int(self.orderiir)
        
        self.cutoffiir = data['Cutoff_iir']
        self.cutoffiir = float(self.cutoffiir)
        
        self.design_iir = data['design_iir']
        self.type_irr = data['type_iir']
        
        self.rp = data['rp']
        self.rp = int(self.rp)
        
        self.rs = data['rs']
        self.rs = int(self.rs)
     
    def locate_path(self):  # Calling the Folder Browser Widget
        output_folder_path = QFileDialog.getExistingDirectory(
            self, caption="Choose a folder to save the data file"
        )
        if output_folder_path == "":
            pass
        else:
            self.path_line_edit.setText(output_folder_path.replace("/", "\\"))

    def start_func_get_data(self):  # Start getting data
        
        # Safety lock: prevents dialog from opening if NI-DAQmx drivers are not found
        if not NIDAQ_AVAILABLE:
            warnings.warn("[PYDAQ] NI-DAQmx drivers not found! Cannot start hardware control.")
            error_w = Error_window()
            error_w.ui.confirm.setText("NI-DAQmx drivers not found! Please install NI-MAX.")
            error_w.exec()
            return

        try:
            # Instantiating the GetData class
            g = GetData()

            # Separating variables
            selected = self.get_selected_channels() 

            # Checking if a path was set
            if self.path_line_edit.text() == "":
                raise ValueError("[PYDAQ] Missing configuration: Empty save path.")

            g.path = self.path_line_edit.text()

            if selected:
                g.device = selected[0].split("/")[0]
                # Sending the list of channel names (e.g., ["ao0", "ao1"])
                g.channels = [ch.split("/")[1] for ch in selected]
            else:
                raise ValueError("[PYDAQ] Missing configuration: Please ensure device and channel are properly defined.")

            g.terminal = g.term_map[self.terminal_config_combo.currentText()]
            g.ts = self.Ts_in.value()
            g.session_duration = self.sesh_dur_in.value()
            if self.yes_rt_plot_radio.isChecked(): # Assumindo que 'yes_radio' agora significa 'Real time'
                g.plot_mode = 'realtime'
            elif self.yes_ate_plot_radio.isChecked(): # Supondo que você criou um radio button com este nome
                g.plot_mode = 'end'
            else: # self.No_radio.isChecked()
                g.plot_mode = 'no'
            g.save = True if self.save_radio_group.checkedId() == -2 else False

            # Restarting variables
            g.data = []
            g.time_var = []
            g.error_path = False

        except BaseException as e :
            # Standardized GUI Error Window
            if str(e): # Only warn if there is a specific message
                warnings.warn(str(e))

            error_w = Error_window()
            error_w.ui.confirm.setText("Missing configuration: Please ensure device, channel, and path are properly defined.")
            error_w.exec()

            g.error_path = True
            return

        # this conditional checks if will have filter or not
        if not g.error_path:
            if self.No_radio.isChecked():
                g.get_data_nidaq()
                self.signals.returned.emit(g)
            else:
                fs = (1/float(self.Ts_in.value()))*2.5
                if self.filter == 'FIR':
                    
                    fc_fir = self.cutofffir
                    numtaps_fir = self.orderfir
                    window_fir = self.design
                    type_fir = self.type
                    
                    if window_fir == 'Blackman':
                        window_fir = 'blackman'
                        
                    elif window_fir == 'Hamming':
                        window_fir = 'hamming'
                    
                    elif window_fir == 'Hann':
                        window_fir = 'hann'
                        
                    elif window_fir == 'Bartlett-Hann':
                        window_fir = 'barthann'
                        
                    elif window_fir == 'Kaiser':
                        window_fir = 'kaiser'
                        
                    elif window_fir == 'Gauss':
                        window_fir == 'gauss'
                        
                    if type_fir == 'bandstop':
                        fc1 = self.fc1
                        fc2 = self.fc2
                        self.fir_coeff = firwin(numtaps_fir, [fc1/(0.5*fs), fc2/(0.5*fs)], window=window_fir, pass_zero='bandstop')

                    elif type_fir == 'bandpass':
                        fc1 = self.fc1
                        fc2 = self.fc2
                        self.fir_coeff = firwin(numtaps_fir, [fc1/(0.5*fs), fc2/(0.5*fs)], window=window_fir, pass_zero='bandpass')

                    else:
                        self.fir_coeff = firwin(numtaps_fir, fc_fir/(0.5*fs), window=window_fir, pass_zero=type_fir)
                    g.get_data_nidaq(filter_coefs=(self.fir_coeff))
                    self.signals.returned.emit(g)
                    self.frequency_response()
                
                elif self.filter == 'IIR':
                    # Create the project of IIR filter
                    fc_iir = self.cutoffiir
                    numtaps_iir = self.orderiir
                    window_iir = self.design_iir
                    type_iir = self.type_irr
                    rp = self.rp 
                    rs = self.rs
                    
                    if window_iir == 'Chebyshev Type I':
                        self.b, self.a = cheby1(numtaps_iir, rp, fc_iir/(0.5*fs), btype=type_iir)
                        
                    elif window_iir == 'Chebyshev Type II':
                        self.b, self.a = cheby2(numtaps_iir, rs, fc_iir/(0.5*fs), btype=type_iir)
                        
                    elif window_iir == 'Butterworth':
                        self.b, self.a = butter(numtaps_iir, fc_iir/(0.5*fs), btype=type_iir)
                        
                    elif window_iir == 'Elliptic':
                        self.b, self.a = ellip(numtaps_iir, rp, rs, fc_iir/(0.5*fs), btype=type_iir)
                    g.get_data_nidaq(filter_coefs=(self.b, self.a))
                    self.signals.returned.emit(g)
                    self.frequency_response()

    def _nidaq_info(self):
        """Gathering NIDAQ info"""

        # Getting all available devices
        self.device_names = []
        self.device_categories = []
        self.device_type = []

        if not NIDAQ_AVAILABLE:
            return
        
        self.local_system = nidaqmx.system.System.local()

        for device in self.local_system.devices:
            self.device_names.append(device.name)
            self.device_categories.append(device.product_category)
            self.device_type.append(device.product_type)

    def update_channels(self):
        
        try:
            dev_name = self.device_names[
                self.device_type.index(self.device_combo.currentText())
            ]
            
            if NIDAQ_AVAILABLE:
                new_ai_channels = nidaqmx.system.device.Device(dev_name).ai_physical_chans.channel_names
            else:
                new_ai_channels = []
        except BaseException:
            new_ai_channels = []

        self.available_channels = new_ai_channels

        # Recreate the channel menu
        self.channel_menu.clear()
        self.channel_actions = []

        for ch in self.available_channels:
            action = QAction(ch, self)
            action.setCheckable(True)
            action.toggled.connect(self._update_channel_text)
            self.channel_menu.addAction(action)
            self.channel_actions.append(action)

        # Select the first channel by default if available
        if self.channel_actions:
            self.channel_actions[0].setChecked(True)
        else:
            self.channel_combo.lineEdit().clear()

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

    def frequency_response(self):
        if self.fr == True:
            if self.filter == 'FIR':
                x = np.loadtxt(self.path_line_edit.text() + "\\" + "time.dat")
                y = np.loadtxt(self.path_line_edit.text() + "\\" + "data_filtered.dat")
                y2 = np.loadtxt(self.path_line_edit.text() + "\\" + "data.dat")
                
                if x.size < 2:
                    print("⚠️ Insufficient data to plot frequency response.")
                    return

                # --- Force 2D array for multi-channel support ---
                if x.ndim == 1: x = x.reshape(-1, 1)
                if y.ndim == 1: y = y.reshape(-1, 1)
                if y2.ndim == 1: y2 = y2.reshape(-1, 1)
                
                num_channels = y2.shape[1]
                
                ts = x[1, 0] - x[0, 0]
                fs = 1/ts
                
                w, h = signal.freqz(self.fir_coeff, 1.0, worN=None, fs=fs)
                mag = 20*np.log10(np.abs(h))
                phase = np.angle(h)
                
                dt = 1/(fs*2.5)  
                channels_selected = self.get_selected_channels()

                # Loop to calculate and create a figure for each channel
                for i in range(num_channels):
                    # Get channel name from self.channels securely

                    ch_name = channels_selected[i] if i < len(channels_selected) else f"CH {i}"
                    
                    orig_col = y2[:, i]
                    filt_col = y[:, i]

                    fft_data = np.fft.fft(orig_col)
                    freqs = np.fft.fftfreq(len(orig_col), dt)

                    fft_data_filtered = np.fft.fft(filt_col)

                    positive_freqs = freqs[:len(freqs) // 2]
                    fft_data_magnitude = np.abs(fft_data[:len(freqs) // 2])
                    fft_data_filtered_magnitude = np.abs(fft_data_filtered[:len(freqs) // 2])
                    
                    fft_data_magnitude_norm = (fft_data_magnitude/np.max(fft_data_magnitude))*100
                    fft_data_filtered_magnitude_norm = (fft_data_filtered_magnitude/np.max(fft_data_filtered_magnitude))*100
                    
                    # Create a new figure for this specific channel
                    plt.figure(figsize=(7,5))
                    
                    plt.subplot(2,1,1)
                    plt.plot(positive_freqs, fft_data_magnitude_norm, label=f'FFT Original ({ch_name})', color='r')
                    plt.title(f'Original Signal in Frequency - {ch_name}')
                    plt.xlabel('Frequency (Hz)')
                    plt.ylabel('Magnitude')
                    plt.legend()
                    plt.grid()
                    
                    plt.subplot(2,1,2)
                    plt.plot(positive_freqs, fft_data_filtered_magnitude_norm, label=f'FFT Filtered ({ch_name})', color='r')
                    plt.title(f'Filtered Signal in Frequency - {ch_name}')
                    plt.xlabel('Frequency (Hz)')
                    plt.ylabel('Magnitude')
                    plt.legend()
                    plt.grid()
                    
                    plt.tight_layout()
                
                # Show all created figures at once
                plt.show()
                
            else:
                x = np.loadtxt(self.path_line_edit.text() + "\\" + "time.dat")
                y = np.loadtxt(self.path_line_edit.text() + "\\" + "data_filtered.dat")
                y2 = np.loadtxt(self.path_line_edit.text() + "\\" + "data.dat")
                
                # --- Force 2D array for multi-channel support ---
                if x.ndim == 1: x = x.reshape(-1, 1)
                if y.ndim == 1: y = y.reshape(-1, 1)
                if y2.ndim == 1: y2 = y2.reshape(-1, 1)
                
                num_channels = y2.shape[1]
                
                ts = x[1, 0] - x[0, 0]
                fs = 1/ts
                
                w, h = signal.freqz(self.b, self.a, worN=None, fs=fs)
                mag = 20*np.log10(np.abs(h))
                phase = np.angle(h)
                
                dt = 1/(fs*2.5)  # 1/(fs*2)
                
                # Loop to calculate and create a figure for each channel
                for i in range(num_channels):
                    # Get channel name from self.channels securely
                    ch_name = self.channels[i] if hasattr(self, 'channels') and i < len(self.channels) else f"CH {i}"
                    
                    orig_col = y2[:, i]
                    filt_col = y[:, i]
                    
                    fft_data = np.fft.fft(orig_col)
                    freqs = np.fft.fftfreq(len(orig_col), dt)

                    fft_data_filtered = np.fft.fft(filt_col)

                    positive_freqs = freqs[:len(freqs) // 2]
                    fft_data_magnitude = np.abs(fft_data[:len(freqs) // 2])
                    fft_data_filtered_magnitude = np.abs(fft_data_filtered[:len(freqs) // 2])
                    
                    # Create a new figure for this specific channel
                    plt.figure(figsize=(7,5))
                    
                    plt.subplot(2,1,1)
                    plt.plot(positive_freqs, fft_data_magnitude, label=f'FFT Original ({ch_name})', color='r')
                    plt.title(f'Original Signal in Frequency - {ch_name}')
                    plt.xlabel('Frequency (Hz)')
                    plt.ylabel('Magnitude')
                    plt.legend()
                    plt.grid()
                    
                    plt.subplot(2,1,2)
                    # Note: I corrected the label here from 'FFT Original' to 'FFT Filtered' based on your original code's typo
                    plt.plot(positive_freqs, fft_data_filtered_magnitude, label=f'FFT Filtered ({ch_name})', color='r')
                    plt.title(f'Filtered Signal in Frequency - {ch_name}')
                    plt.xlabel('Frequency (Hz)')
                    plt.ylabel('Magnitude')
                    plt.legend()
                    plt.grid()
                    
                    plt.tight_layout()
                
                # Show all created figures at once
                plt.show()
        else:
            pass
    
    