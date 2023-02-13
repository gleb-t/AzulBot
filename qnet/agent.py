import operator
import random
from typing import *

import torch.nn

from azulbot.azulsim import Move, Azul, AzulState
from qnet.data_structs import Transition, AzulObs
from qnet.model import AzulQNet
from qnet.play import AzulAgent


def greedy_policy_sampler(q_vals: torch.Tensor, valid_actions: List[int]):
    q_vals_indexed = list(enumerate(q_vals))
    q_vals_valid = [q_vals_indexed[i] for i in valid_actions]

    # Return the original index corresponding to the largest q value.
    return max(q_vals_valid, key=operator.itemgetter(1))[0]


def e_greedy_policy_sampler_factory(eps: float):
    def e_greedy_policy(q_vals: torch.Tensor, valid_actions: List[int]):
        if random.random() < eps:
            return random.choice(valid_actions)

        q_vals_indexed = list(enumerate(q_vals))
        q_vals_valid = [q_vals_indexed[i] for i in valid_actions]

        # Return the original index corresponding to the largest q value.
        return max(q_vals_valid, key=operator.itemgetter(1))[0]

    return e_greedy_policy


class QNetAgent(AzulAgent):

    def __init__(self, q_net: AzulQNet, policy_sampler: Optional[Callable] = None):
        self.azul = Azul()
        self.q_net = q_net  # type: AzulQNet
        self.history = []  # type: List[Transition]
        self.policy_sampler = policy_sampler or greedy_policy_sampler

    def choose_action(self, obs: AzulObs, valid_actions: List[Move]) -> Move:
        recent_obs_history = self._get_last_n_observations(self.q_net.history_len - 1)
        recent_obs_history.append(obs)

        # Convert the recent history to a tensor.
        net_input = self.q_net.obs_list_to_tensor(recent_obs_history)
        net_input = net_input.unsqueeze(0)  # Add the batch dimension.

        # Evaluate the network and choose an action.
        q_action = self.q_net(net_input).squeeze()  # type: torch.Tensor
        action_index = self.policy_sampler(q_action, [m.to_int() for m in valid_actions])

        # Record the transition in the history.
        transition = Transition(obs, Move.from_int(action_index), valid_actions, reward=0.0, done=False)
        self.history.append(transition)

        return Move.from_int(action_index)

    def set_last_reward(self, reward: float, is_done: bool):
        self.history[-1].reward = reward
        self.history[-1].done = is_done

    def handle_game_start(self):
        self.history = []

    def handle_game_end(self, obs: AzulObs):
        self.history.append(Transition(obs, Move.empty(), [], reward=0.0, done=True))

    def _get_last_n_observations(self, n: int) -> List[AzulObs]:
        len_ = len(self.history)
        # Grab the last n observations.
        result = [self.history[i].obs for i in range(max(0, len_ - n), len_)]
        # Now pad the result with empty observations if necessary.
        result = [AzulObs.empty()] * (n - len(result)) + result

        return result


class RandomAgent(AzulAgent):

    def choose_action(self, obs: AzulObs, valid_actions: List[Move]) -> Move:
        return random.choice(valid_actions)


