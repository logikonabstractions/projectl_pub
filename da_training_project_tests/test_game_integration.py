import unittest
import yaml
import os
import sys
import random
import logging
import subprocess

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ProjectL.game_objects import GameManager, Player, GameState
from ProjectL.strategies import RandomStrat, BasicStrat, TakePieceStrat
from ProjectL.actions import TakePiece, PlacePiece, TakeCard, UpgradePiece, Master
from ProjectL.pieces import Piece, PieceSquare
from ProjectL.card import Card


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
STRATEGY_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'strategy_configs.yaml')
DEFAULT_CONFIG_PATH = os.path.join(REPO_ROOT, 'configs.yaml')


def get_test_config():
    with open(STRATEGY_CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


def get_silent_logger():
    logger = logging.getLogger('test_silent')
    logger.handlers = []
    logger.addHandler(logging.NullHandler())
    logger.setLevel(logging.CRITICAL)
    return logger


def _player_strategies(gm):
    return {type(gm.player_1.strategy), type(gm.player_2.strategy)}


class TestGameInitialization(unittest.TestCase):

    def setUp(self):
        self.configs = get_test_config()
        self.logger = get_silent_logger()

    def test_game_initializes_with_two_players(self):
        gm = GameManager(self.configs, self.logger)
        self.assertIsNotNone(gm.player_1)
        self.assertIsNotNone(gm.player_2)

    def test_game_max_turns_is_10(self):
        gm = GameManager(self.configs, self.logger)
        self.assertEqual(gm.max_turns, 10)

    def test_player_names_match_config(self):
        gm = GameManager(self.configs, self.logger)
        config_names = {p['name'] for p in self.configs['players']}
        actual_names = {gm.player_1.name, gm.player_2.name}
        self.assertEqual(actual_names, config_names)

    def test_one_player_has_random_one_has_basic(self):
        gm = GameManager(self.configs, self.logger)
        self.assertEqual(_player_strategies(gm), {RandomStrat, BasicStrat})

    def test_piece_bank_initialized(self):
        gm = GameManager(self.configs, self.logger)
        self.assertTrue(len(gm.piece_bank) > 0)

    def test_cards_initialized(self):
        gm = GameManager(self.configs, self.logger)
        self.assertTrue(len(gm.cards) > 0)


class TestGameRun(unittest.TestCase):

    def setUp(self):
        self.configs = get_test_config()
        self.logger = get_silent_logger()

    def test_game_runs_without_crashing(self):
        gm = GameManager(self.configs, self.logger)
        try:
            gm.run()
        except Exception as e:
            self.fail(f"Game crashed with exception: {e}")

    def test_game_plays_all_configured_turns(self):
        gm = GameManager(self.configs, self.logger)
        gm.run()
        self.assertGreater(gm.game_state.current_turn_number, gm.max_turns)

    def test_game_terminates(self):
        gm = GameManager(self.configs, self.logger)
        gm.run()
        self.assertFalse(gm.is_game_running)


class TestStrategyConfigLoading(unittest.TestCase):

    def setUp(self):
        self.configs = get_test_config()

    def test_strategy_configs_file_exists(self):
        self.assertTrue(os.path.exists(STRATEGY_CONFIG_PATH))

    def test_strategy_config_has_players_with_strategy_field(self):
        self.assertIn('players', self.configs)
        for player in self.configs['players']:
            self.assertIn('strategy', player)

    def test_strategy_config_specifies_random_and_basic(self):
        strategies = [p['strategy'] for p in self.configs['players']]
        self.assertIn('random', strategies)
        self.assertIn('basic', strategies)


class TestRandomStrategy(unittest.TestCase):

    def setUp(self):
        self.logger = get_silent_logger()
        self.configs = get_test_config()
        self.gm = GameManager(self.configs, self.logger)
        self.player = Player(name="TestRandom", logger=self.logger, game_manager=self.gm)
        self.strategy = RandomStrat(player=self.player, logger=self.logger)
        self.player.set_strategy(self.strategy)

    def test_random_strategy_chooses_from_action_pool(self):
        action = self.strategy.choose_action()
        valid_action_types = (TakePiece, PlacePiece, UpgradePiece, TakeCard, Master)
        self.assertIsInstance(action, valid_action_types)

    def test_random_strategy_uses_all_actions_over_many_calls(self):
        # Give the player some pieces so UpgradePiece construction does not crash
        # while we sample (this isolates the choice distribution from the bug
        # exercised in TestUpgradePieceBug).
        self.player.pieces = [PieceSquare() for _ in range(3)]
        action_types_seen = set()
        for _ in range(500):
            try:
                action = self.strategy.choose_action()
                action_types_seen.add(type(action))
            except Exception:
                pass
        self.assertEqual(
            action_types_seen,
            {TakePiece, PlacePiece, UpgradePiece, TakeCard, Master},
            f"Random strategy should sample every action type; got {action_types_seen}",
        )

    def test_random_strategy_play_turn_completes(self):
        try:
            self.strategy.play_turn()
        except Exception as e:
            self.fail(f"RandomStrat play_turn crashed: {e}")


class TestBasicStrategy(unittest.TestCase):
    """Verifies basic-strategy priority order from problem.txt:
    1) place if possible, 2) take card if placing fails, 3) take piece.
    """

    def setUp(self):
        self.logger = get_silent_logger()
        self.configs = get_test_config()
        self.gm = GameManager(self.configs, self.logger)
        self.player = Player(name="TestBasic", logger=self.logger, game_manager=self.gm)
        self.strategy = BasicStrat(player=self.player, logger=self.logger)
        self.player.set_strategy(self.strategy)

    def test_priority_1_place_when_possible(self):
        self.player.pieces = [PieceSquare()]
        self.player.cards = [Card()]
        action = self.strategy._determine_best_action()
        self.assertIsInstance(action, PlacePiece)

    def test_priority_2_take_card_when_place_fails(self):
        # No pieces -> place is impossible. Take-card is valid -> must be TakeCard.
        self.player.pieces = []
        self.player.cards = []
        action = self.strategy._determine_best_action()
        self.assertIsInstance(action, TakeCard)

    def test_priority_3_take_piece_when_place_and_take_card_unavailable(self):
        # No pieces (place fails) and take-card unavailable in current rules
        # (player already holds a card) -> falls through to TakePiece.
        self.player.pieces = []
        self.player.cards = [Card()]
        action = self.strategy._determine_best_action()
        self.assertIsInstance(action, TakePiece)

    def test_basic_strategy_play_turn_completes(self):
        try:
            self.strategy.play_turn()
        except Exception as e:
            self.fail(f"BasicStrat play_turn crashed: {e}")


class TestActionEffects(unittest.TestCase):
    """Acceptance #5: action effects must be observable end-to-end."""

    def setUp(self):
        self.logger = get_silent_logger()
        self.configs = get_test_config()
        self.gm = GameManager(self.configs, self.logger)

    def test_take_piece_adds_to_player_pieces(self):
        player = Player(name="TestPlayer", logger=self.logger, game_manager=self.gm)
        player.pieces = []
        action = TakePiece(pieces=player.pieces, game_manager=self.gm)
        self.assertTrue(action.is_action_valid())
        self.assertTrue(action.perform_action())
        self.assertEqual(len(player.pieces), 1)

    def test_take_card_adds_to_player_cards(self):
        player = Player(name="TestPlayer", logger=self.logger, game_manager=self.gm)
        player.cards = []
        action = TakeCard(cards=player.cards)
        self.assertTrue(action.is_action_valid())
        action.perform_action()
        self.assertEqual(len(player.cards), 1)

    def test_place_piece_adds_piece_to_card(self):
        card = Card()
        piece = PieceSquare()
        # Pick a cell that is inside the card's mask to guarantee a valid placement.
        valid_row, valid_col = np.argwhere(card.mask)[0]
        configuration = np.zeros((5, 5), dtype=int)
        configuration[valid_row, valid_col] = 1
        action = PlacePiece(piece=piece, card=card, pieces=[piece])
        self.assertTrue(action.is_action_valid())
        result = action.perform_action(configuration=configuration)
        self.assertTrue(result)
        self.assertEqual(card.layout[valid_row, valid_col], 1)

    def test_place_piece_removes_from_player_pieces(self):
        player = Player(name="TestPlayer", logger=self.logger, game_manager=self.gm)
        player.pieces = [PieceSquare(), PieceSquare()]
        player.cards = [Card()]
        strategy = BasicStrat(player=player, logger=self.logger)
        player.set_strategy(strategy)
        initial_count = len(player.pieces)
        # Repeat until a placement succeeds; PlacePiece picks configurations at
        # random, so a single attempt may land off-mask.
        random.seed(0)
        succeeded = any(strategy._try_place_piece() for _ in range(50))
        self.assertTrue(succeeded, "Could not achieve a valid placement in 50 attempts")
        self.assertEqual(len(player.pieces), initial_count - 1)


class TestGameState(unittest.TestCase):

    def setUp(self):
        self.logger = get_silent_logger()

    def test_game_state_tracks_turns(self):
        gs = GameState(current_turn_number=1, max_turns=10, logger=self.logger)
        self.assertEqual(gs.current_turn_number, 1)
        gs.next_turn()
        self.assertEqual(gs.current_turn_number, 2)

    def test_game_state_ends_at_max_turns(self):
        gs = GameState(current_turn_number=10, max_turns=10, logger=self.logger)
        self.assertTrue(gs.is_game_running())
        gs.next_turn()
        self.assertFalse(gs.is_game_running())


class TestCommandLineConfigLoading(unittest.TestCase):
    """Acceptance: the strategy config must be loadable via a command-line
    argument, leaving the default configs.yaml untouched."""

    def test_strategy_configs_yaml_is_separate_from_default(self):
        with open(DEFAULT_CONFIG_PATH, 'r') as f:
            default_config = yaml.safe_load(f)
        with open(STRATEGY_CONFIG_PATH, 'r') as f:
            strategy_config = yaml.safe_load(f)
        self.assertNotEqual(default_config, strategy_config)

    def test_strategy_config_has_10_max_turns(self):
        configs = get_test_config()
        self.assertEqual(configs['game_parameters']['max_turns'], 10)

    def test_main_runs_with_cli_config_argument(self):
        """Run main.py with a CLI argument pointing at strategy_configs.yaml
        and verify the alternate config (max_turns=10) was actually used.

        Expected invocation form (any equivalent CLI parsing is acceptable):
            python -m ProjectL.main --config da_training_project_tests/strategy_configs.yaml
        """
        env = os.environ.copy()
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')
        result = subprocess.run(
            [sys.executable, '-m', 'ProjectL.main', '--config', STRATEGY_CONFIG_PATH],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(
            result.returncode, 0,
            f"main.py exited non-zero.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        combined = result.stdout + result.stderr
        # Default configs.yaml has max_turns=50; strategy_configs.yaml has 10.
        # Presence of "/10" (turn-progress repr) and absence of "/50" confirms
        # the alternate config was actually loaded rather than the default.
        self.assertIn("/10", combined,
                      f"Expected progress against max_turns=10 in output:\n{combined}")
        self.assertNotIn("/50", combined,
                         f"Default max_turns=50 leaked into output:\n{combined}")


class TestUpgradePieceBug(unittest.TestCase):
    """Regression: UpgradePiece.__init__ calls random.choice(self.pieces) when
    no piece is supplied. With an empty or missing pieces list this raises an
    IndexError/TypeError, which surfaces intermittently during a RandomStrat
    turn whenever the player happens to hold no pieces. Construction must be
    safe for these inputs."""

    def test_upgrade_piece_init_with_empty_pieces_list(self):
        try:
            UpgradePiece(pieces=[])
        except (IndexError, TypeError) as e:
            self.fail(f"UpgradePiece(pieces=[]) crashed: {type(e).__name__}: {e}")

    def test_upgrade_piece_init_with_no_pieces_argument(self):
        try:
            UpgradePiece()
        except (IndexError, TypeError) as e:
            self.fail(f"UpgradePiece() crashed: {type(e).__name__}: {e}")

    def test_random_strategy_play_turn_with_no_pieces_does_not_crash(self):
        """End-to-end exercise of the intermittent failure: a RandomStrat turn
        for a player holding no pieces must not crash on UpgradePiece sampling."""
        logger = get_silent_logger()
        configs = get_test_config()
        gm = GameManager(configs, logger)
        player = Player(name="NoPieces", logger=logger, game_manager=gm)
        player.pieces = []
        player.cards = []
        strategy = RandomStrat(player=player, logger=logger)
        player.set_strategy(strategy)
        # Many iterations to make the random path exercise UpgradePiece selection.
        random.seed(1234)
        for _ in range(50):
            try:
                strategy.play_turn()
            except (IndexError, TypeError) as e:
                self.fail(f"RandomStrat.play_turn crashed with empty pieces: "
                          f"{type(e).__name__}: {e}")
            player.pieces = []  # reset to keep exercising the empty-pieces path


if __name__ == '__main__':
    unittest.main()
