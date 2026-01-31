# louati_mahdi_analytics/sql_parser.py
import pandas as pd
import sqlparse
import re

class SQLParser:
    def __init__(self, df):
        self.df = df

    def execute(self, query):
        query = query.strip().lower()
        
        # 1. Parse SELECT
        select_match = re.search(r'select (.*?) from', query)
        if not select_match:
            raise ValueError("Invalid SQL: Missing 'SELECT ... FROM'")
        
        columns = [c.strip() for c in select_match.group(1).split(',')]
        if columns[0] == '*':
            columns = self.df.columns.tolist()

        # 2. Parse WHERE
        where_clause = "True"
        if 'where' in query:
            where_part = query.split('where')[1]
            # Handle GROUP BY if exists
            if 'group by' in where_part:
                where_part = where_part.split('group by')[0]
            
            # Simple regex replacements for SQL to Pandas
            where_clause = where_part.strip()
            where_clause = re.sub(r'=', '==', where_clause)
            where_clause = re.sub(r' and ', ' & ', where_clause)
            where_clause = re.sub(r' or ', ' | ', where_clause)

        # 3. Parse GROUP BY
        group_cols = None
        if 'group by' in query:
            group_part = query.split('group by')[1].strip()
            group_cols = [c.strip() for c in group_part.split(',')]

        # 4. Execute
        try:
            result = self.df.copy()
            # Filter
            result = result.query(where_clause)
            
            # Group
            if group_cols:
                agg_dict = {col: 'count' for col in result.columns if col not in group_cols}
                # Keep at least one aggregation
                if not agg_dict: 
                    agg_dict = {result.columns[0]: 'mean'}
                result = result.groupby(group_cols).agg(agg_dict).reset_index()

            # Select Columns
            result = result[columns]
            return result
        except Exception as e:
            raise ValueError(f"SQL Execution Error: {e}\nCheck your column names and syntax.")