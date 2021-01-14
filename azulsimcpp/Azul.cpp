#include "Azul.h"
#include <algorithm>
#include <numeric>
#include <cassert>
#include <iterator>
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

    // todo Maybe we should be returning an rvalue. Check pybind return policies.
    return MoveOutcome{next, is_round_end(next), is_game_end(next)};
}


AzulState Azul::deal_round(const AzulState& state, const std::vector<Color>& fixedSample)
{
    AzulState next{state};

    if (!is_round_end(state))
        throw std::runtime_error{"Not allowed to deal a new round before the old has ended."};

    // Refill the bag using the discarded tiles, if necessary.
    const uint8_t sampleSize = Azul::BinNumber * Azul::BinSize;
    const uint8_t bagCount = std::accumulate(next.bag.begin(), next.bag.end(), decltype(next.bag)::value_type{0});
    if (bagCount < sampleSize)
    {
        _refill_bag(next);
    }

    // Randomly sample the bag to get the tiles for this round.
    std::vector<Color> sample{};
    if (fixedSample.empty())
    {
        std::vector<Color> population{};
        for (size_t iColor = 0; iColor < next.bag.size(); iColor++)
            for (uint8_t i = 0; i < next.bag[iColor]; i++)
                population.push_back(static_cast<Color>(iColor));

    	
        std::sample(population.begin(), population.end(), std::back_inserter(sample), sampleSize, _randomEngine);
    }
    else
    {
        assert(fixedSample.size() == sampleSize);
        sample = fixedSample;
    }

	// Distribute the sampled tiles among the bins.
    for (auto& bin : next.bins)
        std::fill(bin.begin(), bin.end(), 0);

	for (size_t iTile = 0; iTile < sample.size(); iTile++)
	{
        Color color = sample[iTile];
        const auto binIndex = static_cast<size_t>(iTile / Azul::BinSize);
        next.bins[binIndex][static_cast<size_t>(color)] += 1;

        // Keep track of which tiles are left in the bag.
        next.bag[static_cast<size_t>(color)] -= 1;
	}

	// Prepare the first player flags.
    next.poolWasTouched = false;
    next.nextPlayer = next.firstPlayer;

    return next;
}

void Azul::_refill_bag(AzulState& state) const
{
    // First, count all the tiles that lie on the board, they won't be redrawn.
    std::array<uint8_t, Azul::ColorNumber + 1> missingTiles{};
    for (const PlayerState& player : state.players)
    {
        for (const auto& queueRow : player.queue)
            missingTiles[static_cast<size_t>(queueRow[0])] += queueRow[1];

        for (const auto& wallRow : player.wall)
            for (Color color : wallRow)
                missingTiles[static_cast<size_t>(color)] += 1;
    }

    // The rest are the discarded tiles that return back into the bag.
    for (size_t iColor = 0; iColor < missingTiles.size(); iColor++)
        if (static_cast<Color>(iColor) != Color::Empty)
            state.bag[iColor] = Azul::TileNumber - missingTiles[iColor];

    assert(state.bag[static_cast<size_t>(Color::Empty)] == 0);
}

bool Azul::is_game_end(const AzulState& state) const
{
    for (const auto& player : state.players)
    {
        for (const auto& row : player.wall)
        {
            if (std::count_if(row.begin(), row.end(), 
                              [](Color val) { return val != Color::Empty; }) == Azul::WallSize)
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
