"""
Lazy Execution Plan - tracks operations for lazy evaluation.
"""
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time


class OperationType(Enum):
    """Types of DataFrame operations."""
    # Transformations (lazy)
    SELECT = "select"
    FILTER = "filter"
    GROUP_BY = "groupby"
    AGG = "aggregate"
    JOIN = "join"
    ORDER_BY = "orderby"
    LIMIT = "limit"
    DROP = "drop"
    WITH_COLUMN = "withcolumn"
    WITH_COLUMN_RENAMED = "withcolumnrenamed"
    DISTINCT = "distinct"
    UNION = "union"
    REPARTITION = "repartition"
    COALESCE = "coalesce"
    
    # Sources
    SCAN_CSV = "scan_csv"
    SCAN_JSON = "scan_json"
    SCAN_PARQUET = "scan_parquet"
    CREATE_DATAFRAME = "create_dataframe"
    
    # Actions
    COLLECT = "collect"
    SHOW = "show"
    COUNT = "count"
    FIRST = "first"
    TAKE = "take"
    WRITE = "write"


@dataclass
class Operation:
    """Represents a single operation in the execution plan."""
    op_type: OperationType
    params: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def __repr__(self) -> str:
        params_str = ", ".join(f"{k}={v}" for k, v in self.params.items() if k != "columns")
        if "columns" in self.params:
            params_str += f", cols=[{len(self.params['columns'])} cols]"
        return f"{self.op_type.value}({params_str})" if params_str else self.op_type.value


@dataclass
class Stage:
    """Represents a stage in the execution plan (group of operations)."""
    id: int
    operations: List[Operation] = field(default_factory=list)
    num_partitions: int = 1
    input_rows: int = 0
    output_rows: int = 0
    duration_ms: float = 0
    shuffle_read: int = 0
    shuffle_write: int = 0
    status: str = "pending"  # pending, running, completed
    
    def add_operation(self, op: Operation):
        self.operations.append(op)
    
    def describe(self) -> str:
        """Get a description of this stage."""
        if not self.operations:
            return "empty stage"
        main_op = self.operations[-1]
        return f"{main_op.op_type.value} [{self.num_partitions} partitions]"


class LazyExecutionPlan:
    """Tracks the execution plan for lazy evaluation."""
    
    def __init__(self):
        self.operations: List[Operation] = []
        self.stages: List[Stage] = []
        self._current_stage: Optional[Stage] = None
        self._stage_counter = 0
    
    def add_operation(self, op_type: OperationType, **params) -> "LazyExecutionPlan":
        """Add an operation to the plan."""
        op = Operation(op_type=op_type, params=params)
        self.operations.append(op)
        return self
    
    def copy(self) -> "LazyExecutionPlan":
        """Create a copy of this plan."""
        new_plan = LazyExecutionPlan()
        new_plan.operations = self.operations.copy()
        return new_plan
    
    def build_stages(self, num_partitions: int = 4) -> List[Stage]:
        """Build execution stages from operations."""
        self.stages = []
        self._stage_counter = 0
        
        # Operations that trigger a new stage (shuffle boundaries)
        shuffle_ops = {
            OperationType.REPARTITION,
            OperationType.GROUP_BY,
            OperationType.JOIN,
            OperationType.ORDER_BY,
            OperationType.DISTINCT,
        }
        
        current_stage = Stage(id=self._stage_counter, num_partitions=num_partitions)
        
        for op in self.operations:
            if op.op_type in shuffle_ops and current_stage.operations:
                # Start a new stage
                self.stages.append(current_stage)
                self._stage_counter += 1
                
                # Determine new partition count
                if op.op_type == OperationType.REPARTITION:
                    num_partitions = op.params.get("num_partitions", num_partitions)
                elif op.op_type == OperationType.COALESCE:
                    num_partitions = op.params.get("num_partitions", num_partitions)
                
                current_stage = Stage(id=self._stage_counter, num_partitions=num_partitions)
            
            current_stage.add_operation(op)
        
        if current_stage.operations:
            self.stages.append(current_stage)
        
        return self.stages
    
    def get_plan_string(self, indent: int = 0) -> str:
        """Get a string representation of the execution plan."""
        lines = []
        prefix = "  " * indent
        
        for i, op in enumerate(reversed(self.operations)):
            connector = "+- " if i == len(self.operations) - 1 else "+- "
            lines.append(f"{prefix}{connector}{op}")
            prefix = "  " * indent + "   "
        
        return "\n".join(lines)
    
    def explain(self, extended: bool = False) -> str:
        """Generate explain output like Spark's explain()."""
        lines = ["== Physical Plan =="]
        
        # Build plan tree
        for i, op in enumerate(reversed(self.operations)):
            indent = "   " * i
            connector = "*" if i == 0 else "+-"
            lines.append(f"{indent}{connector} {self._format_operation(op)}")
        
        if extended:
            lines.append("\n== Analyzed Logical Plan ==")
            for op in self.operations:
                lines.append(f"  {op}")
        
        return "\n".join(lines)
    
    def _format_operation(self, op: Operation) -> str:
        """Format an operation for display."""
        if op.op_type == OperationType.SELECT:
            cols = op.params.get("columns", [])
            return f"Project [{', '.join(str(c) for c in cols[:3])}{'...' if len(cols) > 3 else ''}]"
        elif op.op_type == OperationType.FILTER:
            return f"Filter {op.params.get('condition', '')}"
        elif op.op_type == OperationType.GROUP_BY:
            return f"HashAggregate(keys=[{', '.join(op.params.get('columns', []))}])"
        elif op.op_type == OperationType.JOIN:
            return f"BroadcastHashJoin {op.params.get('how', 'inner')}"
        elif op.op_type == OperationType.ORDER_BY:
            return f"Sort [{', '.join(op.params.get('columns', []))}]"
        elif op.op_type == OperationType.SCAN_CSV:
            return f"FileScan csv [{op.params.get('path', '')}]"
        elif op.op_type == OperationType.CREATE_DATAFRAME:
            return f"LocalTableScan [{op.params.get('num_rows', 0)} rows]"
        else:
            return str(op)
