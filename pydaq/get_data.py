import os
import time
import warnings
import threading
import queue

import matplotlib.pyplot as plt
import nidaqmx
from nidaqmx.constants import TerminalConfiguration
import numpy as np
import serial
import serial.tools.list_ports
from pydaq.utils.base import Base
from scipy.signal import lfilter, butter, firwin, filtfilt


class GetData(Base):
    """
    Class able to get data from data acquisition boards using (or not) a graphical user interface (GUI)

    :author: Samir Angelo Milani Martins
         - https://www.samirmartins.com.br
         - https://www.github.com/samirmartins/

    :param:
        device: nidaq device from where data will be colected. Example: "Dev1"
        channel: channel from where data will be acquired. Example: ai0
        terminal: 'Diff', 'RSE' or 'NRSE': terminal configuration (differential, referenced single ended or non-referenced single ended)
        com: arduino COM port. Example: 'COM1'
        ts: sample period, in seconds.
        session_duration: session duration, in seconds.
        save: if True, saves data in path defined by path.
        path: where data will be saved.
        plot: if True, plot data iteractively as they are acquired

    """

    def __init__(
            self,
            device="Dev1",
            channel="ai0",
            terminal="Diff",
            com="COM1",
            ts=0.5,
            session_duration=10.0,
            save=True,
            plot_mode="no", # Options: "realtime", "end", "no"
    ):
        super().__init__()
        self.device = device
        self.channel = channel
        self.ts = ts
        self.session_duration = session_duration
        self.save = save
        self.plot_mode = plot_mode
        self.channels = []

        # Terminal configuration
        self.terminal = self.term_map[terminal]

        # Initializing variables
        self.data = []
        self.data_filtered = []
        self.time_var = []
        self.coeffs = []

        # Gathering nidaq info
        self._nidaq_info()

        # Error flags
        self.error_path = False

        # COM ports
        self.com_ports = [i.description for i in serial.tools.list_ports.comports()]
        self.com_port = com  # Default COM port

        # Plot title
        self.title = None

        # Plot legend
        self.legend = ["Input"]

        # Defining default path
        self.path = os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")

        # Arduino ADC resolution (in bits)
        self.arduino_ai_bits = 10

        # Arduino analog input max and min
        self.ard_ai_max, self.ard_ai_min = 5, 0

        # Value per bit - Arduino
        self.ard_vpb = (self.ard_ai_max - self.ard_ai_min) / ((2 ** self.arduino_ai_bits)-1)

        # Flag to control the acquisition thread
        self.acquisition_running = False
        # Flag to signal plot window closure
        self.plot_closed_by_user = False
        self.plot_ready_event = threading.Event()

    def _acquisition_worker_nidaq(self, data_queue):
        """
        This function runs in a separate thread to acquire data from NIDAQ.
        It does not touch the GUI, it only collects data and puts it on the queue.
        """
        # Wait for plot to be ready before starting acquisition to synchronize time_now to ~0
        self.plot_ready_event.wait() 

        task = nidaqmx.Task()
        
        try:
            # --- MULTICHANNEL SUPPORT ---
            channel_str = ",".join([f"{self.device}/{ch}" for ch in self.channels])

            task.ai_channels.add_ai_voltage_chan(
                channel_str, terminal_config=self.terminal
            )

            n_channels = len(self.channels)
            num_cycles_performed = 0

            st_worker = time.perf_counter()
            self.st_worker = st_worker
            
            for k in range(self.cycles):
                if not self.acquisition_running:
                    break

                temp = task.read()
                time_now = time.perf_counter() - st_worker
                if n_channels == 1:
                    temp = [temp]

                for i, ch in enumerate(self.channels):
                    data_queue.put((time_now, ch, temp[i]))

                num_cycles_performed += 1

                wait_time = (st_worker + (k + 1) * self.ts) - time.perf_counter()
                if wait_time > 0:
                    time.sleep(wait_time)
                else:
                    warnings.warn(
                        "Time spent to append data and update interface was greater than ts. You CANNOT trust time.dat"
                    )
        finally:
            task.close()
            data_queue.put(None) # Signal end of data acquisition
            total_acquisition_duration = time.perf_counter() - st_worker
            if num_cycles_performed > 0:
                avg = total_acquisition_duration / num_cycles_performed
                print(
                    f"\nAcquisition Thread finished. "
                    f"Total time: {total_acquisition_duration:.5f}s | "
                    f"Cycles: {num_cycles_performed} | "
                    f"Avg per cycle: {avg:.5f}s"
                )           
            else:
                print("\nAcquisition Thread finished. No data cycles acquired.")
        

    # Handler for plot window closure
    def _on_plot_close(self, event):
        """
        Event handler for Matplotlib figure closure.
        Sets acquisition_running to False and plot_closed_by_user to True.
        """
        print("Plot window closed by user. Initiating shutdown...")
        self.acquisition_running = False # Signal acquisition to stop
        self.plot_closed_by_user = True # Signal that plot was closed manually
        
    def get_data_nidaq(self, filter_coefs=None):
        """
        Data acquisition method using NI-DAQ and threading.
        Now includes a secondary plot thread using a complete redraw approach.
        """
        self.data = {ch: [] for ch in self.channels}
        self.time_var = {ch: [] for ch in self.channels}
        self.data_filtered = {ch: [] for ch in self.channels}
        self.coeffs = []

        if filter_coefs is not None and (isinstance(filter_coefs, tuple) or len(filter_coefs) > 0):
            self.coeffs = filter_coefs
        else:
            self.coeffs = []

        data_queue = queue.Queue()
        self.acquisition_running = True
        self.plot_closed_by_user = False
        self.plot_ready_event.clear()

        self._check_path()
        self.cycles = int(np.floor(self.session_duration / self.ts)) + 1

        acquisition_thread = threading.Thread(
            target=self._acquisition_worker_nidaq,
            args=(data_queue,),
            daemon=True
        )
        acquisition_thread.start()

        if self.plot_mode == 'realtime':
            self.title = f"PYDAQ - Data Acquisition. {self.device}, {self.channel}"
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
                    self.acquisition_running = False
                    # Flushes the queue to ensure all data is processed
                    while not data_queue.empty():
                        remaining_item = data_queue.get_nowait()
                        if remaining_item is not None:
                            timestamp, value = remaining_item
                            self.time_var.append(timestamp)
                            self.data.append(value)
                    break

                timestamp, channel, value = item
                self.time_var[channel].append(timestamp)
                self.data[channel].append(value)

                now = time.perf_counter()
                if self.plot_mode == 'realtime' and (now - last_plot_update_time >= plot_update_interval or not self.acquisition_running):
                    # Applies the filter for real-time plotting
                    if filter_coefs is not None and (isinstance(filter_coefs, tuple) or len(filter_coefs) > 0):
                        for ch in self.channels:
                            if len(self.data[ch]) == 0:
                                continue

                            if isinstance(filter_coefs, tuple) and len(filter_coefs) == 2:
                                b, a = filter_coefs
                                self.data_filtered[ch] = lfilter(b, a, np.array(self.data[ch])).tolist()
                            else:
                                self.data_filtered[ch] = lfilter(filter_coefs, 1.0, np.array(self.data[ch])).tolist()

                    self._update_plot(
                        self.time_var,
                        self.data,
                        y2_values=self.data_filtered if self.data_filtered else None,
                        y1_label="Original Data", 
                        y2_label="Filtered Data"
                    )
                    last_plot_update_time = now

            except queue.Empty:
                time.sleep(0.01)
                if not self.acquisition_running and data_queue.empty():
                    break

        acquisition_thread.join()

        # Applies final filter if coefficients are present (to save and plot at the end)
        if filter_coefs is not None and (isinstance(filter_coefs, tuple) or len(filter_coefs) > 0):
            for ch in self.channels:
                if len(self.data[ch]) == 0:
                    continue

                if isinstance(filter_coefs, tuple) and len(filter_coefs) == 2:
                    b, a = filter_coefs
                    self.data_filtered[ch] = lfilter(b, a, np.array(self.data[ch])).tolist()
                else:
                    self.data_filtered[ch] = lfilter(filter_coefs, 1.0, np.array(self.data[ch])).tolist()

        if self.plot_mode == 'realtime' and not self.plot_closed_by_user:
            print("Plot remaining open. Close window manually to exit.")
            plt.show(block=True)

        # NEW BLOCK: Logic to plot at the end
        if self.plot_mode == 'end' and self.time_var:
            print("\nGenerating plot at the end of acquisition...")
            self.title = f"PYDAQ - Final Acquisition: {self.device}, {self.channel}"
            self._start_updatable_plot(title_str=self.title)
            self._update_plot(
                self.time_var,
                self.data,
                y2_values=self.data_filtered if self.data_filtered else None,
                y1_label="Original Data", 
                y2_label="Filtered Data"
            )
            plt.show(block=True) # Keeps the final plot open

        for ch in self.channels:
            time_formated = [f"{t:.10f}" for t in self.time_var[ch]]
            self._save_data(time_formated, f"time_{ch}.dat")
            self._save_data(self.data[ch], f"data_{ch}.dat")
            if self.data_filtered[ch]:
                self._save_data(self.data_filtered[ch], f"data_filtered_{ch}.dat")
            if len(self.coeffs) > 0:
                self._save_data(self.coeffs, "filter_coeffs.dat")
            print("\nData saved ...")

        if self.plot_mode == 'realtime' and self.plot_closed_by_user:
            plt.ioff()
            plt.close(self.fig)
        return

    def _acquisition_worker_arduino(self, data_queue):
        """
        This function runs in a separate thread to acquire data from Arduino via serial.
        It does not touch the GUI, it only collects data and puts it on the queue.
        """

        channels = self.channels
        n_channels = len(channels)

        # Wait for plot to be ready before starting acquisition to synchronize time_now to ~0
        self.plot_ready_event.wait()
        num_cycles_performed = 0

        try:
            self._open_serial()
            
            # --- WARM-UP SECTION ---
            # Send an initial command (b"0") to "wake up" the Arduino.
            time.sleep(0.05)
            self.ser.reset_input_buffer()

            # Perform a "warm-up read". This is the call that will be slow.
            # We will not use this data, so we assign it to '_' (discard).
            _ = self.ser.readline()
            # --- END WARM-UP SECTION ---

            st_worker = time.perf_counter()
            self.st_worker = st_worker
            
            for k in range(self.cycles):

                if not self.acquisition_running:
                    break
                
                raw = self.ser.readline()

                try:
                    values = list(map(int, raw.decode("utf-8").strip().split(",")))

                    if len(values) < n_channels:
                        raise ValueError("Incomplete multichannel frame")

                    time_now = time.perf_counter() - st_worker

                    # Distribui os valores por canal
                    for i, ch in enumerate(channels):
                        value = values[i] * self.ard_vpb
                        data_queue.put((time_now, ch, value))

                    #scaled_values = [v * self.ard_vpb for v in values[:n_channels]]
                    #data_queue.put((time_now, channels, digital_val * 5.0, scaled_values))

                    num_cycles_performed += 1

                except (ValueError, UnicodeDecodeError):
                    warnings.warn(f"Invalid multichannel read: {raw}")
                    continue

                wait_time = (st_worker + num_cycles_performed * self.ts) - time.perf_counter()
                if wait_time > 0:
                    time.sleep(wait_time)
                else:
                    warnings.warn(
                        "Time spent to append data and update interface was greater than ts. You CANNOT trust time.dat"
                    )
        except serial.SerialException as e:
            warnings.warn(f"Failed to open serial port {self.com_port}: {e}")
            print(f"ERROR: Failed to open serial port {self.com_port}: {e}")
            self.acquisition_running = False
        finally:
            if hasattr(self, 'ser') and self.ser.is_open:
                self.ser.close()
                print(f"Serial port {self.com_port} closed.")
            data_queue.put(None)
            total_acquisition_duration = time.perf_counter() - st_worker
            if num_cycles_performed > 0:
                avg_acquisition_time_per_cycle = total_acquisition_duration / num_cycles_performed
                print(
                    f"\nAcquisition Thread finished. "
                    f"Total time: {total_acquisition_duration:.5f}s | "
                    f"Cycles acquired: {num_cycles_performed} | "
                    f"Average time per cycle: {avg_acquisition_time_per_cycle:.5f}s"
                )
            else:
                print("\nAcquisition Thread finished. No data cycles acquired.")

    def get_data_arduino(self, filter_coefs=None):
        """
        This function can be used for data acquisition and step response experiments using Python + Arduino
        through serial communication. Now adapted to threading model for consistent plot handling.
        """

        # Data storage per channel
        self.data = {ch: [] for ch in self.channels}
        self.time_var = {ch: [] for ch in self.channels}
        self.data_filtered = {ch: [] for ch in self.channels}
        self.coeffs = []

        if filter_coefs is not None and (isinstance(filter_coefs, tuple) or len(filter_coefs) > 0):
            self.coeffs = filter_coefs
        else:
            self.coeffs = []

        data_queue = queue.Queue()
        self.acquisition_running = True
        self.plot_closed_by_user = False
        self.plot_ready_event.clear()

        self._check_path()
        self.cycles = int(np.floor(self.session_duration / self.ts)) + 1

        acquisition_thread = threading.Thread(
            target=self._acquisition_worker_arduino,
            args=(data_queue,), 
            daemon=True
        )
        acquisition_thread.start()

        if self.plot_mode == 'realtime':
            self.title = f"PYDAQ - Data Acquisition. Arduino, Port: {self.com_port}"
            self._start_updatable_plot(title_str=self.title)
            self.fig.canvas.mpl_connect('close_event', self._on_plot_close)
            time.sleep(0.5)
            self.plot_ready_event.set()
        else:
            # If it is not in real time, release the acquisition immediately.
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
                    self.acquisition_running = False
                    break

                timestamp, channel, value = item
                self.time_var[channel].append(timestamp)
                self.data[channel].append(value)

                now = time.perf_counter()

                if self.plot_mode == 'realtime' and (now - last_plot_update_time >= plot_update_interval or not self.acquisition_running):

                    # Applies the filter for real-time plotting
                    if filter_coefs is not None and (isinstance(filter_coefs, tuple) or len(filter_coefs) > 0):
                        
                        for ch in self.channels:
                            if len(self.data[ch]) == 0:
                                continue

                            if isinstance(filter_coefs, tuple) and len(filter_coefs) == 2:
                                b, a = filter_coefs

                                self.data_filtered[ch] = lfilter(b, a, np.array(self.data[ch])).tolist()

                            else:
                                self.data_filtered[ch] = lfilter(filter_coefs, 1.0, np.array(self.data[ch])).tolist()

                    self._update_plot(
                        self.time_var,
                        self.data,
                        y2_values=self.data_filtered if self.data_filtered else None,
                        y1_label="Original Data", 
                        y2_label="Filtered Data"
                    )
                    last_plot_update_time = now

            except queue.Empty:
                time.sleep(0.01)
                if not self.acquisition_running and data_queue.empty():
                    break
        
        acquisition_thread.join()

        # Applies final filter if coefficients are present (to save and plot at the end)
        if filter_coefs is not None and (isinstance(filter_coefs, tuple) or len(filter_coefs) > 0):
            for ch in self.channels:
                if len(self.data[ch]) == 0:
                    continue
                if isinstance(filter_coefs, tuple) and len(filter_coefs) == 2:
                    b, a = filter_coefs
                    self.data_filtered[ch] = lfilter(b, a, np.array(self.data[ch])).tolist()
                else:
                    self.data_filtered[ch] = lfilter(filter_coefs, 1.0, np.array(self.data[ch])).tolist()

        if self.plot_mode == 'realtime' and not self.plot_closed_by_user:
            print("Plot remaining open. Close window manually to exit.")
            plt.show(block=True)

        # NEW BLOCK: Logic to plot at the end
        if self.plot_mode == 'end' and self.time_var:
            print("\nGenerating plot at the end of acquisition...")
            self.title = f"PYDAQ - Final Acquisition: Arduino, Port: {self.com_port}"
            self._start_updatable_plot(title_str=self.title)
            self._update_plot(
                self.time_var,
                self.data,
                y2_values=self.data_filtered if self.data_filtered else None,
                y1_label="Original Data", 
                y2_label="Filtered Data"
            )
            plt.show(block=True) # Keeps the final plot open

        if self.save:
            print("\nSaving data ...")
            for ch in self.channels:
                time_formated = [f"{t:.10f}" for t in self.time_var[ch]]
                self._save_data(time_formated, f"time_{ch}.dat")
                self._save_data(self.data[ch], f"data_{ch}.dat")
                if self.data_filtered[ch]:
                    self._save_data(self.data_filtered[ch], f"data_filtered_{ch}.dat")

            if len(self.coeffs) > 0:
                self._save_data(self.coeffs, "filter_coeffs.dat")

            print("\nData saved ...")

        if self.plot_mode == 'realtime' and self.plot_closed_by_user:
            plt.ioff()
            plt.close(self.fig)

        return