"""Protocol v0.1 KV Cache 协议定义

本模块定义 sageLLM KV Cache 的完整协议类型，包括：
- 核心类型：KVHandle, KVBlock, KVTransferMetadata
- 枚举类型：KVBlockState, DType, Layout, MemoryTier, EvictionPolicy
- 错误码：KVErrorCode
- 指标字段：KVMetricsFields

所有类型定义严格遵循 Protocol v0.1 规范，覆盖 Task2.1-2.9 的需求。
"""

from __future__ import annotations

from sagellm_protocol.kv.enums import (
    CompressionType,
    DType,
    EvictionPolicy,
    KVBlockState,
    Layout,
    MemoryTier,
    RequestType,
    SchedulerState,
    TransferDirection,
    TransferStatus,
)
from sagellm_protocol.kv.errors import (
    KV_ERROR_CATEGORIES,
    RETRYABLE_KV_ERRORS,
    KVErrorCode,
    is_retryable,
)
from sagellm_protocol.kv.metrics import (
    EvictionMetrics,
    KVMetricsFields,
    KVPoolMetrics,
    PrefixCacheMetrics,
    SchedulerMetrics,
    TransferMetrics,
)
from sagellm_protocol.kv.types import (
    EvictionCandidate,
    KVBlock,
    KVHandle,
    KVPoolStats,
    KVTransferMetadata,
    LifetimePrediction,
    PrefixCacheEntry,
    SchedulerPlan,
    SchedulerRequest,
)

__all__ = [
    # === 核心类型 (types.py) ===
    "KVHandle",
    "KVBlock",
    "KVTransferMetadata",
    "PrefixCacheEntry",
    "EvictionCandidate",
    "SchedulerRequest",
    "SchedulerPlan",
    "LifetimePrediction",
    "KVPoolStats",
    # === 枚举类型 (enums.py) ===
    "KVBlockState",
    "DType",
    "Layout",
    "MemoryTier",
    "EvictionPolicy",
    "TransferStatus",
    "TransferDirection",
    "CompressionType",
    "RequestType",
    "SchedulerState",
    # === 错误码 (errors.py) ===
    "KVErrorCode",
    "KV_ERROR_CATEGORIES",
    "RETRYABLE_KV_ERRORS",
    "is_retryable",
    # === 指标字段 (metrics.py) ===
    "KVMetricsFields",
    "PrefixCacheMetrics",
    "KVPoolMetrics",
    "EvictionMetrics",
    "TransferMetrics",
    "SchedulerMetrics",
]
