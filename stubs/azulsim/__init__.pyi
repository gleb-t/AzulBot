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


class AzulState:
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

    bag: List[int]
    bins: List[List[int]]
    players: List[PlayerState]

    nextPlayer: int
    firstPlayer: int
    wasPoolTouched: bool

    def set_bin(self, binIndex: int, color: Color, count: int): ...
    def enumerate_moves(self) -> List[Move]: ...

