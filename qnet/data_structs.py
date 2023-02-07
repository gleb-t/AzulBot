import copy
from dataclasses import dataclass
from typing import *

# import torch
# import numpy as np

# from bots.tictac import Square, Board
from azulbot.azulsim import Azul, Move, Color, AzulState, PlayerState


# class AzulObs:
#     # The players do not see the bag, but they could memorize what's left in it.
#     # We include the bag in the observation, so that the game is fully obesrvable.
#     bag: List[int]
#
#     bins: List[List[int]]
#     players: List[PlayerState]
#
#     nextPlayer: int
#     firstPlayer: int
#     poolWasTouched: bool
#
#     roundIndex: int
#     turnIndex: int
#
#     def __init__(self, state: AzulState):
#         self.bag = state.bag
#         self.bins = copy.deepcopy(state.bins)
#         self.players = copy.deepcopy(state.players)
#
#         self.nextPlayer = state.nextPlayer
#         self.firstPlayer = state.firstPlayer
#         self.poolWasTouched = state.poolWasTouched
#
#         self.roundIndex = state.roundIndex
#         self.turnIndex = state.turnIndex

# Currently the observation is the same as the state. So we just reuse the type.
# However, we swap the players so that the 'current' player is always first.
class AzulObs(AzulState):

    def __init__(self, state: AzulState, player_index):
        self.bag = copy.deepcopy(state.bag)
        self.bins = copy.deepcopy(state.bins)
        self.players = copy.deepcopy(state.players)

        if player_index != 0:
            assert player_index == 1
            self.players = [self.players[1], self.players[0]]

        self.nextPlayer = state.nextPlayer
        self.firstPlayer = state.firstPlayer
        self.poolWasTouched = state.poolWasTouched

        self.roundIndex = state.roundIndex
        self.turnIndex = state.turnIndex


@dataclass
class Transition:
    obs: AzulObs
    action: Move
    valid_actions: List[Move]
    reward: float
    done: bool = False

    @staticmethod
    def get_empty_transition():
        return Transition(AzulState(), Move(0, 0, Color.Blue), [Move(0, 0, Color.Blue)], 0.0, False)


class Episode(NamedTuple):
    transitions: List[Transition]

    def __len__(self):
        return len(self.transitions)


class DataPoint(NamedTuple):
    transition_history: List[Transition]

    @property
    def transition_now(self):
        # The train transition is stored as the next to last in the history.
        return self.transition_history[-2]

    @property
    def transition_next(self):
        # The next (t + 1) transition is stored as the last in the history.
        return self.transition_history[-1]

    @property
    def history_now(self):
        # All but the last, which is the next transition (t + 1).
        return self.transition_history[:-1]

    @property
    def history_next(self):
        # All but the first, which is too old for the history of the next transition.
        return self.transition_history[1:]


# class DataTensors(NamedTuple):
#     obs: torch.Tensor
#     obs_next: torch.Tensor
#     act: torch.Tensor
#     act_next_mask: torch.Tensor
#     rew: torch.Tensor
#     done: torch.Tensor
#     is_move: torch.Tensor
