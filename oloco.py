import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset

# Dados de exemplo
x = np.linspace(0, 10, 100)
y = np.sin(x)

fig, ax = plt.subplots()

# Gráfico principal
ax.plot(x, y, label="Seno")

# Criando o inset plot (zoom)
axins = inset_axes(ax, width="30%", height="30%", loc="upper right")  # Tamanho e posição
axins.plot(x, y)  # Mesmo plot no inset
axins.set_xlim(2, 4)  # Zoom na região desejada
axins.set_ylim(-1, 1)

# Marcando área ampliada
mark_inset(ax, axins, loc1=2, loc2=4, fc="none", ec="red")

plt.show()
