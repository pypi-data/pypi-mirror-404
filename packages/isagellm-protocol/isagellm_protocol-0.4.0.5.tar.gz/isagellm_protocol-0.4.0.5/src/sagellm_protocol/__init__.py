"""sageLLM Protocol v0.1 类型定义。

本包提供 sageLLM 的公共契约类型，包括：
- 请求/响应类型
- Stream 事件类型
- 指标和错误类型
- Backend 能力类型（DType, KernelKind, CapabilityDescriptor）
- KV 生命周期钩子类型
- OpenAI 兼容类型（供 Gateway 使用）

所有类型定义严格遵循 Protocol v0.1 规范。
"""

from __future__ import annotations

from sagellm_protocol.backend_types import (
    DEVICE_TYPE_ASCEND,
    DEVICE_TYPE_CPU,
    DEVICE_TYPE_CUDA,
    DEVICE_TYPE_NPU,
    DEVICE_TYPE_ROCM,
    DEVICE_TYPE_XPU,
    CapabilityDescriptor,
    DeviceStr,
    DType,
    KernelKind,
    format_device_str,
    parse_device_str,
)
from sagellm_protocol.errors import Error, ErrorCode
from sagellm_protocol.kv_hooks import (
    KVAllocateParams,
    KVDType,
    KVEvictReason,
    KVHandle,
    KVLayout,
    KVMigrateParams,
)
from sagellm_protocol.openai_types import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionStreamChoice,
    ChatCompletionStreamDelta,
    ChatCompletionStreamResponse,
    ChatCompletionUsage,
    ChatMessage,
    EmbeddingData,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingUsage,
    ModelInfo,
    ModelListResponse,
    OpenAIError,
    OpenAIErrorResponse,
)
from sagellm_protocol.timestamps import Timestamps
from sagellm_protocol.types import (
    Metrics,
    Request,
    Response,
    StreamEvent,
    StreamEventDelta,
    StreamEventEnd,
    StreamEventStart,
)

# 别名，用于向后兼容
StartEvent = StreamEventStart
DeltaEvent = StreamEventDelta
EndEvent = StreamEventEnd

__version__ = "0.4.0.5"

__all__ = [
    # Version
    "__version__",
    # Core types
    "Request",
    "Response",
    "Metrics",
    # Streaming
    "StreamEvent",
    "StreamEventStart",
    "StreamEventDelta",
    "StreamEventEnd",
    # Streaming aliases
    "StartEvent",
    "DeltaEvent",
    "EndEvent",
    # Errors
    "Error",
    "ErrorCode",
    # Observability
    "Timestamps",
    # Backend types
    "DType",
    "KernelKind",
    "CapabilityDescriptor",
    "DeviceStr",
    "parse_device_str",
    "format_device_str",
    # Device type constants
    "DEVICE_TYPE_CPU",
    "DEVICE_TYPE_CUDA",
    "DEVICE_TYPE_NPU",
    "DEVICE_TYPE_ASCEND",
    "DEVICE_TYPE_ROCM",
    "DEVICE_TYPE_XPU",
    # KV hooks
    "KVDType",
    "KVLayout",
    "KVAllocateParams",
    "KVHandle",
    "KVEvictReason",
    "KVMigrateParams",
    # OpenAI-compatible types (for Gateway)
    "ChatMessage",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "ChatCompletionChoice",
    "ChatCompletionUsage",
    "ChatCompletionStreamResponse",
    "ChatCompletionStreamChoice",
    "ChatCompletionStreamDelta",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "EmbeddingData",
    "EmbeddingUsage",
    "ModelInfo",
    "ModelListResponse",
    "OpenAIError",
    "OpenAIErrorResponse",
]
