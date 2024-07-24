from openai import OpenAI
from utils.config import DEFAULT_SYSTEM_PROMPT


class TextCompletionAPI:

    def __init__(self, api_key):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.aimlapi.com",
        )

    def generate_response(self,
                          prompt,
                          model,
                          system_prompt=DEFAULT_SYSTEM_PROMPT):
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                },
            ],
        )
        return response.choices[0].message.content
