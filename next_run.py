import requests
import datetime


def get_next_execution_time(execution_id, api_token):
    base_url = f"https://api.virtuoso.qa/api/plans/executions/{execution_id}"

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
                timestamp_sec = timestamp_ms / 1000  # Convert milliseconds to seconds
                dt_object = datetime.datetime.fromtimestamp(timestamp_sec)

                formatted_date = dt_object.strftime('%d/%m/%Y')
                # Format time with 12-hour format and AM/PM
                formatted_time = dt_object.strftime('%I:%M %p')

                return formatted_date, formatted_time
            else:
                print("Next schedule execution time not found in API response.")
                return None

        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            return None

    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None


if __name__ == "__main__":
    execution_id = input("Enter the execution ID: ")
    api_token = "7b604933-1eae-43d1-93a1-c2593f6c498b"  # Replace with your actual API token

    date, time = get_next_execution_time(execution_id, api_token)

    if date and time:
        print(f"Next execution date: {date}")
        print(f"Next execution time: {time}")
