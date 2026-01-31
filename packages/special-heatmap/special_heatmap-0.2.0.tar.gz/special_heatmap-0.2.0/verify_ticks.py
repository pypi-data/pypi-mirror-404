import numpy as np
import matplotlib.pyplot as plt
from special_heatmap import SHeatmap

print("--- VERIFYING TICKS VIA REAL DRAW ---")

np.random.seed(42)
data_b = np.random.rand(12, 12) - 0.5
shm = SHeatmap(data_b, fmt='circ')

# Draw
shm.draw(mark_extremes=True)

# Find colorbar axes
fig = shm.ax.figure
# The colorbar axis is usually the last one added or appended
cbar_ax = fig.axes[-1]

ticks = cbar_ax.get_yticks()
labels = [label.get_text() for label in cbar_ax.get_yticklabels()]

print(f"Vmin: {shm.vmin}")
print(f"Vmax: {shm.vmax}")
print(f"Final Ticks: {ticks}")
print(f"Final Labels: {labels}")

# Check if any tick is out of range
out_of_range = [t for t in ticks if t < shm.vmin - 1e-5 or t > shm.vmax + 1e-5]
if out_of_range:
    print(f"FAIL: Found ticks out of range: {out_of_range}")
else:
    print("SUCCESS: All ticks are within range.")

plt.close()
