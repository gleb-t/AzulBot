import itertools
import random
from copy import deepcopy
from enum import IntEnum
from typing import *

import numpy as np


T = TypeVar('T')


def _arg_def(value: T, default: T) -> T:
    return value if value is not None else default


class Color(IntEnum):
    Empty = 0
    Blue = 1
    Yellow = 2
    Red = 3
    Black = 4
    White = 5


class Move(NamedTuple):
    sourceBin: int = 0
    color: int = Color.Empty
    targetQueue: int = 0

    @staticmethod
    def from_str(s: str) -> 'Move':
        return Move(int(s[0]), Azul.str_to_color(s[1]), int(s[2]))


class PlayerState:

    def __init__(self, wall: Optional[np.ndarray] = None, queue: Optional[np.ndarray] = None,
                 floorCount: Optional[int] = None, score: Optional[int] = None):
        self.wall = _arg_def(wall, np.zeros(Azul.WallShape, dtype=np.uint8))
        # Stores color and count per row.
        self.queue = _arg_def(queue, np.zeros((Azul.WallShape[0], 2), dtype=np.uint8))
        self.floorCount = _arg_def(floorCount, 0)

        self.score = _arg_def(score, 0)


class IllegalMoveException(Exception):
    pass


class Azul:
    ColorNumber = 5
    TileNumber = 20
    PlayerNumber = 2
    BinNumber = 5
    BinSize = 4
    WallShape = (5, 5)
    FloorSize = 7
    FloorScores = np.array([1, 1, 2, 2, 2, 3, 3], dtype=np.uint8)

    ScorePerRow = 2
    ScorePerColumn = 7
    ScorePerColor = 10

    ColorToChar = {
        Color.Empty: '_',
        Color.Blue: 'U',
        Color.Yellow: 'Y',
        Color.Red: 'R',
        Color.Black: 'K',
        Color.White: 'W'
    }
    CharToColor = dict(map(reversed, ColorToChar.items()))

    def __init__(self,
                 bag: Optional[np.ndarray] = None,
                 bins: Optional[np.ndarray] = None,
                 playerStates: Optional[List[PlayerState]] = None,
                 nextPlayer: Optional[int] = None,
                 firstPlayer: Optional[int] = None,
                 poolWasTouched: Optional[bool] = None):

        self.bag = _arg_def(bag, np.concatenate(([0], np.repeat(Azul.TileNumber, Azul.ColorNumber))))
        # Bins store the count indexed by the Color enum. The 'empty' color is always at zero.
        # The last bin is the 'pool'.
        self.bins = _arg_def(bins, np.zeros((Azul.BinNumber + 1, Azul.ColorNumber + 1), dtype=np.uint8))

        self.players = _arg_def(playerStates, [PlayerState() for _ in range(Azul.PlayerNumber)])

        self.nextPlayer = _arg_def(nextPlayer, 0)
        self.firstPlayer = _arg_def(firstPlayer, 0)
        self.poolWasTouched = _arg_def(poolWasTouched, False)

    def is_end_of_game(self) -> bool:
        for player in self.players:
            if np.any(np.count_nonzero(player.wall, axis=1) == Azul.WallShape[1]):
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

                        yield Move(iSource, color, iTarget)

                # It's always valid to put the tiles on the floor.
                yield Move(iSource, color, Azul.WallShape[0])

    def apply_move(self, move: Move) -> 'Azul':
        newState = deepcopy(self)
        newState._apply_move_inplace(move)

        return newState

    def _apply_move_inplace(self, move: Move):
        player = self.players[self.nextPlayer]
        count = self.bins[move.sourceBin, move.color]

        if count == 0:
            raise IllegalMoveException(f"Not allowed to take zero tiles. Move: {move}")

        # Update who goes first next round (changes when the pool is touched for the first time).
        if move.sourceBin == Azul.BinNumber:
            becomeFirstPlayer = not self.poolWasTouched
            self.poolWasTouched = True
            if becomeFirstPlayer:
                player.floorCount += 1
                self.firstPlayer = self.nextPlayer

        # Pass the turn to the next player.
        self.nextPlayer = (self.nextPlayer + 1) % Azul.PlayerNumber

        # Take away the tiles of the moved color.
        self.bins[move.sourceBin, move.color] = 0

        # If the move is to take tiles from a bin, then move the rest into the pool.
        if move.sourceBin < Azul.BinNumber:
            self.bins[Azul.BinNumber] += self.bins[move.sourceBin]
            self.bins[move.sourceBin] = 0

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

    def score_round(self):
        if not self.is_end_of_round():
            raise RuntimeError("Not allowed to score the round before it has ended.")

        for player in self.players:
            for iRow, q in enumerate(player.queue):
                color, count = q[0], q[1]
                if count == iRow + 1:
                    iCol = Azul.get_wall_column_by_color(iRow, color)
                    player.wall[iRow, iCol] = color
                    player.queue[iRow] = (Color.Empty, 0)
                    player.score += Azul.get_tile_score(player.wall, iRow, iCol)

            # Score the floor tiles.
            for i in range(player.floorCount):
                player.score = max(0, player.score - Azul.FloorScores[i])

            player.floorCount = 0

    def deal_round(self, fixedSample: Optional[List[Color]] = None):
        if not self.is_end_of_round():
            raise RuntimeError("Not allowed to deal a new round before the old has ended.")

        sampleSize = Azul.BinNumber * Azul.BinSize
        bagCount = sum(self.bag)
        if bagCount < sampleSize:
            assert Azul.PlayerNumber == 2 and bagCount == 0  # The bag can't have leftovers in a two-player game.
            self._refill_bag()

        if fixedSample is None:
            # sample = random.sample(Color, counts=self.bag, k=sampleSize)  # Sadly, only works in Python 3.9
            population = np.repeat(Color, repeats=self.bag)
            sample = np.random.choice(population, size=sampleSize, replace=False)
        else:
            # Allow the sampled tiles to be specified deterministically for testing.
            assert len(fixedSample) == sampleSize
            sample = fixedSample

        self.bins[...] = Color.Empty
        for iBin, iSample in enumerate(range(0, sampleSize, Azul.BinSize)):
            binSubsample = sample[iSample: iSample + Azul.BinSize]
            for color, count in zip(*np.unique(binSubsample, return_counts=True)):
                self.bins[iBin, color] = count

        for color in sample:
            self.bag[color] -= 1

        assert np.all(self.bag >= 0)

        self.poolWasTouched = False
        self.nextPlayer = self.firstPlayer

    def score_game(self):
        if not self.is_end_of_game():
            raise RuntimeError("Cannot score the game before the end of the game.")

        for player in self.players:
            player.score += np.sum(np.count_nonzero(player.wall, axis=1) == Azul.WallShape[1]) * Azul.ScorePerRow
            player.score += np.sum(np.count_nonzero(player.wall, axis=0) == Azul.WallShape[0]) * Azul.ScorePerColumn
            player.score += np.sum(1 for color, count in zip(*np.unique(player.wall, return_counts=True))
                                   if color != Color.Empty and count == Azul.WallShape[0]) * Azul.ScorePerColor

    def _refill_bag(self):
        # First, count all the tiles that lie on the board, they won't be redrawn.
        missingTiles = np.zeros(Azul.ColorNumber + 1)
        for player in self.players:
            for color, count in player.queue:
                missingTiles[color] += count

            for color, count in zip(*np.unique(player.wall, return_counts=True)):
                missingTiles[color] += count

        for color in Color:
            if color != Color.Empty:
                self.bag[color] = Azul.TileNumber - missingTiles[color]

        assert self.bag[Color.Empty] == 0

    def print_state(self):
        print('#' * 20)
        self._print_bins()

        for iPlayer in range(len(self.players)):
            self._print_player(iPlayer)

    def _print_bins(self):
        print("### Table ###")
        print("# Bins")
        for iRow, b in enumerate(self.bins[:-1]):
            line = ''.join(Azul.color_to_str(c) for c in Azul._bin_to_array(b))
            print(f"  [{iRow}]" + line.rjust(4, '_'))

        print("# Pool [{}]".format(' ' if self.poolWasTouched else '1'))
        line = ''.join(Azul.color_to_str(c) for c in Azul._bin_to_array(self.bins[-1]))
        print(f"  [{Azul.WallShape[0]}]" + line)

    def _print_player(self, playerIndex: int):
        player = self.players[playerIndex]

        nextTurnStr = ' (NEXT)' if self.nextPlayer == playerIndex else ''
        print(f"### Player {playerIndex}{nextTurnStr} ###")
        print("# Queue")
        for iRow, (color, count) in enumerate(player.queue):
            line = Azul.color_to_str(color) * count
            line = line.rjust(iRow + 1, '_')
            line = line.rjust(Azul.WallShape[0], ' ')
            print(f"  [{iRow}]" + line)
        print("# Floor")
        print("# " + ''.join(map(str, Azul.FloorScores)))
        line = ''.join('X' for _ in range(player.floorCount)).ljust(Azul.FloorSize, '_')
        print("  " + line)

        print("# Wall")
        for iRow, row in enumerate(player.wall):
            line = ''
            for iCol, color in enumerate(row):
                if color == Color.Empty:
                    line += Azul.color_to_str(Azul.get_wall_slot_color(iRow, iCol)).lower()
                else:
                    line += Azul.color_to_str(color)

            print("  " + line)

    @staticmethod
    def _bin_to_array(bin_: np.ndarray) -> np.ndarray:
        return np.repeat(Color, bin_)

    @staticmethod
    def color_to_str(color: Union[Color, int]) -> str:
        return Azul.ColorToChar[Color(color)]

    @staticmethod
    def str_to_color(s: str) -> Color:
        return Azul.CharToColor[s.upper().strip()]

    @staticmethod
    def get_tile_score(wall: np.ndarray, iRow: int, iCol: int) -> int:
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        neighbors = [0] * 4
        for i, d in enumerate(directions):
            pos = (iRow, iCol)
            while True:
                nextPos = pos[0] + d[0], pos[1] + d[1]
                if nextPos[0] < 0 or nextPos[0] >= Azul.WallShape[0] or \
                        nextPos[1] < 0 or nextPos[1] >= Azul.WallShape[0] or \
                        wall[nextPos] == Color.Empty:
                    break

                neighbors[i] += 1
                pos = nextPos

        # todo Is there a cleaner way?
        scoreRow = neighbors[0] + neighbors[1] + 1
        scoreCol = neighbors[2] + neighbors[3] + 1
        scoreRow = scoreRow if scoreRow > 1 else 0
        scoreCol = scoreCol if scoreCol > 1 else 0

        score = scoreRow + scoreCol

        return score if score > 0 else 1

    @staticmethod
    def get_wall_column_by_color(iRow: int, color: Union[Color, int]) -> int:
        return (int(color) - 1 + iRow) % Azul.ColorNumber

    @staticmethod
    def get_wall_slot_color(iRow: int, iCol: int) -> Color:
        # This generates the diagonal pattern on the playing board.
        return Color((iCol - iRow) % Azul.ColorNumber + 1)
