import cmd
from typing import *

from azulbot.azulsim import Azul, AzulState, Move
from azulbot.azulsim import MctsBot


class AzulCmd(cmd.Cmd):

    prompt = '> '

    def __init__(self):
        # Init with defaults.
        super().__init__()

        self.history = []  # type: List[AzulState]
        self.azul = Azul()
        self.state = self.azul.get_init_state()
        self.state = self.azul.deal_round(self.state)

        self.botPlayerIndex = 0
        # self.budget = 100000
        self.budget = 1000
        self.samplingWidth = 10
        self.explorationWeight = 20

    def preloop(self) -> None:
        super().preloop()

        Azul.print_state(self.state)

    def postcmd(self, stop: bool, line: str) -> bool:
        Azul.print_state(self.state)

        return super().postcmd(stop, line)

    def do_move(self, arg: str):
        bits = list(map(lambda s: s.strip(), arg.strip().split(' ')))

        # Parse the command.
        try:
            move = Move(int(bits[0]), Azul.str_to_color(bits[1]), int(bits[2]))
        except ValueError:
            print("# Invalid command")
            return

        self._apply_move(move)

    def do_bot_move(self, arg: str):
        bot = MctsBot(self.azul, self.state, samplingWidth=self.samplingWidth, explorationWeight=self.explorationWeight)
        move = bot.step_n(self.budget)

        print(f"Bot's move: ")
        print(f"Take {Azul.color_to_str(move.color)} from bin {move.sourceBin} to queue {move.targetQueue}")

        self._apply_move(move)

    def _apply_move(self, move):
        if self.azul.is_game_end(self.state):
            print("The game is over, can't do moves.")
            return

        self.history.append(self.state)

        # Apply the move.
        try:
            outcome = self.azul.apply_move_without_scoring(self.state, move)
            self.state = outcome.state

            if self.azul.is_round_end(self.state):
                self.state = self.azul.score_round(self.state)

                if not self.azul.is_game_end(self.state):
                    self.state = self.azul.deal_round(self.state)
                else:
                    self.state = self.azul.score_game(self.state)

                    winnerIndex = int(self.state.players[0].score > self.state.players[1].score)
                    humanIndex = 1 - self.botPlayerIndex
                    print(f"=== Game Over! ===")
                    print(f"{'Human' if winnerIndex != self.botPlayerIndex else 'Bot'} player wins")
                    print(f"Scores: Bot = {self.state.players[self.botPlayerIndex].score}    "
                          f"Human = {self.state.players[humanIndex].score}")

        except ValueError as e:
            print(f"# {e}")
            print("Undoing the move.")

            self.state = self.history.pop()

    def do_undo(self, arg: str):
        if len(self.history) == 0:
            print("# This is the first turn.")
            return

        print("# UNDO #")
        self.state = self.history.pop()


def main():
    azulCmd = AzulCmd()

    azulCmd.cmdloop()


if __name__ == '__main__':
    main()
