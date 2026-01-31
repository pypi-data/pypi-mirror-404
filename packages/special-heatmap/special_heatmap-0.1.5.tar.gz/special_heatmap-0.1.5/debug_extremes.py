import numpy as np
import matplotlib.pyplot as plt
from special_heatmap import SHeatmap

print("--- DEBUGGING COLORBAR EXTREMES ---")

# Recreate the data from demo_formats (Format_circ_B)
np.random.seed(42) # Fixed seed for reproducibility
data_b = np.random.rand(12, 12) - 0.5

print(f"Data Min: {np.nanmin(data_b)}")
print(f"Data Max: {np.nanmax(data_b)}")
print(f"Data Abs Max: {np.nanmax(np.abs(data_b))}")

# Initialize SHeatmap
shm = SHeatmap(data_b, fmt='circ')

print(f"SHeatmap vmin: {shm.vmin}")
print(f"SHeatmap vmax: {shm.vmax}")

# Simulate Draw logic for colorbar
mark_extremes = True
norm = plt.cm.colors.Normalize(vmin=shm.vmin, vmax=shm.vmax)
cmap = shm.cmap

fig, ax = plt.subplots()
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax)

current_ticks = cbar.get_ticks()
print(f"Default Matplotlib Ticks: {current_ticks}")

if mark_extremes:
    data_range = shm.vmax - shm.vmin
    threshold = data_range * 0.05
    final_ticks = [shm.vmin, shm.vmax]
    for t in current_ticks:
        if abs(t - shm.vmin) > threshold and abs(t - shm.vmax) > threshold:
            final_ticks.append(t)
    final_ticks = sorted(list(set(final_ticks)))
    print(f"Calculated Final Ticks: {final_ticks}")

plt.close()
print("--- END DEBUG ---")
