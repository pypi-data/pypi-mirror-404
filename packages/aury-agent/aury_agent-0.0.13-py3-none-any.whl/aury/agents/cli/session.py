"""
会话管理命令
============

管理 Agent 会话。
"""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from aury.agents.cli.config import load_config, DEFAULT_CONFIG_DIR

session_app = typer.Typer(help="会话管理命令")
console = Console()

# 默认会话存储路径
DEFAULT_SESSIONS_DIR = DEFAULT_CONFIG_DIR / "sessions"


def _get_session_service(config: dict):
    """获取会话服务实例。"""
    from aury.agents.core.services import FileSessionService
    
    storage_path = config.get("session", {}).get(
        "storage_path",
        str(DEFAULT_SESSIONS_DIR)
    )
    
    return FileSessionService(storage_path=storage_path)


@session_app.command("list")
def list_sessions(
    config_file: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="配置文件路径",
    ),
    limit: int = typer.Option(
        20,
        "--limit", "-n",
        help="显示数量限制",
    ),
):
    """列出所有会话。"""
    config = load_config(config_file)
    service = _get_session_service(config)
    
    # 获取会话列表
    sessions = asyncio.run(service.list())
    
    if not sessions:
        console.print("[dim]暂无会话[/dim]")
        return
    
    table = Table(title=f"会话列表 (共 {len(sessions)} 个)")
    table.add_column("会话 ID", style="cyan")
    table.add_column("创建时间")
    table.add_column("消息数")
    table.add_column("状态")
    
    for session_id in sessions[:limit]:
        try:
            session = asyncio.run(service.load(session_id))
            created = session.metadata.get("created_at", "-")
            msg_count = len(session.invocations)
            status = "活跃" if session.invocations else "空闲"
            table.add_row(session_id, str(created)[:19], str(msg_count), status)
        except Exception:
            table.add_row(session_id, "-", "-", "[red]错误[/red]")
    
    console.print(table)
    
    if len(sessions) > limit:
        console.print(f"[dim]还有 {len(sessions) - limit} 个会话未显示[/dim]")


@session_app.command("show")
def show_session(
    session_id: str = typer.Argument(
        ...,
        help="会话 ID",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="配置文件路径",
    ),
):
    """显示会话详情。"""
    config = load_config(config_file)
    service = _get_session_service(config)
    
    try:
        session = asyncio.run(service.load(session_id))
    except Exception as e:
        console.print(f"[red]无法加载会话: {e}[/red]")
        raise typer.Exit(1)
    
    # 会话信息
    info = [
        f"会话 ID: {session.session_id}",
        f"调用数: {len(session.invocations)}",
    ]
    
    # 元数据
    if session.metadata:
        info.append("")
        info.append("[bold]元数据:[/bold]")
        for key, value in session.metadata.items():
            info.append(f"  {key}: {value}")
    
    # 调用历史
    if session.invocations:
        info.append("")
        info.append("[bold]最近调用:[/bold]")
        for inv in session.invocations[-5:]:
            info.append(f"  - {inv.invocation_id}: {inv.status}")
    
    console.print(Panel(
        "\n".join(info),
        title=f"会话: {session_id}",
    ))


@session_app.command("delete")
def delete_session(
    session_id: str = typer.Argument(
        ...,
        help="会话 ID",
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="强制删除，不询问确认",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="配置文件路径",
    ),
):
    """删除会话。"""
    config = load_config(config_file)
    service = _get_session_service(config)
    
    if not force:
        confirm = typer.confirm(f"确定要删除会话 {session_id} 吗？")
        if not confirm:
            console.print("[dim]已取消[/dim]")
            return
    
    try:
        asyncio.run(service.delete(session_id))
        console.print(f"[green]会话已删除: {session_id}[/green]")
    except Exception as e:
        console.print(f"[red]删除失败: {e}[/red]")
        raise typer.Exit(1)


@session_app.command("clear")
def clear_sessions(
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="强制删除，不询问确认",
    ),
    older_than: Optional[int] = typer.Option(
        None,
        "--older-than",
        help="删除超过指定天数的会话",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="配置文件路径",
    ),
):
    """清理会话。"""
    config = load_config(config_file)
    service = _get_session_service(config)
    
    sessions = asyncio.run(service.list())
    
    if not sessions:
        console.print("[dim]暂无会话[/dim]")
        return
    
    to_delete = []
    
    if older_than:
        # 筛选旧会话
        cutoff = datetime.now().timestamp() - (older_than * 86400)
        
        for session_id in sessions:
            try:
                session = asyncio.run(service.load(session_id))
                created = session.metadata.get("created_at")
                if created:
                    created_ts = datetime.fromisoformat(created).timestamp()
                    if created_ts < cutoff:
                        to_delete.append(session_id)
            except Exception:
                pass
    else:
        to_delete = sessions
    
    if not to_delete:
        console.print("[dim]没有符合条件的会话[/dim]")
        return
    
    if not force:
        console.print(f"将删除 {len(to_delete)} 个会话:")
        for sid in to_delete[:5]:
            console.print(f"  - {sid}")
        if len(to_delete) > 5:
            console.print(f"  ... 还有 {len(to_delete) - 5} 个")
        
        confirm = typer.confirm("确定要删除这些会话吗？")
        if not confirm:
            console.print("[dim]已取消[/dim]")
            return
    
    # 执行删除
    deleted = 0
    for session_id in to_delete:
        try:
            asyncio.run(service.delete(session_id))
            deleted += 1
        except Exception:
            pass
    
    console.print(f"[green]已删除 {deleted} 个会话[/green]")


@session_app.command("resume")
def resume_session(
    session_id: str = typer.Argument(
        ...,
        help="会话 ID",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="配置文件路径",
    ),
):
    """恢复会话并继续对话。"""
    from aury.agents.cli.chat import chat_command
    
    config = load_config(config_file)
    
    # 验证会话存在
    service = _get_session_service(config)
    try:
        asyncio.run(service.load(session_id))
    except Exception as e:
        console.print(f"[red]会话不存在: {e}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[dim]恢复会话: {session_id}[/dim]")
    
    # 启动对话
    asyncio.run(chat_command(
        session_id=session_id,
        config=config,
        verbose=False,
    ))


@session_app.command("export")
def export_session(
    session_id: str = typer.Argument(
        ...,
        help="会话 ID",
    ),
    output: Path = typer.Option(
        None,
        "--output", "-o",
        help="输出文件路径",
    ),
    format: str = typer.Option(
        "json",
        "--format",
        help="输出格式 (json/yaml)",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="配置文件路径",
    ),
):
    """导出会话数据。"""
    import json
    import yaml
    
    config = load_config(config_file)
    service = _get_session_service(config)
    
    try:
        session = asyncio.run(service.load(session_id))
    except Exception as e:
        console.print(f"[red]无法加载会话: {e}[/red]")
        raise typer.Exit(1)
    
    # 转换为字典
    data = {
        "session_id": session.session_id,
        "metadata": session.metadata,
        "invocations": [
            {
                "invocation_id": inv.invocation_id,
                "status": inv.status,
            }
            for inv in session.invocations
        ],
    }
    
    # 格式化输出
    if format == "yaml":
        content = yaml.safe_dump(data, allow_unicode=True, default_flow_style=False)
    else:
        content = json.dumps(data, ensure_ascii=False, indent=2)
    
    # 输出
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        console.print(f"[green]已导出到: {output}[/green]")
    else:
        console.print(content)
