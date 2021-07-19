#pragma once

#include <memory>

#include "Azul.h"
#include "AzulState.h"



class MctsBot
{
public:
    MctsBot(Azul& azul, const AzulState& state, int samplingWidth = 10, double_t explorationWeight = 1 / 1.4142);

    void step();
    Move step_n(uint32_t nSteps);
    Move get_best_move();

protected:
    class Node
    {
    public:
        AzulState state;
        Move move;
        Node* parent;
        std::vector<std::unique_ptr<Node>> children{};
        bool isRandom{};
        uint32_t scores{};
        uint32_t plays{};


        Node(AzulState state, Move move, Node* parent)
            :state{state}, move{move}, parent{parent}
        {
        }

    };

    Azul& _game;
    Node _root;
    uint32_t _playerIndex;
    uint32_t _samplingWidth;
    double_t _explorationWeight;

    std::mt19937 _randomEngine{std::random_device{}()};

    Node* _select_max_uct(std::vector<std::unique_ptr<Node>>& nodes, int parentPlays);
};
