from ai_ml_api.text_completion_api import TextCompletionAPI
from utils.config import get_api_key

class TextInference:
    def __init__(self):
        self.api_key = get_api_key()
        self.text_completion_api = TextCompletionAPI(self.api_key)

    def generate_text(self, prompt):
        return self.text_completion_api.generate_response(prompt)

# Example usage
if __name__ == "__main__":
    text_inference = TextInference()
    prompt = "Why is the sky blue?"
    response = text_inference.generate_text(prompt)
    print(f"Generated Text: {response}")
