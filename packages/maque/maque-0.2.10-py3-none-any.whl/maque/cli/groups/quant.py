"""量化命令组"""

from typing import Optional
from rich import print
from rich.console import Console
from rich.table import Table


class QuantGroup:
    """量化命令组

    提供模型量化功能，支持多种量化方案：
    - auto-round: Intel SGD 优化权重舍入 (推荐)
    - awq: Activation-aware Weight Quantization
    - gptq: 经典 GPTQ 量化
    - bnb-nf4: 4-bit NormalFloat 量化 (QLoRA)
    - bnb-int8: 8-bit 整数量化
    """

    def __init__(self, cli_instance):
        self.cli = cli_instance
        self.console = Console()

    def run(
        self,
        model: str,
        output: str = None,
        method: str = "auto-round",
        bits: int = 4,
        group_size: int = 128,
        iters: int = 200,
        seqlen: int = 512,
        nsamples: int = 256,
        batch_size: int = 4,
        low_gpu_mem: bool = True,
        dataset: str = "NeelNanda/pile-10k",
    ):
        """量化模型

        将模型量化为低精度格式，减少显存占用和提升推理速度。

        Args:
            model: 模型路径或 HuggingFace 模型名称
            output: 输出路径，默认为 {model}-{method}
            method: 量化方法 (auto-round/awq/gptq/bnb-nf4/bnb-int8)，默认 auto-round
            bits: 量化位数，默认 4
            group_size: 量化分组大小，默认 128
            iters: 优化迭代次数 (仅 auto-round)，默认 200
            seqlen: 校准序列长度，默认 512
            nsamples: 校准样本数，默认 256
            batch_size: 批次大小，默认 4
            low_gpu_mem: 低显存模式，默认 True
            dataset: 校准数据集 (仅 auto-round)，默认 NeelNanda/pile-10k

        Examples:
            maque quant run Qwen/Qwen3-4B
            maque quant run ./my-model --method=awq --output=./my-model-awq
            maque quant run ./model --dataset=wikitext2 --seqlen=4096
        """
        try:
            from maque.quantization import get_quantizer
        except ImportError as e:
            print(f"[red]无法导入量化模块: {e}[/red]")
            print("请确保已安装依赖: pip install maque[quant]")
            return

        # 设置默认输出路径
        if output is None:
            model_name = model.rstrip("/").split("/")[-1]
            output = f"{model_name}-{method}"

        print(f"[bold blue]模型量化[/bold blue]")
        print(f"  模型: [cyan]{model}[/cyan]")
        print(f"  输出: [green]{output}[/green]")
        print(f"  方法: [yellow]{method}[/yellow]")
        print(f"  精度: [yellow]{bits}-bit[/yellow]")
        print()

        try:
            # 根据方法设置参数
            kwargs = {
                "bits": bits,
                "group_size": group_size,
            }

            if method == "auto-round":
                kwargs.update({
                    "iters": iters,
                    "seqlen": seqlen,
                    "nsamples": nsamples,
                    "batch_size": batch_size,
                    "low_gpu_mem_usage": low_gpu_mem,
                    "dataset": dataset,
                })

            quantizer = get_quantizer(method, **kwargs)
            result_path = quantizer.quantize(model, output)

            print()
            print(f"[bold green]量化完成![/bold green]")
            print(f"  输出路径: [cyan]{result_path}[/cyan]")

        except Exception as e:
            print(f"[red]量化失败: {e}[/red]")
            raise

    def methods(self):
        """显示支持的量化方法

        列出所有可用的量化方法及其特点。

        Examples:
            maque quant methods
        """
        try:
            from maque.quantization import list_methods
        except ImportError:
            print("[red]无法导入量化模块[/red]")
            return

        print("[bold blue]支持的量化方法[/bold blue]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("方法", style="cyan", width=12)
        table.add_column("精度", style="green", width=8)
        table.add_column("库", style="yellow", width=15)
        table.add_column("描述", style="white")
        table.add_column("用途", style="dim")

        for name, info in list_methods().items():
            table.add_row(
                name,
                info["precision"],
                info["library"],
                info["description"],
                info["use_case"],
            )

        self.console.print(table)

        print("\n[dim]使用示例:[/dim]")
        print("  maque quant run Qwen/Qwen3-4B --method=auto-round")
        print("  maque quant run ./my-model --method=awq --output=./my-model-awq")

    def info(self, model: str):
        """显示模型的量化信息

        读取模型的量化配置信息。

        Args:
            model: 模型路径

        Examples:
            maque quant info ./Qwen3-4B-awq
        """
        from pathlib import Path
        import json

        model_path = Path(model)

        if not model_path.exists():
            print(f"[red]模型路径不存在: {model}[/red]")
            return

        print(f"[bold blue]模型量化信息[/bold blue]")
        print(f"  路径: [cyan]{model_path.resolve()}[/cyan]")
        print()

        # 检查 quantization_config.json
        quant_config_path = model_path / "quantization_config.json"
        config_path = model_path / "config.json"

        quant_info = None

        if quant_config_path.exists():
            with open(quant_config_path, "r") as f:
                quant_info = json.load(f)
        elif config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)
                quant_info = config.get("quantization_config")

        if quant_info:
            print("[green]已量化[/green]")
            print()

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("配置项", style="cyan")
            table.add_column("值", style="yellow")

            for key, value in quant_info.items():
                table.add_row(str(key), str(value))

            self.console.print(table)
        else:
            print("[yellow]未检测到量化配置，可能是原始模型[/yellow]")

        # 显示模型文件大小
        print()
        total_size = 0
        safetensors_files = list(model_path.glob("*.safetensors"))
        bin_files = list(model_path.glob("*.bin"))

        model_files = safetensors_files or bin_files
        for f in model_files:
            total_size += f.stat().st_size

        if total_size > 0:
            size_gb = total_size / (1024 ** 3)
            print(f"  模型大小: [cyan]{size_gb:.2f} GB[/cyan]")
