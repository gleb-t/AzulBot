import random
from typing import *

import numpy as np

from frozenlake import FrozenLake, Move, State
from lib.StageTimer import StageTimer
from mcts_bot import MctsBot


def build_random_bot():
    lake = FrozenLake()

    def _bot(state: State) -> Move:
        return random.choice(tuple(lake.enumerate_moves(state)))

    return _bot


def build_mcts_bot(budget: int = 1000):
    lake = FrozenLake()

    def _bot(state: State):
        mcts = MctsBot(lake, state, 0)
        for _ in range(budget):
            mcts.step()

        return mcts.get_best_move()

    return _bot


def main():
    random.seed(0)

    gamesToPlay = 100
    mctsBudget = 1000

    players = [build_mcts_bot(mctsBudget)]
    scores = []
    rounds = []

    timer = StageTimer()
    for iGame in range(gamesToPlay):
        timer.start_pass()

        game = FrozenLake()
        state = game.get_init_state()

        roundCount = 0
        while not game.is_game_end(state):
            timer.start_stage('decide')
            move = players[0](state)
            timer.start_stage('move')
            state = game.apply_move(state, move).state

            # _env.reset()
            # _env.s = game.state
            # print(_env.render())

            roundCount += 1

        timer.end_pass()
        dur = timer.get_pass_duration()
        score = game.get_score(state, 0)
        scores.append([score])
        rounds.append([roundCount])
        print(f"Finished a game with score {score}"
              f" in {roundCount} rounds and {dur:.2f} s.")

    timer.end()

    scoresArray = np.array(scores)
    scoresAvg = scoresArray.mean(axis=0)
    wins = np.count_nonzero(scoresArray[:, 0] > 0)

    print(timer.get_total_report())
    print("Average score: {:.1f}".format(*tuple(scoresAvg)))
    print("Average moves: {:.1f}".format(np.mean(np.array(rounds)).item()))
    print("Rounds of 6: {:.1f}".format(np.count_nonzero(np.array(rounds) == 6)))
    print("Wins: {}".format(wins))
    print("Done.")


if __name__ == '__main__':
    main()
