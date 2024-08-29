import json
import random
import os
import requests
from typing import List, Optional, Dict
from openai import OpenAI

BASE_URL = "https://api.aimlapi.com"
DEFAULT_SYSTEM_PROMPT = ("You are an AI assistant skilled in providing accurate and informative answers to questions. "
                          "Your responses should be clear, concise, and based on factual information. Avoid speculation "
                          "and ensure that each answer is well-supported by knowledge up to the current date. Always "
                          "acknowledge the user's query and address it directly.")
MODELS = "data/models.json"


def get_api_key():
    api_key = os.getenv("AIML_API_KEY", "54a34a43333f47119e47424176f69cf8")
    if not api_key:
        raise ValueError("AI/ML API KEY environment variable not set.")
    return api_key


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
        self.models: dict = {}  # Cache for models

    def get_available_models(self) -> Dict:
        """
        Retrieves the available models from the cache or API if not available in cache.

        Returns:
        - dict: A dictionary of available models.
        """
        if not self.models:  # If models are not loaded or cache is empty
            self.models = (
                self._load_models_from_file(MODELS) or self.fetch_models_from_api()
            )
        return self.models

    def fetch_models_from_api(self) -> Dict:
        """
        Fetches the available models from the API.

        Returns:
        - dict: A dictionary of available models.
        """
        try:
            response = requests.get(f"{self.base_url}/models", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error retrieving available models: {e}")
            return {}

    def save_models_to_file(self, filename: str) -> None:
        """
        Saves the available models to a JSON file.

        Args:
        - filename (str): The name of the file to save the models to.
        """
        models = self.get_available_models()
        try:
            with open(filename, "w") as file:
                json.dump(models, file, indent=4)
            print(f"Models saved to {filename}")
        except IOError as e:
            print(f"Error saving models to file: {e}")

    def _load_models_from_file(self, filename: str) -> Dict:
        """
        Loads models from a JSON file.

        Args:
        - filename (str): The name of the file to load the models from.

        Returns:
        - dict: A dictionary of models if the file exists and is readable, otherwise an empty dictionary.
        """
        if os.path.exists(filename):
            try:
                with open(filename, "r") as file:
                    return json.load(file)
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error loading models from file: {e}")
                return {}
        else:
            print(f"File {filename} does not exist.")
            return {}

    def _select_models(
        self,
        num_models: int,
        model_selection: str,
        selected_models: Optional[List[str]],
    ) -> List[str]:
        """
        Selects models based on the selection method.

        Args:
        - num_models (int): The number of models to select.
        - model_selection (str): The method of model selection.
        - selected_models (Optional[List[str]]): A list of model names to compare if manual selection is chosen.

        Returns:
        - List[str]: A list of selected model names.
        """
        models = list(self.get_available_models().keys())

        if model_selection == "random":
            if len(models) < num_models:
                num_models = len(models)
            random.shuffle(models)
            return models[:num_models]
        elif model_selection == "manual":
            if not selected_models:
                raise ValueError("Model names must be provided for manual selection")
            selected_models = [model for model in selected_models if model in models]
            if not selected_models:
                raise ValueError("None of the provided models are available")
            return selected_models
        else:
            raise ValueError("Invalid model selection method")

    def _get_model_response(self, model: str, prompt: str, system_prompt: str) -> str:
        """
        Retrieves the response from a model.

        Args:
        - model (str): The model name.
        - prompt (str): The user prompt.
        - system_prompt (str): The system prompt.

        Returns:
        - str: The model response.
        """
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                model=model,
            )
            if response.choices:
                return response.choices[0].message.get("content", "")
            else:
                return f"No response from model {model}"
        except Exception as e:
            return f"Error getting response from model {model}: {e}"

    def _print_model_response(
        self, model: str, system_prompt: str, prompt: str, response: str
    ) -> None:
        """
        Prints the response of a model to a given prompt.

        Args:
        - model (str): The model name.
        - system_prompt (str): The system prompt.
        - prompt (str): The user prompt.
        - response (str): The model response.
        """
        print(f"--- {model} ---")
        print(f"System: {system_prompt}")
        print(f"USER: {prompt}")
        print(f"AI  : {response}\n")

    def compare_models(
        self,
        prompt: str,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        num_models: int = 2,
        model_selection: str = "random",
        selected_models: Optional[List[str]] = None,
    ) -> None:
        """
        Compares the responses of multiple models to a given prompt.

        Args:
        - prompt (str): The user prompt.
        - system_prompt (str): The system prompt.
        - num_models (int): The number of models to compare.
        - model_selection (str): The method of model selection.
        - selected_models (Optional[List[str]]): A list of model names to compare if manual selection is chosen.
        """
        if selected_models is None:
            selected_models = []

        selected_models = self._select_models(
            num_models=num_models,
            model_selection=model_selection,
            selected_models=selected_models,
        )

        for model in selected_models:
            response = self._get_model_response(model, prompt, system_prompt)
            self._print_model_response(model, system_prompt, prompt, response)


# Example usage
if __name__ == "__main__":
    base_url = "https://api.aimlapi.com"
    prompt = "Why is the sky blue?"

    model_selector = ModelSelector(base_url)

    # Save available models to a file
    model_selector.save_models_to_file("models.json")

    # Get available models from the file
    available_models = model_selector.get_available_models()
    if not available_models:
        print("No available models to select.")
    else:
        print("Available models:")
        for model in available_models:
            print(model)

        # Get user input for model selection method
        model_selection_method = (
            input("Enter model selection method (random/manual): ").strip().lower()
        )

        if model_selection_method == "manual":
            selected_models_input = input("Enter model names (comma-separated): ")
            selected_models = [
                model.strip()
                for model in selected_models_input.split(",")
                if model.strip()
            ]
            if not selected_models:
                print("No valid models selected.")
            else:
                # Compare selected models' responses
                model_selector.compare_models(
                    prompt, model_selection="manual", selected_models=selected_models
                )
        elif model_selection_method == "random":
            # Compare random models' responses
            num_models = int(input("Enter number of random models to compare: "))
            model_selector.compare_models(prompt, num_models=num_models)
        else:
            print("Invalid model selection method.")
