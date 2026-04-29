import os
import matplotlib
from matplotlib import pyplot as plt

if os.environ.get("HEADLESS", "").lower() in ("1", "true"):
    matplotlib.use("Agg")

def plot_image(array, title=""):
    """ matplotlib to represent each card"""

    plt.imshow(array, cmap='winter')
    plt.title(title)
    plt.grid(False)  # Set to True if you want to see the grid lines
    plt.show()