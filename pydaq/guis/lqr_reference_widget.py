import numpy as np
from PySide6.QtWidgets import QWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon

# Ensure this matches your generated UI file name
from ..uis.ui_PYDAQ_lqr_reference_state_widget import Ui_Select_LQR_References
from .error_window_gui import Error_window
from pydaq.utils.signals import GuiSignals

class Select_LQR_Reference_Widget(QWidget, Ui_Select_LQR_References):

    dataEntered = Signal(dict)

    def __init__(self, n_states=2, n_inputs=2, *args):
        super(Select_LQR_Reference_Widget, self).__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon(':/imgs/imgs/favicon.ico'))

        self.signals = GuiSignals()

        # Internal storage for dimensions
        self.n_states = n_states
        self.n_inputs = n_inputs

        # Standard Reference Matrices (Lookup Dictionary for persistence)
        self.default_matrices = {
            'X': np.zeros((self.n_states, 1)),
            'U': np.zeros((self.n_inputs, 1))
        }

        # UI Updates: Using labels with the new names provided
        if hasattr(self, 'nl_states'):
            self.nl_states.setText(str(self.n_states))
        
        if hasattr(self, 'nl_inputs'):
            self.nl_inputs.setText(str(self.n_inputs))

        # Connections
        self.select_button.clicked.connect(self.send_data)

        # Initial table setup - This will populate with default_matrices values
        self.update_sizes()

    def update_sizes(self):
        """
        Updates the reference tables based on fixed system dimensions.
        References (X_ref and U_eq) are always column vectors (n x 1 and m x 1).
        """
        # Resize for column vectors
        self._resize_table(self.tableX, self.n_states, 1, 'X')
        self._resize_table(self.tableU, self.n_inputs, 1, 'U')

    def _resize_table(self, table, rows, cols, matrix_key=None):
        table.setRowCount(rows)
        table.setColumnCount(cols)

        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for i in range(rows):
            for j in range(cols):
                val = "0.0"
                # Check if we have "cached" data to keep the user values
                if matrix_key in self.default_matrices:
                    m = self.default_matrices[matrix_key]
                    if i < m.shape[0] and j < m.shape[1]:
                        # Format for Brazilian standard display
                        val = str(m[i, j]).replace('.', ',')

                if table.item(i, j) is None:
                    table.setItem(i, j, QTableWidgetItem(val))
                else:
                    table.item(i, j).setText(val)

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
                    # Replace comma with dot for numerical processing
                    raw_text = item.text().replace(',', '.')
                    try:
                        value = float(raw_text)
                    except ValueError:
                        value = 0.0 
                
                M[i, j] = value
        return M
    
    def send_data(self):
        """
        Emits the reference data and closes the widget.
        """
        try:
            X = self.read_matrix(self.tableX)
            U = self.read_matrix(self.tableU)

            data = {
                "X": X,
                "U": U
            }

            self.dataEntered.emit(data)
            self.close()

        except Exception:
            error_w = Error_window()
            error_w.exec()