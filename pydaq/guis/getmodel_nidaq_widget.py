import os
import warnings

from sysidentpy.parameter_estimation import estimators

from PySide6.QtWidgets import QFileDialog, QWidget
from PySide6.QtCore import Qt
from pydaq.utils.signals import GuiSignals
from pydaq.utils.base import Base, NIDAQ_AVAILABLE, TerminalConfiguration, nidaqmx, System

from ..uis.ui_PyDAQ_get_model_NIDAQ_widget import Ui_Arduino_GetModel_W
from .error_window_gui import Error_window
from ..utils import *

from ..get_model import GetModel
from .prbs_config_widget import PRBSConfig_W
from .getmodel_sysconfig_arduino_widget import SysIdentConfig_W


class GetModel_Nidaq_Widget(QWidget, Ui_Arduino_GetModel_W):
    def __init__(self, *args):
        super(GetModel_Nidaq_Widget, self).__init__()
        self.setupUi(self)

        # Gathering nidaq info
        self._nidaq_info()

        # Discover AO and AI channels
        try:
            self.available_ao_channels = nidaqmx.system.device.Device(
                self.device_names[0]
            ).ao_physical_chans.channel_names
            self.available_ai_channels = nidaqmx.system.device.Device(
                self.device_names[0]
            ).ai_physical_chans.channel_names
        except BaseException:
            self.available_ao_channels = []
            self.available_ai_channels = []

        # Setting initial widget values
        self.device_combo.addItems(self.device_type)
        
        # Populate combo boxes with discovered channels
        self.ao_channel_combo.addItems(self.available_ao_channels)
        self.ai_channel_combo.addItems(self.available_ai_channels)

        self.path_line_edit.setText(
            os.path.join(os.path.expanduser("~"), "Desktop")
        )
        
        self.terminal_config_combo.addItems(["Diff", "RSE", "NRSE"])
        self.inp_signal_combo.addItem("PRBS")

        # Logic parameters
        self.signal_bits = 6
        self.signal_seed = 100
        self.signal_var_tb = 1
        self.degree = 2
        self.out_lag = 3
        self.inp_lag = 3
        self.num_info_val = 6
        self.estimator = "least_squares"
        self.ext_lsq = False
        self.perc_value = 30

        # Connecting signals
        self.path_folder_browse.released.connect(self.locate_path)
        self.start_get_model.released.connect(self.start_func_get_model)
        self.device_combo.currentIndexChanged.connect(self.update_channels)
        self.reload_devices.released.connect(self.reload_devices_handler)
        self.config_signal_button.released.connect(self.open_sig_config)
        self.system_settings_button.released.connect(self.open_sysident_config)
        self.label_warning.hide()
        self.plot_radio_group.buttonToggled.connect(self._update_warning_label)

    def _update_warning_label(self):
        if self.yes_rt_plot_radio.isChecked():
            self.label_warning.show()
        else:
            self.label_warning.hide()
            
    def locate_path(self):  # Calling the Folder Browser Widget
        output_folder_path = QFileDialog.getExistingDirectory(
            self, caption="Choose a folder to save the data file"
        )
        if output_folder_path == "":
            pass
        else:
            self.path_line_edit.setText(output_folder_path.replace("/", "\\"))

    def open_sig_config(self):
        if self.inp_signal_combo.currentText() == "PRBS":
            # Creating Instance of the config window
            config = PRBSConfig_W()

            # Setting default values
            config.ui.prbs_bits_in.setValue(self.signal_bits)
            config.ui.prbs_seed_in.setText(str(self.signal_seed))
            config.ui.prbs_tb_var_in.setValue(self.signal_var_tb)
            config.ui.prbs_seed_in.setCursorPosition(len(str(self.signal_seed)))

            # Executing the config window
            config.exec()

            # Fetching data
            self.signal_bits = config.ui.prbs_bits_in.value()
            self.signal_seed = int(config.ui.prbs_seed_in.text())
            self.signal_var_tb = config.ui.prbs_tb_var_in.value()

    def open_sysident_config(self):
        # Creating Instance of the config window
        config = SysIdentConfig_W()

        # Setting default values
        config.ui.degree_sysid_in.setValue(self.degree)
        config.ui.out_lag_sysid_in.setValue(self.out_lag)
        config.ui.inp_lag_sysid_in.setValue(self.inp_lag)
        config.ui.num_inf_value_sysid_in.setValue(self.num_info_val)
        config.ui.esti_sysid_in.addItems(list(self.estimators_handle_dict.keys()))

        # Handling the default value for radio button
        if self.ext_lsq:
            config.ui.true_ext_lsq.setChecked(True)
        else:
            config.ui.false_ext_lsq.setChecked(True)

        config.ui.perc_data_val_in.setValue(self.perc_value)

        # Handling the past estimator value
        for key_d, value_d in self.estimators_handle_dict.items():
            if value_d == self.estimator:
                config.ui.esti_sysid_in.setCurrentText(key_d)

        # Executing the config window
        config.exec()

        # Fetching the data from the popup to the main widget
        self.degree = config.ui.degree_sysid_in.value()
        self.out_lag = config.ui.out_lag_sysid_in.value()
        self.inp_lag = config.ui.inp_lag_sysid_in.value()
        self.num_info_val = config.ui.num_inf_value_sysid_in.value()
        self.estimator = self.estimators_handle_dict[
            config.ui.esti_sysid_in.currentText()
        ]
        self.ext_lsq = (
            True if config.ui.extended_lsq_radio_group.checkedId() == -2 else False
        )
        self.perc_value = config.ui.perc_data_val_in.value()

    def start_func_get_model(self):  # Start getting model

        if not NIDAQ_AVAILABLE:
            error_w = Error_window()
            warnings.warn("[PYDAQ] NI-DAQmx drivers not found! Cannot start hardware acquisition.")
            error_w.ui.confirm.setText("NI-DAQmx drivers not found! Cannot start hardware acquisition.")
            error_w.exec()
            return
        
        try:
            # Instantiating the GetModel class
            g = GetModel()

            # 1. Config Validation: Path
            if self.yes_save_radio.isChecked() and self.path_line_edit.text() == "":
                raise ValueError("[PYDAQ] Missing configuration: Empty save path.")
            g.path = self.path_line_edit.text()

            # Single Channel Acquisition logic
            ao_ch = self.ao_channel_combo.currentText()
            ai_ch = self.ai_channel_combo.currentText()

            if not ao_ch or not ai_ch:
                raise ValueError("[PYDAQ] Dimension mismatch: Please ensure device and channel are properly defined.")
            
            # Formatting channels for the core module (Expected as lists of 1 element for legacy support)
            g.device = ao_ch.split("/")[0]
            g.channels = [ai_ch.split("/")[1]]
            g.ao_channels = [ao_ch.split("/")[1]]

            g.terminal = g.term_map[self.terminal_config_combo.currentText()]
            g.ts = self.Ts_in.value()
            g.start_save_time = self.save_time_in.value()
            g.session_duration = self.sesh_dur_in.value()
            if self.yes_rt_plot_radio.isChecked(): # Assumindo que 'yes_radio' agora significa 'Real time'
                g.plot_mode = 'realtime'
            elif self.yes_ate_plot_radio.isChecked(): # Supondo que você criou um radio button com este nome
                g.plot_mode = 'end'
            else: # self.No_radio.isChecked()
                g.plot_mode = 'no'
            g.save = True if self.save_radio_group.checkedId() == -2 else False

            g.prbs_bits = self.signal_bits
            g.prbs_seed = self.signal_seed
            g.var_tb = self.signal_var_tb

            g.degree = self.degree
            g.out_lag = self.out_lag
            g.inp_lag = self.inp_lag
            g.num_info_val = self.num_info_val
            g.estimator = self.estimator
            g.ext_lsq = self.ext_lsq
            g.perc_value = self.perc_value

            # Restarting variables
            g.data = []
            g.time_var = []
            g.out_read = []
            g.error_path = False

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
            
            # Use locals() check in case 'g' failed to instantiate
            if 'g' in locals():
                g.error_path = True
            return # Exit function to prevent execution

        if not g.error_path:
            # Calling data aquisition method
            g.get_model_nidaq()

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
                new_ai = nidaqmx.system.device.Device(dev_name).ai_physical_chans.channel_names
            else:
                new_ao = []
                new_ai = []
        except BaseException:
            new_ao = []
            new_ai = []

        self.available_ao_channels = new_ao
        self.available_ai_channels = new_ai

        # Updating combo boxes for single channel selection
        self.ao_channel_combo.clear()
        self.ai_channel_combo.clear()
        
        self.ao_channel_combo.addItems(self.available_ao_channels)
        self.ai_channel_combo.addItems(self.available_ai_channels)

        # Setting default indices if channels exist
        if self.available_ao_channels:
            self.ao_channel_combo.setCurrentIndex(0)
        if self.available_ai_channels:
            self.ai_channel_combo.setCurrentIndex(0)

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