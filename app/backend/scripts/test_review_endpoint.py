import requests
import json

url = "http://127.0.0.1:8000/api/infractions/1/review"
headers = {"Content-Type": "application/json"}
payload = {"review_decision": "CONFIRMED", "review_comments": "Placa y velocidad confirmadas."}

try:
    response = requests.put(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")
except requests.exceptions.HTTPError as errh:
    print(f"Http Error: {errh}")
    print(f"Response Body: {errh.response.json()}")
except requests.exceptions.ConnectionError as errc:
    print(f"Error Connecting: {errc}")
except requests.exceptions.Timeout as errt:
    print(f"Timeout Error: {errt}")
except requests.exceptions.RequestException as err:
    print(f"Something went wrong: {err}")
