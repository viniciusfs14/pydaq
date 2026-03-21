import os
import serial
import serial.tools.list_ports

from PySide6.QtWidgets import QFileDialog, QWidget, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

from pydaq.utils.signals import GuiSignals

from ..uis.ui_PyDAQ_lqr_control_Arduino_widget import Ui_Arduino_LQR_Control
from ..guis.lqr_matrices_widget import Select_LQR_Matrices_Widget
from .error_window_gui import Error_window

from ..lqr_control import LQRControl

class LQRControl_Arduino_Widget(QWidget, Ui_Arduino_LQR_Control):
    def __init__(self, *args):
        super(LQRControl_Arduino_Widget, self).__init__()
        self.setupUi(self)

        # Connecting Signals
        self.reload_devices.released.connect(self.update_com_ports)
        self.path_folder_browse.released.connect(self.locate_path)
        self.start_lqr_control.released.connect(self.start_func_LQR_Control)
        self.label_warning.hide()
        self.plot_radio_group.buttonToggled.connect(self._update_warning_label)
        self.insert_matrices.released.connect(self.openMatricesWindow)
        self.simulate_button.released.connect(self.run_pure_simulation)
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

        # LQR matrices
        self.A = None
        self.B = None
        self.Q = None
        self.R = None

    def openMatricesWindow(self):
        self.Matrices = Select_LQR_Matrices_Widget()

        if self.A is not None:
            # We set the spin boxes first to trigger table resizing
            self.Matrices.spin_states.setValue(self.n_states)
            self.Matrices.spin_inputs.setValue(self.n_inputs)
            
            # Create a dictionary with current data to update the table defaults
            current_data = {
                'A': self.A,
                'B': self.B,
                'Q': self.Q,
                'R': self.R
            }
            # Update the defaults in the matrix widget before showing it
            self.Matrices.default_matrices.update(current_data)
            self.Matrices.update_sizes() # Refresh tables with "cached" values

        self.Matrices.dataEntered.connect(self.update_values)
        self.Matrices.show()

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

    def start_func_LQR_Control(self):
        try:
            
            # Instantiating the StepResponse class
            l = LQRControl()

            # Getting the values from the GUI
            l.channels = self.get_selected_ai()
            l.ao_channels = self.get_selected_ao()
            l.com_port = serial.tools.list_ports.comports()[
                self.com_ports.index(self.device_combo.currentText())
            ].name
            l.ts = self.Ts_in.value()
            l.session_duration = self.sesh_dur_in.value()
            if self.yes_rt_plot_radio.isChecked(): 
                l.plot_mode = 'realtime'
            elif self.yes_ate_plot_radio.isChecked():
                l.plot_mode = 'end'
            else: # self.No_radio.isChecked()
                l.plot_mode = 'no'
            l.save = True if self.save_radio_group.checkedId() == -2 else False
            l.path = self.path_line_edit.text()

            if self.A is None or self.B is None or self.Q is None or self.R is None:
                raise BaseException
            l.A = self.A
            l.B = self.B
            l.Q = self.Q
            l.R = self.R

            # Restarting variables
            self.time_var, self.input, self.output = [], [], []

            # Checking if a path was set
            if self.path_line_edit.text() == "":
                raise BaseException

            l.lqr_control_arduino()
            self.signals.returned.emit(l)

        except BaseException:
            error_w = Error_window()
            error_w.exec()

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

    def update_values(self, data):

        self.A = data["A"]
        self.B = data["B"]
        self.Q = data["Q"]
        self.R = data["R"]

        self.n_states = data["n"]
        self.n_inputs = data["m"]

        print("LQR matrices updated")

    def run_pure_simulation(self):
        try:
            if self.A is None or self.B is None or self.Q is None or self.R is None:
                print("Insira as matrizes antes de simular.")
                return

            # Instancia apenas para simular
            l = LQRControl()
            l.A = self.A
            l.B = self.B
            l.Q = self.Q
            l.R = self.R
            l.ts = self.Ts_in.value()
            l.session_duration = self.sesh_dur_in.value()

            l.simulate_lqr()

        except BaseException as e:
            print(f"Erro na simulação: {e}")