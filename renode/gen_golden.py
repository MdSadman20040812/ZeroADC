import numpy as np, sys
sys.path.insert(0, r'D:\Outputs\PaperFix')
from cdm_engine import cdm_rederive, mxr64
rows = []
with open(r'D:\Outputs\PaperFix\data\household_power_consumption.txt') as f:
    next(f)
    for line in f:
        p = line.strip().split(';')
        if len(p) < 3 or p[2] == '?':
            continue
        rows.append(float(p[2]))
        if len(rows) > 50000:
            break
sig = np.array(rows)
s = (sig - sig.min()) / np.ptp(sig)
q = (s * 4095).astype(np.int16)
win = q[1000:1064]
COEFFS = np.array([8, 24, 40, 56, 56, 40, 24, 8], dtype=np.int64)
y = int(np.dot(win[-8:][::-1].astype(np.int64), COEFFS) >> 8)
tok, _ = mxr64(int(win[-1]), int(win[-2]), 0, 42)
g, cyc = cdm_rederive(int(win[-1]), int(win[-2]), 0, 42)
print('WIN:', ','.join(str(int(v)) for v in win))
print('GOLDEN_FIR:', y)
print('GOLDEN_TOK_LO:', tok & 0xFFFFFFFF)
print('GOLDEN_G:', g, 'CYC:', cyc)
