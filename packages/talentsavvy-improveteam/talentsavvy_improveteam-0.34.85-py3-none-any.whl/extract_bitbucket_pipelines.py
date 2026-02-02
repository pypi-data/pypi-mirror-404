#!/usr/bin/env python3
"""
BitBucket Pipelines Data Extraction Script

This script extracts pipeline events from BitBucket and inserts them directly into the database.
It follows the same structure as extract_jira.py but uses BitBucket REST API.

Usage:
    python extract_bitbucket_pipelines.py -p <product_name> [-s <start_date>]
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional
from urllib.parse import urljoin

base_dir = os.path.dirname(os.path.abspath(__file__))
common_dir = os.path.join(base_dir, "common")
if not os.path.isdir(common_dir):
    # go up one level to find "common" (for installed package structure)
    base_dir = os.path.dirname(base_dir)
    common_dir = os.path.join(base_dir, "common")

if os.path.isdir(common_dir) and base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import requests

from common.utils import Utils

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('bitbucket_pipelines_extractor')


class BitbucketPipelinesExtractor:
    """Extracts build and deployment events from BitBucket pipelines."""

    def __init__(self):
        # Statistics
        self.stats = {
            'build_events_inserted': 0,
            'build_events_duplicates': 0,
            'deployment_events_inserted': 0,
            'deployment_events_duplicates': 0
        }

    def get_config_from_database(self, cursor) -> Dict:
        """Get BitBucket Pipelines configuration from database."""
        query = """
        SELECT config_item, config_value
        FROM data_source_config
        WHERE data_source = 'integration_and_build'
        AND config_item IN ('Workspace', 'Personal Access Token', 'Repos', 'Build Stage Pattern')
        """
        cursor.execute(query)
        results = cursor.fetchall()

        config = {}
        for row in results:
            config_item, config_value = row
            if config_item == 'Repos':
                try:
                    repos = json.loads(config_value)
                    config['repos'] = repos if repos else []
                except (json.JSONDecodeError, TypeError):
                    config['repos'] = []
            elif config_item == 'Workspace':
                config['workspace'] = config_value
            elif config_item == 'Personal Access Token':
                config['api_token'] = config_value

        return config

    def get_last_modified_date(self, cursor) -> Optional[datetime]:
        """Get the last modified date from the database."""
        query = "SELECT MAX(timestamp_utc) FROM build_event"
        cursor.execute(query)
        result = cursor.fetchone()
        if result[0]:
            return result[0]
        else:
            return datetime(2024, 1, 1)

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

        if not config.get('workspace') or not config.get('api_token'):
            logger.error("Missing BitBucket workspace or token in configuration")
            sys.exit(1)

        if not config.get('repos'):
            logger.error("No repositories configured")
            sys.exit(1)

        api_url = config.get('api_url', 'https://api.bitbucket.org/2.0')
        workspace = config.get('workspace')
        api_token = config.get('api_token')
        repos = config.get('repos', [])

        # Determine start date
        if start_date:
            try:
                extraction_start_date = datetime.strptime(start_date, '%Y-%m-%d')
                # Convert to naive UTC datetime
                if extraction_start_date.tzinfo is not None:
                    extraction_start_date = extraction_start_date.astimezone(timezone.utc).replace(tzinfo=None)
            except ValueError:
                logger.error("Invalid date format. Please use YYYY-MM-DD format.")
                sys.exit(1)
        else:
            if last_modified:
                # Convert to naive datetime if timezone-aware
                if last_modified.tzinfo is not None:
                    last_modified = last_modified.replace(tzinfo=None)
                extraction_start_date = last_modified
            else:
                extraction_start_date = datetime(2024, 1, 1)

        # Set up save function
        if cursor:
            # Database mode

            def save_output_fn(events):
                if events:
                    build_inserted, build_duplicates, deploy_inserted, deploy_duplicates = save_events_to_database(events, cursor)
                    self.stats['build_events_inserted'] += build_inserted
                    self.stats['build_events_duplicates'] += build_duplicates
                    self.stats['deployment_events_inserted'] += deploy_inserted
                    self.stats['deployment_events_duplicates'] += deploy_duplicates
                    return build_inserted + deploy_inserted, build_duplicates + deploy_duplicates
                return 0, 0
        else:
            # CSV mode - create CSV files lazily
            build_csv_file = None
            deploy_csv_file = None

            build_columns = [
                'timestamp_utc', 'event', 'repo', 'source_branch',
                'workflow_name', 'build_number', 'comment', 'actor', 'build_id'
            ]
            deploy_columns = [
                'timestamp_utc', 'event', 'build_name', 'repo', 'source_branch',
                'comment', 'environment', 'is_major_release', 'release_version', 'build_id'
            ]

            def save_output_fn(events):
                nonlocal build_csv_file, deploy_csv_file

                # Separate build and deployment events
                build_events = []
                deployment_events = []

                for event in events:
                    # Convert created_at to naive UTC datetime for CSV
                    created_at = event.get('created_at')
                    if created_at:
                        if isinstance(created_at, datetime):
                            if created_at.tzinfo is not None:
                                created_at = created_at.astimezone(timezone.utc).replace(tzinfo=None)
                        else:
                            created_at = datetime.fromisoformat(str(created_at).replace('Z', '+00:00'))
                            if created_at.tzinfo is not None:
                                created_at = created_at.astimezone(timezone.utc).replace(tzinfo=None)

                        if event.get('event_type') == 'Build Deployed':
                            # Map to deployment_event CSV format
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
                            deployment_events.append(deploy_event_dict)
                        else:
                            # Map to build_event CSV format (step-level events)
                            build_event_dict = {
                                'timestamp_utc': created_at,
                                'event': event.get('event_type'),  # Step name
                                'repo': event.get('repo_name', '').lower() if event.get('repo_name') else '',
                                'source_branch': event.get('branch_name', ''),
                                'workflow_name': event.get('workflow_name', ''),
                                'build_number': event.get('target_iid', ''),
                                'comment': event.get('comment', ''),
                                'actor': event.get('author', ''),
                                'build_id': event.get('commit_sha', '')
                            }
                            build_events.append(build_event_dict)

                # Create CSV files lazily when first events arrive
                if build_events and not build_csv_file:
                    build_csv_file = Utils.create_csv_file("bitbucket_pipelines_build_events", export_path, logger)
                if deployment_events and not deploy_csv_file:
                    deploy_csv_file = Utils.create_csv_file("bitbucket_pipelines_deployment_events", export_path, logger)

                # Save build events
                build_max_ts = None
                if build_events:
                    result = Utils.save_events_to_csv(build_events, build_csv_file, logger)
                    if len(result) >= 4 and result[3]:
                        build_max_ts = result[3]

                # Save deployment events
                deploy_max_ts = None
                if deployment_events:
                    result = Utils.save_events_to_csv(deployment_events, deploy_csv_file, logger)
                    if len(result) >= 4 and result[3]:
                        deploy_max_ts = result[3]

                # Track maximum timestamp for checkpoint
                nonlocal max_timestamp
                if build_max_ts and (not max_timestamp or build_max_ts > max_timestamp):
                    max_timestamp = build_max_ts
                if deploy_max_ts and (not max_timestamp or deploy_max_ts > max_timestamp):
                    max_timestamp = deploy_max_ts

                total_inserted = len(build_events) + len(deployment_events)
                return total_inserted, 0  # Return inserted and duplicates

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
                            logger.info(f"Loaded build event regex pattern: {build_event_pattern}")
                        except re.error as e:
                            logger.warning(f"Invalid build event regex pattern: {build_event_pattern}, error: {e}")
                            build_event_regex = None
            except Exception as e:
                logger.warning(f"Failed to read build stage pattern from data_source_config: {e}")
                build_event_regex = None

        # Log the fetch information
        logger.info(f"Starting extraction from {extraction_start_date}")
        logger.info(f"Fetching data from {api_url}")

        # Process repositories
        all_events = []
        for repo_name in repos:
            logger.info(f"Processing repository: {repo_name}")

            try:
                # Fetch pipelines for this repository
                pipelines = fetch_pipelines(api_url, workspace, api_token, repo_name, extraction_start_date)
                logger.info(f"Found {len(pipelines)} pipelines for repository {repo_name}")

                if pipelines:
                    # Get environment mapping for deployments
                    environment_mapping = get_pipeline_environment_mapping(api_url, workspace, api_token, repo_name)

                    for pipeline in pipelines:
                        # Create events from pipeline steps + deployment event
                        events = create_events_from_pipeline(
                            pipeline, repo_name, environment_mapping,
                            min_timestamp=extraction_start_date,
                            api_url=api_url, workspace=workspace, api_token=api_token,
                            build_event_regex=build_event_regex
                        )
                        if events:
                            all_events.extend(events)
                            # Save events immediately
                            if cursor:
                                build_inserted, build_duplicates = save_output_fn(events)
                            else:
                                inserted, duplicates = save_output_fn(events)

            except Exception as e:
                logger.error(f"Error processing repository {repo_name}: {e}")
                continue

        # Save checkpoint in CSV mode
        if not cursor and max_timestamp:
            if Utils.save_checkpoint(prefix="bitbucket_pipelines", last_dt=max_timestamp, export_path=export_path):
                logger.info(f"Checkpoint saved successfully: {max_timestamp}")
            else:
                logger.warning("Failed to save checkpoint")

        # Print summary
        if cursor:
            total_inserted = self.stats['build_events_inserted'] + self.stats['deployment_events_inserted']
            total_duplicates = self.stats['build_events_duplicates'] + self.stats['deployment_events_duplicates']
            logger.info(f"Build Events: inserted {self.stats['build_events_inserted']}, skipped {self.stats['build_events_duplicates']} duplicates")
            logger.info(f"Deployment Events: inserted {self.stats['deployment_events_inserted']}, skipped {self.stats['deployment_events_duplicates']} duplicates")
            logger.info(f"Total: inserted {total_inserted} events, skipped {total_duplicates} duplicates")
        else:
            logger.info(f"Total events processed: {len(all_events)}")


def fetch_pipelines(api_url: str, workspace: str, api_token: str, repo: str, start_date: datetime) -> List[Dict]:
    """Fetch pipelines for a specific repository since start_date."""
    url = f"{api_url}/repositories/{workspace}/{repo}/pipelines/"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    all_pipelines = []
    page = 1

    try:
        while True:
            params = {
                'pagelen': 50,
                'page': page,
                'sort': '-created_on'
            }

            # Retry logic for failed requests
            max_retries = 3
            retry_delay = 1  # seconds

            for attempt in range(max_retries):
                try:
                    logger.info(f"Fetching pipelines from: {url}?page={page}")
                    response = requests.get(url, headers=headers, params=params, timeout=30)

                    if response.status_code == 200:
                        data = response.json()
                        # Check if data is a dict with expected structure
                        if isinstance(data, dict) and 'values' in data:
                            pipelines = data.get('values', [])
                            if not pipelines:
                                break
                        else:
                            logger.warning(f"Unexpected response format for pipelines in {repo}: {data}")
                            break
                        break
                    elif response.status_code == 429:
                        # Rate limit exceeded
                        if 'Retry-After' in response.headers:
                            wait_time = int(response.headers['Retry-After'])
                            logging.warning(f"Rate limit exceeded. Waiting {wait_time} seconds...")
                            time.sleep(wait_time)
                            continue
                        else:
                            logging.warning("Rate limit exceeded for pipelines")
                            break
                    else:
                        logging.warning(f"Failed to fetch pipelines for {repo}: {response.status_code} - {response.text}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                            continue
                        else:
                            break

                except requests.exceptions.RequestException as e:
                    logging.warning(f"Request failed for pipelines in {repo} (attempt {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                        continue
                    else:
                        break
                except Exception as ex:
                    logging.error(f"Error fetching pipelines for {repo}: {ex}")
                    break
            else:
                break

            # Filter pipelines since start_date
            filtered_pipelines = []
            for pipeline in pipelines:
                created_on = pipeline.get('created_on')
                if created_on:
                    # Parse ISO datetime and convert to naive UTC
                    pipeline_date = datetime.fromisoformat(created_on.replace('Z', '+00:00'))
                    if pipeline_date.tzinfo is not None:
                        pipeline_date = pipeline_date.astimezone(timezone.utc).replace(tzinfo=None)
                    # Compare with naive start_date
                    if pipeline_date >= start_date:
                        pipeline['repo_name'] = repo
                        pipeline['pipeline_date'] = pipeline_date
                        filtered_pipelines.append(pipeline)
                    else:
                        # Since we're sorted by created_on desc, if we find one older than start_date, we can stop
                        logger.info(f"Reached pipelines older than {start_date}, stopping processing")
                        break

            all_pipelines.extend(filtered_pipelines)

            # Check if we've gone past the start_date (if the last filtered pipeline is older, stop)
            if filtered_pipelines and filtered_pipelines[-1]['pipeline_date'] < start_date:
                break

            # Check if this is the last page
            if len(pipelines) < params['pagelen']:
                break

            page += 1

    except requests.RequestException as e:
        logger.error(f"Error fetching pipelines for repo {repo}: {e}")
        return []

    return all_pipelines


def get_pipeline_steps(api_url: str, workspace: str, api_token: str, repo: str, pipeline_uuid: str) -> List[Dict]:
    """Get detailed steps for a specific pipeline."""
    url = f"{api_url}/repositories/{workspace}/{repo}/pipelines/{pipeline_uuid}/steps"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    try:
        logger.info(f"Fetching pipeline steps from: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        return data.get('values', [])

    except requests.RequestException as e:
        logger.error(f"Error fetching pipeline steps for {pipeline_uuid}: {e}")
        return []


def get_pipeline_environment_mapping(api_url: str, workspace: str, api_token: str, repo: str) -> Dict:
    """Get pipeline to environment mapping for deployments."""
    url = f"{api_url}/repositories/{workspace}/{repo}/deployments/"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    pipeline_to_env = {}

    try:
        page = 1
        while True:
            params = {'pagelen': 100, 'page': page}
            logger.info(f"Fetching deployments from: {url}?page={page}")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            deployments = data.get('values', [])

            if not deployments:
                break

            for deployment in deployments:
                release = deployment.get('release', {})
                pipeline = release.get('pipeline', {})
                environment = deployment.get('environment', {})

                pipeline_uuid = pipeline.get('uuid', '')
                environment_uuid = environment.get('uuid', '')

                if pipeline_uuid and environment_uuid:
                    # Get environment name
                    env_url = f"{api_url}/repositories/{workspace}/{repo}/environments/{environment_uuid}"
                    logger.info(f"Fetching environment from: {env_url}")
                    env_response = requests.get(env_url, headers=headers, timeout=30)
                    if env_response.status_code == 200:
                        env_data = env_response.json()
                        env_name = env_data.get('name', '')
                        if env_name:
                            pipeline_to_env[pipeline_uuid] = env_name

            if len(deployments) < 100:
                break
            page += 1

    except requests.RequestException as e:
        logger.error(f"Error fetching environment mapping for repo {repo}: {e}")

    return pipeline_to_env


def create_events_from_pipeline(pipeline: Dict, repo: str, environment_mapping: Dict, min_timestamp=None, api_url: str = None, workspace: str = None, api_token: str = None, build_event_regex=None) -> List[Dict]:
    """Create SDLC events from a BitBucket pipeline by fetching its steps.
    
    Args:
        pipeline: Pipeline data
        repo: Repository name
        environment_mapping: Mapping of pipeline UUIDs to environments
        min_timestamp: Optional minimum timestamp to filter events
        api_url: BitBucket API URL
        workspace: BitBucket workspace
        api_token: BitBucket API token
        build_event_regex: Optional compiled regex pattern for matching build stage names
    """
    events = []

    pipeline_uuid = pipeline.get('uuid', '')
    pipeline_date = pipeline.get('pipeline_date')
    state = pipeline.get('state', {}).get('name', 'UNKNOWN')
    build_number = pipeline.get('build_number', 0)

    # Get environment from mapping
    environment = environment_mapping.get(pipeline_uuid, '')

    # Get branch and commit from pipeline.target
    target = pipeline.get('target', {})
    source_branch = target.get('ref_name', '')
    commit_hash = target.get('commit', {}).get('hash', '')

    # Get actor from pipeline creator
    creator = pipeline.get('creator', {})
    actor = creator.get('display_name') or creator.get('username') or ''

    # Get trigger type as workflow_name (leave empty/null)
    trigger_name = ''  # Empty workflow name as requested

    # Check pipeline's completed_on BEFORE fetching steps (expensive API call)
    pipeline_completed_on = pipeline.get('completed_on')
    if pipeline_completed_on:
        try:
            pipeline_dt = datetime.fromisoformat(str(pipeline_completed_on).replace('Z', '+00:00'))
            if pipeline_dt.tzinfo is not None:
                pipeline_dt = pipeline_dt.astimezone(timezone.utc).replace(tzinfo=None)
            # Skip pipelines not completed since last extraction
            if min_timestamp and pipeline_dt <= min_timestamp:
                return events  # Return empty list, no need to fetch steps
        except (ValueError, TypeError):
            pass

    # Fetch steps for this pipeline and create build events from steps
    if api_url and workspace and api_token and pipeline_uuid:
        steps = get_pipeline_steps(api_url, workspace, api_token, repo, pipeline_uuid)

        # Track deduplication: (repo, workflow_name, build_number) combinations that have already matched
        build_created_repo_workflow_build_numbers = set()

        for step in steps:
            # Get step name (required) - this goes in 'event' column
            step_name = step.get('name')
            if not step_name:
                continue

            # Get timestamp: MUST have completed_on (only include completed steps)
            completed_on = step.get('completed_on')
            if not completed_on:
                continue  # Skip steps that haven't completed

            # Convert completed_on to naive UTC datetime
            try:
                timestamp_utc = datetime.fromisoformat(str(completed_on).replace('Z', '+00:00'))
                if timestamp_utc.tzinfo is not None:
                    timestamp_utc = timestamp_utc.astimezone(timezone.utc).replace(tzinfo=None)
            except (ValueError, TypeError):
                continue

            # Get step data for comment JSON
            step_uuid = step.get('uuid')
            step_state = step.get('state', {})
            state_name = step_state.get('name')  # PENDING, IN_PROGRESS, COMPLETED
            result = step_state.get('result', {})
            result_name = result.get('name')  # SUCCESSFUL, FAILED
            started_on = step.get('started_on')

            # Build comment as JSON with useful metadata
            comment_data = {
                'pipeline_uuid': pipeline_uuid,
                'step_uuid': step_uuid,
                'state': state_name,
                'result': result_name,
                'started_on': started_on
            }
            comment = json.dumps(comment_data)

            # Determine event name based on build stage pattern matching
            event_type = step_name  # Default to step name
            
            # Check if step name matches build event pattern
            if build_event_regex and step_name:
                if build_event_regex.search(step_name):
                    # Create unique key for this (repo, workflow_name, build_number) combination
                    repo_lower = (repo or '').lower()
                    repo_workflow_build_key = (repo_lower, trigger_name, str(build_number))
                    
                    # Only create "Build Created" or "Build Failed" event if we haven't already created one for this (repo, workflow_name, build_number)
                    if repo_workflow_build_key not in build_created_repo_workflow_build_numbers:
                        if result_name == 'SUCCESSFUL':
                            event_type = 'Build Created'
                            build_created_repo_workflow_build_numbers.add(repo_workflow_build_key)
                        elif result_name == 'FAILED':
                            event_type = 'Build Failed'
                            build_created_repo_workflow_build_numbers.add(repo_workflow_build_key)
                        # For other results (STOPPED, etc.), keep step_name as event
                        # Note: We don't add to the set for other results, so a later matching step with success/failure can still create an event

            step_event = {
                'data_source': 'integration_and_build',
                'event_type': event_type,  # Event name (may be "Build Created", "Build Failed", or step_name)
                'created_at': timestamp_utc,
                'author': actor,
                'target_iid': str(build_number),  # Pipeline build number
                'repo_name': repo,
                'branch_name': source_branch,
                'commit_sha': commit_hash,
                'comment': comment,
                'workflow_name': trigger_name
            }
            events.append(step_event)

    # Also create deployment event if pipeline is completed (existing logic)
    # Convert pipeline_date to naive UTC datetime
    if pipeline_date:
        if isinstance(pipeline_date, datetime):
            if pipeline_date.tzinfo is not None:
                pipeline_date = pipeline_date.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            pipeline_date = datetime.fromisoformat(str(pipeline_date).replace('Z', '+00:00'))
            if pipeline_date.tzinfo is not None:
                pipeline_date = pipeline_date.astimezone(timezone.utc).replace(tzinfo=None)

        # Filter: Skip deployment events before or at min_timestamp (checkpoint)
        if min_timestamp and pipeline_date <= min_timestamp:
            pass  # Skip deployment event
        elif state == 'COMPLETED':
            # Create Build Deployed event for completed pipelines
            deployed_event = {
                'data_source': 'integration_and_build',
                'event_type': 'Build Deployed',
                'created_at': pipeline_date,
                'author': actor,
                'target_iid': str(build_number),
                'repo_name': repo,
                'branch_name': source_branch,
                'commit_sha': commit_hash,
                'comment': f"Deployment of pipeline {build_number} for repository {repo}",
                'environment': environment,
                'test_result': 'SUCCESS'
            }
            events.append(deployed_event)

    return events


def save_events_to_database(events: List[Dict], cursor) -> tuple:
    """Save events to database and return counts."""
    if not events:
        return 0, 0, 0, 0  # build_inserted, build_duplicates, deploy_inserted, deploy_duplicates

    # Separate build and deployment events
    build_events = []
    deployment_events = []

    for event in events:
        if event.get('event_type') == 'Build Deployed':
            deployment_events.append(event)
        else:
            # All other events (step names) are build events
            build_events.append(event)

    build_inserted = 0
    build_duplicates = 0
    deploy_inserted = 0
    deploy_duplicates = 0

    # Insert build events
    if build_events:
        build_inserted, build_duplicates = save_build_events(build_events, cursor)
        logger.info(f"Build events: inserted {build_inserted}, skipped {build_duplicates} duplicates")

    # Insert deployment events
    if deployment_events:
        deploy_inserted, deploy_duplicates = save_deployment_events(deployment_events, cursor)
        logger.info(f"Deployment events: inserted {deploy_inserted}, skipped {deploy_duplicates} duplicates")

    return build_inserted, build_duplicates, deploy_inserted, deploy_duplicates


def save_build_events(events: List[Dict], cursor) -> tuple:
    """Save build events to build_event table."""
    if not events:
        return 0, 0

    from psycopg2.extras import execute_values

    # Get current count for duplicate detection
    count_query = "SELECT COUNT(*) FROM build_event"
    cursor.execute(count_query)
    initial_count = cursor.fetchone()[0]

    # Prepare data for insertion
    # Fields: timestamp_utc, event, repo, source_branch, build_id, build_number, comment, actor, workflow_name
    values = []
    for event in events:
        values.append((
            event.get('created_at'),
            event.get('event_type'),  # Step name
            event.get('repo_name', '').lower() if event.get('repo_name') else None,
            event.get('branch_name', ''),
            event.get('commit_sha', ''),  # build_id (SHA)
            event.get('target_iid', ''),  # build_number (pipeline number)
            event.get('comment', ''),  # JSON with step details
            event.get('author', ''),
            event.get('workflow_name', '')  # trigger type
        ))

    # Insert build events
    insert_query = """
    INSERT INTO build_event (
        timestamp_utc, event, repo, source_branch, build_id, build_number,
        comment, actor, workflow_name
    ) VALUES %s
    ON CONFLICT ON CONSTRAINT build_event_hash_unique DO NOTHING
    """

    execute_values(cursor, insert_query, values, template=None)

    # Get final count
    cursor.execute(count_query)
    final_count = cursor.fetchone()[0]

    inserted_count = final_count - initial_count
    duplicate_count = len(events) - inserted_count

    return inserted_count, duplicate_count


def save_deployment_events(events: List[Dict], cursor) -> tuple:
    """Save deployment events to deployment_event table."""
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
            event.get('target_iid', ''),  # build_name
            event.get('repo_name', '').lower() if event.get('repo_name') else '',
            event.get('branch_name', ''),
            event.get('commit_sha', ''),
            event.get('comment', ''),
            event.get('environment', ''),
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


def process_repositories(config: Dict, start_date: datetime, cursor) -> tuple:
    """Process all configured repositories and extract pipeline events."""
    api_url = config.get('api_url', 'https://api.bitbucket.org/2.0')
    workspace = config.get('workspace')
    api_token = config.get('api_token')
    configured_repos = config.get('repos', [])

    if not workspace or not api_token:
        logger.error("Missing BitBucket workspace or token in configuration")
        return [], 0

    all_events = []

    # If specific repos are configured, use those; otherwise fetch all repos
    if configured_repos:
        repo_names = configured_repos
    else:
        logger.info("No specific repositories configured, fetching all repositories...")
        # For now, we'll require repos to be configured
        logger.error("BitBucket Pipelines requires specific repositories to be configured")
        return [], 0

    logger.info(f"Processing {len(repo_names)} repositories...")

    for repo in repo_names:
        logger.info(f"Processing repository: {repo}")

        # Fetch pipelines for this repository
        pipelines = fetch_pipelines(api_url, workspace, api_token, repo, start_date)
        logger.info(f"Found {len(pipelines)} pipelines for repository {repo}")

        if pipelines:
            # Get environment mapping for deployments
            environment_mapping = get_pipeline_environment_mapping(api_url, workspace, api_token, repo)

            for pipeline in pipelines:
                # Create events from pipeline
                events = create_events_from_pipeline(pipeline, repo, environment_mapping)
                all_events.extend(events)

    return all_events, 0  # No cherry-pick events for BitBucket Pipelines


def main():
    """Main function to run BitBucket Pipelines extraction."""
    parser = argparse.ArgumentParser(description="Extract BitBucket Pipelines events")
    parser.add_argument('-p', '--product', help="Product name (if provided, saves to database; otherwise saves to CSV)")
    parser.add_argument('-s', '--start-date', help="Start date (YYYY-MM-DD format)")
    args = parser.parse_args()

    extractor = BitbucketPipelinesExtractor()

    if args.product is None:
        # CSV Mode: Load configuration from config.json
        config = json.load(open(os.path.join(common_dir, "config.json")))

        # Get configuration from config dictionary
        repos_str = config.get("BITBUCKET_REPOS", '')
        repos_list = [repo.strip() for repo in repos_str.split(",") if repo.strip()]

        config = {
            'workspace': config.get('BITBUCKET_WORKSPACE_ID'),
            'api_token': config.get('BITBUCKET_API_TOKEN'),
            'api_url': config.get('BITBUCKET_API_URL', 'https://api.bitbucket.org/2.0'),
            'repos': repos_list
        }

        # Use checkpoint file for last modified date
        last_modified = Utils.load_checkpoint("bitbucket_pipelines")

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


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
