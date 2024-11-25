import json
import sys
import logging
from pathlib import Path
from typing import Dict, Optional, List
from atlassian import Jira

from common.jira_util import (
    load_jql_queries,
    count_issues_in_project,
    export_issues_to_csv
)

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
    QUERIES_FILE = Path("config/queries.json")
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


def main():
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

        # Process closed tickets if query exists
        if queries.get("closed_tickets", {}).get("query"):
            if not process_query_type(
                "closed",
                queries["closed_tickets"]["query"],
                config,
                stats
            ):
                logger.error("Failed to process closed tickets")
                return 1
        else:
            logger.warning("No closed tickets query found in configuration")

        # Process canceled tickets if query exists
        if queries.get("canceled_tickets", {}).get("query"):
            if not process_query_type(
                "canceled",
                queries["canceled_tickets"]["query"],
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

        # Print statistics if any queries were processed
        if stats:
            print_statistics(stats)
        else:
            logger.warning("No queries were processed")

        return 0

    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
