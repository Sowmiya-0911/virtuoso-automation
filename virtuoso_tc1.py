import json
import csv
import sys
import requests


# Fetch the number of journeys for a given goal ID
def count_journeys(goal_id, api_token, team_name):
    url = f"https://api.virtuoso.qa/api/goals/{goal_id}/journeys/count"
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"Team: {team_name}, Goal ID: {goal_id}, Journeys Count: {data['count']}")
        return data['count']
    else:
        print(f"Failed to fetch journeys count for Goal ID {goal_id}, Status Code: {response.status_code}")
        return 0


# Fetch the next execution time for a given planner ID
def next_execution_time_plannerId(planner_id, api_token, team_name):
    url = f"https://api.virtuoso.qa/api/planners/{planner_id}/next_execution"
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"Team: {team_name}, Planner ID: {planner_id}, Next Execution Time: {data['next_execution']}")
        return data['next_execution']
    else:
        print(f"Failed to fetch next execution time for Planner ID {planner_id}, Status Code: {response.status_code}")
        return None


# Fetch the total executed and passed test cases for a given planner and project
def total_TC_executed_passed(project_id, planner_id, api_token, next_execution_time, team_name):
    url = f"https://api.virtuoso.qa/api/projects/{project_id}/planners/{planner_id}/executions?time={next_execution_time}"
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get(url, headers=headers)
    total_executed = 0
    total_passed = 0
    detailed_results = {}

    if response.status_code == 200:
        data = response.json()
        for job in data['jobs']:
            goal_id = job['goal_id']
            if goal_id not in detailed_results:
                detailed_results[goal_id] = {"executed": 0, "passed": 0, "failed": 0}

            executed = job['executed']
            passed = job['passed']
            failed = executed - passed

            detailed_results[goal_id]["executed"] += executed
            detailed_results[goal_id]["passed"] += passed
            detailed_results[goal_id]["failed"] += failed

            total_executed += executed
            total_passed += passed

            print(f"Included Goal ID: {goal_id}, Executed: {executed}, Passed: {passed}")

    return total_executed, total_passed, detailed_results


# Fetch the name of a planner
def fetch_planner_name(planner_id, api_token):
    url = f"https://api.virtuoso.qa/api/planners/{planner_id}/name"
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['name']
    return f"Planner {planner_id}"


# Fetch the name of a goal
def fetch_goal_name(goal_id, api_token):
    url = f"https://api.virtuoso.qa/api/goals/{goal_id}/name"
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['name']
    return f"Goal {goal_id}"


def process_goals(team_data, api_token):
    detailed_summary = {}
    for team in team_data:
        total_journey_created = 0
        total_TC_executed = 0
        total_TC_passed = 0
        detailed_summary[team['team_name']] = {}
        for project in team['projects']:
            for goal_id in project['goal_ids']:
                count = count_journeys(goal_id, api_token, team['team_name'])
                total_journey_created += count
            for planner_id in project['planner_id']:
                next_execution_time = next_execution_time_plannerId(planner_id, api_token, team['team_name'])
                if next_execution_time:
                    executed, passed, details = total_TC_executed_passed(project['project_id'], planner_id, api_token,
                                                                         next_execution_time, team['team_name'])
                    total_TC_executed += executed
                    total_TC_passed += passed
                    planner_name = fetch_planner_name(planner_id, api_token)
                    for goal_id, goal_data in details.items():
                        goal_name = fetch_goal_name(goal_id, api_token)
                        if planner_name not in detailed_summary[team['team_name']]:
                            detailed_summary[team['team_name']][planner_name] = {}
                        detailed_summary[team['team_name']][planner_name][goal_name] = {
                            "TC Executed": goal_data['executed'],
                            "TC Passed": goal_data['passed'],
                            "TC Failed": goal_data['failed']
                        }
        team['total_journey_created'] = total_journey_created
        team['total_TC_executed'] = total_TC_executed
        team['total_TC_passed'] = total_TC_passed

    return detailed_summary


def export_summary_csv(team_data, summary_file, detailed_summary_file, detailed_summary):
    # Export summary
    fieldnames = ['Team Name', 'Journey Created', 'TC Executed', 'TC Passed']
    with open(summary_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for team in team_data:
            writer.writerow({
                'Team Name': team['team_name'],
                'Journey Created': team['total_journey_created'],
                'TC Executed': team['total_TC_executed'],
                'TC Passed': team['total_TC_passed']
            })

    # Export detailed summary
    with open(detailed_summary_file, 'w', newline='') as csvfile:
        fieldnames = ['Team Name', 'Details']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for team_name, planners in detailed_summary.items():
            details_str = json.dumps(planners)
            writer.writerow({'Team Name': team_name, 'Details': details_str})


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <team_data_file.json>")
        sys.exit(1)

    team_data_file = sys.argv[1]
    api_token = "7b604933-1eae-43d1-93a1-c2593f6c498b"

    try:
        with open(team_data_file, 'r') as file:
            team_data = json.load(file)

        detailed_summary = process_goals(team_data, api_token)
        export_summary_csv(team_data, 'summary.csv', 'detailed_summary.csv', detailed_summary)
        print("Output saved to summary.csv and detailed_summary.csv")
    except Exception as e:
        print(f"An error occurred: {e}")
