import os
import subprocess
import serial.tools.list_ports
from PySide6.QtWidgets import QWidget, QMessageBox, QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QThread, Signal

# Adjust the import according to your UI file name
from pydaq.uis.ui_PyDAQ_Firmware_Arduino import Ui_Firmware 


class FirmwareUploadWorker(QThread):
    """
    Worker thread to handle the firmware compilation and upload in the background,
    preventing the main GUI from freezing.
    """
    # Signals to communicate with the main GUI
    progress_update = Signal(int)
    status_update = Signal(str)
    finished_upload = Signal(bool, str)

    def __init__(self, com_port, fqbn="arduino:avr:uno"):
        super().__init__()
        self.com_port = com_port
        self.fqbn = fqbn

    def run(self):
        # Setup paths
        # O base_dir aponta para a pasta principal do módulo: pydaq/pydaq/
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        cli_path = os.path.join(base_dir, "tools", "arduino-cli.exe")
        
        sketch_path = os.path.join(base_dir, "arduino_code", "arduino_code.ino")
        
        # Basic path validation
        if not os.path.exists(cli_path):
            self.finished_upload.emit(False, f"Arduino CLI not found at:\n{cli_path}")
            return
            
        if not os.path.exists(sketch_path):
            self.finished_upload.emit(False, f"Firmware file not found at:\n{sketch_path}")
            return

        try:
            # 1. Compilation Step
            self.status_update.emit("Compiling firmware...")
            self.progress_update.emit(20)

            compile_cmd = [cli_path, "compile", "--fqbn", self.fqbn, sketch_path]
            res_compile = subprocess.run(compile_cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if res_compile.returncode != 0:
                self.finished_upload.emit(False, f"Compilation failed:\n{res_compile.stderr}")
                return

            self.progress_update.emit(60)

            # 2. Upload Step
            self.status_update.emit(f"Uploading to {self.com_port}...")
            
            upload_cmd = [cli_path, "upload", "-p", self.com_port, "--fqbn", self.fqbn, sketch_path]
            res_upload = subprocess.run(upload_cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)

            if res_upload.returncode != 0:
                self.finished_upload.emit(False, f"Upload failed:\n{res_upload.stderr}")
                return

            # Success
            self.progress_update.emit(100)
            self.status_update.emit("Upload Successful!")
            self.finished_upload.emit(True, "Firmware successfully installed.")

        except Exception as e:
            self.finished_upload.emit(False, f"An unexpected error occurred:\n{str(e)}")


class FirmwareUploadWidget(QWidget, Ui_Firmware):
    def __init__(self, *args):
        super(FirmwareUploadWidget, self).__init__(*args)
        self.setupUi(self)
        self.setWindowTitle("Arduino Firmware Upload")
        self.setWindowIcon(QIcon('docs/img/favicon.ico'))

        # Variables
        self.com_ports = []
        self.worker = None

        # Resetting UI elements
        self.progressBar.setValue(0)
        self.upload_button.setText("Upload")

        # Connecting signals
        self.upload_button.released.connect(self.start_upload)
        self.reload_devices.released.connect(self.update_com_ports)
        
        # Initialize ports
        self.update_com_ports()

    def update_com_ports(self):
        """Updating available COM ports"""
        self.com_ports = [i.description for i in serial.tools.list_ports.comports()]
        selected = self.device_combo.currentText()

        self.device_combo.clear()
        self.device_combo.addItems(self.com_ports)
        
        index_current = self.device_combo.findText(selected)
        if index_current != -1:
            self.device_combo.setCurrentIndex(index_current)

    def start_upload(self):
        """Starts the background thread to upload the firmware"""

        # If the text is "Finished", close the window and interrupt the function.
        if self.upload_button.text() == "Finished":
            self.close()
            return
        
        if self.device_combo.currentIndex() == -1:
            QMessageBox.warning(self, "Warning", "Please select a valid COM port.")
            return

        # Extract the exact COM port name (e.g., 'COM7')
        selected_desc = self.device_combo.currentText()
        com_port = serial.tools.list_ports.comports()[self.com_ports.index(selected_desc)].name

        # Lock the UI to prevent double clicking
        self.upload_button.setEnabled(False)
        self.upload_button.setText("Processing...")
        self.reload_devices.setEnabled(False)
        self.progressBar.setValue(10)

        # NOTE: If you add a combo box for Arduino Boards later, get the FQBN here.
        # For now, it defaults to Arduino Uno ("arduino:avr:uno")
        board_fqbn = "arduino:avr:uno"

        # Instantiate and start the worker thread
        self.worker = FirmwareUploadWorker(com_port, board_fqbn)
        self.worker.progress_update.connect(self.update_progress_bar)
        self.worker.status_update.connect(self.update_status)
        self.worker.finished_upload.connect(self.upload_finished)
        self.worker.start()

    def update_progress_bar(self, value):
        """Updates the progress bar value"""
        self.progressBar.setValue(value)

    def update_status(self, message):
        """Updates a status label if you have one, or print to terminal"""
        print(message)
        # If you have a label in Qt Designer named 'status_label', use:
        # self.status_label.setText(message)

    def upload_finished(self, success, message):
        """Handles the end of the upload process"""
        # Unlock the UI
        self.upload_button.setEnabled(True)
        self.reload_devices.setEnabled(True)
        
        if success:
            self.upload_button.setText("Finished")
            QMessageBox.information(self, "Success", message)
            # Optional: reset button text after a few seconds
            # self.upload_button.setText("Upload")
        else:
            self.upload_button.setText("Retry")
            self.progressBar.setValue(0)
            QMessageBox.critical(self, "Error", message)