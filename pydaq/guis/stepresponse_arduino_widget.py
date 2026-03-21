import os
import serial
import serial.tools.list_ports

from PySide6.QtWidgets import QFileDialog, QWidget, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

from pydaq.utils.signals import GuiSignals

from ..uis.ui_PyDAQ_step_response_Arduino_widget import Ui_Arduino_StepResponse_W
from .error_window_gui import Error_window

from ..step_response import StepResponse


class StepResponse_Arduino_Widget(QWidget, Ui_Arduino_StepResponse_W):
    def __init__(self, *args):
        super(StepResponse_Arduino_Widget, self).__init__()
        self.setupUi(self)

        # Connecting Signals
        self.reload_devices.released.connect(self.update_com_ports)
        self.path_folder_browse.released.connect(self.locate_path)
        self.start_step_response.released.connect(self.start_func_step_response)
        self.label_warning.hide()
        self.pidshow()
        self.pid_radio_group.buttonClicked.connect(self.pidshow)
        self.plot_radio_group.buttonToggled.connect(self._update_warning_label)
        self.signals = GuiSignals()

        # Setting the starting values for some widgets
        self.update_com_ports()
        self.path_line_edit.setText(
            os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")
        )

        # Available channels (Arduino logic)
        self.available_ai_channels = [f"A{i}" for i in range(8)]
        self.available_ao_channels = [f"D{i}" for i in range(0, 14)]

        self._setup_ai_selector()
        self._setup_ao_selector()

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

    def locate_path(self):  # Calling the Folder Browser Widget
        output_folder_path = QFileDialog.getExistingDirectory(
            self, caption="Choose a folder to save the data file"
        )
        if output_folder_path == "":
            pass
        else:
            self.path_line_edit.setText(output_folder_path.replace("/", "\\"))

    def start_func_step_response(self):
        try:
            self.get_sintony_type()
            
            # Instantiating the StepResponse class
            s = StepResponse()

            # Getting the values from the GUI
            s.channels = self.get_selected_ai()
            s.ao_channels = self.get_selected_ao()

            s.com_port = serial.tools.list_ports.comports()[
                self.com_ports.index(self.device_combo.currentText())
            ].name
            s.ts = self.Ts_in.value()
            s.session_duration = self.sesh_dur_in.value()
            s.step_time = self.step_on_s_in.value()
            if self.yes_rt_plot_radio.isChecked(): 
                s.plot_mode = 'realtime'
            elif self.yes_ate_plot_radio.isChecked():
                s.plot_mode = 'end'
            else: # self.No_radio.isChecked()
                s.plot_mode = 'no'
            s.save = True if self.save_radio_group.checkedId() == -2 else False
            s.path = self.path_line_edit.text()
            s.calculate_pid = True if self.pid_radio_group.checkedId() == -2 else False
            s.sintony_type =  self.sintony_type

            # Restarting variables
            self.time_var, self.input, self.output = [], [], []

            # Checking if a path was set
            if self.path_line_edit.text() == "":
                raise BaseException

            s.step_response_arduino()
            self.signals.returned.emit(s)

        except BaseException:
            error_w = Error_window()
            error_w.exec()

    def pidshow(self):
        self.enabled = True if self.pid_radio_group.checkedId() == -2 else False
        if self.enabled is False: #Simulate = False
            self.PID_comboBox.setEnabled(False)
        else:
            self.PID_comboBox.setEnabled(True)

    def get_sintony_type(self):
        if self.PID_comboBox.isEnabled():
            self.sintony_type = self.PID_comboBox.currentIndex() # Can be 0, 1 or 2: P, PI or PID
        else:
            self.sintony_type = None # None if disabled

    def _setup_ai_selector(self):
        self.ai_channel_combo.setEditable(True)
        self.ai_channel_combo.lineEdit().setReadOnly(True)
        self.ai_channel_combo.lineEdit().setPlaceholderText("No channels available")
        self.ai_menu = QMenu(self)
        self.ai_actions = []
        for ch in self.available_ai_channels:
            action = QAction(ch, self)
            action.setCheckable(True)
            action.toggled.connect(self._update_ai_text)
            self.ai_menu.addAction(action)
            self.ai_actions.append(action)

        self.ai_channel_combo.showPopup = self._show_ai_menu

        if self.ai_actions:
            self.ai_actions[0].setChecked(True)
        else:
            self.ai_channel_combo.lineEdit().clear()

    def _show_ai_menu(self):
        self.ai_menu.exec(
            self.ai_channel_combo.mapToGlobal(
                self.ai_channel_combo.rect().bottomLeft()
            )
        )

    def _update_ai_text(self):
        selected = self.get_selected_ai()

        if not any(a.isChecked() for a in self.ai_actions):
            self.ai_actions[0].setChecked(True)
            selected = [self.ai_actions[0].text()]

        self.ai_channel_combo.lineEdit().setText(", ".join(selected))

    def get_selected_ai(self):
        selected = [a.text() for a in self.ai_actions if a.isChecked()]
        return selected if selected else [self.available_ai_channels[0]]
    
    def _setup_ao_selector(self):
        self.ao_channel_combo.setEditable(True)
        self.ao_channel_combo.lineEdit().setReadOnly(True)
        self.ao_channel_combo.lineEdit().setPlaceholderText("No channels available")
        self.ao_menu = QMenu(self)
        self.ao_actions = []
        for ch in self.available_ao_channels:
            action = QAction(ch, self)
            action.setCheckable(True)
            action.toggled.connect(self._update_ao_text)
            self.ao_menu.addAction(action)
            self.ao_actions.append(action)

        self.ao_channel_combo.showPopup = self._show_ao_menu

        if self.ao_actions:
            self.ao_actions[0].setChecked(True)
        else:
            self.ao_channel_combo.lineEdit().clear()

    def _show_ao_menu(self):
        self.ao_menu.exec(
            self.ao_channel_combo.mapToGlobal(
                self.ao_channel_combo.rect().bottomLeft()
            )
        )

    def _update_ao_text(self):
        selected = self.get_selected_ao()

        if not any(a.isChecked() for a in self.ao_actions):
            self.ao_actions[0].setChecked(True)
            selected = [self.ao_actions[0].text()]

        self.ao_channel_combo.lineEdit().setText(", ".join(selected))

    def get_selected_ao(self):
        selected = [a.text() for a in self.ao_actions if a.isChecked()]
        return selected if selected else [self.available_ao_channels[0]]