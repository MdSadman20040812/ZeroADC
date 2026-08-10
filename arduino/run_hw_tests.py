"""Upload + capture + verify CDM hardware tests on the Arduino UNO (COM9).
Compares on-device results against Python golden, writes hw_validation.json."""
import subprocess, sys, time, json
import serial  # pyserial
sys.path.insert(0, r'D:\Outputs\PaperFix')
from cdm_engine import mxr64, collatz_trajectory, bit_log2
import numpy as np

PORT = 'COM9'
SKETCH = r'D:\Outputs\PaperFix\arduino\cdm_hw_test'

# ---- Python golden for the 5 windows ----
WIN = [
  [1558,992,1276,1378,1436,933,1314,1255],
  [2425,1558,992,1276,1378,1436,933,1314],
  [1266,1917,2424,2095,2197,2425,1558,992],
  [2388,2573,2179,1376,1135,1508,1524,1272],
  [2547,2564,2561,2199,2388,2573,2179,1376]]
COEFFS = np.array([8,24,40,56,56,40,24,8], dtype=np.int64)
golden = []
for w in WIN:
    tok, _ = mxr64(w[7] & 0xFFFF, w[6] & 0xFFFF, 0, 42)
    n, _ = collatz_trajectory(tok, 32)
    g, _ = bit_log2(n)
    fir = int(np.dot(np.array(w[::-1], dtype=np.int64), COEFFS) >> 8)
    golden.append(dict(tok_lo=tok & 0xFFFFFFFF, n_lo=n & 0xFFFFFFFF, g=g, fir=fir))
tok4 = golden[4]

print('uploading...')
r = subprocess.run([r'D:\arduino-cli.exe', 'upload', '-p', PORT,
                    '--fqbn', 'arduino:avr:uno', SKETCH],
                   capture_output=True, text=True, timeout=180)
print(r.stdout.strip() or r.stderr.strip())

print('capturing serial...')
ser = serial.Serial(PORT, 115200, timeout=3)
time.sleep(1.0)              # board resets on open
# phase 1: drain whatever the previous run prints (up to its TESTS_DONE)
t0 = time.time()
while time.time() - t0 < 15:
    ln = ser.readline().decode(errors='replace').strip()
    if ln == 'TESTS_DONE':
        break
ser.write(b'R')              # fresh run
lines, t0 = [], time.time()
while time.time() - t0 < 120:
    ln = ser.readline().decode(errors='replace').strip()
    if ln:
        lines.append(ln)
        if ln == 'TESTS_DONE':
            break
ser.close()
open(r'D:\Outputs\PaperFix\arduino\serial_log.txt', 'w').write('\n'.join(lines))
print(f'captured {len(lines)} lines')

# ---- parse & verify ----
import re
kv = {}
t4_tokens, t4_gs = [], []
for ln in lines:
    m = re.match(r'T4\.boot=(\d+)\.token_lo=(\d+)$', ln)
    if m:
        t4_tokens.append(int(m.group(2))); continue
    m = re.match(r'T4\.boot=(\d+)\.g=(\d+)$', ln)
    if m:
        t4_gs.append(int(m.group(2))); continue
    if '=' in ln:
        k, v = ln.split('=', 1)
        kv[k] = v

res = {'lines_captured': len(lines)}
ok, fails = 0, []
for i in range(5):
    for field in ('tok_lo', 'n_lo', 'g', 'fir'):
        got = kv.get(f'T1.win{i}.{field}')
        want = golden[i][field]
        if got is not None and int(float(got)) == want:
            ok += 1
        else:
            fails.append(f'win{i}.{field}: got {got} want {want}')
res['T1_bit_exact'] = f'{ok}/20 fields match Python golden'
res['T1_failures'] = fails
res['T2_cdm_recovery_cycles'] = int(kv.get('T2.cdm_recovery_cycles', -1))
res['T2_cdm_recovery_us'] = float(kv.get('T2.cdm_recovery_us', -1))
res['T2_fir8_cycles'] = int(kv.get('T2.fir8_cycles', -1))
res['T2_ckpt_slower_than_cdm_x'] = float(kv.get('T2.ckpt_slower_than_cdm_x', -1))
res['T3_deterministic'] = kv.get('T3.deterministic')
res['T4_boots'] = len(t4_tokens)
res['T4_all_tokens_identical'] = len(set(t4_tokens)) == 1 and len(t4_tokens) > 40
res['T4_token_matches_golden'] = (set(t4_tokens) == {tok4['n_lo']}) if t4_tokens else False
res['T4_all_g_identical'] = len(set(t4_gs)) == 1 and len(t4_gs) > 40
res['T4_g_matches_golden'] = (set(t4_gs) == {tok4['g']}) if t4_gs else False
res['tests_done_seen'] = 'TESTS_DONE' in lines

json.dump(res, open(r'D:\Outputs\PaperFix\arduino\hw_validation.json', 'w'), indent=2)
print(json.dumps(res, indent=2))
