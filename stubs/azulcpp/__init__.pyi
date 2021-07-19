from enum import IntEnum
from typing import *


class Color(IntEnum):
    Empty = 0
    Blue = 1
    Yellow = 2
    Red = 3
    Black = 4
    White = 5


class Move:
    sourceBin: int
    color: Color
    targetQueue: int

    def __init__(self, sourceBin: int, color: Color, targetQueue: int): ...


class PlayerState:
    wall: List[List[int]]
    queue: List[List[int]]
    floorCount: int
    score: int

    def set_wall(self, rowIndex: int, colIndex: int, color: Color): ...
    def set_wall_row(self, rowIndex: int, colors: List[Color]): ...
    def set_wall_col(self, colIndex: int, colors: List[Color]): ...
    def set_queue(self, queueIndex: int, color: Color, count: int): ...


class AzulState:
    bag: List[int]
    bins: List[List[int]]
    players: List[PlayerState]

    nextPlayer: int
    firstPlayer: int
    poolWasTouched: bool

    roundIndex: int
    turnIndex: int

    def copy(self) -> AzulState: ...
    def set_bin(self, binIndex: int, color: Color, count: int): ...


class MoveOutcome:
    state: AzulState
    isRandom: bool
    isEnd: bool


class Azul:
    ColorNumber: int
    TileNumber: int
    PlayerNumber: int
    BinNumber: int
    BinSize: int
    WallSize: int
    FloorSize: int
    FloorScores: List[int]

    ScorePerRow: int
    ScorePerColumn: int
    ScorePerColor: int

    def enumerate_moves(self, state: AzulState) -> List[Move]: ...
    def apply_move(self, state: AzulState, move: Move) -> MoveOutcome:
        """
        Apply the move and do any necessary housekeeping, preparing for the next move.
        This method is meant for the MCTS implementation, which isn't aware of Azul specifics.

        :param state:
        :param move:
        """
        ...
    def apply_move_without_scoring(self, state: AzulState, move: Move) -> MoveOutcome:
        """
        Apply the move but do not do any housekeeping, i.e., do not score the round, do not deal a new round and do
        not score the game.
        This method is meant for organizing the game between bots/humans, where running the scoring manually
        makes it easier to track rounds.
        :param state:
        :param move:
        """
        ...
    def playout(self, state: AzulState, maxRoundTimeout: int = 100) -> AzulState: ...
    def is_game_end(self, state: AzulState) -> bool: ...

    def is_round_end(self, state: AzulState) -> bool: ...
    def deal_round(self, state: AzulState, fixedSample: List[Color] = []) -> AzulState: ...
    def score_round(self, state: AzulState) -> AzulState: ...
    def score_game(self, state: AzulState) -> AzulState: ...
    def _refill_bag(self, state: AzulState): ...
    @staticmethod
    def get_wall_slot_color(iRow: int, iCol: int) -> Color: ...


class MctsBot:

    def __init__(self, azul: Azul, state: AzulState, samplingWidth: int = 10,
                 explorationWeight: float = 1 / 1.4142): ...

    def step(self): ...
    def step_n(self, nSteps: int) -> Move: ...
    def get_best_move(self) -> Move: ...


