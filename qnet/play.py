import asyncio
from abc import ABCMeta, abstractmethod
from typing import *
from typing import Tuple, List

from azulbot.azulsim import Azul, AzulState, Move
from qnet.agent import BatchedQNetAgentFactory, TPolicySampler
from qnet.data_structs import AzulObs, Episode

MaxRoundsTimeout = 20


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


async def play_azul_game(players: List[AzulAgent], state: Optional[AzulState] = None, use_score_as_reward: bool = True) -> int:
    assert len(players) == 2
    assert use_score_as_reward

    azul = Azul()

    if state is None:
        state = azul.get_init_state()

    for player in players:
        player.handle_game_start()

    for _ in range(MaxRoundsTimeout):
        state = azul.deal_round(state)

        # Keep playing until the round is over.
        while not azul.is_round_end(state):
            obs = AzulObs(state, state.nextPlayer)
            valid_actions = azul.enumerate_moves(state)

            move = await players[state.nextPlayer].choose_action(obs, valid_actions)
            state = azul.apply_move_without_scoring(state, move).state

        # Score the round and prepare to update the reward.
        old_scores = [p.score for p in state.players]
        state = azul.score_round(state)

        # Score the game if it's over this round and update the reward.
        is_game_end = azul.is_game_end(state)
        if is_game_end:
            state = azul.score_game(state)

        if use_score_as_reward:
            rewards = [p.score - old for p, old in zip(state.players, old_scores)]
            for player, reward in zip(players, rewards):
                player.set_last_reward(float(reward), is_game_end)

        if is_game_end:
            break

    for i, player in enumerate(players):
        player.handle_game_end(AzulObs(state, player_index=i))

    # print(f"Finished a game with scores {state.players[0].score} - {state.players[1].score}")
    winner_index = 1 if state.players[1].score > state.players[0].score else 0  # Favor player #1 in ties.

    return winner_index


async def play_n_games_async(n_games: int, agent_factory: BatchedQNetAgentFactory, opponent: AzulAgent,
                             policy_sampler: TPolicySampler) -> Tuple[List[int], List[Episode]]:
    """
    Play N games utilizing a batched Q-net agent that uses asyncio to batch calls to the Q-net.
    """

    # Start the worker coroutine which will execute q-net calls.
    await agent_factory.start_worker()

    # Schedule N games with N agents.
    game_tasks = []
    agents = []
    for i_game in range(n_games):
        agent = agent_factory.build_agent(policy_sampler)
        agents.append(agent)

        players = [agent, opponent]
        game_tasks.append(asyncio.create_task(play_azul_game(players)))

    # Wait for all games to finish.
    winner_indices = list(await asyncio.gather(*game_tasks))  # type: List[int]
    # Stop the worker coroutine.
    await agent_factory.stop_worker()

    # Collect the history.
    episodes = [Episode(agent.history) for agent in agents]

    return winner_indices, episodes
