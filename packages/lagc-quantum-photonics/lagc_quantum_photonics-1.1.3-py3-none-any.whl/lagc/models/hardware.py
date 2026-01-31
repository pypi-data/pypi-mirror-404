"""
Hardware Model: Noise and Loss Characterization
================================================

JSON-based hardware parameter management for realistic quantum photonic simulations.
Includes preset profiles for ideal, realistic, and experimental hardware.

Parameters modeled:
- Photon loss rates (source, channel, detection)
- Gate error rates (single-qubit, two-qubit)
- Detector efficiency and dark counts
- Coherence and dephasing times
"""

from __future__ import annotations

import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class HardwareParams:
    """
    Hardware parameters for photonic quantum computing.
    
    All probabilities are per-operation unless otherwise specified.
    """
    # Source parameters
    source_efficiency: float = 0.95  # Single photon source efficiency
    source_indistinguishability: float = 0.99  # Photon indistinguishability
    source_g2: float = 0.001  # g^(2)(0) multi-photon probability
    
    # Channel/waveguide parameters
    channel_loss_per_cm: float = 0.001  # dB/cm for on-chip waveguides
    coupling_loss: float = 0.05  # Loss at each coupling point
    
    # Gate parameters
    gate_error_single: float = 0.001  # Single qubit gate error
    gate_error_two: float = 0.01  # Two qubit (fusion) gate error
    gate_error_cz: float = 0.01  # CZ gate error (for graph state)
    
    # Detection parameters
    detector_efficiency: float = 0.90  # Photon detection efficiency
    detector_dark_count: float = 1e-6  # Dark count rate per ns
    detector_timing_jitter: float = 50e-12  # Timing jitter in seconds
    
    # Coherence parameters
    coherence_time: float = 1e-6  # Coherence time in seconds
    dephasing_rate: float = 1e-4  # Dephasing rate
    
    # System parameters
    clock_rate: float = 1e9  # Clock rate in Hz
    temperature: float = 4.0  # Operating temperature in Kelvin
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HardwareParams':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# Preset hardware profiles
HARDWARE_PRESETS = {
    'ideal': HardwareParams(
        source_efficiency=1.0,
        source_indistinguishability=1.0,
        source_g2=0.0,
        channel_loss_per_cm=0.0,
        coupling_loss=0.0,
        gate_error_single=0.0,
        gate_error_two=0.0,
        gate_error_cz=0.0,
        detector_efficiency=1.0,
        detector_dark_count=0.0,
        detector_timing_jitter=0.0,
        coherence_time=float('inf'),
        dephasing_rate=0.0,
    ),
    'near_term': HardwareParams(
        source_efficiency=0.80,
        source_indistinguishability=0.95,
        source_g2=0.01,
        channel_loss_per_cm=0.01,
        coupling_loss=0.10,
        gate_error_single=0.001,
        gate_error_two=0.05,
        gate_error_cz=0.05,
        detector_efficiency=0.80,
        detector_dark_count=1e-5,
        detector_timing_jitter=100e-12,
        coherence_time=1e-6,
        dephasing_rate=1e-3,
    ),
    'realistic': HardwareParams(
        source_efficiency=0.90,
        source_indistinguishability=0.98,
        source_g2=0.005,
        channel_loss_per_cm=0.005,
        coupling_loss=0.05,
        gate_error_single=0.0005,
        gate_error_two=0.02,
        gate_error_cz=0.02,
        detector_efficiency=0.90,
        detector_dark_count=1e-6,
        detector_timing_jitter=50e-12,
        coherence_time=10e-6,
        dephasing_rate=1e-4,
    ),
    'experimental': HardwareParams(
        source_efficiency=0.70,
        source_indistinguishability=0.90,
        source_g2=0.02,
        channel_loss_per_cm=0.02,
        coupling_loss=0.15,
        gate_error_single=0.005,
        gate_error_two=0.10,
        gate_error_cz=0.10,
        detector_efficiency=0.70,
        detector_dark_count=1e-4,
        detector_timing_jitter=200e-12,
        coherence_time=1e-7,
        dephasing_rate=1e-2,
    ),
    'future': HardwareParams(
        source_efficiency=0.99,
        source_indistinguishability=0.999,
        source_g2=0.0001,
        channel_loss_per_cm=0.0001,
        coupling_loss=0.01,
        gate_error_single=0.0001,
        gate_error_two=0.001,
        gate_error_cz=0.001,
        detector_efficiency=0.99,
        detector_dark_count=1e-8,
        detector_timing_jitter=10e-12,
        coherence_time=100e-6,
        dephasing_rate=1e-5,
    ),
}


class HardwareModel:
    """
    Hardware noise and loss model manager.
    
    Manages hardware parameters for photonic quantum simulations,
    including preset profiles and JSON-based custom configurations.
    
    Example:
        >>> hw = HardwareModel.from_preset('realistic')
        >>> loss = hw.get_effective_loss_rate()
        >>> fidelity = hw.estimate_operation_fidelity(n_gates=100)
    """
    
    def __init__(self, params: Optional[HardwareParams] = None):
        """
        Initialize hardware model.
        
        Args:
            params: Hardware parameters (default: realistic preset)
        """
        self.params = params or HARDWARE_PRESETS['realistic']
        self._cache: Dict[str, Any] = {}
        
        logger.debug(f"HardwareModel initialized with params: {self.params}")
    
    @classmethod
    def from_preset(cls, preset_name: str) -> 'HardwareModel':
        """
        Create from a preset profile.
        
        Args:
            preset_name: One of 'ideal', 'near_term', 'realistic', 
                        'experimental', 'future'
                        
        Returns:
            Configured HardwareModel
        """
        if preset_name not in HARDWARE_PRESETS:
            available = list(HARDWARE_PRESETS.keys())
            raise ValueError(f"Unknown preset '{preset_name}'. Available: {available}")
        
        return cls(HARDWARE_PRESETS[preset_name])
    
    @classmethod
    def from_json(cls, path: Union[str, Path]) -> 'HardwareModel':
        """
        Load hardware model from JSON file.
        
        Args:
            path: Path to JSON file
            
        Returns:
            Configured HardwareModel
        """
        path = Path(path)
        with open(path, 'r') as f:
            data = json.load(f)
        
        params = HardwareParams.from_dict(data)
        return cls(params)
    
    def to_json(self, path: Union[str, Path]) -> None:
        """
        Save hardware model to JSON file.
        
        Args:
            path: Path to save JSON file
        """
        path = Path(path)
        with open(path, 'w') as f:
            json.dump(self.params.to_dict(), f, indent=2)
    
    def get_effective_loss_rate(
        self,
        channel_length_cm: float = 1.0,
        n_couplings: int = 2
    ) -> float:
        """
        Calculate effective photon loss rate through the system.
        
        Args:
            channel_length_cm: Total channel/waveguide length in cm
            n_couplings: Number of coupling points
            
        Returns:
            Total loss probability
        """
        # Source loss
        source_loss = 1 - self.params.source_efficiency
        
        # Channel loss (convert from dB/cm to probability)
        channel_loss_db = self.params.channel_loss_per_cm * channel_length_cm
        channel_loss = 1 - 10 ** (-channel_loss_db / 10)
        
        # Coupling loss
        coupling_loss = 1 - (1 - self.params.coupling_loss) ** n_couplings
        
        # Detection loss
        detection_loss = 1 - self.params.detector_efficiency
        
        # Combined (assuming independent losses)
        # P(loss) = 1 - P(survive_all)
        survival = (
            (1 - source_loss) *
            (1 - channel_loss) *
            (1 - coupling_loss) *
            (1 - detection_loss)
        )
        
        return 1 - survival
    
    def estimate_operation_fidelity(
        self,
        n_single_gates: int = 0,
        n_two_gates: int = 0,
        n_cz_gates: int = 0,
        duration_ns: float = 0
    ) -> float:
        """
        Estimate fidelity of a quantum operation.
        
        Args:
            n_single_gates: Number of single-qubit gates
            n_two_gates: Number of two-qubit gates
            n_cz_gates: Number of CZ gates
            duration_ns: Operation duration in nanoseconds
            
        Returns:
            Estimated fidelity (0 to 1)
        """
        # Gate errors
        single_fidelity = (1 - self.params.gate_error_single) ** n_single_gates
        two_fidelity = (1 - self.params.gate_error_two) ** n_two_gates
        cz_fidelity = (1 - self.params.gate_error_cz) ** n_cz_gates
        
        # Decoherence
        if duration_ns > 0 and self.params.coherence_time > 0:
            duration_s = duration_ns * 1e-9
            coherence_fidelity = np.exp(-duration_s / self.params.coherence_time)
        else:
            coherence_fidelity = 1.0
        
        # Dark count contribution
        dark_count_prob = self.params.detector_dark_count * duration_ns
        dark_count_fidelity = 1 - min(dark_count_prob, 1.0)
        
        total_fidelity = (
            single_fidelity *
            two_fidelity *
            cz_fidelity *
            coherence_fidelity *
            dark_count_fidelity
        )
        
        return float(np.clip(total_fidelity, 0, 1))
    
    def get_error_model_dict(self) -> Dict[str, float]:
        """
        Get error model as dictionary for LossRecovery integration.
        
        Returns:
            Dictionary compatible with LossRecovery.from_hardware_model()
        """
        return {
            'gate_error': self.params.gate_error_cz,
            'detection_error': 1 - self.params.detector_efficiency,
            'source_error': 1 - self.params.source_efficiency,
            'coherence_time': self.params.coherence_time,
        }
    
    def sample_loss(
        self,
        n_photons: int,
        seed: Optional[int] = None
    ) -> np.ndarray:
        """
        Sample photon loss events.
        
        Args:
            n_photons: Number of photons to sample
            seed: Random seed
            
        Returns:
            Boolean array where True indicates loss
        """
        if seed is not None:
            np.random.seed(seed)
        
        loss_rate = self.get_effective_loss_rate()
        return np.random.random(n_photons) < loss_rate
    
    def sample_gate_errors(
        self,
        n_gates: int,
        gate_type: str = 'cz',
        seed: Optional[int] = None
    ) -> np.ndarray:
        """
        Sample gate error events.
        
        Args:
            n_gates: Number of gates
            gate_type: 'single', 'two', or 'cz'
            seed: Random seed
            
        Returns:
            Boolean array where True indicates error
        """
        if seed is not None:
            np.random.seed(seed)
        
        error_rates = {
            'single': self.params.gate_error_single,
            'two': self.params.gate_error_two,
            'cz': self.params.gate_error_cz,
        }
        
        rate = error_rates.get(gate_type, self.params.gate_error_cz)
        return np.random.random(n_gates) < rate
    
    def __repr__(self) -> str:
        loss = self.get_effective_loss_rate()
        fidelity = self.estimate_operation_fidelity(n_cz_gates=10)
        return (
            f"HardwareModel(loss_rate={loss:.3f}, "
            f"10-gate_fidelity={fidelity:.4f})"
        )
    
    @staticmethod
    def list_presets() -> list:
        """List available preset names."""
        return list(HARDWARE_PRESETS.keys())
