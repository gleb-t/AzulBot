#include "AzulState.h"
#include "utils.h"

size_t PlayerState::hash() const
{
    size_t h{0};
    for (const auto& row : wall)
        for (Color color : row)
            h = hash_combine(h, static_cast<uint8_t>(color));

    for (const auto& row : queue)
        h = hash_combine(hash_combine(h, row[0]), row[1]);

    h = hash_combine(h, floorCount);
    h = hash_combine(h, score);

    return h;
}

Move::Move(uint8_t sourceBin, Color color, uint8_t targetQueue)
    :sourceBin(sourceBin), color(color), targetQueue(targetQueue)
{
}

size_t AzulState::hash() const
{
    size_t h{0};
    for (auto count : bag)
        h = hash_combine(h, count);

    for (const auto& bin : bins)
        for (auto count : bin)
            h = hash_combine(h, count);

    for (const auto& player : players)
        h = hash_combine(h, player.hash());

    h = hash_combine(h, nextPlayer);
    h = hash_combine(h, firstPlayer);
    h = hash_combine(h, poolWasTouched);

    return h;
}
