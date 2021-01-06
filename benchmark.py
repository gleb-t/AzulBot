import random
from typing import *

import numpy as np

from azulbot.azul import Azul, Move
from lib.StageTimer import StageTimer
from mcts_bot import MctsBot


def random_bot(azul: Azul) -> Move:
    return random.choice(tuple(azul.enumerate_moves()))


def build_mcts_bot(budget: int = 1000):
    def _bot(azul: Azul):
        mcts = MctsBot(azul)
        for _ in range(budget):
            mcts.step()

        return mcts.get_best_move()

    return _bot


def main():
    gamesToPlay = 50
    maxRoundsPerGame = 100
    mctsBudget = 10

    players = [random_bot, build_mcts_bot(mctsBudget)]
    scores = []

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
                move = players[azul.nextPlayer](azul)
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
            scores.append([azul.players[0].score, azul.players[1].score])
            print(f"Finished a game with scores {azul.players[0].score}:{azul.players[1].score}"
                  f" in {roundCount} rounds and {dur:.2f} s.")

        else:
            print("Timed out playing a game.")

    timer.end()

    scoresArray = np.array(scores)
    scoresAvg = scoresArray.mean(axis=0)
    winsFirst = np.count_nonzero(scoresArray[:, 0] > scoresArray[:, 1])
    winsSecond = np.count_nonzero(scoresArray[:, 0] < scoresArray[:, 1])
    # Could be a draw.

    print(timer.get_total_report())
    print("Average scores: {:.1f} {:.1f}".format(*tuple(scoresAvg)))
    print("Wins: {} vs {}".format(winsFirst, winsSecond))
    print("Done.")


if __name__ == '__main__':
    main()
