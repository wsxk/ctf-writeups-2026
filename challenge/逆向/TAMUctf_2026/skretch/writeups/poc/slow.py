
data = open('eqs.txt').readlines()

eqs = []
for line in data:
    a, b, c, res = map(int, line.split())
    eqs.append((a, b, c, res))

n = len(eqs)

# from z3 import *
# # from cvc5.pythonic import *
# s = Solver()
# x = [Int(f'x_{i}') for i in range(n)]
# for i, (a, b, c, res) in enumerate(eqs):
#     s.add(a * x[i - 1] + b * x[i] + c * x[(i + 1) % n] == res)

#     # all bytes
#     s.add(x[i] >= 0, x[i] <= 255)

# print(s.check())
# model = s.model()
# solution = [model[x[i]].as_long() for i in range(n)]
# print(solution)

# below does not work, too much memory required :)
# solve linear system
import numpy as np
M = np.zeros((n, n))
y = np.zeros(n)

for i, (a, b, c, res) in enumerate(eqs):
    if i == 0:
        M[i, i] = b
        M[i, i + 1] = c
    elif i == n - 1:
        M[i, i - 1] = a
        M[i, i] = b
    else:
        M[i, i - 1] = a
        M[i, i] = b
        M[i, i + 1] = c
    y[i] = res

x = np.linalg.solve(M, y)
print(x)