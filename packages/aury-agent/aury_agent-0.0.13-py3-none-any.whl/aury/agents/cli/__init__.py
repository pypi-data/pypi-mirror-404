"""
Aury Agent CLI - 命令行界面
===========================

提供命令行工具用于:
- 交互式对话 (chat)
- 运行 Workflow (workflow)
- 管理会话 (session)
- 配置管理 (config)

扩展支持:
- 注册自定义 Agent
- 注册自定义 Tool
- 从配置文件加载扩展
- 从 entry points 加载扩展
"""
from aury.agents.cli.main import app, main
from aury.agents.cli.extensions import (
    ExtensionRegistry,
    ExtensionInfo,
    registry,
    register_agent,
    register_tool,
    get_agent,
    get_tool,
    auto_discover,
)

__all__ = [
    "app",
    "main",
    # Extensions
    "ExtensionRegistry",
    "ExtensionInfo",
    "registry",
    "register_agent",
    "register_tool",
    "get_agent",
    "get_tool",
    "auto_discover",
]
