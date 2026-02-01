"""系统工具命令组

包含端口管理、IP获取、压缩解压、文件分割合并、SSH密钥生成、计时器等系统工具。
"""
from __future__ import annotations

import os
import time
import sys
from pathlib import Path
from rich import print


class SystemGroup:
    """系统工具命令组"""

    def __init__(self, parent):
        self.parent = parent

    @staticmethod
    def kill(ports, view: bool = False):
        """杀死指定端口的进程

        跨平台支持 Linux/macOS/Windows

        Args:
            ports: 端口号，可以是单个整数或逗号分隔的多个端口，如 "8080" 或 "8080,3000,5000"
            view: 仅查看进程信息，不执行杀死操作

        Examples:
            spr system kill 8080
            spr system kill 8080,3000,5000
            spr system kill 8080 --view  # 仅查看
        """
        import psutil
        import platform

        # 处理端口参数
        if isinstance(ports, str):
            port_list = [int(p.strip()) for p in ports.split(',') if p.strip()]
        elif isinstance(ports, (int, float)):
            port_list = [int(ports)]
        elif isinstance(ports, (list, tuple)):
            port_list = [int(p) for p in ports]
        else:
            print(f"[red]无效的端口参数: {ports}[/red]")
            return False

        if not port_list:
            print("[yellow]请提供要杀死的端口号[/yellow]")
            return False

        found_any = False

        for port in port_list:
            processes_found = []

            # 使用 psutil 跨平台查找进程
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    connections = proc.connections(kind='inet')
                    for conn in connections:
                        if hasattr(conn.laddr, 'port') and conn.laddr.port == port:
                            processes_found.append({
                                'pid': proc.pid,
                                'name': proc.info['name'],
                                'port': port,
                                'process': proc
                            })
                except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                    continue

            if not processes_found:
                print(f"[yellow]端口 {port} 没有找到运行的进程[/yellow]")
                continue

            found_any = True

            for pinfo in processes_found:
                if view:
                    print(f"[cyan]👁️  {pinfo['name']} (PID: {pinfo['pid']}) 占用端口 {pinfo['port']}[/cyan]")
                else:
                    try:
                        pinfo['process'].terminate()
                        # 等待进程结束
                        try:
                            pinfo['process'].wait(timeout=3)
                        except psutil.TimeoutExpired:
                            # 强制杀死
                            pinfo['process'].kill()
                        print(f"[green]☠️  已杀死 {pinfo['name']} (PID: {pinfo['pid']}) 端口 {pinfo['port']}[/green]")
                    except psutil.NoSuchProcess:
                        print(f"[yellow]进程 {pinfo['pid']} 已不存在[/yellow]")
                    except psutil.AccessDenied:
                        print(f"[red]无权限杀死进程 {pinfo['pid']}，请使用管理员/root权限运行[/red]")
                    except Exception as e:
                        print(f"[red]杀死进程 {pinfo['pid']} 失败: {e}[/red]")

        if not found_any:
            print(f"[yellow]🙃 没有找到占用指定端口的进程[/yellow]")

        return found_any

    @staticmethod
    def get_ip(env: str = "inner"):
        """获取本机IP地址

        Args:
            env: "inner" 获取内网IP，"outer" 获取外网IP

        Examples:
            spr system get_ip
            spr system get_ip --env=outer
        """
        import socket

        if env == "inner":
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(('8.8.8.8', 80))
                    ip = s.getsockname()[0]
                    print(f"[green]内网IP: {ip}[/green]")
                    return ip
            except Exception as e:
                print(f"[red]获取内网IP失败: {e}[/red]")
                return None
        elif env == "outer":
            try:
                import requests
                ip = requests.get('http://ifconfig.me/ip', timeout=5).text.strip()
                print(f"[green]外网IP: {ip}[/green]")
                return ip
            except ImportError:
                print("[red]需要安装 requests 库: pip install requests[/red]")
                return None
            except Exception as e:
                print(f"[red]获取外网IP失败: {e}[/red]")
                return None
        else:
            print(f"[red]无效的 env 参数: {env}，应为 'inner' 或 'outer'[/red]")
            return None

    @staticmethod
    def pack(source_path: str, target_path: str = None, format: str = 'gztar'):
        """压缩文件或文件夹

        Args:
            source_path: 源文件/文件夹路径
            target_path: 目标压缩包路径（不含扩展名），默认与源同名
            format: 压缩格式，支持 "zip", "tar", "gztar"(默认), "bztar", "xztar"

        Examples:
            spr system pack my_folder
            spr system pack my_folder --format=zip
            spr system pack ./data --target_path=backup
        """
        import shutil

        if target_path is None:
            target_path = Path(source_path).name

        try:
            new_path = shutil.make_archive(target_path, format, root_dir=source_path)
            print(f"[green]✓ 压缩完成: {new_path}[/green]")
            return new_path
        except Exception as e:
            print(f"[red]压缩失败: {e}[/red]")
            return None

    @staticmethod
    def unpack(filename: str, extract_dir: str = None, format: str = None):
        """解压文件

        Args:
            filename: 压缩包路径
            extract_dir: 解压目标目录，默认为压缩包同名目录
            format: 压缩格式，默认自动检测。支持 "zip", "tar", "gztar", "bztar", "xztar"

        Examples:
            spr system unpack archive.tar.gz
            spr system unpack data.zip --extract_dir=./output
        """
        import shutil
        from shutil import _find_unpack_format, _UNPACK_FORMATS

        file_path = Path(filename)
        if not file_path.exists():
            print(f"[red]文件不存在: {filename}[/red]")
            return None

        # 自动确定解压目录名
        if extract_dir is None:
            name = file_path.name
            file_format = _find_unpack_format(filename)
            if file_format:
                file_postfix_list = _UNPACK_FORMATS[file_format][0]
                for postfix in file_postfix_list:
                    if name.endswith(postfix):
                        target_name = name[:-len(postfix)]
                        break
                else:
                    target_name = name.replace('.', '_')
            else:
                target_name = name.replace('.', '_')
            extract_dir = f"./{target_name}/"

        extract_path = Path(extract_dir)
        if not extract_path.exists():
            extract_path.mkdir(parents=True)

        try:
            shutil.unpack_archive(filename, extract_dir, format=format)
            print(f"[green]✓ 解压完成: {extract_path.absolute()}[/green]")
            return str(extract_path.absolute())
        except Exception as e:
            print(f"[red]解压失败: {e}[/red]")
            return None

    @staticmethod
    def split(file_path: str, chunk_size: str = "1G"):
        """将大文件分割成多个块

        Args:
            file_path: 原始文件路径
            chunk_size: 每个块的大小，支持 K/M/G 后缀，默认 1G

        Examples:
            spr system split large_file.dat
            spr system split video.mp4 --chunk_size=500M
            spr system split data.bin --chunk_size=100M
        """
        # 解析大小
        size_str = str(chunk_size).upper().strip()
        multipliers = {'K': 1024, 'M': 1024**2, 'G': 1024**3}

        if size_str[-1] in multipliers:
            chunk_bytes = int(float(size_str[:-1]) * multipliers[size_str[-1]])
        else:
            chunk_bytes = int(size_str)

        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            print(f"[red]文件不存在: {file_path}[/red]")
            return None

        file_size = file_path_obj.stat().st_size
        total_chunks = (file_size + chunk_bytes - 1) // chunk_bytes

        print(f"[blue]分割文件: {file_path}[/blue]")
        print(f"文件大小: {file_size / 1024**2:.2f} MB")
        print(f"块大小: {chunk_bytes / 1024**2:.2f} MB")
        print(f"预计分割为 {total_chunks} 个块")

        try:
            with open(file_path, 'rb') as f:
                chunk_number = 0
                while True:
                    chunk = f.read(chunk_bytes)
                    if not chunk:
                        break
                    chunk_file = f"{file_path}_part_{chunk_number:03d}"
                    with open(chunk_file, 'wb') as cf:
                        cf.write(chunk)
                    print(f"  [green]✓[/green] {chunk_file} ({len(chunk) / 1024**2:.2f} MB)")
                    chunk_number += 1

            print(f"[green]✓ 分割完成，共 {chunk_number} 个块[/green]")
            return chunk_number
        except Exception as e:
            print(f"[red]分割失败: {e}[/red]")
            return None

    @staticmethod
    def merge(input_prefix: str, input_dir: str = '.', output_path: str = None):
        """合并分割后的文件块

        Args:
            input_prefix: 分割文件的前缀（原文件名）
            input_dir: 分割文件所在目录，默认当前目录
            output_path: 合并后的文件路径，默认为 input_prefix

        Examples:
            spr system merge large_file.dat
            spr system merge video.mp4 --input_dir=./chunks
            spr system merge data.bin --output_path=restored.bin
        """
        import glob

        if output_path is None:
            output_path = os.path.join(input_dir, input_prefix)

        # 查找所有分块文件
        pattern = os.path.join(input_dir, f"{input_prefix}_part_*")
        parts = sorted(glob.glob(pattern))

        if not parts:
            print(f"[red]没有找到匹配的分块文件: {pattern}[/red]")
            return None

        print(f"[blue]合并文件块[/blue]")
        print(f"找到 {len(parts)} 个分块文件")

        try:
            total_size = 0
            with open(output_path, 'wb') as output_file:
                for part in parts:
                    with open(part, 'rb') as part_file:
                        data = part_file.read()
                        output_file.write(data)
                        total_size += len(data)
                    print(f"  [green]✓[/green] {Path(part).name}")

            print(f"[green]✓ 合并完成: {output_path} ({total_size / 1024**2:.2f} MB)[/green]")
            return output_path
        except Exception as e:
            print(f"[red]合并失败: {e}[/red]")
            return None

    @staticmethod
    def gen_key(name: str, email: str = None, key_type: str = 'rsa'):
        """生成SSH密钥对

        Args:
            name: 密钥名称，将保存为 ~/.ssh/id_{type}_{name}
            email: 关联的邮箱地址
            key_type: 密钥类型，"rsa"(默认) 或 "ed25519"(推荐)

        Examples:
            spr system gen_key github
            spr system gen_key myserver --email=me@example.com
            spr system gen_key legacy --key_type=rsa
        """
        import subprocess

        ssh_dir = Path.home() / '.ssh'
        ssh_dir.mkdir(exist_ok=True)

        if key_type == 'ed25519':
            key_path = ssh_dir / f'id_ed25519_{name}'
            cmd = ['ssh-keygen', '-t', 'ed25519', '-f', str(key_path), '-N', '']
        else:
            key_path = ssh_dir / f'id_rsa_{name}'
            cmd = ['ssh-keygen', '-t', 'rsa', '-b', '4096', '-f', str(key_path), '-N', '']

        if email:
            cmd.extend(['-C', email])

        if key_path.exists():
            print(f"[yellow]密钥已存在: {key_path}[/yellow]")
            response = input("是否覆盖? (y/N): ")
            if response.lower() != 'y':
                print("操作已取消")
                return None

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[red]生成密钥失败: {result.stderr}[/red]")
                return None

            # 读取并显示公钥
            pub_key_path = str(key_path) + '.pub'
            with open(pub_key_path, 'r', encoding='utf-8') as f:
                pub_key = f.read().strip()

            print(f"[green]✓ 密钥生成成功[/green]")
            print(f"\n[cyan]私钥路径:[/cyan] {key_path}")
            print(f"[cyan]公钥路径:[/cyan] {pub_key_path}")
            print(f"\n[cyan]公钥内容:[/cyan]")
            print(f"[dim]{pub_key}[/dim]")

            # 显示配置提示
            config_path = ssh_dir / 'config'
            print(f"""
[yellow]提示: 你可能需要在 {config_path} 中添加以下配置:[/yellow]

[dim]# 远程服务器
Host {name}
  HostName <服务器IP或域名>
  User <用户名>
  Port 22
  IdentityFile {key_path}

# 或 Git 服务
Host {name}
  HostName github.com
  User git
  IdentityFile {key_path}
  IdentitiesOnly yes[/dim]
""")
            return str(key_path)
        except FileNotFoundError:
            print("[red]ssh-keygen 命令不可用，请确保已安装 OpenSSH[/red]")
            return None
        except Exception as e:
            print(f"[red]生成密钥失败: {e}[/red]")
            return None

    @staticmethod
    def timer(interval: float = 0.05):
        """交互式计时器工具

        支持开始、暂停、记录点、停止功能

        快捷键:
            Space/S: 开始 / 暂停
            L: 记录点 (Lap)
            Q: 停止并退出

        Args:
            interval: 刷新间隔（秒），默认 0.05

        Examples:
            spr system timer
            spr system timer --interval=0.1
        """
        def format_time(seconds):
            """格式化时间显示"""
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{secs:05.2f}"
            elif minutes > 0:
                return f"{minutes:02d}:{secs:05.2f}"
            else:
                return f"{secs:.2f}"

        # 跨平台非阻塞键盘输入
        class KeyReader:
            def __init__(self):
                self.is_windows = os.name == 'nt'
                if self.is_windows:
                    import msvcrt
                    self.msvcrt = msvcrt
                else:
                    import termios
                    import tty
                    import select
                    self.termios = termios
                    self.tty = tty
                    self.select = select
                    self.fd = sys.stdin.fileno()
                    self.old_settings = termios.tcgetattr(self.fd)

            def setup(self):
                if not self.is_windows:
                    self.tty.setraw(self.fd)

            def cleanup(self):
                if not self.is_windows:
                    self.termios.tcsetattr(self.fd, self.termios.TCSADRAIN, self.old_settings)

            def get_key(self):
                """非阻塞获取按键，返回 None 如果没有按键"""
                if self.is_windows:
                    if self.msvcrt.kbhit():
                        ch = self.msvcrt.getch()
                        return ch.decode('utf-8', errors='ignore').lower()
                    return None
                else:
                    if self.select.select([sys.stdin], [], [], 0)[0]:
                        ch = sys.stdin.read(1)
                        return ch.lower()
                    return None

        # 进入 raw 模式前使用 rich 格式
        print("[cyan]═══════════════════════════════════════[/cyan]")
        print("[cyan]           交互式计时器[/cyan]")
        print("[cyan]═══════════════════════════════════════[/cyan]")
        print()
        print("快捷键:")
        print("  [green]S / Space[/green]  开始 / 暂停")
        print("  [yellow]L[/yellow]          记录点 (Lap)")
        print("  [red]Q[/red]          停止并退出")
        print()
        print("[yellow]按 S 开始计时...[/yellow]")
        print()

        key_reader = KeyReader()
        key_reader.setup()

        # raw 模式下使用 ANSI 颜色码和 \r\n 换行
        CYAN = "\033[36m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        RED = "\033[31m"
        BOLD = "\033[1m"
        RESET = "\033[0m"
        NL = "\r\n"

        try:
            # 等待开始
            while True:
                key = key_reader.get_key()
                if key in ('s', ' '):
                    break
                if key == 'q':
                    key_reader.cleanup()
                    print("[yellow]已退出[/yellow]")
                    return
                time.sleep(0.05)

            t0 = time.time()
            total_paused = 0.0
            suspend_start = None
            paused = False
            laps = []
            last_lap_time = 0.0

            sys.stdout.write(f"{GREEN}▶ 计时开始{RESET}{NL}{NL}")
            sys.stdout.flush()

            while True:
                time.sleep(interval)
                ct = time.time()

                # 检查按键
                key = key_reader.get_key()
                if key == 'q':
                    break
                elif key in ('s', ' '):
                    paused = not paused
                    if paused:
                        suspend_start = ct
                        current_time = ct - t0 - total_paused
                        sys.stdout.write(f"\r\033[K{YELLOW}⏸ {format_time(current_time)} [暂停 - 按S继续]{RESET}")
                        sys.stdout.flush()
                    else:
                        if suspend_start:
                            total_paused += ct - suspend_start
                            suspend_start = None
                        sys.stdout.write(NL)
                        sys.stdout.flush()
                elif key == 'l' and not paused:
                    current_time = ct - t0 - total_paused
                    lap_time = current_time - last_lap_time
                    laps.append((current_time, lap_time))
                    last_lap_time = current_time
                    sys.stdout.write(f"\r\033[K{YELLOW}Lap {len(laps)}: {format_time(current_time)} ({CYAN}+{format_time(lap_time)}{YELLOW}){RESET}{NL}")
                    sys.stdout.flush()

                # 更新显示
                if not paused:
                    current_time = ct - t0 - total_paused
                    sys.stdout.write(f"\r{GREEN}▶ {format_time(current_time)}{RESET}")
                    sys.stdout.flush()

            # 计算最终时间
            final_time = time.time() - t0 - total_paused
            if suspend_start:
                final_time -= (time.time() - suspend_start)

            sys.stdout.write(f"{NL}{NL}")
            sys.stdout.write(f"{RED}■ 计时停止{RESET}{NL}{NL}")
            sys.stdout.write(f"{CYAN}═══════════════════════════════════════{RESET}{NL}")
            sys.stdout.write(f"{BOLD}总计时间: {format_time(final_time)}{RESET}{NL}")

            if laps:
                sys.stdout.write(f"{NL}{YELLOW}记录点:{RESET}{NL}")
                for i, (total, lap) in enumerate(laps, 1):
                    sys.stdout.write(f"  Lap {i}: {format_time(total)} ({CYAN}+{format_time(lap)}{RESET}){NL}")

            sys.stdout.write(f"{CYAN}═══════════════════════════════════════{RESET}{NL}")
            sys.stdout.flush()

        except Exception as e:
            sys.stdout.write(f"{NL}错误: {e}{NL}")
        finally:
            key_reader.cleanup()

    @staticmethod
    def setup_tmux(force: bool = False):
        """一键配置 Oh my tmux! (gpakosz/.tmux)

        将 tmux 配置文件安装到 $HOME 目录，无需从 GitHub 下载。

        Args:
            force: 强制覆盖已存在的配置文件

        安装后的文件结构:
            ~/.tmux/.tmux.conf      - 主配置文件
            ~/.tmux.conf            - 软链接到 ~/.tmux/.tmux.conf
            ~/.tmux.conf.local      - 用户自定义配置（可编辑）

        Examples:
            maque system setup-tmux
            maque system setup-tmux --force  # 强制覆盖
        """
        import shutil
        from importlib import resources

        home = Path.home()
        tmux_dir = home / '.tmux'
        tmux_conf = tmux_dir / '.tmux.conf'
        tmux_conf_link = home / '.tmux.conf'
        tmux_conf_local = home / '.tmux.conf.local'

        # 检查现有配置
        if not force:
            existing = []
            if tmux_dir.exists():
                existing.append(str(tmux_dir))
            if tmux_conf_link.exists() and not tmux_conf_link.is_symlink():
                existing.append(str(tmux_conf_link))
            if existing:
                print(f"[yellow]检测到现有配置:[/yellow]")
                for p in existing:
                    print(f"  - {p}")
                print(f"\n[yellow]使用 --force 强制覆盖，或手动备份后再试[/yellow]")
                return False

        # 创建 ~/.tmux 目录
        tmux_dir.mkdir(parents=True, exist_ok=True)
        print(f"[green]✓[/green] 创建目录: {tmux_dir}")

        # 定位包内数据文件
        try:
            # Python 3.9+
            data_dir = resources.files('maque.data.tmux')
            tmux_conf_src = data_dir.joinpath('.tmux.conf')
            tmux_conf_local_src = data_dir.joinpath('.tmux.conf.local')

            # 复制 .tmux.conf
            with resources.as_file(tmux_conf_src) as src:
                shutil.copy2(src, tmux_conf)
            print(f"[green]✓[/green] 复制配置: {tmux_conf}")

            # 创建软链接
            if tmux_conf_link.exists() or tmux_conf_link.is_symlink():
                tmux_conf_link.unlink()
            tmux_conf_link.symlink_to('.tmux/.tmux.conf')
            print(f"[green]✓[/green] 创建链接: {tmux_conf_link} -> .tmux/.tmux.conf")

            # 复制 .tmux.conf.local（仅当不存在或 force=True）
            if not tmux_conf_local.exists() or force:
                with resources.as_file(tmux_conf_local_src) as src:
                    shutil.copy2(src, tmux_conf_local)
                print(f"[green]✓[/green] 复制配置: {tmux_conf_local}")
            else:
                print(f"[yellow]⊘[/yellow] 跳过 {tmux_conf_local}（已存在，使用 --force 覆盖）")

        except Exception as e:
            print(f"[red]✗ 安装失败: {e}[/red]")
            return False

        print(f"\n[green]✓ Oh my tmux! 配置完成[/green]")
        print(f"\n[cyan]提示:[/cyan]")
        print(f"  - 编辑 {tmux_conf_local} 自定义配置")
        print(f"  - 在 tmux 中按 <prefix> e 快速编辑配置")
        print(f"  - 重新加载配置: tmux source-file ~/.tmux.conf")
        return True

    @staticmethod
    def setup_vim(force: bool = False, lsp: bool = False):
        """一键配置 Vim

        将精简的 vim 配置文件安装到 $HOME 目录，无需从 GitHub 下载。

        Args:
            force: 强制覆盖已存在的配置文件
            lsp: 启用 LSP/FZF/Git 插件支持

        安装后的文件结构:
            ~/.vimrc              - 主配置文件
            ~/.vim/lsp.vim        - 扩展配置 (LSP/FZF/Git, 仅 --lsp)
            ~/.vim/undodir/       - 撤销历史目录
            ~/.vim/plugged/       - 插件目录 (仅 --lsp)

        Examples:
            maque system setup-vim             # 基础配置
            maque system setup-vim --lsp       # 包含 LSP/FZF/Git 插件
            maque system setup-vim --lsp --force  # 强制覆盖
        """
        import shutil
        from importlib import resources

        home = Path.home()
        vimrc = home / '.vimrc'
        vim_dir = home / '.vim'
        undo_dir = vim_dir / 'undodir'
        lsp_vim = vim_dir / 'lsp.vim'

        # 检查现有配置
        if not force:
            if vimrc.exists():
                print(f"[yellow]检测到现有配置: {vimrc}[/yellow]")
                print(f"[yellow]使用 --force 强制覆盖，或手动备份后再试[/yellow]")
                return False

        # 定位包内数据文件
        try:
            data_dir = resources.files('maque.data.vim')
            vimrc_src = data_dir.joinpath('.vimrc')

            # 创建 ~/.vim 目录
            vim_dir.mkdir(parents=True, exist_ok=True)

            # 复制 .vimrc
            with resources.as_file(vimrc_src) as src:
                shutil.copy2(src, vimrc)
            print(f"[green]✓[/green] 复制配置: {vimrc}")

            # 如果启用 LSP，复制 lsp.vim 到 ~/.vim/
            if lsp:
                lsp_src = data_dir.joinpath('lsp.vim')
                with resources.as_file(lsp_src) as src:
                    shutil.copy2(src, lsp_vim)
                print(f"[green]✓[/green] 复制扩展配置: {lsp_vim}")

            # 创建撤销目录
            undo_dir.mkdir(parents=True, exist_ok=True)
            print(f"[green]✓[/green] 创建目录: {undo_dir}")

        except Exception as e:
            print(f"[red]✗ 安装失败: {e}[/red]")
            return False

        print(f"\n[green]✓ Vim 配置完成[/green]")

        from rich.table import Table
        from rich.console import Console
        console = Console()

        table = Table(title="常用快捷键 (Leader 键为空格)", show_header=True, header_style="bold cyan")
        table.add_column("分类", style="yellow", width=8)
        table.add_column("快捷键", style="green")
        table.add_column("功能", style="white")

        table.add_row("文件", "<Space>w / q / x", "保存 / 退出 / 保存退出")
        table.add_row("", "<Space>e", "文件浏览器 (当前文件目录, 再按关闭)")
        table.add_row("分屏", "<Space>sv / sh", "垂直 / 水平分屏")
        table.add_row("", "<Space>sc / so", "关闭窗口 / 只保留当前")
        table.add_row("", "Ctrl+h/j/k/l", "分屏间导航")
        table.add_row("", "Ctrl+方向键", "调整窗口大小")
        table.add_row("导航", "H / L", "行首 / 行尾")
        table.add_row("", "<Space><Tab>", "切换上一个 buffer")
        table.add_row("", "]q / [q", "Quickfix 下/上一个")
        table.add_row("编辑", "jk", "退出插入模式")
        table.add_row("", "<Space>/", "切换注释")
        table.add_row("", "<Space>s", "替换光标下单词")
        table.add_row("折叠", "za / zR / zM", "切换 / 全展开 / 全折叠")
        table.add_row("搜索", "<Space><Space>", "清除搜索高亮")
        table.add_row("会话", "<Space>ss / sl", "保存 / 加载会话")
        table.add_row("运行", "<Space>r", "运行当前文件")
        table.add_row("其他", "<Space>a", "全选")
        table.add_row("", "<Space>rc", "重载配置")

        console.print(table)

        if lsp:
            print(f"\n[yellow]═══════════════════════════════════════════[/yellow]")
            print(f"[yellow]扩展配置已复制到 {lsp_vim}[/yellow]")
            print(f"[yellow]但尚未启用 (避免网络问题导致卡顿)[/yellow]")
            print(f"[yellow]═══════════════════════════════════════════[/yellow]")
            print(f"\n[cyan]启用方法:[/cyan]")
            print(f"  在 ~/.vimrc 末尾添加:")
            print(f"  [green]source ~/.vim/lsp.vim[/green]")
            print(f"\n[cyan]启用后首次打开 vim 需执行:[/cyan]")
            print(f"  [green]:PlugInstall[/green]")
            print(f"\n[cyan]如遇网络问题，可在 lsp.vim 中配置 GitHub 镜像:[/cyan]")
            print(f"  let g:plug_url_format = 'https://ghproxy.com/https://github.com/%s.git'")

        return True

    @staticmethod
    def setup_search(
        tools: str = "fzf,rg,fd",
        mode: str = "auto",
        shell_integration: bool = True,
        force: bool = False,
        use_mirror: bool = True,
        mirror: str = None
    ):
        """一键安装文件搜索工具 (fzf + ripgrep + fd)

        支持的工具:
            - fzf: 模糊搜索器，支持交互式文件/历史搜索
            - rg (ripgrep): 快速文件内容搜索，比 grep 快 10x+
            - fd: 快速文件名搜索，比 find 快 5x+

        安装模式:
            - auto: 自动选择 (优先 pkg > binary)
            - pkg: 使用系统包管理器 (需要 sudo)
            - binary: 下载预编译二进制到 ~/.local/bin (无需 sudo)
            - cargo: 使用 cargo install (需要 Rust, rg/fd 支持, 需手动指定)

        Args:
            tools: 要安装的工具，逗号分隔，默认全部安装 "fzf,rg,fd"
            mode: 安装模式 (auto/binary/cargo/pkg)
            shell_integration: 是否配置 fzf 的 shell 集成（Ctrl+R 历史搜索等）
            force: 强制重新安装已存在的工具
            use_mirror: 是否使用 GitHub 镜像 (默认 True)
            mirror: 指定镜像名称 (ghproxy/ghfast/kkgithub 等)，运行 maque git mirrors 查看

        Examples:
            maque system setup-search                     # 自动选择，使用默认镜像
            maque system setup-search --mode=binary      # 无 sudo 安装到用户目录
            maque system setup-search --use_mirror=False # 不使用镜像（直连 GitHub）
            maque system setup-search --mirror=ghfast    # 指定镜像
        """
        import subprocess
        import shutil
        import platform
        import tarfile
        import zipfile
        import tempfile
        import urllib.request

        # GitHub releases 下载地址 (预编译二进制)
        # 使用较新的稳定版本
        BINARY_URLS = {
            'fzf': {
                'linux_x86_64': 'https://github.com/junegunn/fzf/releases/download/v0.56.3/fzf-0.56.3-linux_amd64.tar.gz',
                'linux_aarch64': 'https://github.com/junegunn/fzf/releases/download/v0.56.3/fzf-0.56.3-linux_arm64.tar.gz',
                'darwin_x86_64': 'https://github.com/junegunn/fzf/releases/download/v0.56.3/fzf-0.56.3-darwin_amd64.tar.gz',
                'darwin_arm64': 'https://github.com/junegunn/fzf/releases/download/v0.56.3/fzf-0.56.3-darwin_arm64.tar.gz',
            },
            'rg': {
                'linux_x86_64': 'https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-x86_64-unknown-linux-musl.tar.gz',
                'linux_aarch64': 'https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-aarch64-unknown-linux-gnu.tar.gz',
                'darwin_x86_64': 'https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-x86_64-apple-darwin.tar.gz',
                'darwin_arm64': 'https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-aarch64-apple-darwin.tar.gz',
            },
            'fd': {
                'linux_x86_64': 'https://github.com/sharkdp/fd/releases/download/v10.2.0/fd-v10.2.0-x86_64-unknown-linux-musl.tar.gz',
                'linux_aarch64': 'https://github.com/sharkdp/fd/releases/download/v10.2.0/fd-v10.2.0-aarch64-unknown-linux-gnu.tar.gz',
                'darwin_x86_64': 'https://github.com/sharkdp/fd/releases/download/v10.2.0/fd-v10.2.0-x86_64-apple-darwin.tar.gz',
                'darwin_arm64': 'https://github.com/sharkdp/fd/releases/download/v10.2.0/fd-v10.2.0-aarch64-apple-darwin.tar.gz',
            },
        }

        # cargo 包名映射
        CARGO_NAMES = {'rg': 'ripgrep', 'fd': 'fd-find'}

        # 解析要安装的工具 (兼容 tuple/list 和 str)
        if isinstance(tools, (tuple, list)):
            tool_list = [str(t).strip().lower() for t in tools]
        else:
            tool_list = [t.strip().lower() for t in str(tools).split(',')]

        # 规范化工具名
        normalized_tools = []
        for t in tool_list:
            if t in ('rg', 'ripgrep'):
                if 'rg' not in normalized_tools:
                    normalized_tools.append('rg')
            elif t in ('fd', 'fd-find'):
                if 'fd' not in normalized_tools:
                    normalized_tools.append('fd')
            elif t == 'fzf':
                if 'fzf' not in normalized_tools:
                    normalized_tools.append('fzf')
            else:
                print(f"[yellow]未知工具: {t}，跳过[/yellow]")

        if not normalized_tools:
            print("[red]没有有效的工具需要安装[/red]")
            return False

        system = platform.system().lower()
        machine = platform.machine().lower()

        # 规范化架构名
        if machine in ('x86_64', 'amd64'):
            arch = 'x86_64'
        elif machine in ('aarch64', 'arm64'):
            arch = 'aarch64' if system == 'linux' else 'arm64'
        else:
            arch = machine

        platform_key = f"{system}_{arch}"

        # 安装目录
        local_bin = Path.home() / '.local' / 'bin'

        def check_installed(tool):
            """检查工具是否已安装"""
            if tool == 'fd':
                return shutil.which('fd') or shutil.which('fdfind')
            return shutil.which(tool)

        def ensure_local_bin():
            """确保 ~/.local/bin 存在且在 PATH 中"""
            local_bin.mkdir(parents=True, exist_ok=True)
            path_env = os.environ.get('PATH', '')
            if str(local_bin) not in path_env:
                print(f"[yellow]提示: 请将 {local_bin} 添加到 PATH[/yellow]")
                print(f"[yellow]  export PATH=\"{local_bin}:$PATH\"[/yellow]")

        def install_binary(tool):
            """下载预编译二进制安装到 ~/.local/bin"""
            url = BINARY_URLS.get(tool, {}).get(platform_key)
            if not url:
                print(f"[yellow]无可用二进制: {tool} ({platform_key})[/yellow]")
                return False

            # 应用 GitHub 镜像
            if use_mirror:
                try:
                    from maque.git import convert_to_mirror_url
                    url = convert_to_mirror_url(url, mirror)
                except ImportError:
                    # 降级：手动处理
                    if mirror:
                        url = url.replace('https://github.com', f'https://{mirror}')

            ensure_local_bin()
            print(f"[cyan]下载: {url}[/cyan]")

            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmpdir = Path(tmpdir)
                    archive_path = tmpdir / 'archive.tar.gz'

                    # 下载
                    urllib.request.urlretrieve(url, archive_path)
                    print(f"[green]✓ 下载完成[/green]")

                    # 解压
                    with tarfile.open(archive_path, 'r:gz') as tar:
                        tar.extractall(tmpdir)

                    # 查找可执行文件
                    exe_name = tool if tool != 'rg' else 'rg'
                    exe_path = None

                    for f in tmpdir.rglob('*'):
                        if f.name == exe_name and f.is_file():
                            exe_path = f
                            break

                    if not exe_path:
                        # fzf 直接在根目录
                        for f in tmpdir.iterdir():
                            if f.name == exe_name and f.is_file():
                                exe_path = f
                                break

                    if not exe_path:
                        print(f"[red]未找到可执行文件: {exe_name}[/red]")
                        return False

                    # 复制到 ~/.local/bin
                    dest = local_bin / exe_name
                    shutil.copy2(exe_path, dest)
                    dest.chmod(0o755)
                    print(f"[green]✓ 安装到: {dest}[/green]")
                    return True

            except Exception as e:
                print(f"[red]下载安装失败: {e}[/red]")
                return False

        def install_cargo(tool):
            """使用 cargo 安装"""
            if tool == 'fzf':
                print(f"[yellow]fzf 不支持 cargo 安装 (Go 语言编写)[/yellow]")
                return False

            if not shutil.which('cargo'):
                print(f"[yellow]未找到 cargo，跳过[/yellow]")
                return False

            cargo_name = CARGO_NAMES.get(tool, tool)
            cmd = ['cargo', 'install', cargo_name]
            print(f"[cyan]执行: {' '.join(cmd)}[/cyan]")

            try:
                subprocess.run(cmd, check=True)
                return True
            except subprocess.CalledProcessError as e:
                print(f"[red]cargo 安装失败: {e}[/red]")
                return False

        def install_pkg(tool):
            """使用包管理器安装"""
            # 检测包管理器
            pkg_manager = None
            if system == 'darwin':
                if shutil.which('brew'):
                    pkg_manager = 'brew'
            elif system == 'linux':
                for pm in ['apt', 'dnf', 'yum', 'pacman', 'apk']:
                    if shutil.which(pm):
                        pkg_manager = pm
                        break

            if not pkg_manager:
                print("[yellow]未检测到包管理器[/yellow]")
                return False

            # 包名映射
            pkg_names = {
                'brew': {'fzf': 'fzf', 'rg': 'ripgrep', 'fd': 'fd'},
                'apt': {'fzf': 'fzf', 'rg': 'ripgrep', 'fd': 'fd-find'},
                'dnf': {'fzf': 'fzf', 'rg': 'ripgrep', 'fd': 'fd-find'},
                'yum': {'fzf': 'fzf', 'rg': 'ripgrep', 'fd': 'fd-find'},
                'pacman': {'fzf': 'fzf', 'rg': 'ripgrep', 'fd': 'fd'},
                'apk': {'fzf': 'fzf', 'rg': 'ripgrep', 'fd': 'fd'},
            }

            pkg_name = pkg_names.get(pkg_manager, {}).get(tool)
            if not pkg_name:
                return False

            # 检测是否是 root 用户
            is_root = os.geteuid() == 0 if hasattr(os, 'geteuid') else False
            sudo_prefix = [] if is_root else ['sudo']

            install_cmds = {
                'brew': ['brew', 'install', pkg_name],
                'apt': sudo_prefix + ['apt', 'install', '-y', pkg_name],
                'dnf': sudo_prefix + ['dnf', 'install', '-y', pkg_name],
                'yum': sudo_prefix + ['yum', 'install', '-y', pkg_name],
                'pacman': sudo_prefix + ['pacman', '-S', '--noconfirm', pkg_name],
                'apk': sudo_prefix + ['apk', 'add', pkg_name],
            }

            cmd = install_cmds.get(pkg_manager)

            # 非 root 用户检查 sudo 是否可用
            if cmd and cmd[0] == 'sudo' and not shutil.which('sudo'):
                print("[yellow]未找到 sudo，跳过包管理器安装[/yellow]")
                return False

            print(f"[cyan]执行: {' '.join(cmd)}[/cyan]")

            try:
                subprocess.run(cmd, check=True)
                return True
            except subprocess.CalledProcessError as e:
                print(f"[red]包管理器安装失败: {e}[/red]")
                return False
            except FileNotFoundError as e:
                print(f"[red]命令未找到: {e}[/red]")
                return False

        def install_tool(tool, install_mode):
            """根据模式安装工具"""
            if install_mode == 'binary':
                return install_binary(tool)
            elif install_mode == 'cargo':
                return install_cargo(tool)
            elif install_mode == 'pkg':
                return install_pkg(tool)
            elif install_mode == 'auto':
                # 优先级: pkg > binary
                if install_pkg(tool):
                    return True
                print(f"[yellow]pkg 模式失败，尝试 binary...[/yellow]")
                return install_binary(tool)
            return False

        # 开始安装
        print("[cyan]═══════════════════════════════════════════[/cyan]")
        print("[cyan]         文件搜索工具安装器[/cyan]")
        print("[cyan]═══════════════════════════════════════════[/cyan]")
        print()
        print(f"[blue]系统:[/blue] {platform.system()} {platform.machine()} ({platform_key})")
        print(f"[blue]安装模式:[/blue] {mode}")
        print(f"[blue]安装目录:[/blue] {local_bin}")
        print(f"[blue]待安装工具:[/blue] {', '.join(normalized_tools)}")
        if use_mirror:
            try:
                from maque.git import DEFAULT_MIRROR
                mirror_name = mirror or DEFAULT_MIRROR
                print(f"[blue]GitHub 镜像:[/blue] {mirror_name} (使用 maque git mirrors 查看全部)")
            except ImportError:
                print(f"[blue]GitHub 镜像:[/blue] {mirror or '默认'}")
        else:
            print(f"[blue]GitHub 镜像:[/blue] 已禁用 (直连)")
        print()

        installed = []
        failed = []
        skipped = []

        for tool in normalized_tools:
            print(f"\n[bold]{'='*45}[/bold]")
            print(f"[bold cyan]安装 {tool}[/bold cyan]")

            # 检查是否已安装
            if check_installed(tool) and not force:
                exe_path = check_installed(tool)
                print(f"[green]✓ {tool} 已安装: {exe_path}[/green]")
                skipped.append(tool)
                continue

            # 安装
            if install_tool(tool, mode):
                if check_installed(tool):
                    print(f"[green]✓ {tool} 安装成功[/green]")
                    installed.append(tool)
                else:
                    # 可能安装到了 ~/.local/bin 但不在 PATH 中
                    if (local_bin / tool).exists():
                        print(f"[green]✓ {tool} 安装成功 (需要更新 PATH)[/green]")
                        installed.append(tool)
                    else:
                        print(f"[red]✗ {tool} 安装失败[/red]")
                        failed.append(tool)
            else:
                print(f"[red]✗ {tool} 安装失败[/red]")
                failed.append(tool)

        # 配置 fzf shell 集成
        if shell_integration and ('fzf' in installed or 'fzf' in skipped):
            print(f"\n[bold]{'='*40}[/bold]")
            print("[bold cyan]配置 fzf shell 集成[/bold cyan]")

            home = Path.home()
            shell = os.environ.get('SHELL', '/bin/bash')

            # fzf 配置内容
            fzf_config = '''
# fzf 配置
if command -v fzf &> /dev/null; then
    # 使用 fd 作为默认搜索命令（如果可用）
    if command -v fd &> /dev/null; then
        export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git'
        export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
        export FZF_ALT_C_COMMAND='fd --type d --hidden --follow --exclude .git'
    elif command -v fdfind &> /dev/null; then
        export FZF_DEFAULT_COMMAND='fdfind --type f --hidden --follow --exclude .git'
        export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
        export FZF_ALT_C_COMMAND='fdfind --type d --hidden --follow --exclude .git'
    fi

    # fzf 默认选项
    export FZF_DEFAULT_OPTS='--height 40% --layout=reverse --border --info=inline'

    # 加载 fzf 键绑定和补全
    [ -f ~/.fzf.bash ] && source ~/.fzf.bash
    [ -f ~/.fzf.zsh ] && source ~/.fzf.zsh
    [ -f /usr/share/fzf/key-bindings.bash ] && source /usr/share/fzf/key-bindings.bash
    [ -f /usr/share/fzf/completion.bash ] && source /usr/share/fzf/completion.bash
    [ -f /usr/share/doc/fzf/examples/key-bindings.zsh ] && source /usr/share/doc/fzf/examples/key-bindings.zsh
    [ -f /usr/share/doc/fzf/examples/completion.zsh ] && source /usr/share/doc/fzf/examples/completion.zsh
fi
'''
            # 确定配置文件
            if 'zsh' in shell:
                rc_file = home / '.zshrc'
            else:
                rc_file = home / '.bashrc'

            # 检查是否已配置
            marker = '# fzf 配置'
            if rc_file.exists():
                content = rc_file.read_text()
                if marker in content:
                    print(f"[yellow]fzf 配置已存在于 {rc_file}[/yellow]")
                else:
                    with open(rc_file, 'a') as f:
                        f.write(fzf_config)
                    print(f"[green]✓ fzf 配置已添加到 {rc_file}[/green]")
            else:
                with open(rc_file, 'w') as f:
                    f.write(fzf_config)
                print(f"[green]✓ 创建 {rc_file} 并添加 fzf 配置[/green]")

        # 总结
        print(f"\n[cyan]═══════════════════════════════════════[/cyan]")
        print("[bold]安装总结[/bold]")
        if installed:
            print(f"[green]✓ 已安装: {', '.join(installed)}[/green]")
        if skipped:
            print(f"[yellow]⊘ 已跳过 (已存在): {', '.join(skipped)}[/yellow]")
        if failed:
            print(f"[red]✗ 安装失败: {', '.join(failed)}[/red]")

        # 使用提示
        print(f"\n[cyan]使用提示:[/cyan]")
        if 'fzf' in installed or 'fzf' in skipped:
            print("  [green]fzf[/green]:")
            print("    Ctrl+R  - 搜索命令历史")
            print("    Ctrl+T  - 搜索文件")
            print("    Alt+C   - 搜索并进入目录")
            print("    vim **<Tab>  - 模糊补全文件")
        if 'rg' in installed or 'rg' in skipped:
            print("  [green]rg (ripgrep)[/green]:")
            print("    rg 'pattern'           - 搜索当前目录")
            print("    rg -i 'pattern'        - 忽略大小写")
            print("    rg -t py 'def'         - 只搜索 Python 文件")
            print("    rg -g '*.py' 'import'  - 使用 glob 过滤")
        if 'fd' in installed or 'fd' in skipped:
            # binary 模式安装的是 fd，pkg 模式在某些系统上是 fdfind
            fd_cmd = 'fd' if (local_bin / 'fd').exists() or shutil.which('fd') else 'fdfind'
            print(f"  [green]{fd_cmd} (fd)[/green]:")
            print(f"    {fd_cmd} 'pattern'        - 搜索文件名")
            print(f"    {fd_cmd} -e py            - 只搜索 .py 文件")
            print(f"    {fd_cmd} -t d             - 只搜索目录")
            print(f"    {fd_cmd} -H               - 包含隐藏文件")

        if shell_integration and ('fzf' in installed or 'fzf' in skipped):
            print(f"\n[yellow]提示: 执行 source {rc_file} 或重启终端以启用 fzf 快捷键[/yellow]")

        return len(failed) == 0
