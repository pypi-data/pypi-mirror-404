#!/usr/bin/env python3
"""
GitLab CI Build Events Extraction Script

This script extracts build events from GitLab CI pipelines/jobs and saves them to the database.

Usage:
    python extract_gitlab_actions.py -p <product_name> [-s <start_date>]

Modes:
    - Database Mode: if -p/--product is provided
    - CSV Mode: if -p/--product is NOT provided (writes CSV + checkpoint)

Configuration (config.json - CSV Mode):
    - GITLAB_ACTIONS_API_URL: GitLab API URL (e.g., https://gitlab.com)
    - GITLAB_ACTIONS_API_TOKEN: Personal Access Token
    - GITLAB_ACTIONS_PROJECT: GitLab group/namespace name
    - GITLAB_ACTIONS_REPOS: Comma-separated list of repository names

Configuration (data_source_config table - Database Mode):
    - data_source: 'integration_and_build'
    - config_items: 'URL', 'Personal Access Token', 'Projects', 'Repos'
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import quote

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_dir = os.path.dirname(os.path.abspath(__file__))
common_dir = os.path.join(base_dir, "common")
if not os.path.isdir(common_dir):
    # go up one level to find "common" (for installed package structure)
    base_dir = os.path.dirname(base_dir)
    common_dir = os.path.join(base_dir, "common")

if os.path.isdir(common_dir) and base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from common.utils import Utils

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger('extract_gitlab_actions')


def safe_get(data, keys, default_value=None):
    """Safely extract data and handle missing or invalid fields."""
    try:
        for key in keys:
            data = data[key]
        return data
    except (KeyError, TypeError, IndexError):
        return default_value


class GitLabActionsExtractor:
    """Extracts build and deployment events from GitLab CI pipelines/jobs."""

    def __init__(self):
        self.base_url = None
        self.api_token = None
        self.headers = None
        self.group = None
        self.repos = None
        
        # Statistics
        self.stats = {
            'build_events': 0,
            'deployment_events': 0,
            'total_inserted': 0,
            'total_duplicates': 0,
            'deployment_events_inserted': 0,
            'deployment_events_duplicates': 0
        }

    def get_config_from_database(self, cursor) -> Dict:
        """Fetch GitLab CI configuration from data_source_config table."""
        query = """
        SELECT config_item, config_value
        FROM data_source_config
        WHERE data_source = 'integration_and_build'
        AND config_item IN ('Organization', 'Personal Access Token', 'Projects', 'Repos')
        """
        cursor.execute(query)
        results = cursor.fetchall()

        config = {}
        for config_item, config_value in results:
            if config_item == 'Repos':
                try:
                    repos = json.loads(config_value) if config_value else []
                    config['repos'] = repos if repos else []
                except (json.JSONDecodeError, TypeError):
                    config['repos'] = [r.strip() for r in config_value.split(',') if r.strip()] if config_value else []
            elif config_item == 'Organization':
                # Store base URL without /api/v4 suffix
                base_url = config_value.rstrip('/') if config_value else ''
                if base_url:
                    if base_url.endswith('/api/v4'):
                        base_url = base_url[:-7]
                    if not base_url.startswith(('http://', 'https://')):
                        base_url = f"https://{base_url}"
                config['base_url'] = base_url
            elif config_item == 'Personal Access Token':
                config['api_token'] = config_value
            elif config_item == 'Projects':
                try:
                    projects = json.loads(config_value) if config_value else []
                    config['group'] = projects[0] if projects else None
                except (json.JSONDecodeError, TypeError):
                    config['group'] = config_value.strip() if config_value else None

        return config

    def get_last_modified_date(self, cursor) -> Optional[datetime]:
        """Get the last modified date from the database."""
        query = "SELECT MAX(timestamp_utc) FROM build_event"
        cursor.execute(query)
        result = cursor.fetchone()
        if result[0]:
            dt = result[0]
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        return None

    def _make_api_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """
        Make an API request to GitLab with retry logic.

        Args:
            url: Full API URL
            params: Query parameters

        Returns:
            Response JSON as dict or list, or None if request fails
        """
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30, verify=False)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limit exceeded
                    retry_after = response.headers.get('Retry-After', '60')
                    wait_time = int(retry_after) + 10
                    logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.warning(f"API request failed: {response.status_code} - {response.text}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                    break

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                break

        return None

    def fetch_pipelines(self, project_id: str, start_date: datetime) -> List[Dict]:
        """
        Fetch pipelines for a specific project since start_date.
        
        Args:
            project_id: Encoded project ID (group/repo)
            start_date: Start date for extraction
            
        Returns:
            List of pipeline dictionaries
        """
        encoded_project_id = quote(project_id, safe='')
        url = f"{self.base_url}/api/v4/projects/{encoded_project_id}/pipelines"
        
        all_pipelines = []
        page = 1

        while True:
            params = {
                'per_page': 100,
                'page': page,
                'order_by': 'updated_at',
                'sort': 'desc',
                'updated_after': start_date.isoformat()
            }

            logger.info(f"[Pipelines] Fetching page {page}...")
            data = self._make_api_request(url, params)

            if not data or not isinstance(data, list):
                break

            if not data:
                break

            all_pipelines.extend(data)
            logger.info(f"[Pipelines] Page {page}: Fetched {len(data)} pipelines")

            # Check if this is the last page
            if len(data) < 100:
                break

            page += 1

        return all_pipelines

    def fetch_pipeline_jobs(self, project_id: str, pipeline_id: int) -> List[Dict]:
        """
        Fetch jobs for a specific pipeline.
        
        Args:
            project_id: Encoded project ID (group/repo)
            pipeline_id: Pipeline ID
            
        Returns:
            List of job dictionaries
        """
        encoded_project_id = quote(project_id, safe='')
        url = f"{self.base_url}/api/v4/projects/{encoded_project_id}/pipelines/{pipeline_id}/jobs"
        
        all_jobs = []
        page = 1

        while True:
            params = {
                'per_page': 100,
                'page': page
            }

            data = self._make_api_request(url, params)

            if not data or not isinstance(data, list):
                break

            if not data:
                break

            all_jobs.extend(data)

            # Check if this is the last page
            if len(data) < 100:
                break

            page += 1

        return all_jobs

    def create_build_event_from_job(self, repo_name: str, pipeline: Dict, job: Dict, min_timestamp: datetime) -> Optional[Dict]:
        """
        Create build event dictionary from a GitLab job.

        Args:
            repo_name: Repository name
            pipeline: Pipeline data
            job: Job data
            min_timestamp: Minimum timestamp for filtering

        Returns:
            Build event dictionary or None if job should be skipped
        """
        # Get job name (required)
        job_name = safe_get(job, ['name'], None)
        if not job_name:
            return None

        # Get timestamp: MUST have finished_at (only include completed jobs)
        finished_at_raw = safe_get(job, ['finished_at'], None)
        if not finished_at_raw:
            return None  # Skip jobs that haven't finished

        timestamp_utc = Utils.convert_to_utc(finished_at_raw)
        if not timestamp_utc:
            return None

        # Skip jobs older than or equal to min_timestamp
        if timestamp_utc <= min_timestamp:
            return None

        # Get pipeline data
        source_branch = safe_get(pipeline, ['ref'], None)
        build_id = safe_get(pipeline, ['sha'], None)  # Full SHA for join key
        pipeline_id = safe_get(pipeline, ['id'], None)
        workflow_name = safe_get(pipeline, ['name'], None)  # Pipeline name (may be null)

        # Get job data
        job_id = safe_get(job, ['id'], None)
        build_number = str(job_id) if job_id else None
        status = safe_get(job, ['status'], None)
        stage = safe_get(job, ['stage'], None)
        tag = safe_get(job, ['tag'], None)  # Boolean: true if triggered by git tag
        tag_list = safe_get(job, ['tag_list'], None)  # Runner tags
        started_at_raw = safe_get(job, ['started_at'], None)
        created_at_raw = safe_get(job, ['created_at'], None)

        # Get actor
        actor = safe_get(job, ['user', 'username'], None)
        if not actor:
            actor = safe_get(pipeline, ['user', 'username'], None)

        # Build comment as JSON with useful metadata
        comment_data = {
            'pipeline_id': pipeline_id,
            'stage': stage,
            'status': status,
            'tag': tag,
            'tag_list': tag_list,
            'started_at': started_at_raw,
            'created_at': created_at_raw
        }
        comment = json.dumps(comment_data)

        return {
            'timestamp_utc': timestamp_utc,
            'event': job_name,
            'repo': repo_name.lower(),
            'source_branch': source_branch,
            'build_id': build_id,
            'build_number': build_number,
            'comment': comment,
            'actor': actor,
            'workflow_name': workflow_name
        }

    def process_repositories(self, start_date: datetime) -> tuple:
        """
        Process all repositories and extract build and deployment events.
        
        Args:
            start_date: Start date for extraction
            
        Returns:
            Tuple of (build_events, deployment_events)
        """
        all_build_events = []
        all_deployment_events = []

        for repo_name in self.repos:
            repo_name = repo_name.strip()
            if not repo_name:
                continue

            logger.info(f"Processing repository: {repo_name}")

            # Construct full project path
            project_id = f"{self.group}/{repo_name}"

            try:
                # Fetch pipelines for this project
                pipelines = self.fetch_pipelines(project_id, start_date)
                logger.info(f"Found {len(pipelines)} pipelines for repo '{repo_name}'")

                if not pipelines:
                    continue

                # Process each pipeline
                for pipeline in pipelines:
                    pipeline_id = safe_get(pipeline, ['id'], None)
                    if not pipeline_id:
                        continue

                    # Fetch jobs for this pipeline
                    jobs = self.fetch_pipeline_jobs(project_id, pipeline_id)

                    if not jobs:
                        continue

                    # Track if any jobs were added for this pipeline
                    jobs_added = False

                    # Create build events from jobs
                    for job in jobs:
                        event = self.create_build_event_from_job(repo_name, pipeline, job, start_date)
                        if event:
                            all_build_events.append(event)
                            self.stats['build_events'] += 1
                            jobs_added = True

                    # Create deployment event for successful pipelines (only if we added jobs)
                    pipeline_status = safe_get(pipeline, ['status'], None)
                    if pipeline_status == 'success' and jobs_added:
                        pipeline_updated = safe_get(pipeline, ['updated_at'], None)
                        if pipeline_updated:
                            pipeline_dt = Utils.convert_to_utc(pipeline_updated)
                            if pipeline_dt and pipeline_dt > start_date:
                                # Get pipeline name for build_name
                                pipeline_name = safe_get(pipeline, ['name'], None) or str(pipeline_id)
                                
                                deployed_event = {
                                    'event_type': 'Build Deployed',
                                    'created_at': pipeline_dt,
                                    'target_iid': pipeline_name,  # Pipeline name as build_name
                                    'repo_name': repo_name,
                                    'branch_name': safe_get(pipeline, ['ref'], ''),
                                    'commit_sha': safe_get(pipeline, ['sha'], ''),
                                    'comment': f"Deployment of pipeline {pipeline_id} for {repo_name}",
                                    'environment': '',  # Empty as requested
                                }
                                all_deployment_events.append(deployed_event)
                                self.stats['deployment_events'] += 1

            except Exception as e:
                logger.error(f"Error processing repository {repo_name}: {str(e)}")
                continue

        return all_build_events, all_deployment_events

    def save_events_to_database(self, events: List[Dict], cursor) -> tuple:
        """
        Save build events to database.
        
        Args:
            events: List of build event dictionaries
            cursor: Database cursor
            
        Returns:
            Tuple of (total, inserted, duplicates)
        """
        if not events:
            return 0, 0, 0

        from psycopg2.extras import execute_values

        # Get count before insertion
        cursor.execute("SELECT COUNT(*) FROM build_event")
        count_before = cursor.fetchone()[0]

        # Prepare data for batch insertion
        columns = [
            'timestamp_utc', 'event', 'repo', 'source_branch', 
            'build_id', 'build_number', 'comment', 'actor', 'workflow_name'
        ]

        insert_data = []
        for event in events:
            insert_data.append((
                event.get('timestamp_utc'),
                event.get('event'),
                event.get('repo'),
                event.get('source_branch'),
                event.get('build_id'),
                event.get('build_number'),
                event.get('comment'),
                event.get('actor'),
                event.get('workflow_name')
            ))

        execute_values(
            cursor,
            f"INSERT INTO build_event ({', '.join(columns)}) VALUES %s ON CONFLICT ON CONSTRAINT build_event_hash_unique DO NOTHING",
            insert_data,
            template=None,
            page_size=1000
        )

        # Get count after insertion
        cursor.execute("SELECT COUNT(*) FROM build_event")
        count_after = cursor.fetchone()[0]

        inserted_count = count_after - count_before
        duplicate_count = len(insert_data) - inserted_count

        return len(insert_data), inserted_count, duplicate_count

    def save_deployment_events(self, events: List[Dict], cursor) -> tuple:
        """
        Save deployment events to deployment_event table.
        
        Args:
            events: List of deployment event dictionaries
            cursor: Database cursor
            
        Returns:
            Tuple of (inserted, duplicates)
        """
        if not events:
            return 0, 0

        from psycopg2.extras import execute_values

        # Get current count for duplicate detection
        count_query = "SELECT COUNT(*) FROM deployment_event"
        cursor.execute(count_query)
        initial_count = cursor.fetchone()[0]

        # Prepare data for insertion
        values = []
        for event in events:
            values.append((
                event.get('created_at'),
                event.get('event_type'),
                event.get('target_iid', ''),  # build_name (pipeline name)
                event.get('repo_name', '').lower() if event.get('repo_name') else '',
                event.get('branch_name', ''),
                event.get('commit_sha', ''),
                event.get('comment', ''),
                event.get('environment', ''),  # Empty
                None,  # is_major_release
                ''  # release_version
            ))

        # Insert deployment events
        insert_query = """
        INSERT INTO deployment_event (
            timestamp_utc, event, build_name, repo, source_branch, build_id,
            comment, environment, is_major_release, release_version
        ) VALUES %s
        ON CONFLICT ON CONSTRAINT deployment_event_hash_unique DO NOTHING
        """

        execute_values(cursor, insert_query, values, template=None)

        # Get final count
        cursor.execute(count_query)
        final_count = cursor.fetchone()[0]

        inserted_count = final_count - initial_count
        duplicate_count = len(events) - inserted_count

        return inserted_count, duplicate_count

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

        # Set up configuration
        self.base_url = config.get('base_url') or config.get('GITLAB_ACTIONS_API_URL', '')
        # Normalize base URL
        if self.base_url:
            self.base_url = self.base_url.strip().rstrip('/')
            if self.base_url.endswith('/api/v4'):
                self.base_url = self.base_url[:-7]
            if not self.base_url.startswith(('http://', 'https://')):
                self.base_url = f"https://{self.base_url}"

        self.api_token = config.get('api_token') or config.get('GITLAB_ACTIONS_API_TOKEN')

        # Parse group/namespace
        self.group = config.get('group') or config.get('GITLAB_ACTIONS_PROJECT', '')
        if self.group:
            self.group = str(self.group).strip()

        # Parse repositories
        repos_config = config.get('repos') or config.get('GITLAB_ACTIONS_REPOS', '')
        if isinstance(repos_config, list):
            self.repos = [str(x).strip() for x in repos_config if str(x).strip()]
        elif isinstance(repos_config, str):
            repos_config = repos_config.strip()
            if repos_config:
                try:
                    parsed = json.loads(repos_config)
                    if isinstance(parsed, list):
                        self.repos = [str(x).strip() for x in parsed if str(x).strip()]
                    else:
                        self.repos = [x.strip() for x in repos_config.split(',') if x.strip()]
                except (json.JSONDecodeError, TypeError):
                    self.repos = [x.strip() for x in repos_config.split(',') if x.strip()]
            else:
                self.repos = []
        else:
            self.repos = []

        # Validate configuration
        if not self.base_url:
            logger.error("Missing required configuration: Organization (Base URL)")
            sys.exit(1)

        if not self.group:
            logger.error("Missing required configuration: Projects (Group)")
            sys.exit(1)

        if not self.repos:
            logger.error("No repositories configured")
            sys.exit(1)

        # Set up headers
        self.headers = {
            'PRIVATE-TOKEN': self.api_token,
            'Content-Type': 'application/json'
        }

        # Determine start date
        if start_date:
            try:
                start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
                if start_date_dt.tzinfo is not None:
                    start_date_dt = start_date_dt.astimezone(timezone.utc).replace(tzinfo=None)
                else:
                    start_date_dt = start_date_dt.replace(tzinfo=None)
            except ValueError:
                logger.error("Invalid date format. Please use YYYY-MM-DD format.")
                sys.exit(1)
        else:
            if last_modified:
                if last_modified.tzinfo is not None:
                    last_modified = last_modified.replace(tzinfo=None)
                start_date_dt = last_modified
            else:
                start_date_dt = datetime(2024, 1, 1)

        # Set up save function
        if cursor:
            # Database mode
            def save_build_fn(events):
                if events:
                    total, inserted, duplicates = self.save_events_to_database(events, cursor)
                    self.stats['total_inserted'] += inserted
                    self.stats['total_duplicates'] += duplicates
                    return total, inserted, duplicates
                return 0, 0, 0

            def save_deployment_fn(events):
                if events:
                    inserted, duplicates = self.save_deployment_events(events, cursor)
                    self.stats['deployment_events_inserted'] += inserted
                    self.stats['deployment_events_duplicates'] += duplicates
                    return inserted, duplicates
                return 0, 0
        else:
            # CSV mode - create CSV files lazily
            build_csv_file = Utils.create_csv_file("gitlab_actions_build_events", export_path, logger)
            deploy_csv_file = None

            def save_build_fn(events):
                nonlocal max_timestamp
                if events:
                    result = Utils.save_events_to_csv(events, build_csv_file, logger)
                    # Track maximum timestamp for checkpoint
                    if len(result) == 4 and result[3]:
                        if not max_timestamp or result[3] > max_timestamp:
                            max_timestamp = result[3]

                    inserted = result[0] if len(result) > 0 else len(events)
                    duplicates = result[1] if len(result) > 1 else 0
                    self.stats['total_inserted'] += inserted
                    self.stats['total_duplicates'] += duplicates
                    return len(events), inserted, duplicates
                return 0, 0, 0

            def save_deployment_fn(events):
                nonlocal deploy_csv_file, max_timestamp
                if events:
                    if not deploy_csv_file:
                        deploy_csv_file = Utils.create_csv_file("gitlab_actions_deployment_events", export_path, logger)

                    # Convert to CSV format
                    deploy_events_csv = []
                    for event in events:
                        created_at = event.get('created_at')
                        if created_at:
                            deploy_event_dict = {
                                'timestamp_utc': created_at,
                                'event': event.get('event_type'),
                                'build_name': event.get('target_iid', ''),
                                'repo': event.get('repo_name', '').lower() if event.get('repo_name') else '',
                                'source_branch': event.get('branch_name', ''),
                                'comment': event.get('comment', ''),
                                'environment': event.get('environment', ''),
                                'is_major_release': None,
                                'release_version': '',
                                'build_id': event.get('commit_sha', '')
                            }
                            deploy_events_csv.append(deploy_event_dict)

                            # Track max timestamp
                            if created_at and (not max_timestamp or created_at > max_timestamp):
                                max_timestamp = created_at

                    if deploy_events_csv:
                        result = Utils.save_events_to_csv(deploy_events_csv, deploy_csv_file, logger)
                        inserted = result[0] if len(result) > 0 else len(deploy_events_csv)
                        duplicates = result[1] if len(result) > 1 else 0
                        self.stats['deployment_events_inserted'] += inserted
                        self.stats['deployment_events_duplicates'] += duplicates
                        return inserted, duplicates
                return 0, 0

        # Log the fetch information
        logger.info(f"Starting extraction from {start_date_dt}")
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"Group/Namespace: {self.group}")
        logger.info(f"Repositories: {', '.join(self.repos)}")

        # Process repositories
        all_build_events, all_deployment_events = self.process_repositories(start_date_dt)
        logger.info(f"Processed {len(all_build_events)} build events, {len(all_deployment_events)} deployment events")

        # Save build events
        total_build_events = 0
        build_inserted_count = 0
        build_duplicate_count = 0

        if all_build_events:
            # Filter events by start_date and save
            filtered_build_events = []
            for event in all_build_events:
                event_dt = event.get('timestamp_utc')
                if event_dt:
                    if event_dt.tzinfo is not None:
                        event_dt = event_dt.astimezone(timezone.utc).replace(tzinfo=None)
                    if event_dt > start_date_dt:
                        event['timestamp_utc'] = event_dt
                        filtered_build_events.append(event)

                        # Track max timestamp
                        if not max_timestamp or event_dt > max_timestamp:
                            max_timestamp = event_dt

            if filtered_build_events:
                total_build_events, build_inserted_count, build_duplicate_count = save_build_fn(filtered_build_events)

        # Save deployment events
        deploy_inserted_count = 0
        deploy_duplicate_count = 0

        if all_deployment_events:
            # Filter deployment events by start_date
            filtered_deploy_events = []
            for event in all_deployment_events:
                event_dt = event.get('created_at')
                if event_dt:
                    if event_dt.tzinfo is not None:
                        event_dt = event_dt.astimezone(timezone.utc).replace(tzinfo=None)
                    if event_dt > start_date_dt:
                        event['created_at'] = event_dt
                        filtered_deploy_events.append(event)

                        # Track max timestamp
                        if not max_timestamp or event_dt > max_timestamp:
                            max_timestamp = event_dt

            if filtered_deploy_events:
                deploy_inserted_count, deploy_duplicate_count = save_deployment_fn(filtered_deploy_events)

        # Save checkpoint in CSV mode
        if not cursor and max_timestamp:
            if Utils.save_checkpoint(prefix="gitlab_actions", last_dt=max_timestamp, export_path=export_path):
                logger.info(f"Checkpoint saved successfully: {max_timestamp}")
            else:
                logger.warning("Failed to save checkpoint")

        # Print summary
        logger.info(f"Build Events:              {self.stats['build_events']:>6}")
        logger.info(f"Build Inserted:            {build_inserted_count:>6}")
        logger.info(f"Build Duplicates:          {build_duplicate_count:>6}")
        logger.info(f"Deployment Events:         {self.stats['deployment_events']:>6}")
        logger.info(f"Deploy Inserted:           {deploy_inserted_count:>6}")
        logger.info(f"Deploy Duplicates:         {deploy_duplicate_count:>6}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Extract GitLab CI build events.")
    parser.add_argument('-p', '--product', help='Product name (if provided, saves to database; otherwise saves to CSV)')
    parser.add_argument('-s', '--start-date', help='Start date (YYYY-MM-DD)')

    args = parser.parse_args()

    extractor = GitLabActionsExtractor()

    if args.product is None:
        # CSV Mode: Load configuration from config.json
        config = json.load(open(os.path.join(common_dir, "config.json")))

        # Build config dictionary
        repos_str = config.get("GITLAB_ACTIONS_REPOS", '')
        repos_list = [repo.strip() for repo in repos_str.split(",") if repo.strip()]

        # Get base URL from config
        gitlab_api_url = config.get('GITLAB_ACTIONS_API_URL', 'https://gitlab.com/api/v4')
        base_url = gitlab_api_url.rstrip('/')
        if base_url.endswith('/api/v4'):
            base_url = base_url[:-7]
        if not base_url.startswith(('http://', 'https://')):
            base_url = f"https://{base_url}"

        config = {
            'base_url': base_url,
            'api_token': config.get('GITLAB_ACTIONS_API_TOKEN'),
            'group': config.get('GITLAB_ACTIONS_PROJECT'),
            'repos': repos_list
        }

        # Use checkpoint file for last modified date
        last_modified = Utils.load_checkpoint("gitlab_actions")

        extractor.run_extraction(None, config, args.start_date, last_modified)

    else:
        # Database Mode: Connect to the database
        from database import DatabaseConnection
        db = DatabaseConnection()
        try:
            with db.product_scope(args.product) as conn:
                with conn.cursor() as cursor:
                    config = extractor.get_config_from_database(cursor)
                    last_modified = extractor.get_last_modified_date(cursor)
                    extractor.run_extraction(cursor, config, args.start_date, last_modified)
        except Exception as e:
            logger.error(f"Error during extraction: {str(e)}")
            return 1

    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
