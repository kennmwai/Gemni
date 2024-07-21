from openai import OpenAI

class TextCompletionAPI:
    def __init__(self, api_key):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.aimlapi.com",
        )

    def generate_response(self, prompt):
        response = self.client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            messages=[
                {"role": "system", "content": "You are an AI assistant who knows everything."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
