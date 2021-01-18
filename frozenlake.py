import copy
import random
from dataclasses import dataclass
from typing import *

import gym
from gym.envs.registration import register

from azulbot import Game, MoveOutcome, GameState

register(
        id='FrozenLakeNotSlippery-v0',
        entry_point='gym.envs.toy_text:FrozenLakeEnv',
        kwargs={'map_name': '4x4', 'is_slippery': False}
)


@dataclass
class Move:
    d: int


@dataclass
class State(GameState):
    s: int

    def copy(self) -> 'State':
        return State(self.s)


class FrozenLake(Game[State, Move]):

    def __init__(self):
        self.env = gym.make('FrozenLakeNotSlippery-v0')
        self.isTerminalMap = {0: False}  # type: Dict[int, bool]
        self.scoreMap = {0: 0}  # type: Dict[int, float]

    def enumerate_moves(self, state: State) -> List[Move]:
        return [Move(d) for d in (0, 1, 2, 3)]

    def apply_move(self, state: State, move: Move) -> MoveOutcome[State]:
        self.env.reset()
        self.env.s = state.s

        s, reward, isEnd, _ = self.env.step(move.d)

        self.isTerminalMap[s] = isEnd
        self.scoreMap[s] = reward

        return MoveOutcome(State(s), False, isEnd)

    def playout(self, state: State) -> State:
        players = [lambda s: Move(random.choice((0, 1, 2, 3)))]

        isEnd = False
        while not isEnd:
            outcome = self.apply_move(state, players[0](state))
            state = outcome.state
            isEnd = outcome.isEnd

        return state

    def is_game_end(self, state: State) -> bool:
        # Hacky way of evaluating if a state is terminal and its score. Gym doesn't allow for it.
        if state.s in self.isTerminalMap:
            return self.isTerminalMap[state.s]
        else:
            raise RuntimeError(f"Haven't encountered state {state.s}, don't know if it is terminal.")

    def get_score(self, state: State, playerIndex: int) -> float:
        if state.s in self.scoreMap:
            return self.scoreMap[state.s]
        else:
            raise RuntimeError(f"Haven't encountered state {state.s}, don't know it's score.")

    @staticmethod
    def get_init_state():
        return State(0)
