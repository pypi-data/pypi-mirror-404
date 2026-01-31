# Changelog

All notable changes to LAGC will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-31

### Added
- 🎉 Initial public release
- **Core Modules**
  - `StabilizerGraph`: XOR-based graph operations with Local Complementation
  - `TensorSlicer`: Memory-efficient recursive tensor slicing
  - `LossRecovery`: Hardware-aware error mitigation
- **Topology Generators**
  - 3D RHG lattice for fault-tolerant MBQC
  - 2D Cluster state
  - Linear, GHZ, Ring, Complete graphs
- **Hardware Models**
  - 5 preset profiles: ideal, realistic, near_term, experimental, future
  - Custom hardware parameter support
- **Simulation Engine**
  - Vectorized graph state tensor generation
  - CPU multicore parallel processing
  - Automatic memory management
- **User API**
  - `LAGC` main class with fluent interface
  - `quick_simulation()` convenience function
  - Loss tolerance scanning

### Performance
- 4×4 Cluster (16 qubits): ~0.07s
- 5×5 Cluster (25 qubits): ~62s
- 3D RHG 2×2×2 (18 qubits): ~0.21s

---

## [Unreleased]

### Planned
- [ ] MPS-based tensor network for >25 qubits
- [ ] GPU acceleration (optional)
- [ ] Interactive visualization dashboard
- [ ] Quantum error correction decoder integration
