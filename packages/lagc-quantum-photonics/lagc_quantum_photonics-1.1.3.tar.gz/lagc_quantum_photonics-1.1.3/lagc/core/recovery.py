import logging
from .graph_engine import GraphEngine

# 로깅 설정
logger = logging.getLogger(__name__)

class LossRecovery:
    """
    [LAGC Core] 광자 손실 복구 매니저
    GraphEngine과 연동하여 손실된 큐비트 발생 시 그래프 토폴로지를 재구성합니다.
    """
    def __init__(self, engine: GraphEngine):
        # [핵심 수정 1] 들어온 엔진을 반드시 self.engine에 저장해야 합니다.
        if engine is None:
            raise ValueError("LossRecovery requires a valid GraphEngine instance.")
        self.engine = engine

    def handle_loss(self, lost_node):
        """
        특정 노드 유실 시, 해당 노드를 피벗으로 국소 보수(LC)를 수행하여
        주변 이웃 노드들을 서로 얽힘(Entanglement) 상태로 연결합니다.
        """
        # 안전장치: 엔진이 없으면 작동 불가
        if not hasattr(self, 'engine') or self.engine is None:
            logger.warning("No engine registered with LossRecovery. Cannot handle loss.")
            return

        # 1. 유실된 노드의 이웃 확인
        neighbors = self.engine.get_neighbors(lost_node)
        
        # 2. [핵심 수정 2] 복구 로직 (Local Complementation)
        # 1D 체인 복구를 위해 유실된 노드 자체를 피벗으로 사용합니다.
        if len(neighbors) >= 2:
            self.engine.local_complementation(lost_node)
        
        # 3. [핵심 수정 3] 노드 제거 (Physical Removal)
        # 행렬에서 해당 노드의 모든 연결을 0으로 밀어버립니다.
        self.engine.adj[lost_node, :] = 0
        self.engine.adj[:, lost_node] = 0
        
        logger.info(f"Recovered graph from loss at node {lost_node}. Neighbors bridged.")

# 하위 호환성용 Alias
RecoveryManager = LossRecovery
