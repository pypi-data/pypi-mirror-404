"""
RL 训练模块

提供用于 Reranker RL 训练的损失和奖励函数：
- REINFORCE (GRPO/DAPO/Dr.GRPO)
- DPO
- Doc-level rewards
"""

from .rewards import (
    compute_doc_level_rewards,
    compute_doc_level_advantages,
    compute_ndcg_based_rewards,
    compute_recall_based_rewards,
)

from .losses import (
    reinforce_loss,
    dpo_loss,
)

__all__ = [
    # Rewards
    "compute_doc_level_rewards",
    "compute_doc_level_advantages",
    "compute_ndcg_based_rewards",
    "compute_recall_based_rewards",
    # Losses
    "reinforce_loss",
    "dpo_loss",
]
