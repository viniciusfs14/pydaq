import os
import serial
import serial.tools.list_ports
from sysidentpy.parameter_estimation import estimators

from PySide6.QtWidgets import QFileDialog, QWidget
from PySide6.QtCore import Qt

from ..uis.ui_PyDAQ_get_model_Arduino_widget import Ui_Arduino_GetModel_W
from .error_window_gui import Error_window
from ..utils import *

from ..get_model import GetModel
from .prbs_config_widget import PRBSConfig_W
from .getmodel_sysconfig_arduino_widget import SysIdentConfig_W


class GetModel_Arduino_Widget(QWidget, Ui_Arduino_GetModel_W):
    def __init__(self, *args):
        super(GetModel_Arduino_Widget, self).__init__()
        self.setupUi(self)

        # Connecting signals
        self.config_signal_button.released.connect(self.open_sig_config)
        self.system_settings_button.released.connect(self.open_sysident_config)
        self.reload_devices.released.connect(self.update_com_ports)
        self.path_folder_browse.released.connect(self.locate_path)
        self.start_get_model.released.connect(self.start_func_get_model)
        self.label_warning.hide()
        self.plot_radio_group.buttonToggled.connect(self._update_warning_label)

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

        estimators_list = [i for i in estimators.__dict__.keys() if i[:1] != "_"]
        self.estimators_handle_dict = dict()

        for i in estimators_list:
            self.estimators_handle_dict[" ".join(i.split("_")).capitalize()] = i

        self.update_com_ports()
        self.path_line_edit.setText(
            os.path.join(os.path.expanduser("~"), "Desktop")
        )

        # Available channels (Arduino logic)
        self.available_ai_channels = [f"A{i}" for i in range(6)]
        self.available_ao_channels = [f"D{i}" for i in range(0, 14)]

        # Updating combo boxes for single channel selection
        self.ao_channel_combo.clear()
        self.ai_channel_combo.clear()
        
        self.ao_channel_combo.addItems(self.available_ao_channels)
        self.ai_channel_combo.addItems(self.available_ai_channels)

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
        try:
            # Instantiating the GetModel class
            g = GetModel()

            # 1. Config Validation: Path
            if self.yes_save_radio.isChecked() and self.path_line_edit.text() == "":
                raise ValueError("[PYDAQ] Missing configuration: Empty save path.")
            
            # 2. Single Channel Acquisition logic
            ao_ch = self.ao_channel_combo.currentText()
            ai_ch = self.ai_channel_combo.currentText()

            g.path = self.path_line_edit.text()

            g.channels = [ai_ch]
            g.ao_channels = [ao_ch]
            
            if not ao_ch or not ai_ch:
                raise ValueError("[PYDAQ] Dimension mismatch: Please ensure device and channel are properly defined.")

            # 3. Config Validation: COM Port
            try:
                g.com_port = serial.tools.list_ports.comports()[
                    self.com_ports.index(self.device_combo.currentText())
                ].name
                #s.com_port = serial.tools.list_ports.comports()[999].name # Test Error
            except (ValueError, IndexError):
                raise ValueError("[PYDAQ] Missing configuration: No valid COM port selected.")
            
            # 4. GUI-Level Firmware Verification (Fail Fast)
            try:
                g._open_serial()
                firmware_ok = g._verify_arduino_firmware()
                g.ser.close() # CRITICAL: Release the port for the actual acquisition thread!
            except Exception:
                firmware_ok = False
                if hasattr(g, 'ser') and g.ser.is_open:
                    g.ser.close()

            if not firmware_ok:
                raise ValueError("[PYDAQ] PyDAQ Firmware not detected on this board! Please go to the top menu and click on 'Arduino Firmware' to upload the correct code.")
            
            # 5. Remaining Parameters
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
            elif "Firmware" in err_msg:
                error_w.ui.confirm.setText("Firmware not detected on this board. Please go to the top menu and click on 'Arduino Firmware' to upload the correct code.")
            else:
                error_w.ui.confirm.setText("Missing configuration: Please ensure device, channels, and save path are properly defined.")
            error_w.exec()
            
            # Use locals() check in case 'g' failed to instantiate
            if 'g' in locals():
                g.error_path = True
            return # Exit function to prevent execution

        # Execute
        if not g.error_path:
            # Calling data aquisition method
            g.get_model_arduino()