#pragma once

#include <memory>

#include "Azul.h"
#include "AzulState.h"



class MctsBot
{
public:
    constexpr static double ExplorationWeight = 1 / 1.4142;

    MctsBot(Azul& azul, const AzulState& state, int playerIndex, int samplingWidth = 10);

    void step();
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
        int wins{};
        int plays{};


        Node(AzulState state, Move move, Node* parent)
            :state{state}, move{move}, parent{parent}
        {
        }

    };

    Azul& _game;
    Node _root;
    uint32_t _playerIndex;
    uint32_t _samplingWidth;

    std::mt19937 _randomEngine{std::random_device{}()};

    static Node* _select_max_uct(std::vector<std::unique_ptr<Node>>& nodes, int parentPlays);
};
