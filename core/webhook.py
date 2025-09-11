import json
import requests

class WebhookError(Exception):
    pass

def send_webhook(payload: dict, url: str) -> None:
    response = requests.post(url, data=json.dumps(payload), headers={"Content-Type": "application/json"})
    if response.status_code == 200:
        pass
    else:
        raise WebhookError(f"Failed to send webhook: {response.status_code} - {response.text}")