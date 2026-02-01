"""AutoRound 量化器

使用 Intel 的 auto-round 库进行量化，采用 SGD 优化权重舍入，精度损失小。
"""

from .base import BaseQuantizer, QuantConfig
from typing import Optional
from pathlib import Path


class AutoRoundQuantizer(BaseQuantizer):
    """AutoRound 量化器

    使用 Intel 的 auto-round 库，通过 SGD 优化权重舍入实现高质量量化。

    Args:
        bits: 量化位数，默认 4
        group_size: 量化分组大小，默认 128
        sym: 是否对称量化，默认 True
        iters: 优化迭代次数，默认 200
        seqlen: 校准序列长度，默认 512
        nsamples: 校准样本数，默认 256
        batch_size: 批次大小，默认 4
        low_gpu_mem_usage: 低显存模式，默认 True
        format: 输出格式 (auto_round, auto_gptq)，默认 auto_round
        dataset: 校准数据集，默认 NeelNanda/pile-10k

    Examples:
        >>> from maque.quantization import AutoRoundQuantizer
        >>> quantizer = AutoRoundQuantizer(bits=4)
        >>> quantizer.quantize("Qwen/Qwen3-4B", "./Qwen3-4B-quant")

        # 使用自定义数据集
        >>> quantizer = AutoRoundQuantizer(dataset="wikitext2")
        >>> quantizer.quantize(model_path, output_path)
    """

    def __init__(
        self,
        bits: int = 4,
        group_size: int = 128,
        sym: bool = True,
        iters: int = 200,
        seqlen: int = 512,
        nsamples: int = 256,
        batch_size: int = 4,
        low_gpu_mem_usage: bool = True,
        format: str = "auto_round",
        dataset: str = "NeelNanda/pile-10k",
        **kwargs,
    ):
        config = QuantConfig(
            bits=bits,
            group_size=group_size,
            sym=sym,
            seqlen=seqlen,
            nsamples=nsamples,
            batch_size=batch_size,
            low_gpu_mem_usage=low_gpu_mem_usage,
        )
        super().__init__(config)
        self.iters = iters
        self.format = format
        self.dataset = dataset

    @property
    def method_name(self) -> str:
        return "auto-round"

    @property
    def supported_formats(self):
        return ["auto_round", "auto_gptq"]

    def quantize(self, model_path: str, output_path: str, **kwargs) -> str:
        """执行量化

        Args:
            model_path: 原始模型路径
            output_path: 量化后模型保存路径
            **kwargs: 额外参数传递给 AutoRound

        Returns:
            量化后模型路径
        """
        try:
            from auto_round import AutoRound
        except ImportError:
            raise ImportError(
                "auto-round 未安装，请运行: pip install auto-round"
            )

        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"[auto-round] 加载模型: {model_path}")
        print(f"[auto-round] 配置: bits={self.config.bits}, group_size={self.config.group_size}, "
              f"seqlen={self.config.seqlen}, nsamples={self.config.nsamples}")
        print(f"[auto-round] 校准数据集: {self.dataset}")

        # 创建 AutoRound 实例
        autoround = AutoRound(
            model=model_path,
            scheme="W4A16" if self.config.bits == 4 else f"W{self.config.bits}A16",
            iters=self.iters,
            seqlen=self.config.seqlen,
            nsamples=self.config.nsamples,
            batch_size=self.config.batch_size,
            low_gpu_mem_usage=self.config.low_gpu_mem_usage,
            dataset=self.dataset,
            **kwargs,
        )

        print(f"[auto-round] 开始量化 (iters={self.iters})...")
        autoround.quantize()

        print(f"[auto-round] 保存到: {output_path}")
        autoround.save_quantized(str(output_path), format=self.format)

        print(f"[auto-round] 量化完成!")
        return str(output_path)
