from typing import *

import torch.nn

from azulbot.azulsim import Move, AzulState
from qnet.data_structs import Transition, AzulObs
from qnet.model import AzulQNet
from qnet.play import AzulPlayer


def greedy_policy(q_vals: torch.Tensor, valid_actions: List[int]):
    q_vals_indexed = list(enumerate(q_vals))
    q_vals_valid = [q_vals_indexed[i] for i in valid_actions]

    # Return the original index corresponding to the largest q value.
    return max(q_vals_valid, key=operator.itemgetter(1))[0]


def e_greedy_policy_factory(eps: float):
    def e_greedy_policy(q_vals: torch.Tensor, valid_actions: List[int]):
        if random.random() < eps:
            return random.choice(valid_actions)

        q_vals_indexed = list(enumerate(q_vals))
        q_vals_valid = [q_vals_indexed[i] for i in valid_actions]

        # Return the original index corresponding to the largest q value.
        return max(q_vals_valid, key=operator.itemgetter(1))[0]

    return e_greedy_policy


class AzulQNetAgent(AzulPlayer):

    def __init__(self, q_net: AzulQNet, policy: Optional[Callable] = None):
        self.azul = Azul()
        self.q_net = q_net  # type: AzulQNet
        self.history = []  # type: List[Transition]
        self.policy = policy or greedy_policy

    def choose_action(self, obs: AzulObs, valid_actions: List[Move]) -> Move:
        recent_obs_history = [transition.obs for transition in self.history[-(self.q_net.history_len - 1):]]
        recent_obs_history.append(obs)

        # Convert the recent history to a tensor.
        net_input = self.q_net.obs_list_to_tensor(recent_obs_history)
        net_input = net_input.unqueeze(0)  # Add the batch dimension.

        # Evaluate the network and choose an action.
        q_action = self.q_net(net_input)  # type: torch.Tensor
        action_index = self.policy(q_action, [m.to_int() for m in valid_actions])

        # Record the transition in the history.
        transition = Transition(obs, Move.from_int(action_index), valid_actions, reward=0.0, done=False)
        self.history.append(transition)

        return Move.from_int(action_index)

    def set_last_reward(self, reward: float, is_done: bool):
        self.history[-1].reward = reward
        self.history[-1].is_done = is_done

    def handle_game_start(self):
        self.history = []
