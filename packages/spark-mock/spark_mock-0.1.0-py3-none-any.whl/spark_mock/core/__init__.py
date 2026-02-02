"""Core module - execution engine and partition management."""

from spark_mock.core.partition import PartitionManager
from spark_mock.core.execution import ExecutionEngine
from spark_mock.core.lazy import LazyExecutionPlan

__all__ = [
    "PartitionManager",
    "ExecutionEngine",
    "LazyExecutionPlan",
]
