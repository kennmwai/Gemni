import json
import random

import requests
from openai import OpenAI
from utils.config import BASE_URL, DEFAULT_SYSTEM_PROMPT, get_api_key


class ModelSelector:

    def __init__(self, base_url: str = BASE_URL):
        """
        Initializes the ModelSelector with the base URL and API key.

        Args:
        - base_url (str): The base URL of the API.
        """
        self.api_key = get_api_key()
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def get_available_models(self) -> dict:
        """
        Retrieves the available models from the API.

        Returns:
        - dict: A dictionary of available models.
        """
        try:
            response = requests.get(f"{self.base_url}/models",
                                    headers=self.headers)
            response.raise_for_status()
            return json.loads(response.text)
        except requests.RequestException as e:
            print(f"Error retrieving available models: {e}")
            return {}

    def compare_models(
        self,
        prompt: str,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        num_models: int = 2,
        model_selection: str = "random",
        selected_models: list = [],
    ) -> None:
        """
        Compares the responses of multiple models to a given prompt.

        Args:
        - prompt (str): The user prompt.
        - system_prompt (str): The system prompt.
        - num_models (int): The number of models to compare.
        - model_selection (str): The method of model selection.
                                 Can be "random" or "manual".
        - selected_models (list): A list of model names to compare.
                                 Required if model_selection is "manual".
        """
        vendor_by_model = self.get_available_models()
        models = list(vendor_by_model.keys())

        if model_selection == "random":
            random.shuffle(models)
            selected_models = models[:num_models]
        elif model_selection == "manual":
            if selected_models is None:
                raise ValueError(
                    "models must be provided for manual model selection")
            selected_models = [
                model for model in selected_models if model in models
            ]
        else:
            raise ValueError("Invalid model selection method")

        for model in selected_models:
            try:
                completion = self.client.chat.completions.create(
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
                    model=model,
                )

                if completion.choices and completion.choices[0].message:
                    message = completion.choices[0].message.content
                    self._print_model_response(model, system_prompt, prompt,
                                               message)
                else:
                    print(f"No response from model {model}")
            except Exception as e:
                print(f"Error getting response from model {model}: {e}")

    def _print_model_response(self, model: str, system_prompt: str,
                              prompt: str, response: str) -> None:
        """
        Prints the response of a model to a given prompt.

        Args:
        - model (str): The model name.
        - prompt (str): The user prompt.
        - response (str): The model response.
        """
        print(f"--- {model} ---")
        print(f"System: {system_prompt}")
        print(f"USER: {prompt}")
        print(f"AI  : {response}\n")


# Example usage
if __name__ == "__main__":
    base_url = "https://api.aimlapi.com"
    prompt = "Why is the sky blue?"

    model_selector = ModelSelector(base_url)

    model_selection_method = input(
        "Enter model selection method (random/manual): ")
    if model_selection_method == "manual":
        available_models = model_selector.get_available_models()
        print("Available models:")
        for model in available_models:
            print(model)
        selected_models = input("Enter model names (comma-separated): ").split(
            ",")
        selected_models = [model.strip() for model in selected_models]
        model_selector.compare_models(prompt,
                                      model_selection="manual",
                                      selected_models=selected_models)
    else:
        model_selector.compare_models(prompt)
