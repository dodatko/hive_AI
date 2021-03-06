from enum import IntEnum

class dotdict(dict):
    def __getattr__(self, name):
        return self[name]


class HiveException(Exception):
    """Base class for exceptions."""
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors


class Player(object):
    WHITE = "w"
    BLACK = "b"


class GameStatus(object):
    # End game status
    UNFINISHED = 0
    WHITE_WIN = 1
    BLACK_WIN = 2
    DRAW = 3


class Direction(IntEnum):
    HX_O = 0  # origin/on-top
    HX_W = 1  # west
    HX_NW = 2  # north-west
    HX_NE = 3  # north-east
    HX_E = 4  # east
    HX_SE = 5  # south-east
    HX_SW = 6  # south-west
    HX_LOW = 7  # lower
    HX_UP = 8  # upper


def get_queen_name(player: Player) -> str:
    return 'bQ1' if player == Player.BLACK else 'wQ1'
