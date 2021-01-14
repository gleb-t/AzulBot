#pragma once
#include <array>
#include <random>
#include <cstdint>
#include <vector>

// #include "AzulState.h"

struct AzulState;
struct Move;
struct MoveOutcome;
enum class Color : uint8_t;


class Azul
{
public:
    static const uint8_t ColorNumber = 5;
    static const uint8_t TileNumber = 20;
    static const uint8_t PlayerNumber = 2;
    static const uint8_t BinNumber = 5;
    static const uint8_t BinSize = 4;
    static const uint8_t WallSize = 5;
    static const uint8_t FloorSize = 7;
    static const std::array<uint8_t, FloorSize> FloorScores;

    static const uint8_t ScorePerRow;
    static const uint8_t ScorePerColumn;
    static const uint8_t ScorePerColor;

    Azul() = default;

    std::vector<Move> enumerate_moves(const AzulState& state) const;
    MoveOutcome apply_move(const AzulState& state, const Move& move) const;
    
    AzulState deal_round(const AzulState& state, const std::vector<Color>& fixedSample = {});
    void _refill_bag(AzulState& state) const;
    bool is_game_end(const AzulState& state) const;
    bool is_round_end(const AzulState& state) const;

    static Color get_wall_slot_color(uint8_t rowIndex, uint8_t colIndex)
    {
        return static_cast<Color>((colIndex - rowIndex + Azul::ColorNumber) % Azul::ColorNumber + 1);
    }

protected:

    std::mt19937 _randomEngine{std::random_device{}()};
};