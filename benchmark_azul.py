import random
from typing import *

import numpy as np

from azulbot.azulsim import Azul, Move, AzulState
from lib.StageTimer import StageTimer
from mcts_bot import MctsBot


def build_random_bot():
    azul = Azul()

    def _bot(state: AzulState) -> Move:
        return random.choice(tuple(azul.enumerate_moves(state)))

    return _bot


def build_mcts_bot(budget: int = 1000):
    azul = Azul()

    def _bot(state: AzulState):
        mcts = MctsBot(azul, state, state.nextPlayer)
        for _ in range(budget):
            mcts.step()

        return mcts.get_best_move()

    return _bot


def main():
    gamesToPlay = 10
    maxRoundsPerGame = 100
    mctsBudget = 10000

    azul = Azul()
    players = [build_random_bot(), build_mcts_bot(mctsBudget)]
    scores = []
    timePerMove = []

    timer = StageTimer()
    for iGame in range(gamesToPlay):
        timer.start_pass()

        state = azul.get_init_state()

        roundCount = 0
        moveCount = 0
        for _ in range(maxRoundsPerGame):
            timer.start_stage('deal')
            state = azul.deal_round(state)

            while not azul.is_round_end(state):
                timer.start_stage('decide')
                move = players[state.nextPlayer](state)
                timer.start_stage('move')
                state = azul.apply_move(state, move).state
                moveCount += 1 if state.nextPlayer == 1 else 0

            timer.start_stage('score')
            state = azul.score_round(state)
            roundCount += 1

            if azul.is_game_end(state):
                state = azul.score_game(state)
                break

        timer.end_stage()

        if azul.is_game_end(state):
            timer.end_pass()
            dur = timer.get_pass_duration()
            scores.append([state.players[0].score, state.players[1].score])
            timePerMove.append(timer.get_pass_timings()['decide'] / moveCount)
            print(f"Finished a game with scores {state.players[0].score}:{state.players[1].score}"
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
    print("Average time per move: {:.1f}".format(np.mean(np.array(timePerMove))))
    print("Wins: {} vs {}".format(winsFirst, winsSecond))
    print("Done.")


if __name__ == '__main__':
    main()
