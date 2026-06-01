import os
import warnings
import numpy as np

from PySide6.QtWidgets import QFileDialog, QWidget, QMenu
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt
from pydaq.utils.signals import GuiSignals
from pydaq.utils.base import Base, NIDAQ_AVAILABLE, TerminalConfiguration, nidaqmx, System, ClickableLineEdit

from ..uis.ui_PyDAQ_lqr_control_NIDAQ_widget import Ui_NIDAQ_LQR_Control
from ..guis.lqr_reference_widget import Select_LQR_Reference_Widget
from .error_window_gui import Error_window
from ..guis.lqr_matrices_widget import Select_LQR_Matrices_Widget
from ..lqr_control import LQRControl


class LQRControl_NIDAQ_Widget(QWidget, Ui_NIDAQ_LQR_Control):
    def __init__(self, *args):
        super(LQRControl_NIDAQ_Widget, self).__init__()
        self.setupUi(self)
        # Gathering nidaq info
        self._nidaq_info()

        # Discover AO channels
        try:
            self.available_ao_channels = nidaqmx.system.device.Device(
                self.device_names[0]
            ).ao_physical_chans.channel_names
        except BaseException:
            self.available_ao_channels = []

        # Discover AI channels
        try:
            self.available_ai_channels = nidaqmx.system.device.Device(
                self.device_names[0]
            ).ai_physical_chans.channel_names
        except BaseException:
            self.available_ai_channels = []

        # ----------------------------
        # Setting initial widget values
        # ----------------------------
        self.device_combo.addItems(self.device_type)

        self.path_line_edit.setText(
            os.path.join(
                os.path.expanduser("~"),
                "Desktop"
            )
        )

        self.terminal_config_combo.addItems(["Diff", "RSE", "NRSE"])
        # Setup multichannel selectors
        self._setup_ao_selector()
        self._setup_ai_selector()

        # Connecting Signals
        self.path_folder_browse.released.connect(self.locate_path)
        self.start_lqr_control.released.connect(self.start_func_LQR_Control)
        self.device_combo.currentIndexChanged.connect(self.update_channels)
        self.label_warning.hide()
        self.plot_radio_group.buttonToggled.connect(self._update_warning_label)
        self.reload_devices.released.connect(self.reload_devices_handler)
        self.insert_matrices.released.connect(self.openMatricesWindow)
        self.simulate_radio_group.buttonToggled.connect(self.on_simulate_change)
        self.plot_radio_group.buttonToggled.connect(self._update_plot_options)
        self._update_plot_options()
        self.on_simulate_change()
        self.signals = GuiSignals()

        # LQR matrices
        self.A = None
        self.B = None
        self.C = None   
        self.D = None
        self.Q = None
        self.R = None

        # --- NEW: Tracking LQR references ---
        self.X_ref = None
        self.U_eq = None
        self.n_states = 2 # Default fallback
        self.n_inputs = 2 # Default fallback
        
        # --- NEW: Trajectory logic variables ---
        self.is_trajectory = False
        self.trajectory_steps = 1

        self.yes_reference_radio.toggled.connect(self.on_reference_change)
        
        # --- NEW: Auto update duration when Sample Period (Ts) changes ---
        if hasattr(self, 'Ts_in'):
            self.Ts_in.valueChanged.connect(self.auto_update_duration)

    def _update_warning_label(self):
        if self.yes_rt_plot_radio.isChecked():
            self.label_warning.show()
        else:
            self.label_warning.hide()
            
    # --- NEW: Auto calculate session duration based on file ---
    def auto_update_duration(self):
        if self.is_trajectory and self.yes_reference_radio.isChecked():
            new_duration = self.trajectory_steps * self.Ts_in.value()
            if hasattr(self, 'sesh_dur_in'):
                # Block signals momentarily to avoid recursive loops if connected
                self.sesh_dur_in.blockSignals(True)
                self.sesh_dur_in.setValue(new_duration)
                self.sesh_dur_in.blockSignals(False)

    def start_func_LQR_Control(self):
        
        self.simulate = True if self.simulate_radio_group.checkedId() == -2 else False
        
        # Safety lock: prevents dialog from opening if NI-DAQmx drivers are not found
        if not self.simulate and not NIDAQ_AVAILABLE:
            warnings.warn("[PYDAQ] NI-DAQmx drivers not found! Cannot start hardware control.")
            error_w = Error_window()
            error_w.ui.confirm.setText("NI-DAQmx drivers not found! Please install NI-MAX.")
            error_w.exec()
            return
        
        try:
            simulate = True if self.simulate_radio_group.checkedId() == -2 else False
            
            l = LQRControl()

            # 1. Config Validation: Matrices Defined
            if self.A is None or self.B is None or self.Q is None or self.R is None:
                raise ValueError("[PYDAQ] Missing configuration: Matrices are not defined. Cannot simulate or run control.")

            # 2. Config Validation: Path
            if self.yes_save_radio.isChecked() and self.path_line_edit.text() == "":
                raise ValueError("[PYDAQ] Missing configuration: Empty save path.")
            l.path = self.path_line_edit.text()

            # Common LQR parameters for both Simulation and Hardware
            l.A, l.B, l.C, l.D = self.A, self.B, self.C, self.D
            l.Q, l.R = self.Q, self.R

            l.plot_prefs = {
                'y': self.chk_plot_y.isChecked(),
                'x': self.chk_plot_x.isChecked(),
                'e': self.chk_plot_e.isChecked(),
                'u': self.chk_plot_u.isChecked()
            }
            
            if self.yes_rt_plot_radio.isChecked() or self.yes_ate_plot_radio.isChecked():
                if not any(l.plot_prefs.values()):
                    raise ValueError("[PYDAQ] Missing configuration: Please select at least one axis (y, x, e, or u) to plot.")
                
            # --- Pass Reference Tracking variables & Duration Validation ---
            if self.yes_reference_radio.isChecked():
                if self.X_ref is None or self.U_eq is None:
                    raise ValueError("[PYDAQ] Missing configuration: Reference Tracking is enabled but X_ref or U_eq are empty.")
                
                # Check if the user maliciously/accidentally altered the duration
                if self.is_trajectory:
                    expected_duration = self.trajectory_steps * self.Ts_in.value()
                    # Using a small tolerance (1e-3) due to float approximations
                    if abs(self.sesh_dur_in.value() - expected_duration) > 1e-3:
                        raise ValueError(f"[PYDAQ] Trajectory File Mismatch: Session duration must be exactly {expected_duration:.2f}s "
                                         f"({self.trajectory_steps} rows * {self.Ts_in.value()}s) to match the uploaded trajectory file.")

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

            A_arr = np.array(self.A)
            B_arr = np.array(self.B)

            # Determine number of states and inputs based on mode
            if simulate:
                n_states = self.n_states
                n_inputs = self.n_inputs
            else:
                # Input and output range for hardware
                selected_ao = self.get_selected_ao()
                selected_ai = self.get_selected_ai()
                
                if not selected_ai or not selected_ao:
                    raise ValueError("[PYDAQ] Missing configuration: No AI or AO channels selected for hardware control.")

                l.device = selected_ao[0].split("/")[0]
                l.channels = [ch.split("/")[1] for ch in selected_ai]
                l.ao_channels = [ch.split("/")[1] for ch in selected_ao]

                n_states = len(l.channels)      # Number of AI channels
                n_inputs = len(l.ao_channels)   # Number of AO channels

            # Check matrix A: must be square and match the number of states
            if A_arr.ndim != 2 or A_arr.shape[0] != A_arr.shape[1] or A_arr.shape[0] != n_states:
                raise ValueError(f"[PYDAQ] Dimension mismatch: Matrix A must be {n_states}x{n_states} to match system states!")

            # Check matrix B: rows must match states, cols must match inputs
            if B_arr.ndim != 2 or B_arr.shape[0] != n_states or B_arr.shape[1] != n_inputs:
                raise ValueError(f"[PYDAQ] Dimension mismatch: Matrix B must be {n_states}x{n_inputs} to match system inputs!")
            
            if self.yes_reference_radio.isChecked():
                X_arr = np.array(self.X_ref, ndmin=2)
                U_arr = np.array(self.U_eq, ndmin=2)
                
                if X_arr.shape[1] != n_states:
                    raise ValueError(f"[PYDAQ] Dimension mismatch: Reference X_ref must have {n_states} columns (states) to match Matrix A / AI channels!")
                    
                if U_arr.shape[1] != n_inputs:
                    raise ValueError(f"[PYDAQ] Dimension mismatch: Reference U_eq must have {n_inputs} columns (inputs) to match Matrix B / AO channels!")

            # --- SIMULATION MODE ---
            if simulate:
                l.simulate_lqr()
                return  # IMPORTANT: stop here

            # --- HARDWARE MODE ---
            l.terminal = l.term_map[self.terminal_config_combo.currentText()]

            l.lqr_control_nidaq()
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
            elif "Matrices are not defined" in err_msg:
                error_w.ui.confirm.setText("Missing configuration: LQR Matrices (A, B, Q, R) must be defined before running.")
            elif "Trajectory File Mismatch" in err_msg:
                error_w.ui.confirm.setText("Trajectory File Mismatch: Session duration must match the uploaded trajectory file.")
            else:
                error_w.ui.confirm.setText("Missing configuration: Please ensure device, channels, and save path are properly defined.")

            error_w.exec()
            return # Exit function to prevent execution

    def locate_path(self):  # Calling the Folder Browser Widget
        output_folder_path = QFileDialog.getExistingDirectory(
            self, caption="Choose a folder to save the data file"
        )
        if output_folder_path == "":
            pass
        else:
            self.path_line_edit.setText(output_folder_path.replace("/", "\\"))

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
                new_ao = nidaqmx.system.device.Device(dev_name).ao_physical_chans.channel_names
            else:
                new_ao = []

            if NIDAQ_AVAILABLE:
                new_ai = nidaqmx.system.device.Device(dev_name).ai_physical_chans.channel_names
            else:
                new_ai = []
        except BaseException:
            new_ao = []
            new_ai = []

        self.available_ao_channels = new_ao
        self.available_ai_channels = new_ai

        # Recreate AO menu
        self.ao_menu.clear()
        self.ao_actions = []

        for ch in self.available_ao_channels:
            action = QAction(ch, self)
            action.setCheckable(True)
            action.toggled.connect(self._update_ao_text)
            self.ao_menu.addAction(action)
            self.ao_actions.append(action)

        if self.ao_actions:
            self.ao_actions[0].setChecked(True)
        else:
            self.ao_channel_combo.lineEdit().clear()

        # Recreate AI menu
        self.ai_menu.clear()
        self.ai_actions = []

        for ch in self.available_ai_channels:
            action = QAction(ch, self)
            action.setCheckable(True)
            action.toggled.connect(self._update_ai_text)
            self.ai_menu.addAction(action)
            self.ai_actions.append(action)

        if self.ai_actions:
            self.ai_actions[0].setChecked(True)
        else:
            self.ai_channel_combo.lineEdit().clear()

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

    def _setup_ao_selector(self):
        self.ao_channel_combo.setEditable(True)

        clickable_line = ClickableLineEdit()
        clickable_line.setReadOnly(True)
        clickable_line.setPlaceholderText("No channels available")
        
        clickable_line.clicked.connect(self._show_ao_menu) 
        
        self.ao_channel_combo.setLineEdit(clickable_line)
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

        if not any(a.isChecked() for a in self.ao_actions) and self.ao_actions:
            self.ao_actions[0].setChecked(True)
            selected = [self.ao_actions[0].text()]

        self.ao_channel_combo.lineEdit().setText(", ".join(selected))

    def get_selected_ao(self):
        selected = [a.text() for a in self.ao_actions if a.isChecked()]
        return selected if selected else (self.available_ao_channels[:1] if self.available_ao_channels else [])
    
    def _setup_ai_selector(self):
        self.ai_channel_combo.setEditable(True)

        clickable_line = ClickableLineEdit()
        clickable_line.setReadOnly(True)
        clickable_line.setPlaceholderText("No channels available")
        
        clickable_line.clicked.connect(self._show_ai_menu) 
        
        self.ai_channel_combo.setLineEdit(clickable_line)
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

        if not any(a.isChecked() for a in self.ai_actions) and self.ai_actions:
            self.ai_actions[0].setChecked(True)
            selected = [self.ai_actions[0].text()]

        self.ai_channel_combo.lineEdit().setText(", ".join(selected))


    def get_selected_ai(self):
        selected = [a.text() for a in self.ai_actions if a.isChecked()]
        return selected if selected else (self.available_ai_channels[:1] if self.available_ai_channels else [])
    
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
    
    def openMatricesWindow(self):
        simulate = self.yes_simulate_radio.isChecked()
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
            self.label_terminal.show()
            self.widget_terminal.show()
            self.widget_plot.show()
            self.label_plot.show()
        elif self.simulate is True: #Simulate = True
            self.widget_device.hide()
            self.label_device.hide()
            self.ai_channel_combo.hide()
            self.ao_channel_combo.hide()
            self.label_ai_channel.hide()
            self.label_ao_channel.hide()
            self.widget_ai_channel.hide()
            self.widget_ao_channel.hide()
            self.label_terminal.hide()
            self.widget_terminal.hide()
            self.widget_plot.hide()
            self.label_plot.hide()
        self._update_plot_options()
    
    def on_reference_change(self, checked): # Adicione 'checked'
        if checked:
            if self.A is None or self.B is None:
                self.no_reference_radio.blockSignals(True)
                self.no_reference_radio.setChecked(True)
                self.no_reference_radio.blockSignals(False)
                
                error_w = Error_window()
                error_w.ui.confirm.setText("Please define the LQR Matrices (A, B) first before setting references.")
                error_w.exec()
                return
            
            self.openReferenceWindow()

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
        self.X_ref = data["X"]
        self.U_eq = data["U"]
        
        # --- NEW: Capturing trajectory parameters ---
        self.is_trajectory = data.get("is_trajectory", False)
        self.trajectory_steps = data.get("steps", 1)
        
        if self.is_trajectory:
            self.auto_update_duration()
            
        print(f"\n[PYDAQ] LQR Reference states updated. Trajectory mode: {self.is_trajectory}")

    def _update_plot_options(self):
        simulate = True if self.simulate_radio_group.checkedId() == -2 else False
        # Show axes selection only if real-time or at-the-end plotting is selected
        if simulate or self.yes_rt_plot_radio.isChecked() or self.yes_ate_plot_radio.isChecked():
            self.widget_axes.show()
            self.label_axes.show()
        else:
            self.widget_axes.hide()
            self.label_axes.hide()