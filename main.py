import json
import sys
import logging
from pathlib import Path
from typing import Dict, Optional, List
from atlassian import Jira
from datetime import datetime, timedelta

from common.jira_util import (
    download_issue_attachments,
    jql_v2_print,
    load_jql_queries,
    count_issues_in_project,
    export_issues_to_csv
)
import pandas as pd
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QueryConfig:
    """Configuration class for JQL queries"""
    FIELDS = ["key", "summary", "created", "status"]
    CONFIG_FILE = Path("config/jira_team_accounts.json")
    # QUERIES_FILE = Path("config/queries.json")
    QUERIES_FILE = Path("config/queries_v2.json")
    EXPORT_BATCH_SIZE = 1000
    DATA_DIR = Path("data")

    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure required directories exist"""
        cls.DATA_DIR.mkdir(exist_ok=True)


def process_query_type(
    query_type: str,
    jql_query: str,
    config: QueryConfig,
    stats: Dict
) -> bool:
    """
    Process a specific query type (closed or canceled tickets).

    Args:
        query_type: Type of query (closed/canceled)
        jql_query: JQL query string
        config: QueryConfig instance
        stats: Dictionary to store statistics

    Returns:
        bool: True if processing was successful
    """
    try:
        # Get statistics for the query type
        total, records, pages = count_issues_in_project(
            jql_query, str(config.CONFIG_FILE))

        # Store statistics
        stats[query_type] = {
            "total": total,
            "records": records,
            "pages": pages
        }

        # Skip export if no records found
        if records == 0:
            logger.info(f"No {query_type} tickets found to export")
            return True

        # Export tickets in batches
        # Remove existing files for this query type
        existing_files = list(config.DATA_DIR.glob(f'jira_{query_type}_tickets_batch_*.csv'))
        if existing_files:
            logger.info(f"Removing {len(existing_files)} existing {query_type} ticket files")
            for file in existing_files:
                try:
                    file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to remove file {file}: {str(e)}")

        for batch in range(0, records, config.EXPORT_BATCH_SIZE):
            output_file = config.DATA_DIR / \
                f'jira_{query_type}_tickets_batch_{batch // config.EXPORT_BATCH_SIZE + 1}.csv'

            success, count = export_issues_to_csv(
                jql_query,
                str(config.CONFIG_FILE),
                config.FIELDS,
                str(output_file),
                max_results=config.EXPORT_BATCH_SIZE,
                start_at=batch
            )

            if not success:
                logger.error(
                    f"Failed to export {query_type} tickets batch starting at {batch}")
                return False

            logger.info(
                f"Exported {count:,} {query_type} tickets to {output_file}")

        return True

    except Exception as e:
        logger.error(f"Error processing {query_type} tickets: {str(e)}")
        return False


def print_statistics(stats: Dict) -> None:
    """Print detailed statistics for all query types"""
    logger.info("\nJira Ticket Statistics:")
    logger.info("-" * 50)

    total_records = 0
    for query_type, data in stats.items():
        logger.info(f"\n{query_type.title()} Tickets:")
        logger.info(f"  - Total issues: {data['total']:,}")
        logger.info(f"  - Total records: {data['records']:,}")
        logger.info(f"  - Total pages: {data['pages']:,}")
        total_records += data['records']

    logger.info("\nSummary:")
    logger.info(f"Total tickets processed: {total_records:,}")


def main(query_name: Optional[str] = None, from_date: Optional[str] = None, to_date: Optional[str] = None):
    """Main execution function
    
    Args:
        query_name: Name of specific query to run (optional)
        from_date: Start date for date range queries (optional) 
        to_date: End date for date range queries (optional)
    """
    try:
        config = QueryConfig()
        config.ensure_directories()

        # Load JQL queries from configuration file
        queries = load_jql_queries(str(config.QUERIES_FILE))
        if queries is None:
            logger.error("Failed to load JQL queries")
            return 1

        # Initialize statistics dictionary
        stats = {}

        # If query_name specified, only run that query
        if query_name:
            if query_name not in queries:
                logger.error(f"Query '{query_name}' not found in configuration")
                return 1
                
            query = queries[query_name]["query"]
            if from_date is not None and to_date is not None and "date_range" in query_name:
                query = jql_v2_print(query, from_date, to_date)
                
            query_type = query_name.split("_tickets")[0]
            if not process_query_type(query_type, query, config, stats):
                logger.error(f"Failed to process {query_type} tickets")
                return 1
                
        # Otherwise run all configured queries
        else:
            # Process closed tickets if query exists
            if queries.get("closed_tickets_date_range", {}).get("query"):
                if from_date is None and to_date is None:
                    closed_query = queries["closed_tickets_date_range"]["query"]
                else:
                    closed_query = jql_v2_print(queries["closed_tickets_date_range"]["query"], from_date, to_date)
                if not process_query_type(
                    "closed",
                    closed_query,
                    config,
                    stats
                ):
                    logger.error("Failed to process closed tickets")
                    return 1
            else:
                logger.warning("No closed tickets query found in configuration")

            # Process canceled tickets if query exists
            if queries.get("canceled_tickets_date_range", {}).get("query"):
                if from_date is None and to_date is None:
                    canceled_query = queries["canceled_tickets_date_range"]["query"]
                else:
                    canceled_query = jql_v2_print(queries["canceled_tickets_date_range"]["query"], from_date, to_date)
                if not process_query_type(
                    "canceled",
                    canceled_query,
                    config,
                    stats
                ):
                    logger.error("Failed to process canceled tickets")
                    return 1

            # Process in progress tickets if query exists
            if queries.get("in_progress_tickets", {}).get("query"):
                if not process_query_type(
                    "in_progress",
                    queries["in_progress_tickets"]["query"],
                    config,
                    stats
                ):
                    logger.error("Failed to process in progress tickets")
                    return 1
            else:
                logger.warning("No in progress tickets query found in configuration")
                
            if queries.get("royalty_tickets", {}).get("query"):
                if not process_query_type(
                    "royal",
                    queries["royalty_tickets"]["query"],
                    config,
                    stats
                ):
                    logger.error("Failed to process royalty tickets")
                    return 1
            else:
                logger.warning("No royalty tickets query found in configuration")

        # Print statistics if any queries were processed
        if stats:
            print_statistics(stats)
        else:
            logger.warning("No queries were processed")

        return 0

    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        return 1
    
def main_v2():
    """Main execution function"""
    try:
        config = QueryConfig()
        config.ensure_directories()

        # Load JQL queries from configuration file
        queries = load_jql_queries(str(config.QUERIES_FILE))
        if queries is None:
            logger.error("Failed to load JQL queries")
            return 1

        # Initialize statistics dictionary
        stats = {}

        if queries.get("royalty_tickets", {}).get("query"):
            if not process_query_type(
                "royal",
                queries["royalty_tickets"]["query"],
                config,
                stats
            ):
                logger.error("Failed to process in progress tickets")
                return 1
        else:
            logger.warning("No in progress tickets query found in configuration")

        # Print statistics if any queries were processed
        if stats:
            print_statistics(stats)
        else:
            logger.warning("No queries were processed")

        return 0

    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        return 1

def download_main():
    """Main execution function"""
    try:
        config = QueryConfig()
        
        # Create base data directory
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        logger.info(f"Attempting to download attachments for TC-44 to {data_dir}")
        logger.info(f"Using config file: {config.CONFIG_FILE}")
        
        # Download attachments
        # downloaded_files = download_issue_attachments(
        #     "TC-44",
        #     str(config.CONFIG_FILE), 
        #     str(data_dir)  # Pass the base data directory
        # )
        # Read CSV file containing Jira issue keys
        try:
            issues_df = pd.read_csv(data_dir / "jira_royal_tickets_batch_1.csv")
            if 'Issue key' not in issues_df.columns:
                logger.error("CSV file must contain a 'key' column with Jira issue keys")
                return 1
                
            downloaded_files = []
            
            # Process each issue key and download attachments
            for issue_key in issues_df["Issue key"].unique():
                logger.info(f"Downloading attachments for issue {issue_key}")
                
                # Download attachments for current issue
                issue_files = download_issue_attachments(
                    issue_key,
                    str(config.CONFIG_FILE),
                    str(data_dir)
                )
                
                if issue_files:
                    downloaded_files.extend(issue_files)
                    logger.info(f"Downloaded {len(issue_files)} files for issue {issue_key}")
                else:
                    logger.warning(f"No attachments found for issue {issue_key}")
                    
        except FileNotFoundError:
            logger.error(f"Could not find issues CSV file at {data_dir / 'issues.csv'}")
            return 1
        except pd.errors.EmptyDataError:
            logger.error("The issues CSV file is empty")
            return 1
        except Exception as e:
            logger.error(f"Error processing CSV file: {str(e)}")
            return 1
        
        if not downloaded_files:
            logger.error(f"Failed to download attachments to {data_dir}/downloads")
            return 1
            
        logger.info(f"Successfully downloaded {len(downloaded_files)} files to {data_dir}/downloads")
        return 0
        
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        return 1

def attachment_replace_main():
    """Main execution function"""
    try:
        config = QueryConfig()
        
        # Create base data directory
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        logger.info(f"Attempting to download attachments for TC-44 to {data_dir}")
        logger.info(f"Using config file: {config.CONFIG_FILE}")
        
        # Download attachments
        # downloaded_files = download_issue_attachments(
        #     "TC-44",
        #     str(config.CONFIG_FILE), 
        #     str(data_dir)  # Pass the base data directory
        # )
        # Read CSV file containing Jira issue keys
        try:
            issues_df = pd.read_csv(data_dir / "jira_royal_tickets_batch_1.csv")
            if 'Issue key' not in issues_df.columns:
                logger.error("CSV file must contain a 'key' column with Jira issue keys")
                return 1
                
            downloaded_files = []
            
            # Process each issue key and download attachments
            for issue_key in issues_df["Issue key"].unique():
                logger.info(f"Downloading attachments for issue {issue_key}")
                
                # Download attachments for current issue
                issue_files = download_issue_attachments(
                    issue_key,
                    str(config.CONFIG_FILE),
                    str(data_dir)
                )
                
                if issue_files:
                    downloaded_files.extend(issue_files)
                    logger.info(f"Downloaded {len(issue_files)} files for issue {issue_key}")
                else:
                    logger.warning(f"No attachments found for issue {issue_key}")
                    
        except FileNotFoundError:
            logger.error(f"Could not find issues CSV file at {data_dir / 'issues.csv'}")
            return 1
        except pd.errors.EmptyDataError:
            logger.error("The issues CSV file is empty")
            return 1
        except Exception as e:
            logger.error(f"Error processing CSV file: {str(e)}")
            return 1
        
        if not downloaded_files:
            logger.error(f"Failed to download attachments to {data_dir}/downloads")
            return 1
            
        logger.info(f"Successfully downloaded {len(downloaded_files)} files to {data_dir}/downloads")
        return 0
        
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        return 1

if __name__ == "__main__":
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    sys.exit(main(from_date=from_date, to_date=to_date, query_name="closed_tickets_date_range"))