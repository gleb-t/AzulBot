import random
from typing import *

from azul import Azul
from lib.StageTimer import StageTimer


def main():
    gamesToPlay = 100
    maxRoundsPerGame = 100

    timer = StageTimer()
    for iGame in range(gamesToPlay):
        timer.start_pass()

        azul = Azul()

        roundCount = 0
        for _ in range(maxRoundsPerGame):
            timer.start_stage('deal')
            azul.deal_round()

            while not azul.is_end_of_round():
                timer.start_stage('enumerate')
                move = random.choice(list(azul.enumerate_moves()))
                timer.start_stage('move')
                azul = azul.apply_move(move)

            timer.start_stage('score')
            azul.score_round()
            roundCount += 1

            if azul.is_end_of_game():
                azul.score_game()
                break

        timer.end_stage()

        if azul.is_end_of_game():
            timer.end_pass()
            dur = timer.get_pass_duration()
            print(f"Finished a game with scores {azul.players[0].score}:{azul.players[1].score}"
                  f" in {roundCount} rounds and {dur:.2f} s.")

        else:
            print("Timed out playing a game.")

    timer.end()
    print(timer.get_total_report())
    print("Done.")


if __name__ == '__main__':
    main()
