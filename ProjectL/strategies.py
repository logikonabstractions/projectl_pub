import random
import logging

from ProjectL.actions import TakePiece, PlacePiece, UpgradePiece, TakeCard, Master


class Strategy:
    """Base strategy class for implementing different playing strategies.

    Allows for fixed sequences of actions or dynamic decision-making.
    Used by the Player class.
    """
    def __init__(self, player, actions_sequence=None, action_list=None, logger=None):
        self.player = player
        self.action_sequence = actions_sequence if actions_sequence else ()
        self.actions = action_list if action_list else (TakePiece, PlacePiece, UpgradePiece, TakeCard, Master)
        self.actions_left = 3
        self.logger = logger or logging.getLogger('projectL')

    def play_turn(self):
        raise NotImplemented

    @property
    def pieces(self):
        return self.player.pieces
    @property
    def cards(self):
        return self.player.cards
    @cards.setter
    def cards(self, value):
        self.player.cards = value
    @property
    def full_cards(self):
        return self.player.full_cards
    @full_cards.setter
    def full_cards(self, value):
        self.player.full_cards = value
    @property
    def name(self):
        return self.player.name


class RandomStrat(Strategy):
    """Strategy that chooses actions randomly."""

    def __init__(self, player, logger=None, **kwargs):
        super().__init__(player, logger=logger, **kwargs)

    def choose_action(self):
        """Randomly selects an action from available action types."""
        action_class = random.choice(self.actions)
        action_selected = action_class(pieces=self.pieces, cards=self.cards, game_manager=self.player.game_manager)
        self.logger.debug(f"{self.name} randomly selected action: {action_selected}",
                          extra={"normal": False, "verbose": True})
        return action_selected

    def play_turn(self):
        """Play a turn by randomly choosing valid actions until actions run out."""
        self.actions_left = 3
        self.logger.debug(f"{self.name} starting turn with {self.actions_left} actions ",
                          extra={"normal": False})

        while self.actions_left > 0:
            action = self.choose_action()

            attempts = 0
            while not action.is_action_valid() and attempts < 10:
                self.logger.debug(f"{self.name} action invalid, trying another",
                                  extra={"normal": False, "verbose": True})
                action = self.choose_action()
                attempts += 1

            if attempts >= 10:
                self.logger.debug(f"{self.name}  couldn't find valid action after 10 attempts",
                                  extra={"normal": False})
                break

            self.logger.info(f"{self.name}  performs: {action}",  extra={"normal": True})
            action.perform_action()
            self.actions_left -= 1
        self.logger.debug(f"Player state: {self.player}", extra={"normal": False, "verbose": True})

class TakePieceStrat(Strategy):
    """Always takes a piece"""

    def __init__(self, player, logger=None, **kwargs):
        super().__init__(player, logger=logger, **kwargs)

    def choose_action(self):
        """Randomly selects an action from available action types."""
        action_selected = TakePiece(pieces=self.pieces, cards=self.cards, game_manager=self.player.game_manager)
        self.logger.debug(f"{self.name} randomly selected action: {action_selected}",
                          extra={"normal": False, "verbose": True})
        return action_selected

    def play_turn(self):
        """Play a turn by randomly choosing valid actions until actions run out."""
        self.actions_left = 3
        self.logger.debug(f"{self.name} starting turn with {self.actions_left} actions ",
                          extra={"normal": False})

        while self.actions_left > 0:
            action = self.choose_action()

            attempts = 0
            while not action.is_action_valid() and attempts < 10:
                self.logger.debug(f"{self.name} action invalid, trying another",
                                  extra={"normal": False, "verbose": True})
                action = self.choose_action()
                attempts += 1

            if attempts >= 10:
                self.logger.debug(f"{self.name}  couldn't find valid action after 10 attempts",
                                  extra={"normal": False})
                break

            self.logger.info(f"{self.name}  performs: {action}",  extra={"normal": True})
            action.perform_action()
            self.actions_left -= 1
        self.logger.debug(f"Player state: {self.player}", extra={"normal": False, "verbose": True})

class BasicStrat(Strategy):
    """Basic strategy with a simple priority system:

    Priority order:
    1. Attempts to place a piece if this is a valid action in the current state
    3. Take a card if the player currently has no cards
    2. Take a piece otherwise
    """

    def __init__(self, player, logger=None, **kwargs):
        super().__init__(player, logger=logger, **kwargs)

    def _move_full_cards(self):
        """Move completed cards from active cards to full cards collection."""
        full_cards = [card for card in self.cards if card.is_full]
        if full_cards:
            self.logger.info(f"{self.name}  completed {len(self.player.full_cards)} cards", extra={"normal": True})
            self.full_cards.extend(full_cards)
            self.cards = [card for card in self.cards if not card.is_full]

    def _execute_action(self, action):
        """Execute an action if valid and consume an action point.

        Returns:
            bool: True if action was executed successfully
        """
        if action.is_action_valid():
            self.logger.info(f"{self.name}  performs: {action}", extra={"normal": True})
            action.perform_action()
            self.actions_left -= 1
            return True
        else:
            self.logger.debug(f"{self.name}  action invalid: {action}", self.name, action.desc, extra={"normal": False, "verbose": True})
            return False

    def _try_place_piece(self):
        """Attempt to place a piece on a card.

        Returns:
            bool: True if placement was successful
        """
        if not (self.cards and self.pieces):
            self.logger.debug(f"{self.name}  can't place piece - missing cards or pieces",

                             extra={"normal": False, "verbose": True})
            return False

        piece = self.pieces.pop()
        action = PlacePiece(piece, self.cards[0], pieces=self.pieces)
        self.logger.debug(f"{self.name} attempting to place piece on card",  extra={"normal": False})

        if self._execute_action(action):
            return True
        else:
            self.pieces.append(piece)
            self.logger.debug(f"{self.name} failed to place piece, returning to inventory",

                             extra={"normal": False, "verbose": True})
            return False

    def _determine_best_action(self):
        """Determine the best action based on current game state.

        Returns:
            Action result
        """
        if self.cards and self.pieces:
            self.logger.debug(f"{self.name}  strategy: place piece (has cards and pieces)",
                             extra={"normal": False})
            return PlacePiece(self.pieces[-1], self.cards[0], pieces=self.pieces, game_manager=self.player.game_manager)

        if not self.cards:
            self.logger.debug(f"{self.name} strategy: take card (no cards)",
                             extra={"normal": False})
            return TakeCard(cards=self.cards)

        self.logger.debug(f"{self.name}  strategy: default to take piece",
                         extra={"normal": False})

        return TakePiece(pieces=self.pieces, game_manager=self.player.game_manager)

    def play_turn(self):
        """Execute the turn following the basic strategy priority system."""
        self.actions_left = 3
        self.logger.debug(f"{self.player} plays turn (BasicStrat)",
                         extra={"normal": False})

        self._move_full_cards()

        actions_attempted = 0
        max_attempts = 10

        while self.actions_left > 0 and actions_attempted < max_attempts:
            actions_attempted += 1

            action = self._determine_best_action()

            if action and self._execute_action(action):
                continue
            else:
                self.logger.info(f"{self.player.name} passes remaining %d actions",
                               self.name, self.actions_left,
                               extra={"normal": True})
                self.actions_left = 0

        self.logger.debug(f"Player state: {self.player}", extra={"normal": False, "verbose": True})
