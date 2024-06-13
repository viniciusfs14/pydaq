import os
import sys
import time
import warnings
import PySimpleGUI as sg
import matplotlib.pyplot as plt
import nidaqmx
from nidaqmx.constants import TerminalConfiguration
import numpy as np
import serial
import serial.tools.list_ports
from pydaq.utils.base import Base



class Get_data(Base):
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

    def __init__(self,
                 device="Dev1",
                 channel="ai0",
                 terminal='Diff',
                 com='COM1',
                 ts=0.5,
                 session_duration=10.0,
                 save=True,
                 plot=True
                 ):

        super().__init__()
        self.device = device
        self.channel = channel
        self.ts = ts
        self.session_duration = session_duration
        self.save = save
        self.plot = plot

        # Terminal configuration
        self.terminal = self.term_map[terminal]

        # Initializing variables
        self.data = []
        self.time_var = []

        # Gathering nidaq info
        self._nidaq_info()

        # Error flags
        self.error_path = False

        # COM ports
        self.com_ports = [
            i.description for i in serial.tools.list_ports.comports()]
        self.com_port = com  # Default COM port

        # Plot title
        self.title = None

        # Plot legend
        self.legend = ['Input']

        # Defining default path
        self.path = os.path.join(
            os.path.join(
                os.path.expanduser('~')),
            'Desktop')

        # Arduino ADC resolution (in bits)
        self.arduino_ai_bits = 10

        # Arduino analog input max and min
        self.ard_ai_max, self.ard_ai_min = 5, 0

        # Value per bit - Arduino
        self.ard_vpb = (self.ard_ai_max - self.ard_ai_min) / \
            (2**self.arduino_ai_bits)

    def get_data_nidaq(self):
        """
            This function can be used for data acquisition and step response experiments using Python + NIDAQ boards.

        :example:
            get_data_nidaq()
        """

        # Cleaning data array
        self.data = []
        self.time_var = []

        # Checking if path was defined
        self._check_path()

        # Number of self.cycles necessary
        self.cycles = int(np.floor(self.session_duration / self.ts)) + 1

        # Initializing device, with channel defined
        task = nidaqmx.Task()
        task.ai_channels.add_ai_voltage_chan(
            self.device + '/' + self.channel,
            terminal_config=self.terminal)

        if self.plot:  # If plot, start updatable plot
            self.title = f'PYDAQ - Data Acquisition. {self.device}, {self.channel}'
            self._start_updatable_plot()

        # Main loop, where data will be acquired
        for k in range(self.cycles):

            # Counting time to append data and update interface
            st = time.time()

            # Acquire data
            temp = task.read()

            # Queue data in a list
            self.data.append(temp)
            self.time_var.append(k * self.ts)

            if self.plot:

                # Checking if there is still an open figure. If not, stop the
                # for loop.
                try:
                    plt.get_figlabels().index('iter_plot')
                except BaseException:
                    break

                # Updating data values
                self._update_plot(self.time_var, self.data)

            print(f'Iteration: {k} of {self.cycles-1}')

            # Getting end time
            et = time.time()

            # Wait for (ts - delta_time) seconds
            try:
                time.sleep(self.ts + (st - et))
            except BaseException:
                warnings.warn(
                    "Time spent to append data and update interface was greater than ts. "
                    "You CANNOT trust time.dat")

        # Closing task
        task.close()

        # Check if data will or not be saved, and save accordingly
        if self.save:
            print('\nSaving data ...')
            # Saving time_var and data
            self._save_data(self.time_var, 'time.dat')
            self._save_data(self.data, 'data.dat')
            print('\nData saved ...')

        return

    def get_data_nidaq_gui(self):
        """
        This functions provides a Graphical User Interface (GUI) that allows one to get data
        from National Instruments acquisition boards.

        :example:
            get_data_nidaq_gui()

        """

        # Theme
        sg.theme('Dark')

        # First the window layout in 2 columns
        first_column = [
            [sg.Text('Choose device: ')],
            [sg.Text('Choose channel: ')],
            [sg.Text('Terminal Config.')],
            [sg.Text("Sample period (s)")],
            [sg.Text("Session duration (s)")],
            [sg.Text('Plot data?')],
            [sg.Text('Save data?')],
            [sg.Text("Path")],
        ]

        try:
            chan = nidaqmx.system.device.Device(
                self.device_names[0]).ai_physical_chans.channel_names
            defchan = chan[0]
        except BaseException:
            chan = ''
            defchan = ''

        # Second column
        second_column = [
            [sg.DD(self.device_type, size=(40, 1), enable_events=True, default_value=self.device_type[0],
                   key="-DDDev-")],
            [sg.DD(chan, enable_events=True, size=(40, 1), default_value=defchan,
                   key="-DDChan-")],
            [sg.DD(['Diff', 'RSE', 'NRSE'], enable_events=True, size=(40, 1), default_value=['Diff'],
                   key="-Terminal-")],
            [sg.I(self.ts, enable_events=True, key='-TS-', size=(40, 1))],
            [sg.I(self.session_duration, enable_events=True, key='-SD-', size=(40, 1))],
            [sg.Radio("Yes", "plot_radio", default=True, key='-Plot-'), sg.Radio("No", "plot_radio", default=False)],
            [sg.Radio("Yes", "save_radio", default=True, key='-Save-'), sg.Radio("No", "save_radio", default=False)],
            [sg.In(size=(32, 1), enable_events=True, key="-Path-",
                   default_text=os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')),
             sg.FolderBrowse()],
        ]

        bottom_line = [
            [sg.Button('GET DATA', key='-Start-', auto_size_button=True)]
        ]

        # ----- Full layout -----
        layout = [
            [sg.Column(first_column, vertical_alignment='top'),
             sg.VSeparator(),
             sg.Column(second_column, vertical_alignment='center')],
            [sg.HSeparator()],
            [sg.Column(bottom_line, vertical_alignment='center')]
        ]

        window = sg.Window(
            "PYDAQ - Data Acquisition (NIDAQ)",
            layout,
            resizable=False,
            finalize=True,
            element_justification="center",
            font="Helvetica")

        # Event Loop
        while True:

            event, values = window.read()

            if event == sg.WIN_CLOSED:
                break

            # Start
            if event == '-Start-':

                try:
                    # Separating variables
                    self.terminal = self.term_map[values['-Terminal-']]
                    self.ts = float(values['-TS-'])
                    self.session_duration = float(values['-SD-'])
                    self.device = values['-DDChan-'].split('/')[0]
                    self.channel = values['-DDChan-'].split('/')[1]
                    self.save = values['-Save-']
                    self.path = values['-Path-']
                    self.plot = values['-Plot-']

                    # Restarting variables
                    self.data = []
                    self.time_var = []
                    self.error_path = False

                except BaseException:
                    self._error_window()
                    self.error_path = True

                # Calling data aquisition method
                if not self.error_path:
                    self.get_data_nidaq()

            # Changing availables channels if device changes
            if event == "-DDDev-":
                # Discovering new ai channels
                new_ai_channels = nidaqmx.system.device.Device(
                    self.device_names[self.device_type.index(values['-DDDev-'])]).ai_physical_chans.channel_names
                # Default channel
                try:
                    default_channel = new_ai_channels[0]
                except BaseException:
                    default_channel = 'There is no analog input in this board'

                # Rewriting new ai channels into the right place
                window['-DDChan-'].update(default_channel, new_ai_channels)

        window.close()

        return

    def get_data_arduino(self):
        """
            This function can be used for data acquisition and step response experiments using Python + Arduino
            through serial communication

        :example:
            get_data_arduino()
        """

        # Cleaning data array
        self.data = []
        self.time_var = []

        # Check if path was defined
        self._check_path()

        # Number of self.cycles necessary
        self.cycles = int(np.floor(self.session_duration / self.ts)) + 1

        # Oppening ports
        self._open_serial()

        if self.plot:  # If plot, start updatable plot
            self.title = f'PYDAQ - Data Acquisition. Arduino, Port: {self.com_port}'
            self._start_updatable_plot()


        time.sleep(2)  # Wait for Arduino and Serial to start up

        # Main loop, where data will be acquired
        for k in range(self.cycles):

            # Counting time to append data and update interface
            st = time.time()

            # Acquire data
            self.ser.reset_input_buffer()  # Reseting serial input buffer
            # Get the last complete value
            temp = int(self.ser.read(14).split()
                       [-2].decode('UTF-8')) * self.ard_vpb

            # Queue data in a list
            self.data.append(temp)
            self.time_var.append(k * self.ts)

            if self.plot:

                # Checking if there is still an open figure. If not, stop the
                # for loop.
                try:
                    plt.get_figlabels().index('iter_plot')
                except BaseException:
                    break

                # Updating data values
                self._update_plot(self.time_var, self.data)

            print(f'Iteration: {k} of {self.cycles-1}')

            # Getting end time
            et = time.time()

            # Wait for (ts - delta_time) seconds
            try:
                time.sleep(self.ts + (st - et))
            except BaseException:
                warnings.warn(
                    "Time spent to append data and update interface was greater than ts. "
                    "You CANNOT trust time.dat")

        # Closing port
        self.ser.close()

        # Check if data will or not be saved, and save accordingly
        if self.save:
            print('\nSaving data ...')
            # Saving time_var and data
            self._save_data(self.time_var, 'time.dat')
            self._save_data(self.data, 'data.dat')
            print('\nData saved ...')
        return

    def get_data_arduino_gui(self):
        """
        This functions provides a Graphical User Interface (GUI) that allows one to get data
        from Arduino boards.

        :example:
            get_data_arduino_gui()

        """

        # Theme
        sg.theme('Dark')

        # First the window layout in 2 columns
        first_column = [
            [sg.Text('Choose your arduino: ')],
            [sg.Text("Sample period (s)")],
            [sg.Text("Session duration (s)")],
            [sg.Text('Plot data?')],
            [sg.Text('Save data?')],
            [sg.Text("Path")],
        ]

        # Second column
        second_column = [
            [sg.DD(self.com_ports, size=(40, 1), enable_events=True, default_value=self.com_ports[-1], key="-COM-")],
            [sg.I(self.ts, enable_events=True, key='-TS-', size=(40, 1))],
            [sg.I(self.session_duration, enable_events=True, key='-SD-', size=(40, 1))],
            [sg.Radio("Yes", "plot_radio", default=True, key='-Plot-'), sg.Radio("No", "plot_radio", default=False)],
            [sg.Radio("Yes", "save_radio", default=True, key='-Save-'), sg.Radio("No", "save_radio", default=False)],
            [sg.In(size=(32, 1), enable_events=True, key="-Path-",
                   default_text=os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')),
             sg.FolderBrowse()],
        ]

        bottom_line = [
            [sg.Button('GET DATA', key='-Start-', auto_size_button=True)]
        ]

        # ----- Full layout -----
        layout = [
            [sg.Column(first_column, vertical_alignment='top'),
             sg.VSeparator(),
             sg.Column(second_column, vertical_alignment='center')],
            [sg.HSeparator()],
            [sg.Column(bottom_line, vertical_alignment='center')]
        ]

        window = sg.Window(
            "PYDAQ - Data Acquisition (ARDUINO)",
            layout,
            resizable=False,
            finalize=True,
            element_justification="center",
            font="Helvetica")

        # Event Loop
        while True:

            event, values = window.read()

            if event == sg.WIN_CLOSED:
                break

            # Start
            if event == '-Start-':

                try:
                    # Separating variables
                    self.ts = float(values['-TS-'])
                    self.session_duration = float(values['-SD-'])
                    self.com_port = serial.tools.list_ports.comports(
                    )[self.com_ports.index(values['-COM-'])].name
                    self.save = values['-Save-']
                    self.path = values['-Path-']
                    self.plot = values['-Plot-']

                    # Restarting variables
                    self.data = []
                    self.time_var = []
                    self.error_path = False

                except BaseException:
                    self._error_window()
                    self.error_path = True

                # Calling data aquisition method
                if not self.error_path:
                    self.get_data_arduino()

            if event == '-COM-':  # Updating com ports

                self.com_ports = [
                    i.description for i in serial.tools.list_ports.comports()]
                port = values['-COM-']
                window['-COM-'].update(port, self.com_ports)

        window.close()
        return
    
