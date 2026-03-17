import os
import time
import numpy as np
from scipy.signal import dlti, dlsim
import scipy.signal as signal
import serial
import serial.tools.list_ports
from pydaq.utils.base import Base
import os
import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
import warnings
import nidaqmx
from nidaqmx.constants import TerminalConfiguration

class PIDControl(Base): 
    def __init__( 
        self, 
        Kp, 
        Ki, 
        Kd, 
        setpoint=0.0, 
        numerator = '1', 
        denominator = 's+0.2', 
        calibration_equation_vu = None, 
        calibration_equation_uv = None, 
        unit='Voltage (V)', 
        period=1 
        ):

        super().__init__() #Inicializating the matematical control
        self.Kp = float(Kp)
        self.Ki = float(Ki)
        self.Kd = float(Kd)
        self.disturbe = 0
        self.setpoint = float(setpoint)
        self.numerator = numerator
        self.denominator = denominator
        self.calibration_equation_vu = calibration_equation_vu
        self.calibration_equation_uv = calibration_equation_uv
        self.integral = 0.0
        self.previous_error = 0.0
        self.previous_output = 0.0
        self.period = period
        self.device = "Dev1" # To nidaq
        self.ao_channel="ao0"
        self.ai_channel="ai0"
        self.terminal="Diff"
        self.com_port = 'COM1' # To arduino  # Default COM port
        self.a = 0.2 # To simulate
        
        self.channels = [self.ai_channel]       # Default single AI channel
        self.ao_channels = [self.ao_channel]    # Default single AO channel

        # PID internal states per channel
        self.integral = {ch: 0.0 for ch in self.channels}
        self.previous_error = {ch: 0.0 for ch in self.channels}
        self.previous_output = {ch: 0.0 for ch in self.channels}
        self.error = {ch: 0.0 for ch in self.channels}
        self.output = {ch: 0.0 for ch in self.channels}
        self.control_unit = {ch:0 for ch in self.channels}

    def update(self, ch, feedback_value):
        self.error[ch] = self.setpoint - feedback_value
        self.integral[ch] = self.integral[ch] + self.error[ch] * self.period
        derivative = (self.error[ch] - self.previous_error[ch]) / self.period
        self.output[ch] = self.Kp * self.error[ch] + self.Ki * self.integral[ch] + self.Kd * derivative
        self.previous_error[ch] = self.error[ch]
        self.previous_output[ch] = self.output[ch]
        return self.output[ch], self.error[ch]

    def pid_control_arduino(self):
        self.feedback_value = {ch: 0 for ch in self.channels}
        self.feedback_calibrated = {ch: 0 for ch in self.channels}
        self.control_voltage = {ch: 0 for ch in self.channels}
        self.control_unit = {ch: 0 for ch in self.channels}
        self.control = {ch: 0 for ch in self.channels}
        self.error = {ch: 0 for ch in self.channels}

        self.integral = {ch: 0.0 for ch in self.channels}
        self.previous_error = {ch: 0.0 for ch in self.channels}
        self.previous_output = {ch: 0.0 for ch in self.channels}
        self.output = {ch: 0.0 for ch in self.channels}

        self.com_ports = [i.description for i in serial.tools.list_ports.comports()] # COM ports
        self._open_serial() # Oppening ports
        self.arduino_ai_bits = 10 # Arduino ADC resolution (in bits)
        self.ard_ao_max, self.ard_ao_min = 5, 0 # Arduino analog input max and min
        self.ard_vpb = (self.ard_ao_max - self.ard_ao_min) / ((2 ** self.arduino_ai_bits)-1) # Value per bit - Arduino

        time.sleep(0.5)  # Espera o Arduino reiniciar ao abrir a Serial
        self.ser.reset_input_buffer() # Limpa o lixo inicial UMA SÓ VEZ
        try:
            _ = self.ser.readline() # Leitura de descarte
        except:
            pass
        
        self.title = f"PYDAQ - Step Response (Arduino), Port: {self.com_port}" # Start updatable plot

        # --- MOD ---
        self.n_channels = len(self.channels)

        print("Worker channels:", self.channels)
        print("Worker AO channels:", self.ao_channels)

# Updating the Datas to plot
    def update_plot_arduino(self):
        
        #self.ser.reset_input_buffer()
        
        #data = self.ser.read(14).decode("UTF-8") # Get the feedback sensor value

        try:
            raw = self.ser.readline()

            values = list(map(int, raw.decode("utf-8").strip().split(",")))

            if len(values) < self.n_channels:
                raise ValueError("Incomplete multichannel frame")
        except:
            values = [self.feedback_value[ch] for ch in self.channels]

        outputs = {}
        errors = {}
        controls = {}

        duty_cycles = []

        for i, ch in enumerate(self.channels):
            self.feedback_value[ch] = values[i] * self.ard_vpb
            self.feedback_calibrated[ch] = self.calibrationuv(self.feedback_value[ch])
            self.control_unit[ch], error = self.update(ch,self.feedback_calibrated[ch])
            self.control_voltage[ch] = self.calibrationvu(self.control_unit[ch])
            self.control[ch] = self.control_voltage[ch]
            if self.control[ch] <= self.ard_ao_min:
                self.control[ch] = self.ard_ao_min
            elif self.control[ch] >= self.ard_ao_max:
                self.control[ch] = self.ard_ao_max

            duty = int((self.control[ch] / self.ard_ao_max) * 255)
            duty_cycles.append(duty)

            self.error[ch] = error

            outputs[ch] = self.feedback_calibrated[ch]
            errors[ch] = error
            controls[ch] = self.control[ch]

        # --- MOD --- send multichannel control
        msg = ",".join(map(str, duty_cycles)) + "\n"

        self.ser.write(msg.encode())

        #print(f"Control (V)/(U): {self.control:.2f} / {self.control_unit:.2f}; Feedback (V)/(U): {self.feedback_value:.2f} / {self.feedback_calibrated:.2f}; Setpoint(U) {self.setpoint:.2f}; error (U) {self.error}")
        
        return (outputs,errors,{ch: self.setpoint for ch in self.channels},controls)

    def pid_control_nidaq(self): #Inicializating the updating nidaq values
        terminal_config = self.terminal # Terminal configuration
        self._nidaq_info() # Gathering nidaq info
        self.task_ai = nidaqmx.Task()
        self.task_ao = nidaqmx.Task()   

        # --- MULTICHANNEL MOD ---
        for ch in self.channels:

            self.task_ai.ai_channels.add_ai_voltage_chan(
                self.device + "/" + ch, terminal_config=terminal_config
            )
        
        for ch in self.ao_channels:

            self.task_ao.ao_channels.add_ao_voltage_chan(
                self.device + "/" + ch,
                min_val=0.0,
                max_val=5.0
            )

        self.feedback_value = {ch: 0 for ch in self.channels}
        self.feedback_calibrated = {ch: 0 for ch in self.channels}
        self.control_voltage = {ch: 0 for ch in self.channels}
        self.control = {ch: 0 for ch in self.channels}

        self.control_unit = {ch: 0.0 for ch in self.channels}
        self.error = {ch: 0.0 for ch in self.channels}
        self.integral = {ch: 0.0 for ch in self.channels}
        self.previous_error = {ch: 0.0 for ch in self.channels}
        self.previous_output = {ch: 0.0 for ch in self.channels}
        self.output = {ch: 0.0 for ch in self.channels}

    def update_plot_nidaq(self):

        values = self.task_ai.read()

        if len(self.channels) == 1:
            values = [values]

        # --- MOD --- guarantee dictionaries exist
        if not hasattr(self, "error"):
            self.error = {ch: 0 for ch in self.channels}

        if not hasattr(self, "control_unit"):
            self.control_unit = {ch: 0 for ch in self.channels}

        # --- MULTICHANNEL MOD ---
        for i, ch in enumerate(self.channels):
            
            self.feedback_value[ch] = values[i]
            self.feedback_calibrated[ch] = self.calibrationuv(self.feedback_value[ch])
            self.control_unit[ch], error = self.update(ch, self.feedback_calibrated[ch])
            self.control_voltage[ch] = self.calibrationvu(self.control_unit[ch])
            self.control[ch] = self.control_voltage[ch]

            if(self.control[ch] <= 0):
                self.control[ch] = 0
            elif (self.control[ch] >= 5):
                self.control[ch] = 5

            self.error[ch] = error
            
        self.task_ao.write([self.control[ch] for ch in self.channels])

        #self.error = self.setpoint - self.feedback_calibrated[ch]
        #print(f"Control (V)/(U): {self.control:.2f} / {self.control_unit:.2f}; Feedback (V)/(U): {self.feedback_value:.2f} / {self.feedback_calibrated:.2f}; Setpoint(U) {self.setpoint:.2f}; error (U) {self.error}")
        
        return (
            self.feedback_calibrated,
            self.error,
            {ch:self.setpoint for ch in self.channels},
            self.control
        )

    def simulate_system(self):

        ch = self.channels[0]

        self.feedback_voltages = {ch: []}
        self.controls_voltages = {ch: []}
        
        self.feedback_value = {ch: 0}
        self.control = {ch: 0}
        self.control_voltage = {ch: 0}
        self.feedback_calibrated = {ch: 0}

        self.integral = {ch: 0.0}
        self.previous_error = {ch: 0.0}
        self.previous_output = {ch: 0.0}
        self.error = {ch: 0.0}
        self.output = {ch: 0.0}
        self.control_unit = {ch: 0.0}

        numerator_cont = self.parse_polynomial(self.numerator)
        denominator_cont = self.parse_polynomial(self.denominator)

        self.system_cont = signal.TransferFunction(numerator_cont, denominator_cont)

    def update_simulated_system(self):
        
        ch = self.channels[0]

        self.control_unit[ch], error = self.update(ch, self.feedback_calibrated[ch])
        self.control_unit[ch] = self.control_unit[ch] - self.disturbe
        self.control_voltage[ch] = self.calibrationvu(self.control_unit[ch])
        self.control[ch] = self.control_voltage[ch]
        self.feedback_calibrated[ch] = self.calibrationuv(self.feedback_value[ch])
        self.controls_voltages[ch].append(self.control_voltage[ch])
        self.feedback_voltages[ch].append(self.feedback_value[ch])
        _, val = self.get_value_simulate_system(self.system_cont,self.period,self.control[ch],self.feedback_value[ch],)
        self.feedback_value[ch] = val
        self.error[ch] = error

        outputs = {ch: self.feedback_calibrated[ch]}
        errors = {ch: error}
        controls = {ch: self.control[ch]}

        # --- MOD --- return dictionaries
        return (outputs, errors, {ch: self.setpoint},controls)

    def calibrationvu(self, output):
        if not self.calibration_equation_vu or not self.calibration_equation_vu.strip():
            return output
        else:
            # WARNING: Using eval is a security risk if the equation string is not from a trusted source.
            # It can execute arbitrary code. For this application, we assume the user provides a safe
            # mathematical expression.
            try:
                # Safely evaluate the expression with only 'x' available as a variable.
                output_calibrated = eval(self.calibration_equation_vu, {"__builtins__": None}, {"x": output})
                return float(output_calibrated)
            except Exception as e:
                print(f"Error evaluating calibration_equation_vu: {e}")
                return output # Return original value in case of error

    def calibrationuv(self, output):
        if not self.calibration_equation_uv or not self.calibration_equation_uv.strip():
            return output
        else:
            # WARNING: Using eval is a security risk if the equation string is not from a trusted source.
            # It can execute arbitrary code. For this application, we assume the user provides a safe
            # mathematical expression.
            try:
                # Safely evaluate the expression with only 'x' available as a variable.
                output_calibrated = eval(self.calibration_equation_uv, {"__builtins__": None}, {"x": output})
                return float(output_calibrated)
            except Exception as e:
                print(f"Error evaluating calibration_equation_uv: {e}")
                return output # Return original value in case of error

    def parse_polynomial(self,poly_str):
        """
        Parses a polynomial string (e.g., '2*s**2 + 3*s - 1') into a list of coefficients.
        """
        poly_str = poly_str.replace(' ', '').replace('-', '+-')
        if poly_str.startswith('+-'):
            poly_str = poly_str[1:] # Correct for leading negative si   gn
        
        terms = poly_str.split('+')
        
        # --- Find the highest degree of the polynomial ---
        max_degree = 0
        for term in terms:
            if not term: continue
            if 's' in term:
                if '**' in term:
                    try:
                        degree = int(term.split('**')[1])
                        if degree > max_degree:
                            max_degree = degree
                    except (ValueError, IndexError):
                        raise ValueError(f"Invalid term format: {term}")
                else: # s is present, but s** is not, so degree is 1
                    if 1 > max_degree:
                        max_degree = 1

        # --- Initialize coefficient list with zeros ---
        # For a degree 'n' polynomial, we need n+1 coefficients (from s^n to s^0)
        coeffs = [0.0] * (max_degree + 1)
        
        # --- Populate coefficients from each term ---
        for term in terms:
            if not term: continue
            
            # --- Case 1: Constant term (no 's') ---
            if 's' not in term:
                coeffs[max_degree] += float(term)
                continue

            # --- Case 2: Terms with 's' ---
            if '**' in term:
                parts = term.split('**')
                degree = int(parts[1])
                coeff_part = parts[0].replace('s', '').replace('*', '')
            else: # Degree is 1
                degree = 1
                coeff_part = term.replace('s', '').replace('*', '')
            
            # Determine the coefficient value
            if coeff_part == '':
                coeff_val = 1.0
            elif coeff_part == '-':
                coeff_val = -1.0
            else:
                coeff_val = float(coeff_part)
            
            # Place the coefficient in the correct position in the list
            # The position is (max_degree - current_degree)
            coeffs[max_degree - degree] += coeff_val

        return coeffs
    def get_value_simulate_system(self, system, period, control, x0):

        time_control = np.linspace(0, period, 100)  
        input_control_signal = np.full_like(time_control, control)
        time_array_output, system_output, _ = signal.lsim(system, input_control_signal, time_control,x0)
        last_time = time_array_output[-1]
        last_output = system_output[-1]
        return last_time, last_output