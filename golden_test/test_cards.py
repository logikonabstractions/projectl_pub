"""Parametrized verification that every card in cards_list.yaml is correctly implemented.

Each test runs once per card (keyed by id), so adding a card to cards_list.yaml +
tests/fixtures/cards_expected.yaml extends coverage automatically.

Covers: structure & reward parsing (valid mask, mask cell count, empty initial layout,
is_full False, reward points/piece) and behavioral logic (completion detection, out-of-mask
and overlap rejection) derived from each mask.

Note on reward_piece: cards reward a named piece (e.g. P1). The production loader does not
yet resolve a piece reference into a real Piece, so this check currently FAILS by design --
it is the fail-first signal for the deferred reward-resolution feature.
"""
import os
import sys
import unittest

import numpy as np
from parameterized import parameterized

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.dirname(__file__))

from ProjectL.classes import Card
import conftest_helpers as helpers

CARD_IDS = helpers.card_ids()
DEFAULT_REWARD_PIECE = "square_1"


class TestCards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.configs = helpers.cards_by_id()
        cls.expected = helpers.load_expected("cards")

    def _card(self, card_id):
        return Card(self.configs[card_id])

    def _expected(self, card_id):
        self.assertIn(card_id, self.expected, f"No ground truth for {card_id} in cards_expected.yaml")
        return self.expected[card_id]

    @parameterized.expand(CARD_IDS)
    def test_mask_valid(self, card_id):
        """The mask is a 5x5 boolean array."""
        card = self._card(card_id)
        self.assertEqual(card.mask.shape, (5, 5))
        self.assertEqual(card.mask.dtype, np.bool_)

    @parameterized.expand(CARD_IDS)
    def test_mask_cell_count(self, card_id):
        """The mask has the expected number of playable cells."""
        card = self._card(card_id)
        expected_count = self._expected(card_id)["mask_cell_count"]
        self.assertEqual(int(card.mask.sum()), expected_count)

    @parameterized.expand(CARD_IDS)
    def test_initial_state(self, card_id):
        """A fresh card starts with an empty 5x5 layout and is_full False."""
        card = self._card(card_id)
        self.assertEqual(card.layout.shape, (5, 5))
        self.assertTrue(np.all(card.layout == 0))
        self.assertFalse(card.is_full)

    @parameterized.expand(CARD_IDS)
    def test_reward_points(self, card_id):
        """The reward awards the expected number of points."""
        card = self._card(card_id)
        self.assertEqual(card.reward.points, self._expected(card_id)["reward_points"])

    @parameterized.expand(CARD_IDS)
    def test_reward_piece(self, card_id):
        """The reward resolves to the expected piece.

        A null reward yields the default square; otherwise the reference (e.g. P1) must
        resolve to a real Piece whose name matches the fixture. getattr keeps this a clean
        failure (not an error) while resolution is unimplemented and reward.piece is a raw string.
        """
        card = self._card(card_id)
        actual = getattr(card.reward.piece, "name", card.reward.piece)
        expected_piece = self._expected(card_id)["reward_piece"]
        if expected_piece is None:
            self.assertEqual(actual, DEFAULT_REWARD_PIECE)
        else:
            self.assertEqual(actual, expected_piece)

    @parameterized.expand(CARD_IDS)
    def test_completion_detection(self, card_id):
        """Filling exactly the mask region marks the card full and matches the mask."""
        card = self._card(card_id)
        filled = card.place_piece(card.mask.astype(int))
        self.assertTrue(filled, f"{card_id}: filling the mask region should be a valid placement")
        self.assertTrue(card.is_full, f"{card_id}: is_full should be True once the mask is filled")
        np.testing.assert_array_equal(card.layout, card.mask.astype(int))

    @parameterized.expand(CARD_IDS)
    def test_rejects_out_of_mask(self, card_id):
        """A placement touching a non-playable cell is rejected."""
        card = self._card(card_id)
        outside = np.argwhere(~card.mask)
        if outside.size == 0:
            self.skipTest(f"{card_id}: mask covers the whole grid, no out-of-mask cell to test")
        row, col = outside[0]
        config = np.zeros((5, 5), dtype=int)
        config[row, col] = 1
        self.assertFalse(card.place_piece(config), f"{card_id}: out-of-mask placement should be rejected")
        self.assertFalse(card.is_full)

    @parameterized.expand(CARD_IDS)
    def test_rejects_overlap(self, card_id):
        """Placing onto an already-occupied cell is rejected (no double occupation)."""
        card = self._card(card_id)
        row, col = np.argwhere(card.mask)[0]
        config = np.zeros((5, 5), dtype=int)
        config[row, col] = 1
        self.assertTrue(card.place_piece(config), f"{card_id}: first placement on a mask cell should succeed")
        self.assertFalse(card.place_piece(config), f"{card_id}: overlapping placement should be rejected")

    def test_fixture_coverage(self):
        """Every card in cards_list.yaml has a ground-truth entry in cards_expected.yaml."""
        missing = [card_id for (card_id,) in CARD_IDS if card_id not in self.expected]
        self.assertEqual(missing, [], f"Missing ground truth for: {missing}")


if __name__ == "__main__":
    unittest.main()
