import requests
import random
import json
from openai import OpenAI
from utils.config import get_api_key

class ModelSelector:
    def __init__(self, base_url):
        self.api_key = get_api_key()
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        self.openai = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def get_available_models(self):
        response = requests.get(f"{self.base_url}/models", headers=self.headers)
        response.raise_for_status()
        return json.loads(response.text)

    def compare_models(self, prompt, system_prompt="You are an AI assistant that only responds with jokes.", num_models=2):
        vendor_by_model = self.get_available_models()
        models = list(vendor_by_model.keys())
        random.shuffle(models)
        selected_models = models[:num_models]

        for model in selected_models:
            completion = self.openai.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                model=model,
            )
            message = completion.choices[0].message.content
            print(f"--- {model} ---")
            print(f"USER: {prompt}")
            print(f"AI  : {message}\n")

# Example usage
if __name__ == "__main__":
    base_url = "https://api.aimlapi.com"
    prompt = "Why is the sky blue?"

    model_selector = ModelSelector(base_url)
    model_selector.compare_models(prompt)
