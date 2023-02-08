from abc import ABCMeta, abstractmethod
from typing import *

from azulbot.azulsim import Azul, AzulState, Move
from qnet.data_structs import AzulObs


MaxRoundsTimeout = 20


class AzulAgent(metaclass=ABCMeta):
    @abstractmethod
    def choose_action(self, obs: AzulObs, valid_actions: List[Move]) -> Move:
        ...

    @abstractmethod
    def set_last_reward(self, reward: float, is_done: bool):
        ...

    @abstractmethod
    def handle_game_start(self):
        ...


def play_azul_game(players: List[AzulAgent], state: Optional[AzulState] = None, use_score_as_reward: bool = True):
    assert len(players) == 2
    assert use_score_as_reward

    azul = Azul()

    if state is None:
        state = azul.get_init_state()

    for _ in range(MaxRoundsTimeout):
        state = azul.deal_round(state)

        while not azul.is_round_end(state):
            obs = AzulObs(state, state.nextPlayer)
            valid_actions = azul.enumerate_moves(state)

            move, move_callback = players[state.nextPlayer].choose_action(obs, valid_actions)
            state = azul.apply_move_without_scoring(state, move).state

        old_scores = [p.score for p in state.players]
        state = azul.score_round(state)

        if azul.is_game_end(state):
            state = azul.score_game(state)

        if use_score_as_reward:
            rewards = [p.score - old for p, old in zip(state.players, old_scores)]
            for player, reward in zip(players, rewards):
                player.set_last_reward(reward, False)

        if azul.is_game_end(state):
            break

    print(f"Finished a game with scores {state.players[0].score} - {state.players[1].score}")
