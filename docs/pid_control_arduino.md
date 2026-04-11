# PID Control with Arduino

**NOTE 1**: Before working with PYDAQ, the device driver should be installed and working correctly as a DAQ (Data Acquisition) device.

**NOTE 2** To acquire/send data with an Arduino board, the unified firmware provided here (located
at [arduino_code](https://github.com/samirmartins/pydaq/tree/main/pydaq/arduino_code)) must be uploaded to the Arduino first. Starting from v0.0.7, this single firmware supports multi-channel acquisition (A0 to A5) and sending (D0 to D13) simultaneously via serial CSV communication. There is no need to modify the .ino code to change ports; channel selection is now handled entirely within your Python script or GUI.

**NOTE 3**: PYDAQ is programmed to use 10 bits as ADC resolution and 0V to 5V as the input range.  
To change this, the user can alter the following variables:

```python
self.arduino_ai_bits = 10
self.ard_ai_max = 5
self.ard_ai_min = 0
```

## Controlling using Graphical User Interface (GUI)

Using the GUI to perform PID control is very straightforward and requires only two lines of code:

```python
from pydaq.pydaq_global import PydaqGui

PydaqGui()
```

After running the command, the GUI will appear. Navigate to the "PID Control" screen, where you can define the parameters and start the control session.

![](img/pid_control_arduino_gui.png)

## Parameters

- **Simulate**: If this option is selected, you can enter a mathematical equation to simulate a system and apply PID control to it.

- **Device**: Select the Arduino board connected to your system.

- **Setpoint**: Define the desired reference value for the system.

- **Unit** *(optional)*: Define the unit of measurement for the setpoint (e.g., °C, rpm, volts).

- **Equation** *(optional)*: Define a mathematical transformation for the measured input, if needed.

- **Sampling Period (s)**: Time interval (in seconds) between each data sample.

- **Controller Type**: Choose among P, PI, PD, or PID controllers and configure their respective tuning parameters.

- **Save Data**: Choose whether to save the recorded data during the session.

- **Path**: Define where the data files will be saved.

## Simulated System

If you enable the **Simulate** option, the software will not require a physical device. Instead, you can input the transfer function or system equation, and PYDAQ will simulate its response using the defined controller parameters.

This is useful for testing your control strategy before applying it to a real system.

## Real-Time Control

After adjusting the parameters and starting the control, a new window will open to display the real-time control process. Within this window, you can also modify the PID parameters (**kp**, **ki**, **kd**) and the **setpoint** during execution.

A disturbance input can also be simulated during real-time control. It acts as a negative signal added after the control signal, as illustrated in the figure below.

## Example GIF

![](img/pidcontrol_arduino_gif.gif)

# Control PID with Arduino (GUI via code)

It is possible to access the PID Control GUI directly with a few lines of code. This allows you to hardcode your hardware and controller settings for faster testing and deployment, bypassing the initial setup screens.

## Example

The following code demonstrates how to connect to an Arduino board, set the analog/digital channels, and launch the control interface with predefined PID parameters.

```python
import sys
from PySide6.QtWidgets import QApplication
from pydaq.guis.pid_control_window_dialog import PID_Control_Window_Dialog

app = QApplication(sys.argv)
plot_window = PID_Control_Window_Dialog()

# 1. Hardware Configuration
plot_window.check_board(
    board="arduino", 
    hardware_id="COM7", 
    ao=['D0', 'D1'], 
    ai=['A0', 'A1'], 
    terminal=None, 
    simulate=False
)

# 2. Controller & Logging Parameters
plot_window.set_parameters(
    kp=1.0, ki=0.2, kd=0.05, index=3, 
    numerator=None, denominator=None, 
    setpoint=2.0, unit="Voltage (V)", 
    equationvu="", equationuv="", 
    period=0.1, path=None, save=True
)

# 3. Launch the Application
plot_window.exec()
```

### Understanding the Methods

#### `check_board()`
This method injects the hardware configuration into the PyDAQ window.
* **`board`**: Type of board (`'arduino'` or `'nidaq'`).
* **`hardware_id`**: The communication port (e.g., `'COM7'` on Windows, `'/dev/ttyUSB0'` on Linux).
* **`ai` / `ao`**: Lists defining the Analog Inputs (Sensors) and Digital/PWM Outputs (Actuators). *Note: The number of AI and AO channels must match.*
* **`simulate`**: Set to `True` to run a mathematical simulation without hardware.

#### `set_parameters()`
This method sets the initial tuning for your controller and defines how data is saved. Pass `None` or `""` to fields you don't need to override.
* **`kp`, `ki`, `kd`**: Proportional, Integral, and Derivative gains.
* **`index`**: Controller Type (`0` = P, `1` = PI, `2` = PD, `3` = PID).
* **`setpoint`**: The target value the controller will try to reach.
* **`period`**: Sample period in seconds (e.g., `0.1` equals a 10Hz sampling rate).
* **`unit`**: The Y-axis label for the plot.
* **`path` / `save`**: Destination folder for `.dat` files. If `path` is `None`, it defaults to the user's Desktop. Set `save=True` to automatically save data when the window is closed.

#### `exec()`
Opens the control interface and starts the Qt event loop. This blocks the script until the window is closed by the user.

### Summary of Execution
* **`check_board`**: Selects Arduino as the control device and configures channels.
* **`set_parameters`**: Sets gains, setpoint, sampling period, and save path.
* **`exec()`**: Opens the control interface.