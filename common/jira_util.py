import json
import csv
import logging
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from atlassian import Jira

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_current_state_issue(key: str, it_status: str, filename: str) -> Optional[Dict]:
    """
    Find the current state of an issue in a CSV file.

    Args:
        key: Issue key to search for
        it_status: IT status to match
        filename: Path to the CSV file

    Returns:
        Dictionary containing the row data if found, None otherwise
    """
    try:
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if (row['key'] == key and row['it_status'] == it_status):
                    return dict(row)
        return None
    except FileNotFoundError:
        logger.error("File not found: %s", filename)
        return None


def jira_acct_get(team: str) -> Optional[Jira]:
    """
    Get Jira account instance for a team.

    Args:
        team: Team name to get credentials for

    Returns:
        Jira instance if successful, None otherwise
    """
    try:
        config_path = Path("config")
        jira_accts_list = "jira_team_accounts.json"
        jira_accounts = jira_accounts_retrieve(config_path / jira_accts_list)
        jira_acct = team_setting_retrieve(team, jira_accounts)

        logger.debug("Team: %s, Account: %s", team, jira_acct.get('account'))

        return Jira(
                                # url='https://fecredit.atlassian.net',
        url='https://royal-solution.atlassian.net',
            username=jira_acct.get('account'),
            password=jira_acct.get('token')
        )
    except Exception as e:
        logger.error("Failed to get Jira account: %s", str(e))
        return None


def jira_issue_info_by_id_get(ticket: str, jira_acct: Jira) -> Optional[Dict]:
    """Get issue information by ticket ID."""
    try:
        issue = jira_acct.get_issue(ticket)
        return json.loads(json.dumps(issue, indent=4))
    except Exception as e:
        logger.error("Failed to get issue info: %s", str(e))
        return None


def jira_issue_parsed_data_get(
    json_data: Dict,
    data: Dict,
    applied_filter: str = 'N',
    filters: Optional[List[str]] = None
) -> List[Any]:
    """
    Parse Jira issue data based on filters.

    Args:
        json_data: Raw JSON data from Jira
        data: Parsing configuration
        applied_filter: Filter flag ('Y' or 'N')
        filters: List of filters to apply

    Returns:
        List of parsed data objects
    """
    filters = filters or []
    row = []

    for item in data:
        if (applied_filter == 'Y' and item in filters) or applied_filter == 'N':
            parsed_obj = perform_operation(item, json_data, data[item])
            row.append(parsed_obj)

    return row


def issue_data_extract(issue_id: str, team: str, filters: List[str]) -> List[Any]:
    """Extract issue data with filters."""
    jira_acct = jira_acct_get(team)
    if not jira_acct:
        return []

    issue_json_data = jira_issue_info_by_id_get(issue_id, jira_acct)
    if not issue_json_data:
        return []

    parsing_paths_data = path_parsing_data_get("parsing_paths_v9.json")
    return jira_issue_parsed_data_get(
        issue_json_data,
        parsing_paths_data,
        'Y',
        filters
    )


def jql_v2_print(jqltemplate_str: str, p_from: str, p_to: str) -> str:
    """Format JQL template with parameters."""
    return jqltemplate_str.format(p_from=p_from, p_to=p_to)


def path_parsing_data_get(parsing_file_path: str) -> Dict:
    """Get parsing configuration from file."""
    config_path = Path("config-pattern")
    return read_json_file(config_path / parsing_file_path)


def jira_issue_comment_add(
    jira_account: Jira,
    issue_id_or_key: str,
    comment: str
) -> Dict[str, str]:
    """
    Add a comment to a Jira issue.

    Returns:
        Dictionary containing operation result
    """
    try:
        jira_account.issue_add_comment(issue_id_or_key, comment)
        result = "success"
    except Exception as e:
        logger.error("Failed to add comment: %s", str(e))
        result = "failure"

    return {
        "key": issue_id_or_key,
        "function_name": "jira_issue_comment_add",
        "result": result
    }


def jira_issue_comments_get(jira_account: Jira, issue_id_or_key: str) -> List[Dict]:
    """Get all comments for a Jira issue."""
    try:
        issue = jira_account.get_issue(issue_id_or_key)
        return issue['fields']['comment']['comments']
    except Exception as e:
        logger.error("Failed to get comments: %s", str(e))
        return []


def get_jira_credentials(config_file: str) -> Tuple[Optional[str], Optional[str]]:
    """Get Jira credentials from config file."""
    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            config = json.load(file)
            # account_info = config['team_accounts'][0]['IT CM']
            account_info = config['team_accounts'][1]['ROYAL']
            return account_info['account'], account_info['token']
    except Exception as e:
        logger.error("Failed to read credentials: %s", str(e))
        return None, None


def get_jira_issues(
    jql: str,
    config_file: str,
    max_results: int = 50,
    fields: Optional[List[str]] = None,
    expand: Optional[str] = None
) -> Tuple[List[Dict], int]:
    """Get Jira issues with pagination."""
    username, password = get_jira_credentials(config_file)
    if not username or not password:
        return [], 0

    try:
        jira = Jira(
                    # url='https://fecredit.atlassian.net',
        url='https://royal-solution.atlassian.net',
            username=username,
            password=password
        )

        all_issues = []
        start_at = 0
        total_records = 0

        while True:
            try:
                response = jira.jql(
                    jql,
                    start=start_at,
                    limit=max_results,
                    fields=fields,
                    expand=expand
                )
                all_issues.extend(response['issues'])
                total_records = response['total']

                if len(response['issues']) < max_results:
                    break

                start_at += max_results

            except (KeyError, ConnectionError, TimeoutError) as e:
                logger.error("Error fetching issues: %s", str(e))
                break

        return all_issues, total_records

    except Exception as e:
        logger.error("Failed to initialize Jira client: %s", str(e))
        return [], 0


def export_issues_to_csv(
    jql: str,
    config_file: str,
    fields: List[str],
    output_file: str,
    max_results: int = 1000,
    start_at: int = 0,
    delimiter: str = ','
) -> Tuple[bool, int]:
    """Export Jira issues to CSV file."""
    username, password = get_jira_credentials(config_file)
    if not username or not password:
        logger.error("Invalid credentials")
        return False, 0

    try:
        jira = Jira(
                    # url='https://fecredit.atlassian.net',
        url='https://royal-solution.atlassian.net',
            username=username,
            password=password
        )

        csv_data = jira.csv(
            jql,
            limit=max_results,
            start=start_at,
            all_fields=False,
            delimiter=delimiter
        )
        csv_string = csv_data.decode('utf-8')

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            csvfile.write(csv_string)

        total_exported = len(csv_string.split('\n')) - 2
        logger.info("Exported %d issues to %s", total_exported, output_file)
        return True, total_exported

    except Exception as e:
        logger.error("Failed to export issues: %s", str(e))
        return False, 0


def load_jql_queries(query_file: str) -> Optional[Dict]:
    """Load JQL queries from config file."""
    try:
        with open(query_file, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logger.error("Failed to read JQL queries: %s", str(e))
        return None


def count_issues_in_project(jql, config_file, max_results=1000, page_size=100):
    """
    Count the total number of issues in a Jira project based on the provided JQL with pagination.

    :param jql: JQL query string to filter issues
    :param config_file: Path to the JSON configuration file for credentials
    :param max_results: Maximum number of results to fetch per request
    :param page_size: Number of records per page (default 100)
    :return: Tuple of (total issues, total records, total pages) or (0, 0, 0) if an error occurs
    """
    username, password = get_jira_credentials(config_file)
    if username is None or password is None:
        return 0, 0, 0

    jira = Jira(
        # url='https://fecredit.atlassian.net',
        url='https://royal-solution.atlassian.net',
        username=username,
        password=password
    )

    total_issues = 0
    start_at = 0

    while True:
        try:
            response = jira.jql(jql, start=start_at,
                                limit=max_results, fields="*none")
            total_issues += len(response['issues'])
            total_records = response.get("total", 0)
            total_pages = (total_records + page_size -
                           1) // page_size  # Ceiling division

            if len(response['issues']) < max_results:
                break
            start_at += max_results
        except KeyError as e:
            print(f"Error in response structure: {str(e)}")
            return total_issues, total_records, total_pages
        except (ConnectionError, TimeoutError) as e:
            print(f"Network error occurred: {str(e)}")
            return total_issues, total_records, total_pages
        except Exception as e:
            print(f"Failed to count issues: {str(e)}")
            return total_issues, total_records, total_pages

    return total_issues, total_records, total_pages

def download_issue_attachments(issue_key: str, config_file: str, output_dir: str) -> List[str]:
    """
    Download all attachments from a Jira issue.
    """
    try:
        # Create output directory if it doesn't exist
        output_path = Path(output_dir) / "downloads"  # Ensure we use downloads subdirectory
        output_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving attachments to: {output_path}")
        
        # Get credentials
        username, password = get_jira_credentials(config_file)
        if not username or not password:
            logger.error("Failed to get credentials from config file")
            return []

        # Initialize Jira client and verify connection
        jira = Jira(
            url='https://royal-solution.atlassian.net',
            username=username,
            password=password
        )
        
        # Get issue details
        issue = jira.get_issue(issue_key)
        if not issue:
            logger.error(f"Could not find issue {issue_key}")
            return []
            
        attachments = issue.get('fields', {}).get('attachment', [])
        
        if not attachments:
            logger.info(f"No attachments found for issue {issue_key}")
            return []

        downloaded_files = []
        
        # Download each attachment
        for attachment in attachments:
            filename = attachment['filename']
            file_path = output_path / filename
            
            # Ensure the file path is safe
            if not str(file_path).startswith(str(output_path)):
                logger.warning(f"Skipping potentially unsafe path: {filename}")
                continue
                
            content = jira.download_attachments_from_issue(issue_key, attachment['id'])
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(content)
                
            downloaded_files.append(str(file_path))
            logger.info(f"Downloaded attachment {filename} from issue {issue_key}")
            
        return downloaded_files

    except Exception as e:
        logger.error(f"Failed to download attachments for issue {issue_key}: {str(e)}")
        return []
