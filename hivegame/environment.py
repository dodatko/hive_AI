#! /usr/bin/env python

import sys

from hivegame.hive import Hive, HiveException
from hivegame.view import HiveView
from hivegame.hive_utils import Direction
from hivegame.AI.utils.Game import Game
import random


class Environment(Game):
    """
    Environment controls the game. It contains all the methods to
    create a game, move or put down pieces, ask information about
    current state etc.
    """

    # Current player
    BLACK = 'b'
    WHITE = 'w'

    def __init__(self):
        """
        Creates an environment which is reset to initial state. That means no
        bugs are placed yet, etc.
        """
        super(Environment, self).__init__()
        self.hive = Hive()
        self.view = HiveView(self.hive)
        self.input = sys.stdin
        self.logger = None
        self.reset_game()

    def ascii_board(self):
        return str(self.view)

    def reset_game(self):
        self.hive.setup()
        if self.logger is not None:
            self.logger.close()
        self.logger = open('game.log', 'w')

    def exec_cmd(self, cmd):
        try:
            (cmdType, value) = self.parse_cmd(cmd)
        except HiveException:
            return False
        if cmdType == 'non_play' and value == 'pass':
            self.hive.action(cmdType, value)
            return True

        if cmdType != 'play':
            return False  # invalid command type

        (actPiece, point_of_contact, ref_piece) = value

        if point_of_contact is None and self.hive.turn > 1:
            return False

        try:
            direction = None
            if point_of_contact is not None:
                direction = self.poc2direction(point_of_contact)
        except ValueError:
            return False

        try:
            self.hive.action('play', (actPiece, ref_piece, direction))
        except HiveException:
            return False
        
        return True

    def parse_cmd(self, cmd):
        self.logger.write(cmd+'\n')

        if cmd == 'pass':
            return 'non_play', cmd
        if len(cmd) == 3:
            moving_piece = cmd
            point_of_contact = None
            ref_piece = None
        else:
            if len(cmd) != 8:
                raise Exception("Failed to parse command.")
            moving_piece = cmd[:3]
            point_of_contact = cmd[3:5]
            ref_piece = cmd[5:]
        return 'play', (moving_piece, point_of_contact, ref_piece)

    @staticmethod
    def poc2direction(point_of_contact):
        """Parse point of contact to a Hive.direction"""""
        if point_of_contact == '|*':
            return Direction.HX_W
        if point_of_contact == '/*':
            return Direction.HX_NW
        if point_of_contact == '*\\':
            return Direction.HX_NE
        if point_of_contact == '*|':
            return Direction.HX_E
        if point_of_contact == '*/':
            return Direction.HX_SE
        if point_of_contact == '\\*':
            return Direction.HX_SW
        if point_of_contact == '=*':
            return Direction.HX_O
        raise ValueError('Invalid input for point of contact: "%s"' % point_of_contact)

    def check_victory(self):
        """
        UNFINISHED = 0
        WHITE_WIN = 1
        BLACK_WIN = 2
        DRAW = 3
        :return: status of the game
        """
        return self.hive.check_victory()
    
    def current_player(self):
        return Environment.WHITE if self.hive.turn % 2 > 0 else Environment.BLACK
    
    def unplayed_pieces(self, player):
        return self.hive.get_unplayed_pieces(player)
    
    def get_turn_count(self):
        return self.hive.turn
    
    def get_all_possible_actions(self):
        return self.hive.get_all_possible_actions()
    
    def action_piece_to(self, piece, to_cell):
        try:
            self.hive.action_piece_to(piece, to_cell)
            return True
        except HiveException:
            return False

    def randomActionInState(self, state):
        hive = Hive()
        hive.load_state(state)
        return random.choice(tuple(hive.get_all_possible_actions()))

# Methods for Game.py interface
    def stringRepresentation(self, board):
        return self.hive.string_representation(board)

    def getActionSize(self, board, player):
        """
        :param state: A tuple of an adjacency matrix representing the board and the number of turns.
        :return: Number of possible actions in the given state
        """
        hive = Hive()
        hive.load_state_with_player(board, player)
        return len(hive.get_all_possible_actions())

    def getCanonicalForm(self, board, player):
        hive = Hive()
        hive.load_state_with_player(board, player)
        return Hive.list_representation(hive.canonical_adjacency_state())

    def getGameEnded(self, board, player):
        hive = Hive()
        hive.load_state_with_player(board, player)
        status = hive.check_victory()
        if status == Hive.UNFINISHED:
            return 0
        if player == 1:  # Hive.BLACK
            return 1 if status == Hive.BLACK_WIN else -1
        elif player == -1:  # Hive.WHITE
            return 1 if status == Hive.WHITE_WIN else -1
        else:
            raise ValueError('unexpected player')

    def getValidMoves(self, board, player):
        # TODO create load_state with player
        hive = Hive()
        hive.load_state_with_player(board, player)
        return hive.get_all_possible_actions()

    def getNextState(self, board, player, action):
        hive = Hive()
        hive.load_state_with_player(board, player)
        (piece, to_cell) = action
        hive.action_piece_to(piece, to_cell)

    def getInitBoard(self):
        hive = Hive()
        return Hive.list_representation(hive.get_adjacency_state())

    def getSymmetries(self, board_list_repr, pi):
        symmetries = []
        # Rotate the board 5 times
        for i in range(5):
            symmetries.append(self._rotate_adjacency(board_list_repr))
        return map(lambda sim: (sim, pi), symmetries)

    @staticmethod
    def _rotate_adjacency(adjacency_list):
        result = []
        for dir in adjacency_list:
            if 0 < dir <= 5:
                result.append(dir + 1)
            elif dir == 6:
                result.append(1)  # overflow of directions
            else:
                result.append(dir)
        return result