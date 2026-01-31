"""测试 OpenAI API 兼容类型定义

这些类型供 Gateway 使用，用于与 OpenAI API 保持兼容。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sagellm_protocol import (
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


class TestChatMessage:
    """测试 ChatMessage 类型"""

    def test_valid_chat_message(self) -> None:
        """测试合法的聊天消息"""
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.name is None

    def test_chat_message_with_name(self) -> None:
        """测试带 name 字段的消息"""
        msg = ChatMessage(role="assistant", content="Hi", name="bot")
        assert msg.name == "bot"

    def test_all_valid_roles(self) -> None:
        """测试所有合法的角色"""
        valid_roles = ["system", "user", "assistant", "function", "tool"]
        for role in valid_roles:
            msg = ChatMessage(role=role, content="test")  # type: ignore
            assert msg.role == role


class TestChatCompletionRequest:
    """测试 ChatCompletionRequest 类型"""

    def test_minimal_request(self) -> None:
        """测试最小请求"""
        messages = [ChatMessage(role="user", content="Hello")]
        req = ChatCompletionRequest(model="gpt-3.5-turbo", messages=messages)
        assert req.model == "gpt-3.5-turbo"
        assert len(req.messages) == 1
        assert req.stream is False
        assert req.temperature == 1.0
        assert req.n == 1

    def test_request_with_all_fields(self) -> None:
        """测试带所有字段的请求"""
        messages = [
            ChatMessage(role="system", content="You are helpful"),
            ChatMessage(role="user", content="Hello"),
        ]
        req = ChatCompletionRequest(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
            stream=True,
            top_p=0.9,
            n=2,
            stop=["END"],
            presence_penalty=0.5,
            frequency_penalty=0.3,
            user="user-123",
            session_id="sess-001",
            trace_id="trace-001",
        )
        assert req.temperature == 0.7
        assert req.max_tokens == 100
        assert req.stream is True
        assert req.session_id == "sess-001"

    def test_temperature_range(self) -> None:
        """测试 temperature 范围验证"""
        messages = [ChatMessage(role="user", content="test")]
        # temperature 必须在 [0, 2] 范围内
        with pytest.raises(ValidationError):
            ChatCompletionRequest(model="test", messages=messages, temperature=-0.1)
        with pytest.raises(ValidationError):
            ChatCompletionRequest(model="test", messages=messages, temperature=2.1)

    def test_top_p_range(self) -> None:
        """测试 top_p 范围验证"""
        messages = [ChatMessage(role="user", content="test")]
        # top_p 必须在 (0, 1] 范围内
        with pytest.raises(ValidationError):
            ChatCompletionRequest(model="test", messages=messages, top_p=0.0)
        with pytest.raises(ValidationError):
            ChatCompletionRequest(model="test", messages=messages, top_p=1.1)


class TestChatCompletionResponse:
    """测试 ChatCompletionResponse 类型"""

    def test_valid_response(self) -> None:
        """测试合法的响应"""
        choice = ChatCompletionChoice(
            index=0,
            message=ChatMessage(role="assistant", content="Hi"),
            finish_reason="stop",
        )
        usage = ChatCompletionUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        resp = ChatCompletionResponse(
            id="chatcmpl-123",
            model="gpt-3.5-turbo",
            choices=[choice],
            usage=usage,
        )
        assert resp.id == "chatcmpl-123"
        assert resp.object == "chat.completion"
        assert len(resp.choices) == 1
        assert resp.usage.total_tokens == 15

    def test_response_with_trace_id(self) -> None:
        """测试带 trace_id 的响应"""
        choice = ChatCompletionChoice(
            index=0,
            message=ChatMessage(role="assistant", content="Hi"),
            finish_reason="stop",
        )
        usage = ChatCompletionUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        resp = ChatCompletionResponse(
            id="chatcmpl-123",
            model="gpt-3.5-turbo",
            choices=[choice],
            usage=usage,
            trace_id="trace-001",
        )
        assert resp.trace_id == "trace-001"

    def test_response_serialization(self) -> None:
        """测试响应序列化"""
        choice = ChatCompletionChoice(
            index=0,
            message=ChatMessage(role="assistant", content="Hi"),
            finish_reason="stop",
        )
        usage = ChatCompletionUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        resp = ChatCompletionResponse(
            id="chatcmpl-123",
            model="gpt-3.5-turbo",
            choices=[choice],
            usage=usage,
        )
        data = resp.model_dump()
        assert data["object"] == "chat.completion"
        assert data["id"] == "chatcmpl-123"
        assert "created" in data


class TestChatCompletionStreamResponse:
    """测试流式响应类型"""

    def test_stream_response(self) -> None:
        """测试流式响应"""
        delta = ChatCompletionStreamDelta(content="Hi")
        choice = ChatCompletionStreamChoice(index=0, delta=delta)
        resp = ChatCompletionStreamResponse(
            id="chatcmpl-123", model="gpt-3.5-turbo", choices=[choice]
        )
        assert resp.object == "chat.completion.chunk"
        assert resp.choices[0].delta.content == "Hi"

    def test_stream_response_with_finish_reason(self) -> None:
        """测试带结束原因的流式响应"""
        delta = ChatCompletionStreamDelta(content="")
        choice = ChatCompletionStreamChoice(index=0, delta=delta, finish_reason="stop")
        resp = ChatCompletionStreamResponse(
            id="chatcmpl-123", model="gpt-3.5-turbo", choices=[choice]
        )
        assert resp.choices[0].finish_reason == "stop"


class TestEmbeddingTypes:
    """测试 Embedding 相关类型"""

    def test_embedding_request_single_input(self) -> None:
        """测试单个输入的 embedding 请求"""
        req = EmbeddingRequest(input="Hello world", model="text-embedding-ada-002")
        assert req.input == "Hello world"
        assert req.model == "text-embedding-ada-002"
        assert req.encoding_format == "float"

    def test_embedding_request_batch_input(self) -> None:
        """测试批量输入的 embedding 请求"""
        req = EmbeddingRequest(input=["Hello", "World"], model="text-embedding-ada-002")
        assert isinstance(req.input, list)
        assert len(req.input) == 2

    def test_embedding_response(self) -> None:
        """测试 embedding 响应"""
        data = [
            EmbeddingData(embedding=[0.1, 0.2, 0.3], index=0),
            EmbeddingData(embedding=[0.4, 0.5, 0.6], index=1),
        ]
        usage = EmbeddingUsage(prompt_tokens=10, total_tokens=10)
        resp = EmbeddingResponse(data=data, model="text-embedding-ada-002", usage=usage)
        assert resp.object == "list"
        assert len(resp.data) == 2
        assert resp.data[0].object == "embedding"

    def test_embedding_data_serialization(self) -> None:
        """测试 embedding 数据序列化"""
        data = EmbeddingData(embedding=[0.1, 0.2], index=0)
        serialized = data.model_dump()
        assert serialized["object"] == "embedding"
        assert serialized["embedding"] == [0.1, 0.2]
        assert serialized["index"] == 0


class TestModelTypes:
    """测试模型信息类型"""

    def test_model_info(self) -> None:
        """测试模型信息"""
        model = ModelInfo(id="llama2-7b")
        assert model.id == "llama2-7b"
        assert model.object == "model"
        assert model.owned_by == "sagellm"
        assert model.created > 0

    def test_model_list_response(self) -> None:
        """测试模型列表响应"""
        models = [
            ModelInfo(id="llama2-7b"),
            ModelInfo(id="llama2-13b"),
        ]
        resp = ModelListResponse(data=models)
        assert resp.object == "list"
        assert len(resp.data) == 2
        assert resp.data[0].id == "llama2-7b"


class TestErrorTypes:
    """测试错误类型"""

    def test_openai_error(self) -> None:
        """测试 OpenAI 错误"""
        error = OpenAIError(
            message="Invalid request",
            type="invalid_request_error",
            param="model",
            code="model_not_found",
        )
        assert error.message == "Invalid request"
        assert error.type == "invalid_request_error"
        assert error.param == "model"
        assert error.code == "model_not_found"

    def test_openai_error_response(self) -> None:
        """测试 OpenAI 错误响应包装"""
        error = OpenAIError(message="Server error", type="server_error")
        resp = OpenAIErrorResponse(error=error)
        assert resp.error.message == "Server error"
        assert resp.error.type == "server_error"

    def test_error_serialization(self) -> None:
        """测试错误序列化"""
        error = OpenAIError(message="Test error", type="test_error")
        resp = OpenAIErrorResponse(error=error)
        data = resp.model_dump()
        assert "error" in data
        assert data["error"]["message"] == "Test error"


class TestFieldValidation:
    """测试字段验证"""

    def test_penalty_range(self) -> None:
        """测试 penalty 字段范围验证"""
        messages = [ChatMessage(role="user", content="test")]
        # presence_penalty 和 frequency_penalty 必须在 [-2, 2] 范围内
        with pytest.raises(ValidationError):
            ChatCompletionRequest(model="test", messages=messages, presence_penalty=-2.1)
        with pytest.raises(ValidationError):
            ChatCompletionRequest(model="test", messages=messages, frequency_penalty=2.1)

    def test_usage_token_counts(self) -> None:
        """测试 token 计数"""
        usage = ChatCompletionUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        assert usage.prompt_tokens + usage.completion_tokens == usage.total_tokens
