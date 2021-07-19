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

    def print_state(self):
        print('#' * 20)
        self._print_bins()

        for iPlayer in range(len(self.players)):
            self._print_player(iPlayer)

    def _print_bins(self):
        print("### Table ###")
        print("# Bins")
        for iRow, b in enumerate(self.bins[:-1]):
            line = ''.join(Azul.color_to_str(c) for c in AzulState._bin_to_array(b))
            print(f"  [{iRow}]" + line.rjust(4, '_'))

        print("# Pool [{}]".format(' ' if self.poolWasTouched else '1'))
        line = ''.join(Azul.color_to_str(c) for c in AzulState._bin_to_array(self.bins[-1]))
        print(f"  [{Azul.WallSize}]" + line)

    def _print_player(self, playerIndex: int):
        player = self.players[playerIndex]

        nextTurnStr = ' (NEXT)' if self.nextPlayer == playerIndex else ''
        print(f"### Player {playerIndex}{nextTurnStr} ###")
        print("# Queue")
        for iRow, (color, count) in enumerate(player.queue):
            line = Azul.color_to_str(color) * count
            line = line.rjust(iRow + 1, '_')
            line = line.rjust(Azul.WallSize, ' ')
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
    def _bin_to_array(bin_: List[int]) -> List[int]:
        result = []
        for iColor, count in enumerate(bin_):
            result += [Color(iColor)] * count

        return result



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

    # def get_score(self, state: AzulState, playerIndex: int) -> float:
    #     maxScore = max([p.score for p in state.players])
    #     isMax = state.players[playerIndex].score == maxScore
    #     # Draws should be losses.
    #     isOnly = sum(1 for p in state.players if p.score == maxScore) == 1
    #
    #     return int(isMax and isOnly)

    @staticmethod
    def get_wall_column_by_color(iRow: int, color: Union[Color, int]) -> int:
        return (int(color) - 1 + iRow) % Azul.ColorNumber

    @staticmethod
    def color_to_str(color: Union[Color, int]) -> str:
        return Azul.ColorToChar[Color(color)]

    @staticmethod
    def str_to_color(s: str) -> Color:
        return Azul.CharToColor[s.upper().strip()]
