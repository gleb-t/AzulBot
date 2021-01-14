from typing import *

from azulcpp import AzulState as AzulStateCpp, Azul as AzulCpp, Move as MoveCpp
from azulcpp import Color, MoveOutcome


class AzulState(AzulStateCpp):
    pass


class Azul(AzulCpp):
    ColorToChar = {
        Color.Empty: '_',
        Color.Blue: 'U',
        Color.Yellow: 'Y',
        Color.Red: 'R',
        Color.Black: 'K',
        Color.White: 'W'
    }
    CharToColor = dict(map(reversed, ColorToChar.items()))

    def get_init_state(self) -> AzulState:
        return AzulState()

    @staticmethod
    def get_wall_column_by_color(iRow: int, color: Union[Color, int]) -> int:
        return (int(color) - 1 + iRow) % Azul.ColorNumber

    @staticmethod
    def color_to_str(color: Union[Color, int]) -> str:
        return Azul.ColorToChar[Color(color)]

    @staticmethod
    def str_to_color(s: str) -> Color:
        return Azul.CharToColor[s.upper().strip()]


class Move(MoveCpp):

    @staticmethod
    def from_str(s: str) -> 'Move':
        return Move(int(s[0]), Azul.str_to_color(s[1]), int(s[2]))