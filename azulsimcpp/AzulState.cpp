#include "AzulState.h"


Move::Move(uint8_t sourceBin, Color color, uint8_t targetQueue)
    :sourceBin(sourceBin), color(color), targetQueue(targetQueue)
{
}
