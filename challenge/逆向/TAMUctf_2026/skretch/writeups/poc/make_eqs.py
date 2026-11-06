import random

data = open('../flag.png', 'rb').read()
data = list(data)
for i in range(len(data)):
    data[i] = (data[i] + i + 1) % 256
n = len(data)

A = [random.randint(1, 255) for _ in range(n)]
B = [random.randint(1, 255) for _ in range(n)]
C = [random.randint(1, 255) for _ in range(n)]

eqs = []
for i in range(n):
    a, b, c = A[i], B[i], C[i]
    res = a * data[i-1] + b * data[i] + c * data[(i+1) % n]
    eqs.append((a, b, c, res))

with open('eqs.txt', 'w') as f:
    for a, b, c, res in eqs:
        f.write(f'{a} {b} {c} {res}\n')
