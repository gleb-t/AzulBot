









## Training loop

```
Init a replay buffer


For epoch
    Optionally, subsample the replay buffer.

    For games
        Play a game vs. random bot
        Save the episode to the buffer
   
    For steps
        Sample N transitions
        Do a train step
```