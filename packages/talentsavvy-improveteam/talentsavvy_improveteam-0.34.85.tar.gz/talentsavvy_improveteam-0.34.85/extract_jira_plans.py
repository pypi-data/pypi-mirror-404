#!/usr/bin/env python3
"""
Jira Teams Extraction Script

This script extracts team information from Jira Plans (Advanced Roadmaps)
and saves to database or CSV files.

Usage:
    python extract_jira_plan.py [-p <product_name>]

Arguments:
    -p, --product: Product name (if provided, saves to database; otherwise saves to CSV)
"""

import requests
import base64
import json
import sys
import os
import argparse
import time
from typing import Dict, List

# Setup paths
base_dir = os.path.dirname(os.path.abspath(__file__))
common_dir = os.path.join(base_dir, "common")
if not os.path.isdir(common_dir):
    base_dir = os.path.dirname(base_dir)
    common_dir = os.path.join(base_dir, "common")

if os.path.isdir(common_dir) and base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import logging
from common.utils import Utils

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger('extract_jira_plan')


class TeamExtractor:
    """Extracts team information from Jira Plans."""

    def get_config_from_database(self, cursor):
        """Get Jira configuration from data_source_config table."""
        query = """
        SELECT config_item, config_value
        FROM data_source_config
        WHERE data_source = 'work_item_management'
        AND config_item IN ('Organization', 'User Email Address', 'Personal Access Token')
        """
        cursor.execute(query)
        results = cursor.fetchall()

        config = {}
        for row in results:
            config_item, config_value = row
            if config_item == 'Organization':
                config['jira_api_url'] = f"https://{config_value}.atlassian.net"
            elif config_item == 'User Email Address':
                config['jira_user_email'] = config_value
            elif config_item == 'Personal Access Token':
                config['jira_api_token'] = config_value

        return config

    def save_teams_to_database(self, teams, cursor):
        """Save teams to database with UPSERT logic."""
        if not teams:
            return 0, 0

        # Get product_id from session
        cursor.execute("SELECT current_setting('pa.product_id', true)")
        product_id_result = cursor.fetchone()

        if not product_id_result or product_id_result[0] is None:
            logger.error("product_id not set in session configuration")
            return 0, 0

        product_id = int(product_id_result[0])

        for team in teams:
            cursor.execute(
                """
                INSERT INTO team (
                    product_id, team_id, team_name, team_type, sprint_length,
                    capacity, plan_id, plan_name, planning_style, capacity_unit,
                    scheduling, member_ids
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (product_id, team_id, plan_id)
                DO UPDATE SET
                    team_name = EXCLUDED.team_name,
                    team_type = EXCLUDED.team_type,
                    sprint_length = EXCLUDED.sprint_length,
                    capacity = EXCLUDED.capacity,
                    plan_name = EXCLUDED.plan_name,
                    planning_style = EXCLUDED.planning_style,
                    capacity_unit = EXCLUDED.capacity_unit,
                    scheduling = EXCLUDED.scheduling,
                    member_ids = EXCLUDED.member_ids
                """,
                (
                    product_id,
                    team.get("team_id"),
                    team.get("team_name"),
                    team.get("team_type"),
                    team.get("sprint_length"),
                    team.get("capacity"),
                    team.get("plan_id"),
                    team.get("plan_name"),
                    team.get("planning_style"),
                    team.get("capacity_unit"),
                    team.get("scheduling") or None,
                    team.get("member_ids") or None
                )
            )

        total_processed = len(teams)
        logger.info(f"Processed {total_processed} teams with UPSERT")
        return total_processed, 0

    def run_extraction(self, cursor, config, export_path=None):
        """Run team extraction."""
        # Validate config
        required = ['jira_api_url', 'jira_user_email', 'jira_api_token']
        for key in required:
            if not config.get(key):
                logger.error(f"Missing required configuration: {key}")
                return 1

        api_url = config['jira_api_url']
        headers = get_jira_auth_headers(config['jira_user_email'], config['jira_api_token'])

        logger.info(f"Starting Jira Teams extraction from {api_url}")

        # Setup save function
        if cursor:
            def save_fn(teams):
                result = self.save_teams_to_database(teams, cursor)
                cursor.connection.commit()
                return result
        else:
            csv_file = Utils.create_csv_file("jira_teams", export_path, logger)
            def save_fn(teams):
                return Utils.save_events_to_csv(teams, csv_file, logger)[1:3]

        # Fetch and process plans
        plans = fetch_all_plans(api_url, headers)
        if not plans:
            logger.warning("No plans found")
            return 0

        logger.info(f"Found {len(plans)} plans, extracting teams...")
        all_teams = []
        total_save_errors = 0

        for plan in plans:
            plan_id = plan.get('id')
            if not plan_id:
                continue

            plan_name = plan.get('name', '')
            logger.info(f"Processing plan: {plan_name} (ID: {plan_id})")

            # Get scheduling data from plan details
            plan_details = fetch_plan_details(api_url, plan_id, headers)
            scheduling_data = plan_details.get('scheduling', {}) if plan_details else {}

            # Get teams and process them
            teams = fetch_teams_for_plan(api_url, plan_id, headers)
            for team in teams:
                team_row = process_team_row(team, plan_id, plan_name, scheduling_data)
                all_teams.append(team_row)

        # Save teams with error checking
        if all_teams:
            saved_count, error_count = save_fn(all_teams)
            total_save_errors += error_count

            if saved_count > 0:
                logger.info(f"Successfully saved {saved_count} teams")
            if total_save_errors > 0:
                logger.error(f"Failed to save {total_save_errors} teams")
                return 1

        logger.info("=== Teams Extraction Complete ===")
        return 0


# ============================================================================
# API FUNCTIONS
# ============================================================================

def get_jira_auth_headers(email: str, api_token: str) -> Dict:
    """Return headers for Jira API authentication."""
    auth_str = f"{email}:{api_token}"
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {base64_auth}"
    }


def make_api_request(url: str, headers: Dict, params: Dict = None, max_retries: int = 3):
    """Make API request with retry logic and rate limit handling."""
    logger.info(f"[API REQUEST] URL: {url}")

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                return response
            elif response.status_code == 403:
                if 'X-RateLimit-Reset' in response.headers:
                    reset_time = int(response.headers['X-RateLimit-Reset'])
                    wait_time = max(0, reset_time - int(time.time()) + 10)
                    logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
            elif response.status_code == 400:
                logger.warning(f"Bad request: {response.status_code} - {response.text}")
                return None

            logger.warning(f"Request failed: {response.status_code}")
            if attempt < max_retries - 1:
                time.sleep(1 * (2 ** attempt))
                continue
            return None

        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1 * (2 ** attempt))
                continue
            return None

    return None


def fetch_all_plans(api_url: str, headers: Dict) -> List[Dict]:
    """Fetch all plans from Jira."""
    all_plans = []
    cursor = None

    while True:
        url = f"{api_url}/rest/api/3/plans/plan"
        params = {"maxResults": 50, "includeArchived": "true"}
        if cursor:
            params["cursor"] = cursor

        response = make_api_request(url, headers, params)
        if not response:
            break

        data = response.json()
        plans = data.get('values', [])
        if not plans:
            break

        all_plans.extend(plans)

        if data.get('isLast', True):
            break
        cursor = data.get('cursor')
        if not cursor:
            break

    logger.info(f"Fetched {len(all_plans)} plans")
    return all_plans


def fetch_plan_details(api_url: str, plan_id: str, headers: Dict) -> Dict:
    """Fetch plan details."""
    url = f"{api_url}/rest/api/3/plans/plan/{plan_id}"
    response = make_api_request(url, headers)
    return response.json() if response else None


def fetch_team_list_for_plan(api_url: str, plan_id: str, headers: Dict) -> List[Dict]:
    """Fetch team list for a plan."""
    url = f"{api_url}/rest/api/3/plans/plan/{plan_id}/team"
    response = make_api_request(url, headers)
    if not response:
        return []

    data = response.json()
    teams = data.get('values', [])
    logger.info(f"Plan {plan_id}: Found {len(teams)} teams")
    return teams


def fetch_team_details(api_url: str, plan_id: str, team_ref: Dict, headers: Dict) -> Dict:
    """Fetch detailed team information."""
    team_type_raw = team_ref.get('type')
    team_type = str(team_type_raw).lower() if team_type_raw is not None else ''
    team_id = str(team_ref.get('id') or '')

    # Determine which endpoint to use and the correct team type
    if team_type == 'atlassian':
        url = f"{api_url}/rest/api/3/plans/plan/{plan_id}/team/atlassian/{team_id}"
        actual_team_type = 'atlassianTeam'
    elif team_type == 'planonly':
        url = f"{api_url}/rest/api/3/plans/plan/{plan_id}/team/planonly/{team_id}"
        actual_team_type = 'planOnlyTeam'
    else:
        # Fallback detection based on team_id format
        if '-' in team_id and len(team_id) > 30:
            url = f"{api_url}/rest/api/3/plans/plan/{plan_id}/team/atlassian/{team_id}"
            actual_team_type = 'atlassianTeam'
        else:
            url = f"{api_url}/rest/api/3/plans/plan/{plan_id}/team/planonly/{team_id}"
            actual_team_type = 'planOnlyTeam'

    response = make_api_request(url, headers)
    if not response:
        return None

    team_details = response.json()
    team_details['_team_type'] = actual_team_type
    team_details['_team_id'] = team_id
    return team_details


def fetch_teams_for_plan(api_url: str, plan_id: str, headers: Dict) -> List[Dict]:
    """Fetch all teams with details for a plan."""
    team_refs = fetch_team_list_for_plan(api_url, plan_id, headers)
    teams = []

    for team_ref in team_refs:
        team_details = fetch_team_details(api_url, plan_id, team_ref, headers)
        if team_details:
            teams.append(team_details)

    return teams


def process_team_row(team: Dict, plan_id: str, plan_name: str, scheduling_data: Dict = None) -> Dict:
    """Process team data into database row format."""
    def to_json(obj):
        return json.dumps(obj, ensure_ascii=False) if obj else ''

    team_type = team.get('_team_type', 'unknown')
    team_id = team.get('_team_id', '')

    scheduling_data = scheduling_data or {}

    return {
        'product_id': None,  # Will be set by trigger
        'team_id': team_id,
        'team_name': team.get('name') or '',
        'team_type': team_type,
        'sprint_length': str(team.get('sprintLength') or ''),
        'capacity': str(team.get('capacity') or ''),
        'plan_id': plan_id,
        'plan_name': plan_name,
        'planning_style': team.get('planningStyle') or '',
        'capacity_unit': scheduling_data.get('estimation') or '',
        'scheduling': to_json(scheduling_data),
        'member_ids': to_json(team.get('memberAccountIds') or [])
    }


def main():
    parser = argparse.ArgumentParser(description="Extract Jira Teams data to database or CSV.")
    parser.add_argument('-p', '--product', type=str, help='Product name (if provided, saves to database; otherwise saves to CSV)')

    args = parser.parse_args()
    extractor = TeamExtractor()

    if args.product is None:
        # CSV Mode
        config_data = json.load(open(os.path.join(common_dir, "config.json")))

        # Validate required config
        jira_org = config_data.get('JIRA_ORGANIZATION')
        if not jira_org:
            logger.error("Missing required configuration: JIRA_ORGANIZATION")
            return 1

        jira_config = {
            'jira_api_url': f"https://{jira_org}.atlassian.net",
            'jira_user_email': config_data.get('JIRA_USER_EMAIL'),
            'jira_api_token': config_data.get('JIRA_API_TOKEN')
        }
        export_path = config_data.get('EXPORT_PATH')
        exit_code = extractor.run_extraction(None, jira_config, export_path)
    else:
        # Database Mode
        from database import DatabaseConnection
        db = DatabaseConnection()

        with db.product_scope(args.product) as conn:
            with conn.cursor() as cursor:
                config = extractor.get_config_from_database(cursor)
                exit_code = extractor.run_extraction(cursor, config)

    return exit_code


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
