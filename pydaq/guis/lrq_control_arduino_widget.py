import os
import serial
import serial.tools.list_ports
import numpy as np

from PySide6.QtWidgets import QFileDialog, QWidget, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

from pydaq.utils.signals import GuiSignals

from ..uis.ui_PyDAQ_lqr_control_Arduino_widget import Ui_Arduino_LQR_Control
from ..guis.lqr_matrices_widget import Select_LQR_Matrices_Widget
from ..guis.lqr_reference_widget import Select_LQR_Reference_Widget
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
        self.simulate_radio_group.buttonToggled.connect(self.on_simulate_change)
        self.on_simulate_change()
        self.signals = GuiSignals()

        # Setting the starting values for some widgets
        self.update_com_ports()
        self.path_line_edit.setText(
            os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")
        )

        # Available channels (Arduino logic)
        self.available_ai_channels = [f"A{i}" for i in range(6)]
        self.available_ao_channels = [f"D{i}" for i in range(0, 14)]

        self._setup_ai_selector()
        self._setup_ao_selector()

        # LQR matrices
        self.A = None
        self.B = None
        self.C = None   
        self.D = None
        self.Q = None
        self.R = None

        # Tracking LQR references (New)
        self.X_ref = None
        self.U_eq = None
        self.n_states = 2 # Default fallback
        self.n_inputs = 2 # Default fallback

        self.reference_radio_group.buttonToggled.connect(self.on_reference_change)

    def openMatricesWindow(self):
        simulate = True if self.simulate_radio_group.checkedId() == -2 else False
        self.Matrices = Select_LQR_Matrices_Widget(simulate=simulate)

        if self.A is not None:
            # We set the spin boxes first to trigger table resizing
            self.Matrices.spin_states.setValue(self.n_states)
            self.Matrices.spin_inputs.setValue(self.n_inputs)
            
            # Create a dictionary with current data to update the table defaults
            current_data = {
                'A': self.A,
                'B': self.B,
                'C': self.C,
                'D': self.D,
                'Q': self.Q,
                'R': self.R
            }
            # Update the defaults in the matrix widget before showing it
            for key, value in current_data.items():
                if value is not None:
                    self.Matrices.default_matrices[key] = value
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
            simulate = True if self.simulate_radio_group.checkedId() == -2 else False
            output_mode = "arduino_pwm" if self.Arduino_PWM_radio.isChecked() else "free"

            l = LQRControl()

            # 1. Config Validation: Matrices Defined
            if self.A is None or self.B is None or self.Q is None or self.R is None:
                raise ValueError("[PYDAQ] Missing configuration: Matrices are not defined. Cannot simulate or run control.")

            # 2. Config Validation: Path
            if self.path_line_edit.text() == "":
                raise ValueError("[PYDAQ] Missing configuration: Empty save path.")
            
            l.path = self.path_line_edit.text()

            # Common LQR parameters for both Simulation and Hardware
            l.A, l.B, l.C, l.D = self.A, self.B, self.C, self.D
            l.Q, l.R = self.Q, self.R

            # --- NEW: Pass Reference Tracking variables ---
            if self.yes_reference_radio.isChecked():
                if self.X_ref is None or self.U_eq is None:
                    raise ValueError("[PYDAQ] Missing configuration: Reference Tracking is enabled but X_ref or U_eq are empty.")
                l.use_reference = True
                l.x_ref = self.X_ref
                l.u_eq = self.U_eq
            else:
                l.use_reference = False

            l.ts = self.Ts_in.value()
            l.session_duration = self.sesh_dur_in.value()
            l.save = True if self.save_radio_group.checkedId() == -2 else False
            if self.yes_rt_plot_radio.isChecked(): 
                l.plot_mode = 'realtime'
            elif self.yes_ate_plot_radio.isChecked():
                l.plot_mode = 'end'
            else: # self.No_radio.isChecked()
                l.plot_mode = 'no'

            if simulate:
                l.output_mode = output_mode
                l.simulate_lqr()

                return  # IMPORTANT: stop here

            l.channels = self.get_selected_ai()
            l.ao_channels = self.get_selected_ao()

            A_arr = np.array(self.A)
            B_arr = np.array(self.B)

            n_states = len(l.channels)      # Number of AI channels
            n_inputs = len(l.ao_channels)   # Number of AO channels

            # Check matrix A: must be square and match the number of AI channels
            if A_arr.ndim != 2 or A_arr.shape[0] != A_arr.shape[1] or A_arr.shape[0] != n_states:
                raise ValueError(f"[PYDAQ] Dimension mismatch: Matrix A must be {n_states}x{n_states} to match AI channels!")

            # Check matrix B: rows must match AI channels, cols must match AO channels
            if B_arr.ndim != 2 or B_arr.shape[0] != n_states or B_arr.shape[1] != n_inputs:
                raise ValueError(f"[PYDAQ] Dimension mismatch: Matrix B must be {n_states}x{n_inputs} to match AI and AO channels!")

            # 4. Config Validation: COM Port
            try:
                l.com_port = serial.tools.list_ports.comports()[
                    self.com_ports.index(self.device_combo.currentText())
                ].name
            except (ValueError, IndexError):
                raise ValueError("[PYDAQ] Missing configuration: No valid COM port selected.")

            # 5. GUI-Level Firmware Verification
            try:
                l._open_serial()
                firmware_ok = l._verify_arduino_firmware()
                l.ser.close() # CRITICAL: Release the port
            except Exception:
                firmware_ok = False
                if hasattr(l, 'ser') and l.ser.is_open:
                    l.ser.close()

            if not firmware_ok:
                raise ValueError("[PYDAQ] PyDAQ Firmware not detected on this board! Please go to the top menu and click on 'Arduino Firmware' to upload the correct code.")

            l.lqr_control_arduino()

            self.signals.returned.emit(l)

        except BaseException as e:
            # Standardized GUI Error Window
            import warnings
            err_msg = str(e)
            if err_msg: 
                warnings.warn(err_msg)

            error_w = Error_window()

            # Dynamic GUI Message routing
            if "Dimension mismatch" in err_msg:
                error_w.ui.confirm.setText("Dimension mismatch: Number of selected channels incorrect.")
            elif "Firmware" in err_msg:
                error_w.ui.confirm.setText("Firmware not detected on this board. Please go to the top menu and click on 'Arduino - Firmware' to upload the correct code.")
            elif "Matrices are not defined" in err_msg:
                error_w.ui.confirm.setText("Missing configuration: LQR Matrices (A, B, Q, R) must be defined before running.")
            else:
                error_w.ui.confirm.setText("Missing configuration: Please ensure device, channels, and save path are properly defined.")

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
        self.C = data.get("C", None)   
        self.D = data.get("D", None)   
        self.Q = data["Q"]
        self.R = data["R"]

        self.n_states = data["n"]
        self.n_inputs = data["m"]

        print("\n[PYDAQ] LQR matrices updated")

    def on_simulate_change(self):
        self.simulate = True if self.simulate_radio_group.checkedId() == -2 else False
        if self.simulate is False: #Simulate = False
            self.widget_device.show()
            self.label_device.show()
            self.ai_channel_combo.show()
            self.ao_channel_combo.show()
            self.label_ai_channel.show()
            self.label_ao_channel.show()
            self.widget_ai_channel.show()
            self.widget_ao_channel.show()
            self.label_output.hide()
            self.widget_output.hide()

        elif self.simulate is True: #Simulate = True
            self.widget_device.hide()
            self.label_device.hide()
            self.ai_channel_combo.hide()
            self.ao_channel_combo.hide()
            self.label_ai_channel.hide()
            self.label_ao_channel.hide()
            self.widget_ai_channel.hide()
            self.widget_ao_channel.hide()
            self.label_output.show()
            self.widget_output.show()

    def on_reference_change(self):
        """
        Triggered when the user toggles the Reference Tracking Radio Group.
        """
        # If 'Yes' is selected
        if self.yes_reference_radio.isChecked():
            # Safety check: ensure A and B are defined so we know the dimensions
            if self.A is None or self.B is None:
                self.no_reference_radio.setChecked(True) # Revert to No
                error_w = Error_window()
                error_w.ui.confirm.setText("Please define the LQR Matrices (A, B) first before setting references.")
                error_w.exec()
                return
            
            self.openReferenceWindow()
        else:
            pass

    def openReferenceWindow(self):
        """
        Opens the widget to input X_ref and U_eq matrices.
        Passes the current n_states and n_inputs to lock the table dimensions.
        """
        self.RefWindow = Select_LQR_Reference_Widget(n_states=self.n_states, n_inputs=self.n_inputs)
        
        # Lógica de persistência idêntica ao widget de Matrizes
        if self.X_ref is not None and self.U_eq is not None:
            
            # Create a dictionary with current data to update the table defaults
            current_data = {
                'X': self.X_ref,
                'U': self.U_eq
            }
            
            # Update the defaults in the matrix widget before showing it
            for key, value in current_data.items():
                if value is not None:
                    self.RefWindow.default_matrices[key] = value
                    
            # Refresh tables with "cached" values
            self.RefWindow.update_sizes() 

        self.RefWindow.dataEntered.connect(self.update_reference_values)
        self.RefWindow.show()

    def update_reference_values(self, data):
        """
        Slot to receive data from the Select_LQR_Reference_Widget.
        """
        self.X_ref = data["X"]
        self.U_eq = data["U"]
        print("\n[PYDAQ] LQR Reference states updated")