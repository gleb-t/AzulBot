import operator
import random
from typing import *

import numpy as np

from azulbot.azulsim import Azul, Move, AzulState
from lib.StageTimer import StageTimer
# from mcts_bot import MctsBot
from azulbot.azulsim import MctsBot


def build_random_bot():
    azul = Azul()

    def _bot(state: AzulState) -> Move:
        return random.choice(tuple(azul.enumerate_moves(state)))

    return _bot


def build_greedy_bot():
    azul = Azul()

    def _bot(state: AzulState) -> Move:

        player = state.players[state.nextPlayer]

        def get_move_stats(move: Move) -> Tuple[float, ...]:
            tilesAvailable = state.bins[move.sourceBin][int(move.color)]
            if move.targetQueue == Azul.WallSize:
                return tilesAvailable, 0, 0

            spaceLeft = move.targetQueue + 1 - player.queue[move.targetQueue][1]

            tilesMoved = min(tilesAvailable, spaceLeft)
            tilesDropped = -min(0, spaceLeft - tilesAvailable)
            extraSpace = max(0, spaceLeft - tilesAvailable)

            return tilesDropped, -tilesMoved, extraSpace

        moves = azul.enumerate_moves(state)
        moveStats = map(get_move_stats, moves)

        bestMove = min(zip(moves, moveStats), key=operator.itemgetter(1))[0]

        return bestMove

    return _bot


class MctsBotWrapper:

    def __init__(self, budget: int = 1000, samplingWidth: int = 10):
        self.budget = budget
        self.samplingWidth = samplingWidth

    def __call__(self, state):
        azul = Azul()
        self.bot = MctsBot(azul, state, state.nextPlayer, samplingWidth=self.samplingWidth)

        for _ in range(self.budget):
            self.bot.step()

        return self.bot.get_best_move()


def main():
    gamesToPlay = 10
    maxRoundsPerGame = 100
    mctsBudget = 100000
    samplingWidth = 10

    azul = Azul()
    # players = [build_random_bot(), build_mcts_bot(mctsBudget)]
    players = [build_greedy_bot(), MctsBotWrapper(mctsBudget, samplingWidth)]
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
                state = azul.apply_move_without_scoring(state, move).state
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
