import itertools
from copy import deepcopy
from enum import IntEnum
from typing import *

import numpy as np


class Color(IntEnum):
    Empty = 0
    Blue = 1
    Yellow = 2
    Red = 3
    Black = 4
    White = 5


class Move(NamedTuple):
    sourceBin: int = 0
    targetQueue: int = 0
    color: int = Color.Empty
    count: int = 0


class PlayerState:

    def __init__(self, wall: Optional[np.ndarray] = None, queue: Optional[np.ndarray] = None,
                 floorCount: Optional[int] = None, score: Optional[int] = None):
        self.wall = wall or np.zeros(Azul.WallShape, dtype=np.uint8)
        self.queue = queue or np.zeros((Azul.WallShape[0], 2), dtype=np.uint8)  # Stores color and count per row.
        self.floorCount = floorCount or 0

        self.score = score if score is not None else 0


class Azul:
    ColorNumber = 5
    PlayerNumber = 2
    BinNumber = 5
    BinSize = 4
    WallShape = (5, 5)
    FloorSize = 7

    def __init__(self, bagCount: Optional[np.ndarray] = None, bins: Optional[np.ndarray] = None,
                 pool: Optional[np.ndarray] = None, playerStates: Optional[List[PlayerState]] = None,
                 isNextPLayerA: Optional[bool] = None, poolWasTouched: Optional[bool] = None):
        self.bagCount = bagCount or np.repeat(20, Azul.ColorNumber)
        # Bins and pool store the count indexed by the Color enum. The 'empty' color is always at zero.
        self.bins = bins or np.zeros((Azul.BinNumber, Azul.ColorNumber + 1), dtype=np.uint8)
        self.pool = pool or np.zeros(Azul.ColorNumber + 1, dtype=np.uint8)

        self.playerStates = playerStates or [PlayerState() for _ in range(Azul.PlayerNumber)]

        self.isNextPlayerA = isNextPLayerA if isNextPLayerA is not None else True
        self.poolWasTouched = poolWasTouched if poolWasTouched is not None else False

    def is_end_of_game(self) -> bool:
        for player in self.playerStates:
            if np.any(np.count_nonzero(player.wall, axis=0) == 0):
                return True

        return False

    def is_end_of_round(self) -> bool:
        return np.all(self.bins == 0) and np.all(self.pool == 0)

    def enumerate_moves(self):
        player = self.playerStates[0] if self.isNextPlayerA else self.playerStates[1]
        for iSource, source in enumerate(itertools.chain(self.bins, (self.pool, ))):
            for color, count in enumerate(source):
                if count == 0 or color == Color.Empty:
                    continue

                for iTarget, (targetQueue, targetRow) in enumerate(zip(player.queue, player.wall)):
                    # If the color isn't already on the wall in that row,
                    # and the queue has space (its size is index+1),
                    # and the queue is completely empty (first element empty) or contains the same color.
                    if color not in targetRow and \
                            targetQueue[1] < iTarget + 1 and \
                            (targetQueue[0] == Color.Empty or targetQueue[0] == color):

                        yield Move(iSource, iTarget, color, count)

                # It's always valid to put the tiles on the floor.
                yield Move(iSource, Azul.WallShape[0], color=color, count=count)

    @staticmethod
    def get_wall_slot_color(index: Tuple[int, int]) -> Color:
        # This generates the diagonal pattern on the playing board.
        return Color((index[1] - index[0]) % Azul.ColorNumber + 1)
