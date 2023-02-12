

import asyncio
import random
import time
from concurrent.futures import ProcessPoolExecutor
from typing import *


class BatchedAgentFactory:

    def __init__(self, q_net: Callable[[List[int]], List[int]]):
        self.q_net = q_net
        self.executor = ProcessPoolExecutor(max_workers=1)
        self.q_net_queue = asyncio.queues.Queue()

        self.batch_size = 8

        self._worker_should_stop = False
        self._worker_task = None

    def build_agent(self) -> 'BatchedAgent':
        return BatchedAgent(self.q_net_forward)

    async def q_net_forward(self, input_: int) -> int:
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
        # time_last = time.time()
        while not self._worker_should_stop:
            batch = []
            try:
                while len(batch) < self.batch_size:
                    # print("While loop")
                    print("Reading the queue")
                    # To overlap the q-net calls with CPU tasks, it is very important that we do no yield
                    # execution with an 'await' here. We only yield when waiting for q-net.
                    # Otherwise, the CPU tasks will be executed right after the previous batch (because we yield),
                    # and won't overlap with te next batch.
                    input_, future = self.q_net_queue.get_nowait()
                    # input_, future = await asyncio.wait_for(self.q_net_queue.get(), timeout=0.1)
                    print("Finished reading the queue")
                    # queue.task_done()  # Not needed. We don't use queue.join()
                    batch.append((input_, future))
            except asyncio.TimeoutError as e:
                # print("TimeoutError")
                pass  # Timed out waiting for a batch to be full. Run an incomplete batch.
            except asyncio.QueueEmpty as e:
                print("QueueEmpty, pausing")
                await asyncio.sleep(0.1)

            if len(batch) == 0:
                print("Batch is empty, return to waiting")
                continue

            print(f"Executing a batch of length {len(batch)}. Remaining queue length: {self.q_net_queue.qsize()}")
            batch_inputs, batch_futures = zip(*batch)

            # outputs = self.q_net(batch_inputs)
            outputs = await asyncio.get_running_loop().run_in_executor(self.executor, self.q_net, batch_inputs)

            for out_, future in zip(outputs, batch_futures):
                print("Setting future result")
                future.set_result(out_)


class BatchedAgent():

    def __init__(self, async_q_net_forward: Callable[[int], Awaitable[int]]):
        self.async_q_net_forward = async_q_net_forward

    async def choose_move(self, state: int):
        move = await self.async_q_net_forward(state)
        return move


async def play_game(agent: BatchedAgent, i_game: int = None):
    state = 1
    for i_round in range(4):
        print(f"Game {i_game} starts round {i_round}")
        move = await agent.choose_move(state)
        state = state + move
        time.sleep(0.1)

    return state


async def play_n_games(n: int):
    agent_factory = BatchedAgentFactory(q_net)
    await agent_factory.start_worker()

    game_tasks = []
    for i_game in range(n):
        agent = agent_factory.build_agent()
        game_tasks.append(asyncio.create_task(play_game(agent, i_game)))

    game_results = await asyncio.gather(*game_tasks)

    print(f"Game results: {game_results}")

    await agent_factory.stop_worker()


def q_net(inputs: List[int]) -> List[int]:
    results = [i * 2 for i in inputs]
    time.sleep(0.5)

    return results


def main():
    before = time.time()
    asyncio.run(play_n_games(50))
    total = time.time() - before

    print(f"Total time: {total}")


if __name__ == '__main__':
    main()

