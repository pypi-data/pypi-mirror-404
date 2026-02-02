"""LLM Compressor 量化器

使用 vLLM 官方的 llm-compressor 库进行 AWQ/GPTQ 量化。
"""

from .base import BaseQuantizer, QuantConfig
from typing import Literal
from pathlib import Path


class LLMCompressorQuantizer(BaseQuantizer):
    """LLM Compressor 量化器

    使用 vLLM 官方的 llm-compressor 库，支持 AWQ 和 GPTQ 量化方案。

    Args:
        scheme: 量化方案 (awq, gptq)，默认 awq
        bits: 量化位数，默认 4
        group_size: 量化分组大小，默认 128
        sym: 是否对称量化，默认 True

    Examples:
        >>> from maque.quantization import LLMCompressorQuantizer
        >>> quantizer = LLMCompressorQuantizer(scheme="awq")
        >>> quantizer.quantize("Qwen/Qwen3-4B", "./Qwen3-4B-awq")
    """

    def __init__(
        self,
        scheme: Literal["awq", "gptq"] = "awq",
        bits: int = 4,
        group_size: int = 128,
        sym: bool = True,
        **kwargs,
    ):
        config = QuantConfig(
            bits=bits,
            group_size=group_size,
            sym=sym,
        )
        super().__init__(config)
        self.scheme = scheme

    @property
    def method_name(self) -> str:
        return self.scheme

    def quantize(self, model_path: str, output_path: str, **kwargs) -> str:
        """执行量化

        Args:
            model_path: 原始模型路径
            output_path: 量化后模型保存路径
            **kwargs: 额外参数

        Returns:
            量化后模型路径
        """
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from llmcompressor.modifiers.quantization import QuantizationModifier
            from llmcompressor import oneshot
        except ImportError as e:
            if "llmcompressor" in str(e) or "oneshot" in str(e):
                raise ImportError(
                    "llm-compressor 未安装，请运行: pip install llmcompressor"
                )
            raise

        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"[{self.scheme}] 加载模型: {model_path}")

        # 加载模型
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="auto",
            torch_dtype="auto",
        )
        tokenizer = AutoTokenizer.from_pretrained(model_path)

        # 配置量化方案
        scheme_name = f"W{self.config.bits}A16"
        print(f"[{self.scheme}] 配置: scheme={scheme_name}, group_size={self.config.group_size}")

        recipe = QuantizationModifier(
            targets="Linear",
            scheme=scheme_name,
            ignore=["lm_head"],
        )

        print(f"[{self.scheme}] 开始量化...")
        oneshot(
            model=model,
            tokenizer=tokenizer,
            recipe=recipe,
            output_dir=str(output_path),
        )

        print(f"[{self.scheme}] 量化完成! 保存到: {output_path}")
        return str(output_path)
