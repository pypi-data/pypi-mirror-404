import numpy as np
import matplotlib.pyplot as plt
from special_heatmap import SHeatmap

print("Verifying Custom Colormap...")

data = np.random.rand(10, 10)

# Case 1: Standard Matplotlib String
print("Testing 'magma' colormap...")
shm1 = SHeatmap(data, fmt='sq', cmap='magma')
shm1.draw()
plt.title('Custom Colormap: magma')
plt.savefig('verify_cmap_magma.png')
plt.close()

# Case 2: Custom LinearSegmentedColormap
print("Testing custom LinearSegmentedColormap...")
from matplotlib.colors import LinearSegmentedColormap
colors = ["darkorange", "gold", "lawngreen", "lightseagreen"]
cmap1 = LinearSegmentedColormap.from_list("my_cmap", colors)

shm2 = SHeatmap(data, fmt='circ', cmap=cmap1)
shm2.draw()
plt.title('Custom Colormap Object')
plt.savefig('verify_cmap_object.png')
plt.close()

print("Verification done. Check png files.")
