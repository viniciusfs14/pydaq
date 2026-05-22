import os
import time
import numpy as np

import serial
import serial.tools.list_ports
from pydaq.utils.base import Base, NIDAQ_AVAILABLE, TerminalConfiguration, nidaqmx

import threading
import queue

import matplotlib.pyplot as plt
import warnings
from scipy.linalg import solve_discrete_are


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

        # Plot preferences default (y, x, e, u)
        self.plot_prefs = {'y': True, 'x': True, 'e': True, 'u': True}

        # --- NEW: Reference Tracking parameters ---
        self.use_reference = False
        self.x_ref = None
        self.u_eq = None

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

        self.output_mode = "free"  # default

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

            print(f"\n[PYDAQ] LQR Gain K calculated: {self.K}")
        except Exception as e:
            warnings.warn(f"[PYDAQ] Failed to calculate LQR gain: {e}")
            self.K = np.zeros((len(self.ao_channels), len(self.channels)))

    # Handler for plot window closure
    def _on_plot_close(self, event):
        """..."""
        print("\n[PYDAQ] Plot window closed by user. Initiating shutdown...")
        self.acquisition_running = False
        self.plot_closed_by_user = True

    def _lqr_control_worker_arduino(self, data_queue):
        self.plot_ready_event.wait()

        n_ai = len(self.channels)
        n_ao = len(self.ao_channels)

        # Safely define C and D matrices (Fallback for command line usage)
        C_mat = np.array(self.C) if self.C is not None else np.eye(n_ai)
        n_outputs = C_mat.shape[0]
        D_mat = np.array(self.D) if self.D is not None else np.zeros((n_outputs, n_ao))

        st_worker = None
        try:
            self._open_serial()

            if not self._verify_arduino_firmware():
                self.ser.close()
                warnings.warn("[PYDAQ] PyDAQ Firmware not detected on this board! Please go to the top menu and click on 'Arduino - Firmware' to upload the correct code.")
                return 

            # Wake up the Arduino
            self.ser.write(b"0")
            self.ser.reset_input_buffer()
            _ = self.ser.readline()

            num_cycles_performed = 0
            st_worker = time.perf_counter()
            self.st_worker = st_worker

            # Prepare Reference Logic (Fixed or Trajectory)
            if self.use_reference and self.x_ref is not None and self.u_eq is not None:
                x_ref_mat = np.array(self.x_ref, ndmin=2)
                u_eq_mat = np.array(self.u_eq, ndmin=2)

                # Identify if it's a trajectory based on matrix shape
                traj_x = (x_ref_mat.shape[1] == n_ai and x_ref_mat.shape[0] > 1)
                traj_u = (u_eq_mat.shape[1] == n_ao and u_eq_mat.shape[0] > 1)
            else:
                x_ref_mat = np.zeros((1, n_ai))
                u_eq_mat = np.zeros((1, n_ao))
                traj_x = False
                traj_u = False

            for k in range(self.cycles):
                if not self.acquisition_running:
                    break
                try: 
                    self.ser.reset_input_buffer()
                    self.ser.readline()
                    
                    raw = self.ser.readline()
                    try:
                        values = list(map(int, raw.decode("utf-8").strip().split(",")))
                    except (ValueError, UnicodeDecodeError):
                        warnings.warn(f"[PYDAQ] Data parsing error...")
                        continue

                    time_now = time.perf_counter() - st_worker

                    x_list = [] 
                    for ch in self.channels:  
                        idx = int(ch.replace("A", ""))  
                        x_list.append(values[idx] * self.ard_vpb) 

                    x = np.array(x_list).reshape(-1, 1) 

                    # Update Reference Vectors for the current step
                    if traj_x:
                        idx_x = min(k, x_ref_mat.shape[0] - 1)
                        x_ref_vec = x_ref_mat[idx_x, :].reshape(n_ai, 1)
                    else:
                        x_ref_vec = x_ref_mat.reshape(n_ai, 1)

                    if traj_u:
                        idx_u = min(k, u_eq_mat.shape[0] - 1)
                        u_eq_vec = u_eq_mat[idx_u, :].reshape(n_ao, 1)
                    else:
                        u_eq_vec = u_eq_mat.reshape(n_ao, 1)

                    # LQR Control Law
                    e = x - x_ref_vec                    # State Error
                    u = -self.K @ e + u_eq_vec           # Control Effort

                    # Output equation y = Cx + Du
                    y = C_mat @ x + D_mat @ u

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

                    # Package data dynamically mapping channel names
                    x_dict = {ch: float(x[i][0]) for i, ch in enumerate(self.channels)}
                    e_dict = {ch: float(e[i][0]) for i, ch in enumerate(self.channels)}
                    u_dict = {ch: u_to_plot[i] for i, ch in enumerate(self.ao_channels)}
                    y_dict = {f"y{i+1}": float(y[i][0]) for i in range(n_outputs)}
                    data_queue.put((time_now, x_dict, e_dict, u_dict, y_dict))

                except (ValueError, UnicodeDecodeError):
                    warnings.warn(f"[PYDAQ] Data parsing error: Invalid multichannel read from Arduino: {raw}")
                    continue
                
                num_cycles_performed += 1

                wait_time = (st_worker + num_cycles_performed * self.ts) - time.perf_counter()
                if wait_time > 0:
                    time.sleep(wait_time)
                else:
                    warnings.warn("[PYDAQ] Time spent to append data and update interface was greater than ts. You CANNOT trust time.dat")

        except serial.SerialException as err:
            warnings.warn(f"[PYDAQ] Hardware error: Failed to open serial port {self.com_port}. Details: {err}")
        finally:
            if hasattr(self, 'ser') and self.ser.is_open:
                try:
                    stop_parts = []
                    for ch in self.ao_channels:
                        pin_num = ch.replace("D", "")
                        stop_parts.append(f"{pin_num}:0")
                    self.ser.write((",".join(stop_parts) + "\n").encode())
                except:
                    pass
                self.ser.close()
            data_queue.put(None)
            if st_worker is not None:
                total_duration = time.perf_counter() - st_worker
                if num_cycles_performed > 0:
                    avg = total_duration / num_cycles_performed
                    print(f"\n[PYDAQ] Thread finished. Total time: {total_duration:.5f}s | Cycles: {num_cycles_performed} | Avg: {avg:.5f}s")       
                else:
                    print("\n[PYDAQ] Thread finished. No data cycles acquired.")
            else:
                print("\n[PYDAQ] Thread finished before acquisition started.")

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

        # --- NEW: Unified time list and state/input/output dictionaries ---
        n_outputs = np.array(self.C).shape[0] if self.C is not None else len(self.channels)
        self.time_var = []
        self.state_h = {ch: [] for ch in self.channels}
        self.error_h = {ch: [] for ch in self.channels}
        self.input_h = {ch: [] for ch in self.ao_channels}
        self.output_h = {f"y{i+1}": [] for i in range(n_outputs)}

        data_queue = queue.Queue()
        self.acquisition_running = True
        self.plot_closed_by_user = False
        self.plot_ready_event.clear()

        self.cycles = int(np.floor(self.session_duration / self.ts)) + 1

        print("\n[PYDAQ] Running LQR Control ...")
        acquisition_thread = threading.Thread(
            target=self._lqr_control_worker_arduino,
            args=(data_queue,),
            daemon=True
        )
        acquisition_thread.start()

        if self.plot_mode == 'realtime':
            self.title = f"PYDAQ - LQR Control (Arduino), Port: {self.com_port}"
            self._start_updatable_plot_lqr(title_str=self.title, show_pwm_axis=True)
            self.fig.canvas.mpl_connect('close_event', self._on_plot_close)

            time.sleep(0.5)

            self.plot_ready_event.set()
        else:
            self.plot_ready_event.set()

        # Plot update throttling logic for performance
        plot_update_interval = max(self.ts*0.9, 0.05)

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
                            t, x_dict, e_dict, u_dict, y_dict = remaining_item
                            self.time_var.append(t)
                            for ch_key, val in x_dict.items(): self.state_h[ch_key].append(val)
                            for ch_key, val in e_dict.items(): self.error_h[ch_key].append(val)
                            for ch_key, val in u_dict.items(): self.input_h[ch_key].append(val)
                            for ch_key, val in y_dict.items(): self.output_h[ch_key].append(val)
                    break

                t, x_dict, e_dict, u_dict, y_dict = item
                self.time_var.append(t)
                for ch_key, val in x_dict.items(): self.state_h[ch_key].append(val)
                for ch_key, val in e_dict.items(): self.error_h[ch_key].append(val)
                for ch_key, val in u_dict.items(): self.input_h[ch_key].append(val)
                for ch_key, val in y_dict.items(): self.output_h[ch_key].append(val)

                # Throttle plot updates for performance
                now = time.perf_counter()

                if self.plot_mode == 'realtime' and (now - last_plot_update_time >= plot_update_interval or not self.acquisition_running):
                    self._update_plot_lqr(
                        time_values=self.time_var,
                        y_values=self.output_h,
                        x_state_values=self.state_h,
                        e_values=self.error_h,
                        u_values=self.input_h
                    )
                    last_plot_update_time = now

            except queue.Empty:
                # This keeps the loop responsive
                time.sleep(0.01)
                if not self.acquisition_running and data_queue.empty():
                    break

        acquisition_thread.join()

        if self.plot_mode == 'end' and self.time_var:
            self.title = f"PYDAQ - Final Step Response (NIDAQ)"
            self._start_updatable_plot_lqr(title_str=self.title)
            self._update_plot_lqr(
                time_values=self.time_var,
                y_values=self.output_h,
                x_state_values=self.state_h,
                e_values=self.error_h, 
                u_values=self.input_h
            )
            plt.show(block=True)

        if self.save:
            print("\n[PYDAQ] Saving data ...")
            self._save_data(self.time_var, "time.dat")
            self._save_data(self.state_h, "states.dat")
            self._save_data(self.error_h, "error.dat") 
            self._save_data(self.input_h, "control.dat")
            self._save_data(self.output_h, "output.dat")
            print("\n[PYDAQ] Data saved ...")

        if self.plot_mode == 'realtime' and not self.plot_closed_by_user:
            print("\n[PYDAQ] Plot remains open. Close window manually to exit.")
            plt.show(block=True)
        return

    def _lqr_control_worker_nidaq(self, data_queue):
        self.plot_ready_event.wait()
        st_worker = None
        task_ao = nidaqmx.Task()
        task_ai = nidaqmx.Task()
    
        try:
            num_cycles_performed = 0
            ai_str = ",".join([f"{self.device}/{ch}" for ch in self.channels])
            ao_str = ",".join([f"{self.device}/{ch}" for ch in self.ao_channels])

            task_ai.ai_channels.add_ai_voltage_chan(ai_str, terminal_config=self.terminal)
            task_ao.ao_channels.add_ao_voltage_chan(ao_str, min_val=0, max_val=5)

            n_ai = len(self.channels)
            n_ao = len(self.ao_channels)

            C_mat = np.array(self.C) if self.C is not None else np.eye(n_ai)
            n_outputs = C_mat.shape[0]
            D_mat = np.array(self.D) if self.D is not None else np.zeros((n_outputs, n_ao))

            if self.use_reference and self.x_ref is not None and self.u_eq is not None:
                x_ref_mat = np.array(self.x_ref, ndmin=2)
                u_eq_mat = np.array(self.u_eq, ndmin=2)

                traj_x = (x_ref_mat.shape[1] == n_ai and x_ref_mat.shape[0] > 1)
                traj_u = (u_eq_mat.shape[1] == n_ao and u_eq_mat.shape[0] > 1)
            else:
                x_ref_mat = np.zeros((1, n_ai))
                u_eq_mat = np.zeros((1, n_ao))
                traj_x = False
                traj_u = False
                
            st_worker = time.perf_counter()
            for k in range(self.cycles):
                if not self.acquisition_running:
                    break

                # Multichannel Read
                y_raw = task_ai.read()
                y_list = y_raw if n_ai > 1 else [y_raw]
                x = np.array(y_list).reshape(-1, 1)

                if traj_x:
                    idx_x = min(k, x_ref_mat.shape[0] - 1)
                    x_ref_vec = x_ref_mat[idx_x, :].reshape(n_ai, 1)
                else:
                    x_ref_vec = x_ref_mat.reshape(n_ai, 1)

                if traj_u:
                    idx_u = min(k, u_eq_mat.shape[0] - 1)
                    u_eq_vec = u_eq_mat[idx_u, :].reshape(n_ao, 1)
                else:
                    u_eq_vec = u_eq_mat.reshape(n_ao, 1)

                # LQR Control Law
                e = x - x_ref_vec                    # State Error
                u = -self.K @ e + u_eq_vec           # Control Effort
                
                y = C_mat @ x + D_mat @ u

                u_out = [np.clip(float(u[i]), 0, 5) for i in range(n_ao)]
                task_ao.write(u_out if n_ao > 1 else u_out[0])

                time_now = time.perf_counter() - st_worker
                
                # Package data
                x_dict = {ch: float(x[i][0]) for i, ch in enumerate(self.channels)}
                e_dict = {ch: float(e[i][0]) for i, ch in enumerate(self.channels)}
                u_dict = {ch: u_out[i] for i, ch in enumerate(self.ao_channels)}
                y_dict = {f"y{i+1}": float(y[i][0]) for i in range(n_outputs)}
                data_queue.put((time_now, x_dict, e_dict, u_dict, y_dict))

                num_cycles_performed += 1
                wait_time = (st_worker + (k + 1) * self.ts) - time.perf_counter()
                if wait_time > 0:
                    time.sleep(wait_time)
                else:
                    warnings.warn("[PYDAQ] Time spent to update interface was greater than ts.")
        
        finally:
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
            if st_worker is not None:
                total_duration = time.perf_counter() - st_worker
                if num_cycles_performed > 0:
                    avg = total_duration / num_cycles_performed
                    print(f"\n[PYDAQ] Thread finished. Total time: {total_duration:.5f}s | Cycles: {num_cycles_performed} | Avg: {avg:.5f}s")       
                else:
                    print("\n[PYDAQ] Thread finished. No data cycles acquired.")
            else:
                print("\n[PYDAQ] Thread finished before acquisition started.")

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
        
        # --- NEW: Unified time list and state/input/output dictionaries ---
        n_outputs = np.array(self.C).shape[0] if self.C is not None else len(self.channels)
        self.time_var = []
        self.state_h = {ch: [] for ch in self.channels}
        self.error_h = {ch: [] for ch in self.channels} # <- ADD THIS
        self.input_h = {ch: [] for ch in self.ao_channels}
        self.output_h = {f"y{i+1}": [] for i in range(n_outputs)}

        data_queue = queue.Queue()
        self.acquisition_running = True
        self.plot_closed_by_user = False
        self.plot_ready_event.clear()

        self._check_path()

        print ("\n[PYDAQ] Running LQR Control ...")
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

            time.sleep(0.5)

            self.plot_ready_event.set()
        else:
            self.plot_ready_event.set() # Allow acquisition to start immediately

        # Plot update throttling logic for performance
        plot_update_interval = max(self.ts * 0.9, 0.05)

        last_plot_update_time = time.perf_counter()

        # Main loop for data consumption and plotting
        while (self.acquisition_running and not self.plot_closed_by_user) or not data_queue.empty():
            try:
                item = data_queue.get(timeout=0.01)

                if item is None:
                    self.acquisition_running = False
                    while not data_queue.empty():
                        remaining_item = data_queue.get_nowait()
                        if remaining_item is not None:
                            # 5 elements to unpack now
                            t, x_dict, e_dict, u_dict, y_dict = remaining_item
                            self.time_var.append(t)
                            for ch_key, val in x_dict.items(): self.state_h[ch_key].append(val)
                            for ch_key, val in e_dict.items(): self.error_h[ch_key].append(val)
                            for ch_key, val in u_dict.items(): self.input_h[ch_key].append(val)
                            for ch_key, val in y_dict.items(): self.output_h[ch_key].append(val)
                    break

                # 5 elements to unpack now
                t, x_dict, e_dict, u_dict, y_dict = item
                self.time_var.append(t)
                for ch_key, val in x_dict.items(): self.state_h[ch_key].append(val)
                for ch_key, val in e_dict.items(): self.error_h[ch_key].append(val)
                for ch_key, val in u_dict.items(): self.input_h[ch_key].append(val)
                for ch_key, val in y_dict.items(): self.output_h[ch_key].append(val)

                # Throttle plot updates for performance
                now = time.perf_counter()

                if self.plot_mode == 'realtime' and (
                    now - last_plot_update_time >= plot_update_interval
                    or not self.acquisition_running
                ):
                    self._update_plot_lqr(
                        time_values=self.time_var,
                        y_values=self.output_h,
                        x_state_values=self.state_h,
                        e_values=self.error_h,   
                        u_values=self.input_h
                    )
                    last_plot_update_time = now

            except queue.Empty:
                # This keeps the loop responsive
                time.sleep(0.01)
                if not self.acquisition_running and data_queue.empty():
                    break

        acquisition_thread.join()

        if self.plot_mode == 'end' and self.time_var:
            self.title = f"PYDAQ - Final Step Response (NIDAQ)"
            self._start_updatable_plot_lqr(title_str=self.title)
            self._update_plot_lqr(
                time_values=self.time_var,
                y_values=self.output_h,
                x_state_values=self.state_h,
                e_values=self.error_h,  
                u_values=self.input_h
            )
            plt.show(block=True)

        if self.save:
            print("\n[PYDAQ] Saving data ...")
            self._save_data(self.time_var, "time.dat")
            self._save_data(self.state_h, "states.dat")
            self._save_data(self.input_h, "control.dat")
            self._save_data(self.output_h, "output.dat")
            print("\n[PYDAQ] Data saved ...")

        if self.plot_mode == 'realtime' and not self.plot_closed_by_user:
            print("\n[PYDAQ] Plot remains open. Close window manually to exit.")
            plt.show(block=True)

        return

    def simulate_lqr(self):
        """Executes a pure mathematical simulation of the discrete LQR."""
        if self.A is None or self.B is None or self.Q is None or self.R is None:
            warnings.warn("[PYDAQ] Matrices are not defined: Cannot simulate.")
            return

        self._calculate_lqr_gain()
        A_mat = np.array(self.A)
        B_mat = np.array(self.B)
        n_states = A_mat.shape[0]
        n_inputs = B_mat.shape[1]

        C_mat = np.array(self.C) if self.C is not None else np.eye(n_states)
        n_outputs = C_mat.shape[0]
        D_mat = np.array(self.D) if self.D is not None else np.zeros((n_outputs, n_inputs))

        if self.use_reference and self.x_ref is not None and self.u_eq is not None:
            x_ref_mat = np.array(self.x_ref, ndmin=2)
            u_eq_mat = np.array(self.u_eq, ndmin=2)
            traj_x = (x_ref_mat.shape[1] == n_states and x_ref_mat.shape[0] > 1)
            traj_u = (u_eq_mat.shape[1] == n_inputs and u_eq_mat.shape[0] > 1)
        else:
            x_ref_mat = np.zeros((1, n_states))
            u_eq_mat = np.zeros((1, n_inputs))
            traj_x = False
            traj_u = False

        x = np.zeros((n_states, 1))
        steps = int(np.floor(self.session_duration / self.ts)) + 1

        history_y = []
        history_u = []
        history_x = []
        history_e = [] 
        time_arr = []

        print("\n[PYDAQ] Running LQR Control Simulation ...")
        for k in range(steps):
            if traj_x:
                idx_x = min(k, x_ref_mat.shape[0] - 1)
                x_ref_vec = x_ref_mat[idx_x, :].reshape(n_states, 1)
            else:
                x_ref_vec = x_ref_mat.reshape(n_states, 1)

            if traj_u:
                idx_u = min(k, u_eq_mat.shape[0] - 1)
                u_eq_vec = u_eq_mat[idx_u, :].reshape(n_inputs, 1)
            else:
                u_eq_vec = u_eq_mat.reshape(n_inputs, 1)

            # Control law
            e = x - x_ref_vec
            u = -self.K @ e + u_eq_vec

            if self.output_mode == "arduino_pwm":
                u = np.clip(u, 0, 5)

            y = C_mat @ x + D_mat @ u

            # Store data
            history_y.append(y.flatten())
            history_u.append(u.flatten())
            history_x.append(x.flatten())
            history_e.append(e.flatten()) 
            time_arr.append(k * self.ts)

            x = A_mat @ x + B_mat @ u

        # --- PLOTTING LOGIC ---
        history_y = np.array(history_y)
        history_u = np.array(history_u)
        history_x = np.array(history_x)
        history_e = np.array(history_e)

        # Filter active plots
        active_plots = [key for key, is_active in self.plot_prefs.items() if is_active]
        n_axes = len(active_plots)

        if n_axes > 0:
            fig, axes = plt.subplots(n_axes, 1, figsize=(9, 2.5 * n_axes), sharex=True)
            fig.suptitle("LQR Simulation", fontsize=14)
            
            if n_axes == 1:
                axes = [axes]
                
            ax_map = {key: ax for key, ax in zip(active_plots, axes)}

            if 'y' in ax_map:
                for i in range(history_y.shape[1]):
                    ax_map['y'].plot(time_arr, history_y[:, i], marker='o', linestyle='-', markersize=3, label=f"Output y{i+1}", linewidth=2)
                ax_map['y'].set_ylabel("Outputs (y)")
                ax_map['y'].grid(True)
                ax_map['y'].legend(loc="upper right")

            if 'x' in ax_map:
                for i in range(history_x.shape[1]):
                    ax_map['x'].plot(time_arr, history_x[:, i],  marker='o', linestyle='-', markersize=3, label=f"State x{i+1}", linewidth=2)
                ax_map['x'].set_ylabel("States (x)")
                ax_map['x'].grid(True)
                ax_map['x'].legend(loc="upper right")

            if 'e' in ax_map:
                for i in range(history_e.shape[1]):
                    ax_map['e'].plot(time_arr, history_e[:, i],  marker='o', linestyle='-', markersize=3, label=f"Error e{i+1}", linewidth=2)
                ax_map['e'].set_ylabel("State Error (e)")
                ax_map['e'].grid(True)
                ax_map['e'].legend(loc="upper right")

            if 'u' in ax_map:
                for i in range(history_u.shape[1]):
                    ax_map['u'].step(time_arr, history_u[:, i], where='post', marker='o', linestyle='-', markersize=3, label=f"Control Effort u{i+1}", linewidth=2)
                
                ax_map['u'].set_ylabel("Control Effort (u) [V]")
                ax_map['u'].grid(True)
                ax_map['u'].legend(loc="upper right")

                # --- NEW: Conditional PWM Axis for Simulation ---
                if self.output_mode == "arduino_pwm":
                    ax_u_pwm = ax_map['u'].twinx()
                    ax_u_pwm.set_ylabel("PWM Duty Cycle")
                    y_min, y_max = ax_map['u'].get_ylim()
                    ax_u_pwm.set_ylim(y_min * 51.0, y_max * 51.0)

            axes[-1].set_xlabel("Time (s)")
            plt.tight_layout()
            plt.show(block=True)

        if self.save:
            self._check_path()
            print("\n[PYDAQ] Saving data ...")
            
            state_dict = {f"x{i+1}": history_x[:, i].tolist() for i in range(n_states)}
            error_dict = {f"e{i+1}": history_e[:, i].tolist() for i in range(n_states)} 
            input_dict = {f"u{i+1}": history_u[:, i].tolist() for i in range(n_inputs)}
            output_dict = {f"y{i+1}": history_y[:, i].tolist() for i in range(n_outputs)}

            self._save_data(time_arr, "time.dat")
            self._save_data(state_dict, "states.dat")
            self._save_data(error_dict, "error.dat") 
            self._save_data(input_dict, "control.dat")
            self._save_data(output_dict, "output.dat")
            print("\n[PYDAQ] Data saved ...")

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
            self._dim_error(f"[PYDAQ] Matrix A must be {n_states}x{n_states} to match AI channels!")
            return False

        # Check matrix B: rows must match AI channels, cols must match AO channels
        if B.ndim != 2 or B.shape[0] != n_states or B.shape[1] != n_inputs:
            self._dim_error(f"[PYDAQ] Matrix B must be {n_states}x{n_inputs} to match AI and AO channels!")
            return False

        print(A.ndim, A.shape)
        print(B.ndim, B.shape)

        return True