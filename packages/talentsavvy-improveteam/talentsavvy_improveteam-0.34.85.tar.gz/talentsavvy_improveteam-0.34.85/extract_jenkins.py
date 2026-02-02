#!/usr/bin/env python3
"""
Jenkins Data Extraction Script

This script extracts build and deployment events from Jenkins and inserts them directly into the database.
It follows the same structure as extract_jira.py but uses Jenkins REST API.

Usage:
    python extract_jenkins.py -p <product_name> [-s <start_date>]
"""

import argparse
import copy
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
logger = logging.getLogger('jenkins_extractor')

# Maximum folder depth to prevent unbounded recursion
MAX_FOLDER_DEPTH = 15

# Maximum branches per multibranch job to prevent excessive API calls
MAX_BRANCHES_PER_MULTIBRANCH = 20


class JenkinsExtractor:
    """Extracts build and deployment events from Jenkins."""

    def __init__(self):
        self.stats = {
            'build_events_inserted': 0,
            'build_events_duplicates': 0,
            'deployment_events_inserted': 0,
            'deployment_events_duplicates': 0
        }

    def get_config_from_database(self, cursor):
        """Get Jenkins configuration from database."""
        query = """
        SELECT config_item, config_value
        FROM data_source_config
        WHERE data_source = 'integration_and_build'
        AND config_item IN ('URL', 'User', 'Personal Access Token', 'Jobs', 'Folders')
        """
        cursor.execute(query)
        results = cursor.fetchall()

        config = {}
        for row in results:
            config_item, config_value = row
            if config_item == 'Jobs':
                try:
                    jobs = json.loads(config_value)
                    config['jobs'] = jobs if jobs else []
                except (json.JSONDecodeError, TypeError):
                    config['jobs'] = []
            elif config_item == 'Folders':
                # Parse comma-separated folder names
                if config_value:
                    folders = [f.strip() for f in config_value.split(',') if f.strip()]
                    config['folders'] = folders
                else:
                    config['folders'] = []
            elif config_item == 'URL':
                # For Jenkins, URL is the base URL
                base_url = config_value.rstrip('/')
                if not base_url.startswith(('http://', 'https://')):
                    config['jenkins_url'] = f"http://{base_url}"
                else:
                    config['jenkins_url'] = base_url
            elif config_item == 'User':
                config['jenkins_user'] = config_value
            elif config_item == 'Personal Access Token':
                config['jenkins_token'] = config_value

        # Ensure folders key exists (default to empty list if not in DB)
        if 'folders' not in config:
            config['folders'] = []

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

        # Validate configuration
        if not config.get('jenkins_url') or not config.get('jenkins_token'):
            logger.error("Missing Jenkins URL or token in configuration")
            sys.exit(1)

        jenkins_url = config.get('jenkins_url')
        jenkins_user = config.get('jenkins_user', 'admin')
        jenkins_token = config.get('jenkins_token')
        configured_jobs = config.get('jobs', [])
        configured_folders = config.get('folders', [])

        # Determine start date
        if start_date:
            try:
                extraction_start_date = datetime.strptime(start_date, '%Y-%m-%d')
                # Convert to naive UTC datetime
                if extraction_start_date.tzinfo is not None:
                    extraction_start_date = extraction_start_date.astimezone(timezone.utc).replace(tzinfo=None)
                # Convert to timezone-aware for fetch_builds_for_job
                extraction_start_date_tz = extraction_start_date.replace(tzinfo=timezone.utc)
            except ValueError:
                logger.error("Invalid date format. Please use YYYY-MM-DD format.")
                sys.exit(1)
        else:
            if last_modified:
                # Convert to naive datetime if timezone-aware
                if last_modified.tzinfo is not None:
                    last_modified = last_modified.replace(tzinfo=None)
                extraction_start_date = last_modified
                # Convert to timezone-aware for fetch_builds_for_job
                extraction_start_date_tz = extraction_start_date.replace(tzinfo=timezone.utc)
            else:
                extraction_start_date = datetime(2024, 1, 1)
                extraction_start_date_tz = extraction_start_date.replace(tzinfo=timezone.utc)

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

            def save_output_fn(events):
                nonlocal build_csv_file, deploy_csv_file, max_timestamp

                # Separate build and deployment events
                build_events = []
                deployment_events = []

                for event in events:
                    event_type = event.get('event_type', '')
                    
                    if event_type == 'Deployed':
                        # Convert created_at to naive UTC datetime for CSV
                        created_at = event.get('created_at')
                        if created_at:
                            if isinstance(created_at, datetime):
                                if created_at.tzinfo is not None:
                                    created_at = created_at.astimezone(timezone.utc).replace(tzinfo=None)
                            else:
                                created_at = Utils.convert_to_utc(str(created_at))

                            # Map to deployment_event CSV format
                            deploy_event_dict = {
                                'timestamp_utc': created_at,
                                'event': event_type,
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
                        # All other events are build events (stage/job names)
                        created_at = event.get('created_at')
                        if created_at:
                            if isinstance(created_at, datetime):
                                if created_at.tzinfo is not None:
                                    created_at = created_at.astimezone(timezone.utc).replace(tzinfo=None)
                            else:
                                created_at = Utils.convert_to_utc(str(created_at))

                            # Map to build_event CSV format
                            build_event_dict = {
                                'timestamp_utc': created_at,
                                'event': event_type,  # Stage/job name
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
                    build_csv_file = Utils.create_csv_file("jenkins_build_events", export_path, logger)
                if deployment_events and not deploy_csv_file:
                    deploy_csv_file = Utils.create_csv_file("jenkins_deployment_events", export_path, logger)

                # Save build events
                build_max_ts = None
                if build_events:
                    result = Utils.save_events_to_csv(build_events, build_csv_file, logger)
                    if len(result) > 3 and result[3]:
                        build_max_ts = result[3]

                # Save deployment events
                deploy_max_ts = None
                if deployment_events:
                    result = Utils.save_events_to_csv(deployment_events, deploy_csv_file, logger)
                    if len(result) > 3 and result[3]:
                        deploy_max_ts = result[3]

                # Track maximum timestamp for checkpoint
                if build_max_ts and (not max_timestamp or build_max_ts > max_timestamp):
                    max_timestamp = build_max_ts
                if deploy_max_ts and (not max_timestamp or deploy_max_ts > max_timestamp):
                    max_timestamp = deploy_max_ts

                total_inserted = len(build_events) + len(deployment_events)
                return total_inserted, 0  # Return inserted and duplicates

        # Log the fetch information
        logger.info(f"Starting extraction from {extraction_start_date}")
        logger.info(f"Fetching data from {jenkins_url}")

        # Process jobs
        if configured_jobs:
            job_names = configured_jobs
            jobs_data = []  # No jobs_data when using configured jobs
        elif configured_folders:
            logger.info(f"Fetching jobs from folders: {configured_folders}")
            jobs_data = fetch_jobs(jenkins_url, jenkins_user, jenkins_token, allowed_folders=configured_folders)
            # Use full_path for API calls, but keep jobs_data for name access
            job_names = [job.get('full_path', job.get('name', '')) for job in jobs_data if job.get('name')]
        else:
            logger.info("No specific jobs or folders configured, fetching all jobs...")
            jobs_data = fetch_jobs(jenkins_url, jenkins_user, jenkins_token)
            # Use full_path for API calls, but keep jobs_data for name access
            job_names = [job.get('full_path', job.get('name', '')) for job in jobs_data if job.get('name')]

        logger.info(f"Processing {len(job_names)} jobs...")

        for i, job_name in enumerate(job_names):
            # Find matching job in jobs_data by full_path or name (handles filtered jobs correctly)
            matching_job = None
            for job in jobs_data:
                if job.get('full_path', job.get('name', '')) == job_name:
                    matching_job = job
                    break
            # Use short name for logging if available, otherwise full path
            display_name = matching_job.get('name', job_name) if matching_job else job_name
            logger.info(f"Processing job: {display_name} (path: {job_name})")

            try:
                # Fetch builds for this job
                builds = fetch_builds_for_job(jenkins_url, jenkins_user, jenkins_token, job_name, extraction_start_date_tz)
                logger.info(f"Found {len(builds)} builds for job {job_name}")

                for build in builds:
                    build_number = build.get('number', 0)
                    
                    # Get detailed build information
                    build_details = get_build_details(jenkins_url, jenkins_user, jenkins_token,
                                                    job_name, build_number)

                    if build_details:
                        # Extract Git information (returns list of git_info dicts)
                        git_infos = extract_git_info(build_details)

                        # Fallback to EnvironmentAction if no repos found or missing data
                        if not git_infos or (not any(g.get('commit_sha') for g in git_infos) and not any(g.get('repo_name') for g in git_infos)):
                            env_git_infos = extract_git_info_from_env(build_details)
                            
                            # Merge env info into git_infos (fill missing fields)
                            if env_git_infos:
                                env_git_info = env_git_infos[0]
                                for git_info in git_infos:
                                    for key in ('commit_sha', 'branch_name', 'repo_name'):
                                        if not git_info.get(key) and env_git_info.get(key):
                                            git_info[key] = env_git_info[key]
                                
                                # If still no valid git_infos, use env_git_info as fallback
                                if not any(g.get('repo_name') or g.get('commit_sha') for g in git_infos):
                                    git_infos = env_git_infos

                        # Mark inferred repo for each git_info
                        for git_info in git_infos:
                            git_info['repo_inferred'] = not bool(git_info.get('repo_name'))
                        
                        # Extract actor from build_details (since lightweight fetch doesn't include actions)
                        actor = ''
                        actions = build_details.get('actions', [])
                        for action in actions:
                            if not isinstance(action, dict):
                                continue
                            if action.get('_class') == 'hudson.model.CauseAction':
                                causes = action.get('causes', [])
                                for cause in causes:
                                    user_name = cause.get('userName') or cause.get('shortDescription', '')
                                    if user_name:
                                        actor = user_name
                                        break
                                if actor:
                                    break
                        
                        # Add actor to build object for create_events_from_build
                        build['actor'] = actor
                        # Also add actions to build object for compatibility
                        build['actions'] = actions

                        # Fetch stages for Pipeline builds
                        stages = fetch_build_stages(jenkins_url, jenkins_user, jenkins_token,
                                                   job_name, build_number)

                        # Create events from build (with stages if available)
                        events = create_events_from_build(build, job_name, git_infos, stages)
                        if events:
                            # Save events immediately
                            save_output_fn(events)

            except Exception as e:
                logger.error(f"Error processing job {job_name}: {e}")
                continue

        # Save checkpoint in CSV mode
        if not cursor and max_timestamp:
            if Utils.save_checkpoint(prefix="jenkins", last_dt=max_timestamp, export_path=export_path):
                logger.info(f"Checkpoint saved successfully: {max_timestamp}")
            else:
                logger.warning("Failed to save checkpoint")

        # Print summary
        if cursor:
            total_inserted = self.stats['build_events_inserted'] + self.stats['deployment_events_inserted']
            total_duplicates = self.stats['build_events_duplicates'] + self.stats['deployment_events_duplicates']
            logger.info(f"Total: inserted {total_inserted} events, skipped {total_duplicates} duplicates")
        else:
            logger.info(f"Extraction completed")


def build_jenkins_job_url(base_url: str, job_path: str, suffix: str = "/api/json") -> str:
    """
    Build correct Jenkins API URL for a job path.
    
    Args:
        base_url: Jenkins base URL
        job_path: Job path (e.g., "myJob" for root, "folderA/job/folderB/job/myJob" for nested)
                 May also contain leading "job/" if from configured jobs
        suffix: API endpoint suffix (default: "/api/json")
    
    Returns:
        Complete Jenkins API URL
    """
    if job_path:
        normalized_path = job_path.strip().lstrip('/')
        
        # Strip leading "job/" ONLY if it appears to be a Jenkins URL artifact
        # (i.e., there are no further "/job/" segments in the remainder)
        # This preserves legitimate folder names like "job" (e.g., "job/job/myJob")
        # while still handling configured jobs that may have a leading "job/" prefix
        if normalized_path.startswith('job/') and '/job/' not in normalized_path[4:]:
            normalized_path = normalized_path[4:]  # Remove "job/"
        
        # Always prepend job/ to ensure correct Jenkins URL format
        path = f"job/{normalized_path}{suffix}"
    else:
        # Root level - no job path
        path = suffix.lstrip('/')
    return urljoin(f"{base_url}/", path)


def fetch_multibranch_branches(jenkins_url: str, jenkins_user: str, jenkins_token: str, parent_path: str) -> List[str]:
    """
    Fetch branch jobs from a multibranch pipeline parent.
    
    Args:
        jenkins_url: Jenkins base URL
        jenkins_user: Jenkins username
        jenkins_token: Jenkins API token
        parent_path: Path to the multibranch parent job
    
    Returns:
        List of branch job paths (e.g., ["parent/job/main", "parent/job/develop"])
    """
    url = build_jenkins_job_url(jenkins_url, parent_path, "/api/json?tree=jobs[name,_class]")
    auth = (jenkins_user, jenkins_token)
    
    try:
        response = requests.get(url, auth=auth, verify=False, timeout=30)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch branches for multibranch job {parent_path}: HTTP {response.status_code}")
            return []
        
        data = response.json()
        branches = []
        
        for job in data.get('jobs', []):
            name = job.get('name')
            if not name:
                continue
            # Build full path for branch job
            branch_path = f"{parent_path}/job/{name}"
            branches.append(branch_path)
        
        # Limit branches to prevent excessive API calls
        if len(branches) > MAX_BRANCHES_PER_MULTIBRANCH:
            logger.warning(f"Multibranch job {parent_path} has {len(branches)} branches, limiting to {MAX_BRANCHES_PER_MULTIBRANCH}")
            branches = branches[:MAX_BRANCHES_PER_MULTIBRANCH]
        
        return branches
    except Exception as e:
        logger.error(f"Error fetching branches for multibranch job {parent_path}: {e}")
        return []


def fetch_jobs(jenkins_url: str, jenkins_user: str, jenkins_token: str, path: str = "", depth: int = 0, allowed_folders: List[str] = None) -> List[Dict]:
    """
    Fetch all jobs from Jenkins, including those in folders. Recursively traverses folder structure.
    
    Args:
        allowed_folders: List of top-level folder names to include.
                        If None or empty, fetch all folders (backward compatible).
                        If specified, only recurse into matching folders at root level.
    """

    # Depth guard to prevent unbounded recursion
    if depth > MAX_FOLDER_DEPTH:
        logger.warning(f"Max folder depth ({MAX_FOLDER_DEPTH}) reached at path: {path}")
        return []
    
    # If allowed_folders is specified and we're in a nested folder, check if top-level matches
    if allowed_folders and path and depth > 0:
        # Extract top-level folder from path
        # Path format: "folderA" or "folderA/job/folderB"
        path_parts = path.split('/job/')
        top_level_folder = path_parts[0] if path_parts else path
        
        # If we're inside a folder tree, check if top-level matches
        if top_level_folder not in allowed_folders:
            # This entire subtree doesn't match - skip it
            logger.info(f"Skipping folder tree {path} (not in allowed folders)")
            return []

    # Build URL for current path (empty path = root)
    if path:
        url = build_jenkins_job_url(jenkins_url, path, "/api/json?tree=jobs[name,_class]&depth=10")
    else:
        url = urljoin(f"{jenkins_url}/", "api/json?tree=jobs[name,_class]&depth=10")

    auth = (jenkins_user, jenkins_token)

    # Retry logic for failed requests
    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching jobs from: {url}")
            response = requests.get(url, auth=auth, verify=False, timeout=30)

            if response.status_code == 200:
                data = response.json()
                # Check if data is a dict with expected structure
                if isinstance(data, dict) and 'jobs' in data:
                    jobs_data = data.get("jobs", [])
                    break
                else:
                    logging.warning(f"Unexpected response format for jobs: {data}")
                    return []
            elif response.status_code == 404:
                # 404 means folder/job doesn't exist - skip immediately, no retries
                logger.info(f"Folder not found: {path} - skipping")
                return []
            else:
                # For other errors, log status code only (no HTML)
                logging.warning(f"Failed to fetch jobs: HTTP {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    return []

        except requests.RequestException as e:
            logger.warning(f"Request failed for jobs (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                continue
            else:
                return []
        except Exception as ex:
            logger.error(f"Error fetching jobs from Jenkins: {ex}")
            return []
    else:
        return []

    # Process jobs and folders recursively
    all_jobs = []
    for item in jobs_data:
        item_class = item.get('_class', '')
        item_name = item.get('name', '')

        if not item_name:
            continue

        # Build full path for this item
        # Jenkins requires /job/ between each folder level in URLs
        if path:
            full_path = f"{path}/job/{item_name}"
        else:
            full_path = item_name

        if item_class == 'com.cloudbees.hudson.plugins.folder.Folder':
            # Check if this folder should be processed (only at root level)
            if allowed_folders and depth == 0:
                # At root level, only process folders that match
                if item_name not in allowed_folders:
                    logger.info(f"Skipping folder {item_name} (not in allowed folders)")
                    continue
            
            # Recursively get jobs from this folder
            logger.info(f"Found folder: {full_path}, recursing...")
            nested_jobs = fetch_jobs(jenkins_url, jenkins_user, jenkins_token, full_path, depth + 1, allowed_folders)
            all_jobs.extend(nested_jobs)
        elif 'WorkflowMultiBranchProject' in item_class:
            # Multibranch pipeline - fetch branch jobs
            logger.info(f"Found multibranch job: {full_path}, fetching branches...")
            branch_jobs = fetch_multibranch_branches(jenkins_url, jenkins_user, jenkins_token, full_path)
            for branch_path in branch_jobs:
                # Extract branch name from path (last segment after /job/)
                branch_name = branch_path.split('/job/')[-1] if '/job/' in branch_path else branch_path.split('/')[-1]
                all_jobs.append({
                    'name': branch_name,
                    'full_path': branch_path,
                    '_class': 'MultibranchBranchJob'
                })
        else:
            # This is an actual job - add it with both name and full_path
            job_info = {
                'name': item_name,  # Short name for display/logging
                'full_path': full_path,  # Full path for API calls
                '_class': item_class
            }
            all_jobs.append(job_info)

    return all_jobs


def fetch_builds_for_job(jenkins_url: str, jenkins_user: str, jenkins_token: str,
                       job_name: str, start_date: datetime) -> List[Dict]:
    """Fetch builds for a specific job since start_date.
    
    Uses two-phase approach:
    1. Quick check: lastBuild timestamp to skip old jobs
    2. Lightweight fetch: only number, timestamp, result (not full build data)
    """
    auth = (jenkins_user, jenkins_token)
    
    # PHASE 1: Quick check - skip jobs with no recent builds
    quick_check_url = build_jenkins_job_url(jenkins_url, job_name, "/api/json?tree=lastBuild[timestamp]")
    
    try:
        response = requests.get(quick_check_url, auth=auth, verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            last_build = data.get('lastBuild')
            if last_build:
                last_build_timestamp = last_build.get('timestamp', 0)
                if last_build_timestamp:
                    last_build_date = datetime.fromtimestamp(last_build_timestamp / 1000, tz=timezone.utc)
                    if last_build_date < start_date:
                        logger.info(f"Job {job_name} has no builds after {start_date} (last build: {last_build_date}) - skipping")
                        return []
            else:
                # No builds at all
                logger.info(f"Job {job_name} has no builds - skipping")
                return []
    except Exception as e:
        logger.warning(f"Quick check failed for {job_name}: {e}, proceeding with full fetch")
        # Continue to full fetch if quick check fails
    
    # PHASE 2: Lightweight fetch - only essential fields
    url = build_jenkins_job_url(jenkins_url, job_name, "/api/json?tree=allBuilds[number,timestamp,result]")
    
    # Retry logic for failed requests
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching builds from: {url}")
            response = requests.get(url, auth=auth, verify=False, timeout=60)  # Increased timeout
            
            if response.status_code == 200:
                data = response.json()
                # Check if data is a dict with expected structure
                if isinstance(data, dict) and 'allBuilds' in data:
                    builds_data = data.get("allBuilds", [])
                    break
                else:
                    logging.warning(f"Unexpected response format for builds in {job_name}: {data}")
                    return []
            elif response.status_code == 404:
                # 404 means job doesn't exist - skip immediately, no retries
                logger.info(f"Job not found: {job_name} - skipping")
                return []
            else:
                # For other errors, log status code only (no HTML)
                logging.warning(f"Failed to fetch builds for {job_name}: HTTP {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    return []

        except requests.RequestException as e:
            logger.warning(f"Request failed for builds in {job_name} (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                continue
            else:
                return []
        except Exception as ex:
            logger.error(f"Error fetching builds for {job_name}: {ex}")
            return []
    else:
        return []

    # Filter builds since start_date
    filtered_builds = []
    for build in builds_data:
        build_timestamp = build.get('timestamp', 0)
        build_date = datetime.fromtimestamp(build_timestamp / 1000, tz=timezone.utc)

        if build_date >= start_date:
            build['job_name'] = job_name
            build['build_date'] = build_date
            filtered_builds.append(build)

    return filtered_builds


def get_build_details(jenkins_url: str, jenkins_user: str, jenkins_token: str,
                     job_name: str, build_number: int) -> Optional[Dict]:
    """Get detailed information for a specific build."""
    url = build_jenkins_job_url(jenkins_url, job_name, f"/{build_number}/api/json?tree=actions[_class,environment[*],causes[*],remoteUrls,lastBuiltRevision[SHA1,branch[name]]],result,duration,id,building")
    auth = (jenkins_user, jenkins_token)

    # Retry logic for failed requests
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching build details from: {url}")
            response = requests.get(url, auth=auth, verify=False, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # Check if data is a dict
                if isinstance(data, dict):
                    return data
                else:
                    logging.warning(f"Unexpected response format for build details: {data}")
                    return {}
            elif response.status_code == 404:
                # 404 means build doesn't exist - skip immediately, no retries
                logger.info(f"Build not found: {job_name}#{build_number} - skipping")
                return {}
            else:
                # For other errors, log status code only (no HTML)
                logging.warning(f"Failed to fetch build details: HTTP {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    return {}

        except requests.RequestException as e:
            logger.warning(f"Request failed for build details {job_name}#{build_number} (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                continue
            else:
                return {}
        except Exception as ex:
            logger.error(f"Error fetching build details for {job_name}#{build_number}: {ex}")
            return {}
    
    return {}


def extract_repo_name_from_url(repo_url: str) -> str:
    """
    Extract repository name from various Git provider URL formats.
    Handles: GitHub, GitLab, Bitbucket, Azure DevOps, and generic Git URLs.
    
    Args:
        repo_url: Git repository URL in various formats
        
    Returns:
        Repository name (e.g., "my-repo" from "https://bitbucket.org/workspace/my-repo.git")
    """
    if not repo_url:
        return ''
    
    # Normalize URL: remove .git suffix, trailing slashes
    repo_url = repo_url.rstrip('/').replace('.git', '')
    
    # Handle SSH format: git@host:org/repo.git
    if repo_url.startswith('git@'):
        parts = repo_url.split(':')
        if len(parts) == 2:
            path = parts[1]
            # Extract repo name (last segment)
            repo_name = path.split('/')[-1]
            return repo_name
    
    # Handle HTTPS/HTTP format: https://host/org/repo
    # Remove protocol
    for protocol in ['https://', 'http://', 'git://']:
        if repo_url.startswith(protocol):
            repo_url = repo_url[len(protocol):]
            break
    
    # Split by '/' and get last meaningful segment
    parts = [p for p in repo_url.split('/') if p]
    if not parts:
        return ''
    
    # For common Git providers, repo name is typically the last segment
    # Examples:
    # - github.com/org/repo -> repo
    # - gitlab.com/group/subgroup/repo -> repo
    # - bitbucket.org/workspace/repo -> repo
    # - dev.azure.com/org/project/_git/repo -> repo
    repo_name = parts[-1]
    
    # Special handling for Azure DevOps: skip '_git' segment
    if '_git' in parts and len(parts) > 1:
        repo_name = parts[-1] if parts[-1] != '_git' else parts[-2]
    
    return repo_name


def normalize_branch_name(branch: str) -> str:
    """
    Normalize Git branch name by removing common Git prefixes.
    Preserves branch path segments (e.g., release/Jan26 stays as release/Jan26).
    
    Handles:
    - refs/heads/release/Jan26 -> release/Jan26
    - refs/remotes/origin/release/Jan26 -> release/Jan26
    - refs/remotes/release/Jan26 -> release/Jan26
    - origin/release/Jan26 -> release/Jan26
    - release/Jan26 -> release/Jan26 (no change)
    
    Args:
        branch: Raw branch name from Jenkins
        
    Returns:
        Normalized branch name (with path segments preserved)
    """
    if not branch:
        return ''
    
    branch = branch.strip()
    
    # Define prefixes in order of specificity (longest first)
    prefixes = [
        'refs/remotes/origin/',  # Most specific: refs/remotes/origin/...
        'refs/remotes/',          # Less specific: refs/remotes/...
        'refs/heads/',            # refs/heads/...
        'origin/',                # origin/...
    ]
    
    # Remove the longest matching prefix
    for prefix in prefixes:
        if branch.startswith(prefix):
            return branch[len(prefix):]
    
    # No prefix matched, return as-is
    return branch


def extract_git_info(build_details: Dict) -> List[Dict]:
    """
    Extract Git information from build details.
    Returns a list of git_info dicts, one per repository.
    Only one branch + one commit per repo (latest commit from lastBuiltRevision).
    """
    all_git_infos = []
    seen_repos = set()  # De-duplicate repos within a build

    # Look for Git information in actions
    actions = build_details.get('actions', [])
    for action in actions:
        if not isinstance(action, dict):
            continue
        if action.get('_class') == 'hudson.plugins.git.util.BuildData':
            # Extract lastBuiltRevision (latest commit used by this build)
            build_data = action.get('buildData', action)
            last_revision = build_data.get('lastBuiltRevision')
            
            if not last_revision:
                continue
            
            commit = last_revision.get('SHA1', '')
            if not commit:
                continue
            
            # Get branches from lastBuiltRevision
            branches = last_revision.get('branch', [])
            if not branches:
                continue
            
            # Take ONLY the primary branch (first one)
            branch_obj = branches[0]
            if not isinstance(branch_obj, dict):
                continue
            
            raw_branch = branch_obj.get('name', '')
            if not raw_branch:
                continue
            
            # Normalize branch name
            branch = normalize_branch_name(raw_branch)
            
            # Skip detached HEAD branches
            if not branch or branch.lower() == 'detached':
                continue
            
            # Extract repository names from remoteUrls
            remote_urls = action.get('remoteUrls', [])
            if not remote_urls:
                continue
            
            # Create one git_info per repository URL
            for repo_url in remote_urls:
                repo = extract_repo_name_from_url(repo_url)
                
                if not repo:
                    continue
                
                # De-duplicate: only one event per repo per build
                if repo in seen_repos:
                    continue
                
                seen_repos.add(repo)
                
                git_info = {
                    'commit_sha': commit,
                    'branch_name': branch,
                    'repo_name': repo,
                    'repo_inferred': False
                }
                
                all_git_infos.append(git_info)

    # If no repos found, return one empty dict for backward compatibility
    if not all_git_infos:
        return [{
            'commit_sha': '',
            'branch_name': '',
            'repo_name': '',
            'repo_inferred': False
        }]
    
    return all_git_infos


def extract_git_info_from_env(build_details: Dict) -> List[Dict]:
    """
    Extract Git info from Jenkins EnvironmentAction.
    Returns a list (typically one item) for consistency with extract_git_info.
    """
    env_git_info = {
        'commit_sha': '',
        'branch_name': '',
        'repo_name': ''
    }

    actions = build_details.get('actions', [])
    for action in actions:
        if not isinstance(action, dict):
            continue
        if action.get('_class') == 'hudson.model.EnvironmentAction':
            env = action.get('environment', {})

            # Commit SHA
            env_git_info['commit_sha'] = env.get('GIT_COMMIT', '')

            # Branch
            raw_branch = (
                env.get('BRANCH_NAME') or
                env.get('GIT_BRANCH') or
                env.get('CHANGE_BRANCH') or
                ''
            )
            env_git_info['branch_name'] = normalize_branch_name(raw_branch)

            # Repo from URL - use improved extraction
            git_url = env.get('GIT_URL', '')
            if git_url:
                env_git_info['repo_name'] = extract_repo_name_from_url(git_url)

            break

    return [env_git_info]  # Return as list for consistency


def fetch_build_stages(jenkins_url: str, jenkins_user: str, jenkins_token: str,
                       job_name: str, build_number: int) -> List[Dict]:
    """Fetch stages/steps for a Jenkins Pipeline build using wfapi."""
    url = build_jenkins_job_url(jenkins_url, job_name, f"/{build_number}/wfapi/describe")
    auth = (jenkins_user, jenkins_token)

    # Retry logic for failed requests
    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching build stages from: {url}")
            response = requests.get(url, auth=auth, verify=False, timeout=30)

            if response.status_code == 200:
                data = response.json()
                # Check if data is a dict with stages
                if isinstance(data, dict) and 'stages' in data:
                    return data.get('stages', [])
                else:
                    # Not a Pipeline build or no stages
                    return []
            elif response.status_code == 404:
                # wfapi not available (not a Pipeline build)
                return []
            else:
                logging.warning(f"Failed to fetch stages for {job_name}#{build_number}: {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                else:
                    return []

        except requests.RequestException as e:
            logger.warning(f"Request failed for stages {job_name}#{build_number} (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))
                continue
            else:
                return []
        except Exception as ex:
            logger.error(f"Error fetching stages for {job_name}#{build_number}: {ex}")
            return []

    return []


def create_events_from_build(build: Dict, job_name: str, git_infos: List[Dict], stages: List[Dict] = None) -> List[Dict]:
    """
    Create SDLC events from a Jenkins build using stages/steps.
    Creates duplicate events for each git_info (repo+commit combination).
    
    Args:
        build: Build dictionary
        job_name: Jenkins job name
        git_infos: List of git_info dicts (one per repo)
        stages: List of stage dictionaries (for Pipeline builds)
    
    Returns:
        List of event dictionaries
    """
    events = []

    build_number = build.get('number', 0)
    build_date = build.get('build_date')
    result = build.get('result', 'UNKNOWN')

    # Get actor from build cause if available (same for all events)
    actions = build.get('actions', [])
    actor = ''
    for action in actions:
        if not isinstance(action, dict):
            continue
        if action.get('_class') == 'hudson.model.CauseAction':
            causes = action.get('causes', [])
            for cause in causes:
                user_name = cause.get('userName') or cause.get('shortDescription', '')
                if user_name:
                    actor = user_name
                    break
            if actor:
                break

    # Normalize build_date once
    if build_date and build_date.tzinfo is not None:
        build_date_naive = build_date.astimezone(timezone.utc).replace(tzinfo=None)
    elif build_date:
        build_date_naive = build_date
    else:
        build_date_naive = None

    # Create events for each git_info (repo+commit combination)
    for git_info in git_infos:
        # Create Build Created event (using build completion time)
        if build_date_naive:
            build_created_event = {
                'data_source': 'integration_and_build',
                'event_type': 'Build Created',
                'created_at': build_date_naive,
                'author': actor,
                'target_iid': str(build_number),
                'repo_name': git_info.get('repo_name', ''),
                'branch_name': git_info.get('branch_name', ''),
                'commit_sha': git_info.get('commit_sha', ''),
                'comment': "",
                'workflow_name': job_name
            }
            events.append(build_created_event)

        # If stages are available (Pipeline build), create stage-level events
        if stages:
            for stage in stages:
                stage_name = stage.get('name')
                if not stage_name:
                    continue

                # Get stage completion time
                start_time_ms = stage.get('startTimeMillis', 0)
                duration_ms = stage.get('durationMillis', 0)
                
                if not start_time_ms:
                    continue
                    
                # Calculate completion time
                completion_time_ms = start_time_ms + duration_ms
                timestamp_utc = datetime.fromtimestamp(completion_time_ms / 1000, tz=timezone.utc)
                timestamp_utc = timestamp_utc.replace(tzinfo=None)

                # Get stage status
                stage_status = stage.get('status', 'UNKNOWN')

                # Build comment as JSON with useful metadata
                comment_data = {
                    'stage_id': stage.get('id'),
                    'status': stage_status,
                    'started_at': datetime.fromtimestamp(start_time_ms / 1000, tz=timezone.utc).isoformat() if start_time_ms else None,
                    'duration_ms': duration_ms,
                    'pause_duration_ms': stage.get('pauseDurationMillis', 0)
                }
                comment = json.dumps(comment_data)

                stage_event = {
                    'data_source': 'integration_and_build',
                    'event_type': stage_name,
                    'created_at': timestamp_utc,
                    'author': actor,
                    'target_iid': str(build_number),
                    'repo_name': git_info.get('repo_name', ''),
                    'branch_name': git_info.get('branch_name', ''),
                    'commit_sha': git_info.get('commit_sha', ''),
                    'comment': comment,
                    'workflow_name': job_name
                }
                events.append(stage_event)
        else:
            # No stages available (Freestyle build) - create single event with job name
            if build_date_naive:
                # Build comment as JSON with useful metadata
                comment_data = {
                    'build_id': build.get('id'),
                    'result': result,
                    'duration_ms': build.get('duration', 0),
                    'building': build.get('building', False)
                }
                comment = json.dumps(comment_data)

                build_event = {
                    'data_source': 'integration_and_build',
                    'event_type': job_name,
                    'created_at': build_date_naive,
                    'author': actor,
                    'target_iid': str(build_number),
                    'repo_name': git_info.get('repo_name', ''),
                    'branch_name': git_info.get('branch_name', ''),
                    'commit_sha': git_info.get('commit_sha', ''),
                    'comment': comment,
                    'workflow_name': ''
                }
                events.append(build_event)

        # Create Deployed event if successful (for deployment_event table)
        if result == 'SUCCESS' and build_date_naive:
            deployed_event = {
                'data_source': 'integration_and_build',
                'event_type': 'Deployed',
                'created_at': build_date_naive,
                'author': actor,
                'target_iid': str(build_number),
                'repo_name': git_info.get('repo_name', ''),
                'branch_name': git_info.get('branch_name', ''),
                'commit_sha': git_info.get('commit_sha', ''),
                'comment': f"Deployment of build #{build_number} for job {job_name}",
                'environment': '',
                'test_result': result
            }
            events.append(deployed_event)

    return events


def save_events_to_database(events: List[Dict], cursor) -> tuple:
    """Save events to database and return counts."""
    if not events:
        return 0, 0, 0, 0  # build_inserted, build_duplicates, deploy_inserted, deploy_duplicates

    # Read configuration from database (same as load_jenkins_event.py)
    build_event_pattern = None
    deploy_event_mapping = None
    build_event_regex = None
    
    try:
        # Read build stage pattern from data_source_config
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
                    build_event_pattern = build_event_pattern.replace("\\\\", "\\")
                    build_event_regex = re.compile(build_event_pattern, re.IGNORECASE)
                    logger.info(f"Loaded build event regex pattern: {build_event_pattern}")
                except re.error as e:
                    logger.warning(f"Invalid build event regex pattern: {build_event_pattern}, error: {e}")
                    build_event_regex = None
        
        # Read stage to env map from environment_mapping table
        cursor.execute("""
            SELECT stage_name, environment
            FROM environment_mapping
            WHERE stage_name IS NOT NULL AND job_name IS NULL
        """)
        result = cursor.fetchall()
        if result:
            deploy_event_mapping = {}
            for record in result:
                stage_name = record[0]
                environment = record[1]
                if stage_name and environment:
                    deploy_event_mapping[stage_name] = environment
            # If empty dict, set to None
            if not deploy_event_mapping:
                deploy_event_mapping = None
        else:
            deploy_event_mapping = None
    except Exception as e:
        logger.warning(f"Failed to read build stage pattern from data_source_config or stage to env map from environment_mapping: {e}")
        build_event_regex = None
        deploy_event_mapping = None

    # Process events: filter and add new ones (same logic as load_jenkins_event.py)
    processed_events = []
    # Track (repo, workflow_name, build_number) combinations that have already matched for build events
    build_created_repo_workflow_build_numbers = set()
    
    for event in events:
        event_type = event.get('event_type', '')
        
        # If JENKINS_BUILD_EVENT is configured, ignore existing "Build Created" events
        # We will generate new ones based on regex matching
        if build_event_regex and event_type == 'Build Created':
            # Skip this event - we'll generate new "Build Created" events based on regex
            continue
        
        # Add the event normally
        processed_events.append(event)
        
        # Check if stage name matches build event pattern
        # Only check if event_type is NOT "Build Created" (to avoid matching existing "Build Created" events)
        if build_event_regex and event_type != 'Build Created':
            stage_name = event_type
            if stage_name and build_event_regex.search(stage_name):
                # Get build_number and workflow_name explicitly from event
                build_number = event.get('target_iid', '')
                workflow_name = event.get('workflow_name', '')
                repo = (event.get('repo_name', '') or '').lower()
                # Create unique key for this (repo, workflow_name, build_number) combination
                repo_workflow_build_key = (repo, workflow_name, build_number)
                
                # Only create "Build Created" event if we haven't already created one for this (repo, workflow_name, build_number)
                # Same build_number with different repo or workflow_name can still match
                if repo_workflow_build_key not in build_created_repo_workflow_build_numbers:
                    # Create new "Build Created" event with same details
                    build_created_event = copy.deepcopy(event)
                    build_created_event['event_type'] = 'Build Created'
                    processed_events.append(build_created_event)
                    # Mark this (repo, workflow_name, build_number) as having matched
                    build_created_repo_workflow_build_numbers.add(repo_workflow_build_key)
        
        # Check if stage name matches deploy event mapping (for successful stages)
        if deploy_event_mapping and event_type != 'Deployed':
            stage_name = event_type
            if stage_name:
                # Check if stage is successful by parsing comment JSON
                stage_is_successful = False
                try:
                    comment = event.get('comment', '')
                    if comment:
                        comment_data = json.loads(comment)
                        stage_status = comment_data.get('status', '').upper()
                        # Consider SUCCESS, SUCCESSFUL, PASSED as successful
                        stage_is_successful = stage_status in ('SUCCESS', 'SUCCESSFUL', 'PASSED')
                except (json.JSONDecodeError, AttributeError, TypeError):
                    # If comment is not JSON or doesn't have status, skip
                    pass
                
                if stage_is_successful:
                    # Check stage name against mapping keys (case-insensitive)
                    stage_name_lower = stage_name.lower()
                    for key, environment in deploy_event_mapping.items():
                        if key.lower() == stage_name_lower:
                            # Create deployment event with environment
                            deploy_event = copy.deepcopy(event)
                            deploy_event['event_type'] = 'Deployed'
                            deploy_event['environment'] = environment
                            processed_events.append(deploy_event)
                            break  # Stop after first match (as per requirement)

    # Separate build and deployment events from processed_events
    build_events = []
    deployment_events = []

    for event in processed_events:
        if event.get('event_type') == 'Deployed':
            deployment_events.append(event)
        else:
            # All other events (stage/job names) are build events
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
            event.get('event_type'),  # Stage/job name
            event.get('repo_name', '').lower() if event.get('repo_name') else None,
            event.get('branch_name', ''),
            event.get('commit_sha', ''),
            event.get('target_iid', ''),
            event.get('comment', ''),
            event.get('author', ''),
            event.get('workflow_name', '')  # Job name for pipeline builds
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
            event.get('repo_name', '').lower(),
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


def process_jobs(config: Dict, start_date: datetime, cursor) -> tuple:
    """Process all configured jobs and extract events."""
    jenkins_url = config.get('jenkins_url')
    jenkins_user = config.get('jenkins_user', 'admin')
    jenkins_token = config.get('jenkins_token')
    configured_jobs = config.get('jobs', [])
    configured_folders = config.get('folders', [])

    if not jenkins_url or not jenkins_token:
        logger.error("Missing Jenkins URL or token in configuration")
        return 0, 0

    all_events = []

    # If specific jobs are configured, use those; otherwise fetch all jobs
    if configured_jobs:
        job_names = configured_jobs
        jobs_data = []  # No jobs_data when using configured jobs
    elif configured_folders:
        logger.info(f"Fetching jobs from folders: {configured_folders}")
        jobs_data = fetch_jobs(jenkins_url, jenkins_user, jenkins_token, allowed_folders=configured_folders)
        # Use full_path for API calls, but keep jobs_data for name access
        job_names = [job.get('full_path', job.get('name', '')) for job in jobs_data if job.get('name')]
    else:
        logger.info("No specific jobs or folders configured, fetching all jobs...")
        jobs_data = fetch_jobs(jenkins_url, jenkins_user, jenkins_token)
        # Use full_path for API calls, but keep jobs_data for name access
        job_names = [job.get('full_path', job.get('name', '')) for job in jobs_data if job.get('name')]

    logger.info(f"Processing {len(job_names)} jobs...")

    for i, job_name in enumerate(job_names):
        # Find matching job in jobs_data by full_path or name (handles filtered jobs correctly)
        matching_job = None
        for job in jobs_data:
            if job.get('full_path', job.get('name', '')) == job_name:
                matching_job = job
                break
        # Use short name for logging if available, otherwise full path
        display_name = matching_job.get('name', job_name) if matching_job else job_name
        logger.info(f"Processing job: {display_name} (path: {job_name})")

        # Fetch builds for this job
        builds = fetch_builds_for_job(jenkins_url, jenkins_user, jenkins_token, job_name, start_date)
        logger.info(f"Found {len(builds)} builds for job {job_name}")

        for build in builds:
            build_number = build.get('number', 0)
            
            # Get detailed build information
            build_details = get_build_details(jenkins_url, jenkins_user, jenkins_token,
                                            job_name, build_number)

            if build_details:
                # Extract Git information (returns list of git_info dicts)
                git_infos = extract_git_info(build_details)

                # Fallback to EnvironmentAction if no repos found or missing data
                if not git_infos or (not any(g.get('commit_sha') for g in git_infos) and not any(g.get('repo_name') for g in git_infos)):
                    env_git_infos = extract_git_info_from_env(build_details)
                    
                    # Merge env info into git_infos (fill missing fields)
                    if env_git_infos:
                        env_git_info = env_git_infos[0]
                        for git_info in git_infos:
                            for key in ('commit_sha', 'branch_name', 'repo_name'):
                                if not git_info.get(key) and env_git_info.get(key):
                                    git_info[key] = env_git_info[key]
                        
                        # If still no valid git_infos, use env_git_info as fallback
                        if not any(g.get('repo_name') or g.get('commit_sha') for g in git_infos):
                            git_infos = env_git_infos

                # Mark inferred repo for each git_info
                for git_info in git_infos:
                    git_info['repo_inferred'] = not bool(git_info.get('repo_name'))
                
                # Extract actor from build_details (since lightweight fetch doesn't include actions)
                actor = ''
                actions = build_details.get('actions', [])
                for action in actions:
                    if not isinstance(action, dict):
                        continue
                    if action.get('_class') == 'hudson.model.CauseAction':
                        causes = action.get('causes', [])
                        for cause in causes:
                            user_name = cause.get('userName') or cause.get('shortDescription', '')
                            if user_name:
                                actor = user_name
                                break
                        if actor:
                            break
                
                # Add actor to build object for create_events_from_build
                build['actor'] = actor
                # Also add actions to build object for compatibility
                build['actions'] = actions

                # Fetch stages for Pipeline builds
                stages = fetch_build_stages(jenkins_url, jenkins_user, jenkins_token,
                                           job_name, build_number)

                # Create events from build (with stages if available)
                events = create_events_from_build(build, job_name, git_infos, stages)
                all_events.extend(events)

    return all_events, 0  # No cherry-pick events for Jenkins


def main():
    """Main function to run Jenkins extraction."""
    parser = argparse.ArgumentParser(description="Extract Jenkins build and deployment events")
    parser.add_argument('-p', '--product', help="Product name (if provided, saves to database; otherwise saves to CSV)")
    parser.add_argument('-s', '--start-date', help="Start date (YYYY-MM-DD format)")
    args = parser.parse_args()

    extractor = JenkinsExtractor()

    if args.product is None:
        # CSV Mode: Load configuration from config.json
        config = json.load(open(os.path.join(common_dir, "config.json")))
        
        # Get configuration from config dictionary
        jobs_str = config.get("JENKINS_JOBS", '')
        jobs_list = [job.strip() for job in jobs_str.split(",") if job.strip()] if jobs_str else []
        
        folders_str = config.get("JENKINS_FOLDERS", '')
        folders_list = [folder.strip() for folder in folders_str.split(",") if folder.strip()] if folders_str else []

        config = {
            'jenkins_url': config.get('JENKINS_API_URL', 'http://localhost:8080'),
            'jenkins_user': config.get('JENKINS_USER', 'root'),
            'jenkins_token': config.get('JENKINS_API_TOKEN'),
            'jobs': jobs_list,
            'folders': folders_list
        }

        # Use checkpoint file for last modified date
        last_modified = Utils.load_checkpoint("jenkins")

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