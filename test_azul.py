import unittest

from azul import Azul, Color, Move


class TestAzul(unittest.TestCase):

    def test_enumerate_moves_basic(self):
        # Init an empty board, and init with a few tiles.
        azul = Azul()

        azul.bins[0][0] = Color.Red
        azul.bins[0][1] = Color.Red
        azul.bins[0][2] = Color.Blue
        azul.bins[0][3] = Color.Black

        azul.bins[1][0] = Color.White
        azul.bins[1][1] = Color.White
        azul.bins[1][2] = Color.White
        azul.bins[1][3] = Color.White

        expectedSources = [(0, Color.Red, 2), (0, Color.Blue, 1), (0, Color.Black, 1),
                           (1, Color.White, 4)]
        targetNumber = Azul.WallShape[0] + 1

        output = list(azul.enumerate_moves())
        for expSource, expTarget in zip(expectedSources, range(targetNumber)):
            self.assertIn(Move(expSource[0], expTarget, expSource[1], expSource[2]), output)

        self.assertEqual(len(output), len(expectedSources) * (targetNumber))

        # Now put something in the pool, we should get extra moves.
        azul.pool[0] = Color.Yellow
        expectedSources.append((Azul.BinNumber, Color.Yellow, 1))

        output = list(azul.enumerate_moves())
        for expSource, expTarget in zip(expectedSources, range(targetNumber)):
            self.assertIn(Move(expSource[0], expTarget, expSource[1], expSource[2]), output)

        output = list(azul.enumerate_moves())
        for expSource, expTarget in zip(expectedSources, range(targetNumber)):
            self.assertIn(Move(expSource[0], expTarget, expSource[1], expSource[2]), output)

        self.assertEqual(len(output), len(expectedSources) * (targetNumber))

