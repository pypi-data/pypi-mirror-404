"""
Spark UI Console - displays execution information in terminal.
"""
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import box
import time

from spark_mock.core.execution import JobMetrics
from spark_mock.core.lazy import Stage, OperationType


class SparkUI:
    """Console-based Spark UI simulation."""
    
    def __init__(self, app_name: str = "SparkMockApp", enabled: bool = True):
        self.app_name = app_name
        self.enabled = enabled
        self.console = Console()
        self._job_counter = 0
    
    def display_job(self, job: JobMetrics):
        """Display job execution information."""
        if not self.enabled:
            return
        
        # Create main panel
        content = self._build_job_content(job)
        
        panel = Panel(
            content,
            title=f"[bold cyan]SPARK MOCK UI - Job #{job.job_id}[/bold cyan]",
            subtitle=f"[dim]{self.app_name}[/dim]",
            border_style="cyan",
            box=box.DOUBLE,
            padding=(0, 1),
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
    
    def _build_job_content(self, job: JobMetrics) -> str:
        """Build the content for job display."""
        lines = []
        
        # Status line
        status_icon = "✓" if job.status == "completed" else "✗" if job.status == "failed" else "⋯"
        status_color = "green" if job.status == "completed" else "red" if job.status == "failed" else "yellow"
        lines.append(f"[bold]Status:[/bold] [{status_color}]{status_icon} {job.status.upper()}[/{status_color}]")
        lines.append(f"[bold]Duration:[/bold] {job.duration_str}")
        lines.append("")
        
        # Stages section
        lines.append("[bold underline]STAGES[/bold underline]")
        for i, stage in enumerate(job.stages):
            prefix = "└─" if i == len(job.stages) - 1 else "├─"
            status_icon = "✓" if stage.status == "completed" else "✗" if stage.status == "failed" else "○"
            status_color = "green" if stage.status == "completed" else "red" if stage.status == "failed" else "dim"
            
            stage_desc = stage.describe()
            lines.append(f"  {prefix} [{status_color}]{status_icon}[/{status_color}] Stage {stage.id}: {stage_desc}")
        
        lines.append("")
        
        # Execution Plan section
        lines.append("[bold underline]EXECUTION PLAN[/bold underline]")
        plan_lines = self._format_plan(job.stages)
        for line in plan_lines:
            lines.append(f"  {line}")
        
        lines.append("")
        
        # Statistics section
        lines.append("[bold underline]STATISTICS[/bold underline]")
        lines.append(f"  • Input Rows: [cyan]{job.input_rows:,}[/cyan]")
        lines.append(f"  • Output Rows: [cyan]{job.output_rows:,}[/cyan]")
        
        shuffle_read = self._format_bytes(job.shuffle_stats.shuffle_read_bytes)
        shuffle_write = self._format_bytes(job.shuffle_stats.shuffle_write_bytes)
        lines.append(f"  • Shuffle Read: [yellow]{shuffle_read}[/yellow]")
        lines.append(f"  • Shuffle Write: [yellow]{shuffle_write}[/yellow]")
        
        return "\n".join(lines)
    
    def _format_plan(self, stages: List[Stage]) -> List[str]:
        """Format execution plan as a tree."""
        lines = []
        
        # Collect all operations in reverse order
        all_ops = []
        for stage in stages:
            all_ops.extend(stage.operations)
        
        for i, op in enumerate(reversed(all_ops)):
            prefix = "+- " if i < len(all_ops) - 1 else "+- "
            indent = "   " * i
            lines.append(f"{indent}{prefix}{self._format_operation(op)}")
        
        return lines[-5:] if len(lines) > 5 else lines  # Limit to 5 lines
    
    def _format_operation(self, op) -> str:
        """Format a single operation."""
        op_type = op.op_type
        
        if op_type == OperationType.SELECT:
            cols = op.params.get("columns", [])
            return f"[blue]Project[/blue] [{', '.join(str(c) for c in cols[:3])}{'...' if len(cols) > 3 else ''}]"
        elif op_type == OperationType.FILTER:
            return f"[blue]Filter[/blue] ({op.params.get('condition', '')})"
        elif op_type == OperationType.GROUP_BY:
            cols = op.params.get("columns", [])
            return f"[blue]HashAggregate[/blue] (keys=[{', '.join(cols)}])"
        elif op_type == OperationType.AGG:
            return f"[blue]Aggregate[/blue]"
        elif op_type == OperationType.JOIN:
            how = op.params.get("how", "inner")
            return f"[blue]BroadcastHashJoin[/blue] {how}"
        elif op_type == OperationType.ORDER_BY:
            cols = op.params.get("columns", [])
            return f"[blue]Sort[/blue] [{', '.join(str(c) for c in cols)}]"
        elif op_type == OperationType.SCAN_CSV:
            return f"[green]FileScan csv[/green] [{op.params.get('path', '')}]"
        elif op_type == OperationType.CREATE_DATAFRAME:
            return f"[green]LocalTableScan[/green] [{op.params.get('num_rows', 0)} rows]"
        elif op_type == OperationType.LIMIT:
            return f"[blue]Limit[/blue] {op.params.get('n', '')}"
        elif op_type == OperationType.REPARTITION:
            return f"[magenta]Exchange[/magenta] ({op.params.get('num_partitions', '')} partitions)"
        else:
            return f"[blue]{op_type.value}[/blue]"
    
    def _format_bytes(self, num_bytes: int) -> str:
        """Format bytes to human readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(num_bytes) < 1024.0:
                return f"{num_bytes:.1f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.1f} PB"
    
    def display_schema(self, schema_str: str):
        """Display DataFrame schema."""
        if not self.enabled:
            print(schema_str)
            return
        
        self.console.print(Panel(
            schema_str,
            title="[bold]Schema[/bold]",
            border_style="blue",
            box=box.ROUNDED,
        ))
    
    def display_explain(self, plan_str: str):
        """Display execution plan."""
        if not self.enabled:
            print(plan_str)
            return
        
        self.console.print(Panel(
            plan_str,
            title="[bold]Physical Plan[/bold]",
            border_style="green",
            box=box.ROUNDED,
        ))
    
    def display_dataframe(self, table_str: str, title: str = "DataFrame"):
        """Display DataFrame as a table."""
        if not self.enabled:
            print(table_str)
            return
        
        self.console.print(Panel(
            table_str,
            title=f"[bold]{title}[/bold]",
            border_style="white",
            box=box.ROUNDED,
        ))
