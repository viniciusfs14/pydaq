import os
import time
import numpy as np

import serial
import serial.tools.list_ports
from pydaq.utils.base import Base

import threading
import queue

import matplotlib.pyplot as plt
import warnings
from scipy.linalg import solve_discrete_are

try:
    import nidaqmx
    from nidaqmx.constants import TerminalConfiguration
    NIDAQ_AVAILABLE = True
except (ImportError, OSError):
    NIDAQ_AVAILABLE = False
    class TerminalConfiguration:
        DIFF = "Diff"
        RSE = "RSE"
        NRSE = "NRSE"



class LQRControl(Base):
    """
     Class developed to construct Graphical User Interface for lqr control using arduino and NIDAQ boards

    :author: Samir Angelo Milani Martins
          - https://www.samirmartins.com.br
          - https://www.github.com/samirmartins/

     :params:
         device: nidaq default device.
         ao_channel: nidaq default analog output channel
         ai_channel: nidaq default analog input channel
         ts: sample period, in seconds.
         session_duration: session duration, in seconds.
         A, B and LQR matrices: system and cost matrices for LQR control
         terminal: 'Diff', 'RSE' or 'NRSE': terminal configuration (differential, referenced single ended or non-referenced single ended)
         plot: if True, plot data iteractively as they are sent/acquired

    """

    def __init__(
        self,
        device="Dev1",
        ao_channel="ao0",
        ai_channel="ai0",
        ts=0.2,
        session_duration=10.0,
        step_time=3.0,
        terminal="Diff",
        com="COM1",
        plot_mode="no", # Options: "realtime", "end", "no"
        save=True,
    ):

        super().__init__()
        self.ts = ts
        self.session_duration = session_duration
        self.plot_mode = plot_mode
        self.step_time = step_time
        self.device = device
        self.ai_channel = ai_channel
        self.ao_channel = ao_channel
        self.save = save

        # Terminal configuration
        self.terminal = self.term_map[terminal]

        # State-Space Matrices and LQR
        self.A = None
        self.B = None
        self.C = None
        self.D = None
        self.Q = None
        self.R = None
        self.K = None # LQR Gain

        self.time_var = {}
        self.input_data = {}
        self.output_data = {}

        # COM ports
        self.com_ports = [i.description for i in serial.tools.list_ports.comports()]
        self.com_port = com

        # Plot title
        self.title = None

        # Defining default path
        self.path = os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")

        # Arduino ADC resolution (in bits)
        self.arduino_ai_bits = 10
        self.ard_ao_max, self.ard_ao_min = 5, 0
        self.ard_vpb = (self.ard_ao_max - self.ard_ao_min) / ((2**self.arduino_ai_bits) - 1)

        # Legends
        self.legend = ["Output", "Input"]

        # Threading control flags and events
        self.acquisition_running = False
        self.plot_closed_by_user = False # See if its will be used after later check
        self.plot_ready_event = threading.Event()

        self.channels = [ai_channel]        # default single channel
        self.ao_channels = [ao_channel]     # default single channel

    def _calculate_lqr_gain(self):
        """Calculate the gain K by solving the Riccati Algebraic Equation (ARE)."""
        try:
            A = np.array(self.A)
            B = np.array(self.B)
            Q = np.array(self.Q)
            R = np.array(self.R)

            P = solve_discrete_are(A, B, Q, R)


            self.K = np.linalg.solve(
                self.B.T @ P @ self.B + self.R,
                self.B.T @ P @ self.A
            )

            print(f"LQR Gain K calculated: {self.K}")
        except Exception as e:
            warnings.warn(f"Failed to calculate LQR gain: {e}")
            self.K = np.zeros((len(self.ao_channels), len(self.channels)))

    # Handler for plot window closure
    def _on_plot_close(self, event):
        """..."""
        print("Plot window closed by user. Initiating shutdown...")
        self.acquisition_running = False
        self.plot_closed_by_user = True

    def _lqr_control_worker_arduino(self, data_queue):
        self.plot_ready_event.wait()

        n_ai = len(self.channels)
        n_ao = len(self.ao_channels)
    
        
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
            # Send an initial command (b"0") to "wake up" the Arduino.
            self.ser.write(b"0")
            self.ser.reset_input_buffer()

            # Perform a "warm-up read". This is the call that will be slow.
            # We will not use this data, so we assign it to '_' (discard).
            _ = self.ser.readline()
            # --- END WARM-UP SECTION ---

            num_cycles_performed = 0
            st_worker = time.perf_counter()
            self.st_worker = st_worker

            for k in range(self.cycles):
                if not self.acquisition_running:
                    break
                try: 
                    self.ser.reset_input_buffer()
                    self.ser.readline()
                    
                    raw = self.ser.readline()

                    values = list(map(int, raw.decode("utf-8").strip().split(",")))

                    if len(values) < 6:
                        warnings.warn("Incomplete universal frame")
                        continue

                    time_now = time.perf_counter() - st_worker

                    x_list = [] # Take only what interests you!
                    for ch in self.channels:  # Ex: self.channels = ['A0', 'A2']
                        idx = int(ch.replace("A", ""))  # Extracts the channel number (e.g., 'A2' becomes the integer 2)
                        x_list.append(values[idx] * self.ard_vpb) # Take the value at the exact index

                    x = np.array(x_list).reshape(-1, 1) # Create state vector

                    # --- LQR Control Law: u = -Kx ---
                    u = -self.K @ x

                    # Saturation & Universal Write
                    u_to_plot = []
                    msg_parts = []

                    for i, ch in enumerate(self.ao_channels):
                        u_val = np.clip(float(u[i]), 0, 5)
                        u_to_plot.append(u_val)

                        duty = int((u_val / 5.0) * 255)
                        pin_num = ch.replace("D", "")
                        msg_parts.append(f"{pin_num}:{duty}")

                    # CSV Multichannel write
                    msg = ",".join(msg_parts) + "\n"
                    self.ser.write(msg.encode())

                    for i, ch in enumerate(self.channels):
                        # Nota: associamos u[0] ao primeiro canal por padrão
                        u_ref = u_to_plot[0] if len(u_to_plot) > 0 else 0
                        data_queue.put((time_now, ch, u_ref, x[i][0]))

                except (ValueError, UnicodeDecodeError):
                    warnings.warn(f"Invalid multichannel read: {raw}")
                    continue
                
                num_cycles_performed += 1

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
            # Turn off
            stop_msg = ",".join(["0"] * n_ao) + "\n"
            self.ser.write(stop_msg.encode())
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


    
    def lqr_control_arduino(self):

        """
        This method performs the LQR control using an Arduino board for given parameters.

        :example:
            lqr_control_arduino()

        """

        if not self._check_lqr_dimensions():
            return
        
        self._check_path()

        self._calculate_lqr_gain()
        self.cycles = int(np.floor(self.session_duration / self.ts)) + 1

        print("Running LQR control for Arduino...")
        self.time_var = {ch: [] for ch in self.channels}
        self.input_h = {ch: [] for ch in self.channels}
        self.output_h = {ch: [] for ch in self.channels}

        data_queue = queue.Queue()
        self.acquisition_running = True
        self.plot_closed_by_user = False
        self.plot_ready_event.clear()

        self.cycles = int(np.floor(self.session_duration / self.ts)) + 1

        acquisition_thread = threading.Thread(
            target=self._lqr_control_worker_arduino,
            args=(data_queue,),
            daemon=True
        )
        acquisition_thread.start()

        if self.plot_mode == 'realtime':
            self.title = f"PYDAQ - LQR Control (Arduino), Port: {self.com_port}"
            self._start_updatable_plot_lqr(title_str=self.title)
            self.fig.canvas.mpl_connect('close_event', self._on_plot_close)

            # Add a short delay to allow the plot window to open fully
            print("\nReal-time plot started. Waiting 0.5s for the window to render...")
            time.sleep(0.5)

            self.plot_ready_event.set()
        else:
            self.plot_ready_event.set()

        # Plot update throttling logic for performance
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
                    # Drain the queue to ensure all data is processed
                    while not data_queue.empty():
                        remaining_item = data_queue.get_nowait()
                        if remaining_item is not None:
                            t, ch, u, y = remaining_item
                            self.time_var[ch].append(t)
                            self.input_h[ch].append(u)
                            self.output_h[ch].append(y)
                    break

                t, ch, u, y = item
                self.time_var[ch].append(t)
                self.input_h[ch].append(u)
                self.output_h[ch].append(y)

                # Throttle plot updates for performance
                now = time.perf_counter()

                if self.plot_mode == 'realtime' and (now - last_plot_update_time >= plot_update_interval or not self.acquisition_running):
                    self._update_plot_lqr(
                        x_values=self.time_var,
                        y_values=self.output_h,
                        u_values=self.input_h,
                        y_label="System Response / AI",
                        u_label="Control Effort / AO",
                        y_channel_names=self.channels,     # Ex: ["A0", "A1"] ou ["ai0"]
                        u_channel_names=self.ao_channels   # Ex: ["D8", "D9"] ou ["ao0"]
                    )
                    last_plot_update_time = now

            except queue.Empty:
                # This keeps the loop responsive
                time.sleep(0.01)
                if not self.acquisition_running and data_queue.empty():
                    break

        acquisition_thread.join()

        if self.plot_mode == 'end' and self.time_var:
            self.title = f"PYDAQ - Final Step Response: Arduino, Port: {self.com_port}"
            self._start_updatable_plot_lqr(title_str=self.title)
            self._update_plot_lqr(
                        x_values=self.time_var,
                        y_values=self.output_h,
                        u_values=self.input_h,
                        y_label="System Response / AI",
                        u_label="Control Effort / AO",
                        y_channel_names=self.channels,     # Ex: ["A0", "A1"] ou ["ai0"]
                        u_channel_names=self.ao_channels   # Ex: ["D8", "D9"] ou ["ao0"]
                    )
            plt.show(block=True)

        if self.save:
            print("\nSaving data ...")
            self._save_data(self.time_var, "time.dat")
            self._save_data(self.input_h, "input.dat")
            self._save_data(self.output_h, "output.dat")
            print("\nData saved ...")

        if self.plot_mode == 'realtime' and not self.plot_closed_by_user:
            print("\nPlot remains open. Close window manually to exit.")
            plt.show(block=True)
        return

    def _lqr_control_worker_nidaq(self, data_queue):
        # Wait for plot to be ready to synchronize start time
        self.plot_ready_event.wait()
        st_worker = time.perf_counter()
        task_ao = nidaqmx.Task()
        task_ai = nidaqmx.Task()
    
        try:
            num_cycles_performed = 0
            # === NEW: Multi-channel string construction ===
            ai_str = ",".join([f"{self.device}/{ch}" for ch in self.channels])
            ao_str = ",".join([f"{self.device}/{ch}" for ch in self.ao_channels])

            task_ai.ai_channels.add_ai_voltage_chan(ai_str, terminal_config=self.terminal)
            task_ao.ao_channels.add_ao_voltage_chan(ao_str, min_val=0, max_val=5)

            n_ai = len(self.channels)
            n_ao = len(self.ao_channels)

            for k in range(self.cycles):
                if not self.acquisition_running:
                    break

                # Leitura Multicanal
                y_raw = task_ai.read()
                y_list = y_raw if n_ai > 1 else [y_raw]
                x = np.array(y_list).reshape(-1, 1)

                u = -self.K @ x
                
                u_out = [np.clip(float(u[i]), 0, 5) for i in range(n_ao)]
                task_ao.write(u_out if n_ao > 1 else u_out[0])

                time_now = time.perf_counter() - st_worker
                
                # === NEW: queue per channel ===
                for i, ch in enumerate(self.channels):
                    data_queue.put((time_now, ch, u_out[0], x[i][0]))

                num_cycles_performed += 1
                wait_time = (st_worker + (k + 1) * self.ts) - time.perf_counter()
                if wait_time > 0:
                    time.sleep(wait_time)
                else:
                    warnings.warn(
                        "Time spent to append data and update interface was greater than ts. You CANNOT trust time.dat"
                    )
        
        finally:
            # Turn off outputs
            try:
                if n_ao == 1:
                    task_ao.write(0)
                else:
                    task_ao.write([0] * n_ao)
            except:
                pass

            task_ao.close()
            task_ai.close()
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

    def lqr_control_nidaq(self):
        """
        This method performs the LQR control using a NIDAQ board for given parameters.

        :example:
            lqr_control_nidaq()

        """

        # --- NIDAQ SAFETY LOCK ---
        if not self._check_nidaq_availability():
            return

        # --- LQR SAFETY LOCK ---
        if not self._check_lqr_dimensions():
            return
        
        self._calculate_lqr_gain()
        self.cycles = int(np.floor(self.session_duration / self.ts)) + 1
        self.time_var = {ch: [] for ch in self.channels}
        self.input_h = {ch: [] for ch in self.channels}
        self.output_h = {ch: [] for ch in self.channels}

        data_queue = queue.Queue()
        self.acquisition_running = True
        self.plot_closed_by_user = False
        self.plot_ready_event.clear()

        self._check_path()

        acquisition_thread = threading.Thread(
            target=self._lqr_control_worker_nidaq,
            args=(data_queue,),
            daemon=True
        )
        acquisition_thread.start()

        if self.plot_mode == 'realtime':
            self.title = f"PYDAQ - Step Response (NIDAQ). {self.device}, Channels: {self.channels}"
            self._start_updatable_plot_lqr(title_str=self.title)
            self.fig.canvas.mpl_connect('close_event', self._on_plot_close)

            # Add a short delay to allow the plot window to open fully
            print("\nReal-time plot started. Waiting 0.5s for the window to render...")
            time.sleep(0.5)

            self.plot_ready_event.set()
        else:
            self.plot_ready_event.set() # Allow acquisition to start immediately

        # Plot update throttling logic for performance
        if self.ts >= 0.05:
            plot_update_interval = 0.05
        else:
            plot_update_interval = 0.25

        last_plot_update_time = time.perf_counter()

        # Main loop for data consumption and plotting
        while (self.acquisition_running and not self.plot_closed_by_user) or not data_queue.empty():
            try:
                item = data_queue.get(timeout=0.01)

                if item is None:
                    self.acquisition_running = False

                    # Drain the queue to ensure all data is processed
                    while not data_queue.empty():
                        remaining_item = data_queue.get_nowait()
                        if remaining_item is not None:
                            t, ch, u, y = item
                            self.time_var[ch].append(t)
                            self.input_h[ch].append(u)
                            self.output_h[ch].append(y)
                    break

                t, ch, u, y = item

                self.time_var[ch].append(t)
                self.input_h[ch].append(u)
                self.output_h[ch].append(y)

                # Throttle plot updates for performance
                now = time.perf_counter()

                if self.plot_mode == 'realtime' and (
                    now - last_plot_update_time >= plot_update_interval
                    or not self.acquisition_running
                ):
                    self._update_plot_lqr(
                        x_values=self.time_var,
                        y_values=self.output_h,
                        u_values=self.input_h,
                        y_label="System Response / AI",
                        u_label="Control Effort / AO",
                        y_channel_names=self.channels,     # Ex: ["A0", "A1"] ou ["ai0"]
                        u_channel_names=self.ao_channels   # Ex: ["D8", "D9"] ou ["ao0"]
                    )
                    last_plot_update_time = now

            except queue.Empty:
                # This keeps the loop responsive
                time.sleep(0.01)
                if not self.acquisition_running and data_queue.empty():
                    break

        acquisition_thread.join()

        if self.plot_mode == 'end' and any(self.time_var.values()):
            self.title = f"PYDAQ - Final Step Response (NIDAQ)"
            self._start_updatable_plot_lqr(title_str=self.title)
            self._update_plot_lqr(
                        x_values=self.time_var,
                        y_values=self.output_h,
                        u_values=self.input_h,
                        y_label="System Response / AI",
                        u_label="Control Effort / AO",
                        y_channel_names=self.channels,     # Ex: ["A0", "A1"] ou ["ai0"]
                        u_channel_names=self.ao_channels   # Ex: ["D8", "D9"] ou ["ao0"]
                    )
            plt.show(block=True)

        if self.save:
            print("\nSaving data ...")
            self._save_data(self.time_var, "time.dat")
            self._save_data(self.input_h, "input.dat")
            self._save_data(self.output_h, "output.dat")
            print("\nData saved ...")

        if self.plot_mode == 'realtime' and not self.plot_closed_by_user:
            print("\nPlot remains open. Close window manually to exit.")
            plt.show(block=True)

        return

    def simulate_lqr(self):
        """
        Executes a pure mathematical simulation of the discrete LQR 
        (without connecting to the hardware) and displays the outputs (y) and control effort (u).
        """

        if self.A is None or self.B is None or self.Q is None or self.R is None:
            warnings.warn("A, B, Q, R matrices are not defined. Cannot simulate.")
            return
        
        if not self._check_lqr_dimensions():
            return

        self._calculate_lqr_gain()
        
        A_mat = np.array(self.A)
        B_mat = np.array(self.B)
        
        n_states = A_mat.shape[0]
        n_inputs = B_mat.shape[1]

        # Define C and D matrices. If they don't exist, assume C = Identity and D = Zeros
        if hasattr(self, 'C') and self.C is not None:
            C_mat = np.array(self.C)
        else:
            C_mat = np.eye(n_states)

        if hasattr(self, 'D') and self.D is not None:
            D_mat = np.array(self.D)
        else:
            n_outputs = C_mat.shape[0]
            D_mat = np.zeros((n_outputs, n_inputs))

        # Define initial condition (e.g., all states start at 1.0)
        x = np.ones((n_states, 1))

        # Calculate number of iterations based on session duration and sample time
        steps = int(np.floor(self.session_duration / self.ts)) + 1
        
        history_y = []
        history_u = []
        time_arr = []

        print("Running pure LQR simulation...")
        for k in range(steps):
            # Control law
            u = -self.K @ x
            
            # Output equation (What the AI sensors would read)
            y = C_mat @ x + D_mat @ u

            # Store data
            history_y.append(y.flatten())
            history_u.append(u.flatten())
            time_arr.append(k * self.ts)

            # Update the state for the next step: x(k+1) = Ax(k) + Bu(k)
            x = A_mat @ x + B_mat @ u

        history_y = np.array(history_y)
        history_u = np.array(history_u)

        # Generate Static Plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
        fig.suptitle("LQR Pure Simulation (No Hardware)", fontsize=14)

        # Output Plot (System Response - y)
        for i in range(history_y.shape[1]):
            ax1.plot(time_arr, history_y[:, i], label=f"Output y{i+1}", linewidth=2)
        ax1.set_ylabel("Amplitude")
        ax1.grid(True)
        ax1.legend(loc="upper right")

        # Control Effort Plot (Input - u)
        for i in range(history_u.shape[1]):
            ax2.plot(time_arr, history_u[:, i], label=f"Control Effort u{i+1}", linewidth=2)
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Amplitude")
        ax2.grid(True)
        ax2.legend(loc="upper right")

        plt.tight_layout()
        plt.show(block=True)

    def _check_lqr_dimensions(self):
        """
        Verifies if the dimensions of matrices A and B match the selected AI and AO channels.
        Returns True if correct, False otherwise.
        """
        if self.A is None or self.B is None:
            self._dim_error("Matrices A and B must be defined before running LQR!")
            return False

        A = np.array(self.A)
        B = np.array(self.B)

        n_states = len(self.channels)      # Number of AI channels
        n_inputs = len(self.ao_channels)   # Number of AO channels

        # Check matrix A: must be square and match the number of AI channels
        if A.ndim != 2 or A.shape[0] != A.shape[1] or A.shape[0] != n_states:
            self._dim_error(f"Matrix A must be {n_states}x{n_states} to match AI channels!")
            return False

        # Check matrix B: rows must match AI channels, cols must match AO channels
        if B.ndim != 2 or B.shape[0] != n_states or B.shape[1] != n_inputs:
            self._dim_error(f"Matrix B must be {n_states}x{n_inputs} to match AI and AO channels!")
            return False

        return True