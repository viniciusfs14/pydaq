import os
import nidaqmx
import numpy as np

from PySide6.QtWidgets import QFileDialog, QWidget, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from pydaq.utils.signals import GuiSignals

from ..uis.ui_PyDAQ_send_data_NIDAQ_widget import Ui_NIDAQ_SendData_W
from .error_window_gui import Error_window

from ..send_data import SendData


class SendData_NIDAQ_Widget(QWidget, Ui_NIDAQ_SendData_W):
    def __init__(self, *args):
        super(SendData_NIDAQ_Widget, self).__init__()
        self.setupUi(self)

        # Gathering nidaq info
        self._nidaq_info()

        try:
            self.available_channels = nidaqmx.system.device.Device(
                self.device_names[0]
            ).ao_physical_chans.channel_names
        except BaseException:
            self.available_channels = []

        # Setting the starting values 
        self.device_combo.addItems(self.device_type)
        self.path_line_edit.setText(
            os.path.join(os.path.join(os.path.expanduser("~")), "Desktop", "data.dat")
        )
        
        self._setup_channel_selector()

        #defchan_index = self.channel_combo.findText(defchan)
#
 #       if defchan_index == -1:
  #          pass
   #     else:
    #        self.channel_combo.setCurrentIndex(defchan_index)

        # Connecting Signals
        self.path_folder_browse.released.connect(self.locate_path)
        self.start_send_data.released.connect(self.start_func_send_data)
        self.device_combo.currentIndexChanged.connect(self.update_channels)
        self.reload_devices.released.connect(self.reload_devices_handler)
        self.label_warning.hide()
        self.plot_radio_group.buttonToggled.connect(self._update_warning_label)
        self.signals = GuiSignals()

    def _update_warning_label(self):
        if self.yes_rt_plot_radio.isChecked():
            self.label_warning.show()
        else:
            self.label_warning.hide()
            
    def start_func_send_data(self):  # Start sending data
        try:
            # Instantiating the SendData class
            s = SendData()

            s.ao_max = self.out_range_max_in.value()
            s.ao_min = self.out_range_min_in.value()

            # Reading data from defined path
            s.path = self.path_line_edit.text()
            
            # Separating variables
            selected = self.get_selected_channels()
            if selected:
                s.device = selected[0].split("/")[0]
                # Sending the list of channel names (e.g., ["ao0", "ao1"])
                s.channels = [ch.split("/")[1] for ch in selected]
            else:
                raise ValueError("No channel selected")

            s.data = self._prepare_data_matrix_nidaq(
                s.path,
                s.channels,
                s.ao_min,
                s.ao_max
            )

            s.ts = self.Ts_in.value()
            if self.yes_rt_plot_radio.isChecked(): # Assumindo que 'yes_radio' agora significa 'Real time'
                s.plot_mode = 'realtime'
            elif self.yes_ate_plot_radio.isChecked(): # Supondo que você criou um radio button com este nome
                s.plot_mode = 'end'
            else: # self.No_radio.isChecked()
                s.plot_mode = 'no'
            s.error_path = False

        except BaseException:
            error_w = Error_window()
            error_w.exec()
            s.error_path = True

        if not s.error_path:
            # Calling send data method
            s.send_data_nidaq()
            self.signals.returned.emit(s)

    def locate_path(self):  # Calling the File Browser Widget
        data_path = QFileDialog.getOpenFileName(
            self,
            caption="Search for the data file",
            filter="DAT Files (*.dat);;All Files (*)",
        )[0]
        if data_path == "":
            pass
        else:
            self.path_line_edit.setText(data_path.replace("/", "\\"))

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

        # Discovering new ao channels
        new_ao_channels = nidaqmx.system.device.Device(
            self.device_names[self.device_type.index(self.device_combo.currentText())]
        ).ao_physical_chans.channel_names

        # Default channel
        try:
            default_channel = new_ao_channels[0]
        except:
            default_channel = "There is no analog output in this board"

        self.available_channels = new_ao_channels
        # Recreate the channel menu
        self.channel_menu.clear()
        self.channel_actions = []

        if not self.available_channels:
             self.channel_combo.lineEdit().setText("No analog output available")
             return

        for ch in self.available_channels:
            action = QAction(ch, self)
            action.setCheckable(True)
            action.toggled.connect(self._update_channel_text)
            self.channel_menu.addAction(action)
            self.channel_actions.append(action)

        # Select the first channel by default if available
        if self.channel_actions:
            self.channel_actions[0].setChecked(True)
        
        self._update_channel_text()

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

    def _prepare_data_matrix_nidaq(self, path, selected_channels, ao_min, ao_max):
        """
        Reads file and prepares a matrix for NIDAQ AO output.
        
        - 1D file → replicate to all selected channels
        - 2D file → columns must match number of selected channels
        - Validates range against ao_min and ao_max
        """

        raw_data = np.loadtxt(path)
        n_channels = len(selected_channels)

        if n_channels == 0:
            raise ValueError("No channel selected")

        # -----------------------------
        # Case 1: 1D
        # -----------------------------
        if raw_data.ndim == 1:
            data_matrix = np.tile(raw_data.reshape(-1, 1), (1, n_channels))

        # -----------------------------
        # Case 2: 2D
        # -----------------------------
        elif raw_data.ndim == 2:
            if raw_data.shape[1] != n_channels:
                raise ValueError(
                    f"File has {raw_data.shape[1]} columns but "
                    f"{n_channels} channels were selected."
                )
            data_matrix = raw_data

        else:
            raise ValueError("Unsupported file format.")

        # -----------------------------
        # Range validation
        # -----------------------------
        if np.max(data_matrix) > ao_max or np.min(data_matrix) < ao_min:
            raise ValueError(
                f"Data out of range [{ao_min}, {ao_max}]"
            )

        return data_matrix

    def _setup_channel_selector(self):
        self.channel_combo.setEditable(True)
        self.channel_combo.lineEdit().setReadOnly(True)
        self.channel_combo.lineEdit().setPlaceholderText("Select channels...")

        self.channel_menu = QMenu(self)
        self.channel_actions = []

        for ch in self.available_channels:
            action = QAction(ch, self)
            action.setCheckable(True)
            action.toggled.connect(self._update_channel_text)
            self.channel_menu.addAction(action)
            self.channel_actions.append(action)

        self.channel_combo.showPopup = self._show_channel_menu

    def _show_channel_menu(self):
        self.channel_menu.exec(
            self.channel_combo.mapToGlobal(
                self.channel_combo.rect().bottomLeft()
            )
        )
    
    def _update_channel_text(self):
        selected = self.get_selected_channels()

        if not any(a.isChecked() for a in self.channel_actions) and self.channel_actions:
            self.channel_actions[0].setChecked(True)
            selected = [self.channel_actions[0].text()]

        self.channel_combo.lineEdit().setText(", ".join(selected))

    def get_selected_channels(self):
        selected = [a.text() for a in self.channel_actions if a.isChecked()]
        return selected if selected else (self.available_channels[:1] if self.available_channels else [])