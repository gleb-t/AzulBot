import time

from azulbot.azulpy import Azul as AzulPy
from azulbot.azulsim import Azul as AzulCpp


repeats = 10000
print("Timing enumerate_moves.")

azul = AzulPy()
timeBefore = time.time()
for _ in range(repeats):
    s = azul.enumerate_moves()
timeAfter = time.time()

print(f"Python finished in {timeAfter - timeBefore:.3f} s.")


azul = AzulCpp()
state = azul.get_init_state()
timeBefore = time.time()
for _ in range(repeats):
    s = azul.enumerate_moves(state)
timeAfter = time.time()

print(f"C++ finished in {timeAfter - timeBefore:.3f} s.")
# ---------------------------------
print("Timing apply_move")

azul = AzulPy()
azul.deal_round()
move = azul.enumerate_moves()[0]
timeBefore = time.time()
for _ in range(repeats):
    s = azul.apply_move(move)
timeAfter = time.time()

print(f"Python finished in {timeAfter - timeBefore:.3f} s.")

azul = AzulCpp()
state = azul.get_init_state()
state = azul.deal_round(state)
move = azul.enumerate_moves(state)[0]
timeBefore = time.time()
for _ in range(repeats):
    s = azul.apply_move(state, move)
timeAfter = time.time()

print(f"C++ finished in {timeAfter - timeBefore:.3f} s.")

# ---------------------------------
print("Timing playout")

repeats = 1000
azul = AzulPy()
timeBefore = time.time()
for _ in range(repeats):
    a = azul.copy()
    s = a.playout()
timeAfter = time.time()

print(f"Python finished in {timeAfter - timeBefore:.3f} s.")

azul = AzulCpp()
state = azul.get_init_state()
timeBefore = time.time()
for _ in range(repeats):
    s = azul.playout(state)
timeAfter = time.time()

print(f"C++ finished in {timeAfter - timeBefore:.3f} s.")
