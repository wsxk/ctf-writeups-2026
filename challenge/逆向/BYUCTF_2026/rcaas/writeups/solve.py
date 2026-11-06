from z3 import *

# Define unknown variable
vec = [BitVec(f'v{i}', 8) for i in range(46)]

# Create solver
solver = Solver()

### Add conditions here
for i, v in enumerate("byuctf{"):
    solver.add(vec[i] == ord(v))
for i in [13, 21, 24, 26, 29, 31, 36, 37, 39]:
    solver.add(vec[i] == ord('3'))
solver.add(vec[45] == ord('}'))

solver.add(vec[1] * vec[34] % 256 == 41)
solver.add(vec[4] * vec[40] % 256 == 80)
solver.add(vec[6] * vec[12] % 256 == 145)
solver.add(vec[7] * vec[36] % 256 == 233)
solver.add(vec[8] * vec[26] % 256 == 41)
solver.add(vec[9] * vec[45] % 256 == 170)
solver.add(vec[10] * vec[24] % 256 == 130)
solver.add(vec[11] * vec[38] % 256 == 210)
solver.add(vec[12] * vec[27] % 256 == 22)
solver.add(vec[13] * vec[42] % 256 == 28)
solver.add(vec[14] * vec[0] % 256 == 6)
solver.add(vec[15] * vec[25] % 256 == 202)
solver.add(vec[16] * vec[32] % 256 == 138)
solver.add(vec[17] * vec[41] % 256 == 76)
solver.add(vec[18] * vec[22] % 256 == 210)
solver.add(vec[19] * vec[6] % 256 == 165)
solver.add(vec[20] * vec[43] % 256 == 96)
solver.add(vec[22] * vec[1] % 256 == 231)
solver.add(vec[23] * vec[39] % 256 == 182)
solver.add(vec[26] * vec[15] % 256 == 237)
solver.add(vec[28] * vec[39] % 256 == 233)
solver.add(vec[30] * vec[37] % 256 == 237)
solver.add(vec[33] * vec[4] % 256 == 172)
solver.add(vec[35] * vec[17] % 256 == 88)
solver.add(vec[37] * vec[11] % 256 == 195)
solver.add(vec[38] * vec[16] % 256 == 22)
solver.add(vec[41] * vec[22] % 256 == 65)
solver.add(vec[43] * vec[11] % 256 == 48)
solver.add(vec[44] * vec[2] % 256 == 240)
solver.add(vec[40] * vec[8] % 256 == 236)

solver.add(vec[35] >= 0x60)
solver.add(vec[33] >= 0x60)


# Solve
if solver.check() == sat:
    model = solver.model()
    chars = [chr(model[v].as_long()) for v in vec]
    print(''.join(chars))
else:
    print("No solution exists.")
