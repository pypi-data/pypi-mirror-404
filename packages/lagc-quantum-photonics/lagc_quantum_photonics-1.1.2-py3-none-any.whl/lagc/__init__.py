# 파일 위치: lagc/__init__.py
"""
LAGC: LossAware-GraphCompiler
=============================

CPU 전용 손실 인식 양자 그래프 컴파일러
"""

__version__ = "1.1.2"
__author__ = "LAGC Research Team"

# 1. 의존성 체크
def _check_dependencies():
    missing = []
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    try:
        import scipy
    except ImportError:
        missing.append("scipy")
    try:
        import opt_einsum
    except ImportError:
        missing.append("opt-einsum")
    if missing:
        raise ImportError(f"LAGC requires: {', '.join(missing)}. Install with: pip install {' '.join(missing)}")

_check_dependencies()

# 2. core 패키지에서 핵심 클래스들을 위로 가져옵니다.
from .core.graph_engine import GraphEngine, StabilizerGraph
from .core.recovery import LossRecovery, RecoveryManager

# 3. 메인 파사드 클래스를 가져옵니다.
try:
    from .main import LAGC, SimulationResult, quick_simulation
except ImportError:
    LAGC = None
    SimulationResult = None
    quick_simulation = None

# 4. 사용자가 'from lagc import *' 했을 때 노출할 최종 리스트
__all__ = [
    # 버전
    "__version__",
    # 메인 API
    "LAGC",
    "SimulationResult",
    "quick_simulation",
    # 핵심 클래스
    "GraphEngine",
    "StabilizerGraph",
    "LossRecovery",
    "RecoveryManager",
]


def info():
    """라이브러리 정보 출력"""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  LAGC: LossAware-GraphCompiler v{__version__}                      ║
╠══════════════════════════════════════════════════════════════╣
║  CPU 전용 손실 인식 양자 그래프 컴파일러                      ║
╚══════════════════════════════════════════════════════════════╝

>>> from lagc import LAGC
>>> sim = LAGC()
>>> sim.create_lattice('2d_cluster', 5, 5)
>>> sim.apply_loss(0.05)
>>> result = sim.run_simulation()
""")
