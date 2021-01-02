import itertools
import unittest

import numpy as np

from azul import Azul, Color, Move


class TestAzul(unittest.TestCase):

    def test_enumerate_moves_basic(self):
        # Init an empty board, and init with a few tiles.
        azul = Azul()

        azul.bins[0][Color.Red] = 2
        azul.bins[0][Color.Blue] = 1
        azul.bins[0][Color.Black] = 1

        azul.bins[1][Color.White] = 4

        expectedSources = [(0, Color.Red), (0, Color.Blue), (0, Color.Black),
                           (1, Color.White)]
        targetNumber = Azul.WallShape[0] + 1
        expectedTargets = range(targetNumber)

        def assert_moves_match(sources, targets, exclude=None):
            exclude = exclude or []
            output = list(azul.enumerate_moves())
            sourceTargetProduct = list(itertools.product(sources, targets))
            for expSource, expTarget in sourceTargetProduct:
                move = Move(expSource[0], expTarget, expSource[1])
                if move not in exclude:
                    self.assertIn(move, output)

            self.assertEqual(len(output), len(sourceTargetProduct) - len(exclude))

        assert_moves_match(expectedSources, expectedTargets)

        # Now put something in the pool, we should get extra moves.
        azul.bins[Azul.BinNumber, Color.Yellow] = 1
        expectedSources.append((Azul.BinNumber, Color.Yellow))

        assert_moves_match(expectedSources, expectedTargets)

        # Fill up one of the queues, some moves should become invalid.
        azul.players[0].queue[0] = (Color.White, 1)
        expectedTargets = range(1, targetNumber)

        assert_moves_match(expectedSources, expectedTargets)

        # Block a row of the wall, adding more invalid moves.
        azul.players[0].wall[1, 0] = Azul.get_wall_slot_color((1, 0))
        expectedTargets = range(1, targetNumber)

        assert_moves_match(expectedSources, expectedTargets, exclude=[Move(1, 1, Color.White)])

    def test_apply_move_basic(self):
        # This case is taken from the rulebook.
        azul = Azul()

        azul.bins[0, Color.Yellow] = 1
        azul.bins[0, Color.Black] = 2
        azul.bins[0, Color.White] = 1

        azul.bins[1, Color.Yellow] = 1
        azul.bins[1, Color.Red] = 3

        azul.firstPlayer = 1  # We will change it and check later.

        azul = azul.apply_move(Move(0, 1, Color.Black))

        # The pool should hold the leftovers.
        np.testing.assert_equal(azul.bins[-1], [0, 0, 1, 0, 0, 1])  # See 'Color'.

        # The queue should only hold black.
        np.testing.assert_equal(azul.players[0].queue[1], [Color.Black, 2])
        for i, q in enumerate(azul.players[0].queue):
            if i != 1:
                np.testing.assert_equal(q, [0, 0])

        # Nothing should be on the floor.
        self.assertEqual(azul.players[0].floorCount, 0)
        # The wall shouldn't be affected.
        self.assertEqual(np.count_nonzero(azul.players[0].wall), 0)
        # Player two shouldn't be affected.
        self.assertEqual(np.count_nonzero(azul.players[1].queue), 0)
        # Next player is tobe updated.
        self.assertEqual(azul.nextPlayer, 1)

        # Make a few more moves.
        azul = azul.apply_move(Move(1, 2, Color.Yellow))
        azul = azul.apply_move(Move(Azul.BinNumber, 3, Color.Red))

        # Check the pool.
        np.testing.assert_equal(azul.bins[-1], [0, 0, 1, 0, 0, 1])
        self.assertEqual(azul.poolWasTouched, True)
        # Check the first player queues.
        np.testing.assert_equal(azul.players[0].queue[1], [Color.Black, 2])
        np.testing.assert_equal(azul.players[0].queue[3], [Color.Red, 3])
        for i, q in enumerate(azul.players[0].queue):
            if i != 1 and i != 3:
                np.testing.assert_equal(q, [0, 0])

        # Check the second player queues.
        np.testing.assert_equal(azul.players[1].queue[2], [Color.Yellow, 1])
        for i, q in enumerate(azul.players[1].queue):
            if i != 2:
                np.testing.assert_equal(q, [0, 0])

        # Check the floors.
        self.assertEqual(azul.players[0].floorCount, 1)
        self.assertEqual(azul.players[1].floorCount, 0)
        # The wall shouldn't be affected.
        self.assertEqual(np.count_nonzero(azul.players[0].wall), 0)
        self.assertEqual(np.count_nonzero(azul.players[1].wall), 0)
        # Check the next player.
        self.assertEqual(azul.nextPlayer, 1)
        # Check who goes first next round.
        self.assertEqual(azul.firstPlayer, 0)

    def test_score_round(self):

        azul = Azul()

        azul.players[0].wall[0, 3] = Color.Black
        azul.players[0].wall[1, 0:3] = (Color.White, Color.Blue, Color.Yellow)
        azul.players[0].queue[0] = (Color.White, 1)  # Scores 2.
        azul.players[0].queue[1] = (Color.Red, 2)    # Scores 6.
        azul.players[0].queue[2] = (Color.Black, 3)  # Scores 2.
        azul.players[0].queue[3] = (Color.Red, 3)    # Scores 0.
        azul.players[0].queue[4] = (Color.Blue, 5)   # Scores 1.
        azul.players[0].floorCount = 3

        azul.players[1].wall[3, :] = (Color.Red, Color.Black, Color.Empty, Color.Blue, Color.Yellow)
        azul.players[1].wall[:, 2] = (Color.Red, Color.Yellow, Color.Blue, Color.Empty, Color.Black)
        azul.players[1].queue[0] = (Color.Yellow, 1)  # Scores 2.
        azul.players[1].queue[3] = (Color.White, 4)   # Scores 10
        azul.players[1].floorCount = 1

        azul.score_round_and_deal()

        self.assertEqual(azul.players[0].score, 7)
        self.assertEqual(azul.players[1].score, 11)

        np.testing.assert_equal(azul.players[0].queue[0:3], 0)
        np.testing.assert_equal(azul.players[0].queue[3], [Color.Red, 3])
        np.testing.assert_equal(azul.players[0].queue[4], 0)

        np.testing.assert_equal(azul.players[1].queue, 0)

        self.assertEqual(azul.players[0].floorCount, 0)
        self.assertEqual(azul.players[1].floorCount, 0)
