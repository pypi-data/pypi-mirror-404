"""
DataFrameWriter - writes DataFrame to various sinks.
"""
from typing import Optional, Dict, List, Any
import polars as pl
from pathlib import Path


class DataFrameWriter:
    """
    Interface for writing a DataFrame to external storage.
    
    Example:
        df.write.csv("output/")
        df.write.mode("overwrite").parquet("output.parquet")
    """
    
    def __init__(self, df: "DataFrame"):
        self._df = df
        self._format: Optional[str] = None
        self._mode: str = "error"  # error, overwrite, append, ignore
        self._options: Dict[str, Any] = {}
        self._partition_by: List[str] = []
    
    def format(self, source: str) -> "DataFrameWriter":
        """Specify the output data source format."""
        self._format = source.lower()
        return self
    
    def mode(self, saveMode: str) -> "DataFrameWriter":
        """
        Specify the behavior when data already exists.
        
        Args:
            saveMode: One of "error", "overwrite", "append", "ignore"
        """
        self._mode = saveMode.lower()
        return self
    
    def option(self, key: str, value: Any) -> "DataFrameWriter":
        """Add an output option."""
        self._options[key] = value
        return self
    
    def options(self, **opts) -> "DataFrameWriter":
        """Add multiple output options."""
        self._options.update(opts)
        return self
    
    def partitionBy(self, *cols: str) -> "DataFrameWriter":
        """Partition the output by the given columns."""
        self._partition_by = list(cols)
        return self
    
    def save(self, path: Optional[str] = None, **options):
        """Save the DataFrame to the specified path."""
        self._options.update(options)
        
        if path:
            self._options["path"] = path
        
        if self._format == "csv":
            self.csv(self._options.get("path", ""))
        elif self._format == "json":
            self.json(self._options.get("path", ""))
        elif self._format == "parquet":
            self.parquet(self._options.get("path", ""))
        else:
            raise ValueError(f"Unknown format: {self._format}")
    
    def _get_collected_df(self) -> pl.DataFrame:
        """Get the collected DataFrame."""
        return self._df._collect_internal()
    
    def _handle_mode(self, path: str):
        """Handle save mode for existing data."""
        import os
        path_obj = Path(path)
        
        if path_obj.exists():
            if self._mode == "error":
                raise FileExistsError(f"Path already exists: {path}")
            elif self._mode == "overwrite":
                if path_obj.is_dir():
                    import shutil
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            elif self._mode == "ignore":
                return False  # Don't write
            # append mode: continue writing
        
        return True
    
    def csv(self, path: str, header: bool = True, sep: str = ",", **options):
        """Write to CSV."""
        if not self._handle_mode(path):
            return
        
        opts = {**self._options, **options}
        header = opts.get("header", header)
        sep = opts.get("sep", opts.get("delimiter", sep))
        
        df = self._get_collected_df()
        
        # Create directory if needed
        path_obj = Path(path)
        if path_obj.suffix == "":  # Directory
            path_obj.mkdir(parents=True, exist_ok=True)
            output_path = path_obj / "part-00000.csv"
        else:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            output_path = path_obj
        
        df.write_csv(str(output_path), include_header=header, separator=sep)
    
    def json(self, path: str, **options):
        """Write to JSON."""
        if not self._handle_mode(path):
            return
        
        df = self._get_collected_df()
        
        # Create directory if needed
        path_obj = Path(path)
        if path_obj.suffix == "":  # Directory
            path_obj.mkdir(parents=True, exist_ok=True)
            output_path = path_obj / "part-00000.json"
        else:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            output_path = path_obj
        
        df.write_ndjson(str(output_path))
    
    def parquet(self, path: str, compression: str = "snappy", **options):
        """Write to Parquet."""
        if not self._handle_mode(path):
            return
        
        df = self._get_collected_df()
        
        # Create directory if needed
        path_obj = Path(path)
        if path_obj.suffix == "":  # Directory
            path_obj.mkdir(parents=True, exist_ok=True)
            output_path = path_obj / "part-00000.parquet"
        else:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            output_path = path_obj
        
        df.write_parquet(str(output_path), compression=compression)
    
    def saveAsTable(self, name: str):
        """Save as a table (stores in catalog)."""
        df = self._get_collected_df()
        self._df._spark.catalog._tables[name] = df
    
    def insertInto(self, tableName: str, overwrite: bool = False):
        """Insert into an existing table."""
        if overwrite:
            self._mode = "overwrite"
        else:
            self._mode = "append"
        self.saveAsTable(tableName)
