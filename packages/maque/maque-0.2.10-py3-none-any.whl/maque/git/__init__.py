"""
Git 模块 - 纯 Python Git 操作

基于 Dulwich 实现，不依赖 git 客户端。
支持 GitHub 镜像代理，适用于国内网络环境。
"""

try:
    from .pure_git import (
        PureGitRepo,
        GitStatus,
        GitCommitInfo,
        GitStashEntry,
        GitBlameEntry,
        # 镜像代理相关
        GIT_MIRRORS,
        DEFAULT_MIRROR,
        convert_to_mirror_url,
        list_mirrors,
    )
except ImportError:
    pass

__all__ = [
    'PureGitRepo',
    'GitStatus',
    'GitCommitInfo',
    'GitStashEntry',
    'GitBlameEntry',
    # 镜像代理相关
    'GIT_MIRRORS',
    'DEFAULT_MIRROR',
    'convert_to_mirror_url',
    'list_mirrors',
]
