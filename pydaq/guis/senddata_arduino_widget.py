import os
import serial
import serial.tools.list_ports
import numpy as np

from PySide6.QtWidgets import QFileDialog, QWidget, QMenu   
from pydaq.utils.signals import GuiSignals
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from ..uis.ui_PyDAQ_send_data_Arduino_widget import Ui_Arduino_SendData_W
from .error_window_gui import Error_window

from ..send_data import SendData


class SendData_Arduino_Widget(QWidget, Ui_Arduino_SendData_W):
    def __init__(self, *args):
        super(SendData_Arduino_Widget, self).__init__()
        self.setupUi(self)

        # Connecting Signals
        self.reload_devices.released.connect(self.update_com_ports)
        self.path_folder_browse.released.connect(self.locate_path)
        self.start_send_data.released.connect(self.start_func_send_data)
        self.label_warning.hide()
        self.plot_radio_group.buttonToggled.connect(self._update_warning_label)
        self.signals = GuiSignals()

        # Setting the starting values for some widgets
        self.update_com_ports()
        self.path_line_edit.setText(
            os.path.join(os.path.join(os.path.expanduser("~")), "Desktop", "data.dat")
        )
        
        # Channel selection
        # Assuming digital pins 0-13 for Arduino
        self.available_channels = [f"D{i}" for i in range(14)] 
        self._setup_channel_selector()

    def _update_warning_label(self):
        if self.yes_rt_plot_radio.isChecked():
            self.label_warning.show()
        else:
            self.label_warning.hide()
            
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

    def start_func_send_data(self):  # Start sending data
        try:
            # Instantiating the SendData class
            s = SendData()

            # Restarting time and data
            s.time_var, s.data = [], []

            # Reading data from defined path and rearranjing it
            s.path = self.path_line_edit.text()
            
            # Passing the selected digital pins (channels) to the backend
            s.channels = self.get_selected_channels()

            s.data = self._prepare_data_matrix(s.path, s.channels)

            # Getting the remaining values from the GUI
            s.com_port = serial.tools.list_ports.comports()[
                self.com_ports.index(self.device_combo.currentText())
            ].name
            
            s.ts = self.Ts_in.value()
            if self.yes_rt_plot_radio.isChecked():
                s.plot_mode = 'realtime'
            elif self.yes_ate_plot_radio.isChecked(): 
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
            s.send_data_arduino()
            self.signals.returned.emit(s)

    def _prepare_data_matrix(self, path, selected_channels):
        """
        Reads file and prepares a 2D matrix:
        - If file is 1D → replicate column to all channels
        - If file is 2D → each column must match a channel
        - Binarizes values using 2.5V threshold
        """

        raw_data = np.loadtxt(path)
        n_channels = len(selected_channels)

        # ----------------------------------------
        # Case 1: 1D file
        # ----------------------------------------
        if raw_data.ndim == 1:
            raw_data = np.where(raw_data > 2.5, 5, 0)
            data_matrix = np.tile(raw_data.reshape(-1, 1), (1, n_channels))

        # ----------------------------------------
        # Case 2: 2D file
        # ----------------------------------------
        elif raw_data.ndim == 2:
            if raw_data.shape[1] != n_channels:
                raise ValueError(
                    f"File has {raw_data.shape[1]} columns but "
                    f"{n_channels} channels were selected."
                )

            raw_data = np.where(raw_data > 2.5, 5, 0)
            data_matrix = raw_data

        else:
            raise ValueError("Unsupported file format.")

        return data_matrix.tolist()


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

        if not any(a.isChecked() for a in self.channel_actions):
            self.channel_actions[0].setChecked(True)
            selected = [self.channel_actions[0].text()]

        self.channel_combo.lineEdit().setText(", ".join(selected))

    def get_selected_channels(self):
        selected = [a.text() for a in self.channel_actions if a.isChecked()]
        return selected if selected else [self.available_channels[0]]