import nidaqmx
import time
import warnings
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import lfilter, butter


class DataAcquisition:
    def __init__(self, device, channel, ts, session_duration, terminal="default", plot=True, save=True):
        self.device = device
        self.channel = channel
        self.ts = ts  # Tempo de amostragem
        self.session_duration = session_duration  # Duração da aquisição
        self.terminal = terminal  # Configuração do terminal
        self.plot = plot  # Habilitar gráfico
        self.save = save  # Habilitar salvamento de dados
        self.data = []  # Dados originais
        self.filtered_data = []  # Dados filtrados
        self.time_var = []  # Tempo de aquisição

    def _check_path(self):
        # Simulação de verificação de caminho
        print("Verificando caminho para salvar os dados...")

    def _start_updatable_plot(self):
        plt.figure("iter_plot")
        plt.ion()  # Ativa modo interativo
        plt.show()

    def _update_plot_dual(self, time_var, data, filtered_data):
        plt.figure("iter_plot")
        plt.clf()
        plt.plot(time_var, data, label="Original Data", color="blue")
        plt.plot(time_var, filtered_data, label="Filtered Data", color="red")
        plt.title(self.title)
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")
        plt.legend()
        plt.pause(0.01)

    def _save_data(self, data, filename):
        np.savetxt(filename, data, delimiter=",")
        print(f"Arquivo salvo: {filename}")

    def get_data_nidaq(self, filter_coeffs=None):
        """
        Método ajustado para incluir filtro digital e plotar os dados filtrados e originais.
        
        Args:
            filter_coeffs (tuple): Coeficientes do filtro digital na forma (b, a).
        """
        self.data = []
        self.filtered_data = []
        self.time_var = []

        # Checking if path was defined
        self._check_path()

        # Number of self.cycles necessary
        self.cycles = int(np.floor(self.session_duration / self.ts)) + 1

        # Initializing device, with channel defined
        task = nidaqmx.Task()
        task.ai_channels.add_ai_voltage_chan(
            self.device + "/" + self.channel, terminal_config=self.terminal
        )

        if self.plot:  # If plot, start updatable plot
            self.title = f"PYDAQ - Data Acquisition. {self.device}, {self.channel}"
            self._start_updatable_plot()

        # Main loop, where data will be acquired
        for k in range(self.cycles):
            # Counting time to append data and update interface
            st = time.time()

            # Acquire data
            temp = task.read()
            self.data.append(temp)
            self.time_var.append(k * self.ts)

            # Apply filter if coefficients are provided
            if filter_coeffs:
                b, a = filter_coeffs
                filtered_temp = lfilter(b, a, [temp])[-1]  # Filtrando o dado atual
            else:
                filtered_temp = temp  # Sem filtro

            self.filtered_data.append(filtered_temp)

            if self.plot:
                # Checking if there is still an open figure. If not, stop the loop.
                try:
                    plt.get_figlabels().index("iter_plot")
                except BaseException:
                    break

                # Updating data values (add support for filtered data)
                self._update_plot_dual(self.time_var, self.data, self.filtered_data)

            print(f"Iteration: {k} of {self.cycles - 1}")

            # Getting end time
            et = time.time()

            # Wait for (ts - delta_time) seconds
            try:
                time.sleep(self.ts + (st - et))
            except BaseException:
                warnings.warn(
                    "Time spent to append data and update interface was greater than ts. "
                    "You CANNOT trust time.dat"
                )

        # Closing task
        task.close()

        # Check if data will or not be saved, and save accordingly
        if self.save:
            print("\nSaving data ...")
            # Saving time_var and data
            self._save_data(self.time_var, "time.dat")
            self._save_data(self.data, "data.dat")
            self._save_data(self.filtered_data, "filtered_data.dat")
            print("\nData saved ...")

        return


# Exemplo de uso
if __name__ == "__main__":
    # Criando um filtro passa-baixas Butterworth com frequência de corte de 10 Hz
    fs = 100  # Frequência de amostragem
    fc = 10  # Frequência de corte
    b, a = butter(N=4, Wn=fc / (fs / 2), btype="low")

    # Instanciando o objeto
    daq = DataAcquisition(
        device="Dev1",
        channel="ai0",
        ts=0.01,  # Intervalo de 10 ms
        session_duration=5,  # Duração de 5 segundos
        plot=True,
        save=True,
    )

    # Chamada do método ajustado com o filtro
    daq.get_data_nidaq(filter_coeffs=(b, a))
