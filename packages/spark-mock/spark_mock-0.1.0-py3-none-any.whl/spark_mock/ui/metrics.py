"""
Metrics Collector - collects execution metrics for UI display.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import time


@dataclass
class StageMetrics:
    """Metrics for a single stage."""
    stage_id: int
    name: str
    num_tasks: int = 0
    input_rows: int = 0
    output_rows: int = 0
    input_bytes: int = 0
    output_bytes: int = 0
    shuffle_read_bytes: int = 0
    shuffle_write_bytes: int = 0
    duration_ms: float = 0
    status: str = "pending"


@dataclass
class TaskMetrics:
    """Metrics for a single task."""
    task_id: int
    stage_id: int
    partition_id: int
    duration_ms: float = 0
    input_rows: int = 0
    output_rows: int = 0
    status: str = "pending"


class MetricsCollector:
    """Collects and aggregates execution metrics."""
    
    def __init__(self):
        self.stages: Dict[int, StageMetrics] = {}
        self.tasks: Dict[int, List[TaskMetrics]] = {}
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
    
    def start_collection(self):
        """Start metrics collection."""
        self._start_time = time.time()
        self._end_time = None
        self.stages.clear()
        self.tasks.clear()
    
    def end_collection(self):
        """End metrics collection."""
        self._end_time = time.time()
    
    def add_stage(self, stage_id: int, name: str, num_partitions: int) -> StageMetrics:
        """Add a new stage to track."""
        metrics = StageMetrics(
            stage_id=stage_id,
            name=name,
            num_tasks=num_partitions
        )
        self.stages[stage_id] = metrics
        self.tasks[stage_id] = []
        return metrics
    
    def update_stage(self, stage_id: int, **kwargs):
        """Update stage metrics."""
        if stage_id in self.stages:
            for key, value in kwargs.items():
                if hasattr(self.stages[stage_id], key):
                    setattr(self.stages[stage_id], key, value)
    
    def add_task(self, stage_id: int, task_id: int, partition_id: int) -> TaskMetrics:
        """Add a new task to track."""
        metrics = TaskMetrics(
            task_id=task_id,
            stage_id=stage_id,
            partition_id=partition_id
        )
        if stage_id not in self.tasks:
            self.tasks[stage_id] = []
        self.tasks[stage_id].append(metrics)
        return metrics
    
    @property
    def total_duration_ms(self) -> float:
        """Get total duration in milliseconds."""
        if self._start_time and self._end_time:
            return (self._end_time - self._start_time) * 1000
        elif self._start_time:
            return (time.time() - self._start_time) * 1000
        return 0
    
    @property
    def total_input_rows(self) -> int:
        """Get total input rows across all stages."""
        return sum(s.input_rows for s in self.stages.values())
    
    @property
    def total_output_rows(self) -> int:
        """Get total output rows from the last stage."""
        if not self.stages:
            return 0
        last_stage = max(self.stages.values(), key=lambda s: s.stage_id)
        return last_stage.output_rows
    
    @property
    def total_shuffle_read(self) -> int:
        """Get total shuffle read bytes."""
        return sum(s.shuffle_read_bytes for s in self.stages.values())
    
    @property
    def total_shuffle_write(self) -> int:
        """Get total shuffle write bytes."""
        return sum(s.shuffle_write_bytes for s in self.stages.values())
    
    def format_bytes(self, num_bytes: int) -> str:
        """Format bytes to human readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(num_bytes) < 1024.0:
                return f"{num_bytes:.1f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.1f} PB"
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        return {
            "duration_ms": self.total_duration_ms,
            "num_stages": len(self.stages),
            "input_rows": self.total_input_rows,
            "output_rows": self.total_output_rows,
            "shuffle_read": self.format_bytes(self.total_shuffle_read),
            "shuffle_write": self.format_bytes(self.total_shuffle_write),
        }
