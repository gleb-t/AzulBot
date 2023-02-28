import asyncio
import operator
import random
from abc import ABCMeta, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import *
from typing import List

import torch.nn

from azulbot.azulsim import Move, Azul
from qnet.data_structs import Transition, AzulObs
from qnet.model import AzulQNet

TPolicySampler = Callable[[torch.Tensor, List[int]], int]
TQNetCall = Callable[[torch.Tensor], Awaitable[torch.Tensor]]


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


class AzulAgent(metaclass=ABCMeta):
    @abstractmethod
    async def choose_action(self, obs: AzulObs, valid_actions: List[Move]) -> Move:
        ...

    def set_last_reward(self, reward: float, is_done: bool):
        pass

    def handle_game_start(self):
        pass

    def handle_game_end(self, obs: AzulObs):
        pass


class BatchedQNetAgentFactory:

    def __init__(self, q_net: AzulQNet, batch_size: int):
        self.q_net = q_net
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.q_net_queue = asyncio.queues.Queue()

        self.batch_size = batch_size

        self._worker_should_stop = False
        self._worker_task = None

    def build_agent(self, policy_sampler: TPolicySampler) -> 'BatchedQNetAgent':
        return BatchedQNetAgent(self.q_net_call, self.q_net, policy_sampler)

    async def q_net_call(self, input_: torch.Tensor) -> torch.Tensor:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        await self.q_net_queue.put((input_, future))
        result = await future

        return result

    async def start_worker(self):
        print("Starting the worker")
        self._worker_task = asyncio.create_task(self._batched_q_net_worker())

    async def stop_worker(self):
        print("Stopping the worker task.")
        self._worker_should_stop = True
        await self._worker_task
        self._worker_should_stop = False
        print("Worker task has finished.")

    async def _batched_q_net_worker(self):
        while not self._worker_should_stop:
            batch = []
            try:
                while len(batch) < self.batch_size:

                    # To overlap the q-net calls with CPU tasks, it is very important that we do no yield
                    # execution with an 'await' here. We only yield when waiting for q-net or when the queue is empty.
                    # Otherwise, the CPU tasks will be executed right after the previous batch (because we yield),
                    # and won't overlap with the next batch.
                    input_, future = self.q_net_queue.get_nowait()
                    # input_, future = await asyncio.wait_for(self.q_net_queue.get(), timeout=0.1)

                    batch.append((input_, future))
            except asyncio.QueueEmpty as e:
                await asyncio.sleep(0)  # Yield execution to other tasks.

            # If the queue is empty, check again.
            if len(batch) == 0:
                continue

            # print(f"Executing a batch of length {len(batch)}. Remaining queue length: {self.q_net_queue.qsize()}")
            batch_inputs, batch_futures = zip(*batch)

            batch_tensor = torch.concat(batch_inputs, dim=0)
            outputs = await asyncio.get_running_loop().run_in_executor(self.executor, self.q_net, batch_tensor)

            for out_, future in zip(outputs, batch_futures):
                future.set_result(out_)


class BatchedQNetAgent(AzulAgent):

    def __init__(self, async_q_net_call: TQNetCall, q_net: AzulQNet, policy_sampler: Optional[TPolicySampler] = None):
        self.azul = Azul()
        self.async_q_net = async_q_net_call  # type: TQNetCall
        self.q_net = q_net  # type: AzulQNet
        self.history = []  # type: List[Transition]
        self.policy_sampler = policy_sampler or greedy_policy_sampler

    async def choose_action(self, obs: AzulObs, valid_actions: List[Move]) -> Move:
        recent_obs_history = self._get_last_n_observations(self.q_net.history_len - 1)
        recent_obs_history.append(obs)

        # Convert the recent history to a tensor.
        net_input = self.q_net.obs_list_to_tensor(recent_obs_history)
        net_input = net_input.unsqueeze(0)  # Add the batch dimension.

        # Evaluate the network and choose an action.
        # q_action = self.async_q_net(net_input).squeeze()  # type: torch.Tensor
        q_action = await self.async_q_net(net_input)  # type: torch.Tensor
        action_index = self.policy_sampler(q_action.squeeze(), [m.to_int() for m in valid_actions])

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

    async def choose_action(self, obs: AzulObs, valid_actions: List[Move]) -> Move:
        return random.choice(valid_actions)


