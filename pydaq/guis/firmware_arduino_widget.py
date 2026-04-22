import os
import subprocess
import serial.tools.list_ports
from importlib.resources import files
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import QThread, Signal, QTimer

# Import generated UI class
from pydaq.uis.ui_PyDAQ_Firmware_Arduino import Ui_Firmware 

class FirmwareUploadWorker(QThread):
    """
    Worker thread that handles heavy subprocess calls.
    Communicates progress checkpoints to the main GUI.
    """
    step_reached = Signal(int) # Signal to indicate a subprocess has finished
    status_update = Signal(str)
    finished_upload = Signal(bool, str)

    def __init__(self, com_port, fqbn="arduino:avr:uno"):
        super().__init__()
        self.com_port = com_port
        self.fqbn = fqbn

    def run(self):
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        
        try:
            # Resolve paths
            cli_path_obj = files("pydaq.tools") / "arduino-cli.exe"
            sketch_path_obj = files("pydaq.arduino_code") / "arduino_code.ino"
            
            cli_path = str(cli_path_obj)
            sketch_path = str(sketch_path_obj)

            # --- PATH VALIDATION ---
            if not os.path.exists(cli_path):
                self.finished_upload.emit(False, f"Critical Error: arduino-cli.exe not found at {cli_path}")
                return
            
            if not os.path.exists(sketch_path):
                self.finished_upload.emit(False, f"Critical Error: Firmware sketch not found at {sketch_path}")
                return

            # --- STEP 1: Core Update (Target: 20%) ---
            self.status_update.emit("Updating Arduino index...")
            subprocess.run([cli_path, "config", "init"], capture_output=True, creationflags=flags)
            subprocess.run([cli_path, "core", "update-index"], capture_output=True, creationflags=flags)
            self.step_reached.emit(20)

            # --- STEP 2: Core Install (Target: 60%) ---
            check = subprocess.run([cli_path, "core", "list"], capture_output=True, text=True, creationflags=flags)
            if "arduino:avr" not in check.stdout:
                self.status_update.emit("Installing AVR core (first run)...")
                res = subprocess.run([cli_path, "core", "install", "arduino:avr"], capture_output=True, creationflags=flags)
                if res.returncode != 0:
                    # SAFE DECODE
                    err_msg = res.stderr.decode('utf-8', errors='replace')
                    self.finished_upload.emit(False, f"Core installation failed: {err_msg}")
                    return
            self.step_reached.emit(60)

            # --- STEP 3: Compilation (Target: 85%) ---
            self.status_update.emit("Compiling PyDAQ firmware...")
            res_compile = subprocess.run([cli_path, "compile", "--fqbn", self.fqbn, sketch_path], capture_output=True, creationflags=flags)
            if res_compile.returncode != 0:
                err_msg = res_compile.stderr.decode('utf-8', errors='replace')
                self.finished_upload.emit(False, f"Compilation failed: {err_msg}")
                return
            self.step_reached.emit(85)

            # --- STEP 4: Upload (Target: 100%) ---
            self.status_update.emit(f"Uploading to {self.com_port}...")
            res_upload = subprocess.run([cli_path, "upload", "-p", self.com_port, "--fqbn", self.fqbn, sketch_path], capture_output=True, creationflags=flags)
            if res_upload.returncode != 0:
                err_msg = res_upload.stderr.decode('utf-8', errors='replace')
                self.finished_upload.emit(False, f"Upload failed: {err_msg}")
                return

            self.step_reached.emit(100)
            self.finished_upload.emit(True, "Firmware successfully uploaded!")

        except Exception as e:
            self.finished_upload.emit(False, f"Unexpected worker error: {str(e)}")

class FirmwareUploadWidget(QWidget, Ui_Firmware):
    def __init__(self, *args):
        super(FirmwareUploadWidget, self).__init__(*args)
        self.setupUi(self)
        self.setWindowTitle("PyDAQ - Firmware Manager")
        self.setWindowIcon(QIcon(':/imgs/imgs/favicon.ico'))
        
        # Internal state for smooth progress animation
        self.current_display_value = 0
        self.target_step_value = 0
        
        # Timer for smooth progress bar transition
        self.smooth_timer = QTimer()
        self.smooth_timer.timeout.connect(self._animate_progress)
        
        # Connect UI signals
        self.upload_button.released.connect(self.start_upload)
        self.reload_devices.released.connect(self.update_com_ports)
        
        # Initial port scan
        self.update_com_ports()

    def update_com_ports(self):
        """Refreshes the list of available COM ports."""
        self.com_ports = [i.description for i in serial.tools.list_ports.comports()]
        self.device_combo.clear()
        self.device_combo.addItems(self.com_ports)

    def start_upload(self):
        """Initializes the background upload process."""
        if self.upload_button.text() == "Finished":
            self.close()
            return
        
        if self.device_combo.currentIndex() == -1:
            QMessageBox.warning(self, "Warning", "Please select a valid COM port.")
            return

        # Map description back to device name (e.g. COM3)
        selected_index = self.device_combo.currentIndex()
        com_port = serial.tools.list_ports.comports()[selected_index].name

        # Lock UI and reset progress state
        self.upload_button.setEnabled(False)
        self.reload_devices.setEnabled(False)
        self.current_display_value = 0
        self.target_step_value = 15 # Initial fake progress while starting
        self.progressBar.setValue(0)
        
        # Start the animation timer (100ms interval)
        self.smooth_timer.start(100)

        # Setup and start background worker
        self.worker = FirmwareUploadWorker(com_port)
        self.worker.step_reached.connect(self._on_step_reached)
        self.worker.finished_upload.connect(self.upload_finished)
        self.worker.start()

    def _on_step_reached(self, val):
        """Updates the animation target when a real step is completed."""
        self.target_step_value = val

    def _animate_progress(self):
        """Incrementally increases progress bar value for a smooth visual effect."""
        if self.current_display_value < self.target_step_value:
            self.current_display_value += 1
            self.progressBar.setValue(self.current_display_value)
        
        # Stop timer if we hit 100%
        if self.current_display_value >= 100:
            self.smooth_timer.stop()

    def upload_finished(self, success, message):
        """Finalizes the UI state based on success or failure."""
        self.smooth_timer.stop()
        self.upload_button.setEnabled(True)
        self.reload_devices.setEnabled(True)
        
        if success:
            self.progressBar.setValue(100)
            self.upload_button.setText("Finished")
            QMessageBox.information(self, "Success", message)
        else:
            self.progressBar.setValue(0)
            self.upload_button.setText("Retry")
            QMessageBox.critical(self, "Error", message)