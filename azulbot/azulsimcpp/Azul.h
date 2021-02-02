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
    static constexpr uint8_t ColorNumber = 5;
    static constexpr uint8_t TileNumber = 20;
    static constexpr uint8_t PlayerNumber = 2;
    static constexpr uint8_t BinNumber = 5;
    static constexpr uint8_t BinSize = 4;
    static constexpr uint8_t WallSize = 5;
    static constexpr uint8_t FloorSize = 7;
    static constexpr std::array<uint8_t, FloorSize> FloorScores;

    static constexpr uint8_t ScorePerRow = 2;
    static constexpr uint8_t ScorePerColumn = 7;
    static constexpr uint8_t ScorePerColor = 10;

    Azul() = default;

    std::vector<Move> enumerate_moves(const AzulState& state) const;
    MoveOutcome apply_move(const AzulState& state, const Move& move) const;
    AzulState playout(const AzulState& state, uint32_t maxRoundTimeout = 100);
    
    AzulState deal_round(const AzulState& state, const std::vector<Color>& fixedSample = {});
    AzulState score_round(const AzulState& state) const;
    AzulState score_game(const AzulState& state) const;
    void _refill_bag(AzulState& state) const;
    bool is_game_end(const AzulState& state) const;
    bool is_round_end(const AzulState& state) const;

    static uint32_t get_tile_score(std::array<std::array<Color, WallSize>, WallSize> wall, uint8_t iRow, uint8_t iCol);
    static Color get_wall_slot_color(uint8_t rowIndex, uint8_t colIndex)
    {
        return static_cast<Color>((colIndex - rowIndex + Azul::ColorNumber) % Azul::ColorNumber + 1);
    }
    static uint8_t get_wall_column_by_color(uint8_t rowIndex, Color color)
    {
        return (static_cast<uint8_t>(color) - 1 + rowIndex) % Azul::ColorNumber;
    }


protected:

    std::mt19937 _randomEngine{std::random_device{}()};
};

