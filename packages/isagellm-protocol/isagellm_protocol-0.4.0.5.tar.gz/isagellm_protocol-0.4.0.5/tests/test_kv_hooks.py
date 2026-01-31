"""测试 KV 生命周期钩子类型定义"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sagellm_protocol import (
    KVAllocateParams,
    KVDType,
    KVEvictReason,
    KVHandle,
    KVLayout,
    KVMigrateParams,
)


class TestKVDType:
    """测试 KVDType 枚举"""

    def test_kv_dtypes_exist(self) -> None:
        """验证所有 KV 数据类型存在"""
        assert KVDType.FP16 == "fp16"
        assert KVDType.BF16 == "bf16"
        assert KVDType.FP8 == "fp8"
        assert KVDType.INT8 == "int8"


class TestKVLayout:
    """测试 KVLayout 枚举"""

    def test_kv_layouts_exist(self) -> None:
        """验证所有 KV 布局存在"""
        assert KVLayout.BSHD == "bshd"
        assert KVLayout.BHSD == "bhsd"


class TestKVAllocateParams:
    """测试 KVAllocateParams 类型"""

    def test_valid_allocate_params(self) -> None:
        """测试合法的分配参数"""
        params = KVAllocateParams(
            request_id="req-001",
            num_tokens=2048,
            kv_dtype=KVDType.FP16,
            layout=KVLayout.BSHD,
            block_size=64,
        )
        assert params.request_id == "req-001"
        assert params.num_tokens == 2048
        assert params.kv_dtype == KVDType.FP16
        assert params.layout == KVLayout.BSHD
        assert params.block_size == 64

    def test_num_tokens_must_be_positive(self) -> None:
        """测试 num_tokens 必须 > 0"""
        with pytest.raises(ValidationError):
            KVAllocateParams(
                request_id="req-001",
                num_tokens=0,  # 必须 > 0
                kv_dtype=KVDType.FP16,
                layout=KVLayout.BSHD,
                block_size=64,
            )

    def test_block_size_must_be_positive(self) -> None:
        """测试 block_size 必须 > 0"""
        with pytest.raises(ValidationError):
            KVAllocateParams(
                request_id="req-001",
                num_tokens=2048,
                kv_dtype=KVDType.FP16,
                layout=KVLayout.BSHD,
                block_size=0,  # 必须 > 0
            )


class TestKVHandle:
    """测试 KVHandle 类型"""

    def test_valid_handle(self) -> None:
        """测试合法的句柄"""
        handle = KVHandle(
            handle_id="handle-001",
            request_id="req-001",
            num_tokens=2048,
            device="cuda:0",
        )
        assert handle.handle_id == "handle-001"
        assert handle.request_id == "req-001"
        assert handle.num_tokens == 2048
        assert handle.device == "cuda:0"

    def test_handle_serialization(self) -> None:
        """测试句柄序列化"""
        handle = KVHandle(
            handle_id="handle-001",
            request_id="req-001",
            num_tokens=2048,
            device="npu:0",
        )
        data = handle.model_dump()
        assert data["handle_id"] == "handle-001"
        assert data["device"] == "npu:0"


class TestKVEvictReason:
    """测试 KVEvictReason 枚举"""

    def test_evict_reasons_exist(self) -> None:
        """验证所有驱逐原因存在"""
        assert KVEvictReason.MEMORY_PRESSURE == "memory_pressure"
        assert KVEvictReason.TTL_EXPIRED == "ttl_expired"
        assert KVEvictReason.EXPLICIT_FREE == "explicit_free"


class TestKVMigrateParams:
    """测试 KVMigrateParams 类型"""

    def test_valid_migrate_params(self) -> None:
        """测试合法的迁移参数"""
        handle = KVHandle(
            handle_id="handle-001",
            request_id="req-001",
            num_tokens=2048,
            device="cuda:0",
        )
        params = KVMigrateParams(
            kv_handle=handle,
            target_device="cuda:1",
        )
        assert params.kv_handle == handle
        assert params.target_device == "cuda:1"

    def test_migrate_params_serialization(self) -> None:
        """测试迁移参数序列化"""
        handle = KVHandle(
            handle_id="handle-001",
            request_id="req-001",
            num_tokens=2048,
            device="npu:0",
        )
        params = KVMigrateParams(
            kv_handle=handle,
            target_device="npu:1",
        )
        data = params.model_dump()
        assert data["target_device"] == "npu:1"
        assert data["kv_handle"]["device"] == "npu:0"
