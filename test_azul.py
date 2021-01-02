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

    def test_apply_move_sequence(self):
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

        azul.score_round()

        self.assertEqual(azul.players[0].score, 7)
        self.assertEqual(azul.players[1].score, 11)

        np.testing.assert_equal(azul.players[0].queue[0:3], 0)
        np.testing.assert_equal(azul.players[0].queue[3], [Color.Red, 3])
        np.testing.assert_equal(azul.players[0].queue[4], 0)

        np.testing.assert_equal(azul.players[1].queue, 0)

        self.assertEqual(azul.players[0].floorCount, 0)
        self.assertEqual(azul.players[1].floorCount, 0)

    def test_deal_round_basic(self):
        azul = Azul()

        azul.firstPlayer = 1
        azul.poolWasTouched = True

        azul.deal_round()

        self.assertEqual(azul.nextPlayer, 1)
        self.assertEqual(azul.poolWasTouched, False)

        for b in azul.bins[:-1]:
            self.assertEqual(sum(b), Azul.BinSize)
            self.assertEqual(b[Color.Empty], 0)

        np.testing.assert_equal(azul.bins[-1], Color.Empty)

        # Check that the total number of each color's tiles in all the bins
        # is exactly what's missing from the bag.
        for color, count in enumerate(np.sum(azul.bins, axis=0)):
            if color == Color.Empty:
                self.assertEqual(azul.bag[color], 0)
            else:
                self.assertEqual(azul.bag[color], Azul.TileNumber - count)

    def test_deal_round_one_color_left(self):
        bag = np.zeros(Azul.ColorNumber + 1, dtype=np.uint8)
        bag[Color.Blue] = Azul.TileNumber
        azul = Azul(bag=bag)

        azul.deal_round()

        self.assertEqual(np.sum(azul.bins[:, Color.Blue]), Azul.TileNumber)
        np.testing.assert_equal(azul.bag, 0)

    def test_refill_bag(self):
        azul = Azul()

        azul.players[0].wall[0] = [Color.Blue, Color.Yellow, Color.Red, Color.Empty, Color.Empty]
        azul.players[0].wall[1] = [Color.Empty, Color.Blue, Color.Empty, Color.Empty, Color.Empty]
        azul.players[1].queue[3] = [Color.Black, 2]

        azul._refill_bag()

        np.testing.assert_equal(azul.bag, [0, Azul.TileNumber - 2, Azul.TileNumber - 1,
                                           Azul.TileNumber - 1, Azul.TileNumber - 2, Azul.TileNumber])

    def test_dealing_round_refills_bag(self):

        azul = Azul()
        azul.bag[...] = 0

        azul.deal_round()

        self.assertEqual(np.sum(azul.bag), Azul.ColorNumber * Azul.TileNumber - Azul.BinNumber * Azul.BinSize)

    def test_is_end_of_game(self):
        azul = Azul()

        self.assertFalse(azul.is_end_of_game())

        azul.players[0].wall[4] = [Color.Yellow, Color.Red, Color.Black, Color.White, Color.Empty]
        self.assertFalse(azul.is_end_of_game())

        azul.players[0].wall[:, 0] = [Color.Blue, Color.White, Color.Black, Color.Red, Color.Yellow]
        self.assertFalse(azul.is_end_of_game())

        azul.players[1].wall[4] = [Color.Yellow, Color.Red, Color.Black, Color.White, Color.Blue]
        self.assertTrue(azul.is_end_of_game())



