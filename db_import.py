import csv
import os
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from psycopg2 import sql
import psycopg2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('db_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Config:
    """Global configuration settings"""
    DATA_DIR = Path('data')
    TABLE_NAME = 'fecops_jira_tickets_raised_from_bu'
    VALID_FILE_TYPES = {
        'jira_canceled_tickets': TABLE_NAME,
        'jira_closed_tickets': TABLE_NAME,
        'jira_in_progress_tickets': TABLE_NAME
    }
    DB_CONFIG = {
        'dbname': os.getenv('DB_NAME', 'fecops'),
        'user': os.getenv('DB_USER', 'fecops-admin'),
        'password': os.getenv('DB_PASSWORD', 'fecops-admin'),
        'host': os.getenv('DB_HOST', 'khoadue.me'),
        'port': os.getenv('DB_PORT', '5434')
    }


class DatabaseConfig:
    """Database configuration and connection management"""

    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.conn = None
        self.cursor = None

    def connect(self) -> None:
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.config)
            self.cursor = self.conn.cursor()
        except Exception as e:
            logger.error("Database connection failed: %s", str(e))
            raise

    def close(self) -> None:
        """Close database connections"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def commit(self) -> None:
        """Commit transaction"""
        if self.conn:
            self.conn.commit()

    def rollback(self) -> None:
        """Rollback transaction"""
        if self.conn:
            self.conn.rollback()


class ColumnAnalyzer:
    """Analyzes CSV columns and determines appropriate PostgreSQL types"""
    # Known field type mappings
    KNOWN_TEXT_FIELDS = {
        'summary', 'description', 'comments', 'details', 'environment',
        'custom_field_value', 'resolution', 'priority', 'labels',
        'components', 'assignee', 'reporter', 'creator', 'project',
        'status', 'issue_type', 'workflow_status', 'team_name',
        'business_unit', 'department', 'division'
    }

    VARCHAR_LENGTH_MAPPING = {
        'issue_key': 20,
        'project_key': 20,
        'priority_id': 50,
        'status_id': 50,
        'resolution_id': 50,
        'assignee_id': 128,
        'reporter_id': 128,
        'creator_id': 128,
        'email': 255,
        'phone': 50,
        'url': 500
    }

    def __init__(self, headers: List[str]):
        self.headers = headers
        self.normalized_headers = [
            self._normalize_header(h) for h in headers
        ]
        self.header_mapping = dict(zip(headers, self.normalized_headers))
        self.max_lengths = [0] * len(headers)
        self.is_numeric = [True] * len(headers)
        self.has_decimal = [False] * len(headers)
        self.sample_values = [[] for _ in headers]

    def _normalize_header(self, header: str) -> str:
        """Normalize header names by removing special characters and converting to snake_case"""
        # Convert to lowercase
        header = header.lower()
        # Replace special characters and spaces with underscore
        header = re.sub(r'[^a-z0-9]+', '_', header)
        # Remove leading/trailing underscores
        header = header.strip('_')
        # Replace multiple underscores with single underscore
        header = re.sub(r'_+', '_', header)
        return header

    def analyze_row(self, row: List[str]) -> None:
        """Analyze a single row of data"""
        for i, value in enumerate(row):
            current_length = len(value)
            self.max_lengths[i] = max(self.max_lengths[i], current_length)

            if value and len(self.sample_values[i]) < 100:
                self.sample_values[i].append(value)

            if self.is_numeric[i] and value:
                try:
                    float(value)
                    self.has_decimal[i] = self.has_decimal[i] or ('.' in value)
                except ValueError:
                    self.is_numeric[i] = False

    def determine_column_types(self) -> Tuple[List[str], Optional[str]]:
        """Determine PostgreSQL column types"""
        column_types = []
        primary_key_column = None

        for i, header in enumerate(self.normalized_headers):
            logger.debug(f"Analyzing column '{header}': Max length = {self.max_lengths[i]}, "
                         f"Is numeric = {self.is_numeric[i]}, Has decimal = {self.has_decimal[i]}")

            column_type = self._determine_single_column_type(header, i)
            column_types.append(column_type)

            if header == 'issue_key':
                primary_key_column = header

            logger.debug(f"  → Chosen type: {column_types[-1]}")

        return column_types, primary_key_column

    def _determine_single_column_type(self, header: str, index: int) -> str:
        """Determine the type for a single column"""
        if header == 'issue_key':
            return 'VARCHAR(20)'
        elif header in self.VARCHAR_LENGTH_MAPPING:
            return f"VARCHAR({self.VARCHAR_LENGTH_MAPPING[header]})"
        elif any(text_field in header for text_field in self.KNOWN_TEXT_FIELDS):
            return 'TEXT'
        elif self.is_numeric[index]:
            return 'NUMERIC' if self.has_decimal[index] else 'INTEGER'
        else:
            return self._calculate_varchar_length(index)

    def _calculate_varchar_length(self, index: int) -> str:
        """Calculate appropriate VARCHAR length for a column"""
        if self.max_lengths[index] > 255:
            return 'TEXT'

        safe_length = max(
            int(self.max_lengths[index] * 2),
            100,
            self.max_lengths[index] + 50
        )
        safe_length = ((safe_length + 49) // 50) * 50
        return f'VARCHAR({safe_length})'


class DataImporter:
    """Handles the CSV to PostgreSQL import process"""

    def __init__(self, db_config: Dict[str, str], table_name: str):
        self.db = DatabaseConfig(db_config)
        self.table_name = table_name

    def import_file(self, csv_file_path: str) -> int:
        """Import data from CSV to PostgreSQL"""
        try:
            self.db.connect()
            logger.info(f"Processing file: {csv_file_path}")

            analyzer = self._analyze_csv(csv_file_path)
            self._create_table(analyzer)
            records_imported = self._import_data(csv_file_path, analyzer)

            logger.info(
                f"Successfully imported {records_imported:,} records into {self.table_name}")
            return records_imported

        except Exception as error:
            logger.error(f"Import failed: {str(error)}")
            self.db.rollback()
            raise
        finally:
            self.db.close()

    def _analyze_csv(self, csv_file_path: str) -> ColumnAnalyzer:
        """Analyze CSV structure"""
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)
            analyzer = ColumnAnalyzer(headers)
            for row in reader:
                analyzer.analyze_row(row)
        return analyzer

    def _create_table(self, analyzer: ColumnAnalyzer) -> None:
        """Create database table"""
        column_types, primary_key_column = analyzer.determine_column_types()
        columns_def = [
            f"{sql.Identifier(header).as_string(self.db.conn)} {type_}"
            for header, type_ in zip(analyzer.normalized_headers, column_types)
        ]

        create_table_query = sql.SQL("""
            CREATE TABLE IF NOT EXISTS {} (
                {},
                {}
            )
        """).format(
            sql.Identifier(self.table_name),
            sql.SQL(', ').join(map(sql.SQL, columns_def)),
            sql.SQL("PRIMARY KEY ({})").format(
                sql.Identifier(primary_key_column))
            if primary_key_column else sql.SQL("")
        )

        self.db.cursor.execute(create_table_query)
        logger.info(f"Table structure created/verified: {self.table_name}")

    def _import_data(self, csv_file_path: str, analyzer: ColumnAnalyzer) -> int:
        """Import data from CSV file"""
        records_imported = 0
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row_num, row in enumerate(reader, 1):
                try:
                    self._import_row(row, analyzer)
                    records_imported += 1

                    if records_imported % 1000 == 0:
                        self.db.commit()
                        logger.info(
                            f"Processed {records_imported:,} records...")

                except Exception as e:
                    logger.error(f"Error on row {row_num}: {str(e)}")
                    logger.error(f"Problematic row data: {row}")
                    raise

        self.db.commit()
        return records_imported

    def _import_row(self, row: Dict[str, str], analyzer: ColumnAnalyzer) -> None:
        """Import a single row of data"""
        normalized_row = {
            analyzer.header_mapping[k]: v for k, v in row.items()}

        update_set = sql.SQL(', ').join(
            sql.SQL("{} = EXCLUDED.{}").format(
                sql.Identifier(key),
                sql.Identifier(key)
            )
            for key in normalized_row.keys()
            if key != 'issue_key'
        )

        insert_query = sql.SQL("""
            INSERT INTO {} ({}) 
            VALUES ({})
            ON CONFLICT (issue_key) DO UPDATE 
            SET {}
        """).format(
            sql.Identifier(self.table_name),
            sql.SQL(', ').join(map(sql.Identifier, normalized_row.keys())),
            sql.SQL(', ').join(sql.Placeholder() * len(normalized_row)),
            update_set
        )

        self.db.cursor.execute(insert_query, tuple(normalized_row.values()))


def execute_import(filename: Optional[str] = None):
    """Main execution function
    Args:
        filename (Optional[str]): Specific CSV file to process. If None, process all matching files.
    """
    from datetime import datetime

    try:
        if not Config.DATA_DIR.exists():
            raise FileNotFoundError(f"Directory '{Config.DATA_DIR}' not found")

        records_count = 0
        processed_files = []

        start_time = datetime.utcnow()

        # Handle specific file if provided
        if filename:
            file_path = Config.DATA_DIR / filename
            if not file_path.exists():
                raise FileNotFoundError(
                    f"File '{filename}' not found in {Config.DATA_DIR}"
                )

            # Validate file type
            if not any(file_type in filename for file_type in Config.VALID_FILE_TYPES):
                raise ValueError(
                    f"Invalid file type. File must contain one of: {', '.join(Config.VALID_FILE_TYPES.keys())}"
                )

            # Process single file
            for file_type, target_table in Config.VALID_FILE_TYPES.items():
                if file_type in filename:
                    importer = DataImporter(Config.DB_CONFIG, target_table)
                    imported_records = importer.import_file(str(file_path))
                    records_count += imported_records
                    processed_files.append(filename)
                    logger.info(
                        f"Successfully processed {filename}: {imported_records:,} records"
                    )
                    break
        else:
            # Original logic for processing all files
            for file_path in Config.DATA_DIR.glob('*.csv'):
                for file_type, target_table in Config.VALID_FILE_TYPES.items():
                    if file_type in file_path.name:
                        try:
                            importer = DataImporter(
                                Config.DB_CONFIG, target_table
                            )
                            imported_records = importer.import_file(
                                str(file_path)
                            )
                            records_count += imported_records
                            processed_files.append(file_path.name)
                            logger.info(
                                f"Successfully processed {file_path.name}: {imported_records:,} records"
                            )
                        except Exception as e:
                            logger.error(
                                f"Error processing {file_path.name}: {str(e)}"
                            )
                        break

        # Output processing summary
        if not processed_files:
            logger.warning("No matching CSV files found for processing")
        else:
            logger.info("\nProcessing Summary:")
            logger.info(f"Total files processed: {len(processed_files)}")
            logger.info(f"Total records imported: {records_count:,}")
            logger.info(f"Processed files: {', '.join(processed_files)}")

        end_time = datetime.utcnow()
        total_time = (end_time - start_time).total_seconds()

        return {
            "total_imported_data": records_count,
            "processed_file_names": processed_files,
            "total_time_of_processing": total_time
        }

    except Exception as e:
        logger.error(f"Critical error during import process: {str(e)}")
        raise


def main():
    """Main execution function"""
    execute_import()


if __name__ == "__main__":
    main()
