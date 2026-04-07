import os

from PySide6.QtWidgets import QFileDialog, QWidget, QMenu
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt
from pydaq.utils.signals import GuiSignals
from pydaq.utils.base import Base, NIDAQ_AVAILABLE, TerminalConfiguration, nidaqmx, System

from ..uis.ui_PyDAQ_lqr_control_NIDAQ_widget import Ui_NIDAQ_LQR_Control
from .error_window_gui import Error_window
from ..guis.lqr_matrices_widget import Select_LQR_Matrices_Widget
from ..lqr_control import LQRControl


class LQRControl_NIDAQ_Widget(QWidget, Ui_NIDAQ_LQR_Control):
    def __init__(self, *args):
        super(LQRControl_NIDAQ_Widget, self).__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('docs/img/favicon.ico'))
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
        self.on_simulate_change()
        self.signals = GuiSignals()

        # LQR matrices
        self.A = None
        self.B = None
        self.C = None   
        self.D = None
        self.Q = None
        self.R = None

    def _update_warning_label(self):
        if self.yes_rt_plot_radio.isChecked():
            self.label_warning.show()
        else:
            self.label_warning.hide()
            
    def start_func_LQR_Control(self):
        try:
            simulate = True if self.simulate_radio_group.checkedId() == -2 else False

            # --- COMMON VALIDATION ---
            if self.A is None or self.B is None or self.Q is None or self.R is None:
                raise BaseException

            # --- SIMULATION MODE ---
            if simulate:
                l = LQRControl()
                l.A = self.A
                l.B = self.B
                l.C = self.C   
                l.D = self.D
                l.Q = self.Q
                l.R = self.R
                l.ts = self.Ts_in.value()
                l.session_duration = self.sesh_dur_in.value()

                print("Running in SIMULATION mode")
                l.simulate_lqr()

                return  # IMPORTANT: stop here

            # --- HARDWARE MODE ---
            l = LQRControl()
            
            # Input and output range
            selected_ao = self.get_selected_ao()
            selected_ai = self.get_selected_ai()

            if not selected_ao or not selected_ai:
                raise ValueError("Select at least one AO and one AI channel")

            l.device = selected_ao[0].split("/")[0]
            l.channels = [ch.split("/")[1] for ch in selected_ai]
            l.ao_channels = [ch.split("/")[1] for ch in selected_ao]

            l.terminal = l.term_map[self.terminal_config_combo.currentText()]
            l.ts = self.Ts_in.value()
            l.session_duration = self.sesh_dur_in.value()
            if self.yes_rt_plot_radio.isChecked(): 
                l.plot_mode = 'realtime'
            elif self.yes_ate_plot_radio.isChecked(): 
                l.plot_mode = 'end'
            else: # self.No_radio.isChecked()
                l.plot_mode = 'no'
            l.save = True if self.save_radio_group.checkedId() == -2 else False

            if self.path_line_edit.text() == "":
                raise BaseException
            
            l.path = self.path_line_edit.text()
            
            l.A = self.A
            l.B = self.B
            l.C = self.C   
            l.D = self.D
            l.Q = self.Q
            l.R = self.R

            l.lqr_control_nidaq()
            self.signals.returned.emit(l)

        except BaseException:
            error_w = Error_window()
            error_w.exec()

        # Calling send data method
        #if not s.error_path:
        #    s.step_response_nidaq()
        #    self.signals.returned.emit(s)

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

        if not any(a.isChecked() for a in self.ao_actions) and self.ao_actions:
            self.ao_actions[0].setChecked(True)
            selected = [self.ao_actions[0].text()]

        self.ao_channel_combo.lineEdit().setText(", ".join(selected))

    def get_selected_ao(self):
        selected = [a.text() for a in self.ao_actions if a.isChecked()]
        return selected if selected else (self.available_ao_channels[:1] if self.available_ao_channels else [])
    
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

        print("LQR matrices updated")
    
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