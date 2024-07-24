import requests
import base64


class ImageGenerationAPI:

    def __init__(self, api_key):
        self.api_key = api_key

    def generate_image(self, prompt, model):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "prompt": prompt,
            "model": model
        }
        response = requests.post("https://api.aimlapi.com/images/generations",
                                 headers=headers,
                                 json=payload)
        image_base64 = response.json()["output"]["choices"][0]["image_base64"]
        image_data = base64.b64decode(image_base64)
        return image_data
