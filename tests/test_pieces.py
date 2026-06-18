"""Parametrized verification that every piece in pieces_list.yaml is correctly implemented.

Each test runs once per piece (via @parameterized.expand over the names loaded from
pieces_list.yaml), so adding a piece to pieces_list.yaml + tests/fixtures/pieces_expected.yaml
automatically extends coverage with no change to this file.
"""
import os
import sys
import unittest

import numpy as np
from parameterized import parameterized

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.dirname(__file__))

from ProjectL.classes import Piece
import conftest_helpers as helpers

PIECE_NAMES = helpers.piece_names()


class TestPieces(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.configs = helpers.pieces_by_name()
        cls.expected = helpers.load_expected("pieces")

    def _piece(self, piece_name):
        return Piece(self.configs[piece_name])

    def _expected(self, piece_name):
        self.assertIn(piece_name, self.expected, f"No ground truth for {piece_name} in pieces_expected.yaml")
        return self.expected[piece_name]

    @parameterized.expand(PIECE_NAMES)
    def test_cube_shape(self, piece_name):
        """The cube has shape (num_configurations, 5, 5)."""
        piece = self._piece(piece_name)
        expected_count = self._expected(piece_name)["num_configurations"]
        self.assertEqual(piece.cube.shape, (expected_count, 5, 5))

    @parameterized.expand(PIECE_NAMES)
    def test_layouts_binary(self, piece_name):
        """Every layout contains only 0s and 1s."""
        piece = self._piece(piece_name)
        values = np.unique(piece.cube)
        self.assertTrue(np.all(np.isin(values, [0, 1])), f"{piece_name} cube has non-binary values: {values}")

    @parameterized.expand(PIECE_NAMES)
    def test_piece_size(self, piece_name):
        """Every layout occupies exactly piece_size cells."""
        piece = self._piece(piece_name)
        expected_size = self._expected(piece_name)["piece_size"]
        sums = piece.cube.sum(axis=(1, 2))
        self.assertTrue(np.all(sums == expected_size), f"{piece_name} has layouts not summing to {expected_size}: {np.unique(sums)}")

    @parameterized.expand(PIECE_NAMES)
    def test_no_duplicates(self, piece_name):
        """No two layouts in the cube are identical."""
        piece = self._piece(piece_name)
        flattened = piece.cube.reshape(piece.cube.shape[0], -1)
        unique_count = np.unique(flattened, axis=0).shape[0]
        self.assertEqual(unique_count, piece.cube.shape[0], f"{piece_name} cube contains duplicate layouts")

    @parameterized.expand(PIECE_NAMES)
    def test_configuration_fingerprint(self, piece_name):
        """The cube summed along axis 0 matches the expected fingerprint (pins every placement)."""
        piece = self._piece(piece_name)
        expected_sum = np.array(self._expected(piece_name)["configuration_sum"])
        actual_sum = piece.cube.sum(axis=0)
        np.testing.assert_array_equal(actual_sum, expected_sum, f"{piece_name} configuration_sum mismatch")

    def test_fixture_coverage(self):
        """Every piece in pieces.yaml has a ground-truth entry in pieces_expected.yaml."""
        missing = [name for (name,) in PIECE_NAMES if name not in self.expected]
        self.assertEqual(missing, [], f"Missing ground truth for: {missing}")


if __name__ == "__main__":
    unittest.main()
