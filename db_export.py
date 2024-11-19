import json
import psycopg2
import pandas as pd
from typing import Dict, Any
from pathlib import Path


class DatabaseExporter:
    def __init__(self, config_path: str = "config/export_database.json"):
        """Initialize database connection parameters from config file"""
        self.db_params = self._load_config(config_path)
        self.queries = self._load_queries("config/export_queries.json")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load database configuration from JSON file"""
        with open(config_path) as f:
            return json.load(f)

    def _load_queries(self, queries_path: str) -> Dict[str, str]:
        """Load SQL queries from JSON file"""
        with open(queries_path) as f:
            return json.load(f)

    def connect(self):
        """Establish database connection"""
        try:
            return psycopg2.connect(**self.db_params)
        except psycopg2.Error as e:
            raise Exception(f"Failed to connect to database: {str(e)}")

    def execute_query(self, query_name: str) -> pd.DataFrame:
        """Execute a named query and return results as DataFrame"""
        if query_name not in self.queries:
            raise ValueError(f"Query '{query_name}' not found in queries file")

        query = self.queries[query_name]

        try:
            with self.connect() as conn:
                return pd.read_sql_query(query, conn)
        except Exception as e:
            raise Exception(f"Error executing query '{query_name}': {str(e)}")

    def export_to_csv(self, query_name: str, output_path: str):
        """Execute query and export results to CSV file"""
        df = self.execute_query(query_name)
        df.to_csv(output_path, index=False)


def main():
    # Example usage
    exporter = DatabaseExporter()

    # Execute specific query and get results as DataFrame
    # results_df = exporter.execute_query("v_bu_cat_des_2")
    # print(results_df.head())
    # print(results_df.shape)

    # Or export directly to CSV
    exporter.export_to_csv("v_bu_cat_des_2", "data/v_bu_cat_des_2.csv")
    exporter.export_to_csv("bu_category", "data/bu_category.csv")
    exporter.export_to_csv("bu_subcategory", "data/bu_subcategory.csv")
    exporter.export_to_csv("cat_category", "data/cat_category.csv")


if __name__ == "__main__":
    main()
