import copy
import random
from dataclasses import dataclass
from typing import Optional, List, Callable, Generator

import gym
from gym.envs.registration import register

from azulbot import GameState, TMove, MoveOutcome


register(
        id='FrozenLakeNotSlippery-v0',
        entry_point='gym.envs.toy_text:FrozenLakeEnv',
        kwargs={'map_name': '4x4', 'is_slippery': False}
)
_env = gym.make('FrozenLakeNotSlippery-v0')


@dataclass
class Move:
    d: int


class FrozenLake(GameState[Move]):

    def __init__(self):
        self.state = _env.reset()
        self.reward = None
        self.isEnd = False

    def enumerate_moves(self) -> List[Move]:
        return [Move(d) for d in (0, 1, 2, 3)]

    def apply_move(self, move: Move) -> MoveOutcome['FrozenLake']:
        newState = copy.copy(self)
        newState._apply_move_inplace(move)
        return MoveOutcome(newState, False, newState.isEnd)

    def _apply_move_inplace(self, move: Move):
        _env.reset()
        _env.s = self.state

        self.state, self.reward, self.isEnd, _ = _env.step(move.d)

    def playout(self, players: Optional[List[Callable[['FrozenLake'], Move]]] = None):
        if players is None:
            players = [lambda s: Move(random.choice((0, 1, 2, 3)))]

        while not self.isEnd:
            self._apply_move_inplace(players[0](self))

    def is_game_end(self) -> bool:
        return self.isEnd

    def get_score(self, playerIndex: int) -> float:
        return self.reward
