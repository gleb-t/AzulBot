import asyncio
import math
import random
from typing import *

import numpy as np
import torch
import torch.nn.functional
import torchsummary
from tqdm import tqdm

from lib.StageTimer import StageTimer
from qnet.agent import e_greedy_policy_sampler_factory, greedy_policy_sampler, RandomAgent, \
    BatchedQNetAgentFactory
from qnet.data_structs import Episode, DataPoint, Transition
from qnet.loss import q_loss
from qnet.model import AzulQNet
from qnet.play import play_n_games_async


class Config:
    
    def __init__(self):
        self.seed = 42

        self.steps_per_epoch = 32
        self.epoch_number = 2000
        self.games_per_epoch = 128

        self.agent_batch_size = 64

        self.net_history_len = 3
        self.net_enc_size = 256

        self.train_batch_size = 128
        self.train_lr = 1e-3
        self.train_weight_sense = 1.0
        self.train_eps_max = 0.8
        self.train_eps_min = 0.1

        self.eval_freq_epochs = 10
        self.eval_games = 1024

        # self.train_data_mode = 'replay-buffer'
        self.train_data_mode = 'fresh-data'

        # self.train_data_mode = 'fixed-data'
        self.fixed_data_epoch_number = 2

        self.wandb_description = 'first'


def main():

    config = Config()

    # === DEBUG ===
    # config.games_per_epoch = 5
    # config.eval_games = 10
    # config.steps_per_epoch = 32
    # config.epoch_number = 11

    # config.wandb_description = 'fresh-data_true-state_online_eps-sched'
    #
    # wandb.init(project="recon_tictactoe", entity="not-working-solutions", )
    # wandb.run.name = wandb.run.name + '-' + wandb_description if wandb.run.name else wandb_description  # Can be 'None'.

    # plotting_dir = os.path.abspath(os.path.join(wandb.run.dir, "games"))

    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    dtype = torch.float32

    random.seed(config.seed)
    torch.manual_seed(config.seed)
    np.random.seed(config.seed)

    timer = StageTimer()
    timer.start_stage('init')

    print(f"Training on device {device}")

    q_net = AzulQNet(config.net_history_len, config.net_enc_size).to(device)
    optimizer = torch.optim.Adam(q_net.parameters(), lr=config.train_lr)

    q_agent_factory = BatchedQNetAgentFactory(q_net, batch_size=config.agent_batch_size)
    train_policy_sampler = e_greedy_policy_sampler_factory(config.train_eps_max)
    eval_policy_sampler = greedy_policy_sampler

    print("Built the Q-Net.")
    torchsummary.summary(q_net, (config.net_history_len, AzulQNet.ObsSize))

    replay_buffer = []  # type: List[Episode]
    for i_epoch in range(config.epoch_number):
        timer.start_pass()

        # ---------------- Collect play data. ----------------
        timer.start_stage('play')
        print(f"Epoch {i_epoch}: Playing {config.games_per_epoch} games...")
        winners, episodes = asyncio.run(play_n_games_async(config.games_per_epoch, q_agent_factory, RandomAgent(),
                                                           train_policy_sampler))

        if config.train_data_mode == 'replay-buffer':
            replay_buffer.extend(episodes)
        elif config.train_data_mode == 'fresh-data':
            replay_buffer = episodes
        elif config.train_data_mode == 'fixed-data':
            if i_epoch < config.fixed_data_epoch_number:
                replay_buffer.extend(episodes)
        else:
            raise ValueError()

        # ---------------- Train the model. ----------------
        timer.start_stage('train')
        # Enumerate the steps by their global index for convenience.
        step_index = i_epoch * config.steps_per_epoch
        loss_epoch = 0.0
        for i_step in tqdm(range(step_index, step_index + config.steps_per_epoch), desc=f"Epoch {i_epoch}: Training"):

            # --- Sample the train transitions with history.
            data_raw = []
            for i_sample in range(config.train_batch_size):
                # Sample an episode, weighted by episode length so all transitions are equally likely.
                episode = random.choices(replay_buffer, weights=[len(e) for e in replay_buffer], k=1)[0]

                # Sample a transition and extract its history. Exclude the last transition because it's empty.
                t_now = random.randint(0, len(episode) - 2)
                transition_history = []
                for t in range(t_now - config.net_history_len + 1, t_now + 2):  # From n steps ago up to next.
                    if t >= 0:
                        transition_history.append(episode.transitions[t])
                    else:  # Pad the history with empty transitions.
                        transition_history.append(Transition.get_empty_transition())

                data_raw.append(DataPoint(transition_history))

            # --- Convert into training tensors.
            data = q_net.convert_transitions_to_tensors(data_raw)

            # --- Update the model.
            optimizer.zero_grad()

            q_now = q_net(data.obs)
            q_next = q_net(data.obs_next)

            # Mask the invalid actions.
            q_next[data.act_next_mask == 0] = torch.finfo(dtype).min

            # Compute the loss.
            loss_total = torch.sum(q_loss(q_now,  q_next, data.act, data.rew, data.done))

            loss_total.backward()
            optimizer.step()

            loss_epoch += loss_total.item()

            # wandb.log(step=i_step, data={
            #     "loss_total_step": loss_total.item(),
            #     "loss_move_step": loss_move.item(),
            #     "loss_sense_step": loss_sense.item(),
            # })

            # print(f"Step: {i_step} | Loss: {loss_total.item():.2f}")

        loss_epoch /= config.steps_per_epoch

        # step_index = ((i_epoch + 1) * steps_per_epoch - 1)  # Compute the last step index.
        # wandb.log(step=step_index, data={"loss_total_epoch": loss_epoch})

        # --- Update the eps-policy on a schedule.
        t = i_epoch / config.epoch_number
        eps = config.train_eps_max * math.cos(t * math.pi / 2) + config.train_eps_min
        train_policy_sampler = e_greedy_policy_sampler_factory(eps)
        # wandb.log(step=step_index, data={"eps": eps})

        # --- Winrate evaluation.
        if i_epoch % config.eval_freq_epochs == 0 and i_epoch > 0:
            timer.start_stage('eval')
            print(f"Epoch {i_epoch}: Evaluating...")
            winners, episodes = asyncio.run(play_n_games_async(config.eval_games, q_agent_factory, RandomAgent(),
                                                               eval_policy_sampler))
            win_count = sum([1 if w == 0 else 0 for w in winners])
            #
            # for i_game in tqdm(range(eval_games), desc=f"Epoch {i_epoch}: Evaluating"):
            #     winner_index = play_azul_game([q_agent_eval, agents[1]])
            #     if winner_index == 0:
            #         win_count += 1

            winrate = win_count / config.eval_games
            print(f"Eval winrate: {winrate}")
            # wandb.log(step=step_index, data={"winrate": winrate})

            # # Enter the plotting context
            # with plotting_mode():
            #     # Set plotting directories for player and opponent (they'll be created if non-existant)
            #     q_agent_eval.plot_directory = os.path.join(plotting_dir, f"player_{i_epoch}")
            #     agents[1].plot_directory = os.path.join(plotting_dir, f"opponent_{i_epoch}")
            #
            #     play_local_game(q_agent_eval, agents[1], TicTacToe())
            #
            # # --- Sync game renders to WANDB.
            # if i_epoch % 100 == 0:
            #     wandb.save("games/*")
        timer.end_pass()

        print(f"Epoch {i_epoch}  Loss: {loss_epoch}")
        print(timer.get_pass_report())

    timer.end()
    print(timer.get_total_report())


if __name__ == '__main__':
    main()
