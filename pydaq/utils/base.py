import os
import matplotlib as mpl
import matplotlib.pyplot as plt
import serial
import serial.tools.list_ports
import warnings
from ..guis.error_window_gui import Error_window

try:
    import nidaqmx
    from nidaqmx.constants import TerminalConfiguration
    from nidaqmx.system import System
    nidaqmx.system.System.local() 
    
    NIDAQ_AVAILABLE = True
except (ImportError, OSError, Exception):
    nidaqmx = None
    System = None
    NIDAQ_AVAILABLE = False
    class TerminalConfiguration:
        DIFF = "Diff"
        RSE = "RSE"
        NRSE = "NRSE"

class Base:
    """
    Base class for data acquisition and to send data.
    """

    def __init__(self):

        # Terminal configuration Map
        self.term_map = {
            "Diff": TerminalConfiguration.DIFF,
            "RSE": TerminalConfiguration.RSE,
            "NRSE": TerminalConfiguration.NRSE,
        }

        # Initialize plot related attributes
        self.fig = None
        self.ax = None
        self.line = None
        self.line2 = None
        
    def _range_error(self):
        """Out of range window"""

        error_w = Error_window()
        error_w.ui.confirm.setText("Out of range value (check step_max and ao_min)!")
        error_w.exec()

    def _check_path(self):
        """Method to check if path was or not defined by the user"""

        # Checking if path was or not defined by the user
        if self.path is None:  # Saving in Desktop if it is not defined
            self.path = os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")

        # Check if able to save data in defined path
        if not os.path.exists(self.path):
            warnings.warn(
                "[PYDAQ] Defined path does not exist! Please redefine the path and run the code again."
            )
            return

    def _open_serial(self):
        """Opening ports for serial communication"""

        self.ser = serial.Serial()
        self.ser.dtr = True
        self.ser.baudrate = 115200
        self.ser.port = self.com_port  # Defining port

        if not self.ser.isOpen():  # Open port if not openned
            self.ser.open()  # Opening port

    def _start_updatable_plot(self, title_str="Data Acquisition"): # Removed has_filter_line as _update_plot handles it
        """
        Method to start an updatable plot.
        Initializes matplotlib figure and axes. Lines are drawn by _update_plot.
        """
        # Changing Matplotlib backend if necessary
        # This can sometimes cause issues if called multiple times or with different backends
        # It's often best to set this once at the very beginning of the script if possible.
        # mpl.use("Qt5Agg") 

        # create the figure and axes objects
        self.fig, self.ax = plt.subplots()
        self.fig._label = "iter_plot"  # Defining label

        # Iteractive plot on
        plt.ion()

        # Title and labels and plot creation
        self.ax.set_title(title_str) # Use passed title
        self.ax.set_xlabel("Time (s)") # Adjusted label for general use
        self.ax.set_ylabel("Amplitude") # Adjusted label for general use
        self.ax.grid(True)
        
        # Show non-blocking
        plt.show(block=False)

    def _update_plot(self, x_values, y1_values, y2_values=None, y1_label="Original Data", y2_label="Filtered Data", channel_names=None, y2_channel_names=None):
        """
        Method to update plot by clearing and redrawing all points up to current moment.

        Supports:
        - Single channel:
            x_values: list
            y1_values: list
            y2_values: list or None

        - Multi channel:
            x_values: dict[channel] -> list
            y1_values: dict[channel] -> list
            y2_values: dict[channel] -> list (optional)
            channel_names: list of strings with custom names for y1 legend (optional)
            y2_channel_names: list of strings with custom names for y2 legend (optional)
        """

        if self.fig is None or self.ax is None:
            warnings.warn("Plot not initialized. Call _start_updatable_plot first.")
            return

        self.ax.clear() # Clear all artists from the axes

        # Set title, labels, and grid again after clearing (matplotlib quirk)
        self.ax.set_title(self.title if hasattr(self, 'title') and self.title else "Data Acquisition")
        self.ax.set_xlabel("Time (s)") # Ensure labels are set again after clear
        self.ax.set_ylabel("Amplitude") # Ensure labels are set again after clear
        self.ax.grid(True)

        # ==========================
        # MULTI-CHANNEL MODE
        # ==========================
        if isinstance(x_values, dict):

            keys = list(x_values.keys())
            # Map for y1 (Output / Sensors)
            if isinstance(channel_names, list):
                ch_map_y1 = {keys[i]: channel_names[i] for i in range(min(len(keys), len(channel_names)))}
            else:
                ch_map_y1 = {}

            # Map for y2 (Input / Actuators)
            if isinstance(y2_channel_names, list):
                ch_map_y2 = {keys[i]: y2_channel_names[i] for i in range(min(len(keys), len(y2_channel_names)))}
            else:
                ch_map_y2 = ch_map_y1 # Fallback to y1 names if y2 names are not provided

            for idx, ch in enumerate(x_values.keys()):
                if len(x_values[ch]) == 0:
                    continue
                
                # Determine display name
                disp_y1 = ch_map_y1.get(ch, str(ch))
                disp_y2 = ch_map_y2.get(ch, str(ch))

                # --- FIRST CHANNEL: legacy colors ---
                if idx == 0:
                    raw_color = "blue"
                    filt_color = "red"

                # --- OTHER CHANNELS: matplotlib default cycle ---
                else:
                    raw_color = None   # None → matplotlib escolhe
                    filt_color = None

                self.ax.plot(
                    x_values[ch],
                    y1_values[ch],
                    marker='o',
                    linestyle='-',
                    color=raw_color,
                    label=f"{y1_label} - ({disp_y1})"  # modified: now uses generic label
                )

                if y2_values is not None and ch in y2_values and len(y2_values[ch]) > 0:
                    self.ax.plot(
                        x_values[ch],
                        y2_values[ch],
                        marker='o',
                        linestyle='-',
                        color=filt_color,
                        label=f"{y2_label} - ({disp_y2})"  # modified: now uses generic label
                        )

        # ==========================
        # SINGLE-CHANNEL MODE (LEGACY)
        # ==========================

        else:

            # Plot original data (always)
            # Using marker='o' and linestyle='-' separately for 'o-' style
            self.ax.plot(x_values, y1_values, color="blue", marker='o', linestyle='-', label=y1_label)
            
            # Plot filtered data if provided
            if y2_values is not None:
                self.ax.plot(x_values, y2_values, color="red", marker='o', linestyle='-', label=y2_label)
            
        self.ax.relim() # Recalculate limits
        self.ax.autoscale_view() # Autoscale axes

        self.ax.legend() # Update legend to reflect current plots

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def _save_data(self, data, name):
        """
        Method to save data in self.path with name.
        Handles multi-channel dicts (saves as matrices) and lists (saves as 1D arrays).
        Outputs a space-separated .dat file containing only numerical values.
        """
        try:
            os.makedirs(self.path, exist_ok=True)
            full_path = os.path.join(self.path, name)
            
            with open(full_path, "w") as file:
                # Handle dictionaries (Matrices: multiple columns separated by space)
                if isinstance(data, dict):
                    channels = list(data.keys())
                    if not channels:
                        return
                    
                    ref_ch = channels[0]
                    n_samples = len(data[ref_ch])
                    
                    for i in range(n_samples):
                        row_vals = []
                        for ch in channels:
                            val = data[ch][i] if i < len(data[ch]) else 0.0
                            row_vals.append(f"{val:.6f}")
                        file.write(" ".join(row_vals) + "\n")
                        
                # Handle lists (1D Arrays: single column)
                elif isinstance(data, list):
                    for d in data:
                        file.write(str(d) + "\n")

        except OSError as e:
            warnings.warn(f"Error saving data to {full_path}: {e}")

    def _nidaq_info(self):
        """Gathering NIDAQ info"""

        # Getting all available devices
        self.device_names = []
        self.device_categories = []
        self.device_type = []

        if not NIDAQ_AVAILABLE:
            return # Exit gracefully if drivers are missing
        
        self.local_system = nidaqmx.system.System.local()
        
        for device in self.local_system.devices:
            self.device_names.append(device.name)
            self.device_categories.append(device.product_category)
            self.device_type.append(device.product_type)

    def adjust_string(label_string):
        spaced_string = " ".join(label_string.split("_"))
        return spaced_string.capitalize()

    def get_acronym(string):
        if string == "R2 score":
            return "R2S"
        else:
            oupt = string[0]

            for i in range(1, len(string)):
                if string[i - 1] == " ":
                    oupt += string[i]
            return oupt.upper()

    def _start_updatable_plot_lqr(self, title_str="PYDAQ - LQR Control"):
        """
        Initializes a matplotlib figure with 2 subplots (vertically stacked)
        specifically for LQR/Control visualization.
        ax1: System Response (y)
        ax2: Control Effort (u)
        """
        plt.ion()
        # sharex=True guarantees synchronized zooming across all 3 plots
        self.fig, (self.ax_y, self.ax_x, self.ax_u) = plt.subplots(3, 1, figsize=(9, 9), sharex=True)
        
        self.title = title_str
        self.fig.suptitle(self.title, fontsize=14)

        self.ax_y.set_ylabel("Outputs (y)")
        self.ax_y.grid(True)

        self.ax_x.set_ylabel("States (x)")
        self.ax_x.grid(True)

        self.ax_u.set_xlabel("Time (s)")
        self.ax_u.set_ylabel("Control Effort (u)")
        self.ax_u.grid(True)

        self.fig.tight_layout()
        plt.show(block=False)

    def _update_plot_lqr(self, time_values, y_values, x_state_values, u_values):
        """
        Updates the LQR 3-axis subplots.
        ax_y plots time vs y_values (Outputs)
        ax_x plots time vs x_state_values (States)
        ax_u plots time vs u_values (Control Effort)
        """
        if self.fig is None or not hasattr(self, 'ax_y'):
            warnings.warn("LQR Plot not initialized. Call _start_updatable_plot_lqr first.")
            return

        # Clear all axes
        self.ax_y.clear()
        self.ax_x.clear()
        self.ax_u.clear()

        # Re-apply styling (clearing removes grid and labels)
        self.ax_y.set_ylabel("Outputs (y)")
        self.ax_y.grid(True)
        self.ax_x.set_ylabel("States (x)")
        self.ax_x.grid(True)
        self.ax_u.set_xlabel("Time (s)")
        self.ax_u.set_ylabel("Control Effort (u)")
        self.ax_u.grid(True)

        # Plot Outputs (y)
        for i, ch_key in enumerate(y_values.keys()):
            if len(y_values[ch_key]) > 0:
                color = plt.cm.tab10(i % 10) 
                self.ax_y.plot(
                    time_values, y_values[ch_key],
                    marker='o', linestyle='-', color=color, markersize=3,
                    label=f"Output ({ch_key})"
                )

        # Plot States (x)
        for i, ch_key in enumerate(x_state_values.keys()):
            if len(x_state_values[ch_key]) > 0:
                color = plt.cm.tab10(i % 10) 
                self.ax_x.plot(
                    time_values, x_state_values[ch_key],
                    marker='o', linestyle='-', color=color, markersize=3,
                    label=f"State ({ch_key})"
                )

        # Plot Control Effort (u) using step for discrete representation
        for i, ch_key in enumerate(u_values.keys()):
            if len(u_values[ch_key]) > 0:
                color = plt.cm.tab10(i % 10) 
                # Use .step instead of .plot
                self.ax_u.step(
                    time_values, u_values[ch_key],
                    where='post',  # Holds the value after the time step
                    marker='o', linestyle='-',
                    color=color, 
                    markersize=3,
                    linewidth=2,
                    label=f"Input/PWM ({ch_key})"
                )

        # Autoscale and Legend
        for ax in [self.ax_y, self.ax_x, self.ax_u]:
            ax.relim()
            ax.autoscale_view()
            ax.legend(loc="upper right", fontsize='small')

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def _verify_arduino_firmware(self):
        """
        Reads samples from the Serial port to confirm that the PyDAQ firmware is running.
        Reads up to 3 lines to avoid failing on partial data streams.
        Returns True if correct, or False if incorrect.
        """
        try:
            self.ser.reset_input_buffer() # Clear old junk
            
            # Save the original timeout and set a quick one
            original_timeout = self.ser.timeout
            self.ser.timeout = 0.5 # 0.5s is more than enough for a continuous stream

            try:
                # Try reading up to 3 lines to catch at least one complete frame
                for _ in range(3):
                    # Use errors='ignore' to prevent crashes with random serial noise
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    if not line:
                        continue # If empty, try the next loop iteration

                    parts = line.split(',')

                    # Check for the exact 6-channel structure defined in the .ino
                    if len(parts) == 6: 
                        int(parts[0]) # Will raise ValueError if it's not a number
                        return True   # Perfect frame found!

                # If the loop finishes and didn't find a 6-part line
                return False

            finally:
                # This block ALWAYS runs, guaranteeing the timeout is restored
                self.ser.timeout = original_timeout 

        except Exception:
            return False

    # NEW: Added method to trigger the dimension error window
    def _dim_error(self, message="Dimension mismatch error!"):
        """Generic dimension error window"""

        error_w = Error_window()
        error_w.ui.confirm.setText(message)
        error_w.exec()

    def _check_nidaq_availability(self):
        """Checks if NIDAQ drivers are installed and loaded."""
        if not NIDAQ_AVAILABLE:
            error_w = Error_window()
            error_w.ui.confirm.setText("[PYDAQ] NI-DAQmx drivers not found! Please install NI-MAX.")
            error_w.exec()
            return False
        return True
    