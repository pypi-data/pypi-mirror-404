"""
SQL Parser - parses SQL queries and converts to DataFrame operations.
"""
from typing import Optional, List, Dict, Any
import re
import sqlglot
from sqlglot import exp


class SQLParser:
    """
    Parses SQL queries and converts them to DataFrame operations.
    
    Uses sqlglot for parsing SQL into an AST, then translates to Polars operations.
    """
    
    def __init__(self, spark_session: "SparkSession"):
        self._spark = spark_session
    
    def parse(self, query: str) -> "DataFrame":
        """Parse a SQL query and return a DataFrame."""
        from spark_mock.sql.dataframe import DataFrame
        from spark_mock.core.lazy import LazyExecutionPlan, OperationType
        import polars as pl
        
        # Parse SQL with sqlglot
        try:
            ast = sqlglot.parse_one(query)
        except Exception as e:
            raise ValueError(f"Failed to parse SQL: {e}")
        
        # Handle different statement types
        if isinstance(ast, exp.Select):
            return self._handle_select(ast)
        elif isinstance(ast, exp.Create):
            return self._handle_create(ast)
        elif isinstance(ast, exp.Insert):
            return self._handle_insert(ast)
        elif isinstance(ast, exp.Drop):
            return self._handle_drop(ast)
        else:
            raise ValueError(f"Unsupported SQL statement type: {type(ast)}")
    
    def _handle_select(self, ast: exp.Select) -> "DataFrame":
        """Handle SELECT statement."""
        from spark_mock.sql.dataframe import DataFrame
        from spark_mock.sql.column import Column
        from spark_mock.sql import functions as F
        from spark_mock.core.lazy import LazyExecutionPlan, OperationType
        import polars as pl
        
        # Get the source table(s)
        from_clause = ast.find(exp.From)
        if from_clause is None:
            raise ValueError("SELECT without FROM is not supported")
        
        # Get table name
        table_expr = from_clause.this
        table_name = self._get_table_name(table_expr)
        
        # Get the DataFrame from catalog
        lazy_df = self._spark._catalog.getTable(table_name)
        if lazy_df is None:
            raise ValueError(f"Table or view '{table_name}' not found")
        
        plan = LazyExecutionPlan()
        plan.add_operation(OperationType.CREATE_DATAFRAME, table=table_name)
        
        df = DataFrame(lazy_df, self._spark, plan)
        
        # Handle JOINs
        for join in ast.find_all(exp.Join):
            join_table = self._get_table_name(join.this)
            join_df = self._spark.table(join_table)
            
            # Get join condition
            on_clause = join.args.get("on")
            if on_clause:
                on_cols = self._extract_column_names(on_clause)
            else:
                on_cols = None
            
            # Get join type
            join_type = "inner"
            if join.args.get("kind"):
                join_type = str(join.args["kind"]).lower()
            
            df = df.join(join_df, on=on_cols, how=join_type)
        
        # Handle WHERE clause
        where = ast.find(exp.Where)
        if where:
            condition = self._translate_condition(where.this)
            df = df.filter(condition)
        
        # Handle GROUP BY
        group_by = ast.find(exp.Group)
        if group_by:
            group_cols = [self._expr_to_string(e) for e in group_by.expressions]
            grouped = df.groupBy(*group_cols)
            
            # Handle SELECT with aggregations
            select_exprs = []
            for sel in ast.expressions:
                translated = self._translate_expression(sel)
                select_exprs.append(translated)
            
            df = grouped.agg(*select_exprs)
        else:
            # Handle SELECT columns
            if ast.expressions:
                select_cols = []
                for sel in ast.expressions:
                    if isinstance(sel, exp.Star):
                        select_cols.append("*")
                    else:
                        translated = self._translate_expression(sel)
                        select_cols.append(translated)
                
                if select_cols and not (len(select_cols) == 1 and select_cols[0] == "*"):
                    df = df.select(*select_cols)
        
        # Handle HAVING
        having = ast.find(exp.Having)
        if having:
            condition = self._translate_condition(having.this)
            df = df.filter(condition)
        
        # Handle ORDER BY
        order_by = ast.find(exp.Order)
        if order_by:
            order_cols = []
            ascending = []
            for ordered in order_by.expressions:
                col_name = self._expr_to_string(ordered.this)
                order_cols.append(col_name)
                ascending.append(not ordered.args.get("desc", False))
            
            df = df.orderBy(*order_cols, ascending=ascending)
        
        # Handle LIMIT
        limit = ast.find(exp.Limit)
        if limit:
            n = int(limit.this.this)
            df = df.limit(n)
        
        # Handle DISTINCT
        if ast.args.get("distinct"):
            df = df.distinct()
        
        return df
    
    def _get_table_name(self, expr) -> str:
        """Extract table name from expression."""
        if isinstance(expr, exp.Table):
            return expr.name
        elif isinstance(expr, exp.Alias):
            return self._get_table_name(expr.this)
        else:
            return str(expr)
    
    def _expr_to_string(self, expr) -> str:
        """Convert expression to string."""
        if isinstance(expr, exp.Column):
            return expr.name
        elif isinstance(expr, exp.Alias):
            return expr.alias
        else:
            return str(expr)
    
    def _translate_expression(self, expr) -> "Column":
        """Translate SQL expression to Column."""
        from spark_mock.sql.column import Column
        from spark_mock.sql import functions as F
        import polars as pl
        
        if isinstance(expr, exp.Column):
            return Column(expr.name)
        
        elif isinstance(expr, exp.Alias):
            inner = self._translate_expression(expr.this)
            return inner.alias(expr.alias)
        
        elif isinstance(expr, exp.Star):
            return Column(pl.all())
        
        elif isinstance(expr, exp.Literal):
            return Column(pl.lit(expr.this))
        
        elif isinstance(expr, exp.Sum):
            col = self._translate_expression(expr.this)
            return F.sum(col)
        
        elif isinstance(expr, exp.Avg):
            col = self._translate_expression(expr.this)
            return F.avg(col)
        
        elif isinstance(expr, exp.Count):
            if isinstance(expr.this, exp.Star):
                return F.count("*")
            col = self._translate_expression(expr.this)
            return F.count(col)
        
        elif isinstance(expr, exp.Max):
            col = self._translate_expression(expr.this)
            return F.max(col)
        
        elif isinstance(expr, exp.Min):
            col = self._translate_expression(expr.this)
            return F.min(col)
        
        elif isinstance(expr, (exp.Add, exp.Sub, exp.Mul, exp.Div)):
            left = self._translate_expression(expr.left)
            right = self._translate_expression(expr.right)
            if isinstance(expr, exp.Add):
                return left + right
            elif isinstance(expr, exp.Sub):
                return left - right
            elif isinstance(expr, exp.Mul):
                return left * right
            elif isinstance(expr, exp.Div):
                return left / right
        
        elif isinstance(expr, exp.Func):
            func_name = expr.name.lower()
            args = [self._translate_expression(a) for a in expr.args.get("expressions", [])]
            
            if func_name == "concat":
                return F.concat(*args)
            elif func_name == "upper":
                return args[0].upper()
            elif func_name == "lower":
                return args[0].lower()
            elif func_name == "length":
                return args[0].length()
            elif func_name == "coalesce":
                return F.coalesce(*args)
            else:
                # Default: try to call as a function
                return args[0] if args else Column(pl.lit(None))
        
        else:
            # Fallback: try to convert to string and use as column name
            return Column(str(expr))
    
    def _translate_condition(self, expr) -> "Column":
        """Translate SQL condition to Column."""
        from spark_mock.sql.column import Column
        from spark_mock.sql import functions as F
        import polars as pl
        
        if isinstance(expr, exp.EQ):
            left = self._translate_expression(expr.left)
            right = self._translate_expression(expr.right)
            return left == right
        
        elif isinstance(expr, exp.NEQ):
            left = self._translate_expression(expr.left)
            right = self._translate_expression(expr.right)
            return left != right
        
        elif isinstance(expr, exp.GT):
            left = self._translate_expression(expr.left)
            right = self._translate_expression(expr.right)
            return left > right
        
        elif isinstance(expr, exp.GTE):
            left = self._translate_expression(expr.left)
            right = self._translate_expression(expr.right)
            return left >= right
        
        elif isinstance(expr, exp.LT):
            left = self._translate_expression(expr.left)
            right = self._translate_expression(expr.right)
            return left < right
        
        elif isinstance(expr, exp.LTE):
            left = self._translate_expression(expr.left)
            right = self._translate_expression(expr.right)
            return left <= right
        
        elif isinstance(expr, exp.And):
            left = self._translate_condition(expr.left)
            right = self._translate_condition(expr.right)
            return left & right
        
        elif isinstance(expr, exp.Or):
            left = self._translate_condition(expr.left)
            right = self._translate_condition(expr.right)
            return left | right
        
        elif isinstance(expr, exp.Not):
            inner = self._translate_condition(expr.this)
            return ~inner
        
        elif isinstance(expr, exp.Between):
            col = self._translate_expression(expr.this)
            low = self._translate_expression(expr.args["low"])
            high = self._translate_expression(expr.args["high"])
            return col.between(low, high)
        
        elif isinstance(expr, exp.In):
            col = self._translate_expression(expr.this)
            values = [self._translate_expression(e) for e in expr.expressions]
            # Extract literal values
            lit_values = []
            for v in values:
                if hasattr(v, '_expr'):
                    # Try to extract literal value
                    lit_values.append(v)
            return col.isin(*lit_values)
        
        elif isinstance(expr, exp.Like):
            col = self._translate_expression(expr.this)
            pattern = str(expr.expression.this)
            return col.like(pattern)
        
        elif isinstance(expr, exp.Is):
            col = self._translate_expression(expr.this)
            if isinstance(expr.expression, exp.Null):
                return col.isNull()
            return col.isNotNull()
        
        elif isinstance(expr, exp.Column):
            return self._translate_expression(expr)
        
        elif isinstance(expr, exp.Literal):
            return Column(pl.lit(expr.this))
        
        else:
            # Fallback
            return Column(pl.lit(True))
    
    def _extract_column_names(self, expr) -> List[str]:
        """Extract column names from expression."""
        cols = []
        for col in expr.find_all(exp.Column):
            cols.append(col.name)
        return cols
    
    def _handle_create(self, ast: exp.Create) -> None:
        """Handle CREATE TABLE statement."""
        # Not implemented yet
        pass
    
    def _handle_insert(self, ast: exp.Insert) -> None:
        """Handle INSERT statement."""
        # Not implemented yet
        pass
    
    def _handle_drop(self, ast: exp.Drop) -> None:
        """Handle DROP statement."""
        table_name = ast.this.name
        self._spark._catalog.dropTable(table_name, ifExists=True)
