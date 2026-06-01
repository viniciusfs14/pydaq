from PySide6.QtWidgets import QDialog

from ..uis.ui_PRBS_Info_widget import Ui_PRBS_Info
from ..utils import *
from PySide6.QtGui import QIcon

class PRBSConfig_W(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_PRBS_Info()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(':/imgs/imgs/favicon.ico'))
        
    def close_dialog(self):
        self.close()
