"""
Claude Code Skill 安装命令

Skill 作用域:
  - 全局: ~/.claude/skills/maque/SKILL.md (install-skill 安装到此处)
  - 项目级: .claude/skills/maque/SKILL.md (符号链接到 maque/SKILL.md)
"""

import shutil
from pathlib import Path

from rich.console import Console

console = Console()


def get_skill_source_path() -> Path:
    """获取 SKILL.md 源文件路径"""
    return Path(__file__).parent.parent / "SKILL.md"


def get_skill_target_dir() -> Path:
    """获取全局 skill 安装目标目录"""
    return Path.home() / ".claude" / "skills" / "maque"


def _find_project_skill() -> Path | None:
    """查找项目级 skill 文件（从 maque 包目录向上找 .claude/skills/）"""
    project_root = Path(__file__).parent.parent.parent
    project_skill = project_root / ".claude" / "skills" / "maque" / "SKILL.md"
    if project_skill.exists() or project_skill.is_symlink():
        return project_skill
    return None


def _check_project_skill_sync() -> None:
    """检查项目级 skill 符号链接是否有效"""
    project_skill = _find_project_skill()
    if project_skill is None:
        return
    if project_skill.is_symlink():
        if project_skill.resolve().exists():
            console.print(
                f"  [dim]项目级 skill (symlink): {project_skill}[/dim]"
            )
        else:
            console.print(
                f"  [yellow]警告: 项目级 skill 符号链接已失效: {project_skill}[/yellow]"
            )


def install_skill() -> None:
    """安装 maque skill 到 Claude Code (全局)"""
    source = get_skill_source_path()
    target_dir = get_skill_target_dir()
    target = target_dir / "SKILL.md"

    if not source.exists():
        console.print("[red]错误: SKILL.md 源文件不存在[/red]")
        raise SystemExit(1)

    # 创建目标目录
    target_dir.mkdir(parents=True, exist_ok=True)

    # 复制文件
    shutil.copy2(source, target)

    console.print("[green]✓[/green] 已安装 maque skill 到 Claude Code (全局)")
    console.print(f"  [dim]{target}[/dim]")
    _check_project_skill_sync()
    console.print()
    console.print("[dim]在 Claude Code 中使用 /maque 调用此 skill[/dim]")


def uninstall_skill() -> None:
    """卸载 maque skill (全局)"""
    target_dir = get_skill_target_dir()
    target = target_dir / "SKILL.md"

    if not target.exists():
        console.print("[yellow]maque skill 未安装[/yellow]")
        return

    target.unlink()

    # 如果目录为空，也删除目录
    if target_dir.exists() and not any(target_dir.iterdir()):
        target_dir.rmdir()

    console.print("[green]✓[/green] 已卸载 maque skill (全局)")


def skill_status() -> None:
    """显示 skill 安装状态"""
    # 全局
    global_target = get_skill_target_dir() / "SKILL.md"
    if global_target.exists():
        console.print("[green]✓[/green] 全局 skill 已安装")
        console.print(f"  [dim]{global_target}[/dim]")
    else:
        console.print("[yellow]✗[/yellow] 全局 skill 未安装")
        console.print("  [dim]运行 maque install-skill 安装[/dim]")

    # 项目级
    project_skill = _find_project_skill()
    if project_skill is not None:
        if project_skill.is_symlink() and project_skill.resolve().exists():
            console.print("[green]✓[/green] 项目级 skill 已配置 (symlink)")
            console.print(f"  [dim]{project_skill}[/dim]")
        elif project_skill.is_symlink():
            console.print("[yellow]✗[/yellow] 项目级 skill 符号链接已失效")
        elif project_skill.exists():
            console.print("[green]✓[/green] 项目级 skill 已配置")
            console.print(f"  [dim]{project_skill}[/dim]")
