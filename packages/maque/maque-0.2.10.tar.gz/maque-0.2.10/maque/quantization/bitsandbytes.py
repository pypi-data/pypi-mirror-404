"""BitsAndBytes 量化器

使用 bitsandbytes 库进行 NF4/INT8 量化，主要用于 QLoRA 微调场景。
注意：bitsandbytes 是推理时动态量化，不生成独立的量化模型文件。
"""

from .base import BaseQuantizer, QuantConfig
from typing import Literal
from pathlib import Path


class BitsAndBytesQuantizer(BaseQuantizer):
    """BitsAndBytes 量化器

    使用 bitsandbytes 库进行 NF4/INT8 量化。

    注意：bitsandbytes 是推理时动态量化，调用 quantize() 会：
    1. 加载模型并应用量化配置
    2. 保存带有 quantization_config 的模型配置

    加载时需要使用 load_in_4bit=True 或 load_in_8bit=True。

    Args:
        bits: 量化位数 (4 或 8)，默认 4
        bnb_4bit_compute_dtype: 4bit 计算精度，默认 bfloat16
        bnb_4bit_quant_type: 4bit 量化类型 (nf4, fp4)，默认 nf4
        bnb_4bit_use_double_quant: 是否使用双重量化，默认 True

    Examples:
        >>> from maque.quantization import BitsAndBytesQuantizer
        >>> quantizer = BitsAndBytesQuantizer(bits=4)
        >>> quantizer.quantize("Qwen/Qwen3-4B", "./Qwen3-4B-bnb")
    """

    def __init__(
        self,
        bits: Literal[4, 8] = 4,
        bnb_4bit_compute_dtype: str = "bfloat16",
        bnb_4bit_quant_type: Literal["nf4", "fp4"] = "nf4",
        bnb_4bit_use_double_quant: bool = True,
        **kwargs,
    ):
        config = QuantConfig(bits=bits)
        super().__init__(config)
        self.bnb_4bit_compute_dtype = bnb_4bit_compute_dtype
        self.bnb_4bit_quant_type = bnb_4bit_quant_type
        self.bnb_4bit_use_double_quant = bnb_4bit_use_double_quant

    @property
    def method_name(self) -> str:
        return f"bnb-{'nf4' if self.config.bits == 4 else 'int8'}"

    def quantize(self, model_path: str, output_path: str, **kwargs) -> str:
        """应用量化配置并保存模型

        注意：bitsandbytes 是推理时动态量化，此方法会：
        1. 使用量化配置加载模型
        2. 保存模型和带有 quantization_config 的配置文件

        Args:
            model_path: 原始模型路径
            output_path: 输出路径
            **kwargs: 额外参数

        Returns:
            输出路径
        """
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        except ImportError as e:
            if "bitsandbytes" in str(e):
                raise ImportError(
                    "bitsandbytes 未安装，请运行: pip install bitsandbytes"
                )
            raise

        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"[bnb] 加载模型: {model_path}")

        # 配置 BitsAndBytes
        if self.config.bits == 4:
            compute_dtype = getattr(torch, self.bnb_4bit_compute_dtype)
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=compute_dtype,
                bnb_4bit_quant_type=self.bnb_4bit_quant_type,
                bnb_4bit_use_double_quant=self.bnb_4bit_use_double_quant,
            )
            print(f"[bnb] 配置: NF4, compute_dtype={self.bnb_4bit_compute_dtype}")
        else:
            bnb_config = BitsAndBytesConfig(load_in_8bit=True)
            print(f"[bnb] 配置: INT8")

        # 加载模型
        print(f"[bnb] 应用量化配置加载模型...")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=bnb_config,
            device_map="auto",
        )
        tokenizer = AutoTokenizer.from_pretrained(model_path)

        # 保存模型和配置
        print(f"[bnb] 保存到: {output_path}")
        model.save_pretrained(str(output_path))
        tokenizer.save_pretrained(str(output_path))

        print(f"[bnb] 完成! 加载时请使用 load_in_{self.config.bits}bit=True")
        return str(output_path)

    def get_load_kwargs(self) -> dict:
        """获取加载量化模型时需要的参数"""
        import torch

        if self.config.bits == 4:
            compute_dtype = getattr(torch, self.bnb_4bit_compute_dtype)
            return {
                "load_in_4bit": True,
                "bnb_4bit_compute_dtype": compute_dtype,
                "bnb_4bit_quant_type": self.bnb_4bit_quant_type,
                "bnb_4bit_use_double_quant": self.bnb_4bit_use_double_quant,
            }
        else:
            return {"load_in_8bit": True}
