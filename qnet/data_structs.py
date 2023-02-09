import copy
from dataclasses import dataclass
from typing import *

import torch

# import torch
# import numpy as np

# from bots.tictac import Square, Board
from azulbot.azulsim import Azul, Move, Color, AzulState, PlayerState


# Currently the observation is the same as the state. So we just reuse the type.
# However, we swap the players so that the 'current' player is always first.
class AzulObs(AzulState):

    def __init__(self, state: AzulState, player_index):
        super().__init__()

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

    @classmethod
    def empty(cls) -> 'AzulObs':
        return AzulObs(AzulState(), 0)


@dataclass
class Transition:
    obs: AzulObs
    action: Move
    valid_actions: List[Move]
    reward: float
    done: bool = False

    def get_valid_actions_int(self) -> List[int]:
        return [action.to_int() for action in self.valid_actions]

    @staticmethod
    def get_empty_transition():
        return Transition(AzulObs.empty(), Move(0, Color.Empty, Color.Blue), [], 0.0, False)

    def __repr__(self):
        return f"Transition(obs={self.obs}, action={self.action}, valid_actions=[... {len(self.valid_actions)} ...], " \
               f"reward={self.reward}, done={self.done})"


class Episode(NamedTuple):
    transitions: List[Transition]

    def __len__(self):
        return len(self.transitions)


class DataPoint(NamedTuple):
    transition_history: List[Transition]

    @property
    def transition_now(self) -> Transition:
        # The train transition is stored as the next to last in the history.
        return self.transition_history[-2]

    @property
    def transition_next(self) -> Transition:
        # The next (t + 1) transition is stored as the last in the history.
        return self.transition_history[-1]

    @property
    def history_now(self) -> List[Transition]:
        # All but the last, which is the next transition (t + 1).
        return self.transition_history[:-1]

    @property
    def history_next(self) -> List[Transition]:
        # All but the first, which is too old for the history of the next transition.
        return self.transition_history[1:]


class DataTensors(NamedTuple):
    obs: torch.Tensor
    obs_next: torch.Tensor
    act: torch.Tensor
    act_next_mask: torch.Tensor
    rew: torch.Tensor
    done: torch.Tensor
