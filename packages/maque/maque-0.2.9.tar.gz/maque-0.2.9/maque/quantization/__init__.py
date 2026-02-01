"""模型量化模块

提供多种量化方案的统一接口，支持 vLLM 推理和 QLoRA 微调场景。

支持的量化方法:
    - auto-round: Intel SGD 优化权重舍入，精度好 (推荐)
    - awq: Activation-aware Weight Quantization
    - gptq: 经典 GPTQ 量化
    - bnb-nf4: 4-bit NormalFloat 量化 (QLoRA)
    - bnb-int8: 8-bit 整数量化

Examples:
    >>> from maque.quantization import get_quantizer
    >>> quantizer = get_quantizer("auto-round")
    >>> quantizer.quantize("Qwen/Qwen3-4B", "./Qwen3-4B-quant")

    >>> from maque.quantization import AutoRoundQuantizer
    >>> quantizer = AutoRoundQuantizer(bits=4, group_size=128)
    >>> quantizer.quantize(model_path, output_path)
"""

from .base import (
    BaseQuantizer,
    QuantConfig,
    get_quantizer,
    list_methods,
    QUANTIZATION_METHODS,
)
from .auto_round import AutoRoundQuantizer
from .llm_compressor import LLMCompressorQuantizer
from .bitsandbytes import BitsAndBytesQuantizer

__all__ = [
    "BaseQuantizer",
    "QuantConfig",
    "get_quantizer",
    "list_methods",
    "QUANTIZATION_METHODS",
    "AutoRoundQuantizer",
    "LLMCompressorQuantizer",
    "BitsAndBytesQuantizer",
]
