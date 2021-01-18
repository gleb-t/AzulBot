from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import *


TMove = TypeVar('TMove')
TState = TypeVar('TState')


@dataclass
class MoveOutcome(Generic[TState]):
    state: TState
    isRandom: bool = False
    isEnd: bool = False


class GameState(metaclass=ABCMeta):

    @abstractmethod
    def copy(self) -> 'GameState':
        pass


class Game(Generic[TState, TMove], metaclass=ABCMeta):
    @abstractmethod
    def enumerate_moves(self, state: TState) -> List[TMove]:
        pass

    @abstractmethod
    def apply_move(self, state: TState, move: TMove) -> MoveOutcome[TState]:
        pass

    @abstractmethod
    def playout(self, state: TState) -> TState:
        pass

    @abstractmethod
    def is_game_end(self, state: TState) -> bool:
        pass

    @abstractmethod
    def get_score(self, state: TState, playerIndex: int) -> float:
        pass

    @staticmethod
    @abstractmethod
    def get_init_state():
        pass