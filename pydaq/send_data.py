import os
import time
import warnings
import threading
import queue

import matplotlib.pyplot as plt
import nidaqmx
import numpy as np
import serial
import serial.tools.list_ports
from pydaq.utils.base import Base

class SendData(Base):
    """
    Class able to send data from data acquisition boards using (or not) a graphical user interface (GUI)

    :author: Samir Angelo Milani Martins
         - https://www.samirmartins.com.br
         - https://www.github.com/samirmartins/

    :params:
        data: data array (list or np.array) that will be sent to the board
        device: nidaq device from where data will be colected. Example: "Dev1"
        channel: channel from where data will be acquired. Example: ao0
        com: arduino COM port. Example: 'COM1'
        ts: sample period, in seconds.
        ao_min: minimum allowed analog output value
        ao_max: maximum allowed analog output value
        plot: if True, plot data iteractively as they are acquired
    """

    def __init__(
        self,
        data=None,
        device="Dev1",
        channels=None,
        com="COM1",
        ts=0.5,
        ao_min=0,
        ao_max=5,
        plot_mode="no", # Options: "realtime", "end", "no"
    ):

        super().__init__()
        self.device = device
        # Handling channels (default to single channel if not list)
        # Ensure channels is a list
        if channels is None:
            self.channels = ["ao0"] # Default
        elif isinstance(channels, str) or isinstance(channels, int):
            self.channels = [channels]
        else:
            self.channels = channels
        self.ts = ts
        self.plot_mode = plot_mode
        self.ao_min = ao_min
        self.ao_max = ao_max
        self.com_port = com

        # Processing input data
        if data is not None:
            self.data = np.asarray(data)
            n_channels = len(self.channels)
            
            # If we have multiple channels but data is 1D, we assume the user wants
            # to send the SAME signal to all channels (Broadcasting)
            if n_channels > 1 and self.data.ndim == 1:
                # Reshape to (Samples, Channels) by repeating columns
                self.data = np.tile(self.data[:, np.newaxis], (1, n_channels))
            
            # If data is already 2D, we assume it is (Samples, Channels).
            # If the shape doesn't match, we warn but proceed (might crash later if mismatch)
            if self.data.ndim == 2 and self.data.shape[1] != n_channels:
                warnings.warn(f"Data columns ({self.data.shape[1]}) do not match number of channels ({n_channels}). Check input.")

        else:
            self.data = np.array([])

        # Gathering nidaq info
        self._nidaq_info()

        # Data storage for plotting/saving (Dictionary based, like get_data)
        self.time_var = {ch: [] for ch in self.channels}
        self.sent_data_history = {ch: [] for ch in self.channels} 

        # Defining default path
        self.path = os.path.join(
            os.path.join(os.path.expanduser("~")), "Desktop", "data.dat"
        )

        # Plot title and legend
        self.title = None

        # Threading control
        self.sending_running = False
        self.plot_closed_by_user = False
        self.plot_ready_event = threading.Event()

    # Handler for plot window closure
    def _on_plot_close(self, event):
        """
        Event handler for Matplotlib figure closure.
        Sets sending_running to False and plot_closed_by_user to True.
        """
        print("Plot window closed by user. Halting data sending...")
        self.sending_running = False
        self.plot_closed_by_user = True

    def _send_data_worker_nidaq(self, progress_queue):
        self.plot_ready_event.wait() # Wait for plot to be ready

        try:
            task = nidaqmx.Task()   # cria primeiro
            
            channel_str = ",".join([f"{self.device}/{ch}" for ch in self.channels])

            task.ao_channels.add_ao_voltage_chan(
                channel_str,
                min_val=float(self.ao_min),
                max_val=float(self.ao_max),
            )

            # Number of samples (rows in data)
            n_channels = len(self.channels)
            cycles = self.data.shape[0] # Number of samples (rows)
            
            st_worker = time.perf_counter()

            for k in range(cycles):
                if not self.sending_running:
                    break

                # Get current sample(s) for this step
                if n_channels == 1:
                    # If 1D array or (N, 1) matrix
                    if self.data.ndim == 1:
                        current_val = self.data[k]
                    else:
                        current_val = self.data[k][0]
                    
                    # Write single value
                    task.write(current_val)
                    val_to_queue = [current_val] # List for consistency in queue
                else:
                    # Multi-channel write (expects list or array of values for that sample)
                    current_vals = self.data[k].tolist()
                    task.write(current_vals)
                    val_to_queue = current_vals

                time_now = time.perf_counter() - st_worker
                
                # Put progress on the queue: (timestamp, [val_ch0, val_ch1...])
                progress_queue.put((time_now, val_to_queue))

                wait_time = (st_worker + (k + 1) * self.ts) - time.perf_counter()
                if wait_time > 0:
                    time.sleep(wait_time)
        finally:
            try:
                if len(self.channels) == 1:
                    task.write(0)
                else:
                    task.write([0] * len(self.channels))
            except:
                pass
            task.close()
            progress_queue.put(None) # Signal end of sending

    def send_data_nidaq(self):
        """
            This function can be used to send experimental data  using Python + NIDAQ boards.

        :example:
            send_data_nidaq()
        """

        if self.data is None:
            warnings.warn("You must define data to be sent.")
            return

        self.data = np.array(self.data)

        # Initialize storage dicts
        self.time_var = {ch: [] for ch in self.channels}
        self.sent_data_history = {ch: [] for ch in self.channels}

        progress_queue = queue.Queue()
        self.sending_running = True
        self.plot_closed_by_user = False
        self.plot_ready_event.clear()

        sending_thread = threading.Thread(
            target=self._send_data_worker_nidaq,
            args=(progress_queue,),
            daemon=True
        )
        sending_thread.start()

        # Plot Setup
        if self.plot_mode == 'realtime':
            self.title = f"PYDAQ - Sending Data. {self.device}, Channels: {self.channels}"
            self._start_updatable_plot(title_str=self.title)
            self.fig.canvas.mpl_connect('close_event', self._on_plot_close)
            time.sleep(0.5)
            self.plot_ready_event.set()
        else:
            self.plot_ready_event.set()

        # Plot Update Rate
        if self.ts >= 0.05:
            plot_update_interval = 0.05
        else:
            plot_update_interval = 0.25
        last_plot_time = time.perf_counter()

        # Main loop to consume progress and update plot
        while (self.sending_running and not self.plot_closed_by_user) or not progress_queue.empty():
            try:
                item = progress_queue.get(timeout=0.01)

                if item is None:
                    self.sending_running = False
                    # Drain the queue to ensure all data is processed
                    while not progress_queue.empty():
                        remaining = progress_queue.get_nowait()
                        if remaining:
                            t_stamp, vals = remaining
                            for i, ch in enumerate(self.channels):
                                self.time_var[ch].append(t_stamp)
                                self.sent_data_history[ch].append(vals[i])
                    break

                timestamp, values = item
                # Append data for each channel
                for i, ch in enumerate(self.channels):
                    self.time_var[ch].append(timestamp)
                    self.sent_data_history[ch].append(values[i])

                now = time.perf_counter()
                # Improved plot condition to ensure the final frame is drawn
                if self.plot_mode == 'realtime' and (now - last_plot_time >= plot_update_interval or not self.sending_running):
                    # Plot using the dictionaries, matching get_data style
                    self._update_plot(self.time_var, self.sent_data_history)
                    last_plot_time = now
            
            except queue.Empty:
                time.sleep(0.01)
                if not self.sending_running and progress_queue.empty():
                    break

        sending_thread.join()

        # Plotting at the end logic remains the same
        if self.plot_mode == 'end' and any(self.time_var.values()):
            self.title = f"PYDAQ - Final Sent Data (NIDAQ)"
            self._start_updatable_plot(title_str=self.title)
            self._update_plot(self.time_var, self.sent_data_history)
            plt.show(block=True)
            
        if self.plot_mode == 'realtime' and not self.plot_closed_by_user:
            print("\nPlot remains open. Close window manually to exit.")
            plt.show(block=True)

        return

    def _send_data_worker_arduino(self, progress_queue):
        """
        Worker thread for Arduino data transmission.
        Supports sending digital signals (on/off) or formatted strings.
        """
        self.plot_ready_event.wait()
        
        n_channels = len(self.channels)
        cycles = self.data.shape[0]
        
        # This logic is specific to sending digital signals based on a voltage threshold
        #data_to_send = [b"1" if i > 2.5 else b"0" for i in self.data]

        try:
            self._open_serial()
            time.sleep(0.5) # Wait for serial to settle
            
            st_worker = time.perf_counter()

            for k in range(cycles):
                if not self.sending_running:
                    break
                
                # Logic to get values for this step
                if n_channels == 1:
                     if self.data.ndim == 1:
                        val = self.data[k]
                     else:
                        val = self.data[k][0]
                     
                     current_vals = [val]
                else:
                    current_vals = self.data[k].tolist()

                # Digital logic: High/Low based on 2.5V threshold
                digital_vals = [1 if x > 2.5 else 0 for x in current_vals]

                if n_channels > 1:
                    # Create CSV string: "1,0,1\n"
                    msg = ",".join(map(str, digital_vals)) + "\n"
                    self.ser.write(msg.encode())
                else:
                    # Single channel legacy mode (send byte '0' or '1')
                    if digital_vals[0] == 1:
                        self.ser.write(b'1') 
                    else:
                        self.ser.write(b'0')
                
                time_now = time.perf_counter() - st_worker

                plot_vals = [5 if x == 1 else 0 for x in digital_vals]
                progress_queue.put((time_now, plot_vals))

                wait_time = (st_worker + (k + 1) * self.ts) - time.perf_counter()
                if wait_time > 0:
                    time.sleep(wait_time)
        
        except serial.SerialException as e:
            warnings.warn(f"Failed to open or use serial port {self.com_port}: {e}")
        finally:
            if hasattr(self, 'ser') and self.ser.is_open:
                # Try to reset to 0
                try:
                    if n_channels > 1:
                        self.ser.write((",".join(["0"]*n_channels) + "\n").encode())
                    else:
                        self.ser.write(b'0')
                except:
                    pass
                self.ser.close()
            progress_queue.put(None)

    def send_data_arduino(self):
        """
            This function can be used to send experimental data  using Python +
            Arduino boards (digital output only). If "High", the value should be greather
            than 2.5. Else, "Low"

        :example:
            send_data_arduino()
        """
        if self.data is None:
            warnings.warn("You must define data to be sent.")
            return
        
        self.data = np.array(self.data)

        # Initialize storage dicts
        self.time_var = {ch: [] for ch in self.channels}
        self.sent_data_history = {ch: [] for ch in self.channels}

        progress_queue = queue.Queue()
        self.sending_running = True
        self.plot_closed_by_user = False
        self.plot_ready_event.clear()

        sending_thread = threading.Thread(
            target=self._send_data_worker_arduino,
            args=(progress_queue,),
            daemon=True
        )
        sending_thread.start()

        if self.plot_mode == 'realtime':
            self.title = f"PYDAQ - Sending Data. Arduino, Port: {self.com_port}"
            self._start_updatable_plot(title_str=self.title)
            self.fig.canvas.mpl_connect('close_event', self._on_plot_close)
            time.sleep(0.5)
            self.plot_ready_event.set()
        else:
            self.plot_ready_event.set()

        # Control variables for periodic plot update
        if self.ts >= 0.05:
            plot_update_interval = 0.05
        else:
            plot_update_interval = 0.25

        last_plot_time = time.perf_counter()

        # Main loop to consume progress and update plot
        while (self.sending_running and not self.plot_closed_by_user) or not progress_queue.empty():
            try:
                item = progress_queue.get(timeout=0.01)

                if item is None:
                    self.sending_running = False
                    # Flush
                    while not progress_queue.empty():
                        remaining = progress_queue.get_nowait()
                        if remaining:
                            t_stamp, vals = remaining
                            for i, ch in enumerate(self.channels):
                                self.time_var[ch].append(t_stamp)
                                self.sent_data_history[ch].append(vals[i])
                    break
                
                timestamp, vals = item
                for i, ch in enumerate(self.channels):
                    self.time_var[ch].append(timestamp)
                    self.sent_data_history[ch].append(vals[i])

                now = time.perf_counter()
                if self.plot_mode == 'realtime' and (now - last_plot_time >= plot_update_interval or not self.sending_running):
                    self._update_plot(self.time_var, self.sent_data_history)
                    last_plot_time = now
            
            except queue.Empty:
                time.sleep(0.01)
                if not self.sending_running and progress_queue.empty():
                    break

        sending_thread.join()

        if self.plot_mode == 'end' and any(self.time_var.values()):
            self.title = f"PYDAQ - Final Sent Data (Arduino)"
            self._start_updatable_plot(title_str=self.title)
            self._update_plot(self.time_var, self.sent_data_history)
            plt.show(block=True)
        
        if self.plot_mode == 'realtime' and not self.plot_closed_by_user:
            print("\nPlot remains open. Close window manually to exit.")
            plt.show(block=True)
            
        return