import matplotlib.pyplot as plt
import numpy as np
import yaml
import os
import sys

# Add the project root directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ProjectL.classes import Piece


def visualize_cube_layouts(piece_name):
    """Visualize all layouts in the cube for a given piece"""
    # Load configuration
    with open("configs.yaml", 'r') as file:
        configs = yaml.safe_load(file)

    # Find the piece config
    piece_config = next((piece for piece in configs["pieces"] if piece["name"] == piece_name), None)
    if not piece_config:
        print(f"Piece '{piece_name}' not found in configs")
        return

    # Create and generate cube for the piece
    piece = Piece(piece_config)

    # Get number of layouts
    num_layouts = piece.cube.shape[0]
    print(f"Piece '{piece_name}' has {num_layouts} layouts")

    # Create a figure with subplots
    rows = (num_layouts + 3) // 4  # Calculate rows needed
    fig, axes = plt.subplots(rows, 4, figsize=(16, 4 * rows))

    # Flatten axes for easy iteration
    axes = axes.flatten()

    for i in range(num_layouts):
        ax = axes[i]
        layout = piece.cube[i]

        # Create heatmap
        im = ax.imshow(layout, cmap='binary', vmin=0, vmax=1)

        # Add a grid
        ax.set_xticks(np.arange(-.5, 5, 1), minor=True)
        ax.set_yticks(np.arange(-.5, 5, 1), minor=True)
        ax.grid(which="minor", color="black", linestyle='-', linewidth=0.5)

        # Remove ticks
        ax.tick_params(axis='both', which='both', length=0)

        # Set title
        ax.set_title(f"Layout {i + 1}")

    # Hide unused subplots
    for i in range(num_layouts, len(axes)):
        axes[i].axis('off')

    plt.tight_layout()
    plt.suptitle(f"All layouts for piece '{piece_name}'", fontsize=16, y=1.02)
    plt.savefig(f'/tmp/outputs/{piece_name}_layouts.png', dpi=150, bbox_inches='tight')
    plt.close()

    # Also create a unified view of all layouts stacked
    summed_matrix = np.sum(piece.cube, axis=0)
    plt.figure(figsize=(8, 8))
    plt.imshow(summed_matrix, cmap='viridis')
    plt.colorbar(label='Number of layouts using this cell')
    plt.grid(which="both", color="black", linestyle='-', linewidth=0.5, alpha=0.3)
    plt.title(f"Summed layouts for '{piece_name}'")
    plt.savefig(f'/tmp/outputs/{piece_name}_summed.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Visualizations saved to /tmp/outputs/{piece_name}_layouts.png and {piece_name}_summed.png")


if __name__ == "__main__":
    # Visualize the corner_3 piece
    visualize_cube_layouts("corner_3")

    # Uncomment to visualize other pieces
    # visualize_cube_layouts("square_1")
    # visualize_cube_layouts("line_2")
    # visualize_cube_layouts("line_3")
    # visualize_cube_layouts("big_square_4")
