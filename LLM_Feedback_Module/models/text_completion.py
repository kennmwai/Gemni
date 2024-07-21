from ai_ml_api.text_completion_api import TextCompletionAPI
from utils.config import get_api_key


class TextCompletion:
    def __init__(self):
        self.api_key = get_api_key()
        self.api = TextCompletionAPI(self.api_key)

    def generate_response(self, prompt, model="mistralai/Mistral-7B-Instruct-v0.2"):
        response = self.api.generate_response(prompt)
        return response


# Example usage
if __name__ == "__main__":
    text_completion = TextCompletion()
    prompt = "Explain why the sky is blue."
    response = text_completion.generate_response(prompt)
    print(f"Generated Response: {response}")
