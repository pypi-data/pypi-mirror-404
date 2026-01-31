import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as mcolors
from matplotlib.collections import PatchCollection

class SHeatmap:
    def __init__(self, data, fmt='sq', parent=None, cmap=None):
        self.data = np.array(data)
        self.fmt = fmt
        self.ax = parent
        
        # Default Colors (copied from SHeatmap.m)
        # Sequential (Greens)
        self.dfColor1 = np.array([
            [0.9686, 0.9882, 0.9412], [0.9454, 0.9791, 0.9199], [0.9221, 0.9700, 0.8987], [0.8988, 0.9609, 0.8774],
            [0.8759, 0.9519, 0.8560], [0.8557, 0.9438, 0.8338], [0.8354, 0.9357, 0.8115], [0.8152, 0.9276, 0.7892],
            [0.7909, 0.9180, 0.7685], [0.7545, 0.9039, 0.7523], [0.7180, 0.8897, 0.7361], [0.6816, 0.8755, 0.7199],
            [0.6417, 0.8602, 0.7155], [0.5962, 0.8430, 0.7307], [0.5507, 0.8258, 0.7459], [0.5051, 0.8086, 0.7610],
            [0.4596, 0.7873, 0.7762], [0.4140, 0.7620, 0.7914], [0.3685, 0.7367, 0.8066], [0.3230, 0.7114, 0.8218],
            [0.2837, 0.6773, 0.8142], [0.2483, 0.6378, 0.7929], [0.2129, 0.5984, 0.7717], [0.1775, 0.5589, 0.7504],
            [0.1421, 0.5217, 0.7314], [0.1066, 0.4853, 0.7132], [0.0712, 0.4488, 0.6950], [0.0358, 0.4124, 0.6768],
            [0.0314, 0.3724, 0.6364], [0.0314, 0.3319, 0.5929], [0.0314, 0.2915, 0.5494], [0.0314, 0.2510, 0.5059]
        ])
        
        # Diverging (Red-Blue)
        self.dfColor2 = np.array([
            [0.6196, 0.0039, 0.2588], [0.6892, 0.0811, 0.2753], [0.7588, 0.1583, 0.2917], [0.8283, 0.2354, 0.3082],
            [0.8706, 0.2966, 0.2961], [0.9098, 0.3561, 0.2810], [0.9490, 0.4156, 0.2658], [0.9660, 0.4932, 0.2931],
            [0.9774, 0.5755, 0.3311], [0.9887, 0.6577, 0.3690], [0.9930, 0.7266, 0.4176], [0.9943, 0.7899, 0.4707],
            [0.9956, 0.8531, 0.5238], [0.9968, 0.9020, 0.5846], [0.9981, 0.9412, 0.6503], [0.9994, 0.9804, 0.7161],
            [0.9842, 0.9937, 0.7244], [0.9526, 0.9810, 0.6750], [0.9209, 0.9684, 0.6257], [0.8721, 0.9486, 0.6022],
            [0.7975, 0.9183, 0.6173], [0.7228, 0.8879, 0.6325], [0.6444, 0.8564, 0.6435], [0.5571, 0.8223, 0.6448],
            [0.4698, 0.7881, 0.6460], [0.3868, 0.7461, 0.6531], [0.3211, 0.6727, 0.6835], [0.2553, 0.5994, 0.7139],
            [0.2016, 0.5261, 0.7378], [0.2573, 0.4540, 0.7036], [0.3130, 0.3819, 0.6694], [0.3686, 0.3098, 0.6353]
        ])

        # Determine Colormap and Range
        self.max_v = np.nanmax(np.abs(self.data))
        if np.any(self.data < 0):
            # Diverging
            self.colormap_data = self.dfColor2
            self.vmin, self.vmax = -self.max_v, self.max_v
            self.cmap_name = 'SHeatmap_Diverging'
        else:
            # Sequential (Reversed dfColor1 to match SHeatmap logic: Light -> Dark or Dark -> Light?)
            # SHeatmap.m: obj.dfColor1(end:-1:1,:)
            # dfColor1 last row is dark green (0.03...). First row is light (0.96...).
            # Reversing it puts Dark at index 1 and Light at index End.
            # So Low Values = Dark, High Values = Light.
            # This is slightly unusual for standard heatmaps (usually High=Dark/Intense).
            # Let's double check MATLAB behavior.
            # colormap(map). Data maps to map.
            # If map is [Dark ... Light]. Low data = Dark. High data = Light.
            # Let's stick to the code.
            self.colormap_data = self.dfColor1[::-1] 
            self.vmin, self.vmax = 0, self.max_v
            self.cmap_name = 'SHeatmap_Sequential'

        if cmap is None:
            self.cmap = mcolors.LinearSegmentedColormap.from_list(self.cmap_name, self.colormap_data)
        else:
            self.cmap = plt.get_cmap(cmap)
        
        self.type = 'full'
            
        self.patches_list = []
        self.texts = []
        
    def set_type(self, type_str):
        """
        Set heatmap type: 'full', 'triu', 'tril', 'triu0', 'tril0'
        """
        self.type = type_str

    def draw(self):
        if self.ax is None:
            fig, self.ax = plt.subplots(figsize=(8, 8))
        
        rows, cols = self.data.shape
        
        # Setup Axes
        self.ax.set_xlim(0, cols)
        self.ax.set_ylim(rows, 0) # Invert Y axis (0 at top)
        self.ax.set_aspect('equal')
        self.ax.set_xticks(np.arange(cols) + 0.5)
        self.ax.set_yticks(np.arange(rows) + 0.5)
        self.ax.set_xticklabels(np.arange(1, cols + 1))
        self.ax.set_yticklabels(np.arange(1, rows + 1))
        self.ax.tick_params(top=False, bottom=True, labeltop=False, labelbottom=True)
        
        # Grid/Box
        # self.ax.grid(True, color='0.85', linestyle='-', linewidth=0.8)
        
        norm = mcolors.Normalize(vmin=self.vmin, vmax=self.vmax)
        
        for r in range(rows):
            for c in range(cols):
                # Visibility Logic
                visible = True
                if self.type == 'triu':
                    if c < r: visible = False
                elif self.type == 'tril':
                    if c > r: visible = False
                elif self.type == 'triu0':
                    if c <= r: visible = False
                elif self.type == 'tril0':
                    if c >= r: visible = False
                
                if not visible:
                    continue

                val = self.data[r, c]
                # Center coordinates
                cx, cy = c + 0.5, r + 0.5
                
                if np.isnan(val):
                    # Draw X for NaN
                    # Gray background
                    rect = patches.Rectangle((c, r), 1, 1, facecolor='0.8', edgecolor='none')
                    self.ax.add_patch(rect)
                    # X text
                    self.ax.text(cx, cy, '×', ha='center', va='center', fontsize=16, fontname='Times New Roman')
                    continue
                
                color = self.cmap(norm(val))
                t_ratio = abs(val) / self.max_v
                
                patch = None
                
                if self.fmt == 'sq':
                    # Square filling the cell
                    patch = patches.Rectangle((c + 0.01, r + 0.01), 0.98, 0.98, facecolor=color, edgecolor='none')
                    self.ax.add_patch(patch)
                    
                elif self.fmt == 'asq':
                    # Auto-size Square
                    size = 0.98 * t_ratio
                    offset = (1 - size) / 2
                    patch = patches.Rectangle((c + offset, r + offset), size, size, facecolor=color, edgecolor='none')
                    self.ax.add_patch(patch)
                    
                elif self.fmt == 'circ':
                    # Circle
                    radius = 0.92 * 0.5 # 0.46
                    patch = patches.Circle((cx, cy), radius, facecolor=color, edgecolor='none')
                    self.ax.add_patch(patch)
                    
                elif self.fmt == 'acirc':
                    # Auto-size Circle
                    radius = 0.92 * 0.5 * t_ratio
                    patch = patches.Circle((cx, cy), radius, facecolor=color, edgecolor='none')
                    self.ax.add_patch(patch)
                
                elif self.fmt == 'pie':
                    # Pie Chart
                    # Background circle (white/outline)
                    bg_radius = 0.92 * 0.5
                    bg_circ = patches.Circle((cx, cy), bg_radius, facecolor='white', edgecolor='0.3', linewidth=0.8)
                    self.ax.add_patch(bg_circ)
                    
                    # Wedge
                    # Matplotlib wedge: theta1, theta2 in degrees.
                    # MATLAB: linspace(pi/2, pi/2 + ratio*2pi). 
                    # 90 degrees start.
                    theta1 = 90
                    theta2 = 90 + (val / self.max_v) * 360 # Assuming positive ratio for simplicity or mapping logic
                    
                    # If val is negative in pie? SHeatmap uses obj.Data(row,col) directly.
                    # If val is negative, theta2 < theta1.
                    
                    wedge = patches.Wedge((cx, cy), bg_radius, theta1, theta2, facecolor=color, edgecolor='0.3', linewidth=0.8)
                    self.ax.add_patch(wedge)

                elif self.fmt == 'hex':
                    # Hexagon
                    # RegularPolygon takes radius (distance to vertex).
                    # Width of cell is 1. Radius approx 0.5.
                    radius = 0.5 * 0.98 * t_ratio
                    # Orientation: MATLAB uses flat top or pointy top? 
                    # MATLAB cos(hexT) where hexT=linspace(0, 2pi, 7). 0 is (1,0) (Right).
                    # So vertices at 0, 60, 120... Pointy on right/left?
                    # Matplotlib RegularPolygon orientation is rotation in radians.
                    poly = patches.RegularPolygon((cx, cy), numVertices=6, radius=radius, 
                                                  orientation=0, facecolor=color, edgecolor='0.3', linewidth=0.8)
                    self.ax.add_patch(poly)

                elif self.fmt == 'oval':
                    # Oval (Ellipse)
                    # SHeatmap logic:
                    # tValue = val/maxV
                    # baseA = 1 + (tValue<=0)*tValue  (If neg, shrinks width?)
                    # baseB = 1 - (tValue>=0)*tValue  (If pos, shrinks height?)
                    # This logic seems to make it "fat" or "tall" based on sign?
                    # Let's approximate:
                    # width = 0.98 * baseA
                    # height = 0.98 * baseB
                    
                    # Implementation:
                    t_val = val / self.max_v
                    base_a = 1 + t_val if t_val <= 0 else 1
                    base_b = 1 - t_val if t_val >= 0 else 1
                    
                    # Rotated 45 degrees?
                    # MATLAB: thetaMat = [1 -1; 1 1]*sqrt(2)/2 (Rotation 45 deg)
                    # baseOvalXY = thetaMat * [baseOvalX; baseOvalY]
                    
                    ellipse = patches.Ellipse((cx, cy), width=base_a*0.9, height=base_b*0.9, angle=45,
                                              facecolor=color, edgecolor='0.3', linewidth=0.8)
                    self.ax.add_patch(ellipse)


        # Colorbar
        sm = plt.cm.ScalarMappable(cmap=self.cmap, norm=norm)
        sm.set_array([])
        plt.colorbar(sm, ax=self.ax)
        
        return self

    def set_text(self, fmt='{:.2f}', **kwargs):
        rows, cols = self.data.shape
        for r in range(rows):
            for c in range(cols):
                # Visibility Logic
                visible = True
                if self.type == 'triu':
                    if c < r: visible = False
                elif self.type == 'tril':
                    if c > r: visible = False
                elif self.type == 'triu0':
                    if c <= r: visible = False
                elif self.type == 'tril0':
                    if c >= r: visible = False
                
                if not visible:
                    continue

                val = self.data[r, c]
                if np.isnan(val):
                    continue
                
                # Determine text color based on background brightness
                # Simple heuristic: if abs(val) is high, bg is dark -> white text.
                # But our colormap logic might be reversed?
                # Let's just default to black/white threshold.
                # For now, just black or passed kwargs.
                
                s = fmt.format(val)
                cx, cy = c + 0.5, r + 0.5
                self.ax.text(cx, cy, s, ha='center', va='center', **kwargs)

if __name__ == '__main__':
    # Simple self-test
    data = np.random.rand(10, 10) - 0.5
    data[2, 2] = np.nan
    shm = SHeatmap(data, fmt='sq')
    shm.draw()
    plt.show()
