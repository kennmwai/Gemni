import requests


def make_post_request(url, headers, payload):
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


# Example usage
if __name__ == "__main__":
    url = "https://api.aimlapi.com/some_endpoint"
    headers = {
        "Authorization": "Bearer YOUR_API_KEY",
        "Content-Type": "application/json"
    }
    payload = {"key1": "value1", "key2": "value2"}

    try:
        response = make_post_request(url, headers, payload)
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
