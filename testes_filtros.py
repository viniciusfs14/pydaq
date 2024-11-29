import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import firwin, lfilter, freqz
import scipy.signal as signal

time_way = "C:\\Users\\55319\\Desktop\\time.dat"
data_way = "C:\\Users\\55319\\Desktop\\data.dat"
dataf_way = "C:\\Users\\55319\\Desktop\\data_filtered.dat"

# Carregando dados
time = np.loadtxt(time_way)
data = np.loadtxt(data_way)
data_filtered = np.loadtxt(dataf_way)

plt.plot(time, data, color='b')
plt.plot(time, data_filtered, color='r')
plt.grid()
plt.show()


