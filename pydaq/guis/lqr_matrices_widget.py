from matplotlib.table import table
import numpy as np
from ..uis.ui_PYDAQ_lqr_matrices_widget import Ui_Select_LQR_Matrices_Widget
from PySide6.QtWidgets import QFileDialog, QWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon

from ..get_data import GetData
from .error_window_gui import Error_window
from pydaq.utils.signals import GuiSignals

class Select_LQR_Matrices_Widget(QWidget, Ui_Select_LQR_Matrices_Widget):

    dataEntered = Signal(dict)

    def __init__(self, simulate=False, *args):
        super(Select_LQR_Matrices_Widget, self).__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon(':/imgs/imgs/favicon.ico'))
        self.simulate_mode = simulate

        self.signals = GuiSignals()

        # Standard Matrices (Lookup Dictionary)
        self.default_matrices = {
            'A': np.array([[1.0, 0.1], [0.0, 1.0]]),
            'B': np.array([[0.0, 0.05], [0.1, 0.1]]),
            'C': np.eye(2),              # NEW
            'D': np.zeros((2, 2)),        # NEW
            'Q': np.eye(2), # Identity 2x2
            'R': np.eye(2)
        }

        # Signals 
        # connections
        self.spin_states.valueChanged.connect(self.update_sizes)
        self.spin_inputs.valueChanged.connect(self.update_sizes)
        
        self.select_button.clicked.connect(self.send_data)

        # Default values
        self.spin_states.setValue(2)
        self.spin_inputs.setValue(2)
        
        self.update_sizes()

    def update_sizes(self):

        n = self.spin_states.value()
        m = self.spin_inputs.value()

        self._resize_table(self.tableA, n, n, 'A')
        self._resize_table(self.tableB, n, m, 'B')
        self._resize_table(self.tableC, n, n, 'C')   
        self._resize_table(self.tableD, n, m, 'D')   
        self._resize_table(self.tableQ, n, n, 'Q')
        self._resize_table(self.tableR, m, m, 'R')

    
    def _resize_table(self, table, rows, cols, matrix_key=None):

        table.setRowCount(rows)
        table.setColumnCount(cols)

        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setVisible(False)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for i in range(rows):
            for j in range(cols):
                val = "0"
                # Check if we have data for this specific matrix and position
                if matrix_key in self.default_matrices:
                    m = self.default_matrices[matrix_key]
                    # Ensure the indices are within the bounds of the stored matrix
                    if i < m.shape[0] and j < m.shape[1]:
                        val = str(m[i, j]).replace('.', ',')

                # Use setItem only if the item doesn't exist or to update the text
                if table.item(i, j) is None:
                    table.setItem(i, j, QTableWidgetItem(val))
                else:
                    table.item(i, j).setText(val)
    # ------------------------------------------------

    def read_matrix(self, table):
        rows = table.rowCount()
        cols = table.columnCount()
        M = np.zeros((rows, cols))

        for i in range(rows):
            for j in range(cols):
                item = table.item(i, j)
                if item is None or item.text() == "":
                    value = 0.0
                else:
                    # --- NEW: Replace comma with dot for Brazilian standard support ---
                    raw_text = item.text().replace(',', '.')
                    try:
                        value = float(raw_text)
                    except ValueError:
                        value = 0.0 # Safety if user types letters
                
                M[i, j] = value
        return M
    
    def send_data(self):

        try:

            A = self.read_matrix(self.tableA)
            B = self.read_matrix(self.tableB)
            C = self.read_matrix(self.tableC)   
            D = self.read_matrix(self.tableD)   
            Q = self.read_matrix(self.tableQ)
            R = self.read_matrix(self.tableR)

            data = {
                "A": A,
                "B": B,
                "C": C,
                "D": D,
                "Q": Q,
                "R": R,
                "n": self.spin_states.value(),
                "m": self.spin_inputs.value()
            }

            self.dataEntered.emit(data)
            self.close()

        except Exception:
            error_w = Error_window()
            error_w.exec()
