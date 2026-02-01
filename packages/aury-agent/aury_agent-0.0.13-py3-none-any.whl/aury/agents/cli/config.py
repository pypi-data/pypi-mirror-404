"""
配置管理命令
============

管理 Aury Agent 的配置文件。
"""
import os
from pathlib import Path
from typing import Optional, Any

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

config_app = typer.Typer(help="配置管理命令")
console = Console()

# 默认配置目录
DEFAULT_CONFIG_DIR = Path.home() / ".aury"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"


def get_default_config() -> dict:
    """获取默认配置。"""
    return {
        "agent": {
            "default": "chat_agent",
            "max_iterations": 20,
        },
        "model": {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 4096,
        },
        "session": {
            "storage_path": str(DEFAULT_CONFIG_DIR / "sessions"),
            "auto_save": True,
            "max_history": 100,
        },
        "logging": {
            "level": "INFO",
            "file": None,
        },
    }


def load_config(config_path: Optional[Path] = None) -> dict:
    """
    加载配置文件。
    
    Args:
        config_path: 配置文件路径，为 None 时使用默认路径
        
    Returns:
        配置字典
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_FILE
    
    config = get_default_config()
    
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f) or {}
            
            # 合并用户配置
            _deep_merge(config, user_config)
        except Exception as e:
            console.print(f"[yellow]警告: 无法加载配置文件 {config_path}: {e}[/yellow]")
    
    return config


def save_config(config: dict, config_path: Optional[Path] = None) -> None:
    """保存配置文件。"""
    if config_path is None:
        config_path = DEFAULT_CONFIG_FILE
    
    # 确保目录存在
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, allow_unicode=True, default_flow_style=False)


def _deep_merge(base: dict, override: dict) -> None:
    """深度合并字典。"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


@config_app.command("show")
def show_config(
    config_file: Optional[Path] = typer.Option(
        None,
        "--file", "-f",
        help="配置文件路径",
    ),
):
    """显示当前配置。"""
    config = load_config(config_file)
    
    yaml_str = yaml.safe_dump(config, allow_unicode=True, default_flow_style=False)
    
    console.print(Panel(
        Syntax(yaml_str, "yaml", theme="monokai"),
        title="当前配置",
    ))


@config_app.command("init")
def init_config(
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="强制覆盖已存在的配置",
    ),
):
    """初始化默认配置文件。"""
    if DEFAULT_CONFIG_FILE.exists() and not force:
        console.print(f"[yellow]配置文件已存在: {DEFAULT_CONFIG_FILE}[/yellow]")
        console.print("[dim]使用 --force 覆盖[/dim]")
        raise typer.Exit(1)
    
    # 创建默认配置
    config = get_default_config()
    save_config(config)
    
    console.print(f"[green]配置文件已创建: {DEFAULT_CONFIG_FILE}[/green]")


@config_app.command("set")
def set_config(
    key: str = typer.Argument(..., help="配置项键名（用点号分隔，如 model.temperature）"),
    value: str = typer.Argument(..., help="配置项值"),
    config_file: Optional[Path] = typer.Option(
        None,
        "--file", "-f",
        help="配置文件路径",
    ),
):
    """设置配置项。"""
    config = load_config(config_file)
    
    # 解析键路径
    keys = key.split(".")
    current = config
    
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    # 尝试解析值类型
    try:
        # 尝试解析为数字
        if "." in value:
            parsed_value = float(value)
        else:
            parsed_value = int(value)
    except ValueError:
        # 尝试解析为布尔值
        if value.lower() in ["true", "yes"]:
            parsed_value = True
        elif value.lower() in ["false", "no"]:
            parsed_value = False
        elif value.lower() == "null":
            parsed_value = None
        else:
            parsed_value = value
    
    current[keys[-1]] = parsed_value
    
    # 保存
    save_config(config, config_file)
    
    console.print(f"[green]已设置 {key} = {parsed_value}[/green]")


@config_app.command("get")
def get_config(
    key: str = typer.Argument(..., help="配置项键名"),
    config_file: Optional[Path] = typer.Option(
        None,
        "--file", "-f",
        help="配置文件路径",
    ),
):
    """获取配置项值。"""
    config = load_config(config_file)
    
    # 解析键路径
    keys = key.split(".")
    current = config
    
    try:
        for k in keys:
            current = current[k]
        console.print(f"{key} = {current}")
    except KeyError:
        console.print(f"[red]配置项不存在: {key}[/red]")
        raise typer.Exit(1)


@config_app.command("path")
def config_path():
    """显示配置文件路径。"""
    console.print(f"配置目录: {DEFAULT_CONFIG_DIR}")
    console.print(f"配置文件: {DEFAULT_CONFIG_FILE}")
    console.print(f"文件存在: {'是' if DEFAULT_CONFIG_FILE.exists() else '否'}")


@config_app.command("edit")
def edit_config():
    """使用默认编辑器编辑配置文件。"""
    import subprocess
    
    if not DEFAULT_CONFIG_FILE.exists():
        console.print("[yellow]配置文件不存在，先创建默认配置[/yellow]")
        config = get_default_config()
        save_config(config)
    
    editor = os.environ.get("EDITOR", "vim")
    
    try:
        subprocess.run([editor, str(DEFAULT_CONFIG_FILE)])
    except FileNotFoundError:
        console.print(f"[red]编辑器未找到: {editor}[/red]")
        console.print(f"[dim]请设置 EDITOR 环境变量或手动编辑: {DEFAULT_CONFIG_FILE}[/dim]")
