"""
Recovery: Loss Recovery and Error Mitigation (Algorithm 3)
===========================================================

Implements hardware-aware error correction and result calibration.
Applies fidelity estimation and log-probability weighting to simulation results.

Key Features:
- Fidelity estimation: F_final = Π(1-p_gate) × exp(-Σ loss_path)
- Log-probability weighting for numerical stability
- Hardware characteristic integration
"""

from __future__ import annotations

import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RecoveryResult:
    """
    Result container for loss recovery and error mitigation.
    
    Attributes:
        raw_amplitude: Raw simulation amplitude
        corrected_amplitude: Amplitude after error mitigation
        fidelity: Estimated output state fidelity
        log_probability: Log-scale probability weight
        n_corrections: Number of error corrections applied
        metadata: Additional recovery information
    """
    raw_amplitude: complex
    corrected_amplitude: complex
    fidelity: float
    log_probability: float
    n_corrections: int
    metadata: Dict[str, Any]
    
    def __repr__(self) -> str:
        return (
            f"RecoveryResult(fidelity={self.fidelity:.4f}, "
            f"corrections={self.n_corrections})"
        )


class LossRecovery:
    """
    Handles photon loss recovery and hardware error mitigation.
    
    Integrates hardware characteristics into simulation results
    to account for realistic device imperfections.
    
    Attributes:
        p_gate: Gate error probability
        p_detection: Detection error probability
        p_source: Source error probability
        loss_paths: Tracked optical loss paths
        engine: GraphEngine instance for graph surgery
    """
    
    def __init__(
        self,
        p_gate: float = 0.01,
        p_detection: float = 0.05,
        p_source: float = 0.02,
        coherence_time: float = 1.0,
        engine: Optional[Any] = None
    ):
        """
        Initialize loss recovery module.
        
        Args:
            p_gate: Gate error probability (default 1%)
            p_detection: Detection error probability (default 5%)
            p_source: Source error probability (default 2%)
            coherence_time: Coherence time in arbitrary units
            engine: Optional GraphEngine instance for handling loss
        """
        self.p_gate = p_gate
        self.p_detection = p_detection
        self.p_source = p_source
        self.coherence_time = coherence_time
        self.engine = engine
        
        self.loss_paths: List[float] = []
        self.n_gates: int = 0
        self.n_detections: int = 0
        
        logger.debug(
            f"LossRecovery initialized: p_gate={p_gate}, "
            f"p_detection={p_detection}, p_source={p_source}"
        )
    
    def register_gate(self, n: int = 1) -> None:
        """Register n gate operations for fidelity tracking."""
        self.n_gates += n
    
    def register_detection(self, n: int = 1) -> None:
        """Register n detection events for fidelity tracking."""
        self.n_detections += n
    
    def handle_loss(self, lost_node: int) -> None:
        """
        Handle loss at a specific node by applying graph surgery.
        
        Algorithm (v1.0.8):
        1. Get neighbors of lost node
        2. Apply local complementation at the lost node itself (bridging neighbors)
        3. Remove all edges to/from lost node
        
        Args:
            lost_node: Index of the lost node
        """
        if self.engine is None:
            logger.warning("No engine registered with LossRecovery. Cannot handle loss.")
            return

        neighbors = self.engine.get_neighbors(lost_node)
        
        # [v1.0.8 핵심 로직] 유실된 노드 자체를 피벗으로 사용
        if len(neighbors) >= 2:
            self.engine.local_complementation(lost_node)
        
        # 유실된 노드 제거
        if hasattr(self.engine, 'remove_node'):
            self.engine.remove_node(lost_node)
        elif hasattr(self.engine, 'adj'):
            # Fallback for direct adj matrix manipulation
            self.engine.adj[lost_node, :] = 0
            self.engine.adj[:, lost_node] = 0
        else:
            logger.error("Engine does not support node removal operations.")
    
    def register_loss_path(self, loss_probability: float) -> None:
        """Register an optical loss path."""
        self.loss_paths.append(loss_probability)
    
    def estimate_fidelity(
        self,
        n_qubits: Optional[int] = None,
        custom_gate_count: Optional[int] = None,
        custom_loss_paths: Optional[List[float]] = None
    ) -> float:
        """
        Estimate final state fidelity.
        
        Formula: F_final = Π(1-p_gate)^n_gates × Π(1-p_det)^n_det × exp(-Σ loss_path)
        """
        n_gates = custom_gate_count if custom_gate_count is not None else self.n_gates
        loss_paths = custom_loss_paths if custom_loss_paths is not None else self.loss_paths
        
        gate_fidelity = (1 - self.p_gate) ** n_gates
        detection_fidelity = (1 - self.p_detection) ** self.n_detections
        source_fidelity = 1 - self.p_source
        
        if loss_paths:
            total_loss = sum(loss_paths)
            loss_fidelity = np.exp(-total_loss)
        else:
            loss_fidelity = 1.0
        
        fidelity = gate_fidelity * detection_fidelity * source_fidelity * loss_fidelity
        
        logger.debug(
            f"Fidelity estimate: gate={gate_fidelity:.4f}, "
            f"detection={detection_fidelity:.4f}, loss={loss_fidelity:.4f}, "
            f"total={fidelity:.4f}"
        )
        
        return float(np.clip(fidelity, 0, 1))
    
    def apply_log_weighting(
        self,
        amplitudes: np.ndarray,
        loss_probabilities: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Apply log-probability weighting to prevent floating-point underflow."""
        log_probs = 2 * np.log(np.abs(amplitudes) + 1e-300)
        
        if loss_probabilities is not None:
            log_survival = np.log(1 - loss_probabilities + 1e-300)
            log_probs += log_survival
        
        max_log_prob = np.max(log_probs)
        normalized_log_probs = log_probs - max_log_prob
        normalized_amplitudes = amplitudes * np.exp(normalized_log_probs / 2)
        
        norm = np.sqrt(np.sum(np.abs(normalized_amplitudes) ** 2))
        if norm > 0:
            normalized_amplitudes /= norm
        
        return log_probs, normalized_amplitudes
    
    def mitigate_errors(
        self,
        raw_result: complex,
        n_qubits: int,
        loss_rate: float = 0.0
    ) -> RecoveryResult:
        """Apply complete error mitigation pipeline to raw simulation result."""
        estimated_gates = n_qubits * 2
        
        self.register_gate(estimated_gates)
        self.register_loss_path(loss_rate * n_qubits)
        
        fidelity = self.estimate_fidelity()
        corrected_amplitude = raw_result * np.sqrt(fidelity)
        
        log_prob = np.log(np.abs(raw_result) ** 2 + 1e-300)
        log_prob += np.log(fidelity + 1e-300)
        
        result = RecoveryResult(
            raw_amplitude=raw_result,
            corrected_amplitude=corrected_amplitude,
            fidelity=fidelity,
            log_probability=float(log_prob),
            n_corrections=estimated_gates,
            metadata={
                'n_qubits': n_qubits,
                'loss_rate': loss_rate,
                'n_gates': self.n_gates,
                'n_loss_paths': len(self.loss_paths)
            }
        )
        
        logger.info(f"Error mitigation complete: fidelity={fidelity:.4f}")
        
        return result
    
    def zero_noise_extrapolation(
        self,
        results: List[Tuple[float, complex]]
    ) -> complex:
        """Perform zero-noise extrapolation from multiple noise levels."""
        if len(results) < 2:
            return results[0][1] if results else 0j
        
        results = sorted(results, key=lambda x: x[0])
        
        noise_levels = np.array([r[0] for r in results])
        amplitudes = np.array([r[1] for r in results])
        
        real_coeffs = np.polyfit(noise_levels, amplitudes.real, 1)
        imag_coeffs = np.polyfit(noise_levels, amplitudes.imag, 1)
        
        zero_noise_real = np.polyval(real_coeffs, 0)
        zero_noise_imag = np.polyval(imag_coeffs, 0)
        
        return complex(zero_noise_real, zero_noise_imag)
    
    def probabilistic_error_cancellation(
        self,
        noisy_results: List[complex],
        quasi_probabilities: List[float]
    ) -> complex:
        """Apply probabilistic error cancellation."""
        if len(noisy_results) != len(quasi_probabilities):
            raise ValueError("Results and quasi-probabilities must have same length")
        
        result = sum(q * r for q, r in zip(quasi_probabilities, noisy_results))
        
        return complex(result)
    
    def reset(self) -> None:
        """Reset all tracked error information."""
        self.loss_paths = []
        self.n_gates = 0
        self.n_detections = 0
        logger.debug("LossRecovery state reset")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current recovery state for serialization."""
        return {
            'p_gate': self.p_gate,
            'p_detection': self.p_detection,
            'p_source': self.p_source,
            'coherence_time': self.coherence_time,
            'n_gates': self.n_gates,
            'n_detections': self.n_detections,
            'n_loss_paths': len(self.loss_paths),
            'total_loss': sum(self.loss_paths)
        }
    
    @classmethod
    def from_hardware_model(cls, hardware_params: Dict[str, Any]) -> 'LossRecovery':
        """Create LossRecovery from hardware model parameters."""
        return cls(
            p_gate=hardware_params.get('gate_error', 0.01),
            p_detection=hardware_params.get('detection_error', 0.05),
            p_source=hardware_params.get('source_error', 0.02),
            coherence_time=hardware_params.get('coherence_time', 1.0)
        )


class SimpleLossHandler:
    """
    Simplified loss handler for quick graph recovery operations.
    
    Provides a minimal interface for handling photon loss without
    the full error mitigation pipeline.
    """
    
    def __init__(self, engine):
        """Initialize with a graph engine."""
        self.engine = engine
    
    def handle_loss(self, lost_node: int) -> None:
        """
        Handle loss at a specific node by applying graph surgery.
        
        Algorithm (v1.0.8 수정):
        1. Get neighbors of lost node
        2. Apply local complementation at THE LOST NODE ITSELF (not neighbor!)
           - This creates edges between all pairs of neighbors (bridging)
        3. Remove all edges to/from lost node
        
        Why this works:
        - Local complementation at node v inverts edges between all neighbors of v
        - For linear chain 1-2-3, if node 2 is lost:
          - Neighbors of 2 are {1, 3}
          - LC at node 2 creates edge between 1 and 3 (the bridge!)
        """
        neighbors = self.engine.get_neighbors(lost_node)
        
        # [핵심 수정 v1.0.8] 유실된 노드 자체를 피벗으로 사용
        # 이웃이 2개 이상일 때만 LC가 의미있음 (이웃들을 서로 연결)
        if len(neighbors) >= 2:
            self.engine.local_complementation(lost_node)
        
        # 유실된 노드의 모든 에지 제거
        if hasattr(self.engine, 'remove_node'):
            self.engine.remove_node(lost_node)
        else:
            self.engine.adj[lost_node, :] = 0
            self.engine.adj[:, lost_node] = 0
    
    def handle_multiple_losses(self, lost_nodes: List[int]) -> int:
        """Handle multiple node losses."""
        count = 0
        for node in sorted(lost_nodes, reverse=True):
            self.handle_loss(node)
            count += 1
        return count


# Backward Compatibility Alias
RecoveryManager = LossRecovery
