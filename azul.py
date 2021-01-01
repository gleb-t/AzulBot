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

    def __init__(self,
                 bagCount: Optional[np.ndarray] = None,
                 bins: Optional[np.ndarray] = None,
                 playerStates: Optional[List[PlayerState]] = None,
                 nextPlayer: Optional[int] = None,
                 firstPlayer: Optional[int] = None,
                 poolWasTouched: Optional[bool] = None):

        self.bagCount = bagCount or np.repeat(20, Azul.ColorNumber + 1)
        # Bins store the count indexed by the Color enum. The 'empty' color is always at zero.
        # The last bin is the 'pool'.
        self.bins = bins or np.zeros((Azul.BinNumber + 1, Azul.ColorNumber + 1), dtype=np.uint8)

        self.players = playerStates or [PlayerState() for _ in range(Azul.PlayerNumber)]

        self.nextPlayer = nextPlayer if nextPlayer is not None else 0
        self.firstPlayer = firstPlayer if firstPlayer is not None else 0
        self.poolWasTouched = poolWasTouched if poolWasTouched is not None else False

    def is_end_of_game(self) -> bool:
        for player in self.players:
            if np.any(np.count_nonzero(player.wall, axis=0) == 0):
                return True

        return False

    def is_end_of_round(self) -> bool:
        return np.all(self.bins == 0)

    def enumerate_moves(self):
        player = self.players[self.nextPlayer]
        for iSource, source in enumerate(self.bins):
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

                        yield Move(iSource, iTarget, color)

                # It's always valid to put the tiles on the floor.
                yield Move(iSource, Azul.WallShape[0], color)

    def apply_move(self, move: Move) -> 'Azul':
        newState = deepcopy(self)
        newState._apply_move_inplace(move)

        return newState

    def _apply_move_inplace(self, move: Move):
        player = self.players[self.nextPlayer]
        count = self.bins[move.sourceBin, move.color]

        # Update who goes first next round (changes when the pool is touched for the first time).
        if move.sourceBin == Azul.BinNumber:
            becomeFirstPlayer = not self.poolWasTouched
            self.poolWasTouched = True
            if becomeFirstPlayer:
                player.floorCount += 1
                self.firstPlayer = self.nextPlayer

        # Pass the turn to the next player.
        self.nextPlayer = (self.nextPlayer + 1) % Azul.PlayerNumber

        # Take away the tiles.
        self.bins[move.sourceBin, move.color] = 0

        # If the move is to take tiles from a bin, then move the rest into the pool.
        if move.sourceBin < Azul.BinNumber:
            self.bins[Azul.BinNumber] += self.bins[move.sourceBin]

        if move.targetQueue < Azul.WallShape[0]:
            # Place the tiles into the queue.
            queueSize = move.targetQueue + 1
            queueCount = player.queue[move.targetQueue][1]
            newCount = queueCount + count
            # Put the tiles into the queue, move the leftovers onto the floor.
            player.queue[move.targetQueue] = (move.color, min(newCount, queueSize))
            player.floorCount += max(newCount - queueSize, 0)
        else:
            # Place tiles onto the floor.
            player.floorCount += count

    @staticmethod
    def get_wall_slot_color(index: Tuple[int, int]) -> Color:
        # This generates the diagonal pattern on the playing board.
        return Color((index[1] - index[0]) % Azul.ColorNumber + 1)
