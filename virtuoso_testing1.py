import sys
import requests
import csv
import json
from datetime import datetime, timedelta
import pytz


def fetch_goal_name(goal_id, api_token):
    base_url = f"https://api.virtuoso.qa/api/goals/{goal_id}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(base_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if 'item' in data and 'name' in data['item']:
                return data['item']['name']
            else:
                print(f"Goal name not found for goal ID '{goal_id}'. Response: {data}")
        else:
            print(f"Failed to fetch goal name for goal ID '{goal_id}'. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching goal name for goal ID '{goal_id}': {e}")

    return f"Goal {goal_id}"


def fetch_planner_name(planner_id, api_token):
    base_url = f"https://api.virtuoso.qa/api/plans/executions/{planner_id}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(base_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data['item'].get('name', f"Planner {planner_id}")
        else:
            print(f"Failed to fetch planner name for planner ID '{planner_id}'. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching planner name for planner ID '{planner_id}': {e}")
    return f"Planner {planner_id}"


def count_journeys(goal_id, api_token, team_name):
    base_url = "https://api.virtuoso.qa/api/testsuites/latest_status"
    params = {
        "goalId": goal_id,
        "envelope": "false"
    }
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(base_url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            total_count = 0
            for key, value in data.items():
                if 'journey' in value and 'id' in value['journey']:
                    total_count += 1
            return total_count
        elif response.status_code == 401:
            print(
                f"Authentication failed with status code 401 for team '{team_name}' and goal ID '{goal_id}'. Please check your API token.")
        else:
            print(
                f"Failed to fetch data from {base_url} for team '{team_name}' and goal ID '{goal_id}'. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching data from {base_url} for team '{team_name}' and goal ID '{goal_id}': {e}")
    return 0


def next_execution_time_plannerId(planner_id, api_token, team_name):
    base_url = f"https://api.virtuoso.qa/api/plans/executions/{planner_id}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(base_url, headers=headers)
        if response.status_code == 200:
            execution_data = response.json()
            if 'nextScheduleExecution' in execution_data['item']:
                timestamp_ms = execution_data['item']['nextScheduleExecution']
                return datetime.fromtimestamp(timestamp_ms / 1000)
        elif response.status_code == 401:
            print(
                f"Authentication failed with status code 401 for team '{team_name}' and planner ID '{planner_id}'. Please check your API token.")
        else:
            print(
                f"Failed to fetch data from {base_url} for team '{team_name}' and planner ID '{planner_id}'. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching data from {base_url} for team '{team_name}' and planner ID '{planner_id}': {e}")
    return None


def fetch_jobs(base_url, params, headers, team_name, project_id, plan_id):
    try:
        response = requests.get(base_url, params=params, headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            print(
                f"Authentication failed with status code 401 for team '{team_name}', project ID '{project_id}', and plan ID '{plan_id}'. Please check your API token.")
        else:
            print(
                f"Failed to fetch data from {base_url} for team '{team_name}', project ID '{project_id}', and plan ID '{plan_id}'. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(
            f"Error fetching data from {base_url} for team '{team_name}', project ID '{project_id}', and plan ID '{plan_id}': {e}")
    return {}


def fetch_journey_names(snapshot_id, goal_id, api_token):
    base_url = f"https://api.virtuoso.qa/api/testsuites/latest_status"
    params = {
        "snapshotId": snapshot_id,
        "goalId": goal_id,
        "envelope": "false"
    }
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    journey_names = {
        "passed": [],
        "failed": []
    }
    try:
        response = requests.get(base_url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for key, value in data.items():
                if 'journey' in value and 'title' in value['journey']:
                    outcome = value.get('lastExecution', {}).get('statistics', {}).get('outcome', '')
                    print("outcome ",outcome)
                    if outcome == 'PASS':
                        journey_names['passed'].append(value['journey']['title'])
                    elif outcome == "ERROR":
                        journey_names['failed'].append(value['journey']['title'])
        else:
            print(f"Failed to fetch journey names from {base_url}. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching journey names from {base_url}: {e}")
    return journey_names


def total_TC_executed_passed(project_id, plan_id, api_token, next_execution_time, team_name):
    previous_day = next_execution_time - timedelta(days=1)
    dateBegin = int(previous_day.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
    dateEnd = int(previous_day.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp() * 1000)

    base_url = f"https://api.virtuoso.qa/api/projects/{project_id}/jobs"
    params = {
        "dateBegin": dateBegin,
        "dateEnd": dateEnd,
        "planIds[]": plan_id,
        "envelope": "false"
    }
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    #print(f"Fetching data for team '{team_name}', project ID '{project_id}', and plan ID '{plan_id}'")

    data = fetch_jobs(base_url, params, headers, team_name, project_id, plan_id)
    if not isinstance(data, dict):
        return 0, 0, 0, {}

    total_executed = 0
    total_passed = 0
    total_failed = 0
    detailed_results = {}

    #print(f"Execution Planner ID: {plan_id}")

    filtered_jobs = {}
    for job_id, job in data.items():
        if 'submitDate' in job:
            job_date = datetime.fromtimestamp(job['submitDate'] / 1000)
            time_diff = abs(previous_day - job_date)
            goal_id = job['goalId']
            if goal_id in filtered_jobs:
                if time_diff < filtered_jobs[goal_id]['time_diff']:
                    filtered_jobs[goal_id] = {
                        'executed': job.get('totalTestExecutions', 0),
                        'passed': job.get('successfulTestExecutions', 0),
                        'failed': job.get('totalTestExecutions', 0) - job.get('successfulTestExecutions', 0),
                        'time_diff': time_diff,
                        'snapshot_id': job.get('snapshotId', None)
                    }
            else:
                filtered_jobs[goal_id] = {
                    'executed': job.get('totalTestExecutions', 0),
                    'passed': job.get('successfulTestExecutions', 0),
                    'failed': job.get('totalTestExecutions', 0) - job.get('successfulTestExecutions', 0),
                    'time_diff': time_diff,
                    'snapshot_id': job.get('snapshotId', None)
                }

    for goal_id, job_data in filtered_jobs.items():
        total_executed += job_data['executed']
        total_passed += job_data['passed']
        total_failed += job_data['failed']

        # Fetch journey names based on snapshot_id and goal_id
        if job_data['snapshot_id']:
            journey_names = fetch_journey_names(job_data['snapshot_id'], goal_id, api_token)
            detailed_results[goal_id] = {
                "executed": job_data['executed'],
                "passed": job_data['passed'],
                "failed": job_data['failed'],
                "passed_journeys": journey_names['passed'],
                "failed_journeys": journey_names['failed']
            }
        else:
            detailed_results[goal_id] = {
                "executed": job_data['executed'],
                "passed": job_data['passed'],
                "failed": job_data['failed'],
                "passed_journeys": [],
                "failed_journeys": []
            }

    #print(f"Results for team '{team_name}': Total executed: {total_executed}, Total passed: {total_passed}, Total failed: {total_failed}")
    return total_executed, total_passed, total_failed, detailed_results


def process_goals(team_data, api_token):
    detailed_summary = {}
    for team in team_data:
        total_journey_created = 0
        total_TC_executed = 0
        total_TC_passed = 0
        total_TC_failed = 0
        detailed_summary[team['team_name']] = {}
        for project in team['projects']:
            for goal_id in project['goal_ids']:
                count = count_journeys(goal_id, api_token, team['team_name'])
                total_journey_created += count
            for planner_id in project['planner_id']:
                next_execution_time = next_execution_time_plannerId(planner_id, api_token, team['team_name'])
                if next_execution_time:
                    executed, passed, failed, details = total_TC_executed_passed(project['project_id'], planner_id,
                                                                                 api_token, next_execution_time,
                                                                                 team['team_name'])
                    total_TC_executed += executed
                    total_TC_passed += passed
                    total_TC_failed += failed
                    planner_name = fetch_planner_name(planner_id, api_token)
                    for goal_id, goal_data in details.items():
                        goal_name = fetch_goal_name(goal_id, api_token)
                        detailed_summary[team['team_name']][goal_id] = {
                            "goal_name": goal_name,
                            "planner_name": planner_name,
                            "executed": executed,
                            "passed": passed,
                            "failed": failed,
                            "details": goal_data
                        }
        team['total_journey_created'] = total_journey_created
        team['total_TC_executed'] = total_TC_executed
        team['total_TC_passed'] = total_TC_passed
        team['total_TC_failed'] = total_TC_failed
    return detailed_summary


def export_summary_csv(team_data, summary_file, detailed_summary_file_path, detailed_summary):
    fieldnames = ['Team Name', 'Journey Created', 'TC Executed', 'TC Passed', 'TC Failed']
    with open(summary_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for team in team_data:
            writer.writerow({
                'Team Name': team['team_name'],
                'Journey Created': team['total_journey_created'],
                'TC Executed': team['total_TC_executed'],
                'TC Passed': team['total_TC_passed'],
                'TC Failed': team['total_TC_failed']
            })

    fieldnames = ["Team Name", "Planner Name", "Goal Name", "Total Executed",
                  "Total Passed", "Total Failed", "Passed Journey Names", "Failed Journey Names"]



    with open(detailed_summary_file_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for team_name, goals in detailed_summary.items():
            for goal_id, result in goals.items():
                writer.writerow({
                    "Team Name": team_name,
                    "Planner Name": result["planner_name"],
                    "Goal Name": result["goal_name"],
                    "Total Executed": result["executed"],
                    "Total Passed": result["passed"],
                    "Total Failed": result["failed"],
                    "Passed Journey Names": ", ".join(result["details"]["passed_journeys"]),
                    "Failed Journey Names": ", ".join(result["details"]["failed_journeys"])
                })


def main():
    team_data_file = "proj_details.json"
    api_token = "7b604933-1eae-43d1-93a1-c2593f6c498b"

    try:
        with open(team_data_file, 'r') as file:
            team_data = json.load(file)

        detailed_summary = process_goals(team_data, api_token)
        ist = pytz.timezone('Asia/Kolkata')
        current_time_ist = datetime.now(ist)
        formatted_time_ist = current_time_ist.strftime('%Y-%m-%d_%H-%M-%S')
        detailed_summary_file = f'log_{formatted_time_ist}.csv'
        export_summary_csv(team_data, 'summary-final.csv', detailed_summary_file, detailed_summary)
        print("Output saved to summary1.csv and", detailed_summary_file)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()

