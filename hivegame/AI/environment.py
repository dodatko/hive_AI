#! /usr/bin/env python

import sys

from hivegame.hive import Hive, HiveException
from utils.ascii_view import HiveView
from hivegame.hive_utils import GameStatus, Player
from hivegame.AI.utils.Game import Game

import logging
import hivegame.hive_representation as represent


class Environment(Game):
    """
    Environment controls the game. It contains all the methods to
    create a game, move or put down pieces, ask information about
    current state etc.
    """

    def __init__(self):
        """
        Creates an environment which is reset to initial state. That means no
        bugs are placed yet, etc.
        """
        super(Environment, self).__init__()
        self.hive = Hive()
        self.view = HiveView(self.hive)
        self.input = sys.stdin
        self.reset_game()
        self.debug_hive = Hive()

    def reset_game(self):
        self.hive.reset()

    @staticmethod
    def pass_turn(hive):
        hive.pass_turn()

    def check_victory(self):
        """
        UNFINISHED = 0
        WHITE_WIN = 1
        BLACK_WIN = 2
        DRAW = 3
        :return: status of the game
        """
        return self.hive.check_victory()

    @property
    def current_player(self):
        return self.hive.current_player
    
    def unplayed_pieces(self, player):
        return self.hive.level.get_unplayed_pieces(player)
    
    def get_all_possible_actions(self):
        return represent.get_all_possible_actions(self.hive)
    
    def action_piece_to(self, piece, to_cell):
        try:
            self.hive.action_piece_to(piece, to_cell)
            return True
        except HiveException:
            return False

    @staticmethod
    def _player_to_inner_player(player_num):
        assert player_num == 1 or player_num == -1
        return Player.WHITE if player_num == 1 else Player.BLACK

# Methods for Game.py interface
    def stringRepresentation(self, board):
        return represent.string_representation(board)

    def getActionSize(self):
        """
        :return: Number of possible actions in the given state
        """
        hive = Hive()
        return len(represent.get_all_action_vector(hive))

    def getCanonicalForm(self, board, player_num):
        hive = Hive.load_state_with_player(board, self._player_to_inner_player(player_num))
        return represent.two_dim_representation(represent.canonical_adjacency_state(hive))

    def getGameEnded(self, board, player_num):
        hive = Hive.load_state_with_player(board, self._player_to_inner_player(player_num))
        status = hive.check_victory()
        if status == GameStatus.UNFINISHED:
            return 0
        if player_num == 1:  # Hive.BLACK
            return 1 if status == GameStatus.BLACK_WIN else -1
        elif player_num == -1:  # Hive.WHITE
            return 1 if status == GameStatus.WHITE_WIN else -1
        else:
            raise ValueError('Unexpected game status')

    def getValidMoves(self, board, player_num):
        hive = Hive.load_state_with_player(board, self._player_to_inner_player(player_num))
        return represent.get_all_action_vector(hive)

    def getNextState(self, board, player, action_number):
        assert action_number >= 0
        hive = Hive.load_state_with_player(board, Environment._player_to_inner_player(player))
        try:
            (piece, to_cell) = hive.action_from_vector(action_number)
        except HiveException as error:
            logging.error("HiveException was caught: {}".format(error))
            logging.error("action number: {}".format(action_number))
            #logging.error("\n{}".format(HiveView(hive)))
            raise
        # TODO handle pass
        try:
            hive.action_piece_to(piece, to_cell)
        except HiveException as error:
            logging.error("HiveException was caught: {}".format(error))
            logging.error("action number: {}, resulting action: ({}, {})".format(action_number, piece, to_cell))
            #logging.error("\n{}".format(HiveView(hive)))
            raise
        self.debug_hive = hive
        return represent.two_dim_representation(represent.get_adjacency_state(hive)), player*(-1)

    def getInitBoard(self):
        hive = Hive()
        return represent.two_dim_representation(represent.get_adjacency_state(hive))

    def getSymmetries(self, board, pi):
        symmetries = []
        # Rotate the board 5 times
        for i in range(5):
            symmetries.append(self._rotate_adjacency(board))
        return map(lambda sim: (sim, pi), symmetries)

    @staticmethod
    def _rotate_adjacency(two_dim_adjacency):
        result = []
        for row in two_dim_adjacency:
            for direction in row:
                if 0 < direction <= 5:
                    result.append(direction + 1)
                elif direction == 6:
                    result.append(1)  # overflow of directions
                else:
                    result.append(direction)
        return result

    def getBoardSize(self):
        hive = Hive()
        return represent.two_dim_representation(represent.canonical_adjacency_state(hive)).shape