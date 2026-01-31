<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-CPU_Only-orange.svg" alt="Platform">
  <img src="https://img.shields.io/badge/Version-1.0.9ple.svg" alt="Version">
</p>

<h1 align="center">LAGC</h1>
<h3 align="center">LossAware-GraphCompiler</h3>

<p align="center">
  <b>A CPU-only, loss-aware quantum graph compiler for photonic quantum computing simulation</b>
</p>

<p align="center">
  <a href="#-key-features">Features</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-documentation">Docs</a> •
  <a href="#-citation">Citation</a>
</p>

---

## 🎯 What is LAGC?

**LAGC** is a high-performance simulation library for photonic quantum computing that runs **entirely on CPU** — no GPU required.

It models realistic photon loss, automatically repairs damaged graph states through graph surgery, and performs memory-efficient tensor network contraction to simulate large-scale cluster states.

### Why LAGC?

| Traditional Simulators | LAGC |
|------------------------|------|
| Requires GPU | ✅ **CPU-only operation** |
| Disk swap on memory overflow (100x slower) | ✅ **Recursive slicing within RAM** |
| Ideal states only | ✅ **Realistic loss modeling + auto recovery** |
| Low experimental accuracy | ✅ **Hardware-aware error mitigation** |

---

## ✨ Key Features

- **🖥️ CPU-Only**: No GPU required — runs on standard hardware
- **📉 Loss-Aware**: Realistic photon loss modeling with automatic graph surgery
- **💾 Memory-Efficient**: Recursive tensor slicing stays within RAM limits
- **🔧 Hardware Models**: Built-in noise profiles (ideal, realistic, near-term, experimental, future)
- **📊 Multiple Topologies**: 3D RHG, 2D Cluster, Linear, GHZ, Ring, Complete

---

## 📦 Installation

```bash
pip install lagc
```

### From Source

```bash
git clone https://github.com/quantum-dev/lagc.git
cd lagc
pip install -e ".[dev]"
```

### Requirements

- Python ≥ 3.9
- NumPy, SciPy, opt-einsum, NetworkX (auto-installed)
- **No GPU needed** ✨

---

## 🚀 Quick Start

```python
from lagc import LAGC

# 1. Create simulator (8GB RAM limit)
sim = LAGC(ram_limit_gb=8.0, hardware='realistic')

# 2. Build 3D RHG lattice (for fault-tolerant quantum computing)
sim.create_lattice('3d_rhg', 5, 5, 5)
print(f"Created: {sim.n_qubits} qubits")

# 3. Apply 5% photon loss with automatic recovery
sim.apply_loss(p_loss=0.05)

# 4. Run simulation
result = sim.run_simulation()

# 5. Get results
print(f"Fidelity: {result.fidelity:.4f}")
print(f"Active qubits: {result.n_active}/{result.n_qubits}")
print(f"Time: {result.execution_time:.2f}s")
```

---

## 🗺️ Supported Topologies

| Topology | Use Case |
|----------|----------|
| `'3d_rhg'` | Fault-tolerant MBQC (Raussendorf-Harrington-Goyal) |
| `'2d_cluster'` | Standard cluster state |
| `'linear'` | 1D chain (one-way quantum computing) |
| `'ghz'` | GHZ state (entanglement distribution) |
| `'ring'` | Cyclic protocols |
| `'complete'` | Fully connected graph |

---

## 🔧 Hardware Models

```python
from lagc import LAGC

# Built-in presets
sim = LAGC(hardware='ideal')        # Perfect system (no errors)
sim = LAGC(hardware='realistic')    # Current technology
sim = LAGC(hardware='near_term')    # 5-year projection
sim = LAGC(hardware='experimental') # Cutting-edge prototypes
sim = LAGC(hardware='future')       # 10-year outlook
```

### Custom Hardware

```python
from lagc import HardwareModel, HardwareParams

params = HardwareParams(
    source_efficiency=0.92,
    detector_efficiency=0.88,
    gate_error_cz=0.015,
    coherence_time=5e-6
)
sim = LAGC(hardware=HardwareModel(params))
```

---

## 📊 Example: Loss Threshold Analysis

```python
from lagc import LAGC

sim = LAGC(hardware='ideal', seed=42)

results = sim.scan_loss_rates(
    loss_rates=[0.0, 0.05, 0.10, 0.15, 0.20],
    topology='2d_cluster',
    dims=(10, 10),
    n_samples=5
)

for p, f in zip(results['loss_rates'], results['fidelities']):
    bar = '█' * int(f * 30)
    print(f"p={p:.2f}: {f:.4f} |{bar}")
```

Output:
```
p=0.00: 1.0000 |██████████████████████████████
p=0.05: 0.8521 |█████████████████████████
p=0.10: 0.6234 |██████████████████
p=0.15: 0.3892 |███████████
p=0.20: 0.1847 |█████
```

---

## 🧮 Core Algorithms

### Algorithm 1: Graph Surgery (XOR-based)

For each lost photon, performs **Local Complementation (τ_a)** to repair the graph state:

```python
# Invert edges between neighbors of lost node a
adj_matrix[neighbors(a), neighbors(a)] ^= 1
```

### Algorithm 2: Recursive Tensor Slicing

Automatic memory management:

```
Intermediate tensor > Available RAM?
├── YES → Cut highest-centrality bond
│         ├── Branch 0: index=0
│         └── Branch 1: index=1
│         → Parallel execution via ProcessPoolExecutor
└── NO  → Direct contraction
```

### Algorithm 3: Fidelity Estimation

$$F_{final} = \prod (1 - p_{gate})^{n_{gates}} \times \exp\left(-\sum \text{loss\_paths}\right)$$

---

## ⚡ Performance

| Lattice | Qubits | Time (8-core) | Memory |
|---------|--------|---------------|--------|
| 4×4 Cluster | 16 | 0.07s | < 1 GB |
| 5×5 Cluster | 25 | ~62s | ~2 GB |
| 3D RHG 2×2×2 | 18 | 0.21s | < 1 GB |

*Benchmarked on Intel Core i7*

---

## 💻 Command Line Interface

```bash
# Show version
lagc --version

# Show library info
lagc info

# Run simulation
lagc simulate --topology 2d_cluster --size 5 5 --loss 0.05 --hardware realistic
```

---

## 📚 API Reference

### Main Classes

| Class | Description |
|-------|-------------|
| `LAGC` | Main simulator interface |
| `StabilizerGraph` | Graph state management |
| `TensorSlicer` | Memory-efficient contraction |
| `LossRecovery` | Error mitigation |
| `HardwareModel` | Noise modeling |
| `TopologyGenerator` | Lattice creation |

```python
from lagc import (
    LAGC,
    StabilizerGraph,
    TensorSlicer,
    LossRecovery,
    HardwareModel,
    TopologyGenerator,
)
```

---

## 📖 Documentation

Full documentation: [https://lagc.readthedocs.io](https://lagc.readthedocs.io)

- [Getting Started Tutorial](https://lagc.readthedocs.io/tutorial)
- [API Reference](https://lagc.readthedocs.io/api)
- [Theoretical Background](https://lagc.readthedocs.io/theory)

---

## 📝 Citation

If you use LAGC in your research, please cite:

```bibtex
@software{lagc2026,
  title = {LAGC: LossAware-GraphCompiler for Photonic Quantum Computing},
  author = {LAGC Research Team},
  year = {2026},
  url = {https://github.com/quantum-dev/lagc},
  version = {1.0.0}
}
```

---

## 📚 References

1. Raussendorf, R., Harrington, J., & Goyal, K. (2007). "Topological fault-tolerance in cluster state quantum computation." *New Journal of Physics*.

2. Bartolucci, S., et al. (2023). "Fusion-based quantum computation." *Nature Communications*.

3. Bombin, H., et al. (2021). "Interleaving: Modular architectures for fault-tolerant photonic quantum computing." *arXiv:2103.08612*.

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Development setup
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Format code
black lagc/
isort lagc/
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  <b>LAGC v1.0.0</b><br>
  <i>Accelerating Photonic Quantum Computing Research</i><br>
  <br>
  ⭐ Star us on GitHub if LAGC helps your research!
</p>
