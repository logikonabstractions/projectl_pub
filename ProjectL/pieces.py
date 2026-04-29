import random

import numpy as np

from ProjectL.utils.utils import plot_image


class Piece:
    """describes a Piece that a Player can place on a Card"""

    def __init__(self, configs = None):
        self.level = None
        self.shape = None
        self.name = None
        self.configurations_array = []
        self.cube = None
        if configs:
            self.level = configs["level"]
            self.shape = np.array(configs["shape"])
            self.name = configs["name"]
            self.configurations_array = []
            self.cube = None
            self.generate_cube()


    def generate_cube(self):
        """ To be efficient in computation, we represent all the possible positions of a piece within a card as a 3D matrix.

            The axis=0 of the matrix (numpy array) represents all the possible configuration of that Piece. This method is responsible for generating all that. A valid cube must:
            1 - contain only layouts laying entirely within a card (5x5)
            2 - contain only continuous piece position (cannot overflow or wrap around)
            3 - only contain 0,1 values where 1 == a square occupied by the piecce and 0 == not occupied
            4 - all possible translations AND rotations possible must be represented by 1 slice along axis 0
            5 - there must be no duplicated layouts
        """
        minimal_shape = self.get_minimal_shape(self.shape)

        rotations = [
            minimal_shape,  # 0° (original)
            np.rot90(minimal_shape, 1),  # 90°
            np.rot90(minimal_shape, 2),  # 180°
            np.rot90(minimal_shape, 3)  # 270°
        ]

        configurations_arrays = []
        for rotated_shape in rotations:
            configurations_arrays.extend(self.generate_configurations(rotated_shape))
        unique_configs = self.remove_duplicates(configurations_arrays)
        self.cube = np.stack(unique_configs, axis=0)

    def remove_duplicates(self, configurations_arrays):
        """ ensures we have no duplicates in the configurations """
        unique_configs = []
        for config in configurations_arrays:
            if not any(np.array_equal(config, existing) for existing in unique_configs):
                unique_configs.append(config)
        return unique_configs

    def get_minimal_shape(self, array):
        """Extract the minimal bounding box of the non-zero elements in the array."""
        rows = np.any(array, axis=1)
        cols = np.any(array, axis=0)
        if not np.any(rows) or not np.any(cols):
            return np.array([])  # Empty shape
        ymin, ymax = np.where(rows)[0][[0, -1]]
        xmin, xmax = np.where(cols)[0][[0, -1]]
        return array[ymin:ymax + 1, xmin:xmax + 1]

    def generate_configurations(self, minimal_shape):
        """For a given (rotated) minimal shape, generate all possible translations within a 5x5 grid."""
        if minimal_shape.size == 0:
            return []  # No configurations for empty shape

        h, w = minimal_shape.shape
        configurations = []

        for i in range(5 - h + 1):
            for j in range(5 - w + 1):
                config = np.zeros((5, 5), dtype=int)
                config[i:i + h, j:j + w] = minimal_shape
                configurations.append(config)

        return configurations


    def plot_configurations(self):
        """ for debug - plots the configurations for our piece """
        for idx, arr in enumerate(self.configurations_array):
            plot_image(arr, f"Configuration {idx}/{len(self.configurations_array)}")

    def validate_cube(self):
        summed_matrix = np.sum(self.cube, axis=0)
        # plot_image(summed_matrix, self.name)

    def __repr__(self):
        return f"{self.name} - lvl {self.level}"


class PieceSquare(Piece):
    """ a subclass for easy access to a basic piece, e.g. a simpe square"""

    def __init__(self):
        configs = {"name": "square_1", "level": 1, "shape": [[1, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]}
        super().__init__(configs)
