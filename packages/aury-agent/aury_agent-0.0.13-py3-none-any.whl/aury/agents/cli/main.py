#!/usr/bin/env python3
"""
Aury Agent CLI 主入口
======================

使用方式:
    aury-agent chat              # 启动交互式对话
    aury-agent workflow run      # 运行 Workflow
    aury-agent session list      # 列出会话
    aury-agent config show       # 显示配置
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from aury.agents.cli.chat import chat_command
from aury.agents.cli.workflow import workflow_app
from aury.agents.cli.session import session_app
from aury.agents.cli.config import config_app, load_config

# 创建主应用
app = typer.Typer(
    name="aury-agent",
    help="Aury Agent 命令行工具 - AI Agent 框架",
    add_completion=True,
)

# 注册子命令
app.add_typer(workflow_app, name="workflow", help="Workflow 相关命令")
app.add_typer(session_app, name="session", help="会话管理命令")
app.add_typer(config_app, name="config", help="配置管理命令")

# Rich console 用于美化输出
console = Console()


@app.command()
def chat(
    agent: Optional[str] = typer.Option(
        None,
        "--agent", "-a",
        help="要使用的 Agent 名称或路径",
    ),
    session_id: Optional[str] = typer.Option(
        None,
        "--session", "-s",
        help="会话 ID，用于恢复之前的对话",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="配置文件路径",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="显示详细输出",
    ),
):
    """
    启动交互式对话。
    
    示例:
        aury-agent chat
        aury-agent chat --agent my_agent
        aury-agent chat --session session-123 --verbose
    """
    # 加载配置
    cfg = load_config(config_file)
    
    # 运行交互式对话
    asyncio.run(chat_command(
        agent_name=agent,
        session_id=session_id,
        config=cfg,
        verbose=verbose,
    ))


@app.command()
def run(
    script: Path = typer.Argument(
        ...,
        help="要运行的 Agent 脚本路径",
    ),
    input_data: Optional[str] = typer.Option(
        None,
        "--input", "-i",
        help="输入数据（JSON 格式）",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="配置文件路径",
    ),
):
    """
    运行 Agent 脚本。
    
    示例:
        aury-agent run agent.py
        aury-agent run agent.py --input '{"query": "hello"}'
    """
    import json
    import importlib.util
    
    # 加载配置
    cfg = load_config(config_file)
    
    # 加载脚本
    if not script.exists():
        console.print(f"[red]错误: 脚本文件不存在: {script}[/red]")
        raise typer.Exit(1)
    
    # 解析输入
    input_dict = {}
    if input_data:
        try:
            input_dict = json.loads(input_data)
        except json.JSONDecodeError as e:
            console.print(f"[red]错误: 无效的 JSON 输入: {e}[/red]")
            raise typer.Exit(1)
    
    console.print(f"[green]运行脚本: {script}[/green]")
    
    # 动态导入并运行
    spec = importlib.util.spec_from_file_location("agent_script", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # 查找并运行 main 函数
    if hasattr(module, "main"):
        asyncio.run(module.main())
    else:
        console.print("[yellow]警告: 脚本中没有 main 函数[/yellow]")


@app.command()
def version():
    """显示版本信息。"""
    from aury.agents import __version__
    
    console.print(Panel(
        f"[bold blue]Aury Agent Framework[/bold blue]\n"
        f"版本: {__version__}",
        title="版本信息",
    ))


@app.command()
def info():
    """显示系统信息和配置状态。"""
    import platform
    
    console.print(Panel(
        f"[bold]系统信息[/bold]\n"
        f"Python: {platform.python_version()}\n"
        f"平台: {platform.platform()}\n\n"
        f"[bold]Aury Agent[/bold]\n"
        f"配置目录: ~/.aury/\n"
        f"会话目录: ~/.aury/sessions/",
        title="系统信息",
    ))


@app.callback()
def main_callback(
    ctx: typer.Context,
):
    """
    Aury Agent 命令行工具。
    
    使用 --help 查看各子命令的帮助信息。
    """
    pass


def main():
    """CLI 入口点。"""
    app()


if __name__ == "__main__":
    main()
