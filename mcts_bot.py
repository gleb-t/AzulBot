import copy
import math
import random
from typing import *

from azulbot import Game, GameState, TMove


class Node:

    def __init__(self, state: Optional[GameState], move: Optional[TMove], parent: Optional['Node'],
                 isRandom: bool = False):
        self.state = state
        self.move = move
        self.parent = parent
        self.children = []  # type: List[Node]
        self.wins = 0
        self.plays = 0

        self.isRandom = isRandom


class MctsBot:

    ExplorationWeight = 1 / 1.4142

    def __init__(self, game: Game[GameState, TMove], state: GameState, playerIndex: int,
                 samplingWidth: int = 10):

        self.game = game
        self.root = Node(state.copy(), move=None, parent=None)
        self.playerIndex = playerIndex
        self.samplingWidth = samplingWidth

    def step(self):

        # Select a leaf node according to UCT.
        node = self.root
        while len(node.children) > 0:
            if node.plays == 0 and not node.isRandom:  # Can happen on the first run.
                break

            if node.isRandom:
                # When going through a random node, generate new outcomes until the sampling width is reached.
                if len(node.children) < self.samplingWidth:
                    newRandomOutcome = self.game.apply_move(node.parent.state, node.move)
                    assert newRandomOutcome.isRandom
                    newChild = Node(newRandomOutcome.state, None, node, isRandom=False)
                    node.children.append(newChild)
                    node = newChild
                else:
                    node = random.choice(node.children)
            else:
                node = self._select_max_uct(node.children, node.plays)

        # If the node represents a terminal state, we don't need to expand it.
        if not self.game.is_game_end(node.state):  # todo can't we cache this as a flag?
            # Otherwise, expand the node, appending all possible states, and playout a random new child.
            assert len(node.children) == 0
            for move in self.game.enumerate_moves(node.state):
                outcome = self.game.apply_move(node.state, move)
                if not outcome.isRandom:
                    node.children.append(Node(outcome.state, move, node))
                else:
                    # Create a special random node, whose children are the possible outcomes of the same move.
                    randomNode = Node(None, move, node, isRandom=True)
                    node.children.append(randomNode)
                    randomNode.children.append(Node(outcome.state, None, randomNode, isRandom=False))

            node = random.choice(node.children)
            if node.isRandom:
                node = random.choice(node.children)

        if not self.game.is_game_end(node.state):
            # Do a playout.
            terminalState = self.game.playout(node.state)

        else:
            # We're already in the terminal state, just reuse the result.
            terminalState = node.state

        isWinInt = self.game.get_score(terminalState, self.playerIndex)

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
        bestIndices, bestVal = [], -1
        for i, node in enumerate(nodes):
            if node.plays == 0:
                return node

            uct = node.wins / node.plays + MctsBot.ExplorationWeight * math.sqrt(math.log(parentPlays) / node.plays)

            if uct > bestVal:
                bestVal = uct
                bestIndices = [i]
            elif uct == bestVal:
                bestIndices.append(i)

        return nodes[random.choice(bestIndices)]
