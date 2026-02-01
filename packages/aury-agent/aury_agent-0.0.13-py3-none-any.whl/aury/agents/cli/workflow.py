"""
Workflow 命令
=============

运行和管理 Workflow。
"""
import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from aury.agents.cli.config import load_config

workflow_app = typer.Typer(help="Workflow 相关命令")
console = Console()


@workflow_app.command("run")
def run_workflow(
    workflow_file: Path = typer.Argument(
        ...,
        help="Workflow 定义文件路径（.py 或 .yaml）",
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
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="显示详细输出",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="模拟运行，不实际执行",
    ),
):
    """
    运行 Workflow。
    
    示例:
        aury-agent workflow run pipeline.py
        aury-agent workflow run pipeline.yaml --input '{"data": "test"}'
    """
    # 加载配置
    cfg = load_config(config_file)
    
    if not workflow_file.exists():
        console.print(f"[red]错误: Workflow 文件不存在: {workflow_file}[/red]")
        raise typer.Exit(1)
    
    # 解析输入
    input_dict = {}
    if input_data:
        try:
            input_dict = json.loads(input_data)
        except json.JSONDecodeError as e:
            console.print(f"[red]错误: 无效的 JSON 输入: {e}[/red]")
            raise typer.Exit(1)
    
    console.print(f"[bold]运行 Workflow: {workflow_file}[/bold]")
    
    if dry_run:
        console.print("[yellow]模拟运行模式[/yellow]")
        _dry_run_workflow(workflow_file, input_dict, verbose)
        return
    
    # 实际运行
    asyncio.run(_execute_workflow(workflow_file, input_dict, cfg, verbose))


async def _execute_workflow(
    workflow_file: Path,
    input_data: dict,
    config: dict,
    verbose: bool,
):
    """执行 Workflow。"""
    from aury.agents.workflow import WorkflowExecutor
    from aury.agents.core import Session, InvocationContext
    
    # 加载 Workflow
    workflow = await _load_workflow(workflow_file)
    
    if workflow is None:
        console.print("[red]无法加载 Workflow[/red]")
        return
    
    console.print(f"[dim]Workflow: {workflow.name}[/dim]")
    console.print(f"[dim]步骤数: {len(workflow.step_map)}[/dim]")
    
    # 创建上下文
    session = Session(session_id=f"workflow-{workflow.name}")
    context = InvocationContext(session=session)
    
    # 创建执行器
    executor = WorkflowExecutor(workflow)
    
    # 执行
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("执行中...", total=None)
        
        try:
            result = await executor.execute(context, input_data=input_data)
            progress.update(task, description="完成")
        except Exception as e:
            progress.update(task, description=f"[red]失败: {e}[/red]")
            raise
    
    # 显示结果
    console.print()
    
    if result.success:
        console.print(Panel(
            f"[green]Workflow 执行成功[/green]\n\n"
            f"完成步骤: {', '.join(result.state.get_completed_steps())}",
            title="结果",
        ))
    else:
        console.print(Panel(
            f"[red]Workflow 执行失败[/red]\n\n"
            f"失败步骤: {', '.join([s for s in result.state.step_statuses if result.state.is_step_failed(s)])}",
            title="结果",
        ))
    
    # 详细输出
    if verbose:
        console.print("\n[bold]步骤详情:[/bold]")
        for step_id, status in result.state.step_statuses.items():
            step_result = result.state.get_step_result(step_id)
            console.print(f"  {step_id}: {status}")
            if step_result:
                console.print(f"    结果: {step_result}")


async def _load_workflow(workflow_file: Path):
    """加载 Workflow 定义。"""
    if workflow_file.suffix == ".py":
        # 从 Python 文件加载
        import importlib.util
        
        spec = importlib.util.spec_from_file_location("workflow_module", workflow_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 查找 Workflow 对象或构建函数
        if hasattr(module, "workflow"):
            return module.workflow
        elif hasattr(module, "build_workflow"):
            return module.build_workflow()
        elif hasattr(module, "create_workflow"):
            return module.create_workflow()
        else:
            console.print("[yellow]警告: 未找到 workflow 对象或构建函数[/yellow]")
            return None
    
    elif workflow_file.suffix in [".yaml", ".yml"]:
        # 从 YAML 文件加载
        # TODO: 实现 YAML 格式的 Workflow 定义
        console.print("[yellow]YAML Workflow 格式暂未支持[/yellow]")
        return None
    
    else:
        console.print(f"[red]不支持的文件格式: {workflow_file.suffix}[/red]")
        return None


def _dry_run_workflow(workflow_file: Path, input_data: dict, verbose: bool):
    """模拟运行 Workflow。"""
    console.print("\n[dim]模拟运行步骤:[/dim]")
    console.print(f"  1. 加载 Workflow: {workflow_file}")
    console.print(f"  2. 验证输入: {input_data or '(无输入)'}")
    console.print("  3. 执行各步骤 (模拟)")
    console.print("  4. 返回结果")


@workflow_app.command("list")
def list_workflows(
    directory: Path = typer.Option(
        Path("."),
        "--dir", "-d",
        help="搜索目录",
    ),
):
    """列出可用的 Workflow 文件。"""
    workflows = []
    
    # 搜索 Python 文件
    for py_file in directory.glob("**/*.py"):
        if "workflow" in py_file.name.lower():
            workflows.append(py_file)
    
    # 搜索 YAML 文件
    for yaml_file in directory.glob("**/*.yaml"):
        if "workflow" in yaml_file.name.lower():
            workflows.append(yaml_file)
    
    if not workflows:
        console.print("[dim]未找到 Workflow 文件[/dim]")
        return
    
    table = Table(title="可用 Workflow")
    table.add_column("文件", style="cyan")
    table.add_column("类型")
    
    for wf in workflows:
        file_type = "Python" if wf.suffix == ".py" else "YAML"
        table.add_row(str(wf.relative_to(directory)), file_type)
    
    console.print(table)


@workflow_app.command("validate")
def validate_workflow(
    workflow_file: Path = typer.Argument(
        ...,
        help="Workflow 定义文件路径",
    ),
):
    """验证 Workflow 定义。"""
    if not workflow_file.exists():
        console.print(f"[red]文件不存在: {workflow_file}[/red]")
        raise typer.Exit(1)
    
    console.print(f"验证 Workflow: {workflow_file}")
    
    try:
        workflow = asyncio.run(_load_workflow(workflow_file))
        
        if workflow is None:
            console.print("[red]验证失败: 无法加载 Workflow[/red]")
            raise typer.Exit(1)
        
        # 验证
        errors = []
        
        if not workflow.entry_step_id:
            errors.append("未定义入口步骤")
        
        if not workflow.step_map:
            errors.append("没有定义任何步骤")
        
        if workflow.entry_step_id and workflow.entry_step_id not in workflow.step_map:
            errors.append(f"入口步骤不存在: {workflow.entry_step_id}")
        
        if errors:
            console.print("[red]验证失败:[/red]")
            for err in errors:
                console.print(f"  - {err}")
            raise typer.Exit(1)
        
        console.print(f"[green]验证通过[/green]")
        console.print(f"  名称: {workflow.name}")
        console.print(f"  步骤数: {len(workflow.step_map)}")
        console.print(f"  入口: {workflow.entry_step_id}")
        
    except Exception as e:
        console.print(f"[red]验证失败: {e}[/red]")
        raise typer.Exit(1)
