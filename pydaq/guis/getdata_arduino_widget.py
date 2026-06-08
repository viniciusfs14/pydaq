import os
import warnings
import serial
import serial.tools.list_ports

from PySide6.QtWidgets import QFileDialog, QWidget, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from pydaq.utils.base import Base, ClickableLineEdit
from pydaq.utils.signals import GuiSignals
import scipy.signal as signal

from ..uis.ui_PyDAQ_get_data_Arduino_widget import Ui_Arduino_GetData_W
from ..guis.digital_filters_nidaq_widget import Digital_Filters_NIDAQ_Widget
from .error_window_gui import Error_window
from ..get_data import GetData

from scipy.signal import lfilter, butter, firwin, cheby1, cheby2, ellip, freqz

import numpy as np
import matplotlib.pyplot as plt

class GetData_Arduino_Widget(QWidget, Ui_Arduino_GetData_W): 
    def __init__(self, *args):
        super(GetData_Arduino_Widget, self).__init__()
        self.setupUi(self) 

        # Connecting Signals
        self.reload_devices.released.connect(self.update_com_ports)
        self.path_folder_browse.released.connect(self.locate_path)
        self.start_get_data.released.connect(self.start_func_get_data)
        self.signals = GuiSignals()
        self.label_warning.hide()
        self.plot_radio_group.buttonToggled.connect(self._update_warning_label)

        # Setting the starting values for some widgets
        self.update_com_ports()
        self.path_line_edit.setText(
            os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")
        )
        self.yes_radio.clicked.connect(self.openFilterWindow)

        # Channel selection
        self.available_channels = [f"A{i}" for i in range(6)]
        self._setup_channel_selector()

    def _update_warning_label(self):
        if self.yes_rt_plot_radio.isChecked():
            self.label_warning.show()
        else:
            self.label_warning.hide()
            
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

    def update_com_ports(self):  # Updating com ports
        self.com_ports = [i.description for i in serial.tools.list_ports.comports()]
        selected = self.device_combo.currentText()

        self.device_combo.clear()
        self.device_combo.addItems(self.com_ports)
        index_current = self.device_combo.findText(selected)

        if index_current == -1:
            pass
        else:
            self.device_combo.setCurrentIndex(index_current)

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

            # Checking if a path was set
            if self.yes_save_radio.isChecked() and self.path_line_edit.text() == "":
                raise ValueError("[PYDAQ] Missing configuration: Empty save path.")

            g.path = self.path_line_edit.text()

            # Getting the values from the GUI
            try:
                g.com_port = serial.tools.list_ports.comports()[
                    self.com_ports.index(self.device_combo.currentText())
                ].name
                #g.com_port = serial.tools.list_ports.comports()[999].name # Test Error
            except (ValueError, IndexError):
                raise ValueError("[PYDAQ] Missing configuration: No valid COM port selected.")

            try:
                g._open_serial()
                firmware_ok = g._verify_arduino_firmware()
                g.ser.close() # CRITICAL: Release the port for the actual acquisition thread!
            except Exception:
                firmware_ok = False
                if hasattr(g, 'ser') and g.ser.is_open:
                    g.ser.close()

            if not firmware_ok:
                raise ValueError("[PYDAQ] PyDAQ Firmware not detected on this board! Please go to the top menu and click on 'Arduino - Firmware' to upload the correct code.")

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

            g.channels = self.get_selected_channels()

        except BaseException as e :
            # Standardized GUI Error Window
            err_msg = str(e)
            if err_msg: 
                warnings.warn(err_msg)

            error_w = Error_window()
            # Dynamic GUI Message routing based on the error type
            if "Firmware" in err_msg:
                error_w.ui.confirm.setText("Firmware not detected on this board. Please go to the top menu and click on 'Arduino - Firmware' to upload the correct code.")
            else:
                error_w.ui.confirm.setText("Missing configuration: Please ensure device, channel, and path are properly defined.")
            error_w.exec()

            # Use locals() check in case 'g' failed to instantiate
            if 'g' in locals():
                g.error_path = True

            return

        if not g.error_path:
            filter_coefs = None
            fs = (1 / float(self.Ts_in.value())) * 2.5 # Sample rate estimate

            # 1. Check if we need to prepare filters before acquiring
            if not self.no_radio.isChecked():
                if self.filter == 'FIR':
                    # FIR filter configuration
                    fc_fir = self.cutofffir
                    numtaps_fir = self.orderfir
                    window_fir = self.design
                    type_fir = self.type
                    
                    # Normalize window names for scipy
                    window_map = {
                        'Blackman': 'blackman', 'Hamming': 'hamming',
                        'Hann': 'hann', 'Bartlett-Hann': 'barthann',
                        'Kaiser': 'kaiser', 'Gauss': 'gauss'
                    }
                    window_fir = window_map.get(window_fir, window_fir)

                    if type_fir in ['bandstop', 'bandpass']:
                        filter_coefs = firwin(numtaps_fir, [self.fc1/(0.5*fs), self.fc2/(0.5*fs)], 
                                              window=window_fir, pass_zero=type_fir)
                    else:
                        filter_coefs = firwin(numtaps_fir, fc_fir/(0.5*fs), 
                                              window=window_fir, pass_zero=type_fir)
                    self.fir_coeff = filter_coefs # Store for frequency_response

                elif self.filter == 'IIR':
                    # IIR filter configuration
                    if self.design_iir == 'Chebyshev Type I':
                        self.b, self.a = cheby1(self.orderiir, self.rp, self.cutoffiir/(0.5*fs), btype=self.type_irr)
                    elif self.design_iir == 'Chebyshev Type II':
                        self.b, self.a = cheby2(self.orderiir, self.rs, self.cutoffiir/(0.5*fs), btype=self.type_irr)
                    elif self.design_iir == 'Butterworth':
                        self.b, self.a = butter(self.orderiir, self.cutoffiir/(0.5*fs), btype=self.type_irr)
                    elif self.design_iir == 'Elliptic':
                        self.b, self.a = ellip(self.orderiir, self.rp, self.rs, self.cutoffiir/(0.5*fs), btype=self.type_irr)
                    
                    filter_coefs = (self.b, self.a)

        success = g.get_data_arduino(filter_coefs=filter_coefs)

        # 3. Handle the results
        if success:
            self.signals.returned.emit(g)
            # Only call frequency response if filtering was active and successful
            if not self.no_radio.isChecked():
                self.frequency_response()
        else:
            # This will print if the firmware check failed or the user cancelled
            print("Acquisition failed or interrupted. Analysis skipped.")

    def frequency_response(self):
        if self.fr == True:
            if self.filter == 'FIR':
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
                
                w, h = signal.freqz(self.fir_coeff, 1.0, worN=None, fs=fs)
                mag = 20*np.log10(np.abs(h))
                phase = np.angle(h)
                
                dt = 1/(fs*2.5)  # 1/(fs*2)
                
                channels_selected = self.get_selected_channels()
                
                # Loop to calculate and create a figure for each channel
                for i in range(num_channels):
                    # Get the correct name using the index
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
                
                channels_selected = self.get_selected_channels()
                
                # Loop to calculate and create a figure for each channel
                for i in range(num_channels):
                    # Get the correct name using the index
                    ch_name = channels_selected[i] if i < len(channels_selected) else f"CH {i}"
                    
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
    
    
    def _setup_channel_selector(self):
        self.channel_combo.setEditable(True)

        clickable_line = ClickableLineEdit()
        clickable_line.setReadOnly(True)
        clickable_line.setPlaceholderText("No channels available")
        
        clickable_line.clicked.connect(self._show_channel_menu) 
        
        self.channel_combo.setLineEdit(clickable_line)

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

        if not any(a.isChecked() for a in self.channel_actions):
            self.channel_actions[0].setChecked(True)
            selected = [self.channel_actions[0].text()]

        self.channel_combo.lineEdit().setText(", ".join(selected))

    def get_selected_channels(self):
        selected = [a.text() for a in self.channel_actions if a.isChecked()]
        return selected if selected else [self.available_channels[0]]
