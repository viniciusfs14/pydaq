import os
import time
import numpy as np

import serial
import serial.tools.list_ports
from pydaq.utils.base import Base, NIDAQ_AVAILABLE, TerminalConfiguration, nidaqmx

import threading
import queue

import os
import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
import warnings
from scipy.signal import savgol_filter


class StepResponse(Base):
    """
     Class developed to construct Graphical User Interface for step
     response using arduino and NIDAQ boards

    :author: Samir Angelo Milani Martins
          - https://www.samirmartins.com.br
          - https://www.github.com/samirmartins/

     :params:
         device: nidaq default device.
         ao_channel: nidaq default analog output channel
         ai_channel: nidaq default analog input channel
         ts: sample period, in seconds.
         session_duration: session duration, in seconds.
         step_time: time when step will be applied, in seconds
         step_min: minimum step  value
         step_max: maximum step value
         terminal: 'Diff', 'RSE' or 'NRSE': terminal configuration (differential, referenced single ended or non-referenced single ended)
         plot: if True, plot data iteractively as they are sent/acquired


    """

    def __init__(
        self,
        device="Dev1",
        ao_channel="ao0",
        ai_channel="ai0",
        ts=0.5,
        session_duration=10.0,
        step_time=3.0,
        step_min=0,
        step_max=5,
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
        self.step_min = step_min
        self.step_max = step_max
        self.save = save

        # Terminal configuration
        self.terminal = self.term_map[terminal]

        # COM ports
        self.com_ports = [i.description for i in serial.tools.list_ports.comports()]
        self.com_port = com

        # Initializing variables
        self.time_var, self.input, self.output = [], [], []

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

        self.calculate_pid = False  # Flag to enable calculation
        self.sintony_type = 0  # Tuning type: 'P', 'PI', or 'PID'
        self.pid_parameters = []    # To store the results [Kp, Ki, Kd]

        # Threading control flags and events
        self.acquisition_running = False
        self.plot_closed_by_user = False
        self.plot_ready_event = threading.Event()

        self.channels = [ai_channel]        # default single channel
        self.ao_channels = [ao_channel]     # default single channel

    # Handler for plot window closure
    def _on_plot_close(self, event):
        """..."""
        print("\n[PYDAQ] Plot window closed by user. Initiating shutdown...")
        self.acquisition_running = False
        self.plot_closed_by_user = True

    def _step_response_worker_arduino(self, data_queue):

        channels = self.channels  # === NEW ===
        n_channels = len(channels)  # === NEW ===
        self.plot_ready_event.wait()
        num_cycles_performed = 0  # === NEW ===
        st_worker = None 
        try:
            self._open_serial()
            if not self._verify_arduino_firmware():
                self.ser.close()
                warnings.warn("[PYDAQ] PyDAQ Firmware not detected on this board! Please go to the top menu and click on 'Arduino - Firmware' to upload the correct code.")

                return
            # --- WARM-UP SECTION ---
            # Send an initial command (b"0") to "wake up" the Arduino.
            self.ser.write(b"0")
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

                # Update step value
                if k * self.ts >= float(self.step_time):
                    digital_val = 1
                else:
                    digital_val = 0

                # === MODIFIED: multi-channel digital send ===
                msg_parts = []
                for ch in self.ao_channels:
                    pin_num = ch.replace("D", "")
                    msg_parts.append(f"{pin_num}:{digital_val}")
                
                msg = ",".join(msg_parts) + "\n"
                self.ser.write(msg.encode())
                
                try:
                    self.ser.reset_input_buffer()
                    self.ser.readline()
                    
                    raw = self.ser.readline()
                    values = list(map(int, raw.decode("utf-8").strip().split(",")))

                    if len(values) < 6:
                        warnings.warn("[PYDAQ] Data parsing error: Incomplete universal frame received. Please ensure the correct PyDAQ firmware is running.")
                        continue

                    time_now = time.perf_counter() - st_worker

                    # === NEW: distribute per channel like get_data ===
                    for ch in channels:
                        idx = int(ch.replace("A", ""))
                        value = values[idx] * self.ard_vpb
                        data_queue.put((time_now, ch, digital_val * 5.0, value))

                    num_cycles_performed += 1

                except (ValueError, UnicodeDecodeError):
                    warnings.warn(f"[PYDAQ] Data parsing error: Invalid multichannel read from Arduino: {raw}")
                    continue

                wait_time = (st_worker + num_cycles_performed * self.ts) - time.perf_counter()
                if wait_time > 0:
                    time.sleep(wait_time)
                else:
                    warnings.warn("[PYDAQ] Time spent to append data and update interface was greater than ts. You CANNOT trust time.dat")

        except serial.SerialException as e:
            warnings.warn(f"[PYDAQ] Hardware error: Failed to open serial port {self.com_port}. Details: {e}")
        finally:
            if hasattr(self, 'ser') and self.ser.is_open:
                try:
                    if n_channels > 1:
                        self.ser.write((",".join(["0"] * n_channels) + "\n").encode())
                    else:
                        self.ser.write(b"0")
                except:
                    pass
                self.ser.close()
            data_queue.put(None)
            # PROTECTION: Only calculates the time if the acquisition has actually started.
            if st_worker is not None:
                total_acquisition_duration = time.perf_counter() - st_worker
                if num_cycles_performed > 0:
                    avg = total_acquisition_duration / num_cycles_performed
                    print(
                        f"\n[PYDAQ] Thread finished. "
                        f"Total time: {total_acquisition_duration:.5f}s | "
                        f"Cycles processed: {num_cycles_performed} | "
                        f"Avg per cycle: {avg:.5f}s"
                    )       
                else:
                    print("\n[PYDAQ] Thread finished. No data cycles acquired.")
            else:
                print("\n[PYDAQ] Thread finished before acquisition started (Configuration blocked).")  
    
    def step_response_arduino(self):
        """
        This method performs the step response using an Arduino board for given parameters.

        :example:
            step_response_arduino()

        """

        #if hasattr(self, "channels") and self.channels:
        #    self.channels = self.channels  # use selected input channels

        #if hasattr(self, "ao_channels") and self.ao_channels:
        #    self.ao_channels = self.ao_channels  # use selected output channels

        # --- Start of placeholder implementation ---
        
        self.time_var = {ch: [] for ch in self.channels}
        self.input = {ch: [] for ch in self.channels}
        self.output = {ch: [] for ch in self.channels}

        data_queue = queue.Queue()
        self.acquisition_running = True
        self.plot_closed_by_user = False
        self.plot_ready_event.clear()

        self._check_path()
        self.cycles = int(np.floor(self.session_duration / self.ts)) + 1

        print ("\n[PYDAQ] Running Step Response...")
        acquisition_thread = threading.Thread(
            target=self._step_response_worker_arduino,
            args=(data_queue,),
            daemon=True
        )
        acquisition_thread.start()

        if self.plot_mode == 'realtime':
            self.title = f"PYDAQ - Step Response (Arduino), Port: {self.com_port}"
            self._start_updatable_plot(title_str=self.title)
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
                            timestamp, channel, input_val, output_val = remaining_item
                            self.time_var[channel].append(timestamp)
                            self.input[channel].append(input_val)
                            self.output[channel].append(output_val)
                    break

                timestamp, channel, input_val, output_val = item

                self.time_var[channel].append(timestamp)
                self.input[channel].append(input_val)
                self.output[channel].append(output_val)

                # Throttle plot updates for performance
                now = time.perf_counter()

                if self.plot_mode == 'realtime' and (now - last_plot_update_time >= plot_update_interval or not self.acquisition_running):
                    self._update_plot(
                        self.time_var,
                        self.output,
                        y2_values=self.input,
                        y1_label="Output",
                        y2_label="Input",
                        channel_names=self.channels,        # Ex: ["A0", "A1"]
                        y2_channel_names=self.ao_channels   # Ex: ["D8", "D9"]
                    )
                    last_plot_update_time = now

            except queue.Empty:
                # This keeps the loop responsive
                time.sleep(0.01)
                if not self.acquisition_running and data_queue.empty():
                    break

        acquisition_thread.join()

        if self.calculate_pid:

            # === NEW: dict to store pid per channel ===
            self.pid_parameters = {}

            ch = self.channels[0]  # default to first channel for error messages if needed

            for ch in self.channels:   # === NEW: loop per channel ===

                if len(self.time_var[ch]) < 3:
                    continue  # safety

                channel_name=ch  

                Kp, Ki, Kd, tangent_plot = self.get_parameters(
                    self.time_var[ch][0:-1],     # === MODIFIED ===
                    self.output[ch][1:],         # === MODIFIED ===
                    self.step_time,
                    self.sintony_type,
                    self.ard_ao_min,
                    self.ard_ao_max,
                    channel_name     # === NEW: pass channel name for better error messages ===
                )

                # === NEW: store per channel ===
                self.pid_parameters[ch] = [Kp, Ki, Kd]

                if self.plot_mode != 'no':

                    # === NEW: plot per channel ===
                    plt.figure(figsize=(10, 6))

                    plt.plot(
                        self.time_var[ch][0:-1],
                        self.output[ch][1:],
                        label=f"System Output - {ch}",
                        linewidth=2
                    )

                    plt.plot(
                        self.time_var[ch][0:-1],
                        self.input[ch][0:-1],
                        label=f"Step Input - {ch}",
                        linewidth=2
                    )

                    plt.plot(
                        self.time_var[ch][0:-1],
                        tangent_plot,
                        '--',
                        label=f"Tangent Line - {ch}",
                        linewidth=2
                    )

                    plt.title(f"Ziegler-Nichols Tuning - Channel {ch}", fontsize=16)
                    plt.xlabel("Time (s)", fontsize=14)
                    plt.ylabel("Amplitude", fontsize=14)
                    plt.legend()
                    plt.grid(True)
                    plt.show(block=False)

        if self.plot_mode == 'end' and self.time_var:
            self.title = f"PYDAQ - Final Step Response: Arduino, Port: {self.com_port}"
            self._start_updatable_plot(title_str=self.title)
            self._update_plot(
                self.time_var,
                self.output,
                y2_values=self.input,
                y1_label="Output",
                y2_label="Input",
                channel_names=self.channels,        # Ex: ["A0", "A1"]
                y2_channel_names=self.ao_channels   # Ex: ["D8", "D9"]
            )
            plt.show(block=True)

        if self.save:
            print("\n[PYDAQ] Saving data ...")
            self._save_data(self.time_var, "time.dat")
            self._save_data(self.input, "input.dat")
            self._save_data(self.output, "output.dat")
            print("\n[PYDAQ] Data saved ...")

        if self.plot_mode == 'realtime' and not self.plot_closed_by_user:
            print("\n[PYDAQ] Plot remains open. Close window manually to exit.")
            plt.show(block=True)

        return

    def _step_response_worker_nidaq(self, data_queue):

        # Wait for plot to be ready to synchronize start time
        self.plot_ready_event.wait()
        st_worker = None
        
        task_ao = nidaqmx.Task()
        task_ai = nidaqmx.Task()
    
        try:
            num_cycles_performed = 0
            
            # === NEW: Multi-channel string construction ===
            ao_channel_str = ",".join([f"{self.device}/{ch}" for ch in self.ao_channels])
            ai_channel_str = ",".join([f"{self.device}/{ch}" for ch in self.channels])

            # Configure AO
            task_ao.ao_channels.add_ao_voltage_chan(
                ao_channel_str,
                min_val=float(self.step_min),
                max_val=float(self.step_max),
            )

            # Configure AI
            task_ai.ai_channels.add_ai_voltage_chan(
                ai_channel_str,
                terminal_config=self.terminal
            )
            
            n_channels = len(self.channels)

            st_worker = time.perf_counter()
            for k in range(self.cycles):
                if not self.acquisition_running:
                    break

                # Update step value
                if k * self.ts >= float(self.step_time):
                    sent_val = self.step_max
                else:
                    sent_val = self.step_min
                
                # === NEW: multi-channel AO write ===
                if n_channels == 1:
                    task_ao.write(sent_val)
                    input_vals = [sent_val]
                else:
                    input_vals = [sent_val] * n_channels
                    task_ao.write(input_vals)

                # Read AI
                temp = task_ai.read()

                if n_channels == 1:
                    temp = [temp]

                time_now = time.perf_counter() - st_worker

                num_cycles_performed += 1
                # === NEW: queue per channel ===
                for i, ch in enumerate(self.channels):
                    data_queue.put((time_now, ch, input_vals[i], temp[i]))

                wait_time = (st_worker + (k + 1) * self.ts) - time.perf_counter()
                if wait_time > 0:
                    time.sleep(wait_time)
                else:
                    warnings.warn("[PYDAQ] Time spent to append data and update interface was greater than ts. You CANNOT trust time.dat")
        
        finally:
            # Turn off outputs
            try:
                if n_channels == 1:
                    task_ao.write(0)
                else:
                    task_ao.write([0] * n_channels)
            except:
                pass

            task_ao.close()
            task_ai.close()
            data_queue.put(None)
            if st_worker is not None:
                total_acquisition_duration = time.perf_counter() - st_worker
                if num_cycles_performed > 0:
                    avg = total_acquisition_duration / num_cycles_performed
                    print(
                        f"\n[PYDAQ] Thread finished. "
                        f"Total time: {total_acquisition_duration:.5f}s | "
                        f"Cycles processed: {num_cycles_performed} | "
                        f"Avg per cycle: {avg:.5f}s"
                    )       
                else:
                    print("\n[PYDAQ] Thread finished. No data cycles acquired.")
            else:
                print("\n[PYDAQ]Thread finished before acquisition started (Configuration blocked).") 


    def step_response_nidaq(self):
        """
        This method performs the step response using a NIDAQ board for given parameters.

        :example:
            step_response_nidaq()

        """

        # --- NIDAQ SAFETY LOCK ---
        if not self._check_nidaq_availability():
            return
        
        self.time_var = {ch: [] for ch in self.channels}
        self.input = {ch: [] for ch in self.channels}
        self.output = {ch: [] for ch in self.channels}

        data_queue = queue.Queue()
        self.acquisition_running = True
        self.plot_closed_by_user = False
        self.plot_ready_event.clear()

        self._check_path()
        self.cycles = int(np.floor(self.session_duration / self.ts)) + 1

        print ("\n[PYDAQ] Running Step Response...")
        acquisition_thread = threading.Thread(
            target=self._step_response_worker_nidaq,
            args=(data_queue,),
            daemon=True
        )
        acquisition_thread.start()

        if self.plot_mode == 'realtime':
            self.title = f"PYDAQ - Step Response (NIDAQ). {self.device}, Channels: {self.channels}"
            self._start_updatable_plot(title_str=self.title)
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

                    # Drain the queue to ensure all data is processed
                    while not data_queue.empty():
                        remaining_item = data_queue.get_nowait()
                        if remaining_item is not None:
                            timestamp, channel, input_val, output_val = remaining_item
                            self.time_var[channel].append(timestamp)
                            self.input[channel].append(input_val)
                            self.output[channel].append(output_val)
                    break

                timestamp, channel, input_val, output_val = item

                self.time_var[channel].append(timestamp)
                self.input[channel].append(input_val)
                self.output[channel].append(output_val)

                # Throttle plot updates for performance
                now = time.perf_counter()

                if self.plot_mode == 'realtime' and (
                    now - last_plot_update_time >= plot_update_interval
                    or not self.acquisition_running
                ):
                    self._update_plot(
                        self.time_var,
                        self.output,
                        y2_values=self.input,
                        y1_label="Output",
                        y2_label="Input",
                        channel_names=self.channels,        # Ex: ["A0", "A1"]
                        y2_channel_names=self.ao_channels   # Ex: ["D8", "D9"]
                    )
                    last_plot_update_time = now

            except queue.Empty:
                # This keeps the loop responsive
                time.sleep(0.01)
                if not self.acquisition_running and data_queue.empty():
                    break

        acquisition_thread.join()

        if self.calculate_pid:

            self.pid_parameters = {}  # === NEW ===

            for ch in self.channels:  # === NEW ===

                if len(self.time_var[ch]) < 3:
                    continue

                channel_name  = ch  # === NEW: for better error messages ===

                Kp, Ki, Kd, tangent_plot = self.get_parameters(
                    self.time_var[ch][0:-1],
                    self.output[ch][1:],
                    self.step_time,
                    self.sintony_type,
                    self.step_min,
                    self.step_max,
                    channel_name              # === NEW: pass channel name for better error messages ===
                )

                self.pid_parameters[ch] = [Kp, Ki, Kd]

                if self.plot_mode != 'no':

                    plt.figure(figsize=(10, 6))
                    plt.plot(self.time_var[ch][0:-1], self.output[ch][1:], label=f"Output - {ch}", linewidth=2)
                    plt.plot(self.time_var[ch][0:-1], self.input[ch][0:-1], label=f"Input - {ch}", linewidth=2)
                    plt.plot(self.time_var[ch][0:-1], tangent_plot, '--', label="Tangent", linewidth=2)

                    plt.title(f"Ziegler-Nichols Tuning - {ch}", fontsize=16)
                    plt.xlabel("Time (s)", fontsize=14)
                    plt.ylabel("Amplitude", fontsize=14)
                    plt.legend()
                    plt.grid(True)
                    plt.show(block=False)

        if self.plot_mode == 'end' and any(self.time_var.values()):
            self.title = f"PYDAQ - Final Step Response (NIDAQ)"
            self._start_updatable_plot(title_str=self.title)
            self._update_plot(
                self.time_var,
                self.output,
                y2_values=self.input,
                y1_label="Output",
                y2_label="Input",
                channel_names=self.channels,        # Ex: ["A0", "A1"]
                y2_channel_names=self.ao_channels   # Ex: ["D8", "D9"]
            )
            plt.show(block=True)

        if self.save:
            print("\n[PYDAQ] Saving data ...")
            self._save_data(self.time_var, "time.dat")
            self._save_data(self.input, "input.dat")
            self._save_data(self.output, "output.dat")
            print("\n[PYDAQ] Data saved ...")

        if self.plot_mode == 'realtime' and not self.plot_closed_by_user:
            print("\n[PYDAQ] Plot remains open. Close window manually to exit.")
            plt.show(block=True)

        return

    def get_parameters(self, time, system_value, step_time, type_sintony, min_val, max_val, channel_name):

        time = np.array(time)
        system_value = np.array(system_value)

        n = len(system_value)

        # Subtract baseline (minimum value) from the system response
        mask_after_step = time >= step_time

        if np.any(mask_after_step):
            baseline = np.min(system_value[mask_after_step])
        else:
            baseline = np.min(system_value)  # Use the minimum value of the entire signal
        system_value_normalized = system_value - baseline

        # Calculate the process gain K
        delta_input = max_val - min_val
        if delta_input == 0:
            # Avoid division by zero if step is zero
            k = np.inf
        else:
            k = (system_value_normalized[-1] - system_value_normalized[0]) / delta_input

        if n >= 5:
            # escolher janela ímpar permitida
            window_size = min(7, n if n % 2 == 1 else n - 1)
            max_derivative_idx, derivative = self.get_max_derivative_idx(
                time, system_value_normalized, step_time, window_size
            )
        else:
            # derivada simples
            derivative = np.gradient(system_value_normalized, time)
            valid = time >= step_time
            if not np.any(valid):
                max_derivative_idx = 0
            else:
                max_local = np.argmax(derivative[valid])
                max_derivative_idx = np.where(valid)[0][0] + max_local

        time_inflection = time[max_derivative_idx]
        sys_inflection = system_value_normalized[max_derivative_idx]

        # Fit tangent line at the inflection point
        slope = derivative[max_derivative_idx]
        intercept = sys_inflection - slope * time_inflection
        tangent_line = slope * time + intercept

        # Convert normalized tangent back to real scale
        tangent_line_real = tangent_line + baseline

        # Find L (delay) and T (time constant)
        # L is the time until the tangent crosses the y=0 axis
        L = -intercept / slope
        # T is the time the tangent takes to go from y=0 to y=K
        T = k / slope

        # L adjusted by the step time
        L_adjusted = L - step_time
        
        type_sintony_code = type_sintony
        if type_sintony_code == 0:  # P
            Kp = T / L_adjusted
            Ki = 0
            Kd = 0
        elif type_sintony_code == 1: # PI
            Kp = 0.9 * (T / L_adjusted)
            Ti = L_adjusted / 0.3
            Ki = Kp / Ti
            Kd = 0
        else: # PID
            Kp = 1.2 * (T / L_adjusted)
            Ti = 2 * L_adjusted
            Ki = Kp / Ti
            Td = 0.5 * L_adjusted
            Kd = Kp * Td

        if L_adjusted <= 0 or T <= 0 or Kp <= 0 or Ki < 0 or Kd < 0 or n < 3 or slope <= 0:
            print(f"\n[PYDAQ] Invalid sample values for channel {channel_name}. Sintony cannot be calculated correctly.")
            return 0, 0, 0, tangent_line_real  # Retorna PID=0
        
        print(f"\n[PYDAQ] Gains: Kp={Kp:.4f}, Ki={Ki:.4f}, Kd={Kd:.4f}")
        
        return Kp, Ki, Kd, tangent_line_real

    def get_max_derivative_idx(self, time, system_value, step_time, window_size=7, polyorder=2):
        window_size = int(window_size)

        # Make sure window size is odd and at least 3
        if window_size % 2 == 0:
            window_size -= 1
        if window_size < 3:
            window_size = 3

        system_value_smooth = savgol_filter(system_value, window_size, polyorder)
        derivative = np.gradient(system_value_smooth, time)
        
        valid_indices = time >= step_time
        derivative_valid = derivative[valid_indices]
        
        if len(derivative_valid) == 0:
            return 0, derivative

        max_derivative_local_idx = np.argmax(derivative_valid)
        max_derivative_idx = np.where(valid_indices)[0][max_derivative_local_idx]
                
        return max_derivative_idx, derivative