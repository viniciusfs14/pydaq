import sys

from PySide6 import QtWidgets
from .uis.ui_PyDAQ_Base import Ui_PydaqGlobal
from pydaq.guis.benchmarking_widget import BenchmarkingWidget 
from pydaq.guis.firmware_arduino_widget import FirmwareUploadWidget 
from pydaq.guis.benchmarking_widget import BenchmarkingNIWidget
import webbrowser
from pydaq.utils.base import NIDAQ_AVAILABLE


class PYDAQ_Global_GUI(QtWidgets.QMainWindow, Ui_PydaqGlobal):
    def __init__(self):
        super(PYDAQ_Global_GUI, self).__init__()
        self.setupUi(self)
        self.nidaq_tabs.setHidden(True)
        self.logo.released.connect(self.open_pydaq_website)

        # Connecting Signals to access data
        self.fetched_object = None

        self.get_ino_placeholder.signals.returned.connect(self.fetch_object)
        self.get_nidaq_placeholder.signals.returned.connect(self.fetch_object)
        self.send_ino_placeholder.signals.returned.connect(self.fetch_object)
        self.send_nidaq_placeholder.signals.returned.connect(self.fetch_object)
        self.step_ino_placeholder.signals.returned.connect(self.fetch_object)
        self.step_nidaq_placeholder.signals.returned.connect(self.fetch_object)
        self.actionArduino_3.triggered.connect(self.open_firmware_upload_arduino)
        self.actionArduino_1.triggered.connect(self.open_benchmarking_arduino)
        self.actionNIDAQ_1.triggered.connect(self.open_benchmarking_nidaq)
        self.actionNIDAQ_3.triggered.connect(self.open_nidaq_drivers_website)
        self.actionDocumentation.triggered.connect(self.open_pydaq_website)

        # NIDAQ WARNING CONTROL
        self.nidaq_warning_shown = False
        self.radioButton_2.toggled.connect(self._check_nidaq_on_click)

    def fetch_object(self, fetched_obj):
        self.fetched_object = fetched_obj

    def open_pydaq_website(self):
        url = "https://samirmartins.github.io/pydaq/"
        webbrowser.open(url)

    def open_nidaq_drivers_website(self):
        url = "https://www.ni.com/en-us/support/downloads/drivers/download.ni-daqmx.html"
        webbrowser.open(url)

    def open_benchmarking_arduino(self):
        self.benchmarking = BenchmarkingWidget()
        self.benchmarking.show()

    def open_firmware_upload_arduino(self):
        self.firmware_upload = FirmwareUploadWidget()
        self.firmware_upload.show()

    def open_benchmarking_nidaq(self):
        self.benchmarking = BenchmarkingNIWidget()
        self.benchmarking.show()

    def _check_nidaq_on_click(self, checked):
        """The warning is triggered only if the user attempts to access the NIDAQ tab without the drivers."""
        if checked and not NIDAQ_AVAILABLE and not self.nidaq_warning_shown:
            QtWidgets.QMessageBox.warning(
                self,
                "Missing NI-DAQmx Drivers",
                "PyDAQ could not find the National Instruments drivers (NI-DAQmx).\n\n"
                "Arduino and Simulation features will work perfectly, but NI-DAQ hardware execution will be blocked.\n"
                "Please install NI-MAX if you intend to use National Instruments hardware."
            )
            # Marca como verdadeiro para não avisar de novo caso ele fique clicando nos botões
            self.nidaq_warning_shown = True


def PydaqGui():
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()
    window = PYDAQ_Global_GUI()
    window.show()

    try:
        app.exec()
        return window.fetched_object
    except SystemExit:
        print("")