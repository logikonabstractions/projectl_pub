import unittest
import numpy as np
import yaml
import os
import sys
from parameterized import parameterized

# Add the project root directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ProjectL.classes import Piece


class TestCubeGeneration(unittest.TestCase):
    def setUp(self):
        """Load configuration for all pieces"""
        with open("tests/test_configs_cube.yaml", 'r') as file:
            self.configs = yaml.safe_load(file)

        self.all_pieces = self.configs["pieces"]

    def _get_piece_config(self, piece_name):
        """Helper method to get piece configuration by name"""
        return next((piece for piece in self.all_pieces if piece["name"] == piece_name), None)

    def _get_expected_layouts_count(self, piece_name):
        """Return the expected number of layouts for each piece type"""
        # This mapping can be extended as needed for new piece types

        return self._get_piece_config(piece_name)["solutions"]["num_configurations"]

    def _get_expected_piece_size(self, piece_name):
        """Return the expected number of cells in the piece"""
        # Map piece names to their sizes (number of 1s in the matrix)
        return self._get_piece_config(piece_name)["solutions"]["piece_size"]


    @parameterized.expand([
        ("corner_3",),
        ("square_1",),
        # Add more pieces as needed
    ])
    def test_cube_dimensions(self, piece_name):
        """Test that the cube has correct dimensions for each piece"""
        piece_config = self._get_piece_config(piece_name)
        self.assertIsNotNone(piece_config, f"{piece_name} configuration not found")
        piece = Piece(piece_config)

        # Check that cube was generated
        self.assertIsNotNone(piece.cube, f"Cube not generated for {piece_name}")

        # Check dimensions
        num_layouts, rows, cols = piece.cube.shape

        self.assertEqual(rows, 5, f"{piece_name} cube should have 5 rows")
        self.assertEqual(cols, 5, f"{piece_name} cube should have 5 columns")

        # Check number of layouts
        expected_count = self._get_expected_layouts_count(piece_name)
        self.assertEqual(num_layouts, expected_count,
                         f"Expected {expected_count} layouts for {piece_name}, got {num_layouts}")


    @parameterized.expand([
        ("corner_3",),
        ("square_1",),
        # Add more pieces as needed
    ])
    def test_valid_layouts(self, piece_name):
        """Test that each layout in the cube is valid"""
        piece_config = self._get_piece_config(piece_name)
        self.assertIsNotNone(piece_config, f"{piece_name} configuration not found")
        piece = Piece(piece_config)

        expected_size = self._get_expected_piece_size(piece_name)
        num_layouts = piece.cube.shape[0]

        for i in range(num_layouts):
            layout = piece.cube[i]

            # Check that layout fits within 5x5 grid
            self.assertEqual(layout.shape, (5, 5), f"Layout {i} has incorrect shape")

            # Check that layout only contains 0s and 1s
            values = np.unique(layout)
            self.assertTrue(np.all(np.isin(values, [0, 1])),
                            f"Layout {i} contains values other than 0 or 1: {values}")

            # Check the piece size
            piece_sum = np.sum(layout)
            self.assertEqual(piece_sum, expected_size,
                             f"Layout {i} has invalid total: {piece_sum} (expected {expected_size})")

    @parameterized.expand([
        ("corner_3",),
        ("square_1",),
        # Add more pieces as needed
    ])
    def test_no_duplicates(self, piece_name):
        """Test that there are no duplicate layouts in the cube"""
        piece_config = self._get_piece_config(piece_name)
        self.assertIsNotNone(piece_config, f"{piece_name} configuration not found")
        piece = Piece(piece_config)
        num_layouts = piece.cube.shape[0]

        # Compare each layout with all other layouts
        for i in range(num_layouts):
            for j in range(i + 1, num_layouts):
                layout_i = piece.cube[i]
                layout_j = piece.cube[j]

                # Check that layouts are not identical
                self.assertFalse(np.array_equal(layout_i, layout_j),
                                 f"Duplicate layouts found at indices {i} and {j}")

    @parameterized.expand([
        ("corner_3",),
        ("square_1",),
        # Add more pieces as needed
    ])
    def test_corner_3_specific_layouts(self, piece_name):
        """Additional test for corner_3 piece to check correct layouts are generated"""
        piece_config = self._get_piece_config(piece_name)
        self.assertIsNotNone(piece_config, f"{piece_name} configuration not found")
        piece = Piece(piece_config)


        expected_sum_matrix = np.array(piece_config["solutions"]["configuration_sum"])
        actual_sum_matrix = np.sum(piece.cube, axis=0)

        self.assertEqual(expected_sum_matrix.tobytes(), actual_sum_matrix.tobytes() ,
                         f"Expected {expected_sum_matrix} unique layouts, but got {actual_sum_matrix}")

if __name__ == '__main__':
    unittest.main()
