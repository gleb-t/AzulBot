import itertools
import unittest

import numpy as np

from azulbot.azulsim import Azul, Color, Move


class TestAzul(unittest.TestCase):

    def test_enumerate_moves_basic(self):
        # Init an empty board, and init with a few tiles.
        azul = Azul()
        state = azul.get_init_state()

        state.set_bin(0, Color.Red, 2)
        state.set_bin(0, Color.Blue, 1)
        state.set_bin(0, Color.Black, 1)

        state.set_bin(1, Color.White, 4)

        expectedSources = [(0, Color.Red), (0, Color.Blue), (0, Color.Black),
                           (1, Color.White)]
        targetNumber = Azul.WallSize + 1
        expectedTargets = range(targetNumber)

        def assert_moves_match(sources, targets, exclude=None):
            exclude = exclude or []
            output = list(azul.enumerate_moves(state))
            sourceTargetProduct = list(itertools.product(sources, targets))
            for expSource, expTarget in sourceTargetProduct:
                move = Move(expSource[0], expSource[1], expTarget)
                if move not in exclude:
                    self.assertIn(move, output)

            self.assertEqual(len(output), len(sourceTargetProduct) - len(exclude))

        assert_moves_match(expectedSources, expectedTargets)

        # Now put something in the pool, we should get extra moves.
        state.set_bin(Azul.BinNumber, Color.Yellow, 1)
        expectedSources.append((Azul.BinNumber, Color.Yellow))

        assert_moves_match(expectedSources, expectedTargets)

        # Fill up one of the queues, some moves should become invalid.
        state.players[0].set_queue(0, Color.White, 1)
        expectedTargets = range(1, targetNumber)

        assert_moves_match(expectedSources, expectedTargets)

        # Block a row of the wall, adding more invalid moves.
        state.players[0].set_wall(1, 0, Azul.get_wall_slot_color(1, 0))
        expectedTargets = range(1, targetNumber)

        assert_moves_match(expectedSources, expectedTargets, exclude=[Move(1, Color.White, 1)])

    def test_apply_move_sequence(self):
        # This case is taken from the rulebook.
        azul = Azul()
        state = azul.get_init_state()

        state.set_bin(0, Color.Yellow, 1)
        state.set_bin(0, Color.Black, 2)
        state.set_bin(0, Color.White, 1)

        state.set_bin(1, Color.Yellow, 1)
        state.set_bin(1, Color.Red, 3)

        state.firstPlayer = 1  # We will change it and check later.

        state = azul.apply_move_without_scoring(state, Move(0, Color.Black, 1, )).state

        # The pool should hold the leftovers.
        self.assertEqual(state.bins[-1], [0, 0, 1, 0, 0, 1])  # See 'Color'.
        # The bin should be empty
        self.assertEqual(state.bins[0], [0] * (Azul.ColorNumber + 1))
        # The other bin shouldn't change.
        self.assertEqual(state.bins[1], [0, 0, 1, 3, 0, 0])

        # The queue should only hold black.
        self.assertEqual(state.players[0].queue[1], [int(Color.Black), 2])
        for i, q in enumerate(state.players[0].queue):
            if i != 1:
                self.assertEqual(q, [0, 0])

        # Nothing should be on the floor.
        self.assertEqual(state.players[0].floorCount, 0)
        # The wall shouldn't be affected.
        self.assertEqual(np.count_nonzero(np.array(state.players[0].wall, dtype=np.int32)), 0)
        # Player two shouldn't be affected.
        self.assertEqual(np.count_nonzero(state.players[1].queue), 0)
        # Next player is tobe updated.
        self.assertEqual(state.nextPlayer, 1)

        # Make a few more moves.
        state = azul.apply_move_without_scoring(state, Move(1, Color.Yellow, 2, )).state
        state = azul.apply_move_without_scoring(state, Move(Azul.BinNumber, Color.Red, 3)).state

        # Check the pool.
        self.assertEqual(state.bins[-1], [0, 0, 1, 0, 0, 1])
        self.assertEqual(state.poolWasTouched, True)
        # Check the first player queues.
        self.assertEqual(state.players[0].queue[1], [int(Color.Black), 2])
        self.assertEqual(state.players[0].queue[3], [int(Color.Red), 3])
        for i, q in enumerate(state.players[0].queue):
            if i != 1 and i != 3:
                self.assertEqual(q, [0, 0])

        # Check the second player queues.
        self.assertEqual(state.players[1].queue[2], [int(Color.Yellow), 1])
        for i, q in enumerate(state.players[1].queue):
            if i != 2:
                self.assertEqual(q, [0, 0])

        # Check the floors.
        self.assertEqual(state.players[0].floorCount, 1)
        self.assertEqual(state.players[1].floorCount, 0)
        # The wall shouldn't be affected.
        self.assertEqual(np.count_nonzero(np.array(state.players[0].wall, dtype=np.int32)), 0)
        self.assertEqual(np.count_nonzero(np.array(state.players[1].wall, dtype=np.int32)), 0)
        # Check the next player.
        self.assertEqual(state.nextPlayer, 1)
        # Check who goes first next round.
        self.assertEqual(state.firstPlayer, 0)

    def test_score_round(self):

        azul = Azul()
        state = azul.get_init_state()

        state.players[0].set_wall(0, 3, Color.Black)
        state.players[0].set_wall(1, 0, Color.White)
        state.players[0].set_wall(1, 1, Color.Blue)
        state.players[0].set_wall(1, 2, Color.Yellow)
        state.players[0].set_queue(0, Color.White, 1)  # Scores 2.
        state.players[0].set_queue(1, Color.Red, 2)    # Scores 6.
        state.players[0].set_queue(2, Color.Black, 3)  # Scores 2.
        state.players[0].set_queue(3, Color.Red, 3)  # Scores 0.
        state.players[0].set_queue(4, Color.Blue, 5)  # Scores 1.

        state.players[0].floorCount = 3

        state.players[1].set_wall_row(3, [Color.Red, Color.Black, Color.Empty, Color.Blue, Color.Yellow])
        state.players[1].set_wall_col(2, [Color.Red, Color.Yellow, Color.Blue, Color.Empty, Color.Black])
        state.players[1].set_queue(0, Color.Yellow, 1)  # Scores 2.
        state.players[1].set_queue(3, Color.White, 4)   # Scores 10
        state.players[1].floorCount = 1

        state = azul.score_round(state)

        self.assertEqual(state.players[0].score, 7)
        self.assertEqual(state.players[1].score, 11)

        self.assertEqual(state.players[0].queue[0:3], [[0, 0]] * 3)
        self.assertEqual(state.players[0].queue[3], [int(Color.Red), 3])
        self.assertEqual(state.players[0].queue[4], [0, 0])

        self.assertEqual(state.players[1].queue, np.zeros_like(np.array(state.players[1].queue)).tolist())

        self.assertEqual(state.players[0].floorCount, 0)
        self.assertEqual(state.players[1].floorCount, 0)

    def test_deal_round_basic(self):
        azul = Azul()
        state = azul.get_init_state()

        state.firstPlayer = 1
        state.poolWasTouched = True

        state = azul.deal_round(state)

        self.assertEqual(state.nextPlayer, 1)
        self.assertEqual(state.poolWasTouched, False)

        for b in state.bins[:-1]:
            self.assertEqual(sum(b), Azul.BinSize)
            self.assertEqual(b[Color.Empty], 0)

        self.assertEqual(state.bins[-1], [int(Color.Empty)] * (Azul.ColorNumber + 1))

        # Check that the total number of each color's tiles in all the bins
        # is exactly what's missing from the bag.
        for color, count in enumerate(np.sum(np.array(state.bins), axis=0)):
            if Color(color) == Color.Empty:
                self.assertEqual(state.bag[color], 0)
            else:
                self.assertEqual(state.bag[color], Azul.TileNumber - count)

    def test_deal_round_one_color_left(self):
        azul = Azul()
        state = azul.get_init_state()

        bag = np.zeros(Azul.ColorNumber + 1, dtype=np.uint8)
        bag[Color.Blue] = Azul.TileNumber
        state.bag = bag.tolist()

        state = azul.deal_round(state)

        self.assertEqual(np.sum(np.array(state.bins)[:, Color.Blue]), Azul.TileNumber)
        self.assertEqual(state.bag, [0] * (Azul.ColorNumber + 1))

    def test_refill_bag(self):
        azul = Azul()
        state = azul.get_init_state()

        state.players[0].set_wall_row(0, [Color.Blue, Color.Yellow, Color.Red, Color.Empty, Color.Empty])
        state.players[0].set_wall_row(1, [Color.Empty, Color.Blue, Color.Empty, Color.Empty, Color.Empty])
        state.players[1].set_queue(3, Color.Black, 2)

        azul._refill_bag(state)

        self.assertEqual(state.bag, [0, Azul.TileNumber - 2, Azul.TileNumber - 1,
                                     Azul.TileNumber - 1, Azul.TileNumber - 2, Azul.TileNumber])

    def test_dealing_round_refills_bag(self):

        azul = Azul()
        state = azul.get_init_state()
        state.bag = np.zeros_like(np.array(state.bag)).tolist()

        state = azul.deal_round(state)

        self.assertEqual(np.sum(np.array(state.bag)), Azul.ColorNumber * Azul.TileNumber - Azul.BinNumber * Azul.BinSize)

    def test_is_end_of_game(self):
        azul = Azul()
        state = azul.get_init_state()

        self.assertFalse(azul.is_game_end(state))

        state.players[0].set_wall_row(4, [Color.Yellow, Color.Red, Color.Black, Color.White, Color.Empty])
        self.assertFalse(azul.is_game_end(state))

        state.players[0].set_wall_col(0, [Color.Blue, Color.White, Color.Black, Color.Red, Color.Yellow])
        self.assertFalse(azul.is_game_end(state))

        state.players[1].set_wall_row(4, [Color.Yellow, Color.Red, Color.Black, Color.White, Color.Blue])
        self.assertTrue(azul.is_game_end(state))

    def test_score_game(self):
        azul = Azul()
        state = azul.get_init_state()
        # Fill the main diagonal (all blue), the first row and the first column.
        for i in range(Azul.WallSize):
            state.players[0].set_wall(i, i, Azul.get_wall_slot_color(i, i))
            state.players[0].set_wall(i, 0, Azul.get_wall_slot_color(i, 0))
            state.players[0].set_wall(0, i, Azul.get_wall_slot_color(0, i))

        state = azul.score_game(state)
        self.assertEqual(state.players[0].score, Azul.ScorePerRow + Azul.ScorePerColumn + Azul.ScorePerColor)

    def test_full_game(self):
        # Test a full recorded game.
        azul = Azul()
        state = azul.get_init_state()

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
        state.nextPlayer = firstPlayer
        for iRound, (tiles, moves, scores) in enumerate(zip(tilesPerRound, movesPerRound, scoresPerRound)):
            state = azul.deal_round(state, tiles)

            for move in moves:
                state = azul.apply_move_without_scoring(state, move).state

            self.assertTrue(azul.is_round_end(state))
            state = azul.score_round(state)

            self.assertEqual([p.score for p in state.players], scores)

        state = azul.score_game(state)
        self.assertEqual([p.score for p in state.players], finalScores)

    def test_hash(self):
        import copy
        azul = Azul()

        state1 = azul.get_init_state()
        bins = state1.bins
        bins[1] = [0, 2, 3, 4, 5, 6]
        state1.bins = bins
        state1.players[0].set_wall(1, 1, Azul.get_wall_slot_color(1, 1))

        state2 = state1.copy()

        self.assertEqual(state1, state2)
        self.assertEqual(hash(state1), hash(state2))

        state2.set_bin(1, Color.Blue, 5)

        self.assertNotEqual(state1, state2)
        self.assertNotEqual(hash(state1), hash(state2))

        state2 = state1.copy()
        state2.players[1].score = 1

        self.assertNotEqual(state1, state2)
        self.assertNotEqual(hash(state1), hash(state2))

        state2 = state1.copy()
        state2.players[1].set_queue(0, Color.Blue, 1)

        self.assertNotEqual(state1, state2)
        self.assertNotEqual(hash(state1), hash(state2))

        # Trying using as keys in a dict. This shouldn't throw.
        d1 = {state1: 'a1', state2: 'a2'}
        d2 = copy.copy(d1)

        d1[state1] = 'a1'
        self.assertEqual(d1, d2)

        d1[state2] = 'a3'
        self.assertNotEqual(d1, d2)

    def test_playout(self):
        azul = Azul()
        state = azul.get_init_state()

        self.assertFalse(azul.is_game_end(state))

        state = azul.playout(state)

        self.assertTrue(azul.is_game_end(state))

    def test_move_to_and_from_int(self):
        for sourceBin in range(Azul.BinNumber + 1):
            for targetQueue in range(Azul.WallSize + 1):
                for color in [Color.Blue, Color.Yellow, Color.Red, Color.Black, Color.White]:

                    move = Move(sourceBin, color, targetQueue)
                    value = move.to_int()
                    move_after = Move.from_int(value)

                    self.assertGreaterEqual(value, 0)
                    self.assertLess(value, Move.PossibleMoveNumber)
                    self.assertEqual(move.sourceBin, move_after.sourceBin)
                    self.assertEqual(move.color, move_after.color)
                    self.assertEqual(move.targetQueue, move_after.targetQueue)





