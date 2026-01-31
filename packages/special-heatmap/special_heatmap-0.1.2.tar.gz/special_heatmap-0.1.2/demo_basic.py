import numpy as np
import matplotlib.pyplot as plt
import os
from special_heatmap import SHeatmap

def ensure_gallery():
    if not os.path.exists('gallery'):
        os.makedirs('gallery')

def demo_basic_positive():
    print("Running Demo: Basic Positive (sq)")
    plt.figure()
    data = np.random.rand(15, 15)
    shm = SHeatmap(data, fmt='sq')
    shm.draw()
    plt.title('Basic Positive')
    plt.savefig('gallery/Basic_positive.png', bbox_inches='tight', dpi=150)
    plt.close()

def demo_basic_negative():
    print("Running Demo: Basic Negative (sq)")
    plt.figure()
    data = np.random.rand(15, 15) - 0.5
    shm = SHeatmap(data, fmt='sq')
    shm.draw()
    plt.title('Basic Negative')
    plt.savefig('gallery/Basic_negative.png', bbox_inches='tight', dpi=150)
    plt.close()

def demo_formats():
    print("Running Demo: Various Formats")
    formats = ['sq', 'pie', 'circ', 'oval', 'hex', 'asq', 'acirc']
    data_a = np.random.rand(12, 12)
    data_b = np.random.rand(12, 12) - 0.5
    
    for fmt in formats:
        print(f"  - Format: {fmt}")
        
        # A (Positive)
        plt.figure()
        shm = SHeatmap(data_a, fmt=fmt)
        shm.draw()
        plt.title(f'Format {fmt} (Positive)')
        plt.savefig(f'gallery/Format_{fmt}_A.png', bbox_inches='tight', dpi=150)
        plt.close()
        
        # B (Negative/Mixed)
        plt.figure()
        shm = SHeatmap(data_b, fmt=fmt)
        shm.draw()
        plt.title(f'Format {fmt} (Mixed)')
        plt.savefig(f'gallery/Format_{fmt}_B.png', bbox_inches='tight', dpi=150)
        plt.close()

def demo_text_nan():
    print("Running Demo: Text and NaN")
    plt.figure()
    data = np.random.rand(12, 12) - 0.5
    # Set some NaNs
    data[3, 3] = np.nan
    data[4, 4] = np.nan
    data[11, 11] = np.nan
    
    shm = SHeatmap(data, fmt='sq')
    shm.draw()
    shm.set_text(fontsize=8, color='black') # Simple black text
    plt.title('Basic with Text and NaN')
    plt.savefig('gallery/Basic_with_text.png', bbox_inches='tight', dpi=150)
    plt.close()

def demo_triangle():
    print("Running Demo: Triangular Heatmaps")
    types = ['triu', 'tril', 'triu0', 'tril0']
    data = np.random.rand(12, 12)
    
    for t in types:
        print(f"  - Type: {t}")
        plt.figure()
        shm = SHeatmap(data, fmt='sq')
        shm.set_type(t)
        shm.draw()
        shm.set_text(fontsize=6, color='black')
        plt.title(f'Triangular: {t}')
        plt.savefig(f'gallery/Type_{t}.png', bbox_inches='tight', dpi=150)
        plt.close()

if __name__ == "__main__":
    ensure_gallery()
    demo_basic_positive()
    demo_basic_negative()
    demo_formats()
    demo_text_nan()
    demo_triangle()
    print("All demos completed. Check 'gallery' folder.")
