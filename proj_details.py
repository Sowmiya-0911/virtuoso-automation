import sys
import requests
import csv
import json

def count_journeys(goal_id, api_token):
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
            print("Authentication failed with status code 401. Please check your API token.")
        else:
            print(f"Failed to fetch data from {base_url}. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching data from {base_url}: {e}")
    return 0

def process_goals(team_data, api_token):
    for team in team_data:
        total_count = 0
        for project in team['projects']:
            for goal_id in project['goal_ids']:
                count = count_journeys(goal_id, api_token)
                total_count += count
        team['total_journey_count'] = total_count

def export_to_csv(team_data, output_file):
    fieldnames = ['Team Name', 'Total Journey Count']
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for team in team_data:
            writer.writerow({
                'Team Name': team['team_name'],
                'Total Journey Count': team['total_journey_count']
            })

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <team_data_file.json> <api_token>")
        sys.exit(1)

    team_data_file = sys.argv[1]
    api_token = "7b604933-1eae-43d1-93a1-c2593f6c498b"

    try:
        with open(team_data_file, 'r') as file:
            team_data = json.load(file)

        process_goals(team_data, api_token)
        export_to_csv(team_data, 'output.csv')
        print("Output saved to output.csv")

    except Exception as e:
        print(f"An error occurred: {e}")
