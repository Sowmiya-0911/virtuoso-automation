import sys
import requests
import csv
import json
from datetime import datetime, timedelta

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
            print(f"Authentication failed with status code 401 for team '{team_name}' and goal ID '{goal_id}'. Please check your API token.")
        else:
            print(f"Failed to fetch data from {base_url} for team '{team_name}' and goal ID '{goal_id}'. Status code: {response.status_code}")
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
            print(f"Authentication failed with status code 401 for team '{team_name}' and planner ID '{planner_id}'. Please check your API token.")
        else:
            print(f"Failed to fetch data from {base_url} for team '{team_name}' and planner ID '{planner_id}'. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching data from {base_url} for team '{team_name}' and planner ID '{planner_id}': {e}")
    return None

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

    try:
        print(f"Fetching data with params: {params} for team '{team_name}', project ID '{project_id}', and plan ID '{plan_id}'")
        response = requests.get(base_url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()

            total_executed = 0
            total_passed = 0

            print(f"Start date (epoch ms): {dateBegin}, End date (epoch ms): {dateEnd}")
            print(f"Execution Planner ID: {plan_id}")

            # Filter out jobs based on goal ID and matching hour and minute
            filtered_jobs = {}
            target_hour = next_execution_time.hour
            target_minute = next_execution_time.minute

            for job_id, job in data.items():
                if 'submitDate' in job:
                    job_date = datetime.fromtimestamp(job['submitDate'] / 1000)
                    if job_date.hour == target_hour and job_date.minute == target_minute:
                        goal_id = job['goalId']
                        if goal_id not in filtered_jobs:
                            filtered_jobs[goal_id] = {
                                'executed': job.get('totalTestExecutions', 0),
                                'passed': job.get('successfulTestExecutions', 0)
                            }

            for goal_id, job_data in filtered_jobs.items():
                total_executed += job_data['executed']
                total_passed += job_data['passed']
                print(f"Included Goal ID: {goal_id}, Executed: {job_data['executed']}, Passed: {job_data['passed']}")

            return total_executed, total_passed
        elif response.status_code == 401:
            print(f"Authentication failed with status code 401 for team '{team_name}', project ID '{project_id}', and plan ID '{plan_id}'. Please check your API token.")
        else:
            print(f"Failed to fetch data from {base_url} for team '{team_name}', project ID '{project_id}', and plan ID '{plan_id}'. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching data from {base_url} for team '{team_name}', project ID '{project_id}', and plan ID '{plan_id}': {e}")
    return 0, 0

# Assuming the process_goals and other necessary functions are already defined
def process_goals(team_data, api_token):
    for team in team_data:
        total_journey_created = 0
        total_TC_executed = 0
        total_TC_passed = 0
        for project in team['projects']:
            for goal_id in project['goal_ids']:
                count = count_journeys(goal_id, api_token, team['team_name'])
                total_journey_created += count
            for planner_id in project['planner_id']:
                next_execution_time = next_execution_time_plannerId(planner_id, api_token, team['team_name'])
                if next_execution_time:
                    executed, passed = total_TC_executed_passed(project['project_id'], planner_id, api_token, next_execution_time, team['team_name'])
                    total_TC_executed += executed
                    total_TC_passed += passed
        team['total_journey_created'] = total_journey_created
        team['total_TC_executed'] = total_TC_executed
        team['total_TC_passed'] = total_TC_passed

def export_to_csv(team_data, output_file):
    fieldnames = ['Team Name', 'Journey Created', 'TC Executed', 'TC Passed']
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for team in team_data:
            writer.writerow({
                'Team Name': team['team_name'],
                'Journey Created': team['total_journey_created'],
                'TC Executed': team['total_TC_executed'],
                'TC Passed': team['total_TC_passed']
            })

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <team_data_file.json>")
        sys.exit(1)

    team_data_file = sys.argv[1]
    api_token = "7b604933-1eae-43d1-93a1-c2593f6c498b"

    try:
        with open(team_data_file, 'r') as file:
            team_data = json.load(file)

        process_goals(team_data, api_token)
        export_to_csv(team_data, 'result.csv')
        print("Output saved to result.csv")
    except Exception as e:
        print(f"An error occurred: {e}")
