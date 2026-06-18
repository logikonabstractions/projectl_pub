"""Production loaders for the canonical game data.

The canonical game data lives in pieces_list.yaml and cards_list.yaml (authored in the
project's own schema). These helpers read those files and adapt each entry into the config
shape the production Piece/Card classes expect, so the runtime (and the test suite) drive the
real classes from the real data.

Schema adaptation:
  pieces_list.yaml: {id, name, cells, matrix(<=5x5 ints)} -> {id, name, level, cells, shape(5x5 ints)}
  cards_list.yaml:  {id, name, rewards{points, piece}, matrix(5x5 ints)}
                    -> {id, name, mask(5x5 bool), reward{points, piece}}
Pieces are keyed by name (unique); cards reference a reward piece by id (P1..P10). The
reference is resolved into a real Piece by resolve_reward_piece (used by Reward), so a card
config can carry either the raw id or an already-resolved Piece.
"""
import os

import numpy as np
import yaml

from ProjectL.pieces import Piece

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PIECES_LIST_YAML = os.path.join(PROJECT_ROOT, "pieces_list.yaml")
CARDS_LIST_YAML = os.path.join(PROJECT_ROOT, "cards_list.yaml")

# Lazily-built caches so piece configs are parsed once and Piece prototypes (which build their
# rotation/translation cube) are created once per id rather than per card.
_PIECE_CONFIG_BY_ID = None
_PIECE_PROTOTYPE_BY_ID = {}


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


def load_pieces(path=PIECES_LIST_YAML):
    """Return piece definition dicts (production Piece schema) from pieces_list.yaml."""
    raw = load_yaml(path)["pieces"]
    return [
        {"id": p["id"], "name": p["name"], "level": p["cells"], "cells": p["cells"], "shape": _pad_to_5x5(p["matrix"])}
        for p in raw
    ]


def load_cards(path=CARDS_LIST_YAML):
    """Return card definition dicts (production Card schema) from cards_list.yaml.

    The reward keeps the raw piece reference (e.g. "P1"); Reward resolves it into a real Piece
    via resolve_reward_piece when the card is constructed.
    """
    raw = load_yaml(path)["cards"]
    cards = []
    for c in raw:
        mask = [[bool(value) for value in row] for row in c["matrix"]]
        reward = {"points": c["rewards"]["points"], "piece": c["rewards"]["piece"]}
        cards.append({"id": c["id"], "name": c.get("name") or c["id"], "mask": mask, "reward": reward})
    return cards


def piece_config_by_id(path=PIECES_LIST_YAML):
    """Return (and cache) {id: piece_config} for all pieces in pieces_list.yaml."""
    global _PIECE_CONFIG_BY_ID
    if _PIECE_CONFIG_BY_ID is None:
        _PIECE_CONFIG_BY_ID = {config["id"]: config for config in load_pieces(path)}
    return _PIECE_CONFIG_BY_ID


def resolve_reward_piece(reference):
    """Resolve a card's reward piece reference into a real Piece (or None).

    reference may be None (-> None, so Reward falls back to its default), an already-resolved
    Piece (-> returned unchanged), or a piece id string such as "P1" (-> the matching Piece).
    An unknown id resolves to None. Prototypes are cached and reused across cards.
    """
    if reference is None or isinstance(reference, Piece):
        return reference
    if reference not in _PIECE_PROTOTYPE_BY_ID:
        config = piece_config_by_id().get(reference)
        _PIECE_PROTOTYPE_BY_ID[reference] = Piece(configs=config) if config else None
    return _PIECE_PROTOTYPE_BY_ID[reference]
