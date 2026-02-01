"""测试观测时间戳类型定义"""

from __future__ import annotations

import time

import pytest
from pydantic import ValidationError

from sagellm_protocol import Timestamps


class TestTimestamps:
    """测试 Timestamps 类型"""

    def test_valid_timestamps(self) -> None:
        """测试合法的时间戳"""
        now = time.time()
        ts = Timestamps(
            queued_at=now,
            scheduled_at=now + 0.1,
            executed_at=now + 0.2,
            completed_at=now + 0.5,
        )
        assert ts.queued_at == now
        assert ts.scheduled_at == now + 0.1
        assert ts.executed_at == now + 0.2
        assert ts.completed_at == now + 0.5

    def test_timestamps_serialization(self) -> None:
        """测试时间戳序列化"""
        ts = Timestamps(
            queued_at=1000.0,
            scheduled_at=1000.1,
            executed_at=1000.2,
            completed_at=1000.5,
        )
        data = ts.model_dump()
        assert data["queued_at"] == 1000.0
        assert data["scheduled_at"] == 1000.1
        assert data["executed_at"] == 1000.2
        assert data["completed_at"] == 1000.5

    def test_timestamps_missing_field(self) -> None:
        """测试缺少必填字段"""
        with pytest.raises(ValidationError):
            Timestamps(  # type: ignore
                queued_at=1000.0,
                scheduled_at=1000.1,
                executed_at=1000.2,
                # 缺少 completed_at
            )

    def test_metrics_calculation(self) -> None:
        """测试指标计算"""
        ts = Timestamps(
            queued_at=1000.0,
            scheduled_at=1000.1,
            executed_at=1000.2,
            completed_at=1000.5,
        )
        # ttft_ms = (executed_at - scheduled_at) * 1000
        ttft_ms = (ts.executed_at - ts.scheduled_at) * 1000
        assert abs(ttft_ms - 100.0) < 0.01  # 浮点数比较，允许微小误差

        # total_time_ms = (completed_at - queued_at) * 1000
        total_time_ms = (ts.completed_at - ts.queued_at) * 1000
        assert abs(total_time_ms - 500.0) < 0.01  # 浮点数比较，允许微小误差
