import string
import random
import logging

from ProjectL.pieces import Piece, PieceSquare
from ProjectL.card import Card
from ProjectL.actions import TakePiece, PlacePiece, TakeCard
from ProjectL.strategies import Strategy, RandomStrat, TakePieceStrat, BasicStrat


class GameState:
    """ encapsulates the current state of a game """

    def __init__(self, current_turn_number=1, max_turns=2, logger=None):
        self.current_turn_number = current_turn_number
        self.max_turns = max_turns
        self.logger = logger or logging.getLogger('projectL')

    def next_turn(self):
        """ """
        self.current_turn_number += 1
        self.logger.debug(f"{self}",
                          extra={"normal": False})

    def is_game_running(self):
        """ checks if the game is running or over"""
        is_running = self.current_turn_number <= self.max_turns
        if not is_running:
            self.logger.info(f"Game over: reached maximum turns {self.max_turns}",
                             extra={"normal": True})
        return is_running

    def __repr__(self):
        return f"Game progress: {self.current_turn_number}/{self.max_turns}"

class GameManager:
    """ the main game engine that runs the game. """

    def __init__(self, configs_dict, logger=None):
        self.configs = configs_dict
        self.configs_pieces = configs_dict["pieces"]
        self.configs_cards = configs_dict["cards"]
        self.logger = logger or logging.getLogger('projectL')
        self.game_state = GameState(current_turn_number=1, max_turns=configs_dict["game_parameters"]["max_turns"], logger=self.logger)

        self.pieces = []
        self.piece_bank = {}
        self.actions = [TakePiece, PlacePiece, TakeCard]
        self.cards = []

        # players        TODO: ugly, refactor & makes a more robust initialization
        self.player_1 = Player(name=configs_dict["players"][0]["name"], actions=self.actions, logger=self.logger, game_manager=self)
        self.player_1.set_strategy(TakePieceStrat(player=self.player_1, logger=self.logger))
        self.player_2 = Player(name=configs_dict["players"][1]["name"], actions=self.actions, logger=self.logger, game_manager=self)
        self.player_2.set_strategy(TakePieceStrat(player=self.player_2, logger=self.logger))

        self.game_init()

    def game_init(self):
        """ setup for the beginning of the game
        """
        self.logger.debug("Initializing game", extra={"normal": False})
        self.instantiate_elements()

    def instantiate_elements(self):
        """
        """
        self.logger.debug("Creating game pieces", extra={"normal": False})
        for piece_confs in self.configs_pieces:
            piece_name = piece_confs["name"]
            level = piece_confs["level"]
            quantity = piece_confs.get("quantity", 10)

            prototype_piece = Piece(configs=piece_confs)
            self.logger.debug(f"Created piece prototype: {prototype_piece}",
                              extra={"normal": False, "verbose": True})

            self.piece_bank[piece_name] = []
            for _ in range(quantity):
                p = Piece(configs=piece_confs)
                self.piece_bank[piece_name].append(p)


        for card_confs in self.configs_cards:
            card = Card(configs=card_confs)
            self.cards.append(card)
            self.logger.debug(f"Created card: {card}",
                              extra={"normal": False, "verbose": True})

    def get_piece(self, piece_name=None):
        """Get a piece from the bank

        Args:
            piece_name: Optional name of the piece to get. If None, returns a random piece.

        Returns:
            A piece from the bank, or None if the requested piece is not available
        """
        if piece_name is None:
            available_types = [name for name, pieces in self.piece_bank.items() if pieces]
            if not available_types:
                self.logger.debug("No pieces available in the bank",
                                  extra={"normal": False})
                return None

            piece_name = random.choice(available_types)

        if piece_name not in self.piece_bank or not self.piece_bank[piece_name]:
            self.logger.debug(f"No {piece_name} pieces available in the bank",
                              extra={"normal": False})
            return None

        piece = self.piece_bank[piece_name].pop()
        self.logger.debug(f"Taking {piece_name} from bank. Remaining: {len(self.piece_bank[piece_name])}",
                          extra={"normal": False})
        return piece


    def run(self):
        """ loop that runs the game """
        self.logger.info(f"Game started with players: {self.player_1}, {self.player_2}", extra={"normal": True})

        while self.is_game_running:
            self.logger.info(f"====== Playing turn {self.current_turn_number}======",  extra={"normal": True})

            self.logger.debug(f"{self.player_1.name}'s turn",  extra={"normal": False})
            self.player_1.play_turn()

            self.logger.debug(f"{self.player_2.name}'s turn", extra={"normal": False})
            self.player_2.play_turn()

            if self.current_turn_number % 10 == 0:
                self.logger.info(f"Player state: {self.player_1}", extra={"normal": True})
                self.logger.info(f"Player state: {self.player_2}", extra={"normal": True})
            self.game_state.next_turn()

        self.logger.info("Game ended after %d turns", self.current_turn_number - 1, extra={"normal": True})

    @property
    def is_game_running(self):
        """ checks if the game is running or over"""
        is_running = self.current_turn_number <= self.max_turns
        return is_running

    @property
    def current_turn_number(self):
        return self.game_state.current_turn_number

    @property
    def max_turns(self):
        return self.configs["game_parameters"]["max_turns"]


class Player:
    """ a class that describes a player """

    def __init__(self, name=None, cards=None, pieces=None, actions=None, strategy=None, logger=None, game_manager=None, **kwargs):
        self.logger = logger or logging.getLogger('projectL')

        self.name = name if name is not None else self.generate_random_name()
        self.actions_left = 3
        self.game_manager = game_manager

        self.cards = cards if cards else []
        self.full_cards = []
        self.pieces = pieces if pieces else self.get_initial_pieces()
        self.kwargs = kwargs

        self.strategy = strategy if strategy else RandomStrat(player=self, logger=self.logger)

        self.logger.debug("Player %s initialized", self.name, extra={"normal": False})

    def play_turn(self):
        """  delegates the playing to the strategy """
        self.logger.debug(f"{self.name} is playing their turn",  extra={"normal": False})
        self.logger.debug(f"Pieces in the bank: {len(self.game_manager.pieces)}",  extra={"normal": False})
        return self.strategy.play_turn()

    def __repr__(self):
        return f"Name: {self.name} " \
               f"pieces: {self.pieces} cards: {self.cards}"

    def generate_random_name(self, length=5):
        """ just for fun - generates random names to players if none assigned """
        chars = string.ascii_lowercase
        name = ''.join(random.choice(chars) for _ in range(length))
        self.logger.debug(f"Generated random name: {self.name}", extra={"normal": False, "verbose": True})
        return name

    def get_initial_pieces(self):
        self.logger.debug(f"Getting initial pieces for {self.name}", extra={"normal": False, "verbose": True})
        if self.game_manager:
            piece = self.game_manager.get_piece("square_1")
            return [piece] if piece else []
        return [PieceSquare()]  # Fallback

    def set_strategy(self, strategy):
        self.logger.debug(f"Setting strategy for {self.name}",  extra={"normal": False})
        self.strategy = strategy
        self.strategy.player = self
        if hasattr(strategy, 'logger'):
            strategy.logger = self.logger
