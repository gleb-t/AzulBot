#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <vector>

#include "Azul.h"


enum class Color : uint8_t
{
    Empty = 0,
    Blue = 1,
    Yellow = 2,
    Red = 3,
    Black = 4,
    White = 5
};


struct PlayerState
{
    std::array<std::array<Color, Azul::WallSize>, Azul::WallSize> wall = {};
    std::array<std::array<uint8_t, 2>, Azul::WallSize> queue = {};
    uint8_t floorCount = 0;
    uint32_t score = 0;

    void set_wall(uint8_t rowIndex, uint8_t colIndex, Color color)
    {
        wall[rowIndex][colIndex] = color;
    }
    void set_wall_row(uint8_t rowIndex, std::array<Color, Azul::WallSize> colors)
    {
        wall[rowIndex] = colors;
    }
    void set_wall_col(uint8_t colIndex, std::array<Color, Azul::WallSize> colors)
    {
        for (size_t i = 0; i < wall.size(); i++)
            wall[i][colIndex] = colors[i];
    }
	
    void set_queue(uint8_t queueIndex, Color color, uint8_t count)
    {
        queue[queueIndex][0] = static_cast<uint8_t>(color);
        queue[queueIndex][1] = count;
    }
};


struct Move
{
    uint8_t sourceBin{ 0 };
    Color color{ Color::Empty };
    uint8_t targetQueue{ 0 };

    Move(uint8_t sourceBin, Color color, uint8_t targetQueue);

    bool operator==(const Move& other) const
    {
        return sourceBin == other.sourceBin && color == other.color && targetQueue == other.targetQueue;
    }

};


struct AzulState
{
    std::array<uint8_t, Azul::ColorNumber + 1> bag = {};
    std::array<std::array<uint8_t, Azul::ColorNumber + 1>, Azul::BinNumber + 1> bins = {};

    std::array<PlayerState, Azul::PlayerNumber> players = {};

    uint8_t nextPlayer{ 0 };
    uint8_t firstPlayer{ 0 };
    bool poolWasTouched{ false };

    AzulState() = default;

    AzulState copy() const
    {
        return *this;
    }

    void set_bin(size_t binIndex, Color color, uint8_t count)
    {
        bins[binIndex][static_cast<uint8_t>(color)] = count;
    }

};

struct MoveOutcome
{
    AzulState state;
    bool isRandom;
    bool isEnd;


    MoveOutcome(const AzulState& state, bool isRandom, bool isEnd)
        : state(state),
          isRandom(isRandom),
          isEnd(isEnd)
    {
    }
};
