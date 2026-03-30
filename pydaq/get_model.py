import os
import time
import warnings
import matplotlib.pyplot as plt
import matplotlib as mpl
import nidaqmx
from nidaqmx.constants import TerminalConfiguration
import numpy as np
import serial
import serial.tools.list_ports
from pydaq.utils.base import Base
from sysidentpy.metrics import __ALL__ as metrics_list
import sysidentpy.metrics as metrics
import threading
import queue

import numpy as np
import matplotlib.pyplot as plt

from pydaq.utils.signals import Signal
from math import floor
from sysidentpy.model_structure_selection import FROLS
#from sysidentpy.basis_function._basis_function import Polynomial
from sysidentpy.basis_function import Polynomial
from sysidentpy.metrics import root_relative_squared_error
from sysidentpy.utils.display_results import results
from sysidentpy.utils.plotting import plot_residues_correlation, plot_results
from sysidentpy.residues.residues_correlation import (
    compute_residues_autocorrelation,
    compute_cross_correlation,
)
from collections import Counter
from typing import Tuple

from sysidentpy.parameter_estimation import LeastSquares

mpl.rcParams["axes.spines.right"] = False
mpl.rcParams["axes.spines.top"] = False


def display_formated_results(results_array):
    r = np.array(results_array, dtype="U50")

    col_widths = []
    for col in range(r.shape[1]):
        max_int_part = 0
        max_dec_part = 0
        for item in r[:, col]:
            if "." in item:
                int_part, dec_part = item.split(".")
                max_int_part = max(max_int_part, len(int_part))
                max_dec_part = max(max_dec_part, len(dec_part))
            else:
                max_int_part = max(max_int_part, len(item))
        col_widths.append((max_int_part, max_dec_part))

    # Display
    for row in r:
        formatted_row = []
        for item, (int_width, dec_width) in zip(row, col_widths):
            if "." in item:
                int_part, dec_part = item.split(".")
                formatted_item = (
                    f"{int_part.rjust(int_width)}.{dec_part.ljust(dec_width)}"
                )
            else:
                formatted_item = item.rjust(
                    int_width + dec_width + 1
                )  # Caso não tenha ponto decimal
            formatted_row.append(formatted_item)
        print("  ".join(formatted_row))

def plot_combined_results_with_metrics(
    y: np.ndarray,
    yhat: np.ndarray,
    residuals: np.ndarray,
    cross_corr: np.ndarray,
    metrics_namelist: list,
    metrics_vallist: list,
    n: int = 100,
    title_main: str = "Free run simulation",
    title_residuals: str = "Residual Analysis - Autocorrelation",
    title_cross_corr: str = "Residual Analysis - Cross-Correlation",
    xlabel_main: str = "Samples",
    ylabel_main: str = r"y, $\hat{y}$",
    ylabel_residuals: str = "Correlation",
    ylabel_cross_corr: str = "Cross-Correlation",
    data_color: str = "#1f77b4",
    model_color: str = "#ff7f0e",
    marker: str = "o",
    model_marker: str = "*",
    linewidth: float = 1.5,
    figsize: Tuple[int, int] = (14, 8),
    style: str = "default",
    facecolor: str = "white",
) -> None:
    """Plot combined results with three stacked subplots and a metrics table."""

    if len(y) == 0 or len(yhat) == 0:
        raise ValueError("Arrays must have at least 1 sample.")

    if len(residuals) == 0 or len(cross_corr) == 0:
        raise ValueError(
            "Residuals and cross-correlation arrays must have at least 1 sample."
        )

    # Set Matplotlib style and figure properties
    plt.style.use(style)
    plt.rcParams["axes.facecolor"] = facecolor

    fig = plt.figure(figsize=figsize, facecolor=facecolor)
    gs = plt.GridSpec(2, 3, width_ratios=[2, 2, 1], height_ratios=[2, 1])

    # Plot main results
    ax_main = fig.add_subplot(gs[0, :2])
    ax_main.plot(
        y[:], c=data_color, alpha=1, marker=marker, label="Data", linewidth=linewidth
    )
    ax_main.plot(
        yhat[:], c=model_color, marker=model_marker, label="Model", linewidth=linewidth
    )
    ax_main.set_title(title_main, fontsize=18)
    ax_main.legend()
    ax_main.tick_params(labelsize=14)
    ax_main.set_xlabel(xlabel_main, fontsize=14)
    ax_main.set_ylabel(ylabel_main, fontsize=14)

    # Plot residuals autocorrelation
    ax_residuals = fig.add_subplot(gs[1, 0])
    ax_residuals.plot(residuals[0][:], color=data_color)
    ax_residuals.axhspan(residuals[1], residuals[2], color="#ccd9ff", alpha=0.5, lw=0)
    ax_residuals.set_xlabel("Lag", fontsize=14)
    ax_residuals.set_ylabel(ylabel_residuals, fontsize=14)
    ax_residuals.tick_params(labelsize=14)
    ax_residuals.set_ylim([-1, 1])
    ax_residuals.set_title(title_residuals, fontsize=18)

    # Plot residuals cross-correlation
    ax_cross_corr = fig.add_subplot(gs[1, 1])
    ax_cross_corr.plot(cross_corr[0][:], color=data_color)
    ax_cross_corr.axhspan(
        cross_corr[1], cross_corr[2], color="#ccd9ff", alpha=0.5, lw=0
    )
    ax_cross_corr.set_xlabel("Lag", fontsize=14)
    ax_cross_corr.set_ylabel(ylabel_cross_corr, fontsize=14)
    ax_cross_corr.tick_params(labelsize=14)
    ax_cross_corr.set_ylim([-1, 1])
    ax_cross_corr.set_title(title_cross_corr, fontsize=18)

    # Add table with metrics
    ax_table = fig.add_subplot(gs[:, 2])
    ax_table.axis("off")

    data = np.array([metrics_namelist, metrics_vallist]).T
    table = ax_table.table(
        cellText=data, colLabels=["Metrics", "Value"], loc="center", cellLoc="center"
    )
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.auto_set_column_width([0, 1])
    for i, j in table.get_celld().keys():
        table[(i, j)].set_height(0.1)

    plt.tight_layout()
    plt.show()


class GetModel(Base):

    def __init__(
        self,
        device="Dev1",
        ao_channel="ao0",
        ai_channel="ai0",
        channel="ai0",
        terminal="Diff",
        com="COM1",
        ts=0.5,
        var_tb=1,
        ao_min=0,
        ao_max=5,
        session_duration=10.0,
        save=True,
        plot_mode="no",
        degree=2,
        start_save_time=1,
        out_lag=3,
        inp_lag=3,
        num_info_values=6,
        estimator=None,
        ext_lsq=True,
        prbs_bits=6,
        prbs_seed=101,
        perc_value=30,
    ):

        super().__init__()
        self.device = device
        self.ai_channel = ai_channel
        self.ao_channel = ao_channel
        self.ao_min = ao_min
        self.ao_max = ao_max
        # >>> CHANGE: normalize channels as list
        self.channels = [ai_channel]
        self.ao_channels = [ao_channel]

        self.input_channels = None
        self.output_channels = None
        self.session_duration = session_duration
        self.ts = ts
        self.var_tb = var_tb
        self.save = save
        self.plot_mode = plot_mode
        self.legend = ["Input", "Output"]
        self.degree = degree
        self.start_save_time = start_save_time
        self.out_lag = out_lag
        self.inp_lag = inp_lag
        self.num_info_val = num_info_values
        self.estimator = estimator
        self.ext_lsq = ext_lsq
        self.prbs_bits = prbs_bits
        self.prbs_seed = prbs_seed
        self.perc_value = perc_value
        self.final_model = {}  # >>> CHANGE
        self.theta = {}        # >>> CHANGE
        self.n_terms = {}      # >>> CHANGE
        self.terminal = self.term_map[terminal]

        # >>> CHANGE: storage per channel
        self.out_read = {ch: [] for ch in self.channels}
        self.inp_read = {ch: [] for ch in self.channels}
        self.time_var = {ch: [] for ch in self.channels}

        self.input_channels = []
        self.output_channels = []

        # Thread controls
        self.acquisition_running = False
        self.plot_closed_by_user = False
        self.plot_ready_event = threading.Event()

        # Error flags
        self.error_path = False

        # COM ports
        self.com_ports = [i.description for i in serial.tools.list_ports.comports()]
        self.com_port = com  # Default COM port

        # Plot title
        self.title = None

        self._nidaq_info()

        # Defining default path
        self.path = os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")

        # Arduino ADC resolution (in bits)
        self.arduino_ai_bits = 10

        # Arduino analog input max and min
        self.ard_ai_max, self.ard_ai_min = 5, 0

        # Value per bit - Arduino
        self.ard_vpb = (self.ard_ai_max - self.ard_ai_min) / (
            (2**self.arduino_ai_bits) - 1
        )

        # Number of necessary cycles
        self.cycles = None

    def _acquisition_worker_arduino(self, data_queue, signal_to_send, sent_data_bytes):
        """Worker to send signal and acquire data with Arduino."""
        self.plot_ready_event.wait()

        channels = self.channels
        n_channels = len(channels)

        try:
            self._open_serial()

            if not self._verify_arduino_firmware():
                self.ser.close()
                warnings.warn(
                    "⚠️ PyDAQ Firmware not detected on this board!\n"
                    "Please go to the top menu and click on 'Arduino Firmware' to upload the correct code."
                )
                # If you are using a graphical interface with PySide6, you can call a QMessageBox here.
                # QMessageBox.critical(None, "Firmware Error", "PyDAQ Firmware not detected. Please upload it first.")

                return 
            # --- WARM-UP SECTION ---
            self.ser.write(b"0")
            self.ser.reset_input_buffer()
            _ = self.ser.readline()
            # --- END WARM-UP SECTION ---

            # Start the clock AFTER serial is open
            st_worker = time.perf_counter()
            num_cycles_performed = 0

            for k in range(self.cycles):
                if not self.acquisition_running:
                    break

                # Send signal
                val_to_send = 1 if signal_to_send[k] == self.ao_max else 0
                msg_parts = []
                for ch in self.ao_channels: 
                    pin_num = ch.replace("D", "")
                    msg_parts.append(f"{pin_num}:{val_to_send}")
                
                msg = ",".join(msg_parts) + "\n"
                self.ser.write(msg.encode())

                self.ser.reset_input_buffer()
                self.ser.readline()
                
                try:
                    raw = self.ser.readline()
                    values = list(map(int, raw.decode("utf-8").strip().split(",")))

                    if len(values) < 6:
                        raise ValueError("Incomplete universal frame")

                    time_now = time.perf_counter() - st_worker
                    sent_value = signal_to_send[k]

                    for ch in channels:
                        idx = int(ch.replace("A", "")) 
                        value = values[idx] * self.ard_vpb
                        data_queue.put((time_now, ch, sent_value, value))
                
                    num_cycles_performed += 1

                except (ValueError, UnicodeDecodeError):
                    warnings.warn(f"Invalid multichannel read: {raw}")
                    continue

                wait_time = (st_worker + num_cycles_performed * self.ts) - time.perf_counter()
                if wait_time > 0:
                    time.sleep(wait_time)
                else:
                    warnings.warn(
                        "Time spent exceeded ts. You CANNOT trust time.dat"
                    )

        except serial.SerialException as e:
            warnings.warn(f"Failed to open or use serial port {self.com_port}: {e}")
        finally:
            if hasattr(self, 'ser') and self.ser.is_open:
                self.ser.write(b"0")
                self.ser.close()
            data_queue.put(None)
            total_acquisition_duration = time.perf_counter() - st_worker
            if num_cycles_performed > 0:
                avg = total_acquisition_duration / num_cycles_performed
                print(
                    f"\nThread finished. "
                    f"Total time: {total_acquisition_duration:.5f}s | "
                    f"Cycles processed: {num_cycles_performed} | "
                    f"Avg per cycle: {avg:.5f}s"
                )       
            else:
                print("\nThread finished. No data cycles acquired.")

    def _acquisition_worker_nidaq(self, data_queue, signal_to_send):
        """Worker to send signal and acquire data with NI-DAQ."""
        self.plot_ready_event.wait()

        task_ao = nidaqmx.Task()
        task_ai = nidaqmx.Task()
        
        try:
            num_cycles_performed = 0
            # === MODIFIED === multi-channel configuration
            ao_str = ",".join([f"{self.device}/{ch}" for ch in self.ao_channels])  # === MODIFIED ===
            ai_str = ",".join([f"{self.device}/{ch}" for ch in self.channels])  # === MODIFIED ===

            task_ao.ao_channels.add_ao_voltage_chan(ao_str, min_val=self.ao_min, max_val=self.ao_max)  # === MODIFIED ===
            task_ai.ai_channels.add_ai_voltage_chan(ai_str, terminal_config=self.terminal)  # === MODIFIED ===
            
            # Zero the output before starting
            task_ao.write([self.ao_min] * len(self.ao_channels))

            # Start the clock AFTER hardware setup
            st_worker = time.perf_counter()

            for k in range(self.cycles):
                if not self.acquisition_running:
                    break

                # Send signal and read response
                sent_value = signal_to_send[k]
                task_ao.write([sent_value] * len(self.ao_channels))
                read_values = task_ai.read(number_of_samples_per_channel=1)
                
                # Calculate timestamp and put data in the queue
                if len(self.channels) == 1:  # === NEW ===
                    read_values = [read_values]  # === NEW ===
                
                time_now = time.perf_counter() - st_worker

                for i, ch in enumerate(self.channels):  # === NEW ===
                    data_queue.put((time_now, ch, sent_value, read_values[i]))  # === NEW ===

                num_cycles_performed += 1
                # Wait to maintain the sampling period
                wait_time = (st_worker + (k + 1) * self.ts) - time.perf_counter()

                if wait_time > 0:
                    time.sleep(wait_time)
                else:
                    warnings.warn(
                        "Time spent to append data and update interface was greater than ts. You CANNOT trust time.dat"
                    )
        finally:
            # Ensure tasks are safely closed
            task_ao.write([self.ao_min] * len(self.ao_channels))
            task_ao.close()
            task_ai.close()

            data_queue.put(None) # Signal the end of acquisition

            total_acquisition_duration = time.perf_counter() - st_worker
            if num_cycles_performed > 0:
                avg = total_acquisition_duration / num_cycles_performed
                print(
                    f"\nThread finished. "
                    f"Total time: {total_acquisition_duration:.5f}s | "
                    f"Cycles processed: {num_cycles_performed} | "
                    f"Avg per cycle: {avg:.5f}s"
                )          
            else:
                print("\nThread finished. No data cycles acquired.")

    def _orchestrate_acquisition(self, worker_target, worker_args):
        """General-purpose orchestrator for data acquisition and plotting."""
        # === MODIFIED === reset dict storage
        self.time_var = {ch: [] for ch in self.channels}  # === MODIFIED ===
        self.inp_read = {ch: [] for ch in self.channels}  # === MODIFIED ===
        self.out_read = {ch: [] for ch in self.channels}  # === MODIFIED ===

        data_queue = queue.Queue()
        self.acquisition_running = True
        self.plot_closed_by_user = False
        self.plot_ready_event.clear()

        acquisition_thread = threading.Thread(
            target=worker_target,
            args=(data_queue, *worker_args),
            daemon=True
        )
        acquisition_thread.start()

        if self.plot_mode == 'realtime':
            self._start_updatable_plot(title_str=self.title)
            self.fig.canvas.mpl_connect('close_event', self._on_plot_close)
            time.sleep(0.5)
            self.plot_ready_event.set()
        else:
            self.plot_ready_event.set()
        
        if self.ts >= 0.05:
            plot_update_interval = 0.05
        else:
            plot_update_interval = 0.25
            
        last_plot_update_time = time.perf_counter()

        while (self.acquisition_running and not self.plot_closed_by_user) or not data_queue.empty():
            try:
                item = data_queue.get(timeout=0.01)
                if item is None:
                    break # Worker has finished
                
                timestamp, ch, input_val, output_val = item  # === MODIFIED ===
                self.time_var[ch].append(timestamp)  # === MODIFIED ===
                self.inp_read[ch].append(input_val)  # === MODIFIED ===
                self.out_read[ch].append(output_val)  # === MODIFIED ===

                now = time.perf_counter()
                if self.plot_mode == 'realtime' and (now - last_plot_update_time >= plot_update_interval or not self.acquisition_running):
                    # Apply alignment only for Arduino acquisitions
                    aligned_time = {}
                    aligned_out = {}
                    aligned_in = {}
                    if 'Arduino' in self.title:
                        for ch in self.channels:  # >>> CHANGE
                            aligned_time[ch] = self.time_var[ch][:-1]
                            aligned_out[ch] = self.out_read[ch][1:]
                            aligned_in[ch] = self.inp_read[ch][:-1]

                        self._update_plot(       # >>> CHANGE
                            aligned_time,
                            aligned_out,
                            y2_values=aligned_in,
                            y1_label="Output",
                            y2_label="Input",
                            channel_names=self.channels,        # Ex: ["A0", "A1"]
                            y2_channel_names=self.ao_channels   # Ex: ["D8", "D9"]
                        )
                    else:
                        for ch in self.channels:  # >>> CHANGE
                            aligned_time[ch] = self.time_var[ch]
                            aligned_out[ch] = self.out_read[ch]
                            aligned_in[ch] = self.inp_read[ch]

                        self._update_plot(       # >>> CHANGE
                            aligned_time,
                            aligned_out,
                            y2_values=aligned_in,
                            y1_label="Output",
                            y2_label="Input",
                            channel_names=self.channels,        # Ex: ["A0", "A1"]
                            y2_channel_names=self.ao_channels   # Ex: ["D8", "D9"]
                        )
                    last_plot_update_time = now
            except queue.Empty:
                if not acquisition_thread.is_alive() and data_queue.empty():
                    break
                continue
        
        acquisition_thread.join()

    def _on_plot_close(self, event):
        """Event handler for Matplotlib figure closure."""
        print("Plot window closed by user. Initiating shutdown...")
        self.acquisition_running = False
        self.plot_closed_by_user = True

    def get_model_arduino(self):

        if self.input_channels:
            self.channels = self.input_channels

        if self.output_channels:
            self.ao_channels = self.output_channels

        self._check_path()
        self.cycles = int(np.floor(self.session_duration / self.ts)) + 1

        signal_generator = Signal(self.prbs_bits, self.prbs_seed, self.var_tb)
        signal_finale = signal_generator.prbs_final(cycles=self.cycles, ao_max=self.ao_max)
        
        # Arduino expects bytes for digital output
        sent_data_bytes = [b"1" if v == self.ao_max else b"0" for v in signal_finale]
        
        self.title = f"PYDAQ - Data Collection for Model (Arduino)"
        self._orchestrate_acquisition(self._acquisition_worker_arduino, (signal_finale, sent_data_bytes))

        # Plot at the end if requested
        if self.plot_mode == 'end' and any(len(self.time_var[ch]) > 0 for ch in self.channels):  # === MODIFIED === explicit non-empty check
            self._start_updatable_plot(title_str=self.title)
            aligned_time = {}
            aligned_out = {}
            aligned_in = {}

            for ch in self.channels:
                aligned_time[ch] = self.time_var[ch][:-1]
                aligned_out[ch] = self.out_read[ch][1:]
                aligned_in[ch] = self.inp_read[ch][:-1]

            self._update_plot(
                aligned_time,
                aligned_out,
                y2_values=aligned_in,
                y1_label="Output",
                y2_label="Input",
                channel_names=self.channels,        # Ex: ["A0", "A1"]
                y2_channel_names=self.ao_channels   # Ex: ["D8", "D9"]
            )
            plt.show(block=True)

        if self.save:  # Adjusting data, since no last data is acquired by arduino
            print("\nSaving data ...")
            # Saving time_var and data
            sliced_time_var = {ch: self.time_var[ch][:-1] for ch in self.channels}
            sliced_input = {ch: self.inp_read[ch][:-1] for ch in self.channels}
            sliced_output = {ch: self.out_read[ch][1:] for ch in self.channels}

            self._save_data(sliced_time_var, f"time.dat")
            self._save_data(sliced_input, f"input.dat")
            self._save_data(sliced_output, f"output.dat")
            print("\nData saved ...")

        self.acquired_model = {}
        self.final_model = {}
        self.theta = {}
        self.n_terms = {}

        # adapts the time at which data starts to be saved to obtain the model
        time_save = int(self.start_save_time / self.ts)

        for ch in self.channels:

            print(f"\nIdentifying model for channel: {ch}")
            data_x = np.array(self.inp_read[ch][:-1])   # input (discard last)
            data_y = np.array(self.out_read[ch][1:])    # output (discard first)
            
            # Ensure arrays are the same length (extra security)
            min_len = min(len(data_x), len(data_y))
            data_x = data_x[:min_len]
            data_y = data_y[:min_len]

            perc_index = floor(data_x.shape[0] - data_x.shape[0] * (self.perc_value / 100))

            x_train, x_valid = (
                data_x[time_save:perc_index].reshape(-1, 1),
                data_x[perc_index:].reshape(-1, 1),
            )
            y_train, y_valid = (
                data_y[time_save:perc_index].reshape(-1, 1),
                data_y[perc_index:].reshape(-1, 1),
            )

            basis_function = Polynomial(degree=self.degree)

            if self.ext_lsq:
                self.estimator = LeastSquares(unbiased=True)
            elif self.estimator is None or isinstance(self.estimator, str):
                self.estimator = LeastSquares(unbiased=False)

            model = FROLS(
                order_selection=True,
                n_info_values=self.num_info_val,
                # The extended_least_squares parameter no longer goes here; it's defined by the estimator above.
                ylag=[i + 1 for i in range(self.inp_lag)],
                xlag=[i + 1 for i in range(self.out_lag)],
                info_criteria="aic",
                estimator=self.estimator,
                basis_function=basis_function,
            )
            model.fit(X=x_train, y=y_train)
            yhat = model.predict(X=x_valid, y=y_valid)
            rrse = root_relative_squared_error(y_valid, yhat)
            print(f"Channel {ch}: Root relative squared error: {rrse}")

            results_data = results(
                model.final_model,
                model.theta,
                model.err,
                model.n_terms,
                err_precision=8,
                dtype="sci",
            )

            results_data.insert(0, ["Regressors", "Parameters", "ERR"])

            display_formated_results(results_data)

            self.acquired_model[ch] = model
            self.final_model[ch] = model.final_model
            self.theta[ch] = model.theta
            self.n_terms[ch] = model.n_terms

            ee = compute_residues_autocorrelation(y_valid, yhat)
            x1e = compute_cross_correlation(y_valid, yhat, x_valid)

            metrics_namelist = []
            metrics_vallist = []

            for name in dir(metrics):
                if name.startswith("_"):
                    continue

                func = getattr(metrics, name)

                if callable(func):
                    try:
                        value = func(y_valid, yhat)

                        # Ensure value is scalar
                        if isinstance(value, (int, float, np.number)):
                            metrics_namelist.append(
                                Base.get_acronym(Base.adjust_string(name))
                            )
                            metrics_vallist.append(f"{value:.4f}")

                    except Exception:
                        continue

            plot_combined_results_with_metrics(
                y=y_valid,
                yhat=yhat,
                residuals=ee,
                cross_corr=x1e,
                title_main=f"Free run simulation - {ch}",
                title_residuals="Residues",
                title_cross_corr="Residues",
                xlabel_main="Samples",
                ylabel_main=r"y, $\hat{y}$",
                ylabel_residuals="$e^2$",
                ylabel_cross_corr="$x_1e$",
                data_color="#1f77b4",
                model_color="#ff7f0e",
                marker="o",
                model_marker="*",
                linewidth=1.5,
                metrics_namelist=metrics_namelist,
                metrics_vallist=metrics_vallist,
            )
            self.show_results(results_data,ch)

    def get_model_nidaq(self):

        if self.input_channels:
            self.channels = self.input_channels

        if self.output_channels:
            self.ao_channels = self.output_channels

        self._check_path()
        self.cycles = int(np.floor(self.session_duration / self.ts)) + 1

        signal_generator = Signal(self.prbs_bits, self.prbs_seed, self.var_tb)
        signal_finale = signal_generator.prbs_final(cycles=self.cycles, ao_max=self.ao_max)
        
        self.title = f"PYDAQ - Data Collection for Model (NIDAQ)"
        self._orchestrate_acquisition(self._acquisition_worker_nidaq, (signal_finale,))
        
        # Plot at the end if requested
        if self.plot_mode == 'end' and any(self.time_var[ch] for ch in self.channels):
            self._start_updatable_plot(title_str=self.title)
            aligned_time = {}
            aligned_out = {}
            aligned_in = {}

            for ch in self.channels:
                aligned_time[ch] = self.time_var[ch]
                aligned_out[ch] = self.out_read[ch]
                aligned_in[ch] = self.inp_read[ch]

            self._update_plot(
                aligned_time,
                aligned_out,
                y2_values=aligned_in,
                y1_label="Output",
                y2_label="Input",
                channel_names=self.channels,        # Ex: ["A0", "A1"]
                y2_channel_names=self.ao_channels   # Ex: ["D8", "D9"]
            )
            plt.show(block=True)

        if self.save:
            print("\nSaving data ...")
            # Saving time_var and data
            self._save_data(self.time_var, f"time.dat")
            self._save_data(self.inp_read, f"input.dat")
            self._save_data(self.out_read, f"output.dat")
            print("\nData saved ...")

        self.acquired_model = {}
        self.final_model = {}
        self.theta = {}
        self.n_terms = {}

        # adapts the time at which data starts to be saved to obtain the model
        time_save = int(self.start_save_time / self.ts)
        
        for ch in self.channels:
                
            print(f"\nIdentifying model for channel: {ch}")

            data_x = np.array(self.inp_read[ch])
            data_y = np.array(self.out_read[ch])

            perc_index = floor(data_x.shape[0] - data_x.shape[0] * (self.perc_value / 100))

            x_train, x_valid = (
                data_x[time_save:perc_index].reshape(-1, 1),
                data_x[perc_index:].reshape(-1, 1),
            )
            y_train, y_valid = (
                data_y[time_save:perc_index].reshape(-1, 1),
                data_y[perc_index:].reshape(-1, 1),
            )

            basis_function = Polynomial(degree=self.degree)

            if self.ext_lsq:
                self.estimator = LeastSquares(unbiased=True)
            elif self.estimator is None or isinstance(self.estimator, str):
                self.estimator = LeastSquares(unbiased=False)

            model = FROLS(
                order_selection=True,
                n_info_values=self.num_info_val,
                # The extended_least_squares parameter no longer goes here; it's defined by the estimator above.
                ylag=[i + 1 for i in range(self.inp_lag)],
                xlag=[i + 1 for i in range(self.out_lag)],
                info_criteria="aic",
                estimator=self.estimator,
                basis_function=basis_function,
            )
            model.fit(X=x_train, y=y_train)
            yhat = model.predict(X=x_valid, y=y_valid)
            rrse = root_relative_squared_error(y_valid, yhat)
            print(f"Channel {ch}: Root relative squared error: {rrse}")

            results_data = results(
                model.final_model,
                model.theta,
                model.err,
                model.n_terms,
                err_precision=8,
                dtype="sci",
            )
            results_data.insert(0, ["Regressors", "Parameters", "ERR"])

            display_formated_results(results_data)

            self.acquired_model[ch] = model
            self.final_model[ch] = model.final_model
            self.theta[ch] = model.theta
            self.n_terms[ch] = model.n_terms

            ee = compute_residues_autocorrelation(y_valid, yhat)
            x1e = compute_cross_correlation(y_valid, yhat, x_valid)

            metrics_namelist = []
            metrics_vallist = []

            for name in dir(metrics):
                if name.startswith("_"):
                    continue

                func = getattr(metrics, name)

                if callable(func):
                    try:
                        value = func(y_valid, yhat)

                        # Ensure value is scalar
                        if isinstance(value, (int, float, np.number)):
                            metrics_namelist.append(
                                Base.get_acronym(Base.adjust_string(name))
                            )
                            metrics_vallist.append(f"{value:.4f}")

                    except Exception:
                        continue

            plot_combined_results_with_metrics(
                y=y_valid,
                yhat=yhat,
                residuals=ee,
                cross_corr=x1e,
                title_main=f"Free run simulation - {ch}",
                title_residuals="Residues",
                title_cross_corr="Residues",
                xlabel_main="Samples",
                ylabel_main=r"y, $\hat{y}$",
                ylabel_residuals="$e^2$",
                ylabel_cross_corr="$x_1e$",
                data_color="#1f77b4",
                model_color="#ff7f0e",
                marker="o",
                model_marker="*",
                linewidth=1.5,
                metrics_namelist=metrics_namelist,
                metrics_vallist=metrics_vallist,
            )

            self.show_results(results_data, ch)

    def show_results(self, results, ch):

        model = self.acquired_model[ch]

        r = np.array(results[1:], dtype="U50")
        model_string = "y_k = "
        line_control = 0
        string_list = []

        for ind in range(r.shape[0]):
            if r[ind, 0] == "1":
                model_string += f"{float(r[ind,1]):.4f}"
            else:
                model_string += f"{float(r[ind,1]):.4f}*{r[ind,0]}"

            if ind < r.shape[0] - 1:
                if float(r[ind + 1, 1]) >= 0:
                    model_string += "+"
            line_control += 1
            if line_control % 2 == 0:
                string_list.append(model_string)
                model_string = ""
        if line_control % 2 != 0:
            string_list.append(model_string)

        for cont, i in enumerate(string_list):
            string_list[cont] = i.replace("(", "_{")
            string_list[cont] = string_list[cont].replace(")", "}")
            string_list[cont] = string_list[cont].replace("*", " ")
            string_list[cont] = string_list[cont].replace("x1", "x")

        fig, ax = plt.subplots()
        aux_pos = 0
        fig.patch.set_facecolor("#404040") 
        ax.axis("off")
        ax.text(0.5, 1, f"Mathematical Model (Channel {ch})", fontsize=18, ha="center", color="white")
        plt.axhline(y=0.96, color="#044c04", linestyle="-")

        if (
            model.basis_function.degree == 1
            and 0 not in model.final_model
        ):
            numerator_string = ""
            denominator_string = "1"
            for i in range(model.n_terms):
                if np.max(model.final_model[i]) < 1:
                    tmp_regressor_str = str(1)
                else:
                    regressor_dic = Counter(model.final_model[i])
                    regressor_string = []
                    for j in range(len(list(regressor_dic.keys()))):
                        regressor_key = list(regressor_dic.keys())[j]
                        if regressor_key < 1:
                            regressor_Z_transformed = ""
                        else:
                            expoent_string = str(
                                -int(
                                    regressor_key
                                    - np.floor(regressor_key / 1000) * 1000
                                )
                            )
                            if int(regressor_key / 1000) < 2:
                                if model.theta[i][0] > 0:
                                    regressor_Z_transformed = f"\\,-\\,{model.theta[i][0]:.4f}\\,z^{{{expoent_string}}}"
                                    denominator_string += regressor_Z_transformed
                                else:
                                    regressor_Z_transformed = f"\\,+\\,{-model.theta[i][0]:.4f}\\,z^{{{expoent_string}}}"
                                    denominator_string += regressor_Z_transformed
                            else:
                                if (
                                    numerator_string
                                    and model.theta[i][0] > 0
                                ):
                                    numerator_string += "\\,+\\,"
                                    regressor_Z_transformed = f"{model.theta[i][0]:.4f}\\,z^{{{expoent_string}}}"
                                    numerator_string += regressor_Z_transformed
                                else:
                                    regressor_Z_transformed = f"{model.theta[i][0]:.4f}\\,z^{{{expoent_string}}}"
                                    numerator_string += regressor_Z_transformed

            latex_eq = "H[z]\\,=\\,\\frac{Y[z]}{X[z]}\\,=\\,"

            if numerator_string:
                latex_eq += f"\\frac{{{numerator_string}}}{{{denominator_string}}}"
            else:
                latex_eq += f"\\frac{{1}}{{{denominator_string}}}"

            string_list.append("")
            string_list.append(latex_eq)

        for i in range(len(string_list)):
            if string_list[i]:
                ax.text(
                    0.5,  # Center the text horizontally
                    0.7 - i * 0.07,
                    rf"${string_list[i]}$",
                    fontsize=15,
                    ha="center",  # Adjust horizontal alignment to center
                    color="white",  
                )
                aux_pos = 1

        ax.axis("off")
        plt.show()