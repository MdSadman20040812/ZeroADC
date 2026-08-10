"""Figures for the combined Zero-ADC + CDM paper."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

R = json.load(open(r'D:\Outputs\PaperFix\combined_results.json'))
FIG = r'D:\Outputs\PaperFix\figs'
plt.rcParams.update({'font.size': 11, 'axes.grid': True, 'grid.alpha': 0.3,
                     'figure.facecolor': 'white'})
C = dict(A='#E4572E', B='#F6AE2D', Cc='#7B2D8E', D='#2E86AB', ok='#3CA370', gry='#666666')
NAMES = {'A': 'A: Polling + Checkpoint', 'B': 'B: Polling + CDM',
         'C': 'C: Zero-ADC + Checkpoint', 'D': 'D: Zero-ADC + CDM (combined)'}
COLS = {'A': C['A'], 'B': C['B'], 'C': C['Cc'], 'D': C['D']}

# ---- Fig C1: headline energy bars (log) --------------------------------------
t9 = R['T9_headline']['archs']
fig, ax = plt.subplots(figsize=(8.5, 5))
vals = [t9[a]['E_total_J'] for a in 'ABCD']
bars = ax.bar(range(4), vals, color=[COLS[a] for a in 'ABCD'], edgecolor='k')
for i, (b, a) in enumerate(zip(bars, 'ABCD')):
    ax.annotate(f'{b.get_height():.3g} J', (i, b.get_height() * 1.15), ha='center',
                fontweight='bold', fontsize=10)
ax.set_yscale('log'); ax.set_ylim(1e-3, 3e3)
ax.set_xticks(range(4)); ax.set_xticklabels([NAMES[a] for a in 'ABCD'], fontsize=9)
ax.set_ylabel('Energy per 24 h (J, log scale)')
ax.set_title(f"24-hour batteryless scenario (253 events, 4,753 brownouts/hr=150/s-mode):\n"
             f"combined node saves {R['T9_headline']['savings_D_vs_A_pct']}% vs classical",
             fontweight='bold', fontsize=11)
fig.tight_layout(); fig.savefig(FIG + r'\fc1_headline.png', dpi=160); plt.close(fig)

# ---- Fig C2: event-rate sweep -------------------------------------------------
t1 = R['T1_event_rate_sweep']
rates = sorted(float(k) for k in t1)
fig, ax = plt.subplots(figsize=(8.5, 5))
for a in 'ABCD':
    ax.loglog(rates, [t1[str(r) if str(r) in t1 else str(int(r))][a] for r in rates],
              'o-', color=COLS[a], lw=2, label=NAMES[a])
ax.set_xlabel('Physical events per hour (log)'); ax.set_ylabel('Energy per 24 h (J, log)')
ax.set_title('Energy vs. event rate — the idle-power wall dominates polling architectures',
             fontweight='bold')
ax.legend(fontsize=9); fig.tight_layout(); fig.savefig(FIG + r'\fc2_eventrate.png', dpi=160); plt.close(fig)

# ---- Fig C3: brownout density, heavy mode --------------------------------------
t2 = R['T2_brownout_density']
dens = sorted(int(k) for k in t2)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.6))
a1.semilogx([max(d, 1) for d in dens], [t2[str(d)]['C']['interrupted'] for d in dens],
            's-', color=C['Cc'], lw=2, label='C: Zero-ADC + Flash ckpt')
a1.semilogx([max(d, 1) for d in dens], [t2[str(d)]['D']['interrupted'] for d in dens],
            'o-', color=C['D'], lw=2, label='D: combined (CDM)')
a1.set_xlabel('Brownouts per hour'); a1.set_ylabel('Interrupted inferences / day')
a1.set_title('Mid-inference interruptions', fontweight='bold'); a1.legend(fontsize=9)
a2.semilogx([max(d, 1) for d in dens], [max(t2[str(d)]['C']['writes'], 1) for d in dens],
            's-', color=C['Cc'], lw=2, label='C: Flash bytes written/day')
a2.semilogx([max(d, 1) for d in dens], [max(t2[str(d)]['D']['writes'], 1) for d in dens],
            'o-', color=C['D'], lw=2, label='D: bytes written/day')
a2.set_yscale('log'); a2.set_xlabel('Brownouts per hour'); a2.set_ylabel('NVM writes (bytes/day)')
a2.set_title('NVM wear burden', fontweight='bold'); a2.legend(fontsize=9)
fig.suptitle('Heavy-inference mode (50 ms per event) — both survive; only one wears out', fontweight='bold')
fig.tight_layout(); fig.savefig(FIG + r'\fc3_brownout.png', dpi=160); plt.close(fig)

# ---- Fig C4: processing-time sweep ---------------------------------------------
t10 = R['T10_proc_time_sweep']
tp = sorted(float(k) for k in t10)
interr = [t10[str(int(x)) if str(int(x)) in t10 else str(x)]['C_interrupted'] for x in tp]
writes = [max(t10[str(int(x)) if str(int(x)) in t10 else str(x)]['C_writes'], 1) for x in tp]
fig, ax = plt.subplots(figsize=(8.5, 5))
ax.semilogx(tp, interr, 'o-', color=C['A'], lw=2.5, label='Interrupted inferences/day (C & D alike)')
ax.set_xlabel('On-trigger processing time (ms)'); ax.set_ylabel('Interruptions / day', color=C['A'])
ax2 = ax.twinx()
ax2.semilogx(tp, writes, 's--', color=C['Cc'], lw=2.5, label='C: Flash writes/day (D = 0 always)')
ax2.set_ylabel('Flash bytes written / day', color=C['Cc']); ax2.set_yscale('log')
ax.set_title('The heavier the on-trigger inference, the more checkpointing costs — CDM stays free',
             fontweight='bold')
fig.tight_layout(); fig.savefig(FIG + r'\fc4_proctime.png', dpi=160); plt.close(fig)

# ---- Fig C5: per-interruption cost vs inference state size ----------------------
t11 = R['T11_inference_state_size']['sweep']
Bs = sorted(int(k) for k in t11)
fig, ax = plt.subplots(figsize=(8.5, 5))
x = np.arange(len(Bs)); w = 0.36
ck = [t11[str(b)]['ckpt_energy_uJ'] for b in Bs]
cd = [t11[str(b)]['cdm_energy_uJ'] for b in Bs]
ax.bar(x - w/2, ck, w, color=C['Cc'], edgecolor='k', label='Flash checkpoint')
ax.bar(x + w/2, cd, w, color=C['D'], edgecolor='k', label='CDM re-derivation')
for i, b in enumerate(Bs):
    ax.annotate(f"{t11[str(b)]['energy_ratio']:.0f}×", (i, ck[i] * 1.2), ha='center',
                fontweight='bold', color=C['ok'])
ax.set_yscale('log')
ax.set_xticks(x); ax.set_xticklabels([f'{b} B' if b < 1024 else f'{b//1024} KB' for b in Bs])
ax.set_xlabel('Volatile inference state to save'); ax.set_ylabel('Energy per interruption (µJ, log)')
ax.set_title('Per mid-inference brownout: CDM is 47×–4,855× cheaper (and ~711× faster resume)',
             fontweight='bold')
ax.legend(); fig.tight_layout(); fig.savefig(FIG + r'\fc5_statecost.png', dpi=160); plt.close(fig)

# ---- Fig C6: combined architecture block diagram --------------------------------
fig, ax = plt.subplots(figsize=(11, 6)); ax.axis('off')
ax.set_xlim(0, 11); ax.set_ylim(0, 6)
def box(x, y, w, h, label, fc, fs=9):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.08',
                                fc=fc, ec='k', lw=1.4))
    ax.text(x + w/2, y + h/2, label, ha='center', va='center', fontsize=fs,
            fontweight='bold', wrap=True)
def arrow(x1, y1, x2, y2, label='', color='k'):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>',
                                 mutation_scale=16, color=color, lw=1.6))
    if label:
        ax.text((x1+x2)/2, (y1+y2)/2 + 0.18, label, fontsize=8, ha='center', color=color)
box(0.2, 2.6, 1.6, 1.0, 'Analog\nsensor', '#D9E8F5')
box(2.3, 3.6, 1.9, 1.0, 'Bandpass f₀\n(physical Fourier)', '#B7D7A8')
box(2.3, 1.4, 1.9, 1.0, 'Analog delay line\nτ = 173 µs', '#B7D7A8')
box(4.7, 3.6, 1.9, 1.0, 'Envelope +\nSchmitt trigger', '#B7D7A8')
box(4.7, 1.4, 1.9, 1.0, 'ADC frame\nx(t−τ) window', '#FCE5CD')
box(7.1, 3.6, 1.7, 1.0, 'GPIO/EXTI\nwake (1-bit step)', '#F6AE2D')
box(7.1, 1.4, 1.7, 1.0, 'CDM re-derive\nMXR→Collatz→g', '#9FC5E8')
box(9.2, 2.5, 1.7, 1.2, 'FIR / TinyML\ninference\n(stateless resume)', '#2E86AB', fs=9)
ax.text(9.2 + 0.85, 2.35, 'output event', ha='center', fontsize=8, style='italic')
arrow(1.8, 3.1, 2.3, 4.1); arrow(1.8, 3.1, 2.3, 1.9)
arrow(4.2, 4.1, 4.7, 4.1); arrow(4.2, 1.9, 4.7, 1.9)
arrow(6.6, 4.1, 7.1, 4.1); arrow(6.6, 1.9, 7.1, 1.9, 'Markov window', '#7B2D8E')
arrow(8.8, 4.1, 9.6, 3.7); arrow(8.8, 1.9, 9.6, 3.1, '225 cycles', '#2E86AB')
ax.text(5.5, 5.4, 'Analog Layer-0 (Zero-ADC): kills idle power', fontsize=11,
        fontweight='bold', color='#3CA370', ha='center')
ax.text(5.5, 0.5, 'CDM (Topological Determinism): kills checkpoint energy, wear, death-spiral',
        fontsize=11, fontweight='bold', color='#2E86AB', ha='center')
ax.set_title('Combined architecture: physical event gating + stateless mathematical recovery',
             fontsize=12, fontweight='bold')
fig.tight_layout(); fig.savefig(FIG + r'\fc6_architecture.png', dpi=160); plt.close(fig)

print('combined figures done')
