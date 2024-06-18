import requests
import datetime

def find_closest_execution(project_id, target_datetime, threshold_minutes, api_token):
    base_url = f"https://api.virtuoso.qa/api/projects/{project_id}/executions"

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(base_url, headers=headers)
        if response.status_code == 200:
            executions = response.json()['items']

            closest_execution = None
            closest_diff = float('inf')

            # Convert target_datetime to timestamp
            target_timestamp = target_datetime.timestamp()

            # Iterate over each execution to find the closest one
            for execution in executions:
                execution_timestamp = execution['submitDate'] / 1000
                time_diff = abs(execution_timestamp - target_timestamp) / 60  # Difference in minutes

                # Check if this execution is closer and within the threshold
                if time_diff <= threshold_minutes and time_diff < closest_diff:
                    closest_execution = execution
                    closest_diff = time_diff

            return closest_execution

        else:
            print(f"Failed to fetch execution data. Status code: {response.status_code}")
            return None

    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None


if __name__ == "__main__":
    project_id = 78044  # Replace with your project ID
    target_datetime = datetime.datetime(2024, 6, 15, 12, 50)  # Replace with your target date and time
    threshold_minutes = 30  # Replace with your threshold in minutes
    api_token = "7b604933-1eae-43d1-93a1-c2593f6c498b"  # Replace with your actual API token

    closest_execution = find_closest_execution(project_id, target_datetime, threshold_minutes, api_token)

    if closest_execution:
        execution_date = datetime.datetime.fromtimestamp(closest_execution['submitDate'] / 1000)
        execution_time = execution_date.strftime('%d/%m/%Y %H:%M:%S')  # Format in dd/mm/YYYY HH:MM:SS
        print(f"Closest execution time found: {execution_time}")
        print(f"Execution ID: {closest_execution['id']}")
        print(f"Total Test Cases Executed: {closest_execution['totalTests']}")
        print(f"Total Test Cases Passed: {closest_execution['totalPasses']}")
    else:
        print("No executions found within the specified threshold.")
