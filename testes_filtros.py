import numpy as np
import matplotlib.pyplot as plt

# Caminhos dos arquivos
time_way = "C:\\Users\\55319\\Desktop\\ok\\time.dat"
data_way = "C:\\Users\\55319\\Desktop\\ok\\data.dat"
dataf_way = "C:\\Users\\55319\\Desktop\\ok\\data_filtered.dat"

# Carregando dados
time = np.loadtxt(time_way)
data = np.loadtxt(data_way)
data_filtered = np.loadtxt(dataf_way)

plt.plot(time,data)
plt.show()

'''# Calculando o intervalo de amostragem e a frequência de amostragem
dt = 1 / (1.22 * 2)  # 1/(fs*2)
fs = 8               # Frequência de amostragem

# FFT do sinal original
fft_data = np.fft.fft(data)
freqs = np.fft.fftfreq(len(data), dt)

# FFT do sinal filtrado
fft_data_filtered = np.fft.fft(data_filtered)

# Apenas a parte positiva do espectro
positive_freqs = freqs[:len(freqs) // 2]
fft_data_magnitude = np.abs(fft_data[:len(freqs) // 2])
fft_data_filtered_magnitude = np.abs(fft_data_filtered[:len(freqs) // 2])

# Configurando a figura principal com subplots
fig = plt.figure(figsize=(10, 8))

# Subplot 1: Sinal no domínio do tempo
ax1 = fig.add_subplot(2, 2, 1)
ax1.plot(time, data, label='Sinal Original', color='b')
ax1.plot(time, data_filtered, label='Sinal Filtrado', color='r')
ax1.set_title('Sinal no Domínio do Tempo')
ax1.set_xlabel('Tempo (s)')
ax1.set_ylabel('Amplitude')
ax1.legend()
ax1.grid()

# Subplot 2: FFT dos sinais
ax2 = fig.add_subplot(2, 2, 2)
ax2.plot(positive_freqs, fft_data_magnitude, label='FFT Original', color='b')
ax2.plot(positive_freqs, fft_data_filtered_magnitude, label='FFT Filtrado', color='r')
ax2.set_title('Sinal no Domínio da Frequência')
ax2.set_xlabel('Frequência (Hz)')
ax2.set_ylabel('Magnitude')
ax2.legend()
ax2.grid()

# Ajustar layout para evitar sobreposição
plt.tight_layout()
plt.show()
'''