from __future__ import annotations
from hivegame.hive_utils import get_queen_name
from hivegame.pieces.bee_piece import BeePiece
import logging

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from hivegame.hive import Hive
    from hivegame.pieces.piece import HivePiece

from utils import hexutil


def validate_queen_rules(hive: 'Hive', piece: 'HivePiece', action: str) -> bool:
    """
    Validate rules related to the queen.
    :param hive: game state
    :param piece: Piece to move or place down
    :param action: move or place
    :return: Returns if the action is valid or not.
    """
    # Tournament rule: no queen in the first move
    if len(hive.level.get_played_pieces()) < 3 and isinstance(piece, BeePiece):
        logging.info("Queen should not be placed in the first turn")
        return False

    queen = hive.get_piece_by_name(get_queen_name(hive.current_player))

    # Move actions are only allowed after the queen is on the board
    if action == 'move':
        if not queen.position:
            logging.info("Moves actions permitted until queen is on board")
            return False

    # White Queen must be placed by turn 7 (4th white action), black queen in turn 8
    if hive.level.get_played_pieces(hive.current_player) == 3 and not queen.position:
        if piece.kind != 'Q' or action != 'place':
            logging.info("Queen should be placed now")
            return False

    return True


def validate_turn(hive: 'Hive', piece: 'HivePiece', action: str) -> bool:
    """
    Verifies if the action is valid on this turn.
    :param hive: State of game
    :param piece: Piece on which the action is performed
    :param action: move or place
    :return: Whether the action is valid or not
    """

    # Validate piece color
    if piece.color != hive.current_player:
        logging.info("validate_turn: Attempt to move or place a piece with wrong color")
        return False

    # Validate queen rules
    if not validate_queen_rules(hive, piece, action):
        logging.info("validate_turn: Queen rules violated")
        return False

    return True


def validate_move_piece(hive: 'Hive', moving_piece: 'HivePiece', target_cell: hexutil.Hex) -> bool:
    # check if the piece has been placed
    moving_piece = hive.level.find_piece_played(moving_piece)
    if moving_piece is None:
        logging.info("validate_move_piece: piece was not played yet")
        return False

    # Do not move to the very same cell
    if moving_piece.position == target_cell:
        logging.info("validate_move_piece: moving to the same place")
        return False

    # check if moving this piece won't break the hive
    if not validate_one_hive(hive, moving_piece):
        logging.info("validate_move_piece: break one_hive rule")
        return False

    if not moving_piece.validate_move(hive, target_cell):
        logging.info("validate_move_piece: piece is unable to move there")
        return False
    return True


def validate_place_piece(hive: 'Hive', piece: 'HivePiece', target_cell: hexutil.Hex) -> bool:
    """
    Verifies if a piece can be played from hand into a given target_cell.
    The piece must be placed touching at least one piece of the same color
    and can only be touching pieces of the same color.
    :param hive: game state
    :param piece: piece which is being placed to board
    :param target_cell: hexagon where the piece is being placed to.
    :return: whether it's valid or not
    """

    # target_cell must be free
    if hive.level.get_tile_content(target_cell):
        logging.info("validate_place_piece: cell not free")
        return False

    if hive.level.find_piece_played(piece):
        logging.info("validate_place_piece: piece has been already placed")
        return False

    # The below rules apply only after the second turn. E.g. neighbor color matching is not enforced
    if len(hive.level.get_played_pieces()) < 3:
        return True

    nbs = hive.level.occupied_surroundings(target_cell)
    if any(piece.color !=  hive.level.get_tile_content(nb)[-1].color for nb in nbs):
        logging.info("validate_place_piece: Invalid placement")
        return False

    return True


def validate_one_hive(hive: 'Hive', piece: 'HivePiece'):
    """
    Check if removing a piece doesn't break the one hive rule.
    :param hive: game state
    :param piece: piece to perform action on.
    :return: False if the hive is broken.
    """
    # if the piece is not in the board then placing it won't break the hive
    if piece.position is None:
        return True

    # if there is another piece in the same cell then the one hive rule
    # won't be broken
    piece_list = hive.level.get_tile_content(piece.position)
    if len(piece_list) > 1:
        return True

    if not hive.level.tiles:
        print("[DEBUG] why is that called then?")
        return True

    # Get all pieces that are in contact with the removed one and try to
    # reach all of them from one of them.
    occupied = hive.level.occupied_surroundings(piece.position)
    assert occupied
    visited = set()
    to_explore = {occupied[0]}
    to_reach = set(occupied[1:])
    res = False

    while len(to_explore) > 0:
        found = []
        for cell in to_explore:
            found += hive.level.occupied_surroundings(cell)
            if piece in found:
                found.remove(piece)  # as if the current piece would be removed
            visited.add(cell)
        to_explore = set(found) - visited
        if to_reach.issubset(visited):
            print("True is the verdict")
            res = True
            break

    return res
