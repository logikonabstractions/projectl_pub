"""Shared loaders for the parametrized piece/card test suites.

The canonical game data lives in pieces_list.yaml and cards_list.yaml (authored in the
project's own schema). These helpers read those files and adapt each entry into the
config shape the production Piece/Card classes expect, so the tests exercise the real
classes against the real data. Ground-truth (expected) values live in tests/fixtures/.

Tests call the *_names() helpers at import time to build their @parameterized.expand
lists, so adding a piece/card to the list files automatically adds coverage.

Schema adaptation:
  pieces_list.yaml: {id, name, cells, matrix(<=5x5 ints)} -> {id, name, level, cells, shape(5x5 ints)}
  cards_list.yaml:  {id, name, rewards{points, piece}, matrix(5x5 ints)}
                    -> {id, name, mask(5x5 bool), reward{points, piece}}
Pieces are keyed by name (unique); cards are keyed by id (names are non-unique / sometimes blank).
"""
import os

import numpy as np
import yaml

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

PIECES_LIST_YAML = os.path.join(PROJECT_ROOT, "pieces_list.yaml")
CARDS_LIST_YAML = os.path.join(PROJECT_ROOT, "cards_list.yaml")
PIECES_EXPECTED_YAML = os.path.join(FIXTURES_DIR, "pieces_expected.yaml")
CARDS_EXPECTED_YAML = os.path.join(FIXTURES_DIR, "cards_expected.yaml")


def load_yaml(path):
    """Load and return the parsed contents of a YAML file."""
    with open(path, "r") as file:
        return yaml.safe_load(file)


def _pad_to_5x5(matrix):
    """Place an arbitrary (<=5x5) int matrix into the top-left of a 5x5 grid."""
    grid = np.zeros((5, 5), dtype=int)
    src = np.array(matrix, dtype=int)
    grid[: src.shape[0], : src.shape[1]] = src
    return grid.tolist()


def load_pieces():
    """Return piece definition dicts (production Piece schema) from pieces_list.yaml."""
    raw = load_yaml(PIECES_LIST_YAML)["pieces"]
    return [
        {"id": p["id"], "name": p["name"], "level": p["cells"], "cells": p["cells"], "shape": _pad_to_5x5(p["matrix"])}
        for p in raw
    ]


def load_cards():
    """Return card definition dicts (production Card schema) from cards_list.yaml."""
    raw = load_yaml(CARDS_LIST_YAML)["cards"]
    cards = []
    for c in raw:
        mask = [[bool(value) for value in row] for row in c["matrix"]]
        reward = {"points": c["rewards"]["points"], "piece": c["rewards"]["piece"]}
        cards.append({"id": c["id"], "name": c.get("name") or c["id"], "mask": mask, "reward": reward})
    return cards


def pieces_by_name():
    """Return {name: piece_config} for all pieces."""
    return {piece["name"]: piece for piece in load_pieces()}


def cards_by_id():
    """Return {id: card_config} for all cards."""
    return {card["id"]: card for card in load_cards()}


def piece_names():
    """Return [(name,), ...] for feeding @parameterized.expand over all pieces."""
    return [(piece["name"],) for piece in load_pieces()]


def card_ids():
    """Return [(id,), ...] for feeding @parameterized.expand over all cards."""
    return [(card["id"],) for card in load_cards()]


def load_expected(kind):
    """Load a ground-truth fixture. kind is 'pieces' or 'cards'."""
    paths = {"pieces": PIECES_EXPECTED_YAML, "cards": CARDS_EXPECTED_YAML}
    return load_yaml(paths[kind])
