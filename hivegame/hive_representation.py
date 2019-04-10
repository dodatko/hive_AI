import logging
from hivegame.hive_utils import Direction, Player

import hivegame.hive_validation as valid
import hivegame.pieces.piece_factory as piece_fact

from hivegame.pieces.bee_piece import BeePiece
from hivegame.pieces.ant_piece import AntPiece
from hivegame.pieces.spider_piece import SpiderPiece

# Adjacency matrix of pieces
# - rows in order: (22 pieces at the moment, i may change when adding extensions)
#   ['wA1', 'wA2', 'wA3', 'wB1', 'wB2', 'wG1', 'wG2', 'wG3', 'wQ1', 'wS1', 'wS2',
#    'bA1', 'bA2', 'bA3', 'bB1', 'bB2', 'bG1', 'bG2', 'bG3', 'bQ1', 'bS1', 'bS2']
# - cells:
#   + 0: they are not adjacent
#   + 7: is lower, 8: is upper
#
#    2/ \3
#   1|   |4
#    6\ /5
#
#   + eg. in row of bA2 and column of bG1 there is a 3.
#     That means bG1 is north-east from bA2.


def get_adjacency_state(hive):
    """
    Returns a two dimensional dictionary, where both keys are the string representation of the pieces.
    One cell represents the adjacency of the two pieces. 0 means they are not adjacent.

    The first X rows represents the white pieces. The next X rows contain the black player's pieces.
    """
    pieces = piece_fact.piece_set("w")
    pieces.update(piece_fact.piece_set("b"))

    # Initially nobody has a neighbor
    result = {}
    for row in pieces:
        result[row] = {}
        for col in pieces:
            if col != row:
                result[row][col] = 0

    for piece, relations in result.items():
        cell = hive.locate(piece)

        # the piece is not set yet
        if not cell:
            continue

        # check if there are more pieces at the same cell (beetles)
        pieces_in_cell = hive.piecesInCell[cell]
        if len(pieces_in_cell) > 1:
            position = pieces_in_cell.index(piece)
            for lower_piece in pieces_in_cell[:position]:
                relations[lower_piece] = Direction.HX_LOW
            if position + 1 < len(pieces_in_cell):
                for upper_piece in pieces_in_cell[position + 1:]:
                    relations[upper_piece] = Direction.HX_UP

        surrounding_cells = hive.occupied_surroundings(cell)
        for neighbor_cell in surrounding_cells:
            # get piece on the top of the neighbor cell
            neighbor_piece = hive.piecesInCell[neighbor_cell][-1]
            relations[str(neighbor_piece)] = hive.board.get_line_dir(cell, neighbor_cell)
    return result


def canonical_adjacency_state(hive):
    """
    Representation of state with adjacency matrix. From the players point of view. Instead of having a white and
    a black player, there are my pieces and the opponent's pieces.

    Practically it means that we have to switch colors of each piece.
    """

    # sorted by their names. That means black piece are at front.
    matrix = get_adjacency_state(hive)
    inverse_matrix = {}
    for (row_name, row) in matrix.items():
        inverse_row = {}
        for (col_name, cell) in row.items():
            inverse_row[_toggle_color(col_name)] = cell
        inverse_matrix[_toggle_color(row_name)] = inverse_row

    return inverse_matrix


def list_representation(adjacency):
    directions = []  # current turn number is the first data
    for sorted_row in [v for (k, v) in sorted(adjacency.items(), key=lambda row: row[0])]:
        for sorted_dir in [v for (_k, v) in sorted(sorted_row.items(), key=lambda col: col[0])]:
            directions.append(sorted_dir)
    return directions


def dict_representation(adjacency_list):
    """
    :param adjacency_list: List representation of the state
    :return: Dictionary representation of the state
    """
    print("[DEBUG] dict_representation: len(adjacency_list) == {}".format(len(adjacency_list)))
    # get list of bug names sorted by name alphabetically
    list_of_names = sorted(list(piece_fact.piece_set(Player.WHITE).keys()) + list(
        piece_fact.piece_set(Player.BLACK).keys()))
    print("[DEBUG] dict_representation: len(list_of_names) == {}".format(len(list_of_names)))

    adjacency_iter = iter(adjacency_list)
    # Create a dictionary
    result = {}
    for bug_name in list_of_names:
        column = {}
        result[bug_name] = column
        for inner_name in list_of_names:
            if inner_name == bug_name:
                break  # adjacency with itself is not stored
            column[inner_name] = next(adjacency_iter)
    return result


def string_representation(adjacency_list_repr):
    # We need to use comma as separator, because turn number can consist of more digits.
    return ",".join(str(x) for x in adjacency_list_repr)


def _toggle_color(piece_name):
    assert(len(piece_name) == 3)
    s = list(piece_name)
    s[0] = Player.BLACK if s[0] == Player.WHITE else Player.WHITE
    return "".join(s)


def get_all_action_vector(hive):
    """
    :return: A one-hot encoded representation of possible actions.
    The size of the vector returned is fixed.
    """
    result = []
    direction_count = 6
    # Pieces not played yet:
    piece_set = piece_fact.piece_set(hive.activePlayer)
    print("[DEBUG] piece set length: %d" % len(piece_set))
    possible_neighbor_count = len(piece_set) - 1  # it can't be adjacent to itself

    my_pieces = [piece for piece in hive.playedPieces.values() if piece.color == hive.activePlayer]
    # The first row is about placing the first piece. However, the player in the second turn can place his
    # bug to 6 different places, those states are identical, so the AI can be restricted to only one
    # direction.
    # Also, we do not need action for placing the queen, because that is forbidden in the first turn.
    if not my_pieces:
        result += [1] * (len(piece_set) - 1)
    else:
        result += [0] * (len(piece_set) - 1)

    # Placing pieces
    for piece_name in piece_set.keys():
        if piece_name in hive.playedPieces.keys():
            result += [0] * (possible_neighbor_count * direction_count)
        else:
            for adj_piece_name in piece_set.keys():
                # It cannot move next to itself
                if adj_piece_name == piece_name:
                    continue
                adj_piece = hive.playedPieces.get(adj_piece_name, None)
                if adj_piece is None:
                    # neighbor candidate not placed yet
                    result += [0] * direction_count
                    continue
                # get all boundary free cells
                surroundings = hive.board.get_surrounding(adj_piece.position)
                for sur in surroundings:
                    if not hive.is_cell_free(sur):
                        result.append(0)
                    elif not all(hive.is_cell_free(s) or hive.piecesInCell.get(s)[-1].color ==
                                 hive.activePlayer for s in hive.board.get_surrounding(sur)):
                        result.append(0)
                    else:
                        result.append(1)
    print("[DEBUG] result length of placing only: %d" % (len(result)))
    # moving pieces
    for piece_name, piece_without_pos in piece_set.items():
        piece = hive.playedPieces.get(piece_name, None)
        if piece is None:
            result += [0] * piece_without_pos.move_vector_size
            continue

        # It cannot move unless queen is already placed
        if hive.activePlayer + 'Q1' not in hive.playedPieces:
            result += [0] * piece.move_vector_size
            continue

        # It cannot move if that breaks the one_hive rule
        if not valid.validate_one_hive(hive, piece):
            result += [0] * piece.move_vector_size
            continue

        result += piece.available_moves_vector(hive)

    print("[DEBUG]: Resulting move vector is: {}".format(result))
    expected_len = len(piece_set) - 1 + (possible_neighbor_count * direction_count) * len(piece_set) +\
        1*6 + 3*6 + 3*AntPiece.MAX_STEP_COUNT + 2*SpiderPiece.MAX_STEP_COUNT + 2*6
    print("[DEBUG] len of result: %d, and expected len is: %d" % (len(result), expected_len))
    assert len(result) == expected_len
    return result


def get_all_possible_actions(hive):
    result = set()

    # choose the current players played pieces
    my_pieces = [piece for piece in hive.playedPieces.values() if piece.color == hive.activePlayer]

    if not my_pieces:
        # no piece of that player has been played yet
        if not hive.piecesInCell.get((0, 0)):
            return [(piece, (0, 0)) for piece in hive.unplayedPieces[hive.activePlayer].values() if
                    not isinstance(piece, BeePiece)]
        else:
            for sur in hive.board.get_surrounding((0, 0)):
                result.update([(piece, sur) for piece in hive.unplayedPieces[hive.activePlayer].values() if
                               not isinstance(piece, BeePiece)])
            return result

    # pieces which can be put down from hand
    pieces_to_put_down = []
    # cells where the player can put an unplayed piece to
    available_cells = set()

    if hive.activePlayer + 'Q1' in hive.playedPieces:
        # Actions of pieces already on board
        for piece in my_pieces:
            if not valid.validate_one_hive(hive, piece):
                continue
            end_cells = piece.available_moves(hive)
            result.update([(piece, end_cell) for end_cell in end_cells if end_cell != piece.position])

    logging.info("Hive: Unplayed pieces: {}".format(hive.unplayedPieces[hive.activePlayer]))
    if hive.turn >= 7 and hive.activePlayer + 'Q1' not in hive.playedPieces:
        pieces_to_put_down.append(hive.unplayedPieces[hive.activePlayer][hive.activePlayer + 'Q1'])
    else:
        pieces_to_put_down += hive.unplayedPieces[hive.activePlayer].values()

    # get all boundary free cells
    for piece in my_pieces:
        surroundings = hive.board.get_surrounding(piece.position)
        available_cells.update([sur for sur in surroundings if hive.is_cell_free(sur)])
    # Keep only those which have no opposite side neighbors
    cells_to_remove = set()
    for cell in available_cells:
        surroundings = hive.board.get_surrounding(cell)
        if not all(hive.is_cell_free(sur) or hive.piecesInCell.get(sur)[-1].color == hive.activePlayer
                   for sur in surroundings):
            cells_to_remove.add(cell)
    available_cells.difference_update(cells_to_remove)

    # You can place all of your pieces there
    for piece in pieces_to_put_down:
        result.update([(piece, end_cell) for end_cell in available_cells])
    return result
