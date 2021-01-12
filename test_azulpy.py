import itertools
import unittest

import numpy as np

from azulpy.azul import Azul, Color, Move


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
                move = Move(expSource[0], expSource[1], expTarget)
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
        azul.players[0].wall[1, 0] = Azul.get_wall_slot_color(1, 0)
        expectedTargets = range(1, targetNumber)

        assert_moves_match(expectedSources, expectedTargets, exclude=[Move(1, Color.White, 1)])

    def test_apply_move_sequence(self):
        # This case is taken from the rulebook.
        azul = Azul()

        azul.bins[0, Color.Yellow] = 1
        azul.bins[0, Color.Black] = 2
        azul.bins[0, Color.White] = 1

        azul.bins[1, Color.Yellow] = 1
        azul.bins[1, Color.Red] = 3

        azul.firstPlayer = 1  # We will change it and check later.

        azul = azul.apply_move(Move(0, Color.Black, 1, )).state

        # The pool should hold the leftovers.
        np.testing.assert_equal(azul.bins[-1], [0, 0, 1, 0, 0, 1])  # See 'Color'.
        # The bin should be empty
        np.testing.assert_equal(azul.bins[0], 0)
        # The other bin shouldn't change.
        np.testing.assert_equal(azul.bins[1], [0, 0, 1, 3, 0, 0])

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
        azul = azul.apply_move(Move(1, Color.Yellow, 2, )).state
        azul = azul.apply_move(Move(Azul.BinNumber, Color.Red, 3)).state

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

        self.assertFalse(azul.is_game_end())

        azul.players[0].wall[4] = [Color.Yellow, Color.Red, Color.Black, Color.White, Color.Empty]
        self.assertFalse(azul.is_game_end())

        azul.players[0].wall[:, 0] = [Color.Blue, Color.White, Color.Black, Color.Red, Color.Yellow]
        self.assertFalse(azul.is_game_end())

        azul.players[1].wall[4] = [Color.Yellow, Color.Red, Color.Black, Color.White, Color.Blue]
        self.assertTrue(azul.is_game_end())

    def test_score_game(self):
        azul = Azul()
        # Fill the main diagonal (all blue), the first row and the first column.
        for i in range(Azul.WallShape[0]):
            azul.players[0].wall[i, i] = Azul.get_wall_slot_color(i, i)
            azul.players[0].wall[i, 0] = Azul.get_wall_slot_color(i, 0)
            azul.players[0].wall[0, i] = Azul.get_wall_slot_color(0, i)

        azul.score_game()
        self.assertEqual(azul.players[0].score, Azul.ScorePerRow + Azul.ScorePerColumn + Azul.ScorePerColor)

    def test_full_game(self):
        # Test a full recorded game.
        azul = Azul()

        tilesPerRoundRaw = [
            'RWYYRYUURRWWKKYYWWUR',
            'WWUUUURKKKRUYKRUKYYU',
            'URYKUWYYURYYKKURWWYK',
            'RKKWUUWWRRKUUKWWWKRR',
            'KYYRRYWKYYUWWWKRYRKU'
        ]

        tilesPerRound = [list(map(Azul.str_to_color, tiles)) for tiles in tilesPerRoundRaw]

        # Moves alternate between players 0 and 1 within a round.
        # The game keeps track of which player goes first each round, we only specify the very first.
        firstPlayer = 0
        movesPerRoundRaw = [
            [
                '3K1', '4W3', '0Y3', '2W3',
                '5R2', '5Y1', '5W0', '1R0',
                '5U4', '5Y5'
            ],
            [
                '4Y3', '2K4', '0U4', '1U2',
                '3K0', '5Y0', '5R1', '5K4',
                '5U2', '5W1'
            ],
            [
                       '4K4', '2Y1', '5U2',
                '1Y2', '0K0', '3R0', '5U1',
                '5Y2', '5K3', '5W4', '5R5'
            ],
            [
                       '3W2', '1W4', '2R4',
                '5U3', '5K3', '0R5', '5W2',
                '5K2', '4R1', '5K2', '5W0'
            ],
            [
                '2U1', '4U0', '3W2', '5R4',
                '5K3', '5Y2', '5W2', '1R4',
                '5Y0', '5K1', '0K3', '5Y3',
                '5R4', '5W5'
            ]
        ]

        movesPerRound = [list(map(Move.from_str, moves)) for moves in movesPerRoundRaw]

        scoresPerRound = [
            [4, 3],
            [19, 5],
            [33, 16],
            [45, 37],
            [54, 55]
        ]
        finalScores = [70, 71]

        # Simulate the game and check the score each round.
        azul.nextPlayer = firstPlayer
        for iRound, (tiles, moves, scores) in enumerate(zip(tilesPerRound, movesPerRound, scoresPerRound)):
            azul.deal_round(fixedSample=tiles)

            for move in moves:
                azul = azul.apply_move(move).state

            self.assertTrue(azul.is_round_end())
            azul.score_round()

            self.assertEqual([p.score for p in azul.players], scores)

        azul.score_game()
        self.assertEqual([p.score for p in azul.players], finalScores)

    def test_hash(self):
        import copy

        azul1 = Azul()
        azul1.bins[1] = [0, 2, 3, 4, 5, 6]
        azul1.players[0].wall[1, 1] = Azul.get_wall_slot_color(1, 1)

        azul2 = copy.deepcopy(azul1)

        self.assertEqual(azul1, azul2)
        self.assertEqual(hash(azul1), hash(azul2))

        azul2.bins[1, 1] = 5

        self.assertNotEqual(azul1, azul2)
        self.assertNotEqual(hash(azul1), hash(azul2))

        azul2 = copy.deepcopy(azul1)
        azul2.players[1].score = 1

        self.assertNotEqual(azul1, azul2)
        self.assertNotEqual(hash(azul1), hash(azul2))

        azul2 = copy.deepcopy(azul1)
        azul2.players[1].queue[0] = [1, 1]

        self.assertNotEqual(azul1, azul2)
        self.assertNotEqual(hash(azul1), hash(azul2))

        # Trying using as keys in a dict. This shouldn't throw.
        d1 = {azul1: 'a1', azul2: 'a2'}
        d2 = copy.deepcopy(d1)

        d1[azul1] = 'a1'
        self.assertEqual(d1, d2)





