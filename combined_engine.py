"""Combined Zero-ADC + CDM simulation kernel.

Four architectures, identical event stream + harvest trace + brownouts:
  A. Continuous polling + FRAM checkpointing   (classical)
  B. Continuous polling + CDM stateless        (CDM only)
  C. Zero-ADC analog gating + checkpointing    (Layer-0 only)
  D. Zero-ADC analog gating + CDM stateless    (combined — proposed)

Energy model anchored to the Zero-ADC paper's STM32L476RG numbers and the CDM
paper's cycle-counted recovery (225 cycles). All constants explicit below.
"""
import numpy as np

# ---------------- MCU constants (STM32L476RG @ 80 MHz, Zero-ADC paper §IV) ----
CLK = 80e6
P_POLL = 8.4e-3          # W  continuous ADC+CPU polling (30.24 J/hr, Table I)
P_SLEEP = 1.1e-6         # W  STOP2 standby
P_ACTIVE = 24e-3         # W  active processing (datasheet-class, 100 uA/MHz @3V)
T_WAKEUP = 17.5e-6       # s  EXTI wake + ADC/DMA init
T_ACQ = 12.5e-6          # s  ADC frame acquisition setup
FIR_TAPS = 8
FIR_WINDOW = 1024        # samples per event frame
FIR_CYC_PER_SAMPLE = 40  # int MAC + loop overhead, Cortex-M4
T_FIR = FIR_WINDOW * FIR_CYC_PER_SAMPLE / CLK          # 512 us
E_EVENT = P_ACTIVE * (T_WAKEUP + T_ACQ + T_FIR)        # ~13.1 uJ per event

# ---------------- CDM / checkpoint constants --------------------------------
CDM_CYCLES = 225                              # measured, cdm_engine
E_CDM_RECOVERY = P_ACTIVE * CDM_CYCLES / CLK  # 67.5 nJ @80MHz
CKPT_BYTES = 80
E_FRAM_BYTE = 200e-12; E_FRAM_RD = 48e-12     # pJ/B
E_FLASH_BYTE = 40e-9                          # Flash-class write
E_CKPT_FRAM = CKPT_BYTES * (E_FRAM_BYTE + E_FRAM_RD)   # 19.8 nJ
E_CKPT_FLASH = CKPT_BYTES * E_FLASH_BYTE               # 3.2 uJ

# ---------------- event stream ----------------------------------------------
def make_event_stream(hours, events_per_hr, shock_frac, seed):
    """Returns (event_times_s, shock_times_s) over the simulation horizon."""
    rng = np.random.default_rng(seed)
    T = hours * 3600.0
    n_ev = rng.poisson(events_per_hr * hours)
    n_sh = rng.poisson(events_per_hr * hours * shock_frac)
    ev = np.sort(rng.uniform(0, T, n_ev))
    sh = np.sort(rng.uniform(0, T, n_sh))
    return ev, sh

def make_brownouts(hours, brownouts_per_hr, seed):
    rng = np.random.default_rng(seed + 777)
    n = rng.poisson(brownouts_per_hr * hours)
    return np.sort(rng.uniform(0, hours * 3600.0, n))

def in_any_window(t, centers, halfwidth):
    """True if t falls within +-halfwidth of any center (event active window)."""
    if len(centers) == 0:
        return False
    idx = np.searchsorted(centers, t)
    for j in (idx - 1, idx):
        if 0 <= j < len(centers) and abs(centers[j] - t) <= halfwidth:
            return True
    return False

# ---------------- one simulation run -----------------------------------------
def simulate(hours, events_per_hr, brownouts_per_hr, shock_frac=0.2, seed=0,
             nvm='flash', t_proc=None):
    """t_proc: active processing time per event (s). Default = FIR frame time.
    Heavy TinyML inference on trigger => t_proc ~ 10-200 ms, which is exactly
    the regime where mid-processing brownouts become probable."""
    if t_proc is None:
        t_proc = T_FIR
    e_event = P_ACTIVE * (T_WAKEUP + T_ACQ + t_proc)
    ev, sh = make_event_stream(hours, events_per_hr, shock_frac, seed)
    bo = make_brownouts(hours, brownouts_per_hr, seed)
    T = hours * 3600.0
    active_halfwin = (T_WAKEUP + T_ACQ + t_proc)
    e_ckpt = E_CKPT_FRAM if nvm == 'fram' else E_CKPT_FLASH
    out = {}
    nvm_writes = {}
    for arch in 'ABCD':
        zero_adc = arch in 'CD'
        cdm = arch in 'BD'
        P_mon = P_SLEEP if zero_adc else P_POLL
        E_mon = P_mon * T
        processed = len(ev) + (0 if zero_adc else len(sh))
        E_ev = processed * e_event
        # brownouts inside active windows interrupt processing
        bo_active = sum(1 for t in bo if in_any_window(t, ev, active_halfwin))
        if zero_adc:
            n_state_events = bo_active
        else:
            n_state_events = len(bo)
        if cdm:
            E_bo = n_state_events * E_CDM_RECOVERY
            writes = 0
        else:
            E_bo = n_state_events * e_ckpt
            writes = n_state_events * CKPT_BYTES
        out[arch] = dict(E_total_J=E_mon + E_ev + E_bo,
                         E_mon_J=E_mon, E_events_J=E_ev, E_brownout_J=E_bo,
                         events_detected=len(ev), shocks=processed - len(ev),
                         interrupted_events=bo_active if zero_adc else 0,
                         brownout_overheads=n_state_events)
        nvm_writes[arch] = writes
    for arch in 'ABCD':
        out[arch]['nvm_bytes_written'] = nvm_writes[arch]
    return out, dict(events=len(ev), shocks=len(sh), brownouts=len(bo))
