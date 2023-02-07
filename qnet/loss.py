import torch


def q_loss(
    q_values,
    q_values_next,
    act,
    rew,
    done,
    q_values_next_estimate: torch.Tensor = None,
    discount: float = 1.0,
) -> torch.Tensor:

    # Select Q values for chosen actions
    q_values_selected = q_values.gather(-1, act)

    # Select optimal values for the next time step
    q_opt_next, _ = torch.max(q_values_next, dim=-1, keepdim=True)
    if q_values_next_estimate is not None:
        # Double Q idea: select the optimum action for the observation at t+1
        # using the trainable model, but compute it's Q value with target one
        q_opt_next = q_values_next.gather(
            -1, torch.argmax(q_values_next_estimate, dim=-1, keepdim=True)
        )

    # Target estimate for Cumulative Discounted Reward
    q_values_target = rew + discount * q_opt_next * (1. - done)

    # Compute TD error
    loss = torch.nn.functional.smooth_l1_loss(q_values_selected, q_values_target)

    return loss
