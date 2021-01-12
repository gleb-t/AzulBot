#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <vector>

static const uint8_t WallSize = 5;


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
    std::array<std::array<Color, WallSize>, WallSize> wall = {};
    std::array<std::array<uint8_t, 2>, WallSize> queue = {};
    uint8_t floorCount = 0;
    uint32_t score = 0;

    void set_wall(uint8_t rowIndex, uint8_t colIndex, Color color)
    {
        wall[rowIndex][colIndex] = color;
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


class AzulState
{
public:
    static const uint8_t ColorNumber = 5;
    static const uint8_t TileNumber = 20;
    static const uint8_t PlayerNumber = 2;
    static const uint8_t BinNumber = 5;
    static const uint8_t BinSize = 4;
    static const uint8_t WallSize = WallSize;
    static const uint8_t FloorSize = 7;
    static const std::array<uint8_t, FloorSize> FloorScores;

    static const uint8_t ScorePerRow;
    static const uint8_t ScorePerColumn;
    static const uint8_t ScorePerColor;

    std::array<uint8_t, ColorNumber + 1> bag = {};
    std::array<std::array<uint8_t, ColorNumber + 1>, BinNumber + 1> bins = {};

    std::array<PlayerState, PlayerNumber> players = {};

    uint8_t nextPlayer{ 0 };
    uint8_t firstPlayer{ 0 };
    bool poolWasTouched{ false };

    AzulState();

    void set_bin(size_t binIndex, Color color, uint8_t count)
    {
        bins[binIndex][static_cast<uint8_t>(color)] = count;
    }

    std::vector<Move> enumerate_moves();

    static Color get_wall_slot_color(uint8_t rowIndex, uint8_t colIndex)
    {
        return static_cast<Color>((colIndex - rowIndex + ColorNumber) % ColorNumber + 1);
    }
};
