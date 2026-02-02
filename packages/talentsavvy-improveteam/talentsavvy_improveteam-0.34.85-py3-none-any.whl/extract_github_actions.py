import requests
import json
import time
import re
from datetime import datetime, timezone
from typing import Optional, Dict, List
import pytz  # Import pytz to handle timezone conversions
import sys
import os
import argparse

base_dir = os.path.dirname(os.path.abspath(__file__))
common_dir = os.path.join(base_dir, "common")
if not os.path.isdir(common_dir):
    # go up one level to find "common" (for installed package structure)
    base_dir = os.path.dirname(base_dir)
    common_dir = os.path.join(base_dir, "common")

if os.path.isdir(common_dir) and base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from common.utils import Utils
import logging

# Configure logging to print messages on stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)

# GitHub and CI/CD API details - Configuration will be loaded from database
repos = None
repo_owner = None
personal_access_token = None
headers = None
valid_workflow_names = None


class GitHubActionsExtractor:
    """Extracts build events from GitHub Actions."""

    def __init__(self):
        self.stats = {
            'build_events_inserted': 0,
            'build_events_duplicates': 0
        }

    def get_config_from_database(self, cursor):
        """Fetch GitHub Actions configuration from data_source_config table."""
        cursor.execute("""
            SELECT config_item, config_value
            FROM data_source_config
            WHERE data_source = 'integration_and_build'
            AND config_item IN ('Organization', 'Repos', 'Personal Access Token', 'Workflows', 'Build Stage Pattern')
        """)

        config = {}
        for row in cursor.fetchall():
            config[row[0]] = row[1]

        return config

    def get_last_modified_date(self, cursor) -> Optional[datetime]:
        """Get the last modified date from the database."""
        query = "SELECT MAX(timestamp_utc) FROM build_event"
        cursor.execute(query)
        result = cursor.fetchone()
        if result[0]:
            # Convert to naive datetime if timezone-aware
            dt = result[0]
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        else:
            return datetime(2000, 1, 1)

    def run_extraction(self, cursor, config: Dict, start_date: Optional[str], last_modified: Optional[datetime], export_path: str = None):
        """
        Run extraction: fetch and save data.

        Args:
            cursor: Database cursor (None for CSV mode)
            config: Configuration dictionary
            start_date: Start date from command line (optional)
            last_modified: Last modified datetime from database or checkpoint
            export_path: Export path for CSV mode
        """
        # Track maximum timestamp for checkpoint saving
        max_timestamp = None

        # Set up global variables from configuration (needed by fetch_builds)
        global repo_owner, repos, personal_access_token, headers, valid_workflow_names
        repo_owner = config.get('Organization')

        # Parse repositories
        repos_config = config.get('Repos', '')
        if repos_config:
            try:
                repos = json.loads(repos_config)
            except (json.JSONDecodeError, TypeError):
                repos = repos_config.split(',')
        else:
            repos = []

        personal_access_token = config.get('Personal Access Token')

        # Parse workflows
        workflows_config = config.get('Workflows', '')
        if workflows_config:
            try:
                valid_workflow_names = json.loads(workflows_config)
            except (json.JSONDecodeError, TypeError):
                valid_workflow_names = workflows_config.split(',')
        else:
            valid_workflow_names = []

        # Validate configuration
        if not repo_owner or not repos or not personal_access_token:
            logging.error("Missing required configuration: Organization / Personal Access Token / Repos")
            sys.exit(1)

        # Set up headers
        headers = {
            'Authorization': f'Bearer {personal_access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        # Determine start date
        if start_date:
            try:
                extraction_start_date = datetime.strptime(start_date, '%Y-%m-%d')
                # Convert to naive UTC datetime
                if extraction_start_date.tzinfo is not None:
                    extraction_start_date = extraction_start_date.astimezone(pytz.utc).replace(tzinfo=None)
                else:
                    # Ensure naive datetime
                    extraction_start_date = extraction_start_date.replace(tzinfo=None)
            except ValueError:
                logging.error("Invalid date format. Please use YYYY-MM-DD format.")
                sys.exit(1)
        else:
            if last_modified:
                # Convert to naive datetime if timezone-aware
                if last_modified.tzinfo is not None:
                    last_modified = last_modified.replace(tzinfo=None)
                extraction_start_date = last_modified
            else:
                extraction_start_date = datetime(2000, 1, 1)

        # Set up save function
        if cursor:
            # Database mode

            def save_output_fn(build_data_list):
                if build_data_list:
                    data_count, inserted_count, duplicate_count = insert_build_data_batch(cursor, build_data_list)
                    self.stats['build_events_inserted'] += inserted_count
                    self.stats['build_events_duplicates'] += duplicate_count
                    return data_count, inserted_count, duplicate_count
                return 0, 0, 0
        else:
            # CSV mode - create CSV file lazily
            build_csv_file = None

            def save_output_fn(build_data_list):
                nonlocal build_csv_file, max_timestamp

                if not build_data_list:
                    return 0, 0, 0

                # Convert tuples to dictionaries for CSV
                # Tuple format: (source_branch, repo, event, timestamp_utc, actor, workflow_name, build_number, build_id, comment)
                build_events = []
                for build_tuple in build_data_list:
                    timestamp_utc = build_tuple[3]
                    # Convert to naive UTC datetime if needed
                    if timestamp_utc:
                        if isinstance(timestamp_utc, datetime):
                            if timestamp_utc.tzinfo is not None:
                                timestamp_utc = timestamp_utc.astimezone(pytz.utc).replace(tzinfo=None)
                        else:
                            timestamp_utc = datetime.fromisoformat(str(timestamp_utc).replace('Z', '+00:00'))
                            if timestamp_utc.tzinfo is not None:
                                timestamp_utc = timestamp_utc.astimezone(pytz.utc).replace(tzinfo=None)

                    build_event_dict = {
                        'timestamp_utc': timestamp_utc,
                        'event': build_tuple[2],
                        'repo': build_tuple[1].lower() if build_tuple[1] else '',
                        'source_branch': build_tuple[0],
                        'workflow_name': build_tuple[5],
                        'build_number': build_tuple[6],
                        'comment': build_tuple[8],
                        'actor': build_tuple[4],
                        'build_id': build_tuple[7]
                    }
                    build_events.append(build_event_dict)

                # Create CSV file lazily when first events arrive
                if build_events and not build_csv_file:
                    build_csv_file = Utils.create_csv_file("github_actions_build_events", export_path, logging)

                # Save build events
                build_max_ts = None
                if build_events:
                    result = Utils.save_events_to_csv(build_events, build_csv_file, logging)
                    if len(result) > 3 and result[3]:
                        build_max_ts = result[3]

                # Track maximum timestamp for checkpoint
                if build_max_ts and (not max_timestamp or build_max_ts > max_timestamp):
                    max_timestamp = build_max_ts

                return len(build_events), 0, 0

        # Read build stage pattern from database (if in database mode)
        build_event_regex = None
        if cursor:
            try:
                cursor.execute("""
                    SELECT config_value
                    FROM data_source_config
                    WHERE data_source = 'integration_and_build'
                    AND config_item = 'Build Stage Pattern'
                """)
                result = cursor.fetchone()
                if result and result[0]:
                    build_event_pattern = result[0].strip() or None
                    if build_event_pattern:
                        try:
                            # Handle escaped backslashes from database
                            build_event_pattern = build_event_pattern.replace("\\\\", "\\")
                            build_event_regex = re.compile(build_event_pattern, re.IGNORECASE)
                            logging.info(f"Loaded build event regex pattern: {build_event_pattern}")
                        except re.error as e:
                            logging.warning(f"Invalid build event regex pattern: {build_event_pattern}, error: {e}")
                            build_event_regex = None
            except Exception as e:
                logging.warning(f"Failed to read build stage pattern from data_source_config: {e}")
                build_event_regex = None

        # Log the fetch information
        logging.info(f"Workflow names: {valid_workflow_names}")
        logging.info(f"Starting extraction from {extraction_start_date}")

        # Fetch builds for each repository
        for repo in repos:
            repo = repo.strip()  # Remove any whitespace
            logging.info(f"Fetching data from https://api.github.com/repos/{repo_owner}/{repo}")

            try:
                # Fetch builds and get actual counts
                build_data_list = fetch_builds(repo, extraction_start_date, build_event_regex)

                if build_data_list:
                    # Save events
                    save_output_fn(build_data_list)

            except Exception as e:
                logging.error(f"Error processing repository {repo}: {str(e)}")
                continue

        # Save checkpoint in CSV mode
        if not cursor and max_timestamp:
            if Utils.save_checkpoint(prefix="github_actions", last_dt=max_timestamp, export_path=export_path):
                logging.info(f"Checkpoint saved successfully: {max_timestamp}")
            else:
                logging.warning("Failed to save checkpoint")

        # Print summary
        if cursor:
            total_inserted = self.stats['build_events_inserted']
            total_duplicates = self.stats['build_events_duplicates']
            logging.info(f"Total: inserted {total_inserted} events, skipped {total_duplicates} duplicates")
        else:
            logging.info(f"Extraction completed")


# Function to safely extract data and handle missing or invalid fields
def safe_get(data, keys, default_value='NULL'):
    try:
        for key in keys:
            data = data[key]
        return data
    except (KeyError, TypeError):
        return default_value


# Function to insert build data into the build_event table using batch insertion
def insert_build_data_batch(cursor, build_data_list):
    """Insert build data into the database using batch insertion."""
    if not build_data_list:
        return 0, 0, 0

    from psycopg2.extras import execute_values

    # Get count before insertion
    cursor.execute("SELECT COUNT(*) FROM build_event")
    count_before = cursor.fetchone()[0]

    # Use execute_values for batch insertion
    columns = [
        'source_branch', 'repo', 'event', 'timestamp_utc', 'actor', 'workflow_name', 'build_number', 'build_id', 'comment'
    ]

    execute_values(
        cursor,
        f"INSERT INTO build_event ({', '.join(columns)}) VALUES %s ON CONFLICT DO NOTHING",
        build_data_list,
        template=None,
        page_size=1000
    )

    # Get count after insertion to determine actual inserted records
    cursor.execute("SELECT COUNT(*) FROM build_event")
    count_after = cursor.fetchone()[0]

    # Calculate actual inserted and skipped records
    inserted_count = count_after - count_before
    duplicate_count = len(build_data_list) - inserted_count

    return len(build_data_list), inserted_count, duplicate_count


# Function to fetch jobs for a specific workflow run
def fetch_jobs_for_run(repo, run_id) -> List[Dict]:
    """Fetch all jobs for a specific workflow run."""
    jobs_url = f"https://api.github.com/repos/{repo_owner}/{repo}/actions/runs/{run_id}/jobs?per_page=100"
    all_jobs = []

    while jobs_url:
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                logging.info(f"Fetching jobs from: {jobs_url}")
                response = requests.get(jobs_url, headers=headers, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    jobs = data.get('jobs', [])
                    all_jobs.extend(jobs)

                    # Check for pagination
                    if 'next' in response.links:
                        jobs_url = response.links['next']['url']
                    else:
                        jobs_url = None
                    break

                elif response.status_code == 429:
                    # Rate limit exceeded
                    if 'Retry-After' in response.headers:
                        wait_time = int(response.headers['Retry-After'])
                        logging.warning(f"Rate limit exceeded. Waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logging.warning("Rate limit exceeded for GitHub Actions jobs API")
                        jobs_url = None
                        break
                else:
                    logging.warning(f"Failed to fetch jobs for run {run_id}: {response.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        jobs_url = None
                        break

            except requests.RequestException as e:
                logging.warning(f"Request failed for jobs (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                else:
                    jobs_url = None
                    break
        else:
            # All retries exhausted without break
            jobs_url = None

    return all_jobs


# Function to fetch build from CI/CD system with If-Modified-Since header
def fetch_builds(repo, last_modified_date, build_event_regex=None):
    # Format the last modified date to the proper HTTP date format
    if_modified_since = last_modified_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
    headers['If-Modified-Since'] = if_modified_since

    builds_url = f"https://api.github.com/repos/{repo_owner}/{repo}/actions/runs?per_page=100"
    build_data_list = []

    while builds_url:
        # Retry logic for failed requests
        max_retries = 3
        retry_delay = 1  # seconds

        for attempt in range(max_retries):
            try:
                logging.info(f"Fetching workflow runs from: {builds_url}")
                response = requests.get(builds_url, headers=headers, timeout=30)

                if response.status_code == 200:
                    builds = response.json()
                    break
                elif response.status_code == 304:
                    # Not modified since last check
                    logging.info(f"No new builds since {last_modified_date}.")
                    return build_data_list
                elif response.status_code == 429:
                    # Rate limit exceeded
                    if 'Retry-After' in response.headers:
                        wait_time = int(response.headers['Retry-After'])
                        logging.warning(f"Rate limit exceeded. Waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logging.warning("Rate limit exceeded for GitHub Actions")
                        return build_data_list
                else:
                    logging.warning(f"Failed to fetch GitHub Actions runs: {response.status_code} - {response.text}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                        continue
                    else:
                        return build_data_list

            except requests.RequestException as e:
                logging.warning(f"Request failed for GitHub Actions runs (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    return build_data_list
            except Exception as ex:
                logging.error(f"Error fetching GitHub Actions runs: {ex}")
                return build_data_list
        else:
            return build_data_list

        # Process the workflow runs from the response
        for build in builds['workflow_runs']:
            workflow_name = safe_get(build, ['name'], 'NULL')
            # Skip builds that don't match the valid workflow names
            if valid_workflow_names and workflow_name not in valid_workflow_names:
                continue

            # Check run's updated_at BEFORE fetching jobs (expensive API call)
            run_updated_at = build.get('updated_at')
            if run_updated_at:
                try:
                    run_dt = datetime.fromisoformat(str(run_updated_at).replace('Z', '+00:00'))
                    if run_dt.tzinfo is not None:
                        run_dt = run_dt.astimezone(timezone.utc).replace(tzinfo=None)
                    # Skip runs not updated since last extraction
                    if run_dt <= last_modified_date:
                        continue
                except (ValueError, TypeError):
                    pass

            # Get run-level data
            run_id = safe_get(build, ['id'], None)
            branch = safe_get(build, ['head_branch'], None)
            release_str = None
            if branch.startswith("release/"):
                release_str = branch.split("release/")[1]
            elif branch == "main":
                release_str = "0.0"
            build_number = safe_get(build, ['run_number'], None)
            commit_sha = safe_get(build, ['head_sha'], None)  # Full SHA for join key
            short_sha = commit_sha[:7] if len(commit_sha) >= 7 else safe_get(commit_sha)
            actor = safe_get(build, ['actor', 'login'], None)

            # Skip if no run_id
            if not run_id:
                continue

            # Fetch jobs for this workflow run
            jobs = fetch_jobs_for_run(repo, run_id)

            # Track deduplication: (repo, workflow_name, build_number) combinations that have already matched
            build_created_repo_workflow_build_numbers = set()

            for job in jobs:
                # Get job name - this goes in 'event' column
                job_name = job.get('name')
                if not job_name:
                    continue

                # Get timestamp: MUST have completed_at (only include completed jobs)
                completed_at = job.get('completed_at')
                if not completed_at:
                    continue  # Skip jobs that haven't completed

                # Convert completed_at to naive UTC datetime
                try:
                    timestamp_utc = datetime.fromisoformat(str(completed_at).replace('Z', '+00:00'))
                    if timestamp_utc.tzinfo is not None:
                        timestamp_utc = timestamp_utc.astimezone(timezone.utc).replace(tzinfo=None)
                except (ValueError, TypeError):
                    continue

                # Skip jobs older than the last known modification date
                if timestamp_utc <= last_modified_date:
                    continue

                # Get job conclusion (success, failure, cancelled, etc.)
                conclusion = job.get('conclusion', '').lower()

                # Build comment as JSON with useful metadata
                comment_data = {
                    'job_id': job.get('id'),
                    'run_id': run_id,
                    'conclusion': job.get('conclusion'),
                    'status': job.get('status'),
                    'started_at': job.get('started_at')
                }
                comment = json.dumps(comment_data)

                # Determine event name based on build stage pattern matching
                event_name = job_name  # Default to job name
                
                # Check if job name matches build event pattern
                if build_event_regex and job_name:
                    if build_event_regex.search(job_name):
                        # Create unique key for this (repo, workflow_name, build_number) combination
                        repo_lower = (repo or '').lower()
                        repo_workflow_build_key = (repo_lower, workflow_name, build_number)
                        
                        # Only create "Build Created" or "Build Failed" event if we haven't already created one for this (repo, workflow_name, build_number)
                        if repo_workflow_build_key not in build_created_repo_workflow_build_numbers:
                            if conclusion == 'success':
                                event_name = 'Build Created'
                                build_created_repo_workflow_build_numbers.add(repo_workflow_build_key)
                            elif conclusion == 'failure':
                                event_name = 'Build Failed'
                                build_created_repo_workflow_build_numbers.add(repo_workflow_build_key)
                            # For other conclusions (cancelled, skipped, etc.), keep job_name as event
                            # Note: We don't add to the set for cancelled/skipped, so a later matching job with success/failure can still create an event

                if not release_str:
                    build_id = commit_sha
                else:
                    date_str = timestamp_utc.date().isoformat()
                    build_id = f"{release_str}.{build_number}-{date_str}-{short_sha}"

                build_data = (
                    branch,
                    repo,
                    event_name,  # Event name (may be "Build Created", "Build Failed", or job_name)
                    timestamp_utc,
                    actor,
                    workflow_name,
                    build_number,
                    build_id,
                    comment
                )
                build_data_list.append(build_data)

        # Check for pagination
        if 'next' in response.links:
            builds_url = response.links['next']['url']
        else:
            builds_url = None  # No more pages to fetch

    return build_data_list


# Main Execution: Fetching data for each repo and writing to the database
def main():
    parser = argparse.ArgumentParser(description="Add new events in the build_event table.")

    parser.add_argument('-p', '--product', type=str, help='Product name (if provided, saves to database; otherwise saves to CSV)')
    parser.add_argument('-s', '--start-date', type=str, help='Start date in YYYY-MM-DD format')
    args = parser.parse_args()

    extractor = GitHubActionsExtractor()

    if args.product is None:
        # CSV Mode: Load configuration from config.json
        config = json.load(open(os.path.join(common_dir, "config.json")))
        
        # Get configuration from config dictionary
        repos_str = config.get("GITHUB_REPOS", '')
        repos_list = [repo.strip() for repo in repos_str.split(",") if repo.strip()] if repos_str else []

        workflows_str = config.get("GITHUB_WORKFLOWS", '')
        workflows_list = [wf.strip() for wf in workflows_str.split(",") if wf.strip()] if workflows_str else []

        config = {
            'Organization': config.get('GITHUB_ORGANIZATION'),
            'Repos': json.dumps(repos_list) if repos_list else '',
            'Personal Access Token': config.get('GITHUB_API_TOKEN'),
            'Workflows': json.dumps(workflows_list) if workflows_list else ''
        }

        # Use checkpoint file for last modified date
        last_modified = Utils.load_checkpoint("github_actions")

        extractor.run_extraction(None, config, args.start_date, last_modified)

    else:
        # Database Mode: Connect to the database
        from database import DatabaseConnection
        db = DatabaseConnection()
        with db.product_scope(args.product) as conn:
            with conn.cursor() as cursor:
                config = extractor.get_config_from_database(cursor)
                last_modified = extractor.get_last_modified_date(cursor)
                extractor.run_extraction(cursor, config, args.start_date, last_modified)

    return 0


# Run the main function
if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
