import cmd
from typing import *

import numpy as np

from azulbot.azul import Azul, PlayerState, Color, Move, IllegalMoveException


class AzulCmd(cmd.Cmd):

    prompt = '> '

    def __init__(self):
        # Init with defaults.
        super().__init__()

        self.history = []  # type: List[Azul]
        self.azul = Azul()

        self.azul.deal_round()

    def preloop(self) -> None:
        super().preloop()

        self.azul.print_state()

    def postcmd(self, stop: bool, line: str) -> bool:
        self.azul.print_state()
        return super().postcmd(stop, line)

    def do_move(self, arg: str):
        bits = list(map(lambda s: s.strip(), arg.strip().split(' ')))

        # Parse the command.
        try:
            move = Move(int(bits[0]), Azul.str_to_color(bits[1]), int(bits[2]))
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


def main():
    azulCmd = AzulCmd()

    azulCmd.cmdloop()


if __name__ == '__main__':
    main()
