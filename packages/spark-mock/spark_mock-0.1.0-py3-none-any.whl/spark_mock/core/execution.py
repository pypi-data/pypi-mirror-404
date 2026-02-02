"""
Execution Engine - wraps Polars for execution with metrics collection.
"""
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
import time
import polars as pl

from spark_mock.core.lazy import LazyExecutionPlan, Stage, OperationType
from spark_mock.core.partition import PartitionManager, PartitionInfo, ShuffleStats


@dataclass
class JobMetrics:
    """Metrics for a job execution."""
    job_id: int
    start_time: float = 0
    end_time: float = 0
    input_rows: int = 0
    output_rows: int = 0
    stages: List[Stage] = field(default_factory=list)
    shuffle_stats: ShuffleStats = field(default_factory=ShuffleStats)
    status: str = "pending"  # pending, running, completed, failed
    error: Optional[str] = None
    
    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000 if self.end_time else 0
    
    @property
    def duration_str(self) -> str:
        ms = self.duration_ms
        if ms < 1000:
            return f"{ms:.0f}ms"
        return f"{ms/1000:.2f}s"


class ExecutionEngine:
    """Engine that executes DataFrame operations using Polars."""
    
    def __init__(self, num_partitions: int = 4, app_name: str = "SparkMockApp"):
        self.num_partitions = num_partitions
        self.app_name = app_name
        self.partition_manager = PartitionManager(num_partitions)
        self.job_counter = 0
        self.jobs: List[JobMetrics] = []
        self._ui_callback: Optional[Callable[[JobMetrics], None]] = None
    
    def set_ui_callback(self, callback: Callable[[JobMetrics], None]):
        """Set callback for UI updates."""
        self._ui_callback = callback
    
    def execute(self, lazy_df: pl.LazyFrame, plan: LazyExecutionPlan, 
                action: OperationType = OperationType.COLLECT) -> pl.DataFrame:
        """Execute a lazy DataFrame and return the result."""
        self.job_counter += 1
        
        # Create job metrics
        job = JobMetrics(job_id=self.job_counter)
        job.start_time = time.time()
        job.status = "running"
        
        # Build stages from plan
        job.stages = plan.build_stages(self.num_partitions)
        
        # Notify UI of job start
        if self._ui_callback:
            self._ui_callback(job)
        
        try:
            # Execute each stage
            for stage in job.stages:
                stage.status = "running"
                stage_start = time.time()
                
                # Simulate stage execution timing
                # In reality, Polars handles all this internally
                
                stage.duration_ms = (time.time() - stage_start) * 1000
                stage.status = "completed"
            
            # Collect the result
            result = lazy_df.collect()
            
            job.output_rows = len(result)
            job.status = "completed"
            job.end_time = time.time()
            
            # Calculate shuffle stats based on operations
            self._calculate_shuffle_stats(job, result)
            
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.end_time = time.time()
            raise
        finally:
            self.jobs.append(job)
            if self._ui_callback:
                self._ui_callback(job)
        
        return result
    
    def _calculate_shuffle_stats(self, job: JobMetrics, result: pl.DataFrame):
        """Calculate shuffle statistics based on the execution plan."""
        shuffle_ops = {OperationType.GROUP_BY, OperationType.JOIN, 
                       OperationType.ORDER_BY, OperationType.REPARTITION}
        
        for stage in job.stages:
            for op in stage.operations:
                if op.op_type in shuffle_ops:
                    # Estimate shuffle based on result size
                    estimated_size = result.estimated_size()
                    job.shuffle_stats.add_shuffle(
                        records=len(result),
                        size_bytes=estimated_size
                    )
                    stage.shuffle_read = estimated_size // 2
                    stage.shuffle_write = estimated_size // 2
    
    def get_last_job(self) -> Optional[JobMetrics]:
        """Get the most recent job."""
        return self.jobs[-1] if self.jobs else None
    
    def clear_jobs(self):
        """Clear job history."""
        self.jobs.clear()
        self.job_counter = 0
