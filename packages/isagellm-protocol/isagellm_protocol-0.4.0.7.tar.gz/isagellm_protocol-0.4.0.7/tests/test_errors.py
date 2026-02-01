"""测试错误类型定义"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sagellm_protocol import Error, ErrorCode


class TestErrorCode:
    """测试 ErrorCode 枚举"""

    def test_error_codes_exist(self) -> None:
        """验证所有错误码存在"""
        assert ErrorCode.INVALID_ARGUMENT == "invalid_argument"
        assert ErrorCode.RESOURCE_EXHAUSTED == "resource_exhausted"
        assert ErrorCode.UNAVAILABLE == "unavailable"
        assert ErrorCode.DEADLINE_EXCEEDED == "deadline_exceeded"
        assert ErrorCode.NOT_IMPLEMENTED == "not_implemented"


class TestError:
    """测试 Error 类型"""

    def test_valid_error(self) -> None:
        """测试合法的错误对象"""
        error = Error(
            code=ErrorCode.INVALID_ARGUMENT,
            message="Missing required field: model",
        )
        assert error.code == ErrorCode.INVALID_ARGUMENT
        assert error.message == "Missing required field: model"
        assert error.retryable is None

    def test_error_with_retryable(self) -> None:
        """测试带 retryable 标识的错误"""
        error = Error(
            code=ErrorCode.RESOURCE_EXHAUSTED,
            message="KV cache budget exceeded",
            retryable=True,
        )
        assert error.retryable is True

    def test_error_serialization(self) -> None:
        """测试错误对象序列化"""
        error = Error(
            code=ErrorCode.UNAVAILABLE,
            message="Backend unavailable",
            retryable=False,
        )
        data = error.model_dump()
        assert data["code"] == ErrorCode.UNAVAILABLE
        assert data["message"] == "Backend unavailable"
        assert data["retryable"] is False

    def test_error_missing_required_field(self) -> None:
        """测试缺少必填字段"""
        with pytest.raises(ValidationError):
            Error(code=ErrorCode.INVALID_ARGUMENT)  # type: ignore
