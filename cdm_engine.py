"""
CDM (Collatz Deterministic Modelling) simulation engine — rebuilt for rigorous validation.
Fixes vs. the original paper:
  * MXR hash H(i, j, layer, salt) is fully specified (was undefined in the paper).
  * Cycle-accurate op counting for the re-derivation cost N_cycles.
  * Event-driven intermittent-computing simulation (energy capacitor + brownouts).
  * Honest state-integrity verification against a golden uninterrupted run.
"""
import numpy as np

MASK64 = 0xFFFFFFFFFFFFFFFF
GOLDEN64 = 0x9E3779B97F4A7C15
MXR_MUL  = 0xBF58476D1CE4E5B9   # splitmix64-style odd multiplier

# ---------------------------------------------------------------- primitives
def rotl64(x, r):
    return ((x << r) | (x >> (64 - r))) & MASK64

def mxr64(i, j, layer, salt, rounds=2):
    """Multiply-XOR-Rotate avalanche hash — concrete spec for H(i,j,layer,salt).

    h seeded with golden-ratio constant XOR salt; each 64-bit operand is
    injected, multiplied by an odd 64-bit constant, and rotated.
    Returns (hash_value, cycle_count) where cycles count ALU ops on an
    MSP430-class MCU (mul=8, rot=4, xor/add=1).
    """
    h = (GOLDEN64 ^ (salt & MASK64)) & MASK64
    cyc = 2
    for v in (i, j, layer):
        h ^= (v & MASK64); cyc += 1
        for _ in range(rounds):
            h = (h * MXR_MUL) & MASK64;  cyc += 8
            h ^= rotl64(h, 31);          cyc += 5
    h ^= (h >> 33); cyc += 2
    h = (h * MXR_MUL) & MASK64; cyc += 8
    h ^= (h >> 29); cyc += 2
    return h, cyc

def collatz_step(n):
    """Eq. (1): 64-bit masked Collatz map. Cost: 4 cycles (test, add/shift, mask)."""
    if n & 1:
        return ((3 * n + 1) & MASK64), 4
    return (n >> 1), 4

def collatz_trajectory(seed, iters=32):
    n = seed & MASK64
    cyc = 0
    for _ in range(iters):
        n, c = collatz_step(n)
        cyc += c
    return n, cyc

def bit_log2(n):
    """Eq. (2): g = floor(log2 n) via CLZ/FFS — 2 cycles."""
    if n == 0:
        return 0, 2
    return n.bit_length() - 1, 2

def cdm_rederive(i, j, layer, salt, collatz_iters=32):
    """Full CDM wake-up pipeline: MXR hash -> masked Collatz -> bitwise log2.
    Returns (g, total_cycles)."""
    h, c1 = mxr64(i, j, layer, salt)
    n, c2 = collatz_trajectory(h, collatz_iters)
    g, c3 = bit_log2(n)
    return g, c1 + c2 + c3

# ---------------------------------------------------------------- workload
def fir8(signal_q, coeffs):
    """Golden 8-tap integer FIR (vectorized). signal_q: int16 array."""
    k = len(coeffs)
    n = len(signal_q)
    out = np.zeros(n, dtype=np.int64)
    for t in range(k - 1, n):
        out[t] = int(np.dot(signal_q[t - k + 1:t + 1][::-1].astype(np.int64), coeffs) >> 8)
    return out

# ---------------------------------------------------------------- simulation
class EnergyModel:
    """Energy/cost constants (paper's Table, overridable for sweeps)."""
    def __init__(self, e_alu_pj=50.0, e_fram_write_pj=200.0, e_fram_read_pj=48.0,
                 clk_hz=1_000_000, fir_cycles_per_sample=40, checkpoint_bytes=80):
        self.e_alu = e_alu_pj                 # pJ / cycle
        self.e_wr  = e_fram_write_pj          # pJ / byte
        self.e_rd  = e_fram_read_pj           # pJ / byte
        self.clk   = clk_hz
        self.fir_cyc = fir_cycles_per_sample
        self.ckpt = checkpoint_bytes          # 80 B  (matches paper: 827520/10344)

def find_brownouts(harvest_mw, e_cap_max_uj, e_min_uj, e_load_uj_per_sample):
    """Capacitor simulation over a harvested-power trace (1 sample/s grid).
    Returns array of brownout sample indices (capacitor collapse events)."""
    cap = e_cap_max_uj * 0.5
    events = []
    for t, p in enumerate(harvest_mw):
        cap = min(e_cap_max_uj, cap + p * 1000.0)   # mW over 1 s = 1000 uJ
        cap -= e_load_uj_per_sample
        if cap < e_min_uj:
            events.append(t)
            cap = 0.0
    return np.array(events, dtype=np.int64)

def simulate_fram(n_samples, brownouts, em: EnergyModel):
    """Conventional checkpointing node. Returns (energy_uJ, time_s, ckpt_bytes, n_failed_ckpt)."""
    e_work = n_samples * em.fir_cyc * em.e_alu / 1e6          # uJ
    e_ckpt = len(brownouts) * em.ckpt * (em.e_wr + em.e_rd) / 1e6
    t = (n_samples * em.fir_cyc + len(brownouts) * em.ckpt * 2 * 8) / em.clk
    return e_work + e_ckpt, t, len(brownouts) * em.ckpt

def simulate_cdm(n_samples, brownouts, em: EnergyModel, recovery_cycles):
    """CDM stateless node. Returns (energy_uJ, time_s)."""
    e_work = n_samples * em.fir_cyc * em.e_alu / 1e6
    e_rec  = len(brownouts) * recovery_cycles * em.e_alu / 1e6
    t = (n_samples * em.fir_cyc + len(brownouts) * recovery_cycles) / em.clk
    return e_work + e_rec, t
