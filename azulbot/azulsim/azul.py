from typing import *

from azulbot.game import Game, GameState
from azulcpp import Azul as AzulCpp, Move as MoveCpp
from azulcpp import AzulState, Color, MoveOutcome


# Avoids metaclass conflict between abc and pybind.
class PybindAbcMeta(type(Game), type(AzulCpp)):
    pass


class Move(MoveCpp):

    @staticmethod
    def from_str(s: str) -> 'Move':
        return Move(int(s[0]), Azul.str_to_color(s[1]), int(s[2]))



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
    def print_state(state: AzulState):
        print('=' * 20 + f' Round {state.roundIndex + 1} Turn {state.turnIndex + 1} ' + '=' * 20)
        Azul._print_bins(state)

        for iPlayer in range(len(state.players)):
            Azul._print_player(state, iPlayer)

    @staticmethod
    def _print_bins(state: AzulState):
        print("### Table ###")
        print("# Bins")
        for iRow, b in enumerate(state.bins[:-1]):
            line = ''.join(Azul.color_to_str(c) for c in Azul._bin_to_array(b))
            print(f"  [{iRow}]" + line.rjust(4, '_'))

        print("# Pool [{}]".format(' ' if state.poolWasTouched else '1'))
        line = ''.join(Azul.color_to_str(c) for c in Azul._bin_to_array(state.bins[-1]))
        print(line)

    @staticmethod
    def _print_player(state: AzulState, playerIndex: int):
        player = state.players[playerIndex]

        nextTurnStr = ' (NEXT)' if state.nextPlayer == playerIndex else ''
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

    @staticmethod
    def get_wall_column_by_color(iRow: int, color: Union[Color, int]) -> int:
        return (int(color) - 1 + iRow) % Azul.ColorNumber

    @staticmethod
    def color_to_str(color: Union[Color, int]) -> str:
        return Azul.ColorToChar[Color(color)]

    @staticmethod
    def str_to_color(s: str) -> Color:
        return Azul.CharToColor[s.upper().strip()]
