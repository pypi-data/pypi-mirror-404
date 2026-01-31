"""测试核心类型定义"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sagellm_protocol import (
    Error,
    ErrorCode,
    Metrics,
    Request,
    Response,
    StreamEventDelta,
    StreamEventEnd,
    StreamEventStart,
)


class TestRequest:
    """测试 Request 类型"""

    def test_valid_request(self) -> None:
        """测试合法的请求"""
        req = Request(
            request_id="req-001",
            trace_id="trace-001",
            model="llama2-7b",
            prompt="Hello",
            max_tokens=128,
            stream=False,
        )
        assert req.request_id == "req-001"
        assert req.trace_id == "trace-001"
        assert req.model == "llama2-7b"
        assert req.prompt == "Hello"
        assert req.max_tokens == 128
        assert req.stream is False

    def test_request_with_optional_fields(self) -> None:
        """测试带可选字段的请求"""
        req = Request(
            request_id="req-001",
            trace_id="trace-001",
            model="llama2-7b",
            prompt="Hello",
            max_tokens=128,
            stream=False,
            temperature=0.7,
            top_p=0.9,
            kv_budget_tokens=2048,
            metadata={"key": "value"},
        )
        assert req.temperature == 0.7
        assert req.top_p == 0.9
        assert req.kv_budget_tokens == 2048
        assert req.metadata == {"key": "value"}

    def test_missing_required_field(self) -> None:
        """测试缺少必填字段"""
        with pytest.raises(ValidationError):
            Request(  # type: ignore
                request_id="req-001",
                trace_id="trace-001",
                # 缺 model, prompt, max_tokens, stream
            )

    def test_max_tokens_must_be_positive(self) -> None:
        """测试 max_tokens 必须 > 0"""
        with pytest.raises(ValidationError):
            Request(
                request_id="req-001",
                trace_id="trace-001",
                model="test",
                prompt="Hello",
                max_tokens=0,  # 必须 > 0
                stream=False,
            )

    def test_temperature_range(self) -> None:
        """测试 temperature 范围"""
        # temperature 必须 > 0 且 <= 2
        with pytest.raises(ValidationError):
            Request(
                request_id="req-001",
                trace_id="trace-001",
                model="test",
                prompt="Hello",
                max_tokens=10,
                stream=False,
                temperature=0.0,  # 必须 > 0
            )

        with pytest.raises(ValidationError):
            Request(
                request_id="req-001",
                trace_id="trace-001",
                model="test",
                prompt="Hello",
                max_tokens=10,
                stream=False,
                temperature=3.0,  # 必须 <= 2
            )

    def test_top_p_range(self) -> None:
        """测试 top_p 范围"""
        # top_p 必须 > 0 且 <= 1
        with pytest.raises(ValidationError):
            Request(
                request_id="req-001",
                trace_id="trace-001",
                model="test",
                prompt="Hello",
                max_tokens=10,
                stream=False,
                top_p=0.0,  # 必须 > 0
            )

        with pytest.raises(ValidationError):
            Request(
                request_id="req-001",
                trace_id="trace-001",
                model="test",
                prompt="Hello",
                max_tokens=10,
                stream=False,
                top_p=1.5,  # 必须 <= 1
            )

    def test_kv_budget_tokens_must_be_positive(self) -> None:
        """测试 kv_budget_tokens 必须 > 0"""
        with pytest.raises(ValidationError):
            Request(
                request_id="req-001",
                trace_id="trace-001",
                model="test",
                prompt="Hello",
                max_tokens=10,
                stream=False,
                kv_budget_tokens=0,  # 必须 > 0
            )


class TestMetrics:
    """测试 Metrics 类型"""

    def test_valid_metrics_with_tbt(self) -> None:
        """测试带 tbt_ms 的合法指标"""
        m = Metrics(
            ttft_ms=45.2,
            tbt_ms=12.5,
            throughput_tps=80.0,
            peak_mem_mb=24576,
            error_rate=0.02,
        )
        assert m.ttft_ms == 45.2
        assert m.tbt_ms == 12.5
        assert m.tpot_ms == 0.0  # 默认值为 0，符合 Demo Contract

    def test_valid_metrics_with_tpot(self) -> None:
        """测试带 tpot_ms 的合法指标"""
        m = Metrics(
            ttft_ms=45.2,
            tpot_ms=12.5,
            throughput_tps=80.0,
            peak_mem_mb=24576,
            error_rate=0.0,
        )
        assert m.ttft_ms == 45.2
        assert m.tpot_ms == 12.5
        assert m.tbt_ms == 0.0  # 默认值为 0，符合 Demo Contract

    def test_valid_metrics_with_both(self) -> None:
        """测试同时有 tbt_ms 和 tpot_ms"""
        m = Metrics(
            ttft_ms=45.2,
            tbt_ms=12.5,
            tpot_ms=12.5,
            throughput_tps=80.0,
            peak_mem_mb=24576,
            error_rate=0.0,
        )
        assert m.tbt_ms == 12.5
        assert m.tpot_ms == 12.5

    def test_default_values_for_optional_metrics(self) -> None:
        """测试 tbt_ms 和 tpot_ms 有默认值 0（符合 Demo Contract）"""
        # 现在不需要显式提供 tbt_ms 或 tpot_ms，会自动填充 0
        m = Metrics(
            ttft_ms=45.2,
            throughput_tps=80.0,
            peak_mem_mb=24576,
            error_rate=0.0,
        )
        assert m.tbt_ms == 0.0
        assert m.tpot_ms == 0.0
        # 验证所有 Demo Contract 必需字段都有默认值
        assert m.kv_used_tokens == 0
        assert m.kv_used_bytes == 0
        assert m.prefix_hit_rate == 0.0
        assert m.evict_count == 0
        assert m.evict_ms == 0.0
        assert m.spec_accept_rate == 0.0

    def test_error_rate_range(self) -> None:
        """测试 error_rate 范围"""
        with pytest.raises(ValidationError):
            Metrics(
                ttft_ms=45.2,
                tbt_ms=12.5,
                throughput_tps=80.0,
                peak_mem_mb=24576,
                error_rate=1.5,  # 必须 <= 1
            )

    def test_metrics_with_optional_fields(self) -> None:
        """测试带可选字段的指标"""
        m = Metrics(
            ttft_ms=45.2,
            tbt_ms=12.5,
            throughput_tps=80.0,
            peak_mem_mb=24576,
            error_rate=0.02,
            kv_used_tokens=4096,
            kv_used_bytes=134217728,
            prefix_hit_rate=0.85,
            evict_count=3,
            evict_ms=2.1,
            spec_accept_rate=0.72,
        )
        assert m.kv_used_tokens == 4096
        assert m.prefix_hit_rate == 0.85
        assert m.spec_accept_rate == 0.72

    def test_optional_fields_range(self) -> None:
        """测试可选字段范围校验"""
        with pytest.raises(ValidationError):
            Metrics(
                ttft_ms=45.2,
                tbt_ms=12.5,
                throughput_tps=80.0,
                peak_mem_mb=24576,
                error_rate=0.0,
                prefix_hit_rate=1.5,  # 必须 <= 1
            )


class TestResponse:
    """测试 Response 类型"""

    def test_valid_response(self) -> None:
        """测试合法的响应"""
        metrics = Metrics(
            ttft_ms=45.2,
            tbt_ms=12.5,
            throughput_tps=80.0,
            peak_mem_mb=24576,
            error_rate=0.0,
        )
        resp = Response(
            request_id="req-001",
            trace_id="trace-001",
            output_text="Hi there",
            output_tokens=[42, 17],
            finish_reason="stop",
            metrics=metrics,
        )
        assert resp.request_id == "req-001"
        assert resp.output_text == "Hi there"
        assert resp.finish_reason == "stop"
        assert resp.error is None

    def test_response_with_error(self) -> None:
        """测试带错误的响应"""
        metrics = Metrics(
            ttft_ms=45.2,
            tbt_ms=12.5,
            throughput_tps=80.0,
            peak_mem_mb=24576,
            error_rate=0.0,
        )
        error = Error(
            code=ErrorCode.RESOURCE_EXHAUSTED,
            message="KV cache exhausted",
        )
        resp = Response(
            request_id="req-001",
            trace_id="trace-001",
            output_text="",
            output_tokens=[],
            finish_reason="error",
            metrics=metrics,
            error=error,
        )
        assert resp.error is not None
        assert resp.error.code == ErrorCode.RESOURCE_EXHAUSTED


class TestStreamEvent:
    """测试 StreamEvent 类型"""

    def test_stream_event_start(self) -> None:
        """测试 start 事件"""
        event = StreamEventStart(
            request_id="req-001",
            trace_id="trace-001",
            engine_id="engine-001",  # 添加 engine_id
            prompt_tokens=10,
        )
        assert event.event == "start"
        assert event.request_id == "req-001"
        assert event.engine_id == "engine-001"
        assert event.prompt_tokens == 10

    def test_stream_event_delta(self) -> None:
        """测试 delta 事件"""
        event = StreamEventDelta(
            request_id="req-001",
            trace_id="trace-001",
            engine_id="engine-001",  # 添加 engine_id
            chunk="Hi",
            chunk_tokens=[42],
        )
        assert event.event == "delta"
        assert event.engine_id == "engine-001"
        assert event.chunk == "Hi"
        assert event.chunk_tokens == [42]

    def test_stream_event_end(self) -> None:
        """测试 end 事件"""
        metrics = Metrics(
            ttft_ms=40.0,
            tbt_ms=11.0,
            throughput_tps=75.0,
            peak_mem_mb=20480,
            error_rate=0.0,
        )
        event = StreamEventEnd(
            request_id="req-001",
            trace_id="trace-001",
            engine_id="engine-001",  # 添加 engine_id
            output_text="Hi there",
            output_tokens=[42, 17],
            finish_reason="stop",
            metrics=metrics,
        )
        assert event.event == "end"
        assert event.output_text == "Hi there"
        assert event.finish_reason == "stop"

    def test_stream_event_discriminated_union(self) -> None:
        """测试 StreamEvent 作为 Discriminated Union"""
        # 注意：这里测试的是类型解析，实际使用时会自动根据 event 字段选择类型
        start_event = StreamEventStart(
            request_id="req-001",
            trace_id="trace-001",
            engine_id="engine-001",  # 添加 engine_id
        )
        delta_event = StreamEventDelta(
            request_id="req-001",
            trace_id="trace-001",
            engine_id="engine-001",  # 添加 engine_id
            chunk="Hi",
            chunk_tokens=[42],
        )
        metrics = Metrics(
            ttft_ms=40.0,
            tbt_ms=11.0,
            throughput_tps=75.0,
            peak_mem_mb=20480,
            error_rate=0.0,
        )
        end_event = StreamEventEnd(
            request_id="req-001",
            trace_id="trace-001",
            engine_id="engine-001",  # 添加 engine_id
            output_text="Hi there",
            output_tokens=[42, 17],
            finish_reason="stop",
            metrics=metrics,
        )

        # 这些事件都应该能被序列化
        assert start_event.model_dump()["event"] == "start"
        assert delta_event.model_dump()["event"] == "delta"
        assert end_event.model_dump()["event"] == "end"
