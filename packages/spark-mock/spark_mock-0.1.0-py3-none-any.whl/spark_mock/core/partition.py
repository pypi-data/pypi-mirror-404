"""
Partition Manager - simulates Spark partitioning behavior.
"""
from typing import List, Optional, Any
from dataclasses import dataclass, field
import polars as pl
import time


@dataclass
class Partition:
    """Represents a single partition of data."""
    id: int
    num_rows: int = 0
    size_bytes: int = 0
    
    def __repr__(self) -> str:
        return f"Partition(id={self.id}, rows={self.num_rows}, size={self.size_bytes}B)"


@dataclass
class PartitionInfo:
    """Information about partitioning strategy."""
    num_partitions: int
    partitions: List[Partition] = field(default_factory=list)
    partition_columns: Optional[List[str]] = None
    
    def total_rows(self) -> int:
        return sum(p.num_rows for p in self.partitions)
    
    def total_size(self) -> int:
        return sum(p.size_bytes for p in self.partitions)


class PartitionManager:
    """Manages partition simulation for DataFrames."""
    
    def __init__(self, default_partitions: int = 4):
        self.default_partitions = default_partitions
    
    def create_partitions(self, df: pl.DataFrame, num_partitions: Optional[int] = None) -> PartitionInfo:
        """Create partition info for a DataFrame."""
        num_parts = num_partitions or self.default_partitions
        total_rows = len(df)
        
        if total_rows == 0:
            return PartitionInfo(
                num_partitions=num_parts,
                partitions=[Partition(id=i) for i in range(num_parts)]
            )
        
        # Estimate size
        estimated_size = df.estimated_size()
        
        # Distribute rows across partitions
        rows_per_partition = total_rows // num_parts
        remainder = total_rows % num_parts
        
        partitions = []
        for i in range(num_parts):
            extra = 1 if i < remainder else 0
            partition_rows = rows_per_partition + extra
            partition_size = int(estimated_size * partition_rows / total_rows) if total_rows > 0 else 0
            partitions.append(Partition(
                id=i,
                num_rows=partition_rows,
                size_bytes=partition_size
            ))
        
        return PartitionInfo(
            num_partitions=num_parts,
            partitions=partitions
        )
    
    def repartition(self, partition_info: PartitionInfo, num_partitions: int, 
                    columns: Optional[List[str]] = None) -> PartitionInfo:
        """Simulate repartition operation."""
        total_rows = partition_info.total_rows()
        total_size = partition_info.total_size()
        
        rows_per_partition = total_rows // num_partitions if num_partitions > 0 else 0
        remainder = total_rows % num_partitions if num_partitions > 0 else 0
        
        partitions = []
        for i in range(num_partitions):
            extra = 1 if i < remainder else 0
            partition_rows = rows_per_partition + extra
            partition_size = int(total_size * partition_rows / total_rows) if total_rows > 0 else 0
            partitions.append(Partition(
                id=i,
                num_rows=partition_rows,
                size_bytes=partition_size
            ))
        
        return PartitionInfo(
            num_partitions=num_partitions,
            partitions=partitions,
            partition_columns=columns
        )
    
    def coalesce(self, partition_info: PartitionInfo, num_partitions: int) -> PartitionInfo:
        """Simulate coalesce operation (reduce partitions without shuffle)."""
        if num_partitions >= partition_info.num_partitions:
            return partition_info
        
        # Coalesce merges adjacent partitions
        old_partitions = partition_info.partitions
        partitions_per_new = len(old_partitions) // num_partitions
        
        partitions = []
        for i in range(num_partitions):
            start_idx = i * partitions_per_new
            end_idx = start_idx + partitions_per_new if i < num_partitions - 1 else len(old_partitions)
            
            merged_rows = sum(p.num_rows for p in old_partitions[start_idx:end_idx])
            merged_size = sum(p.size_bytes for p in old_partitions[start_idx:end_idx])
            
            partitions.append(Partition(
                id=i,
                num_rows=merged_rows,
                size_bytes=merged_size
            ))
        
        return PartitionInfo(
            num_partitions=num_partitions,
            partitions=partitions
        )


@dataclass 
class ShuffleStats:
    """Statistics about shuffle operations."""
    shuffle_read_bytes: int = 0
    shuffle_write_bytes: int = 0
    shuffle_read_records: int = 0
    shuffle_write_records: int = 0
    
    def add_shuffle(self, records: int, size_bytes: int):
        self.shuffle_read_bytes += size_bytes
        self.shuffle_write_bytes += size_bytes
        self.shuffle_read_records += records
        self.shuffle_write_records += records
