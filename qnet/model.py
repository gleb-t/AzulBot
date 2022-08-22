import functools
import operator

import numpy as np
import torch
import typing as t

from qnet.data_structs import AzulObs
from azulbot.azulsim import Azul, PlayerState, Move


class AzulQNet(torch.nn.Module):


    # Wall is a NxN square, plus N queues, each with two values, plus score and floor tile count.
    PlayerStateSize = Azul.WallSize ** 2 + Azul.WallSize * 2 + 2
    BinsSize = (Azul.ColorNumber + 1) * (Azul.BinNumber + 1)
    TableStateSize = BinsSize + 5
    ObsSize = PlayerStateSize * 2 + TableStateSize

    def __init__(self, history_len, enc_size: int = 64, fc_sizes: t.Optional[t.List[int]] = None):
        super().__init__()

        self.history_len = history_len
        self.enc_size = enc_size
        self.fc_sizes = fc_sizes or [64, 128, 256]

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
        prev_size = enc_size * 3
        for fc_size in fc_sizes:
            self.fc_stack.append(torch.nn.Linear(prev_size, fc_size))
            self.fc_stack.append(torch.nn.ReLU())
            prev_size = fc_size

        self.fc_q = torch.nn.Linear(prev_size, Move.PossibleMoveNumber)

    def forward(self, obs_memory: torch.Tensor):

        assert len(obs_memory.shape) == 3  # Batch, history, features.
        assert obs_memory.shape[-1] == self.ObsSize

        table_state = obs_memory[..., :self.TableStateSize]
        player_states_cont = obs_memory[..., self.TableStateSize:]
        player_states = [player_states_cont[..., i * self.PlayerStateSize : (i + 1) * self.PlayerStateSize]
                         for i in range(Azul.PlayerNumber)]

        table_encoding = self.table_enc(table_state)
        player_encodings = [self.player_enc(s) for s in player_states]

        encodings_concat = torch.concat([table_encoding] + player_encodings, dim=2)

        ^^ WONT WORK AS IS, CAUSE WE LAOS HAVE THE HISTORY DIM.

        board_encoding = self.backbone(board_memory)

        # Compute heads
        sense_q = self.fc_sense_q(board_encoding)
        move_q = self.fc_move_q(board_encoding)

        return sense_q, move_q

    def backbone(self, board_memory: torch.Tensor):
        # Re-align board memory to fit the shape described in init
        # (B, T, H, W, C) -> (B, C, T, H, W)
        assert board_memory.ndim == 5
        board_encoding = board_memory.permute(0, 4, 1, 2, 3)

        board_encoding = self.conv_stack(board_encoding)

        board_encoding = torch.flatten(board_encoding, start_dim=1)
        board_encoding = self.fc_stack(board_encoding)

        return board_encoding

    def convert_transitions_to_tensors(self, data_raw: t.List[DataPoint]):
        data_n = len(data_raw)

        # Use the same device and dtype as the network itself.
        dtype, device = self._detect_dtype_and_device()

        data_obs = torch.empty((data_n, self.history_len, *self.ObsSize), dtype=dtype, device=device)
        data_obs_next = torch.empty((data_n, self.history_len, *self.ObsSize), dtype=dtype, device=device)
        data_act = torch.empty((data_n, 1), dtype=torch.int64, device=device)
        data_act_next_mask = torch.zeros((data_n, Board.Size ** 2), dtype=torch.int64, device=device)
        data_rew = torch.empty((data_n, 1), dtype=dtype, device=device)
        data_done = torch.empty((data_n, 1), dtype=dtype, device=device)
        data_is_move = torch.empty((data_n, 1), dtype=dtype, device=device)

        for i_sample, point in enumerate(data_raw):
            data_obs[i_sample, ...] = self.obs_list_to_tensor([t.observation for t in point.history_now])
            data_obs_next[i_sample, ...] = self.obs_list_to_tensor([t.observation for t in point.history_next])
            data_act[i_sample] = point.transition_now.action
            data_act_next_mask[i_sample, point.transition_next.valid_actions] = 1
            data_rew[i_sample] = point.transition_now.reward
            data_done[i_sample] = point.transition_now.done
            data_is_move[i_sample] = int(point.transition_now.is_move)

        return DataTensors(data_obs, data_obs_next, data_act, data_act_next_mask, data_rew, data_done, data_is_move)

    def obs_list_to_tensor(self, obs_list: t.List[np.ndarray]):
        # Pad the obs length to the required memory length.
        if len(obs_list) < self.history_len:
            obs_list = obs_list + [np.zeros_like(obs_list[0])] * (self.history_len - len(obs_list))

        dtype, device = self._detect_dtype_and_device()

        # Convert to a tensor and add a trivial channel dimension.
        return torch.tensor(np.stack(obs_list), dtype=dtype, device=device).unsqueeze(-1)

    def _detect_dtype_and_device(self):
        some_net_params = next(self.fc_stack.parameters())

        return some_net_params.dtype, some_net_params.device

    # @staticmethod
    # def action_to_one_hot(action):
    #     return torch.nn.functional.one_hot(torch.tensor(action), TicTacToe.BoardSize ** 2)
