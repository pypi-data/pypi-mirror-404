"""
交互式对话命令
==============

提供命令行交互式对话功能。
"""
import asyncio
from typing import Optional, Any
from uuid import uuid4

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from aury.agents.core import Session, InvocationContext
from aury.agents.react import ReactAgent

console = Console()


class DefaultChatAgent(ReactAgent):
    """默认对话 Agent。"""
    
    name = "chat_agent"
    description = "通用对话助手"
    system_prompt = """你是一个友好的 AI 助手。请用中文回答用户的问题。"""
    tools = []


async def chat_command(
    agent_name: Optional[str] = None,
    session_id: Optional[str] = None,
    config: Optional[dict] = None,
    verbose: bool = False,
):
    """
    运行交互式对话。
    
    Args:
        agent_name: Agent 名称或模块路径
        session_id: 会话 ID（可选，用于恢复会话）
        config: 配置字典
        verbose: 是否显示详细信息
    """
    config = config or {}
    
    # 显示欢迎信息
    console.print(Panel(
        "[bold blue]Aury Agent 交互式对话[/bold blue]\n\n"
        "输入消息与 Agent 对话\n"
        "输入 /help 查看可用命令\n"
        "输入 /quit 或按 Ctrl+C 退出",
        title="欢迎",
    ))
    
    # 创建或加载会话
    if session_id:
        console.print(f"[dim]恢复会话: {session_id}[/dim]")
        session = Session(session_id=session_id)
        # TODO: 从存储加载会话
    else:
        session_id = f"chat-{uuid4().hex[:8]}"
        session = Session(session_id=session_id)
        console.print(f"[dim]新会话: {session_id}[/dim]")
    
    # 创建 Agent
    agent = await _create_agent(agent_name, config)
    
    if verbose:
        console.print(f"[dim]使用 Agent: {agent.name}[/dim]")
    
    # 创建上下文
    context = InvocationContext(session=session)
    
    # 主循环
    while True:
        try:
            # 获取用户输入
            user_input = Prompt.ask("\n[bold cyan]你[/bold cyan]")
            
            if not user_input.strip():
                continue
            
            # 处理命令
            if user_input.startswith("/"):
                should_continue = await _handle_command(
                    user_input, session, context, verbose
                )
                if not should_continue:
                    break
                continue
            
            # 运行 Agent
            console.print("[dim]思考中...[/dim]")
            
            try:
                result = await agent.run(user_input, context)
                
                # 显示响应
                console.print()
                console.print(Panel(
                    Markdown(result.output) if result.output else "[dim]无响应[/dim]",
                    title="[bold green]Agent[/bold green]",
                    border_style="green",
                ))
                
                # 显示工具调用（详细模式）
                if verbose and hasattr(result, 'tool_calls') and result.tool_calls:
                    console.print("[dim]工具调用:[/dim]")
                    for tc in result.tool_calls:
                        console.print(f"  [dim]- {tc.name}[/dim]")
                
            except Exception as e:
                console.print(f"[red]错误: {e}[/red]")
                if verbose:
                    import traceback
                    console.print(f"[dim]{traceback.format_exc()}[/dim]")
        
        except KeyboardInterrupt:
            console.print("\n[yellow]收到中断信号[/yellow]")
            break
        except EOFError:
            break
    
    # 退出
    console.print("\n[dim]再见！[/dim]")


async def _create_agent(
    agent_name: Optional[str],
    config: dict,
) -> ReactAgent:
    """创建 Agent 实例。"""
    
    if agent_name is None:
        # 使用默认 Agent
        return DefaultChatAgent()
    
    # 尝试从模块加载
    if "." in agent_name or agent_name.endswith(".py"):
        try:
            import importlib.util
            from pathlib import Path
            
            if agent_name.endswith(".py"):
                # 从文件加载
                path = Path(agent_name)
                spec = importlib.util.spec_from_file_location("agent_module", path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                # 从模块路径加载
                module = importlib.import_module(agent_name)
            
            # 查找 Agent 类
            for name in dir(module):
                obj = getattr(module, name)
                if (
                    isinstance(obj, type)
                    and issubclass(obj, ReactAgent)
                    and obj is not ReactAgent
                ):
                    return obj()
            
            raise ValueError(f"模块中未找到 Agent 类: {agent_name}")
        
        except Exception as e:
            console.print(f"[yellow]无法加载 Agent '{agent_name}': {e}[/yellow]")
            console.print("[dim]使用默认 Agent[/dim]")
            return DefaultChatAgent()
    
    # TODO: 从注册表查找已注册的 Agent
    console.print(f"[yellow]未找到 Agent '{agent_name}'，使用默认 Agent[/yellow]")
    return DefaultChatAgent()


async def _handle_command(
    command: str,
    session: Session,
    context: InvocationContext,
    verbose: bool,
) -> bool:
    """
    处理斜杠命令。
    
    Returns:
        bool: 是否继续对话
    """
    cmd = command.strip().lower()
    
    if cmd in ["/quit", "/exit", "/q"]:
        return False
    
    elif cmd == "/help":
        console.print(Panel(
            "[bold]可用命令:[/bold]\n\n"
            "/help     - 显示帮助信息\n"
            "/quit     - 退出对话\n"
            "/clear    - 清空对话历史\n"
            "/session  - 显示当前会话信息\n"
            "/history  - 显示对话历史\n"
            "/save     - 保存当前会话\n"
            "/verbose  - 切换详细模式",
            title="帮助",
        ))
    
    elif cmd == "/clear":
        context.history = []
        console.print("[green]对话历史已清空[/green]")
    
    elif cmd == "/session":
        console.print(Panel(
            f"会话 ID: {session.session_id}\n"
            f"消息数: {len(context.history) if hasattr(context, 'history') else 0}",
            title="会话信息",
        ))
    
    elif cmd == "/history":
        if hasattr(context, 'history') and context.history:
            for msg in context.history[-10:]:  # 最近 10 条
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:100]
                console.print(f"[dim]{role}: {content}...[/dim]")
        else:
            console.print("[dim]暂无对话历史[/dim]")
    
    elif cmd == "/save":
        # TODO: 实现会话保存
        console.print("[green]会话已保存[/green]")
    
    elif cmd == "/verbose":
        console.print(f"[dim]详细模式: {'开启' if verbose else '关闭'}[/dim]")
    
    else:
        console.print(f"[yellow]未知命令: {command}[/yellow]")
        console.print("[dim]输入 /help 查看可用命令[/dim]")
    
    return True
