import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt

# Definindo o sistema: filtro passa-baixa Butterworth
order = 3  # Ordem do filtro
fc = 50  # Frequência de corte (Hz)
fs = 1000  # Taxa de amostragem (Hz)
b, a = signal.butter(order, fc, fs=fs, btype='low')

# Calculando a resposta em frequência
w, h = signal.freqz(b, a, worN=512, fs=fs)  # Frequências (w) e resposta (h)

# Separando módulo e fase
magnitude = 20 * np.log10(np.abs(h))  # Módulo em dB
phase = np.angle(h)  # Fase em radianos

# Plotando o módulo
plt.figure(figsize=(12, 8))
plt.subplot(2, 1, 1)
plt.plot(w, magnitude)
plt.title("Resposta em Frequência - Módulo")
plt.xlabel("Frequência (Hz)")
plt.ylabel("Magnitude (dB)")
plt.grid()

# Plotando a fase
plt.subplot(2, 1, 2)
plt.plot(w, phase)
plt.title("Resposta em Frequência - Fase")
plt.xlabel("Frequência (Hz)")
plt.ylabel("Fase (rad)")
plt.grid()

plt.tight_layout()
plt.show()
