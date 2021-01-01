import itertools
import unittest

from azul import Azul, Color, Move


class TestAzul(unittest.TestCase):

    def test_enumerate_moves_basic(self):
        # Init an empty board, and init with a few tiles.
        azul = Azul()

        azul.bins[0][Color.Red] = 2
        azul.bins[0][Color.Blue] = 1
        azul.bins[0][Color.Black] = 1

        azul.bins[1][Color.White] = 4

        expectedSources = [(0, Color.Red, 2), (0, Color.Blue, 1), (0, Color.Black, 1),
                           (1, Color.White, 4)]
        targetNumber = Azul.WallShape[0] + 1
        expectedTargets = range(targetNumber)

        def assert_moves_match(sources, targets, exclude=None):
            exclude = exclude or []
            output = list(azul.enumerate_moves())
            sourceTargetProduct = list(itertools.product(sources, targets))
            for expSource, expTarget in sourceTargetProduct:
                move = Move(expSource[0], expTarget, expSource[1], expSource[2])
                if move not in exclude:
                    self.assertIn(move, output)

            self.assertEqual(len(output), len(sourceTargetProduct) - len(exclude))

        assert_moves_match(expectedSources, expectedTargets)

        # Now put something in the pool, we should get extra moves.
        azul.pool[Color.Yellow] = 1
        expectedSources.append((Azul.BinNumber, Color.Yellow, 1))

        assert_moves_match(expectedSources, expectedTargets)

        # Fill up one of the queues, some moves should become invalid.
        azul.playerStates[0].queue[0] = (Color.White, 1)
        expectedTargets = range(1, targetNumber)

        assert_moves_match(expectedSources, expectedTargets)

        # Block a row of the wall, adding more invalid moves.
        azul.playerStates[0].wall[1, 0] = Azul.get_wall_slot_color((1, 0))
        expectedTargets = range(1, targetNumber)

        assert_moves_match(expectedSources, expectedTargets, exclude=[Move(1, 1, Color.White, 4)])

