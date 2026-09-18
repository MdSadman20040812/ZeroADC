![ZeroADC](https://img.shields.io/badge/ZeroADC-Asynchronous%20Delta%20Compute-dc2626?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

**Asynchronous Delta Compute — event-driven inference for energy-constrained hardware.**

---

## 📊 Results

| Metric | Value |
|--------|-------|
| Energy reduction | 3.2× vs synchronous |
| Latency @ P99 | 8.4 m |
| Accuracy retention | 97.1% baseline |

![Architecture](figs/fc6_architecture.png)
*Figure 1: ZeroADC asynchronous pipeline architecture.*

![Headline](figs/fc1_headline.png)
*Figure 2: Headline energy-accuracy tradeoff.*

![Event rate](figs/fc2_eventrate.png)
*Figure 3: Event rate vs workload.*

![Brownout](figs/fc3_brownout.png)
*Figure 4: Brownout resilience characterization.*

![Processing time](figs/fc4_proctime.png)
*Figure 5: Per-event processing time distribution.*

![State cost](figs/fc5_statecost.png)
*Figure 6: Memory state transition cost.*

---

## 🏗️ Architecture

```mermaid
graph TB
    S[Sensor<br/>Event Stream] --> PF[Pre-Filter<br/>Delta Threshold]
    PF --> AD[Asynchronous<br/>Dispatcher]
    AD --> P[PE Array<br/>Spike-driven]
    P --> AG[Adder<br/>Tree]
    AG --> O[Output<br/>Reconstruction]
    R[(State<br/>Memory)] --> P
    R --> AG
```

---

## ✨ Features

- **Event-driven dispatch** — compute only on significant input changes
- **Delta thresholding** — configurable sparsity-accuracy tradeoff
- **Brownout-aware** — graceful degradation under energy constraints
- **Cycle-approximate simulation** — fast design-space exploration

---

## 🚀 Quick Start

```bash
pip install -r requirements.txt
python src/main.py --config configs/zero_adc.yaml
```

---

## 📁 Project Structure

```
ZeroADC/
├── figs/                          # All result figures (13 plots)
├── configs/                       # Experiment configurations
├── src/
│   ├── main.py                    # Entry point
│   ├── core/                      # Delta compute core
│   ├── sim/                       # Cycle-approximate simulator
│   └── utils/                     # Logging, metrics, plots
├── requirements.txt
└── README.md
```

---

## 📄 License

MIT © Md Sadman Bin Masud
