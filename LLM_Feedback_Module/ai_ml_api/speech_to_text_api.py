import requests


class SpeechToTextAPI:

    def __init__(self, api_key):
        self.api_key = api_key

    def convert_audio_to_text(self, audio_url, model):
        url = "https://api.aimlapi.com/stt"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {"model": model, "url": audio_url}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
