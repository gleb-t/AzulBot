import itertools
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
                 floor: Optional[np.ndarray] = None, score: Optional[int] = None):
        self.wall = wall or np.zeros(Azul.WallShape, dtype=np.uint8)
        self.queue = queue or np.zeros(Azul.WallShape, dtype=np.uint8)
        self.floor = floor or np.zeros(Azul.FloorSize, dtype=np.uint8)

        self.score = score if score is not None else 0


class Azul:
    ColorNumber = 5
    PlayerNumber = 2
    BinNumber = 5
    WallShape = (5, 5)
    FloorSize = 7

    def __init__(self, bagCount: Optional[np.ndarray] = None, bins: Optional[np.ndarray] = None,
                 pool: Optional[np.ndarray] = None, playerStates: Optional[List[PlayerState]] = None,
                 isNextPLayerA: Optional[bool] = None, poolWasTouched: Optional[bool] = None):
        self.bagCount = bagCount or np.repeat(20, Azul.ColorNumber)
        self.bins = bins or np.zeros((Azul.BinNumber, 4), dtype=np.uint8)
        # self.binEmptyFlags = np.array((np.all(b == Color.empty) for b in self.bins), dtype=np.bool)
        self.pool = pool or np.zeros(20, dtype=np.uint8)

        self.playerStates = playerStates or [PlayerState() for _ in range(Azul.PlayerNumber)]

        self.isNextPlayerA = isNextPLayerA if isNextPLayerA is not None else True
        self.poolWasTouched = poolWasTouched if poolWasTouched is not None else False

    def is_end_of_game(self):
        for player in self.playerStates:
            if np.any(np.count_nonzero(player.wall, axis=0) == 0):
                return True

        return False

    def is_end_of_round(self):
        return np.all(self.bins == Color.empty) and np.all(self.pool == Color.empty)

    def enumerate_moves(self):
        player = self.playerStates[0] if self.isNextPlayerA else self.playerStates[1]
        for iSource, source in enumerate(itertools.chain(self.bins, (self.pool, ))):
            # BLAH = np.unique(source, return_counts=True) # todo
            for color, count in zip(*np.unique(source, return_counts=True)):
                if color == Color.Empty:
                    continue

                for iTarget, (targetQueue, targetRow) in enumerate(zip(player.queue, player.wall)):
                    # If the color isn't already on the wall in that row,
                    # and the queue has space (last element is empty),
                    # and the queue is completely empty (first element empty) or contains the same color.
                    if color not in targetRow and \
                            targetQueue[iTarget] == Color.Empty and \
                            (targetQueue[0] == Color.Empty or targetQueue[0] == color):

                        yield Move(iSource, iTarget, color, count)

                # It's always valid to put the tiles on the floor.
                yield Move(iSource, Azul.WallShape[0] + 1, color=color, count=count)




