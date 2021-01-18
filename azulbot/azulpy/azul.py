import random
from enum import IntEnum
from typing import *

import numpy as np
from numba import jit

from azulbot.game import MoveOutcome

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
    # Which bin to take tiles from. The last index means taking from the pool.
    sourceBin: int = 0
    # Which color to take. We always take all tiles of that color.
    color: int = Color.Empty
    # Which queue to put the tiles in. The last index means putting directly on the floor.
    targetQueue: int = 0

    @staticmethod
    def from_str(s: str) -> 'Move':
        return Move(int(s[0]), Azul.str_to_color(s[1]), int(s[2]))


class ComparableNumpy():
    """
    An abstract class implementing the equality operator
    with the support for numpy array fields.
    """
    def __eq__(self, o: object) -> bool:
        if type(self) == type(o):
            # Object's field could be changed dynamically, so we have to check the keys as well as values.
            if tuple(self.__dict__.keys()) != tuple(o.__dict__.keys()):
                return False
            for v1, v2 in zip(self.__dict__.values(), o.__dict__.values()):
                if isinstance(v1, np.ndarray):
                    if not np.array_equal(v1, v2):
                        return False
                elif v1 != v2:
                    return False

            return True
        else:
            return NotImplemented


class PlayerState(ComparableNumpy):

    def __init__(self, wall: Optional[np.ndarray] = None, queue: Optional[np.ndarray] = None,
                 floorCount: Optional[int] = None, score: Optional[int] = None):
        # A 2D array that stores the color value at each position.
        # (Somewhat redundant, but support playing with the 'free board' variant.)
        self.wall = _arg_def(wall, np.zeros(Azul.WallShape, dtype=np.uint8))
        # Stores color and count per row.
        self.queue = _arg_def(queue, np.zeros((Azul.WallShape[0], 2), dtype=np.uint8))
        # The number of tiles lying on the floor. (The color is irrelevant.)
        self.floorCount = _arg_def(floorCount, 0)

        self.score = _arg_def(score, 0)

    def __hash__(self) -> int:
        return hash(tuple(map(hash, (self.wall.tobytes(), self.queue.tobytes(), self.floorCount, self.score))))

    def copy(self) -> 'PlayerState':
        return PlayerState(self.wall.copy(), self.queue.copy(), self.floorCount, self.score)


class IllegalMoveException(Exception):
    pass


class Azul(ComparableNumpy):

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

        # A 1D array that stores how many tiles of each color are left in the bag (indexed by the Color enum).
        # The 'empty' color is always at zero.
        self.bag = _arg_def(bag, np.concatenate(([0], np.repeat(Azul.TileNumber, Azul.ColorNumber))))
        # Bins store the count per color, similarly to the bag.
        # The last bin is the 'pool'.
        self.bins = _arg_def(bins, np.zeros((Azul.BinNumber + 1, Azul.ColorNumber + 1), dtype=np.uint8))

        self.players = _arg_def(playerStates, [PlayerState() for _ in range(Azul.PlayerNumber)])

        # The index of the player, whose turn it is to make a move.
        self.nextPlayer = _arg_def(nextPlayer, 0)
        # The index of the player that will go first in the next round.
        self.firstPlayer = _arg_def(firstPlayer, 0)
        # Whether someone has already taken tiles from the center (the pool) this round.
        self.poolWasTouched = _arg_def(poolWasTouched, False)

    def __hash__(self) -> int:
        return hash(tuple(map(hash, (self.bag.tobytes(), self.bins.tobytes(),
                                     tuple(map(hash, self.players)),
                                     self.nextPlayer, self.firstPlayer, self.poolWasTouched))))

    def copy(self) -> 'Azul':
        return Azul(self.bag.copy(), self.bins.copy(), [p.copy() for p in self.players],
                    self.nextPlayer, self.firstPlayer, self.poolWasTouched)

    def is_game_end(self) -> bool:
        for player in self.players:
            if np.any(np.count_nonzero(player.wall, axis=1) == Azul.WallShape[1]):
                return True

        return False

    def is_round_end(self) -> bool:
        return np.all(self.bins == 0)

    def enumerate_moves(self):
        """
        Enumerate all legal moves in the current state.
        """
        player = self.players[self.nextPlayer]
        return Azul._enumerate_moves_fast(self.bins, player.queue, player.wall, Azul.WallShape[0])

    @staticmethod
    @jit(nopython=True)
    def _enumerate_moves_fast(bins: np.ndarray, queue: np.ndarray, wall: np.ndarray,
                              floorIndex: int = 5):
        moves = []
        for iSource, source in enumerate(bins):
            for color, count in enumerate(source):
                if count == 0 or color == Color.Empty:
                    continue

                for iTarget, (targetQueue, targetRow) in enumerate(zip(queue, wall)):
                    # If the color isn't already on the wall in that row,
                    # and the queue has space (its size is index+1),
                    # and the queue is completely empty (first element empty) or contains the same color.
                    if np.all(targetRow != color) and \
                            targetQueue[1] < iTarget + 1 and \
                            (targetQueue[0] == Color.Empty or targetQueue[0] == color):
                        moves.append(Move(iSource, color, iTarget))

                # It's always valid to put the tiles on the floor.
                moves.append(Move(iSource, color, floorIndex))

        return moves

    def apply_move(self, move: Move) -> MoveOutcome['Azul']:
        newState = self.copy()
        newState._apply_move_inplace(move)

        return MoveOutcome(newState, isRandom=newState.is_round_end(), isEnd=newState.is_game_end())

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

    def playout(self, players: Optional[List[Callable[['Azul'], Move]]] = None, maxRoundTimeout: int = 100):
        if players is None:
            def random_bot(az: Azul):
                return random.choice(tuple(az.enumerate_moves()))

            players = [random_bot] * Azul.PlayerNumber

        roundCount = 0
        while not self.is_game_end():
            # We might get a game in the middle of a round, so we have to check.
            if self.is_round_end():
                self.deal_round()

            while not self.is_round_end():
                move = players[self.nextPlayer](self)
                self._apply_move_inplace(move)

            self.score_round()
            roundCount += 1

            if roundCount > maxRoundTimeout:
                raise RuntimeError(f"Timed out after {maxRoundTimeout} rounds.")

        self.score_game()

    def get_score(self, playerIndex: int) -> float:
        if not self.is_game_end():
            return 0

        assert len(self.players) == 2

        # 1 if won, 0 otherwise.
        return int(self.players[playerIndex].score > self.players[(playerIndex + 1) % 2].score)

    def score_round(self):
        """
        Move the tiles from the queue to the wall and score them.
        """
        if not self.is_round_end():
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
            for i in range(min(player.floorCount, Azul.FloorSize)):
                player.score = max(0, player.score - Azul.FloorScores[i])

            player.floorCount = 0

    def deal_round(self, fixedSample: Optional[List[Color]] = None):
        if not self.is_round_end():
            raise RuntimeError("Not allowed to deal a new round before the old has ended.")

        # Refill the bag using the discarded tiles, if necessary.
        sampleSize = Azul.BinNumber * Azul.BinSize
        bagCount = sum(self.bag)
        if bagCount < sampleSize:
            self._refill_bag()

        # Randomly sample the bag to get the tiles for this round.
        if fixedSample is None:
            # sample = random.sample(Color, counts=self.bag, k=sampleSize)  # Sadly, only works in Python 3.9
            population = np.repeat(Color, repeats=self.bag)
            sample = np.random.choice(population, size=sampleSize, replace=False)
        else:
            # Allow the sampled tiles to be specified deterministically for testing.
            assert len(fixedSample) == sampleSize
            sample = fixedSample

        # Distribute the sampled tiles among the bins.
        self.bins[...] = Color.Empty
        for iBin, iSample in enumerate(range(0, sampleSize, Azul.BinSize)):
            binSubsample = sample[iSample: iSample + Azul.BinSize]
            for color, count in zip(*np.unique(binSubsample, return_counts=True)):
                self.bins[iBin, color] = count

        # Keep track of which tiles are left in the bag.
        for color in sample:
            self.bag[color] -= 1

        assert np.all(self.bag >= 0)

        # Prepare the first player flags.
        self.poolWasTouched = False
        self.nextPlayer = self.firstPlayer

    def score_game(self):
        if not self.is_game_end():
            raise RuntimeError("Cannot score the game before the end of the game.")

        for player in self.players:
            # Score full rows.
            player.score += np.sum(np.count_nonzero(player.wall, axis=1) == Azul.WallShape[1]) * Azul.ScorePerRow
            # Score full columns.
            player.score += np.sum(np.count_nonzero(player.wall, axis=0) == Azul.WallShape[0]) * Azul.ScorePerColumn
            # Score complete colors.
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

        # The rest are the discarded tiles that return back into the bag.
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
        """
        Compute the score awarded for placing a tile onto the wall.
        """
        # Compute how many consecutive neighbors lie in each direction.
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

        # Compute the total score based on the neighbor information.
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


