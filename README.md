# ZeroADC

**Zero-ADC analog front-end with CDM fusion for batteryless event-driven nodes.**

ZeroADC replaces the traditional ADC bottleneck in embedded sensing with an analog Layer-0 gating stage fused to a Charge Domain Modulator (CDM). The result is a batteryless, event-driven node that can operate on harvested energy with no digital sampling overhead until an event actually occurs.

Validated across three orthogonal platforms: simulation, Renode M33 emulation, and physical Arduino UNO.

---

## Why This Exists

Every batteryless sensor node today still carries an ADC. That ADC:
- Draws continuous power during sampling
- Creates a hard lower bound on energy per sample
- Forces the digital domain to process noise it never needed to see

ZeroADC moves the decision **into the analog domain** before the signal ever reaches a digital converter. The CDM fusion stage encodes the gating decision as charge packets, not samples — which means the node can sleep until an event actually occurs, then wake, capture, and transmit in a single burst.

---

## Key Results

| Metric | Value |
|---|---|
| **Platforms validated** | Simulation + Renode M33 + Arduino UNO |
| **Architecture** | Analog Layer-0 gating + CDM fusion |
| **Node type** | Batteryless, event-driven |
| **Digital sampling** | Zero until event trigger |
| **Validation dossier** | `VALIDATION_DOSSIER.md` |

---

## How It Works

```
Sensor → Analog Layer-0 Gate → CDM Fusion → Event Trigger → Digital Capture
                              ↑
                         No ADC needed here
```

1. **Analog Layer-0 Gate** — continuous-time analog comparator network gates the signal path before any sampling occurs
2. **CDM Fusion** — Charge Domain Modulator encodes the gating decision as charge-domain pulses, not voltage samples
3. **Event Trigger** — digital wakeup occurs only when the analog gate fires
4. **Digital Capture** — ADC engages only for the event window, not the entire signal

---

## Repository Structure

```
ZeroADC/
├── README.md                       # This file
├── VALIDATION_DOSSIER.md           # Full validation report across all 3 platforms
├── cdm_engine.py                   # CDM fusion engine
├── combined_engine.py              # Combined analog + CDM pipeline
├── generate_combined_paper.py      # Paper generation script
├── run_combined_tests.py           # Cross-platform test runner
├── make_combined_figures.py        # Figure generation
├── combined_results.json           # Quantitative results
├── results.json                    # Test results
├── arduino/                        # Arduino UNO deployment
│   ├── cdm_hw_test/
│   ├── HW_VALIDATION_REPORT.md
│   ├── hw_validation.json
│   ├── run_hw_tests.py
│   └── serial_log.txt
├── renode/                         # Renode M33 emulation
│   ├── app_cdm.c
│   ├── app.ld
│   ├── app_cdm.elf
│   ├── gen_golden.py
│   └── run.re
└── figs/                           # Generated figures
    ├── fc1_headline.png
    ├── fc2_eventrate.png
    ├── fc3_brownout.png
    ├── fc4_proctime.png
    ├── fc5_statecost.png
    ├── fc6_architecture.png
    ├── fig_avalanche.png
    └── ...
```

---

## Validation

See `VALIDATION_DOSSIER.md` for the full dossier. Summary:

- **Simulation:** behavioral model verified in Python
- **Renode M33:** full system emulation with event-driven wakeup
- **Arduino UNO:** physical hardware validation on real silicon

All three platforms produced consistent event-detection behavior with no false negatives in the validated test set.

---

## Requirements

- Python 3.10+
- Renode (for M33 emulation)
- Arduino CLI + UNO board (for hardware validation)
- MATLAB/Octave (optional, for figure generation)

---

## Status

Research-grade prototype. Not yet production-hardened. Validated as proof-of-concept across simulation, emulation, and hardware.

---

## License

MIT
