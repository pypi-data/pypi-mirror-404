"""
损失函数模块

提供用于 Reranker 训练的各类损失函数：
- LambdaLoss 框架：支持 NDCG、MAP、MRR 等指标优化
- Listwise 损失：ListMLE、p-ListMLE、ListNet
- Pairwise 损失：RankNet、正例排序
- Pointwise 损失：二分类 CE
- 对比损失：InfoNCE、多正例变体
"""

from .lambda_loss import (
    # 权重方案
    BaseWeightingScheme,
    NoWeightingScheme,
    NDCGLoss1Scheme,
    NDCGLoss2Scheme,
    LambdaRankScheme,
    NDCGLoss2PPScheme,
    MAPScheme,
    MRRScheme,
    WEIGHTING_SCHEMES,
    get_weighting_scheme,
    # 主函数
    lambda_loss,
)

from .listwise import (
    listwise_softmax_ce,
    list_mle,
    p_list_mle,
)

from .pairwise import (
    pairwise_posrank_loss,
    ranknet_loss,
)

from .pointwise import (
    yes_no_to_score,
    pointwise_ce_from_yes_no_logits,
)

from .contrastive import (
    infonce_loss,
)

__all__ = [
    # 权重方案
    "BaseWeightingScheme",
    "NoWeightingScheme",
    "NDCGLoss1Scheme",
    "NDCGLoss2Scheme",
    "LambdaRankScheme",
    "NDCGLoss2PPScheme",
    "MAPScheme",
    "MRRScheme",
    "WEIGHTING_SCHEMES",
    "get_weighting_scheme",
    # LambdaLoss
    "lambda_loss",
    # Listwise
    "listwise_softmax_ce",
    "list_mle",
    "p_list_mle",
    # Pairwise
    "pairwise_posrank_loss",
    "ranknet_loss",
    # Pointwise
    "yes_no_to_score",
    "pointwise_ce_from_yes_no_logits",
    # Contrastive
    "infonce_loss",
]
