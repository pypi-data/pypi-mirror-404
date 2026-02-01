"""量化器抽象基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Literal
from pathlib import Path


@dataclass
class QuantConfig:
    """量化配置"""
    bits: int = 4
    group_size: int = 128
    sym: bool = True
    seqlen: int = 512
    nsamples: int = 128
    batch_size: int = 4
    low_gpu_mem_usage: bool = True


class BaseQuantizer(ABC):
    """量化器抽象基类"""

    def __init__(self, config: QuantConfig = None):
        self.config = config or QuantConfig()

    @abstractmethod
    def quantize(self, model_path: str, output_path: str, **kwargs) -> str:
        """量化模型

        Args:
            model_path: 原始模型路径
            output_path: 量化后模型保存路径
            **kwargs: 额外参数

        Returns:
            量化后模型路径
        """
        pass

    @property
    @abstractmethod
    def method_name(self) -> str:
        """量化方法名称"""
        pass

    @property
    def supported_formats(self) -> List[str]:
        """支持的输出格式"""
        return ["auto"]

    def get_model_info(self, model_path: str) -> dict:
        """获取模型的量化信息"""
        import json
        model_path = Path(model_path)

        # 检查 quantization_config.json
        quant_config_path = model_path / "quantization_config.json"
        if quant_config_path.exists():
            with open(quant_config_path, "r") as f:
                return json.load(f)

        # 检查 config.json 中的 quantization_config
        config_path = model_path / "config.json"
        if config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)
                if "quantization_config" in config:
                    return config["quantization_config"]

        return {}


# 支持的量化方法
QUANTIZATION_METHODS = {
    "auto-round": "AutoRoundQuantizer",
    "awq": "LLMCompressorQuantizer",
    "gptq": "LLMCompressorQuantizer",
    "bnb-nf4": "BitsAndBytesQuantizer",
    "bnb-int8": "BitsAndBytesQuantizer",
}


def get_quantizer(method: str, **kwargs) -> BaseQuantizer:
    """根据方法名获取量化器

    Args:
        method: 量化方法名称 (auto-round, awq, gptq, bnb-nf4, bnb-int8)
        **kwargs: 传递给量化器的参数

    Returns:
        BaseQuantizer 实例
    """
    if method not in QUANTIZATION_METHODS:
        available = ", ".join(QUANTIZATION_METHODS.keys())
        raise ValueError(f"不支持的量化方法: {method}，可用方法: {available}")

    if method == "auto-round":
        from .auto_round import AutoRoundQuantizer
        return AutoRoundQuantizer(**kwargs)
    elif method in ("awq", "gptq"):
        from .llm_compressor import LLMCompressorQuantizer
        return LLMCompressorQuantizer(scheme=method, **kwargs)
    elif method in ("bnb-nf4", "bnb-int8"):
        from .bitsandbytes import BitsAndBytesQuantizer
        bits = 4 if method == "bnb-nf4" else 8
        return BitsAndBytesQuantizer(bits=bits, **kwargs)
    else:
        raise ValueError(f"未实现的量化方法: {method}")


def list_methods() -> dict:
    """列出所有支持的量化方法及其描述"""
    return {
        "auto-round": {
            "library": "auto-round",
            "precision": "W4A16",
            "description": "Intel 出品，SGD 优化权重舍入，精度好",
            "use_case": "vLLM 推理",
        },
        "awq": {
            "library": "llm-compressor",
            "precision": "W4A16",
            "description": "Activation-aware Weight Quantization",
            "use_case": "vLLM 推理",
        },
        "gptq": {
            "library": "llm-compressor",
            "precision": "W4A16",
            "description": "经典 GPTQ 量化",
            "use_case": "通用推理",
        },
        "bnb-nf4": {
            "library": "bitsandbytes",
            "precision": "NF4",
            "description": "4-bit NormalFloat 量化",
            "use_case": "QLoRA 微调",
        },
        "bnb-int8": {
            "library": "bitsandbytes",
            "precision": "INT8",
            "description": "8-bit 整数量化",
            "use_case": "显存节省",
        },
    }
