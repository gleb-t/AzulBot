import time

from azulpy.azul import Azul
from azulsim import AzulState


azul = Azul()
timeBefore = time.time()
for _ in range(1000):
    s = azul.enumerate_moves()
timeAfter = time.time()

print(f"Python finished in {timeAfter - timeBefore:.2f} s.")


azul = AzulState()
timeBefore = time.time()
for _ in range(1000):
    s = azul.enumerate_moves()
timeAfter = time.time()

print(f"C++ finished in {timeAfter - timeBefore:.2f} s.")