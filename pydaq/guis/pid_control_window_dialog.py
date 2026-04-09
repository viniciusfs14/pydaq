import sys, os
import serial
import serial.tools.list_ports
import numpy as np
import warnings
import time
import queue
import threading
from pydaq.utils.base import Base
from PySide6 import QtWidgets
from PySide6.QtWidgets import QDialog, QFileDialog, QApplication, QWidget, QVBoxLayout, QPushButton, QSizePolicy
from PySide6.QtGui import *
from PySide6.QtCore import *
from ..uis.ui_PyDAQ_pid_control_window_dialog import Ui_Dialog_Plot_PID_Window
from ..pid_control import PIDControl
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class PID_Control_Window_Dialog(QDialog, Ui_Dialog_Plot_PID_Window, Base):

# Signal to send back to QWidget the values
    send_values = Signal(float, float, float, int, float)
    update_plot_signal = Signal()  # Added next to send_values


    def __init__(self, *args):
        super(PID_Control_Window_Dialog, self).__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('docs/img/favicon.ico'))
        self.setWindowTitle("PYDAQ - PID Control")
        self.pushButton_startstop.clicked.connect(self.stopstart)
        self.pushButton_close.clicked.connect(self.go_back)
        self.pushButton_apply.clicked.connect(self.apply_parameters)
        self.comboBox_TypeDialog.currentIndexChanged.connect(self.on_type_combo_changed)
        self.paused = False
        self.pid = None
        self.control_running = False

        self.path = os.path.join(os.path.join(os.path.expanduser("~")), "Desktop") # Defining default path
        self.figure = Figure(figsize=(6.4, 4.8), facecolor='#404040')  # Starting the canvas
        self.figure.patch.set_facecolor('#404040')  # External background
        self.ax = self.figure.add_subplot(111, facecolor='#505050')  # Output graph
        self.ax2 = self.ax.twinx()
        self.canvas = FigureCanvas(self.figure)
        self.image_layout.addWidget(self.canvas)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setMinimumHeight(400)

        self.k = 0
        self.system_values = {}
        self.errors = {}
        self.setpoints = {}
        self.controls = {}
        self.time_var = []
        self.elapsed_time = 0.0
        
        self.lock = threading.Lock()
        self.update_plot_signal.connect(self._update_plot_gui_safe)


    def stopstart(self):
        self.paused = not self.paused
        if self.paused:
            self.plot_running = False
            self.control_running = False
            # saves the time accumulated so far
            self.elapsed_time += time.perf_counter() - self.t0
            self.pushButton_startstop.setText("START")
        else:
            self.plot_running = True
            self.control_running = True
            self.pushButton_startstop.setText("STOP")
            self.start_threaded_control()
            
    def go_back(self): #def to save and go back
        if hasattr(self, "_already_closed") and self._already_closed:
            return
        
        self.plot_running = False
        self.control_running = False
        self._already_closed = True
        time.sleep(0.1)

        if self.save: #save if wanted
            print("\n[PYDAQ] Saving data ...")
            self._save_data(self.time_var, "time.dat") # Saving time_var and data
            self._save_data(self.system_values, "output.dat")
            self._save_data(self.errors, "error.dat")
            self._save_data(self.setpoints, "setpoint.dat")
            self._save_data(self.controls, "controls.dat")
            print("\n[PYDAQ] Data saved ...")

        self.send_values.emit( #sending the values to QWidget
            self.kp if self.kp is not None else 0.0,
            self.ki if self.ki is not None else 0.0,
            self.kd if self.kd is not None else 0.0,
            self.index,
            self.setpoint,
        )

        if self.simulate == True:
            print('\n[PYDAQ] Closing simulation ...')
        elif self.board == 'arduino': #stop the event and close the dialog
            try:
                self.pid.ser.write(b"0\n") # Turning off all outputs
            except:
                pass
            self.pid.ser.close() # Closing port
        elif self.board == 'nidaq':
            try:
                # Usa hasattr para checar se a tarefa existe antes de tentar acessá-la
                if hasattr(self.pid, 'task_ao') and self.pid.task_ao:
                    n_ao = len(self.ao_channels)
                    if n_ao == 1:
                        self.pid.task_ao.write(0.0)
                    else:
                        self.pid.task_ao.write([0.0] * n_ao)
                    self.pid.task_ao.close()
                    
                if hasattr(self.pid, 'task_ai') and self.pid.task_ai:
                    self.pid.task_ai.close()
            except Exception as e:
                print('\n[PYDAQ] Warning when closing NI-DAQ tasks:', e)

        self.close()

    def closeEvent(self, event):
        # Ensures the same behavior as the "CLOSE" or "SAVE AND CLOSE" button
        if not hasattr(self, "_already_closed"):
            self.go_back()
        event.accept()         # The event needs to be explicitly accepted for PySide6 to close the window

    def apply_parameters(self): #apply all pid parameters while the event goes on
        try:
            self.setpoint = self.doubleSpinBox_SetpointDialog.value()
            if self.pid:
                self.pid.setpoint = self.setpoint
        except ValueError:
            pass  # Ignore invalid input  
        if self.doubleSpinBox_KpDialog.isEnabled(): #changing Kp Ki and Kd parameters
            self.kp = self.doubleSpinBox_KpDialog.value()
            self.pid.Kp = self.kp
        else:
            self.kp = None
            self.pid.Kp = 0
        if self.doubleSpinBox_KiDialog.isEnabled():
            self.ki = self.doubleSpinBox_KiDialog.value()
            # Reseta o integral de todos os canais sem quebrar o dicionário
            if self.pid:
                for ch in self.pid.channels:
                    self.pid.integral[ch] = 0.0
            self.pid.Ki = self.ki
        else:
            self.ki = None
            if self.pid: 
                self.pid.Ki = 0
        if self.doubleSpinBox_KdDialog.isEnabled():
            self.kd = self.doubleSpinBox_KdDialog.value()
            self.pid.Kd = self.kd
        else:
            self.kd = None
            self.pid.Kd = 0
        self.disturbe = self.doubleSpinBox_DisturbeDialog.value() #changing the disturbe
        self.pid.disturbe = self.disturbe

    # Both function below are to set the comboBox enabled/desabled status
    def on_type_combo_changed(self, index):
        if index == 0:  
            self.enable_pid_parameters(True, False, False)
        elif index == 1:  
            self.enable_pid_parameters(True, True, False)
        elif index == 2: 
            self.enable_pid_parameters(True, False, True)
        elif index == 3:  
            self.enable_pid_parameters(True, True, True)  
        self.index = index  

    # Defining the fuctions
    def set_parameters(self, kp, ki, kd, index, numerator, denominator, setpoint, unit, equationvu, equationuv, period, path, save):
        self.kp = kp if kp else 1
        self.ki = ki if ki else 0
        self.kd = kd if kd else 0
        self.numerator = numerator if numerator else '1'
        self.denominator = denominator if denominator else 's+0.2'
        self.index = index if index else 0
        self.setpoint = setpoint if setpoint else 0.0
        self.unit = unit if unit else 'Voltage (V)'
        self.calibration_equation_vu = equationvu
        self.calibration_equation_uv = equationuv
        self.period = period if period else 1 
        self.path = path if path else os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")
        self.save = save
        self._check_path()
        self.set_text()
        self.on_type_combo_changed(self.index)
        self.init_plot()
        self.start_control()

 # Inicializate variables and start controling 
    def start_control(self):
        try:
            # Initialize dictionaries using channels
            self.system_values = {ch: [] for ch in self.channels}
            self.errors = {ch: [] for ch in self.channels}
            self.setpoints = {ch: [] for ch in self.channels}
            self.controls = {ch: [] for ch in self.channels}

            self.pid = PIDControl(
                self.kp, self.ki, self.kd, self.setpoint,
                self.numerator, self.denominator,
                self.calibration_equation_vu, self.calibration_equation_uv,
                self.unit, self.period
            )
            self.check_start()
            self.start_threaded_control()
        except Exception as e:
            print('\n[PYDAQ] Error starting control:', e)

    def start_threaded_control(self):
        self.data_queue = queue.Queue()
        self.plot_running = True
        self.control_running = True
        self.ts = self.period
        self.k = 1

        self.control_thread = threading.Thread(target=self.control_loop_task, daemon=True)
        self.plot_thread = threading.Thread(target=self.update_plot_task, daemon=True)
        self.save_thread = threading.Thread(target=self.save_data_task, daemon=True)

        self.control_thread.start()
        self.plot_thread.start()
        self.save_thread.start()

    def control_loop_task(self):
        st_worker = time.perf_counter()
        self.t0 = st_worker
        self.k = 0
        
        try:
            while not self.paused:
                if not self.control_running:
                    break

                if self.simulate:
                    outputs, errors, setpoints, controls = self.pid.update_simulated_system()
                elif self.board == 'arduino':
                    outputs, errors, setpoints, controls = self.pid.update_plot_arduino()
                elif self.board == 'nidaq':
                    outputs, errors, setpoints, controls = self.pid.update_plot_nidaq()

                time_now = (time.perf_counter() - self.t0) + self.elapsed_time

                with self.lock:
                    self.data_queue.put((time_now, outputs, errors, setpoints, controls))

                target_time = st_worker + (self.k + 1) * self.ts
                wait_time = target_time - time.perf_counter()
                if wait_time > 0:
                    time.sleep(wait_time)
                else:
                    # Padronizado com a nossa matriz de erros
                    warnings.warn(
                        "[PYDAQ] Timing warning: Acquisition cycle exceeded sample period (ts). The 'time.dat' vector may be inaccurate."
                    )

                self.k += 1

        finally:
            # PROTECTION: Only calculates the time if the acquisition has actually started.
            if st_worker is not None:
                total_acquisition_duration = time.perf_counter() - st_worker
                if self.k > 0:
                    avg = total_acquisition_duration / self.k
                    print(
                        f"\n[PYDAQ] Control Thread finished. "
                        f"Total time: {total_acquisition_duration:.5f}s | "
                        f"Cycles processed: {self.k} | "
                        f"Avg per cycle: {avg:.5f}s"
                    )       
                else:
                    print("\n[PYDAQ] Control Thread finished. No data cycles acquired.")
            else:
                print("\n[PYDAQ] Control Thread finished before acquisition started (Configuration blocked).")

    def _update_plot(self):

        if len(self.time_var) == 0:
            return

        # =========================
        # UPDATE LINES
        # =========================
        for ch in self.channels:
            self.lines_output[ch].set_data(self.time_var, self.system_values[ch])
            self.lines_setpoint[ch].set_data(self.time_var, self.setpoints[ch])
            self.lines_error[ch].set_data(self.time_var, self.errors[ch])

        # X axis
        self.ax1.set_xlim(0, max(self.time_var))

        # =========================
        # Y SCALE (OUTPUT + SETPOINT)
        # =========================
        all_outputs = []
        all_setpoints = []

        for ch in self.channels:
            if self.system_values[ch]:
                all_outputs.extend(self.system_values[ch])
            if self.setpoints[ch]:
                all_setpoints.extend(self.setpoints[ch])

        if all_outputs:
            y_min = min(all_outputs + all_setpoints)
            y_max = max(all_outputs + all_setpoints)

            y_range = y_max - y_min
            if y_range == 0:
                y_range = 1e-6

            margin = 0.1 * y_range
            self.ax1.set_ylim(y_min - margin, y_max + margin)

        # =========================
        # Y SCALE (ERROR)
        # =========================
        all_errors = []

        for ch in self.channels:
            if self.errors[ch]:
                all_errors.extend(self.errors[ch])

        if all_errors:
            e_min = min(all_errors)
            e_max = max(all_errors)

            e_range = e_max - e_min
            if e_range == 0:
                e_range = 1e-6

            margin = 0.1 * e_range
            self.ax2.set_ylim(e_min - margin, e_max + margin)

    def check_start(self):
        if self.simulate == True:
            self.pid.channels = self.channels       
            self.pid.ao_channels = self.ao_channels 
            self.pid.simulate_system()
        elif self.board == 'arduino':
            self.pid.com_port = self.com_port
            self.pid.ao_channels = self.ao_channels
            self.pid.channels = self.channels
            self.pid.pid_control_arduino() 
        elif self.board == 'nidaq':
            self.pid.device = self.device
            self.pid.ao_channels = self.ao_channels
            self.pid.channels = self.channels
            self.pid.terminal = self.pid.term_map[self.terminal]
            self.pid.pid_control_nidaq() 

# Changing the text of the pid parameters inputs
    def set_text(self):
        self.comboBox_TypeDialog.setCurrentIndex(self.index)
        self.doubleSpinBox_KpDialog.setValue(self.kp)
        self.doubleSpinBox_KiDialog.setValue(self.ki)
        self.doubleSpinBox_KdDialog.setValue(self.kd)
        self.doubleSpinBox_SetpointDialog.setValue(self.setpoint)
        if self.save == True:
            self.pushButton_close.setText("SAVE AND CLOSE")
            self.pushButton_close.setMinimumWidth(180)
        else:
            self.pushButton_close.setText("CLOSE")
            self.pushButton_close.setMinimumWidth(100)

    def check_board(self, board, hardware_id, ao, ai, terminal, simulate):
        self.board = board
        self.simulate = simulate
        self.ao_channels = ao 
        self.channels = ai

        if self.simulate == True:
            print ('\n[PYDAQ] Starting PID Control Simulation ...')
        elif self.board == 'arduino':
            self.com_port = hardware_id
            print ('\n[PYDAQ] Starting PID Control on Arduino ...') 
        elif self.board == 'nidaq':
            self.device = hardware_id # Recebe o nome do dispositivo, ex: "Dev1"
            self.terminal = terminal
            print ('\n[PYDAQ] Starting PID Control on NIDAQ ...')

    def enable_pid_parameters(self, kp_enabled, ki_enabled, kd_enabled):
        self.doubleSpinBox_KpDialog.setEnabled(kp_enabled)
        self.doubleSpinBox_KiDialog.setEnabled(ki_enabled)
        self.doubleSpinBox_KdDialog.setEnabled(kd_enabled)
        if ki_enabled == False:
            self.doubleSpinBox_KiDialog.setValue(0)
        if kd_enabled == False:
            self.doubleSpinBox_KdDialog.setValue(0)

    def init_plot(self):
        
        is_single_channel = len(self.channels) == 1

        # Clear and create subplots
        self.figure.clear()
        self.ax1 = self.figure.add_subplot(211)
        self.ax2 = self.figure.add_subplot(212, sharex=self.ax1)

        # =========================
        # DARK THEME
        # =========================
        self.figure.patch.set_facecolor('#404040')
        self.ax1.set_facecolor("#FFFFFF")
        self.ax2.set_facecolor('#FFFFFF')

        for ax in [self.ax1, self.ax2]:
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')

            for spine in ax.spines.values():
                spine.set_color('white')

        # =========================
        # LINES (MULTICHANNEL)
        # =========================
        self.lines_output = {}
        self.lines_setpoint = {}
        self.lines_error = {}

        colors = plt.cm.Set1.colors  # good contrast

        for i, ch in enumerate(self.channels):
            if is_single_channel:
                color_out = 'tab:blue'
                color_sp  = 'tab:orange'
                color_err = 'tab:red'
            else:
                base_color = plt.cm.Set1.colors[i % len(plt.cm.Set1.colors)]
                color_out = base_color
                color_sp  = base_color
                color_err = base_color

            # Output
            line_out, = self.ax1.plot(
                [], [],
                color=color_out,
                marker='o',
                linestyle='-',
                markersize=3,
                linewidth=1,
                label=f'Output ({ch})'
            )

            # Setpoint
            line_sp, = self.ax1.plot(
                [], [],
                linestyle='--',
                color=color_sp,
                linewidth=1.5,
                label=f'Setpoint ({ch})'
            )

            # Error
            line_err, = self.ax2.plot(
                [], [],
                marker='o',
                linestyle='-',
                color=color_err,
                markersize=3,
                linewidth=1,
                label=f'Error ({ch})'
            )

            self.lines_output[ch] = line_out
            self.lines_setpoint[ch] = line_sp
            self.lines_error[ch] = line_err

        # =========================
        # LABELS & GRID
        # =========================
        self.ax1.set_ylabel(self.unit)
        self.ax2.set_ylabel('Error')
        self.ax2.set_xlabel('Time (s)')

        self.ax1.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.6)
        self.ax2.grid(True, linestyle='--', linewidth=0.6, color='gray', alpha=0.6)

        # =========================
        # LEGENDS OUTSIDE
        # =========================
        self.ax1.legend(
            loc='upper left',
            bbox_to_anchor=(1.02, 1),
            borderaxespad=0,
            fontsize=8
        )

        self.ax2.legend(
            loc='upper left',
            bbox_to_anchor=(1.02, 1),
            borderaxespad=0,
            fontsize=8
        )

        # =========================
        # LAYOUT FIX
        # =========================
        self.figure.subplots_adjust(right=0.78, bottom=0.15, hspace=0.3)

    def update_plot_task(self):
        plot_update_interval = max(self.ts * 0.9, 0.05)

        while self.plot_running:
            self.update_plot_signal.emit()
            time.sleep(plot_update_interval)

    def save_data_task(self):
        while self.control_running or not self.data_queue.empty():
            try:
                item = self.data_queue.get(timeout=0.05)
            except queue.Empty:
                continue
            t, outputs, errors, setpoints, controls = item
            self.time_var.append(t)

            # --- MULTICHANNEL MOD ---
            for ch in self.channels:
                if ch not in self.system_values:
                    self.system_values[ch] = []

                if ch not in self.errors:
                    self.errors[ch] = []

                if ch not in self.setpoints:
                    self.setpoints[ch] = []

                if ch not in self.controls:
                    self.controls[ch] = []

                self.system_values[ch].append(outputs[ch])
                self.errors[ch].append(errors[ch])
                self.setpoints[ch].append(setpoints[ch])
                self.controls[ch].append(controls[ch])

    def _update_plot_gui_safe(self):
        with self.lock:
            self._update_plot()
            self.canvas.draw_idle()

        #dont ctrl z more than once, otherwise it will cause a crash when the plot is updating and the data is being saved at the same time.