#include "MctsBot.h"
#include <cassert>
#include <iterator>
#include <stdexcept>

MctsBot::MctsBot(Azul& azul, const AzulState& state, int playerIndex, int samplingWidth)
    :_game(azul), _root(state, Move(), nullptr), _playerIndex(playerIndex), _samplingWidth(samplingWidth)
{
}

void MctsBot::step()
{
    //# Select a leaf node according to UCT.
    //node = self.root
    //while len(node.children) > 0:
    //	if node.plays == 0 and not node.isRandom:  # Can happen on the first run.
    //		break
    //	if node.isRandom:
    //		# When going through a random node, generate new outcomes until the sampling width is reached.
    //		if len(node.children) < self.samplingWidth:
    //			newRandomOutcome = self._game.apply_move(node.parent.state, node.move)
    //			assert newRandomOutcome.isRandom
    //			newChild = Node(newRandomOutcome.state, None, node, isRandom=False)
    //			node.children.append(newChild)
    //			node = newChild
    //		else:
    //			node = random.choice(node.children)
    //	else:
    //		node = self._select_max_uct(node.children, node.plays)
    //

    // Select a leaf node according to UCT.
    Node* node = &_root;
    while (!node->children.empty())
    {
        if (node->plays == 0 && !node->isRandom)
            break;

        if (node->isRandom)
        {
            // When going through a random node, generate new outcomes until the sampling width is reached.
            if (node->children.size() < _samplingWidth)
            {
                MoveOutcome newRandomOutcome = _game.apply_move(node->parent->state, node->move);
                assert(newRandomOutcome.isRandom);
                node->children.emplace_back(newRandomOutcome.state, Move(), node);
                node = &node->children[node->children.size() - 1];
            }
            else
            {
                // If the sampling width is reached, just pick one of the sampled outcomes.
                std::uniform_int_distribution<> uniform(0, static_cast<int>(node->children.size()) - 1);
                node = &node->children[uniform(_randomEngine)];
            }
        }
        else
        {
            node = _select_max_uct(node->children, node->plays);
        }
    }



    //# If the node represents a terminal state, we don't need to expand it.
    //if not self._game.is_game_end(node.state):  # todo can't we cache this as a flag?
    //	# Otherwise, expand the node, appending all possible states, and playout a random new child.
    //	assert len(node.children) == 0
    //	for move in self._game.enumerate_moves(node.state):
    //		outcome = self._game.apply_move(node.state, move)
    //		if not outcome.isRandom:
    //			node.children.append(Node(outcome.state, move, node))
    //		else:
    //			# Create a special random node, whose children are the possible outcomes of the same move.
    //			randomNode = Node(None, move, node, isRandom=True)
    //			node.children.append(randomNode)
    //			randomNode.children.append(Node(outcome.state, None, randomNode, isRandom=False))
    //
    //	node = random.choice(node.children)
    //	if node.isRandom:
    //		node = random.choice(node.children)
    //
    

    // If the node represents a terminal state, we don't need to expand it.
    if (!_game.is_game_end(node->state))  // todo no need to recompute, store move outcome.
    {
        // Otherwise, expand the node, appending all possible states, and playout a random new child.
        assert(node->children.empty());
        for (Move& move : _game.enumerate_moves(node->state))
        {
            MoveOutcome outcome = _game.apply_move(node->state, move);
            if (!outcome.isRandom)
            {
                node->children.emplace_back(outcome.state, move, node);
            }
            else
            {
                // Create a special random node, whose children are the possible outcomes of the same move. Fill one of those outcome.
                Node randomNode{AzulState{}, move, node};
                randomNode.isRandom = true;
                randomNode.children.emplace_back(outcome.state, Move{}, randomNode);
                node->children.push_back(std::move(randomNode));
            }
        }

    }
    std::uniform_int_distribution<> uniform(0, static_cast<int>(node->children.size()) - 1);
    node = &node->children[uniform(_randomEngine)];
    if (node->isRandom)
    {
        uniform = std::uniform_int_distribution<>(0, static_cast<int>(node->children.size()) - 1);
        node = &node->children[uniform(_randomEngine)];
    }

    //if not self._game.is_game_end(node.state):
    //	# Do a playout.
    //	terminalState = self._game.playout(node.state)
    //
    //else:
    //	# We're already in the terminal state, just reuse the result.
    //	terminalState = node.state
    //
    //isWinInt = self._game.get_score(terminalState, self.playerIndex)
    //
    //# Update the parents.
    //while node is not None:
    //	node.plays += 1
    //	node.wins += isWinInt
    //	node = node.parent

    AzulState terminalState{};
    if (!_game.is_game_end(node->state))
    {
        // Do a playout.
        terminalState = _game.playout(node->state);
    }
    else
    {
        // We're already in the terminal state, just reuse the result.
        terminalState = node->state;
    }

    const int isWinInt = _game.get_score(terminalState, _playerIndex);

    // Update the parents;
    while (node != nullptr)
    {
        node->plays += 1;
        node->wins += isWinInt;
        node = node->parent;
    }
    
}

Move MctsBot::get_best_move()
{
    //	if len(self.root.children) == 0:
    //		raise RuntimeError("Can't get the best move from an empty tree. Did you iterate? Are there legal moves?")
    //
    //	node = max(self.root.children, key=lambda n: n.wins / (n.plays + 0.001))
    //
    //	return node.move
    if (_root.children.empty())
        throw std::runtime_error("Can't get the best move from an empty tree. Did you iterate? Are there legal moves?");

    std::vector<double> winPercentages{};
    std::transform(_root.children.begin(), _root.children.end(), std::back_inserter(winPercentages),
                   [](Node* n) { return static_cast<double>(n->wins) / (n->plays + 0.001); });
    const auto maxIt = std::max_element(winPercentages.begin(), winPercentages.end());

    return _root.children[maxIt - winPercentages.begin()].move;
}

MctsBot::Node* MctsBot::_select_max_uct(std::vector<Node>& nodes, int parentPlays)
{
    //def _select_max_uct(nodes: Sequence[Node], parentPlays: int):
    //	bestIndices, bestVal = [], -1
    //	for i, node in enumerate(nodes):
    //		if node.plays == 0:
    //			return node
    //
    //		uct = node.wins / node.plays + MctsBot.ExplorationWeight * math.sqrt(math.log(parentPlays) / node.plays)
    //
    //		if uct > bestVal:
    //			bestVal = uct
    //			bestIndices = [i]
    //		elif uct == bestVal:
    //			bestIndices.append(i)
    //
    //	return nodes[random.choice(bestIndices)]

    // todo This code is biased, not choosing randomly for equal values (see the Python version).
    Node* bestNode = nullptr;
    double bestValue = -1;
    for (auto& i : nodes)
    {
        auto* node = &i;
        if (i.plays == 0)
            return node;

        double uct = static_cast<double>(node->wins) / node->plays + ExplorationWeight * sqrt(log(parentPlays) / node->plays);

        if (uct > bestValue)
        {
            bestValue = uct;
            bestNode = node;
        }
    }

    return bestNode;
}
