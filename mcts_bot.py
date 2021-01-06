import math
import random
from typing import *

from azulbot.azul import Azul, Move, play_until_end


class Node:

    def __init__(self, state: Azul, move: Optional[Move], parent: Optional['Node']):
        self.state = state
        self.move = move
        self.parent = parent
        self.children = []  # type: List[Node]
        self.wins = 0
        self.plays = 0

        self.isRandom = False


class MctsBot:

    ExplorationWeight = 1.4142

    def __init__(self, state: Azul):

        self.root = Node(state, move=None, parent=None)

    def step(self):

        # Select a leaf node according to UCT.
        node = self.root
        while len(node.children) > 0:
            if node.plays == 0:  # Can happen on the first run.
                break

            node = self._select_max_uct(node.children, node.plays)

        # If the node is followed by a stochastic state update, mark it as random and just do a playout.
        if node.isRandom or node.state.is_end_of_round():
            node.isRandom = True
        else:
            # Otherwise, expand the node, appending all possible states, and playout a random new child.
            node.children = list(map(lambda m: Node(node.state.apply_move(m), m, node), node.state.enumerate_moves()))
            node = random.choice(node.children)

        # Do a playout.
        terminalState = play_until_end(node.state)

        assert len(terminalState.players) == 2
        iPlayer = self.root.state.nextPlayer
        isWinInt = int(terminalState.players[iPlayer].score > terminalState.players[(iPlayer + 1) % 2].score)

        # Update the parents.
        while node is not None:
            node.plays += 1
            node.wins += isWinInt
            node = node.parent

    def get_best_move(self):
        if len(self.root.children) == 0:
            raise RuntimeError("Can't get the best move from an empty tree. Did you iterate? Are there legal moves?")

        node = max(self.root.children, key=lambda n: n.wins / (n.plays + 0.001))

        return node.move

    @staticmethod
    def _select_max_uct(nodes: Sequence[Node], parentPlays: int):
        bestIndex, bestVal = 0, -1
        for i, node in enumerate(nodes):
            if node.plays == 0:
                return node

            uct = node.wins / node.plays + MctsBot.ExplorationWeight * math.sqrt(math.log(parentPlays) / node.plays)

            if uct > bestVal:
                bestVal = uct
                bestIndex = i

        return nodes[bestIndex]
