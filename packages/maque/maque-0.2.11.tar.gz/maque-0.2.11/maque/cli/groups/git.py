"""Git 命令组 - 代理到 Dulwich CLI + 镜像代理支持

直接调用 dulwich CLI，支持所有 git 命令。
注意：实际的 git 命令在 __main__.py 中直接处理，绕过 fire。

新增功能：GitHub 镜像代理支持（适用于国内网络环境）

Usage:
    maque git <command> [args...]

Examples:
    maque git status
    maque git add .
    maque git commit -m "message"
    maque git log
    maque git rebase main
    maque git stash push
    maque git cherry-pick <commit>
    maque git config -l

    # 镜像代理相关命令
    maque git clone https://github.com/user/repo --use_mirror=True
    maque git mirrors                           # 列出可用镜像
    maque git clone-mirror https://github.com/user/repo ./repo  # 使用默认镜像克隆
"""


class GitGroup:
    """Git 命令组 - 代理到 Dulwich CLI

    注意：此类仅作为占位符，实际的 git 命令处理在 __main__.py 中，
    直接调用 dulwich CLI 以避免 fire 参数解析问题。

    支持 GitHub 镜像代理功能，适用于国内网络环境加速 clone/fetch/pull。
    """

    def __init__(self, cli_instance):
        self.cli = cli_instance

    def mirrors(self):
        """列出所有可用的 GitHub 镜像代理

        Returns:
            镜像列表及其 URL
        """
        from maque.git import GIT_MIRRORS, DEFAULT_MIRROR

        print("可用的 GitHub 镜像代理:")
        print("-" * 60)
        for name, info in GIT_MIRRORS.items():
            default_mark = " (默认)" if name == DEFAULT_MIRROR else ""
            print(f"  {name:12} → {info['url']}{default_mark}")
            print(f"               {info['description']}")
        print("-" * 60)
        print("\n使用方法:")
        print("  maque git clone-mirror <url> <path> [--mirror=ghproxy]")
        print("  maque git fetch-mirror [--remote=origin] [--mirror=ghproxy]")
        print("  maque git pull-mirror [--remote=origin] [--mirror=ghproxy]")
        print("\n推荐: ghproxy 系列镜像速度最快 (ghproxy, ghproxy-cdn, ghproxy-hk)")
        print("注意: 镜像可用性可能随时间变化，如遇问题请尝试其他镜像")
        return GIT_MIRRORS

    def clone_mirror(
        self,
        url: str,
        path: str,
        mirror: str = None,
        username: str = None,
        password: str = None,
    ):
        """使用镜像代理克隆 GitHub 仓库

        Args:
            url: GitHub 仓库 URL (https://github.com/user/repo)
            path: 本地目标路径
            mirror: 镜像提供商 (gitclone, ghproxy, ghfast, gitmirror, bgithub)
            username: Git 用户名（可选）
            password: Git 密码/Token（可选）

        Returns:
            PureGitRepo 实例

        Examples:
            maque git clone-mirror https://github.com/pytorch/pytorch ./pytorch
            maque git clone-mirror https://github.com/user/repo ./repo --mirror=ghproxy
        """
        from maque.git import PureGitRepo, convert_to_mirror_url

        mirror_url = convert_to_mirror_url(url, mirror)
        print(f"使用镜像克隆: {mirror_url}")
        repo = PureGitRepo.clone(
            url, path, username=username, password=password,
            use_mirror=True, mirror_provider=mirror
        )
        print(f"克隆完成: {path}")
        return repo

    def fetch_mirror(
        self,
        remote: str = "origin",
        mirror: str = None,
        username: str = None,
        password: str = None,
        repo_path: str = ".",
    ):
        """使用镜像代理拉取远程更新（不合并）

        Args:
            remote: 远程仓库名
            mirror: 镜像提供商
            username: Git 用户名（可选）
            password: Git 密码/Token（可选）
            repo_path: 仓库路径，默认当前目录

        Examples:
            maque git fetch-mirror
            maque git fetch-mirror --mirror=ghproxy
        """
        from maque.git import PureGitRepo

        repo = PureGitRepo.open(repo_path)
        remote_url = repo.get_remote_url(remote)
        if remote_url:
            print(f"远程仓库: {remote_url}")
        repo.fetch(
            remote, username=username, password=password,
            use_mirror=True, mirror_provider=mirror
        )
        print("Fetch 完成")
        return repo

    def pull_mirror(
        self,
        remote: str = "origin",
        mirror: str = None,
        username: str = None,
        password: str = None,
        repo_path: str = ".",
    ):
        """使用镜像代理拉取并合并远程更新

        Args:
            remote: 远程仓库名
            mirror: 镜像提供商
            username: Git 用户名（可选）
            password: Git 密码/Token（可选）
            repo_path: 仓库路径，默认当前目录

        Examples:
            maque git pull-mirror
            maque git pull-mirror --mirror=ghproxy
        """
        from maque.git import PureGitRepo

        repo = PureGitRepo.open(repo_path)
        remote_url = repo.get_remote_url(remote)
        if remote_url:
            print(f"远程仓库: {remote_url}")
        repo.pull(
            remote, username=username, password=password,
            use_mirror=True, mirror_provider=mirror
        )
        print("Pull 完成")
        return repo

    def convert_url(self, url: str, mirror: str = None):
        """将 GitHub URL 转换为镜像 URL（不执行操作，仅输出）

        Args:
            url: 原始 GitHub URL
            mirror: 镜像提供商

        Examples:
            maque git convert-url https://github.com/user/repo
            maque git convert-url https://github.com/user/repo --mirror=ghproxy
        """
        from maque.git import convert_to_mirror_url

        mirror_url = convert_to_mirror_url(url, mirror)
        print(f"原始 URL: {url}")
        print(f"镜像 URL: {mirror_url}")
        return mirror_url

    # =========================================================================
    # Git 全局镜像配置（让原生 git clone 自动使用镜像）
    # =========================================================================

    def _get_known_mirror_urls(self) -> list:
        """获取所有已知镜像的 URL 列表"""
        from maque.git import GIT_MIRRORS
        urls = []
        for name, info in GIT_MIRRORS.items():
            urls.append(info["url"])
        return urls

    def _clear_all_mirror_configs(self):
        """清除所有 maque 设置的镜像配置"""
        import subprocess

        # 获取当前所有 insteadOf 配置
        result = subprocess.run(
            ['git', 'config', '--global', '--get-regexp', r'url\..*\.insteadOf'],
            capture_output=True, text=True
        )

        if not result.stdout.strip():
            return

        # 解析并清除与已知镜像相关的配置
        known_mirrors = self._get_known_mirror_urls()
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            # 格式: url.https://mirror/....insteadOf https://github.com/
            parts = line.split(' ', 1)
            if len(parts) < 2:
                continue
            key = parts[0]  # url.https://mirror/....insteadOf

            # 检查是否是我们设置的镜像配置
            for mirror_url in known_mirrors:
                if mirror_url in key:
                    subprocess.run(
                        ['git', 'config', '--global', '--unset', key],
                        capture_output=True
                    )
                    break

    def mirror_set(self, mirror: str = None):
        """设置 Git 全局镜像，让原生 git clone 自动使用镜像

        设置后，直接使用 git clone https://github.com/user/repo 就会自动走镜像。

        Args:
            mirror: 镜像名称 (ghproxy, ghproxy-cdn, ghproxy-hk, cors, kkgithub, ghfast)
                   默认使用 ghproxy

        Examples:
            maque git mirror-set                      # 使用默认镜像 (ghproxy)
            maque git mirror-set --mirror=ghproxy-cdn # 使用 CDN 镜像
            # 之后直接用 git clone https://github.com/user/repo 就会自动走镜像
        """
        import subprocess
        from maque.git import GIT_MIRRORS, DEFAULT_MIRROR

        if mirror is None:
            mirror = DEFAULT_MIRROR

        if mirror not in GIT_MIRRORS:
            print(f"未知镜像: {mirror}")
            print(f"可用镜像: {', '.join(GIT_MIRRORS.keys())}")
            return

        mirror_info = GIT_MIRRORS[mirror]
        mirror_url = mirror_info["url"]
        mirror_type = mirror_info["type"]

        # 先清除旧配置
        self._clear_all_mirror_configs()

        # 根据镜像类型设置
        if mirror_type == "prefix":
            # prefix 类型: https://mirror/https://github.com/user/repo
            insteadOf_key = f'url.{mirror_url}https://github.com/.insteadOf'
            insteadOf_value = 'https://github.com/'
        else:  # replace 类型
            # replace 类型: https://mirror.com/user/repo
            insteadOf_key = f'url.{mirror_url}.insteadOf'
            insteadOf_value = 'https://github.com/'

        result = subprocess.run(
            ['git', 'config', '--global', insteadOf_key, insteadOf_value],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            print(f"✓ 已设置 Git 全局镜像: {mirror} ({mirror_url})")
            print(f"  现在可以直接使用: git clone https://github.com/user/repo")
        else:
            print(f"✗ 设置失败: {result.stderr}")

    def mirror_unset(self):
        """移除 Git 全局镜像配置，恢复直连 GitHub

        Examples:
            maque git mirror-unset
        """
        self._clear_all_mirror_configs()
        print("✓ 已移除 Git 镜像配置，恢复直连 GitHub")

    def mirror_status(self):
        """查看当前 Git 镜像配置状态

        Examples:
            maque git mirror-status
        """
        import subprocess
        from maque.git import GIT_MIRRORS

        result = subprocess.run(
            ['git', 'config', '--global', '--get-regexp', r'url\..*\.insteadOf'],
            capture_output=True, text=True
        )

        if not result.stdout.strip():
            print("当前未配置任何 URL 重写，使用直连 GitHub")
            return

        print("当前 Git URL 重写配置:")
        print("-" * 60)

        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split(' ', 1)
            if len(parts) < 2:
                continue
            key = parts[0]
            value = parts[1]

            # 尝试识别镜像名称
            mirror_name = None
            for name, info in GIT_MIRRORS.items():
                if info["url"] in key:
                    mirror_name = name
                    break

            if mirror_name:
                print(f"  镜像: {mirror_name}")
                print(f"  {value} → {key.replace('url.', '').replace('.insteadOf', '')}")
            else:
                print(f"  {key} = {value}")

        print("-" * 60)
        print("\n提示:")
        print("  移除镜像: maque git mirror-unset")
        print("  切换镜像: maque git mirror-set --mirror=<name>")

    # =========================================================================
    # Mirror Shell - 镜像加速的子 Shell 环境
    # =========================================================================

    def mirror_shell(self, mirror: str = None):
        """启动一个 GitHub 镜像加速的子 Shell 环境

        在这个环境中，git clone/fetch/pull 和 curl/wget 访问 GitHub 时
        会自动使用镜像加速，适合运行包含大量 GitHub 链接的安装脚本。

        Args:
            mirror: 镜像名称 (ghproxy, ghproxy-cdn, kkgithub 等)，默认 ghproxy-cdn

        Examples:
            maque git mirror-shell
            maque git mirror-shell --mirror=kkgithub

            # 进入后可以直接运行：
            > git clone https://github.com/user/repo
            > curl -fsSL https://raw.githubusercontent.com/xxx/install.sh | bash
            > exit  # 退出镜像环境
        """
        import os
        import tempfile
        import subprocess
        from maque.git import GIT_MIRRORS, DEFAULT_MIRROR

        mirror = mirror or "ghproxy-cdn"
        if mirror not in GIT_MIRRORS:
            print(f"未知镜像: {mirror}")
            print(f"可用镜像: {', '.join(GIT_MIRRORS.keys())}")
            return

        mirror_info = GIT_MIRRORS[mirror]
        mirror_url = mirror_info["url"]
        mirror_type = mirror_info["type"]

        # 构建 URL 替换规则
        if mirror_type == "prefix":
            # prefix 类型: https://ghproxy.cn/https://github.com/user/repo
            github_replace = f"{mirror_url}https://github.com"
            raw_replace = f"{mirror_url}https://raw.githubusercontent.com"
            git_insteadof_key = f"{mirror_url}https://github.com/"
        else:
            # replace 类型: https://kkgithub.com/user/repo
            github_replace = mirror_url.rstrip("/")
            raw_replace = f"https://raw.{mirror_url.split('://')[1]}"
            git_insteadof_key = mirror_url

        # 检测当前 shell
        current_shell = os.environ.get("SHELL", "/bin/bash")
        shell_name = os.path.basename(current_shell)

        # 创建临时 RC 文件
        rc_content = f'''
# ============================================================
# Maque Mirror Shell - GitHub 镜像加速环境
# 镜像: {mirror} ({mirror_url})
# ============================================================

# 保留原始 RC 配置
if [ -f ~/.{shell_name}rc ]; then
    source ~/.{shell_name}rc 2>/dev/null || true
fi

# Git 镜像配置 (临时，仅在此 shell 中生效)
git config --global url."{git_insteadof_key}".insteadOf "https://github.com/"

# 包装 curl - 自动替换 GitHub URL
_maque_original_curl=$(which curl 2>/dev/null)
curl() {{
    local args=()
    for arg in "$@"; do
        arg="${{arg//https:\\/\\/github.com/{github_replace}}}"
        arg="${{arg//https:\\/\\/raw.githubusercontent.com/{raw_replace}}}"
        args+=("$arg")
    done
    $_maque_original_curl "${{args[@]}}"
}}

# 包装 wget - 自动替换 GitHub URL
_maque_original_wget=$(which wget 2>/dev/null)
wget() {{
    local args=()
    for arg in "$@"; do
        arg="${{arg//https:\\/\\/github.com/{github_replace}}}"
        arg="${{arg//https:\\/\\/raw.githubusercontent.com/{raw_replace}}}"
        args+=("$arg")
    done
    $_maque_original_wget "${{args[@]}}"
}}

# 设置环境变量标识
export MAQUE_MIRROR_SHELL="{mirror}"

# 修改终端标题
echo -ne "\\033]0;[Mirror: {mirror}] $(pwd)\\007"

# 如果使用 starship，添加自定义环境变量显示
# 用户可以在 starship.toml 中添加:
# [env_var.MAQUE_MIRROR_SHELL]
# format = "[🪞 $env_value]($style) "
# style = "bold green"

# 每次命令前显示镜像标识 (通过 PROMPT_COMMAND / precmd)
if [ -n "$BASH_VERSION" ]; then
    _maque_prompt_prefix() {{
        echo -ne "\\033[1;32m[🪞 {mirror}]\\033[0m "
    }}
    PROMPT_COMMAND="_maque_prompt_prefix; $PROMPT_COMMAND"
elif [ -n "$ZSH_VERSION" ]; then
    precmd() {{
        echo -ne "\\033[1;32m[🪞 {mirror}]\\033[0m "
    }}
fi

# 清理函数 - 退出时移除临时 git 配置
_maque_cleanup() {{
    git config --global --unset url."{git_insteadof_key}".insteadOf 2>/dev/null || true
}}
trap _maque_cleanup EXIT

echo ""
echo "🚀 已进入 GitHub 镜像加速环境"
echo "   镜像: {mirror} ({mirror_url})"
echo ""
echo "   现在可以直接运行："
echo "   > git clone https://github.com/user/repo"
echo "   > curl -fsSL https://raw.githubusercontent.com/xxx/install.sh | bash"
echo ""
echo "   输入 exit 退出镜像环境"
echo ""
'''

        # 写入临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{shell_name}rc', delete=False) as f:
            f.write(rc_content)
            rc_file = f.name

        try:
            # 启动子 shell (交互式)
            if shell_name == "zsh":
                # zsh 使用 ZDOTDIR 指定配置目录
                env = {**os.environ}
                env["ZDOTDIR"] = os.path.dirname(rc_file)
                # 重命名 rc 文件为 .zshrc
                zsh_rc = os.path.join(os.path.dirname(rc_file), ".zshrc")
                os.rename(rc_file, zsh_rc)
                rc_file = zsh_rc
                subprocess.run([current_shell, "-i"], env=env)
            else:
                # bash: 使用 --rcfile 并强制交互模式
                subprocess.run([current_shell, "--rcfile", rc_file, "-i"])
        finally:
            # 清理临时文件
            os.unlink(rc_file)
            # 确保 git 配置被清理（以防 trap 没触发）
            subprocess.run(
                ['git', 'config', '--global', '--unset', f'url.{git_insteadof_key}.insteadOf'],
                capture_output=True
            )

    def run_script(
        self,
        url: str,
        mirror: str = None,
        shell: str = "bash",
        dry_run: bool = False,
    ):
        """通过镜像下载并执行安装脚本

        自动将脚本中的 GitHub URL 替换为镜像地址后执行。

        Args:
            url: 脚本 URL (支持 github.com 和 raw.githubusercontent.com)
            mirror: 镜像名称，默认 ghproxy-cdn
            shell: 执行脚本的 shell，默认 bash
            dry_run: 仅下载并显示替换后的脚本，不执行

        Examples:
            maque git run-script https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh
            maque git run-script https://xxx/install.sh --dry-run  # 预览不执行
        """
        import subprocess
        import tempfile
        import requests
        from maque.git import GIT_MIRRORS

        mirror = mirror or "ghproxy-cdn"
        if mirror not in GIT_MIRRORS:
            print(f"未知镜像: {mirror}")
            return

        mirror_info = GIT_MIRRORS[mirror]
        mirror_url = mirror_info["url"]
        mirror_type = mirror_info["type"]

        # 构建替换规则
        if mirror_type == "prefix":
            github_replace = f"{mirror_url}https://github.com"
            raw_replace = f"{mirror_url}https://raw.githubusercontent.com"
        else:
            github_replace = mirror_url.rstrip("/")
            raw_replace = f"https://raw.{mirror_url.split('://')[1]}"

        # 先替换下载 URL
        download_url = url
        download_url = download_url.replace("https://github.com", github_replace)
        download_url = download_url.replace("https://raw.githubusercontent.com", raw_replace)

        print(f"下载脚本: {download_url}")

        try:
            resp = requests.get(download_url, timeout=30)
            resp.raise_for_status()
            script_content = resp.text
        except Exception as e:
            print(f"下载失败: {e}")
            return

        # 替换脚本内容中的 GitHub URL
        script_content = script_content.replace("https://github.com", github_replace)
        script_content = script_content.replace("https://raw.githubusercontent.com", raw_replace)

        if dry_run:
            print("\n" + "=" * 60)
            print("替换后的脚本内容 (dry-run 模式，不执行):")
            print("=" * 60)
            print(script_content)
            return

        # 写入临时文件并执行
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(script_content)
            script_file = f.name

        try:
            print(f"执行脚本...")
            subprocess.run([shell, script_file])
        finally:
            import os
            os.unlink(script_file)

    def mirror_fetch(
        self,
        url: str,
        output: str = None,
        mirror: str = None,
    ):
        """通过镜像下载 GitHub 文件

        Args:
            url: GitHub 文件 URL
            output: 输出文件路径，默认使用 URL 中的文件名
            mirror: 镜像名称，默认 ghproxy-cdn

        Examples:
            maque git mirror-fetch https://github.com/user/repo/archive/main.zip
            maque git mirror-fetch https://raw.githubusercontent.com/xxx/config.yaml -o config.yaml
        """
        import requests
        from maque.git import GIT_MIRRORS

        mirror = mirror or "ghproxy-cdn"
        if mirror not in GIT_MIRRORS:
            print(f"未知镜像: {mirror}")
            return

        mirror_info = GIT_MIRRORS[mirror]
        mirror_url = mirror_info["url"]
        mirror_type = mirror_info["type"]

        # 构建下载 URL
        if mirror_type == "prefix":
            download_url = f"{mirror_url}{url}"
        else:
            download_url = url.replace("https://github.com", mirror_url.rstrip("/"))
            download_url = download_url.replace(
                "https://raw.githubusercontent.com",
                f"https://raw.{mirror_url.split('://')[1]}"
            )

        # 确定输出文件名
        if not output:
            output = url.split("/")[-1]
            if "?" in output:
                output = output.split("?")[0]

        print(f"下载: {download_url}")
        print(f"保存到: {output}")

        try:
            resp = requests.get(download_url, stream=True, timeout=60)
            resp.raise_for_status()

            total_size = int(resp.headers.get('content-length', 0))
            downloaded = 0

            with open(output, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = downloaded * 100 // total_size
                        print(f"\r进度: {percent}% ({downloaded}/{total_size})", end="")

            print(f"\n✓ 下载完成: {output}")
        except Exception as e:
            print(f"下载失败: {e}")
