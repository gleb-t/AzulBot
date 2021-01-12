#include "AzulState.h"

#include <algorithm>

const std::array<uint8_t, AzulState::FloorSize> AzulState::FloorScores = { 1, 1, 2, 2, 2, 3, 3 };

Move::Move(uint8_t sourceBin, Color color, uint8_t targetQueue)
    :sourceBin(sourceBin), color(color), targetQueue(targetQueue)
{
}


AzulState::AzulState() = default;


std::vector<Move> AzulState::enumerate_moves()
{
    PlayerState& player = players[nextPlayer];

    std::vector<Move> moves{};
    for (size_t iSource = 0; iSource < bins.size(); iSource++)
    {
        auto& source = bins[iSource];
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
            moves.push_back(Move{ static_cast<uint8_t>(iSource),
                                         static_cast<Color>(iColor),
                                         static_cast<uint8_t>(WallSize) });

        }
    }

    return moves;
}
