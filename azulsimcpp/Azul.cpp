#include "Azul.h"
#include <algorithm>
#include <stdexcept>

#include "AzulState.h"

const std::array<uint8_t, Azul::FloorSize> Azul::FloorScores = { 1, 1, 2, 2, 2, 3, 3 };

std::vector<Move> Azul::enumerate_moves(const AzulState& state) const
{
    const PlayerState& player = state.players[state.nextPlayer];

    std::vector<Move> moves{};
    for (size_t iSource = 0; iSource < state.bins.size(); iSource++)
    {
        auto& source = state.bins[iSource];
        for (size_t iColor = 0; iColor < source.size(); iColor++)
        {
            const uint8_t count = source[iColor];
            if (count == 0)
                continue;

            for (size_t iTarget = 0; iTarget < player.queue.size(); iTarget++)
            {
                auto& targetRow = player.wall[iTarget];
                auto& targetQueue = player.queue[iTarget];
                // If the color isn't already on the wall in that row,
                // and the queue has space(its size is index + 1),
                // and the queue is completely empty(first element empty) or contains the same color.
                if (std::all_of(targetRow.begin(), targetRow.end(),
                    [iColor](Color c) { return c != static_cast<Color>(iColor); }) &&
                    targetQueue[1] < iTarget + 1 &&
                    (targetQueue[0] == static_cast<uint8_t>(Color::Empty) or targetQueue[0] == iColor))
                {
                    moves.emplace_back(static_cast<uint8_t>(iSource),
                                       static_cast<Color>(iColor),
                                       static_cast<uint8_t>(iTarget));
                }
            }

            // It's always valid to put the tiles on the floor.
            moves.emplace_back(static_cast<uint8_t>(iSource),
                               static_cast<Color>(iColor),
                               static_cast<uint8_t>(WallSize));

        }
    }

    return moves;
}

MoveOutcome Azul::apply_move(const AzulState& state, const Move& move) const
{
    AzulState next{state};
    auto& player = next.players[state.nextPlayer];
    const uint8_t tilesTaken = state.bins[move.sourceBin][static_cast<size_t>(move.color)];

    if (tilesTaken == 0)
        throw std::invalid_argument{"Not allowed to take zero tiles."};

    // Update who goes first next round (changes when the pool is touched for the first time).
    if (move.sourceBin == Azul::BinNumber)
    {
        const bool becomeFirstPlayer = !state.poolWasTouched;
        next.poolWasTouched = true;
        if (becomeFirstPlayer)
        {
            player.floorCount++;
            next.firstPlayer = state.nextPlayer;
        }
    }

    // Pass the turn to the next player.
    next.nextPlayer = (state.nextPlayer + 1) % Azul::PlayerNumber;

    // Take away the tiles of the moved color.
    next.bins[move.sourceBin][static_cast<size_t>(move.color)] = 0;

    // If the move is to take tiles from a bin, then move the rest into the pool.
    if (move.sourceBin < Azul::BinNumber)
    {
        for (size_t iColor = 0; iColor < next.bins[move.sourceBin].size(); iColor++)
        {
            next.bins[Azul::BinNumber][iColor] += next.bins[move.sourceBin][iColor];
            next.bins[move.sourceBin][iColor] = 0;
        }
    }

    if (move.targetQueue < Azul::WallSize)
    {
        // Place the tiles into the queue.
        const int queueSize = move.targetQueue + 1;
        const int queueCount = player.queue[move.targetQueue][1];
        const int newCount = queueCount + tilesTaken;
        // Put the tiles into the queue, move the leftovers onto the floor.
        player.queue[move.targetQueue][0] = static_cast<uint8_t>(move.color);
        player.queue[move.targetQueue][1] = static_cast<uint8_t>(std::min({ newCount, queueSize }));
        player.floorCount += std::max({ newCount - queueSize, 0 });
    }
    else
    {
        // Place tiles onto the floor.
        player.floorCount += tilesTaken;
    }


    return MoveOutcome{next, is_round_end(next), is_game_end(next)};
}

bool Azul::is_game_end(const AzulState& state) const
{
    for (const auto& player : state.players)
    {
        for (const auto& row : player.wall)
        {
            if (std::count_if(row.begin(), row.end(), 
                              [](Color val) { return val != Color::Empty; }))
            {
                return true;
            }
        }
    }

    return false;
}

bool Azul::is_round_end(const AzulState& state) const
{
    for (const auto& bin : state.bins)
        if (!std::all_of(bin.begin(), bin.end(), [](uint8_t val) { return val == 0; }))
            return false;

    return true;
}
