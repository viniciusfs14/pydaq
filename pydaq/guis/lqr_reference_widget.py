import os
import numpy as np
from PySide6.QtWidgets import QWidget, QTableWidgetItem, QHeaderView, QFileDialog
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

        # --- NEW: Connections for the Browse buttons ---
        if hasattr(self, 'btn_browse_x'):
            self.btn_browse_x.clicked.connect(lambda: self.browse_file(self.path_x_ref))
        if hasattr(self, 'btn_browse_u'):
            self.btn_browse_u.clicked.connect(lambda: self.browse_file(self.path_u_eq))

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
                if matrix_key in self.default_matrices:
                    m = self.default_matrices[matrix_key]
                    if i < m.shape[0] and j < m.shape[1]:
                        # Default display using dot
                        val = str(m[i, j])

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
                    # Robust reading for both decimal separators
                    raw_text = item.text().replace(',', '.')
                    try:
                        value = float(raw_text)
                    except ValueError:
                        value = 0.0 
                M[i, j] = value
        return M

    # --- NEW: Browse file method ---
    def browse_file(self, line_edit):
        path, _ = QFileDialog.getOpenFileName(self, "Select Reference File", "", "Data Files (*.dat *.txt);;All Files (*)")
        if path:
            line_edit.setText(path)

    # --- NEW: Process file method ---
    def process_file(self, path, expected_cols):
        """Professor's logic: 1 row = Fixed | N rows = Trajectory"""
        if not path:
            # If no file was passed (e.g., U_eq left blank), assume fixed zero
            return np.zeros((expected_cols, 1)), False, 1

        raw_data = np.loadtxt(path, ndmin=2)

        if raw_data.ndim == 1:
            # CASE 1: Only 1 row
            if len(raw_data) != expected_cols and expected_cols != 1:
                raise ValueError(f"File has {len(raw_data)} columns, expected {expected_cols}.")
            return raw_data.reshape(expected_cols, 1), False, 1
            
        elif raw_data.ndim == 2:
            # CASE 2: Trajectory (Multiple rows)
            if raw_data.shape[1] != expected_cols:
                raise ValueError(f"File has {raw_data.shape[1]} columns, expected {expected_cols}.")
            return raw_data, True, raw_data.shape[0]

    def send_data(self):
        """
        Emits the reference data and closes the widget.
        """
        try:
            # CHECK WHICH TAB IS ACTIVE
            current_tab = 0
            if hasattr(self, 'tabWidget_refs'):
                current_tab = self.tabWidget_refs.currentIndex()

            if current_tab == 0:
                # TAB 1: MANUAL TABLES
                X = self.read_matrix(self.tableX)
                U = self.read_matrix(self.tableU)
                is_trajectory = False
                steps = 1
            
            elif current_tab == 1:
                # TAB 2: FILES
                if not self.path_x_ref.text():
                    raise ValueError("[PYDAQ] The X_ref file is mandatory in file mode.")

                X, is_traj_x, steps_x = self.process_file(self.path_x_ref.text(), self.n_states)
                U, is_traj_u, steps_u = self.process_file(self.path_u_eq.text(), self.n_inputs)

                is_trajectory = is_traj_x or is_traj_u
                steps = max(steps_x, steps_u)

            # Package into the dictionary
            data = {
                "X": X,
                "U": U,
                "is_trajectory": is_trajectory,
                "steps": steps
            }

            self.dataEntered.emit(data)
            self.close()

        except Exception as e:
            import warnings
            err_msg = str(e)
            
            warnings.warn(f"[PYDAQ] Reference Configuration Error: {err_msg}")
            
            error_w = Error_window()
            
            if "columns, expected" in err_msg:
                error_w.ui.confirm.setText("Dimension mismatch: The reference file columns do not match the system dimensions (n or m).")
            elif "mandatory" in err_msg:
                error_w.ui.confirm.setText("Missing configuration: Please ensure the reference file path is properly defined.")
            else:
                error_w.ui.confirm.setText("Reference configuration error: Please check your input data.")
            error_w.exec()