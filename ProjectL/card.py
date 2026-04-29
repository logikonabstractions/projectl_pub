import numpy as np

from ProjectL.pieces import PieceSquare


class Reward:
    """
        Describes what we get for finishing a card. Points and/or a piece
    """
    def __init__(self, points = 0, piece = None):
        self.points = points
        self.piece = piece if piece else PieceSquare()

    def __repr__(self):
        return f"Points: {self.points} with piece: {self.piece.name}"

class Card:
    """ Describes the different cards we can play with.

        layout: the numpy array that describes the state of the card (1 = occupied, 0 = empty for each square)
        reward: the object that describes what piece / points we get for completing the card
        mask: a bool numpy array that describes the playable structure of that card within the maximal matrix
    """
    def __init__(self, configs = None):
        if configs:
            self.layout = np.zeros(shape=(5, 5), dtype=int)
            self.mask = np.array(configs["mask"])
            self.reward = Reward(points=configs["reward"]["points"], piece=configs["reward"]["piece"])
        else:
            self.layout = np.zeros(shape=(5, 5), dtype=int)
            self.mask = np.array([[False,False,True,True,False,], [False,False,True,True,False], [False,False,True,True,False], [False,False,False,False,False], [False,False,False,False,False], ])
            self.reward = Reward()
        self.is_full = False


    def place_piece(self, configuration):
        """
            places the provided piece on the card at a given position. returns T/F for success
            piece: a Piece object to be placed on the current card
            configuration: a description of where on the card to place the piece
        """

        if self.placement_valid(configuration):
            self.layout += configuration            # update the layout
            if np.all((self.layout == 1) == self.mask):
                self.is_full = True
            return True
        else:
            return False

    def placement_valid(self, configuration):
        """ checks if the placement of the piece on this card is valid. conditions:
            - no position on self.layout > 1 after self.layout += configuration
            - no bit of configuration falls on a region where the mask is false

        """
        result = self.layout + configuration
        out_sum = np.sum(result[~self.mask])     # should sum to zero

        double_occupation = np.any(result > 1)

        return out_sum == 0 and not double_occupation

    def __repr__(self):
        return f"Mask: {self.mask}, full: {self.is_full}, reward: {self.reward}"
