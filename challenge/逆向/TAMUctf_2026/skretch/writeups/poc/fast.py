import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

data = open('eqs.txt').readlines()
n = len(data)
A = np.empty(n, dtype=np.float64)
B = np.empty(n, dtype=np.float64)
C = np.empty(n, dtype=np.float64)
R = np.empty(n, dtype=np.float64)

for i, line in enumerate(data):
    a, b, c, r = map(int, line.split())
    A[i], B[i], C[i], R[i] = a, b, c, r

# eq[i]: A[i]*x[i-1] + B[i]*x[i] + C[i]*x[(i+1)%n] = R[i]
# Build sparse cyclic tridiagonal matrix
row = np.concatenate([np.arange(n), np.arange(n), np.arange(n)])
col = np.concatenate([np.arange(n), (np.arange(n) - 1) % n, (np.arange(n) + 1) % n])
val = np.concatenate([B, A, C])

M = sparse.csr_matrix((val, (row, col)), shape=(n, n))
x = spsolve(M, R)
sol = np.rint(x).astype(np.uint8)
for i in range(n):
    sol[i] = (int(sol[i]) - i - 1) % 256
open('solve.png', 'wb').write(bytes(sol))

