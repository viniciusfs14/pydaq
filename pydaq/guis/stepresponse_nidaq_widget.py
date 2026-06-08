import os
import warnings

from PySide6.QtWidgets import QFileDialog, QWidget, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from pydaq.utils.signals import GuiSignals
from pydaq.utils.base import Base, NIDAQ_AVAILABLE, TerminalConfiguration, nidaqmx, System, ClickableLineEdit

from ..uis.ui_PyDAQ_step_response_NIDAQ_widget import Ui_NIDAQ_StepResponse_W
from .error_window_gui import Error_window

from ..step_response import StepResponse


class StepResponse_NIDAQ_Widget(QWidget, Ui_NIDAQ_StepResponse_W):
    def __init__(self, *args):
        super(StepResponse_NIDAQ_Widget, self).__init__()
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
        self.start_step_response.released.connect(self.start_func_step_response)
        self.device_combo.currentIndexChanged.connect(self.update_channels)
        self.label_warning.hide()
        self.pidshow()
        self.pid_radio_group.buttonClicked.connect(self.pidshow)
        self.plot_radio_group.buttonToggled.connect(self._update_warning_label)
        self.reload_devices.released.connect(self.reload_devices_handler)
        self.signals = GuiSignals()

    def _update_warning_label(self):
        if self.yes_rt_plot_radio.isChecked():
            self.label_warning.show()
        else:
            self.label_warning.hide()
            
    def start_func_step_response(self):

        # Safety lock: prevents dialog from opening if NI-DAQmx drivers are not found
        if not NIDAQ_AVAILABLE:
            warnings.warn("[PYDAQ] NI-DAQmx drivers not found! Cannot start hardware control.")
            error_w = Error_window()
            error_w.ui.confirm.setText("NI-DAQmx drivers not found! Please install NI-MAX.")
            error_w.exec()
            return
        
        try:
            self.get_sintony_type()

            # Instantiating the StepResponse class
            s = StepResponse()

            # 1. Config Validation: Path
            if self.yes_save_radio.isChecked() and self.path_line_edit.text() == "":
                raise ValueError("[PYDAQ] Missing configuration: Empty save path.")
            s.path = self.path_line_edit.text()

            s.calculate_pid = True if self.pid_radio_group.checkedId() == -2 else False

            # 2. Config Validation: Channels & Dimensions
            selected_ao = self.get_selected_ao()
            selected_ai = self.get_selected_ai()

            if s.calculate_pid:
                if len(selected_ai) != 1 or len(selected_ao) != 1:
                    raise ValueError(
                        "[PYDAQ] Dimension mismatch: PID tuning requires exactly 1 AI channel and 1 AO channel (SISO)."
                    )
            
            # 3. Config Validation: COM Port
            if selected_ao and selected_ai:
                s.device = selected_ao[0].split("/")[0]
                s.channels = [ch.split("/")[1] for ch in selected_ai]
                s.ao_channels = [ch.split("/")[1] for ch in selected_ao]
            else:
                raise ValueError("[PYDAQ] Missing configuration: Please ensure device and channel are properly defined.")

            s.terminal = s.term_map[self.terminal_config_combo.currentText()]
            s.step_max = self.step_range_max_in.value()
            s.step_min = self.step_range_min_in.value()
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
            s.sintony_type =  self.sintony_type
            
            # Restarting variables
            self.time_var, self.input, self.output = [], [], []

            # Execute
            s.step_response_nidaq()
            self.signals.returned.emit(s)

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
            else:
                error_w.ui.confirm.setText("Missing configuration: Please ensure device, channels, and save path are properly defined.")
            
            error_w.exec()
            
            # Use locals() check in case 's' failed to instantiate
            if 's' in locals():
                s.error_path = True
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

    def pidshow(self):
        self.enabled = True if self.pid_radio_group.checkedId() == -2 else False
        if self.enabled is False: #Simulate = False
            self.PID_comboBox.setEnabled(False)
        else:
            self.PID_comboBox.setEnabled(True)

    def get_sintony_type(self):
        if self.PID_comboBox.isEnabled():
            self.sintony_type = self.PID_comboBox.currentIndex() # Can be 0, 1 or 2
        else:
            self.sintony_type = None # None if desabled

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