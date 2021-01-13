from typing import *

from azulcpp import AzulState as AzulStateCpp, Azul as AzulCpp
from azulcpp import Color, Move, MoveOutcome


class AzulState(AzulStateCpp):
    pass


class Azul(AzulCpp):

    def get_init_state(self) -> AzulState:
        return AzulState()

    @staticmethod
    def get_wall_column_by_color(iRow: int, color: Union[Color, int]) -> int:
        return (int(color) - 1 + iRow) % Azul.ColorNumber
