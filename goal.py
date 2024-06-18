import sys
import requests

def fetch_project_name(project_id, api_token):
    base_url = f"https://api.virtuoso.qa/api/projects/{project_id}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(base_url, headers=headers)

        if response.status_code == 200:
            project_data = response.json()
            project_name = project_data.get('item', {}).get('name')
            print(project_name)
        else:
            print(f"Failed to fetch project details from {base_url}. Status code: {response.status_code}")
            return None

    except requests.RequestException as e:
        print(f"Error fetching project details from {base_url}: {e}")
        return None


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
        # Send GET request to the API endpoint with API token in headers
        response = requests.get(base_url, params=params, headers=headers)

        # Check if request was successful (status code 200)
        if response.status_code == 200:
            data = response.json()  # Parse JSON response

            total_count = 0
            projectId = None

            # Iterate over each item in the JSON response
            for key, value in data.items():
                if 'journey' in value and 'tags' in value['journey']:
                    tags = value['journey']['tags']
                    for tag in tags:
                        if 'projectId' in tag:
                            projectId = tag['projectId']
                if 'journey' in value and 'id' in value['journey']:
                    total_count += 1

            # Print the projectId and total journey count

            print(f"Project ID: {projectId}")
            print(f"Total Journey Count: {total_count}")
            return projectId
        elif response.status_code == 401:
            print("Authentication failed with status code 401. Please check your API token.")

        else:
            print(f"Failed to fetch data from {base_url}. Status code: {response.status_code}")

    except requests.RequestException as e:
        print(f"Error fetching data from {base_url}: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python goal.py <goal_id> <api_token>")
        sys.exit(1)

    goal_id = sys.argv[1]
    api_token = "7b604933-1eae-43d1-93a1-c2593f6c498b"

    project_id=count_journeys(goal_id, api_token)
    fetch_project_name(project_id,api_token)
