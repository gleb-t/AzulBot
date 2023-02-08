import functools
import itertools
import operator
from typing import *

import numpy as np
import torch

from qnet.data_structs import AzulObs
from azulbot.azulsim import Azul, PlayerState, Move


class AzulQNet(torch.nn.Module):

    # Wall is a NxN square, plus N queues, each with two values, plus score and floor tile count.
    PlayerStateSize = Azul.WallSize ** 2 + Azul.WallSize * 2 + 2
    BinsSize = (Azul.ColorNumber + 1) * (Azul.BinNumber + 1)
    BagSize = Azul.ColorNumber + 1
    TableStateSize = BinsSize + BagSize + 5  # "The table" has five scalar features, e.g., next player, scores, etc.
    ObsSize = PlayerStateSize * 2 + TableStateSize

    def __init__(self, history_len, enc_size: int = 64, fc_sizes: Optional[List[int]] = None,
                 dtype: torch.dtype = torch.float32):
        super().__init__()

        self.dtype = dtype

        self.history_len = history_len
        self.enc_size = enc_size
        self.fc_sizes = fc_sizes or [64, 128, 256]
        # We scale the sizes with history length for better hyperparameter consistency.
        self.fc_sizes = [s * history_len for s in self.fc_sizes]

        # State encoders.
        self.player_enc = torch.nn.Sequential(
            torch.nn.Linear(self.PlayerStateSize, enc_size),
            torch.nn.ReLU(),
        )

        self.table_enc = torch.nn.Sequential(
            torch.nn.Linear(self.TableStateSize, enc_size),
            torch.nn.ReLU(),
        )

        # Main FC stack.
        self.fc_stack = torch.nn.Sequential()
        enc_number = (2 + 1) * history_len  # Two player states and one table state for each timestep.
        prev_size = enc_size * enc_number
        for fc_size in self.fc_sizes:
            self.fc_stack.append(torch.nn.Linear(prev_size, fc_size))
            self.fc_stack.append(torch.nn.ReLU())
            prev_size = fc_size

        self.fc_q = torch.nn.Linear(prev_size, Move.PossibleMoveNumber)

    def forward(self, obs_memory: torch.Tensor):

        assert len(obs_memory.shape) == 3  # Batch, history, features.
        assert  obs_memory.shape[1] == self.history_len
        assert obs_memory.shape[2] == self.ObsSize
        assert Azul.PlayerNumber == 2  # To keep the code simpler, we assume there are two players.

        table_state = obs_memory[..., :self.TableStateSize]
        player_states_cont = obs_memory[..., self.TableStateSize:]
        player_a_state = player_states_cont[..., :self.PlayerStateSize]
        player_b_state = player_states_cont[..., self.PlayerStateSize:]

        # We handle the history dimension by simple concatenation along the feature dimension.
        # Now the tensors become [batch, features * history].
        def _apply_at_each_step_and_concat(encoder: Callable[[torch.Tensor], torch.Tensor], state: torch.Tensor):
            return torch.concat([encoder(state[:, t, :]) for t in range(self.history_len)], dim=1)

        table_encoding    = _apply_at_each_step_and_concat(self.table_enc, table_state)
        player_a_encoding = _apply_at_each_step_and_concat(self.player_enc, player_a_state)
        player_b_encoding = _apply_at_each_step_and_concat(self.player_enc, player_b_state)

        # Now that the history dimension has been removed, concat along the last dim.
        encodings_concat = torch.concat([table_encoding, player_a_encoding, player_b_encoding], dim=1)

        fc_out = self.fc_stack(encodings_concat)
        move_q = self.fc_q(fc_out)

        return move_q

    # def convert_transitions_to_tensors(self, data_raw: List[DataPoint]):
    #     raise NotImplementedError()
    #
    #     data_n = len(data_raw)
    #
    #     # Use the same device and dtype as the network itself.
    #     dtype, device = self._detect_dtype_and_device()
    #
    #     data_obs = torch.empty((data_n, self.history_len, *self.ObsSize), dtype=dtype, device=device)
    #     data_obs_next = torch.empty((data_n, self.history_len, *self.ObsSize), dtype=dtype, device=device)
    #     data_act = torch.empty((data_n, 1), dtype=torch.int64, device=device)
    #     data_act_next_mask = torch.zeros((data_n, Board.Size ** 2), dtype=torch.int64, device=device)
    #     data_rew = torch.empty((data_n, 1), dtype=dtype, device=device)
    #     data_done = torch.empty((data_n, 1), dtype=dtype, device=device)
    #     data_is_move = torch.empty((data_n, 1), dtype=dtype, device=device)
    #
    #     for i_sample, point in enumerate(data_raw):
    #         data_obs[i_sample, ...] = self.obs_list_to_tensor([t.observation for t in point.history_now])
    #         data_obs_next[i_sample, ...] = self.obs_list_to_tensor([t.observation for t in point.history_next])
    #         data_act[i_sample] = point.transition_now.action
    #         data_act_next_mask[i_sample, point.transition_next.valid_actions] = 1
    #         data_rew[i_sample] = point.transition_now.reward
    #         data_done[i_sample] = point.transition_now.done
    #         data_is_move[i_sample] = int(point.transition_now.is_move)
    #
    #     return DataTensors(data_obs, data_obs_next, data_act, data_act_next_mask, data_rew, data_done, data_is_move)

    def obs_list_to_tensor(self, obs_list: List[AzulObs]) -> torch.Tensor:

        tensors = list(map(self.obs_to_tensor, obs_list))
        # Pad the obs length to the required memory length.
        if len(tensors) < self.history_len:
            tensors = tensors + [np.zeros_like(tensors[0])] * (self.history_len - len(tensors))

        dtype, device = self._detect_dtype_and_device()

        return torch.stack(tensors).to(dtype).to(device)

    def obs_to_tensor(self, obs: AzulObs) -> torch.Tensor:
        """
        Convert an observation into a 1D tensor by stacking all features together.
        :param obs:
        :return:
        """
        bins = torch.tensor(obs.bins).flatten()
        bag = torch.tensor(obs.bag)
        scalars = torch.tensor([obs.nextPlayer, obs.firstPlayer, obs.poolWasTouched, obs.roundIndex, obs.turnIndex],
                               dtype=self.dtype)

        table = torch.concat([bins, bag, scalars])
        assert table.shape[0] == self.TableStateSize

        players = []
        for obs_player in obs.players:
            wall_flat_int = list(map(int, itertools.chain(*obs_player.wall)))
            wall = torch.tensor(wall_flat_int)
            queue = torch.tensor(obs_player.queue).flatten()
            scalars = torch.tensor([obs_player.floorCount, obs_player.score])

            players.append(torch.concat([wall, queue, scalars]))

        assert players[0].shape[0] == self.PlayerStateSize

        return torch.concat([table] + players)

    def _detect_dtype_and_device(self):
        some_net_params = next(self.fc_stack.parameters())

        return some_net_params.dtype, some_net_params.device

    # @staticmethod
    # def action_to_one_hot(action):
    #     return torch.nn.functional.one_hot(torch.tensor(action), TicTacToe.BoardSize ** 2)
