from typing import *

from azulbot.game import Game, GameState
from azulcpp import AzulState as AzulStateCpp, Azul as AzulCpp, Move as MoveCpp
from azulcpp import Color, MoveOutcome


# Avoids metaclass conflict between abc and pybind.
class PybindAbcMeta(type(Game), type(AzulCpp)):
    pass


class Move(MoveCpp):

    @staticmethod
    def from_str(s: str) -> 'Move':
        return Move(int(s[0]), Azul.str_to_color(s[1]), int(s[2]))


class AzulState(AzulStateCpp, GameState, metaclass=PybindAbcMeta):
    pass


class Azul(AzulCpp, Game[AzulState, Move], metaclass=PybindAbcMeta):
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

    def get_score(self, state: AzulState, playerIndex: int) -> float:
        maxScore = max([p.score for p in state.players])
        isMax = state.players[playerIndex].score == maxScore
        # Draws should be losses.
        isOnly = sum(1 for p in state.players if p.score == maxScore) == 1

        return int(isMax and isOnly)

    @staticmethod
    def get_wall_column_by_color(iRow: int, color: Union[Color, int]) -> int:
        return (int(color) - 1 + iRow) % Azul.ColorNumber

    @staticmethod
    def color_to_str(color: Union[Color, int]) -> str:
        return Azul.ColorToChar[Color(color)]

    @staticmethod
    def str_to_color(s: str) -> Color:
        return Azul.CharToColor[s.upper().strip()]
