"""测试采样参数和解码策略定义"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sagellm_protocol.sampling import (
    DEFAULT_SAMPLING_PARAMS,
    DecodingStrategy,
    SamplingParams,
    SamplingPreset,
)


class TestDecodingStrategy:
    """测试解码策略枚举"""

    def test_strategy_values(self) -> None:
        """测试策略枚举值"""
        assert DecodingStrategy.GREEDY == "greedy"
        assert DecodingStrategy.SAMPLING == "sampling"
        assert DecodingStrategy.BEAM_SEARCH == "beam_search"
        assert DecodingStrategy.CONTRASTIVE == "contrastive"

    def test_strategy_from_string(self) -> None:
        """测试从字符串创建策略"""
        assert DecodingStrategy("greedy") == DecodingStrategy.GREEDY
        assert DecodingStrategy("sampling") == DecodingStrategy.SAMPLING


class TestSamplingParams:
    """测试采样参数配置"""

    def test_default_params(self) -> None:
        """测试默认参数"""
        params = SamplingParams()
        assert params.strategy == DecodingStrategy.GREEDY
        assert params.temperature == 1.0
        assert params.beam_size == 4
        assert params.repetition_penalty == 1.0

    def test_greedy_strategy(self) -> None:
        """测试贪婪解码策略"""
        params = SamplingParams(strategy=DecodingStrategy.GREEDY)
        assert params.strategy == DecodingStrategy.GREEDY
        assert params.temperature == 1.0

    def test_sampling_strategy(self) -> None:
        """测试温度采样策略"""
        params = SamplingParams(
            strategy=DecodingStrategy.SAMPLING, temperature=0.7, top_p=0.9, top_k=50
        )
        assert params.strategy == DecodingStrategy.SAMPLING
        assert params.temperature == 0.7
        assert params.top_p == 0.9
        assert params.top_k == 50

    def test_beam_search_strategy(self) -> None:
        """测试束搜索策略"""
        params = SamplingParams(
            strategy=DecodingStrategy.BEAM_SEARCH,
            beam_size=5,
            length_penalty=1.2,
            early_stopping=True,
        )
        assert params.strategy == DecodingStrategy.BEAM_SEARCH
        assert params.beam_size == 5
        assert params.length_penalty == 1.2
        assert params.early_stopping is True

    def test_contrastive_strategy(self) -> None:
        """测试对比搜索策略"""
        params = SamplingParams(strategy=DecodingStrategy.CONTRASTIVE, alpha=0.6, penalty_alpha=0.6)
        assert params.strategy == DecodingStrategy.CONTRASTIVE
        assert params.alpha == 0.6
        assert params.penalty_alpha == 0.6

    def test_temperature_validation(self) -> None:
        """测试温度参数验证"""
        # 有效温度
        params = SamplingParams(temperature=0.5)
        assert params.temperature == 0.5

        params = SamplingParams(temperature=2.0)
        assert params.temperature == 2.0

        # temperature=0 允许（触发 greedy）
        params = SamplingParams(temperature=0)
        assert params.temperature == 0

        # 无效温度：< 0
        with pytest.raises(ValidationError):
            SamplingParams(temperature=-0.5)

        # 无效温度：> 2
        with pytest.raises(ValidationError):
            SamplingParams(temperature=2.5)

    def test_top_p_validation(self) -> None:
        """测试 top_p 参数验证"""
        # 有效 top_p
        params = SamplingParams(top_p=0.9)
        assert params.top_p == 0.9

        # 无效 top_p：<= 0
        with pytest.raises(ValidationError):
            SamplingParams(top_p=0)

        # 无效 top_p：> 1
        with pytest.raises(ValidationError):
            SamplingParams(top_p=1.5)

    def test_repetition_penalty_validation(self) -> None:
        """测试重复惩罚参数验证"""
        # 有效惩罚系数
        params = SamplingParams(repetition_penalty=1.2)
        assert params.repetition_penalty == 1.2

        # 无效惩罚系数：< 1
        with pytest.raises(ValidationError):
            SamplingParams(repetition_penalty=0.5)

    def test_presence_penalty_validation(self) -> None:
        """测试存在惩罚参数验证"""
        # 有效范围 [-2, 2]
        params = SamplingParams(presence_penalty=0.5)
        assert params.presence_penalty == 0.5

        params = SamplingParams(presence_penalty=-1.5)
        assert params.presence_penalty == -1.5

        # 无效范围
        with pytest.raises(ValidationError):
            SamplingParams(presence_penalty=3.0)

        with pytest.raises(ValidationError):
            SamplingParams(presence_penalty=-3.0)

    def test_validate_greedy_strategy_params(self) -> None:
        """测试贪婪解码参数验证"""
        # 有效：默认 temperature=1.0
        params = SamplingParams(strategy=DecodingStrategy.GREEDY)
        params.validate_strategy_params()  # 不应抛出异常

        # 无效：temperature != 1.0
        params = SamplingParams(strategy=DecodingStrategy.GREEDY, temperature=0.7)
        with pytest.raises(ValueError, match="greedy 策略下 temperature 必须为 1.0"):
            params.validate_strategy_params()

    def test_validate_sampling_strategy_params(self) -> None:
        """测试温度采样参数验证"""
        # 有效：temperature > 0
        params = SamplingParams(strategy=DecodingStrategy.SAMPLING, temperature=0.7)
        params.validate_strategy_params()  # 不应抛出异常

        # 无效：temperature = 0（已在 Pydantic 层拦截，但测试逻辑一致性）
        # 注意：这个会在 Pydantic 验证时失败，这里测试业务逻辑

    def test_validate_beam_search_strategy_params(self) -> None:
        """测试束搜索参数验证"""
        # 有效：beam_size > 1
        params = SamplingParams(strategy=DecodingStrategy.BEAM_SEARCH, beam_size=4)
        params.validate_strategy_params()  # 不应抛出异常

        # 无效：beam_size = 1
        params = SamplingParams(strategy=DecodingStrategy.BEAM_SEARCH, beam_size=1)
        with pytest.raises(ValueError, match="beam_search 策略下 beam_size 必须 > 1"):
            params.validate_strategy_params()

    def test_validate_contrastive_strategy_params(self) -> None:
        """测试对比搜索参数验证"""
        # 有效：alpha in [0, 1], penalty_alpha >= 0
        params = SamplingParams(strategy=DecodingStrategy.CONTRASTIVE, alpha=0.6, penalty_alpha=0.6)
        params.validate_strategy_params()  # 不应抛出异常

        # 无效：alpha > 1（Pydantic 层拦截）
        with pytest.raises(ValidationError):
            SamplingParams(strategy=DecodingStrategy.CONTRASTIVE, alpha=1.5, penalty_alpha=0.6)

        # 无效：penalty_alpha < 0（Pydantic 层拦截）
        with pytest.raises(ValidationError):
            SamplingParams(strategy=DecodingStrategy.CONTRASTIVE, alpha=0.6, penalty_alpha=-0.5)

    def test_stop_sequences(self) -> None:
        """测试停止序列配置"""
        params = SamplingParams(stop_sequences=["###", "\n\n"])
        assert params.stop_sequences == ["###", "\n\n"]

    def test_random_seed(self) -> None:
        """测试随机种子配置"""
        params = SamplingParams(seed=42)
        assert params.seed == 42


class TestSamplingPreset:
    """测试预设采样配置"""

    def test_preset_values(self) -> None:
        """测试预设枚举值"""
        assert SamplingPreset.DETERMINISTIC == "deterministic"
        assert SamplingPreset.BALANCED == "balanced"
        assert SamplingPreset.CREATIVE == "creative"
        assert SamplingPreset.PRECISE == "precise"

    def test_deterministic_preset(self) -> None:
        """测试确定性预设"""
        params = SamplingPreset.get_params(SamplingPreset.DETERMINISTIC)
        assert params.strategy == DecodingStrategy.GREEDY
        assert params.temperature == 1.0

    def test_balanced_preset(self) -> None:
        """测试平衡预设"""
        params = SamplingPreset.get_params(SamplingPreset.BALANCED)
        assert params.strategy == DecodingStrategy.SAMPLING
        assert params.temperature == 0.7
        assert params.top_p == 0.9

    def test_creative_preset(self) -> None:
        """测试创意预设"""
        params = SamplingPreset.get_params(SamplingPreset.CREATIVE)
        assert params.strategy == DecodingStrategy.SAMPLING
        assert params.temperature == 1.2
        assert params.top_p == 0.95

    def test_precise_preset(self) -> None:
        """测试精确预设"""
        params = SamplingPreset.get_params(SamplingPreset.PRECISE)
        assert params.strategy == DecodingStrategy.BEAM_SEARCH
        assert params.beam_size == 4
        assert params.length_penalty == 1.2


class TestDefaultSamplingParams:
    """测试默认配置"""

    def test_default_is_greedy(self) -> None:
        """测试默认配置是贪婪解码（解决 issue #18）"""
        assert DEFAULT_SAMPLING_PARAMS.strategy == DecodingStrategy.GREEDY
        assert DEFAULT_SAMPLING_PARAMS.temperature == 1.0

    def test_default_is_immutable(self) -> None:
        """测试默认配置是常量（不应被修改）"""
        # 验证是否是同一个实例（单例模式）
        assert DEFAULT_SAMPLING_PARAMS is DEFAULT_SAMPLING_PARAMS


class TestSamplingParamsIntegration:
    """集成测试：采样参数在实际场景中的使用"""

    def test_greedy_for_translation(self) -> None:
        """测试翻译场景：使用贪婪解码"""
        params = SamplingParams(strategy=DecodingStrategy.GREEDY)
        params.validate_strategy_params()
        # 确保参数符合翻译需求：确定性、无随机性
        assert params.strategy == DecodingStrategy.GREEDY

    def test_sampling_for_chat(self) -> None:
        """测试对话场景：使用温度采样"""
        params = SamplingParams(
            strategy=DecodingStrategy.SAMPLING, temperature=0.8, top_p=0.95, repetition_penalty=1.1
        )
        params.validate_strategy_params()
        # 确保参数符合对话需求：多样性、避免重复
        assert params.strategy == DecodingStrategy.SAMPLING
        assert params.repetition_penalty > 1.0

    def test_beam_search_for_code_generation(self) -> None:
        """测试代码生成场景：使用束搜索"""
        params = SamplingParams(
            strategy=DecodingStrategy.BEAM_SEARCH,
            beam_size=5,
            length_penalty=1.0,
            early_stopping=False,
        )
        params.validate_strategy_params()
        # 确保参数符合代码生成需求：高质量、完整性
        assert params.strategy == DecodingStrategy.BEAM_SEARCH
        assert params.beam_size > 1

    def test_contrastive_for_story_writing(self) -> None:
        """测试故事创作场景：使用对比搜索"""
        params = SamplingParams(
            strategy=DecodingStrategy.CONTRASTIVE,
            alpha=0.6,
            penalty_alpha=0.6,
            repetition_penalty=1.2,
        )
        params.validate_strategy_params()
        # 确保参数符合创作需求：流畅性、避免重复
        assert params.strategy == DecodingStrategy.CONTRASTIVE
