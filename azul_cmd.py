import cmd
from typing import *

import numpy as np

from azul import Azul, PlayerState, Color, Move, IllegalMoveException


class AzulCmd(cmd.Cmd):
    ColorToChar = {
        Color.Empty: '_',
        Color.Blue: 'U',
        Color.Yellow: 'Y',
        Color.Red: 'R',
        Color.Black: 'K',
        Color.White: 'W'
    }
    CharToColor = dict(map(reversed, ColorToChar.items()))

    prompt = '> '

    def __init__(self):
        # Init with defaults.
        super().__init__()

        self.history = []  # type: List[Azul]
        self.azul = Azul()

        self.azul.deal_round()

    def preloop(self) -> None:
        super().preloop()

        self.print_state()

    def postcmd(self, stop: bool, line: str) -> bool:
        self.print_state()
        return super().postcmd(stop, line)

    def do_move(self, arg: str):
        bits = list(map(lambda s: s.strip(), arg.strip().split(' ')))

        # Parse the command.
        try:
            move = Move(int(bits[0]), int(bits[1]), AzulCmd._str_to_color(bits[2]))
        except ValueError:
            print("# Invalid command")
            return

        # Apply the move.
        self.history.append(self.azul)
        try:
            self.azul = self.azul.apply_move(move)
        except IllegalMoveException as e:
            print(f"# {e}")
            self.history.pop()

    def do_undo(self, arg: str):
        if len(self.history) == 0:
            print("# This is the first turn.")
            return

        print("# UNDO #")
        self.azul = self.history.pop()

    def print_state(self):
        print('#' * 20)
        self._print_bins()

        for iPlayer in range(len(self.azul.players)):
            self._print_player(iPlayer)

    def _print_bins(self):
        print("### Table ###")
        print("# Bins")
        for iRow, b in enumerate(self.azul.bins[:-1]):
            line = ''.join(AzulCmd._color_to_str(c) for c in AzulCmd._bin_to_array(b))
            print(f"  [{iRow}]" + line.rjust(4, '_'))

        print("# Pool [{}]".format(' ' if self.azul.poolWasTouched else '1'))
        line = ''.join(AzulCmd._color_to_str(c) for c in AzulCmd._bin_to_array(self.azul.bins[-1]))
        print(f"  [{Azul.WallShape[0]}]" + line)

    def _print_player(self, playerIndex: int):
        player = self.azul.players[playerIndex]

        nextTurnStr = ' (NEXT)' if self.azul.nextPlayer == playerIndex else ''
        print(f"### Player {playerIndex}{nextTurnStr} ###")
        print("# Queue")
        for iRow, (color, count) in enumerate(player.queue):
            line = AzulCmd._color_to_str(color) * count
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
                    line += AzulCmd._color_to_str(Azul.get_wall_slot_color(iRow, iCol)).lower()
                else:
                    line += AzulCmd._color_to_str(color)

            print("  " + line)

    @staticmethod
    def _bin_to_array(bin_: np.ndarray) -> np.ndarray:
        return np.repeat(Color, bin_)

    @staticmethod
    def _color_to_str(color: Union[Color, int]) -> str:
        return AzulCmd.ColorToChar[Color(color)]

    @staticmethod
    def _str_to_color(s: str) -> Color:
        return AzulCmd.CharToColor[s.upper().strip()]


def main():
    azulCmd = AzulCmd()

    azulCmd.cmdloop()


if __name__ == '__main__':
    main()
