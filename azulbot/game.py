import copy
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import *


TMove = TypeVar('TMove')
TGame = TypeVar('TGame')


@dataclass
class MoveOutcome(Generic[TGame]):
    state: 'TGame'
    isRandom: bool = False
    isEnd: bool = False


class GameState(Generic[TMove], metaclass=ABCMeta):

    def copy(self) -> 'GameState[TMove]':
        return copy.deepcopy(self)

    @abstractmethod
    def enumerate_moves(self) -> List[TMove]:
        pass

    @abstractmethod
    def apply_move(self, move: TMove) -> MoveOutcome['GameState[TMove]']:
        pass

    @abstractmethod
    def playout(self, players: Optional[List[Callable[['GameState[TMove]'], TMove]]] = None):
        pass

    @abstractmethod
    def is_game_end(self) -> bool:
        pass

    @abstractmethod
    def get_score(self, playerIndex: int) -> float:
        pass
