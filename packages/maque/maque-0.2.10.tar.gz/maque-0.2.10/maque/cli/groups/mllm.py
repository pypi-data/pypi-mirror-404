"""MLLM (多模态大语言模型) 命令组"""

import os
import sys

# 强制启用颜色支持
os.environ["FORCE_COLOR"] = "1"
if not os.environ.get("TERM"):
    os.environ["TERM"] = "xterm-256color"

from rich.console import Console
from rich import print
from rich.markdown import Markdown

console = Console(
    force_terminal=True,
    width=100,
    color_system="windows",
    legacy_windows=True,
    safe_box=True
)


def safe_print(*args, **kwargs):
    """安全的打印函数，确保在所有终端中正确显示颜色"""
    try:
        console.print(*args, **kwargs)
    except Exception:
        # 降级到普通print，处理编码问题
        import re
        import sys
        import builtins

        clean_args = []
        for arg in args:
            if isinstance(arg, str):
                # 去除rich markup
                clean_arg = re.sub(r"\[/?[^\]]*\]", "", str(arg))
                # 处理emoji和特殊字符
                try:
                    # 尝试编码为gbk (Windows默认编码)
                    clean_arg.encode('gbk')
                    clean_args.append(clean_arg)
                except UnicodeEncodeError:
                    # 如果包含无法编码的字符，替换emoji为文本描述
                    clean_arg = re.sub(r'❌', '[错误]', clean_arg)
                    clean_arg = re.sub(r'✅', '[成功]', clean_arg)
                    clean_arg = re.sub(r'💡', '[提示]', clean_arg)
                    clean_arg = re.sub(r'🚀', '[启动]', clean_arg)
                    clean_arg = re.sub(r'📦', '[模型]', clean_arg)
                    clean_arg = re.sub(r'🌐', '[服务器]', clean_arg)
                    clean_arg = re.sub(r'👋', '[再见]', clean_arg)
                    clean_arg = re.sub(r'📝', '[记录]', clean_arg)
                    clean_arg = re.sub(r'⚠️', '[警告]', clean_arg)
                    clean_arg = re.sub(r'🔍', '[搜索]', clean_arg)
                    clean_arg = re.sub(r'🤖', '[机器人]', clean_arg)
                    clean_arg = re.sub(r'📡', '[网络]', clean_arg)
                    clean_arg = re.sub(r'🔌', '[连接]', clean_arg)
                    clean_arg = re.sub(r'📋', '[配置]', clean_arg)
                    clean_arg = re.sub(r'📁', '[文件]', clean_arg)
                    clean_arg = re.sub(r'🔧', '[设置]', clean_arg)
                    clean_arg = re.sub(r'🎯', '[目标]', clean_arg)
                    clean_arg = re.sub(r'📊', '[统计]', clean_arg)
                    clean_arg = re.sub(r'🧠', '[思考]', clean_arg)
                    clean_arg = re.sub(r'💭', '[推理]', clean_arg)
                    clean_arg = re.sub(r'🔗', '[逻辑]', clean_arg)
                    # 移除其他无法显示的emoji
                    clean_arg = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF]', '', clean_arg)
                    clean_args.append(clean_arg)
            else:
                clean_args.append(str(arg))

        # 使用内置print
        try:
            builtins.print(*clean_args, **kwargs)
        except UnicodeEncodeError:
            # 最后的降级：使用错误替换
            safe_args = [arg.encode('gbk', errors='replace').decode('gbk') if isinstance(arg, str) else arg for arg in clean_args]
            builtins.print(*safe_args, **kwargs)


def safe_print_stream(text, **kwargs):
    """安全的流式打印函数，用于流式输出

    默认使用原生 print 实现真正的流式输出，避免 Rich console 的格式化干扰。
    """
    import builtins

    flush = kwargs.pop('flush', True)  # 流式输出默认 flush
    end = kwargs.pop('end', '')  # 流式输出默认不换行

    try:
        builtins.print(text, end=end, flush=flush, **kwargs)
    except UnicodeEncodeError:
        # 编码失败时，尝试使用 stdout buffer
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout.buffer.write(text.encode('utf-8', errors='replace'))
            if flush:
                sys.stdout.buffer.flush()
        else:
            # 最后的降级方案：替换无法编码的字符
            safe_text = text.encode('gbk', errors='replace').decode('gbk')
            builtins.print(safe_text, end=end, flush=flush, **kwargs)


def safe_print_markdown(content, **kwargs):
    """安全的Markdown渲染函数"""
    try:
        # 使用Rich的Markdown渲染
        markdown = Markdown(content)
        console.print(markdown, **kwargs)
    except Exception:
        # 降级到普通打印
        safe_print(content, **kwargs)


class StreamingMarkdownRenderer:
    """流式Markdown渲染器 - 实时解析并渲染Markdown"""

    def __init__(self):
        self.buffer = ""
        self.last_rendered_length = 0
        self.in_code_block = False
        self.code_block_lang = ""

    def add_token(self, token):
        """添加新token并尝试渲染"""
        self.buffer += token
        self._try_render_incremental()

    def _try_render_incremental(self):
        """尝试增量渲染Markdown"""
        # 检测代码块
        if "```" in self.buffer[self.last_rendered_length:]:
            code_block_matches = self.buffer.count("```")
            self.in_code_block = (code_block_matches % 2) == 1

        # 如果在代码块中，直接输出原始文本
        if self.in_code_block:
            new_content = self.buffer[self.last_rendered_length:]
            if new_content:
                safe_print_stream(new_content, end="", flush=True)
                self.last_rendered_length = len(self.buffer)
            return

        # 尝试找到可以安全渲染的边界（句子、段落等）
        render_boundary = self._find_render_boundary()
        if render_boundary > self.last_rendered_length:
            content_to_render = self.buffer[self.last_rendered_length:render_boundary]
            self._render_content(content_to_render)
            self.last_rendered_length = render_boundary

    def _find_render_boundary(self):
        """找到适合渲染的边界位置"""
        content = self.buffer

        # 寻找句子结束标记
        for i in range(len(content) - 1, self.last_rendered_length - 1, -1):
            char = content[i]
            # 句子结束
            if char in '.!?。！？':
                # 确保后面有空格或换行，避免误判小数点等
                if i + 1 < len(content) and content[i + 1] in ' \n\t':
                    return i + 1
            # 段落结束
            elif char == '\n' and (i + 1 >= len(content) or content[i + 1] == '\n'):
                return i + 1

        # 如果没有找到合适的边界，返回当前长度（不渲染）
        return self.last_rendered_length

    def _render_content(self, content):
        """渲染内容片段"""
        if not content.strip():
            safe_print_stream(content, end="", flush=True)
            return

        # 简单的行内Markdown渲染
        try:
            # 检查是否包含Markdown元素
            if any(marker in content for marker in ['**', '*', '`', '#', '-', '1.']):
                # 简单的实时渲染，只处理基本元素
                rendered = self._simple_markdown_render(content)
                safe_print_stream(rendered, end="", flush=True)
            else:
                # 纯文本直接输出
                safe_print_stream(content, end="", flush=True)
        except Exception:
            # 出错时降级到原始文本
            safe_print_stream(content, end="", flush=True)

    def _simple_markdown_render(self, content):
        """简单的Markdown渲染 - 只处理基本格式"""
        import re

        # 粗体 **text**
        content = re.sub(r'\*\*([^\*]+)\*\*', r'[bold]\1[/bold]', content)
        # 斜体 *text*
        content = re.sub(r'\*([^\*]+)\*', r'[italic]\1[/italic]', content)
        # 行内代码 `code`
        content = re.sub(r'`([^`]+)`', r'[code]\1[/code]', content)

        return content

    def finalize(self):
        """完成渲染，处理剩余内容"""
        if self.last_rendered_length < len(self.buffer):
            remaining = self.buffer[self.last_rendered_length:]
            self._render_content(remaining)

        safe_print_stream("", end="\n")  # 换行


def safe_print_stream_markdown(content, is_complete=False, **kwargs):
    """流式Markdown渲染函数，累积内容后渲染"""
    if is_complete:
        # 完整内容，进行Markdown渲染
        try:
            markdown = Markdown(content)
            console.print(markdown, **kwargs)
        except Exception:
            safe_print_stream(content, **kwargs)
    else:
        # 流式输出，直接打印原始文本
        safe_print_stream(content, **kwargs)


def get_user_input(prompt_text="You"):
    """获取用户输入，支持Rich格式的提示"""
    try:
        # 使用console.input来支持Rich格式
        return console.input(f"[bold yellow]{prompt_text}:[/bold yellow] ")
    except Exception:
        # 降级到普通input
        return input(f"{prompt_text}: ")


class AdvancedInput:
    """高级输入处理器，支持多行输入（Alt+Enter 换行）"""

    def __init__(self):
        self._use_prompt_toolkit = False
        self._bindings = None
        self._init_prompt_toolkit()

    def _init_prompt_toolkit(self):
        """初始化 prompt_toolkit 的键绑定"""
        try:
            from prompt_toolkit.key_binding import KeyBindings
            from prompt_toolkit.keys import Keys

            # 创建快捷键绑定
            self._bindings = KeyBindings()

            @self._bindings.add(Keys.Enter)
            def _(event):
                """Enter 提交输入"""
                event.current_buffer.validate_and_handle()

            # Alt+Enter (Escape + Enter) 换行 - 最可靠的方式
            @self._bindings.add('escape', 'enter')
            def _(event):
                """Alt+Enter 换行"""
                event.current_buffer.insert_text('\n')

            self._use_prompt_toolkit = True
        except ImportError:
            self._use_prompt_toolkit = False

    def _sync_prompt(self, prompt_text: str) -> str:
        """同步调用 prompt_toolkit（在单独线程中运行）"""
        from prompt_toolkit import prompt as pt_prompt
        return pt_prompt(
            f"{prompt_text}: ",
            key_bindings=self._bindings,
            multiline=False,
        )

    def get_input(self, prompt_text="You") -> str:
        """获取用户输入，支持多行（同步版本）"""
        if self._use_prompt_toolkit:
            try:
                return self._sync_prompt(prompt_text)
            except (KeyboardInterrupt, EOFError):
                raise
            except Exception:
                # 出错时降级到基本输入
                self._use_prompt_toolkit = False

        # Fallback 到基本输入
        return get_user_input(prompt_text)

    async def get_input_async(self, prompt_text="You") -> str:
        """获取用户输入，支持多行（异步版本，在单独线程中运行）"""
        if self._use_prompt_toolkit:
            try:
                import asyncio
                # 在单独线程中运行 prompt_toolkit，避免与 asyncio 冲突
                return await asyncio.to_thread(self._sync_prompt, prompt_text)
            except (KeyboardInterrupt, EOFError):
                raise
            except Exception:
                # 出错时降级到基本输入
                self._use_prompt_toolkit = False

        # Fallback 到基本输入
        return get_user_input(prompt_text)


class ChatCommands:
    """聊天快捷命令处理器"""

    COMMANDS = {
        '/clear': '清空对话历史',
        '/retry': '重新生成上一条回复',
        '/save': '保存对话到文件 (用法: /save [文件名])',
        '/model': '切换模型 (用法: /model [模型名])',
        '/help': '显示帮助信息',
    }

    @classmethod
    def is_command(cls, text: str) -> bool:
        """检查是否是命令"""
        return text.strip().startswith('/')

    @classmethod
    def parse(cls, text: str) -> tuple:
        """解析命令，返回 (命令名, 参数列表)"""
        parts = text.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        return cmd, args

    @classmethod
    def show_help(cls):
        """显示帮助信息"""
        safe_print("\n[bold cyan]📋 可用命令:[/bold cyan]")
        for cmd, desc in cls.COMMANDS.items():
            safe_print(f"  [green]{cmd:12}[/green] - {desc}")
        safe_print("")

    @classmethod
    def handle_clear(cls, messages: list, system_prompt: str = None) -> list:
        """清空对话历史"""
        new_messages = []
        if system_prompt:
            new_messages.append({"role": "system", "content": system_prompt})
        safe_print("[dim]🗑️  对话历史已清空[/dim]\n")
        return new_messages

    @classmethod
    def handle_save(cls, messages: list, filename: str = None):
        """保存对话到文件"""
        import json
        from datetime import datetime

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_{timestamp}.json"

        if not filename.endswith('.json'):
            filename += '.json'

        # 过滤掉系统消息，只保存用户和助手的对话
        chat_history = [
            msg for msg in messages
            if msg.get('role') in ['user', 'assistant']
        ]

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'saved_at': datetime.now().isoformat(),
                    'messages': chat_history
                }, f, ensure_ascii=False, indent=2)
            safe_print(f"[green]💾 对话已保存到: {filename}[/green]\n")
        except Exception as e:
            safe_print(f"[red]❌ 保存失败: {e}[/red]\n")

    @classmethod
    def handle_retry(cls, messages: list) -> tuple:
        """准备重试：移除最后一条助手回复，返回是否需要重试"""
        if len(messages) < 2:
            safe_print("[yellow]⚠️  没有可以重试的回复[/yellow]\n")
            return messages, False

        # 找到最后一条助手消息并移除
        if messages[-1].get('role') == 'assistant':
            messages.pop()
            safe_print("[dim]🔄 正在重新生成...[/dim]")
            return messages, True
        else:
            safe_print("[yellow]⚠️  最后一条不是助手回复，无法重试[/yellow]\n")
            return messages, False


class MllmGroup:
    """MLLM命令组 - 统一管理多模态大语言模型相关功能"""

    def __init__(self, cli_instance):
        self.cli = cli_instance

    def call_table(
        self,
        table_path: str,
        model: str = None,
        base_url: str = None,
        api_key: str = None,
        image_col: str = "image",
        system_prompt: str = "你是一个专业的图像识别专家。",
        text_prompt: str = "请描述这张图像。",
        system_prompt_file: str = None,
        text_prompt_file: str = None,
        sheet_name: str = 0,
        max_num=None,
        output_file: str = "table_results.csv",
        temperature: float = 0.1,
        max_tokens: int = 2000,
        concurrency_limit: int = 10,
        max_qps: int = 50,
        retry_times: int = 3,
        skip_existing: bool = False,
        **kwargs,
    ):
        """对表格中的图像列进行批量大模型识别和分析

        Args:
            table_path: 表格文件路径 (xlsx/csv)
            model: 模型名称
            base_url: API服务地址
            api_key: API密钥
            image_col: 图片列名
            system_prompt: 系统提示词
            text_prompt: 文本提示词
            system_prompt_file: 系统提示词文件路径（优先于 system_prompt）
            text_prompt_file: 文本提示词文件路径（优先于 text_prompt）
            sheet_name: sheet名称
            max_num: 最大处理数量
            output_file: 输出文件路径
            temperature: 温度参数
            max_tokens: 最大token数
            concurrency_limit: 并发限制
            max_qps: 最大QPS
            retry_times: 重试次数
            skip_existing: 是否跳过已有结果的行（断点续传）
        """
        import asyncio
        import pandas as pd
        import os
        from flexllm.mllm_client import MllmClient

        # 从配置文件获取默认值
        mllm_config = self.cli.maque_config.get("mllm", {})
        model = model or mllm_config.get("model", "gemma3:latest")
        base_url = base_url or mllm_config.get("base_url", "http://localhost:11434/v1")
        api_key = api_key or mllm_config.get("api_key", "EMPTY")

        # 从文件读取 prompt（如果指定）
        if system_prompt_file and os.path.exists(system_prompt_file):
            with open(system_prompt_file, 'r', encoding='utf-8') as f:
                system_prompt = f.read().strip()
            safe_print(f"[dim]📄 从文件加载 system_prompt: {system_prompt_file}[/dim]")

        if text_prompt_file and os.path.exists(text_prompt_file):
            with open(text_prompt_file, 'r', encoding='utf-8') as f:
                text_prompt = f.read().strip()
            safe_print(f"[dim]📄 从文件加载 text_prompt: {text_prompt_file}[/dim]")

        async def run_call_table():
            try:
                safe_print(f"\n[bold green]📊 开始批量处理表格[/bold green]")
                safe_print(f"[cyan]📁 文件: {table_path}[/cyan]")
                safe_print(f"[dim]🔧 模型: {model} | 并发: {concurrency_limit} | QPS: {max_qps}[/dim]")

                # 初始化客户端
                client = MllmClient(
                    model=model,
                    base_url=base_url,
                    api_key=api_key,
                    concurrency_limit=concurrency_limit,
                    max_qps=max_qps,
                    retry_times=retry_times,
                    **kwargs,
                )

                # 加载数据
                if table_path.endswith(".xlsx"):
                    df = pd.read_excel(table_path, sheet_name=sheet_name)
                else:
                    df = pd.read_csv(table_path)

                total_rows = len(df)
                if max_num:
                    df = df.head(max_num)

                safe_print(f"[dim]📝 总行数: {total_rows}, 处理行数: {len(df)}[/dim]")

                # 检查并创建结果列
                result_col = "mllm_result"
                if result_col not in df.columns:
                    df[result_col] = None

                # 断点续传：过滤已有结果的行
                if skip_existing and os.path.exists(output_file):
                    existing_df = pd.read_csv(output_file) if output_file.endswith('.csv') else pd.read_excel(output_file)
                    if result_col in existing_df.columns:
                        # 合并已有结果
                        df[result_col] = existing_df[result_col] if len(existing_df) == len(df) else df[result_col]
                        safe_print(f"[yellow]⏭️  断点续传: 检测到已有结果文件[/yellow]")

                # 找出需要处理的行
                if skip_existing:
                    pending_mask = df[result_col].isna() | (df[result_col] == '') | (df[result_col] == 'None')
                    pending_indices = df[pending_mask].index.tolist()
                else:
                    pending_indices = df.index.tolist()

                if not pending_indices:
                    safe_print(f"[green]✅ 所有行已处理完成，无需重新处理[/green]")
                    return

                safe_print(f"[cyan]🔄 待处理: {len(pending_indices)} 行[/cyan]")

                # 构建待处理的 messages
                messages_list = []
                for idx in pending_indices:
                    row = df.loc[idx]
                    messages = []
                    if system_prompt:
                        messages.append({"role": "system", "content": system_prompt})
                    messages.append({
                        "role": "user",
                        "content": [
                            {"type": "text", "text": text_prompt},
                            {"type": "image_url", "image_url": {"url": str(row[image_col])}},
                        ],
                    })
                    messages_list.append(messages)

                # 调用 MLLM
                results = await client.call_llm(
                    messages_list,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                # 填充结果
                for i, idx in enumerate(pending_indices):
                    df.at[idx, result_col] = results[i] if i < len(results) else None

                # 保存结果
                if output_file.endswith('.csv'):
                    df.to_csv(output_file, index=False, encoding='utf-8-sig')
                else:
                    df.to_excel(output_file, index=False)

                safe_print(f"\n[bold green]✅ 处理完成！结果已保存到: {output_file}[/bold green]")

                # 统计
                success_count = df[result_col].notna().sum()
                safe_print(f"[dim]📊 成功: {success_count}/{len(df)}[/dim]")

            except Exception as e:
                safe_print(f"[red]❌ 处理失败: {e}[/red]")
                import traceback
                traceback.print_exc()

        return asyncio.run(run_call_table())

    def call_images(
        self,
        folder_path: str,
        model: str = None,
        base_url: str = None,
        api_key: str = None,
        system_prompt: str = "你是一个专业的图像识别专家。",
        text_prompt: str = "请描述这张图像。",
        system_prompt_file: str = None,
        text_prompt_file: str = None,
        recursive: bool = True,
        max_num: int = None,
        extensions: str = None,
        output_file: str = "results.csv",
        temperature: float = 0.1,
        max_tokens: int = 2000,
        concurrency_limit: int = 10,
        max_qps: int = 50,
        retry_times: int = 3,
        skip_existing: bool = False,
        **kwargs,
    ):
        """对文件夹中的图像进行批量大模型识别和分析

        Args:
            folder_path: 文件夹路径
            model: 模型名称
            base_url: API服务地址
            api_key: API密钥
            system_prompt: 系统提示词
            text_prompt: 文本提示词
            system_prompt_file: 系统提示词文件路径（优先于 system_prompt）
            text_prompt_file: 文本提示词文件路径（优先于 text_prompt）
            recursive: 是否递归扫描子文件夹
            max_num: 最大处理数量
            extensions: 支持的文件扩展名（逗号分隔，如 "jpg,png,webp"）
            output_file: 输出文件路径
            temperature: 温度参数
            max_tokens: 最大token数
            concurrency_limit: 并发限制
            max_qps: 最大QPS
            retry_times: 重试次数
            skip_existing: 是否跳过已处理的图片（断点续传）
        """
        import asyncio
        import pandas as pd
        import os
        from pathlib import Path
        from flexllm.mllm_client import MllmClient

        # 从配置文件获取默认值
        mllm_config = self.cli.maque_config.get("mllm", {})
        model = model or mllm_config.get("model", "gemma3:latest")
        base_url = base_url or mllm_config.get("base_url", "http://localhost:11434/v1")
        api_key = api_key or mllm_config.get("api_key", "EMPTY")

        # 从文件读取 prompt（如果指定）
        if system_prompt_file and os.path.exists(system_prompt_file):
            with open(system_prompt_file, 'r', encoding='utf-8') as f:
                system_prompt = f.read().strip()
            safe_print(f"[dim]📄 从文件加载 system_prompt: {system_prompt_file}[/dim]")

        if text_prompt_file and os.path.exists(text_prompt_file):
            with open(text_prompt_file, 'r', encoding='utf-8') as f:
                text_prompt = f.read().strip()
            safe_print(f"[dim]📄 从文件加载 text_prompt: {text_prompt_file}[/dim]")

        # 解析扩展名
        ext_set = None
        if extensions:
            ext_set = {f".{ext.strip().lower().lstrip('.')}" for ext in extensions.split(',')}

        async def run_call_images():
            try:
                safe_print(f"\n[bold green]📁 开始批量处理文件夹图片[/bold green]")
                safe_print(f"[cyan]📂 路径: {folder_path}[/cyan]")
                safe_print(f"[dim]🔧 模型: {model} | 并发: {concurrency_limit} | QPS: {max_qps}[/dim]")

                # 初始化客户端
                client = MllmClient(
                    model=model,
                    base_url=base_url,
                    api_key=api_key,
                    concurrency_limit=concurrency_limit,
                    max_qps=max_qps,
                    retry_times=retry_times,
                    **kwargs,
                )

                # 扫描图片文件
                image_files = client.folder.scan_folder_images(
                    folder_path=folder_path,
                    recursive=recursive,
                    max_num=max_num,
                    extensions=ext_set,
                )

                if not image_files:
                    safe_print(f"[yellow]⚠️  未找到图片文件[/yellow]")
                    return

                # 创建结果 DataFrame
                df = pd.DataFrame({'image_path': image_files})
                result_col = "mllm_result"
                df[result_col] = None

                # 断点续传：加载已有结果
                processed_paths = set()
                if skip_existing and os.path.exists(output_file):
                    try:
                        existing_df = pd.read_csv(output_file) if output_file.endswith('.csv') else pd.read_excel(output_file)
                        if 'image_path' in existing_df.columns and result_col in existing_df.columns:
                            # 创建路径到结果的映射
                            for _, row in existing_df.iterrows():
                                path = row['image_path']
                                result = row[result_col]
                                if pd.notna(result) and result != '' and result != 'None':
                                    processed_paths.add(path)
                                    # 更新 df 中对应行的结果
                                    mask = df['image_path'] == path
                                    if mask.any():
                                        df.loc[mask, result_col] = result
                            safe_print(f"[yellow]⏭️  断点续传: 已处理 {len(processed_paths)} 个文件[/yellow]")
                    except Exception as e:
                        safe_print(f"[yellow]⚠️  读取已有结果失败: {e}[/yellow]")

                # 找出需要处理的文件
                pending_indices = []
                for idx, row in df.iterrows():
                    if row['image_path'] not in processed_paths:
                        pending_indices.append(idx)

                if not pending_indices:
                    safe_print(f"[green]✅ 所有图片已处理完成，无需重新处理[/green]")
                    return

                safe_print(f"[cyan]🔄 待处理: {len(pending_indices)} 个图片[/cyan]")

                # 构建 messages
                messages_list = []
                pending_files = []
                for idx in pending_indices:
                    image_path = df.loc[idx, 'image_path']
                    pending_files.append(image_path)
                    messages = []
                    if system_prompt:
                        messages.append({"role": "system", "content": system_prompt})
                    messages.append({
                        "role": "user",
                        "content": [
                            {"type": "text", "text": text_prompt},
                            {"type": "image_url", "image_url": {"url": f"file://{image_path}"}},
                        ],
                    })
                    messages_list.append(messages)

                # 调用 MLLM
                results = await client.call_llm(
                    messages_list,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                # 填充结果
                for i, idx in enumerate(pending_indices):
                    df.at[idx, result_col] = results[i] if i < len(results) else None

                # 保存结果
                if output_file.endswith('.csv'):
                    df.to_csv(output_file, index=False, encoding='utf-8-sig')
                else:
                    df.to_excel(output_file, index=False)

                safe_print(f"\n[bold green]✅ 处理完成！结果已保存到: {output_file}[/bold green]")

                # 统计
                success_count = df[result_col].notna().sum()
                safe_print(f"[dim]📊 成功: {success_count}/{len(df)}[/dim]")

            except Exception as e:
                safe_print(f"[red]❌ 处理失败: {e}[/red]")
                import traceback
                traceback.print_exc()

        return asyncio.run(run_call_images())


    def eval(
        self,
        result_file: str,
        source: str = None,
        response_col: str = "content",
        label_col: str = None,
        extract: str = "direct",
        sep: str = None,
        mapping: str = None,
        output_dir: str = "record",
    ):
        """对 batch 输出的 .jsonl 文件进行解析 + 指标计算

        两阶段解析流程：
          阶段1（自动）：去除 <think>...</think>，提取 ```json...``` 代码块
          阶段2（--extract 指定）：管道式提取，支持 " | " 分隔的算子组合

        可用算子：
          direct          原样返回
          tag:标签名      提取 XML 标签内容
          json_key:key    从 JSON 提取 key
          index:N         按 --sep 分割取第 N 项
          line:N          取第 N 行（支持负数，-1=最后一行）
          lines           拆为多行，每行独立走后续管道
          regex:pattern   正则匹配，取第一个捕获组

        Args:
            result_file: batch 输出的 .jsonl 文件路径
            source: 原始输入 .jsonl，按行号对齐合并（当 result_file 不含 label 时使用）
            response_col: 模型响应所在的字段名（支持点号嵌套，如 metadata.content_label）
            label_col: 标签字段名（不指定时自动检测，支持点号嵌套）
            extract: 管道式提取规则，算子间用 " | " 分隔
            sep: 配合 index 算子使用的分隔符
            mapping: 值映射，格式 "k1:v1,k2:v2"，对 pred 和 label 做映射
            output_dir: 指标报告输出目录

        Examples:
            maque mllm eval result.jsonl --label_col=label
            maque mllm eval result.jsonl --extract="tag:一级标签"
            maque mllm eval result.jsonl --extract="index:1" --sep="|"
            maque mllm eval result.jsonl --extract="lines | index:1" --sep="|"
            maque mllm eval result.jsonl --extract="line:-1 | index:1" --sep="|"
            maque mllm eval result.jsonl --extract="json_key:result | index:0" --sep=","
            maque mllm eval result.jsonl --extract="regex:risk_level=(\\w+)"
        """
        import pandas as pd
        from maque.io import jsonl_load
        from maque.nlp.parser import strip_think_tags, extract_code_snippets
        from maque.utils.helper_parser import parse_generic_tags
        from maque.ai_platform.metrics import export_eval_report

        def resolve_nested_col(df, col_name):
            """解析点号嵌套字段，如 'metadata.content_label' → 从 df['metadata'] dict 列取 content_label"""
            if "." not in col_name:
                return col_name, col_name in df.columns
            parts = col_name.split(".", 1)
            root, sub_key = parts[0], parts[1]
            if root not in df.columns:
                return col_name, False
            # 展开嵌套字段到新列
            resolved_name = col_name.replace(".", "__")
            def _get_nested(val):
                if isinstance(val, dict):
                    # 支持多级嵌套
                    keys = sub_key.split(".")
                    cur = val
                    for k in keys:
                        if isinstance(cur, dict):
                            cur = cur.get(k)
                        else:
                            return None
                    return cur
                return None
            df[resolved_name] = df[root].apply(_get_nested)
            return resolved_name, True

        def parse_mapping(mapping_str):
            """解析 'k1:v1,k2:v2' 格式的映射"""
            m = {}
            for pair in mapping_str.split(","):
                pair = pair.strip()
                if ":" in pair:
                    k, v = pair.split(":", 1)
                    m[k.strip()] = v.strip()
            return m

        # --- 加载数据 ---
        data = jsonl_load(result_file)
        df = pd.DataFrame(data)
        safe_print(f"[cyan]加载 {result_file}，共 {len(df)} 条[/cyan]")

        # 合并 source 文件
        if source:
            source_data = jsonl_load(source)
            source_df = pd.DataFrame(source_data)
            if len(source_df) != len(df):
                safe_print(f"[red]行数不一致: result={len(df)}, source={len(source_df)}[/red]")
                return
            # 将 source 中不存在于 df 的列合并过来
            for col in source_df.columns:
                if col not in df.columns:
                    df[col] = source_df[col].values
            safe_print(f"[dim]已合并 source 文件: {source}[/dim]")

        # --- 解析 response_col（支持嵌套）---
        response_col, found = resolve_nested_col(df, response_col)
        if not found:
            safe_print(f"[red]响应列 '{response_col}' 不存在。可用列: {list(df.columns)}[/red]")
            return

        # --- 自动检测 label_col ---
        if label_col is None:
            candidates = ["label", "labels", "content_label", "target", "ground_truth", "answer"]
            for c in candidates:
                if c in df.columns:
                    label_col = c
                    break
            # 顶层找不到时，搜索 dict 类型列的嵌套 key
            if label_col is None:
                for col in df.columns:
                    sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                    if isinstance(sample, dict):
                        for c in candidates:
                            if c in sample:
                                label_col = f"{col}.{c}"
                                break
                    if label_col is not None:
                        break
            if label_col is None:
                safe_print(f"[red]未找到标签列，请通过 --label_col 指定。可用列: {list(df.columns)}[/red]")
                return

        # 解析 label_col（支持嵌套）
        label_col, found = resolve_nested_col(df, label_col)
        if not found:
            safe_print(f"[red]标签列 '{label_col}' 不存在。可用列: {list(df.columns)}[/red]")
            return

        safe_print(f"[dim]response_col={response_col}, label_col={label_col}, extract={extract}[/dim]")

        # --- 阶段1：自动清洗 ---
        def stage1_clean(text):
            if not isinstance(text, str):
                return str(text) if text is not None else ""
            text = strip_think_tags(text)
            # 尝试提取代码块内容
            snippets = extract_code_snippets(text)
            if snippets:
                return snippets[-1]["code"]
            return text.strip()

        # --- 阶段2：管道式提取 ---
        def parse_pipeline(extract_str):
            """解析管道表达式，按 ' | ' 分割"""
            return [op.strip() for op in extract_str.split(" | ") if op.strip()]

        def apply_op(text, op):
            """对单个字符串执行单个算子"""
            if op == "direct":
                return text
            elif op.startswith("tag:"):
                tag_name = op[4:]
                tags = parse_generic_tags(text)
                return tags.get(tag_name, text)
            elif op.startswith("json_key:"):
                key = op[9:]
                try:
                    import json5
                    obj = json5.loads(text)
                except Exception:
                    try:
                        import json
                        obj = json.loads(text)
                    except Exception:
                        return text
                if isinstance(obj, dict):
                    return str(obj.get(key, text))
                return text
            elif op.startswith("index:"):
                idx = int(op[6:])
                delimiter = sep if sep else ","
                parts = text.split(delimiter)
                if 0 <= idx < len(parts):
                    return parts[idx].strip()
                return text
            elif op.startswith("line:"):
                n = int(op[5:])
                text_lines = [l.strip() for l in text.splitlines() if l.strip()]
                if text_lines and -len(text_lines) <= n < len(text_lines):
                    return text_lines[n]
                return text
            elif op.startswith("regex:"):
                import re
                pattern = op[6:]
                m = re.search(pattern, text)
                if m:
                    return m.group(1) if m.lastindex else m.group(0)
                return text
            else:
                safe_print(f"[yellow]未知算子: {op}，跳过[/yellow]")
                return text

        def run_pipeline(text, ops):
            """执行管道，处理 lines 展开"""
            if "lines" in ops:
                pos = ops.index("lines")
                # lines 前面的算子先执行
                for op in ops[:pos]:
                    text = apply_op(text, op)
                # 展开为多行
                items = [l.strip() for l in text.splitlines() if l.strip()]
                # 每行独立走后续管道
                rest_ops = ops[pos + 1:]
                results = []
                for item in items:
                    for op in rest_ops:
                        item = apply_op(item, op)
                    results.append(item)
                if not results:
                    return text
                return results if len(results) > 1 else results[0]
            else:
                for op in ops:
                    text = apply_op(text, op)
                return text

        # 执行两阶段解析
        ops = parse_pipeline(extract)
        pred_col = "__pred__"
        df[pred_col] = df[response_col].apply(lambda x: run_pipeline(stage1_clean(x), ops))

        # --- mapping 阶段 ---
        if mapping:
            m = parse_mapping(mapping)
            # mapping 中值的出现顺序决定优先级，后出现的优先级更高
            priority = {}
            for i, v in enumerate(m.values()):
                priority[v] = i

            def map_value(x):
                if isinstance(x, list):
                    mapped = [m.get(v, v) for v in x]
                    return max(mapped, key=lambda v: priority.get(v, -1))
                return m.get(x, x) if isinstance(x, str) else m.get(str(x), x)

            df[pred_col] = df[pred_col].apply(map_value)
            df[label_col] = df[label_col].apply(map_value)

        # 将 pred 和 label 都转为字符串以确保可比较
        df[pred_col] = df[pred_col].apply(lambda x: str(x).strip() if not isinstance(x, str) else x.strip())
        df[label_col] = df[label_col].apply(lambda x: str(x).strip() if not isinstance(x, str) else x.strip())

        # --- 调用 export_eval_report ---
        safe_print(f"\n[bold green]评估结果[/bold green]")
        export_eval_report(df, pred_col=pred_col, label_col=label_col, record_folder=output_dir)

    # ========== chat, models, test 已移至 flexllm CLI ==========
    # 请使用以下命令替代:
    #   flexllm chat      - 交互式对话
    #   flexllm models    - 列出可用模型
    #   flexllm test      - 测试服务连接
    # ============================================================

    def chain_analysis(
        self,
        query: str,
        steps: int = 3,
        model: str = None,
        base_url: str = None,
        api_key: str = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
        show_details: bool = False,
        **kwargs,
    ):
        """使用Chain of Thought进行分析推理
        
        Args:
            query: 要分析的问题或内容
            steps: 分析步骤数，默认3步
            model: 使用的模型
            base_url: API服务地址
            api_key: API密钥
            temperature: 温度参数
            max_tokens: 最大token数
            show_details: 是否显示每个步骤的详细信息
        """
        import asyncio
        from flexllm.chain_of_thought_client import ChainOfThoughtClient, LinearStep, ExecutionConfig
        from flexllm.openaiclient import OpenAIClient

        # 从配置获取默认值
        mllm_config = self.cli.maque_config.get("mllm", {})
        model = model or mllm_config.get("model", "gemma3:latest")
        base_url = base_url or mllm_config.get("base_url", "http://localhost:11434/v1")
        api_key = api_key or mllm_config.get("api_key", "EMPTY")

        async def run_chain_analysis():
            try:
                safe_print(f"[bold green]🔍 开始Chain of Thought分析推理[/bold green]")
                safe_print(f"[cyan]📝 问题: {query}[/cyan]")
                safe_print(f"[dim]🔧 模型: {model}, 步骤数: {steps}[/dim]\n")

                # 初始化客户端
                openai_client = OpenAIClient(model=model, base_url=base_url, api_key=api_key)
                
                # 配置执行参数
                config = ExecutionConfig(
                    enable_monitoring=True,
                    enable_progress=show_details,
                    log_level="INFO" if show_details else "WARNING"
                )
                
                chain_client = ChainOfThoughtClient(openai_client, config)

                # 定义分析步骤
                def create_analysis_step(step_num: int, step_name: str, prompt_template: str):
                    def prepare_messages(context):
                        previous_analysis = ""
                        if context.history:
                            previous_analysis = "\n\n".join([
                                f"步骤{i+1}: {step.response}" 
                                for i, step in enumerate(context.history)
                            ])
                        
                        system_prompt = f"""你是一个专业的分析师，正在进行第{step_num}步分析。
请根据问题和之前的分析结果，{step_name}。
保持逻辑清晰，分析深入。"""

                        user_prompt = prompt_template.format(
                            query=context.query,
                            previous_analysis=previous_analysis
                        )

                        return [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]
                    
                    return LinearStep(
                        name=f"analysis_step_{step_num}",
                        prepare_messages_fn=prepare_messages,
                        model_params={
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            **kwargs
                        }
                    )

                # 创建分析链条
                analysis_steps = []
                
                if steps >= 1:
                    analysis_steps.append(create_analysis_step(
                        1, "理解和分解问题",
                        "请仔细分析这个问题：\n{query}\n\n请分解这个问题的关键要素，明确分析的方向和重点。"
                    ))
                
                if steps >= 2:
                    analysis_steps.append(create_analysis_step(
                        2, "深入分析各个方面",
                        "基于第一步的分析：\n{previous_analysis}\n\n请从多个角度深入分析问题，探讨可能的解决方案或答案。"
                    ))
                
                if steps >= 3:
                    analysis_steps.append(create_analysis_step(
                        3, "综合结论和建议",
                        "基于前面的分析：\n{previous_analysis}\n\n请总结分析结果，给出明确的结论和实用的建议。"
                    ))
                
                # 如果步骤超过3步，添加更多细化分析
                for i in range(4, steps + 1):
                    analysis_steps.append(create_analysis_step(
                        i, f"进一步细化分析第{i-3}个方面",
                        "继续深化分析：\n{previous_analysis}\n\n请进一步细化和补充分析，提供更详细的见解。"
                    ))

                # 创建线性链条
                first_step = chain_client.create_linear_chain(analysis_steps, "analysis_chain")
                
                # 执行链条
                context = chain_client.create_context({"query": query})
                result_context = await chain_client.execute_chain(
                    first_step, context, show_step_details=show_details
                )

                # 显示结果
                if result_context.history:
                    safe_print(f"\n[bold blue]🎯 Chain of Thought 分析结果[/bold blue]")
                    safe_print(f"[dim]{'=' * 60}[/dim]")
                    
                    for i, step_result in enumerate(result_context.history):
                        step_title = f"步骤 {i+1}"
                        if i == 0:
                            step_title += " - 问题理解"
                        elif i == 1:
                            step_title += " - 深入分析"
                        elif i == 2:
                            step_title += " - 综合结论"
                        else:
                            step_title += f" - 细化分析 {i-2}"
                            
                        safe_print(f"\n[bold cyan]{step_title}[/bold cyan]")
                        safe_print(f"[green]{step_result.response}[/green]")
                    
                    # 执行摘要
                    summary = result_context.get_execution_summary()
                    safe_print(f"\n[dim]📊 执行统计: {summary['total_steps']} 个步骤, "
                              f"耗时 {summary['total_execution_time']:.2f}秒, "
                              f"成功率 {summary['success_rate']*100:.1f}%[/dim]")
                else:
                    safe_print("[red]❌ 分析执行失败，没有生成结果[/red]")

            except Exception as e:
                safe_print(f"[red]❌ Chain of Thought分析执行失败: {e}[/red]")
                safe_print("[yellow]💡 请检查模型配置和网络连接[/yellow]")

        return asyncio.run(run_chain_analysis())

    def chain_reasoning(
        self,
        query: str,
        model: str = None,
        base_url: str = None,
        api_key: str = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
        show_details: bool = False,
        **kwargs,
    ):
        """使用Chain of Thought进行逻辑推理
        
        Args:
            query: 需要推理的问题或情境
            model: 使用的模型
            base_url: API服务地址
            api_key: API密钥
            temperature: 温度参数
            max_tokens: 最大token数
            show_details: 是否显示每个步骤的详细信息
        """
        import asyncio
        from flexllm.chain_of_thought_client import ChainOfThoughtClient, LinearStep, ExecutionConfig
        from flexllm.openaiclient import OpenAIClient

        # 从配置获取默认值
        mllm_config = self.cli.maque_config.get("mllm", {})
        model = model or mllm_config.get("model", "gemma3:latest")
        base_url = base_url or mllm_config.get("base_url", "http://localhost:11434/v1")
        api_key = api_key or mllm_config.get("api_key", "EMPTY")

        async def run_chain_reasoning():
            try:
                safe_print(f"[bold green]🧠 开始Chain of Thought逻辑推理[/bold green]")
                safe_print(f"[cyan]💭 推理问题: {query}[/cyan]")
                safe_print(f"[dim]🔧 模型: {model}[/dim]\n")

                # 初始化客户端
                openai_client = OpenAIClient(model=model, base_url=base_url, api_key=api_key)
                
                config = ExecutionConfig(
                    enable_monitoring=True,
                    enable_progress=show_details,
                    log_level="INFO" if show_details else "WARNING"
                )
                
                chain_client = ChainOfThoughtClient(openai_client, config)

                # 定义推理步骤
                def create_reasoning_step(step_name: str, prompt_template: str):
                    def prepare_messages(context):
                        previous_reasoning = ""
                        if context.history:
                            previous_reasoning = "\n\n".join([
                                f"[{step.step_name}]: {step.response}" 
                                for step in context.history
                            ])
                        
                        return [
                            {"role": "system", "content": "你是一个逻辑推理专家。请使用严谨的逻辑思维，一步一步地分析和推理。每一步都要有明确的逻辑依据。"},
                            {"role": "user", "content": prompt_template.format(
                                query=context.query,
                                previous_reasoning=previous_reasoning
                            )}
                        ]
                    
                    return LinearStep(
                        name=step_name,
                        prepare_messages_fn=prepare_messages,
                        model_params={
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            **kwargs
                        }
                    )

                # 创建推理链条
                reasoning_steps = [
                    create_reasoning_step(
                        "observation",
                        "首先，让我观察和理解这个问题：\n{query}\n\n请仔细观察问题中的关键信息、已知条件和要求解答的内容。列出所有重要的事实和假设。"
                    ),
                    create_reasoning_step(
                        "hypothesis",
                        "基于观察到的信息：\n{previous_reasoning}\n\n现在请提出可能的假设或解决方案。考虑多种可能性，并说明每种假设的依据。"
                    ),
                    create_reasoning_step(
                        "deduction",
                        "基于前面的观察和假设：\n{previous_reasoning}\n\n现在进行逻辑推导。使用演绎推理，从已知条件推导出结论。确保每一步推理都有明确的逻辑关系。"
                    ),
                    create_reasoning_step(
                        "verification",
                        "基于推理过程：\n{previous_reasoning}\n\n现在验证推理结果。检查逻辑是否一致，结论是否合理，是否遗漏了重要因素。如果发现问题，请指出并修正。"
                    ),
                    create_reasoning_step(
                        "conclusion",
                        "综合整个推理过程：\n{previous_reasoning}\n\n请给出最终结论。总结推理的关键步骤，明确回答原始问题，并说明结论的可信度。"
                    )
                ]

                # 创建和执行链条
                first_step = chain_client.create_linear_chain(reasoning_steps, "reasoning_chain")
                context = chain_client.create_context({"query": query})
                result_context = await chain_client.execute_chain(
                    first_step, context, show_step_details=show_details
                )

                # 显示推理结果
                if result_context.history:
                    safe_print(f"\n[bold blue]🎯 Chain of Thought 推理结果[/bold blue]")
                    safe_print(f"[dim]{'=' * 60}[/dim]")
                    
                    step_names = {
                        "observation": "🔍 观察分析",
                        "hypothesis": "💡 假设提出", 
                        "deduction": "🔗 逻辑推导",
                        "verification": "✅ 验证检查",
                        "conclusion": "🎯 最终结论"
                    }
                    
                    for step_result in result_context.history:
                        step_display = step_names.get(step_result.step_name, step_result.step_name)
                        safe_print(f"\n[bold cyan]{step_display}[/bold cyan]")
                        safe_print(f"[green]{step_result.response}[/green]")
                    
                    # 执行摘要
                    summary = result_context.get_execution_summary()
                    safe_print(f"\n[dim]📊 推理统计: {summary['total_steps']} 个步骤, "
                              f"耗时 {summary['total_execution_time']:.2f}秒, "
                              f"成功率 {summary['success_rate']*100:.1f}%[/dim]")
                else:
                    safe_print("[red]❌ 推理执行失败，没有生成结果[/red]")

            except Exception as e:
                safe_print(f"[red]❌ Chain of Thought推理执行失败: {e}[/red]")
                safe_print("[yellow]💡 请检查模型配置和网络连接[/yellow]")

        return asyncio.run(run_chain_reasoning())

    def chain_run(
        self,
        config_file: str,
        input_data: str = None,
        model: str = None,
        base_url: str = None,
        api_key: str = None,
        show_details: bool = False,
        **kwargs,
    ):
        """运行自定义的Chain of Thought配置文件
        
        Args:
            config_file: YAML格式的链条配置文件路径
            input_data: 输入数据，会作为query传入
            model: 使用的模型（覆盖配置文件中的设置）
            base_url: API服务地址
            api_key: API密钥
            show_details: 是否显示详细执行信息
        """
        import asyncio
        import yaml
        import os
        from pathlib import Path
        from flexllm.chain_of_thought_client import ChainOfThoughtClient, LinearStep, ExecutionConfig
        from flexllm.openaiclient import OpenAIClient

        async def run_chain_config():
            try:
                # 读取配置文件
                config_path = Path(config_file)
                if not config_path.exists():
                    safe_print(f"[red]❌ 配置文件不存在: {config_file}[/red]")
                    return

                safe_print(f"[bold green]📋 运行Chain of Thought配置[/bold green]")
                safe_print(f"[cyan]📁 配置文件: {config_file}[/cyan]")

                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                # 从配置文件和命令行参数合并设置
                mllm_config = self.cli.maque_config.get("mllm", {})
                
                # 模型配置优先级: 命令行 > 配置文件 > 全局配置
                final_model = model or config.get('model') or mllm_config.get("model", "gemma3:latest")
                final_base_url = base_url or config.get('base_url') or mllm_config.get("base_url", "http://localhost:11434/v1")
                final_api_key = api_key or config.get('api_key') or mllm_config.get("api_key", "EMPTY")

                # 获取输入数据
                query = input_data or config.get('query', '')
                if not query:
                    safe_print("[red]❌ 缺少输入数据，请通过 --input-data 参数或在配置文件中的 'query' 字段指定[/red]")
                    return

                safe_print(f"[cyan]📝 输入: {query}[/cyan]")
                safe_print(f"[dim]🔧 模型: {final_model}[/dim]\n")

                # 初始化客户端
                openai_client = OpenAIClient(model=final_model, base_url=final_base_url, api_key=final_api_key)
                
                # 执行配置
                exec_config = ExecutionConfig(
                    enable_monitoring=config.get('enable_monitoring', True),
                    enable_progress=show_details,
                    log_level="INFO" if show_details else "WARNING",
                    step_timeout=config.get('step_timeout'),
                    chain_timeout=config.get('chain_timeout'),
                    max_retries=config.get('max_retries', 0),
                    retry_delay=config.get('retry_delay', 1.0)
                )
                
                chain_client = ChainOfThoughtClient(openai_client, exec_config)

                # 构建步骤
                steps = config.get('steps', [])
                if not steps:
                    safe_print("[red]❌ 配置文件中没有定义步骤[/red]")
                    return

                def create_config_step(step_config):
                    step_name = step_config['name']
                    system_prompt = step_config.get('system_prompt', '')
                    user_prompt = step_config.get('user_prompt', '')
                    
                    def prepare_messages(context):
                        # 处理模板变量
                        template_vars = {
                            'query': context.query,
                            'previous_responses': '\n\n'.join([f"[{s.step_name}]: {s.response}" for s in context.history])
                        }
                        
                        # 添加自定义变量
                        custom_vars = context.get_custom_data('template_vars', {})
                        template_vars.update(custom_vars)
                        
                        messages = []
                        if system_prompt:
                            messages.append({
                                "role": "system", 
                                "content": system_prompt.format(**template_vars)
                            })
                        
                        messages.append({
                            "role": "user",
                            "content": user_prompt.format(**template_vars)
                        })
                        
                        return messages
                    
                    # 获取模型参数
                    model_params = step_config.get('model_params', {})
                    model_params.update(kwargs)  # 命令行参数覆盖
                    
                    return LinearStep(
                        name=step_name,
                        prepare_messages_fn=prepare_messages,
                        model_params=model_params
                    )

                # 创建所有步骤
                chain_steps = [create_config_step(step_config) for step_config in steps]
                
                # 创建和执行链条
                chain_name = config.get('name', 'custom_chain')
                first_step = chain_client.create_linear_chain(chain_steps, chain_name)
                
                # 添加自定义模板变量到上下文
                context = chain_client.create_context({"query": query})
                if config.get('template_vars'):
                    context.add_custom_data('template_vars', config['template_vars'])
                
                result_context = await chain_client.execute_chain(
                    first_step, context, show_step_details=show_details
                )

                # 显示结果
                if result_context.history:
                    safe_print(f"\n[bold blue]🎯 {config.get('name', 'Chain')} 执行结果[/bold blue]")
                    safe_print(f"[dim]{'=' * 60}[/dim]")
                    
                    for step_result in result_context.history:
                        step_display = step_result.step_name.replace('_', ' ').title()
                        safe_print(f"\n[bold cyan]📝 {step_display}[/bold cyan]")
                        safe_print(f"[green]{step_result.response}[/green]")
                    
                    # 执行摘要
                    summary = result_context.get_execution_summary()
                    safe_print(f"\n[dim]📊 执行统计: {summary['total_steps']} 个步骤, "
                              f"耗时 {summary['total_execution_time']:.2f}秒, "
                              f"成功率 {summary['success_rate']*100:.1f}%[/dim]")
                else:
                    safe_print("[red]❌ 链条执行失败，没有生成结果[/red]")

            except yaml.YAMLError as e:
                safe_print(f"[red]❌ YAML配置文件解析错误: {e}[/red]")
            except FileNotFoundError as e:
                safe_print(f"[red]❌ 配置文件未找到: {e}[/red]")
            except Exception as e:
                safe_print(f"[red]❌ Chain执行失败: {e}[/red]")
                safe_print("[yellow]💡 请检查配置文件格式和模型连接[/yellow]")

        return asyncio.run(run_chain_config())
