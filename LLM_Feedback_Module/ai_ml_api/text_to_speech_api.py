import requests

class TextToSpeechAPI:
    def __init__(self, api_key):
        self.api_key = api_key

    def convert_text_to_audio(self, text):
        url = "https://api.aimlapi.com/tts"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": "#g1_aura-asteria-en", "text": text}
        response = requests.post(url, json=payload, headers=headers)
        return response.content
