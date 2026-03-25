import os
import matplotlib as mpl
import matplotlib.pyplot as plt
import serial
import serial.tools.list_ports
import nidaqmx
from nidaqmx.constants import TerminalConfiguration
import warnings
from ..guis.error_window_gui import Error_window


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
                "Defined path does not exists! Please redefine path and run the code again"
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
        """Method to save data in self.path with name"""

        try:

            os.makedirs(self.path, exist_ok=True)

            # Safely join the path components for cross-platform compatibility
            full_path = os.path.join(self.path, name)
            
            with open(full_path, "w") as file:
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
        # sharex=True faz com que o zoom no eixo do tempo seja igual para os dois gráficos
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
        
        self.title = title_str
        self.fig.suptitle(self.title, fontsize=14)

        self.ax1.set_ylabel("Amplitude (Output)")
        self.ax1.grid(True)

        self.ax2.set_xlabel("Time (s)")
        self.ax2.set_ylabel("Amplitude (Input)")
        self.ax2.grid(True)

        self.fig.tight_layout()
        plt.show(block=False)

    def _update_plot_lqr(self, x_values, y_values, u_values, y_label="System Response", u_label="Control Effort", y_channel_names=None, u_channel_names=None):
        """
        Updates the LQR subplots.
        ax1 plots x_values vs y_values (Output)
        ax2 plots x_values vs u_values (Input/Control Effort)
        """
        if self.fig is None or not hasattr(self, 'ax1') or not hasattr(self, 'ax2'):
            warnings.warn("LQR Plot not initialized. Call _start_updatable_plot_lqr first.")
            return

        # Limpa ambos os eixos
        self.ax1.clear()
        self.ax2.clear()

        # Configura novamente (pois o clear() apaga as configurações)
        self.ax1.set_ylabel("Amplitude (Output)")
        self.ax1.grid(True)
        self.ax2.set_xlabel("Time (s)")
        self.ax2.set_ylabel("Amplitude (Input)")
        self.ax2.grid(True)

        if isinstance(x_values, dict):
            keys = list(x_values.keys())

            # Mapeamento para as legendas
            ch_map_y = {keys[i]: y_channel_names[i] for i in range(min(len(keys), len(y_channel_names)))} if isinstance(y_channel_names, list) else {}
            ch_map_u = {keys[i]: u_channel_names[i] for i in range(min(len(keys), len(u_channel_names)))} if isinstance(u_channel_names, list) else ch_map_y

            for idx, ch in enumerate(keys):
                if len(x_values[ch]) == 0:
                    continue

                disp_y = ch_map_y.get(ch, str(ch))
                disp_u = ch_map_u.get(ch, str(ch))

                # Garante que a mesma cor seja usada no gráfico de cima e de baixo para o mesmo canal
                color = plt.cm.tab10(idx % 10) 

                # Gráfico Superior: System Response (y)
                self.ax1.plot(
                    x_values[ch], y_values[ch],
                    marker='o', linestyle='-', color=color,
                    label=f"{y_label} ({disp_y})"
                )

                # Gráfico Inferior: Control Effort (u)
                if u_values is not None and ch in u_values and len(u_values[ch]) > 0:
                    self.ax2.plot(
                        x_values[ch], u_values[ch],
                        marker='o', linestyle='-', color=color,
                        label=f"{u_label} ({disp_u})"
                    )

        self.ax1.relim()
        self.ax1.autoscale_view()
        self.ax1.legend(loc="upper right")

        self.ax2.relim()
        self.ax2.autoscale_view()
        self.ax2.legend(loc="upper right")

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()