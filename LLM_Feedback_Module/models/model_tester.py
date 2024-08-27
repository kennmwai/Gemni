import json
from model_selector_v2 import ModelSelector


class ModelTester:
    def __init__(self, model_selector: ModelSelector, test_file: str):
        """
        Initializes the ModelTester with a ModelSelector instance and the path to the test data file.

        Args:
        - model_selector (ModelSelector): An instance of the ModelSelector class.
        - test_file (str): The path to the JSON file containing the test questions and answers.
        """
        self.model_selector = model_selector
        self.test_file = test_file
        self.test_data = self.load_test_data()

    def load_test_data(self) -> dict:
        """
        Loads test data from a JSON file.

        Returns:
        - dict: A dictionary containing the test questions and correct answers.
        """
        try:
            with open(self.test_file, "r") as file:
                return json.load(file)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading test data: {e}")
            return {"questions": []}

    def evaluate_model(self, model: str) -> dict:
        """
        Evaluates a model's performance on the test data.

        Args:
        - model (str): The name of the model to evaluate.

        Returns:
        - dict: A dictionary with the total number of questions and the number of correct answers.
        """
        correct_count = 0
        total_count = len(self.test_data["questions"])

        for item in self.test_data["questions"]:
            question = item["question"]
            correct_answer = item["correct_answer"]
            choices = item["choices"]

            # Get model response
            response = self.get_model_response(model, question, choices)

            # Check if the model's response is the correct answer
            if response == correct_answer:
                correct_count += 1

        accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0
        return {"total": total_count, "correct": correct_count, "accuracy": accuracy}

    def get_model_response(self, model: str, question: str, choices: list) -> str:
        """
        Gets a model's response to a question with multiple choices.

        Args:
        - model (str): The name of the model to use.
        - question (str): The question to ask the model.
        - choices (list): A list of possible answers.

        Returns:
        - str: The model's response.
        """
        prompt = f"{question}\nChoices: {', '.join(choices)}\nAnswer:"
        response = self.model_selector._get_model_response(
            model, prompt, system_prompt=""
        )
        return response.strip()

    def test_models(self, models: list) -> None:
        """
        Tests multiple models and prints their accuracy.

        Args:
        - models (list): A list of model names to test.
        """
        for model in models:
            result = self.evaluate_model(model)
            print(f"Model: {model}")
            print(f"Total Questions: {result['total']}")
            print(f"Correct Answers: {result['correct']}")
            print(f"Accuracy: {result['accuracy']:.2f}%\n")


# Example usage
if __name__ == "__main__":
    base_url = "https://api.aimlapi.com"
    test_file = "test_data.json"

    model_selector = ModelSelector(base_url)
    model_tester = ModelTester(model_selector, test_file)

    models = ["model_1", "model_2"]  # Replace with actual model names
    model_tester.test_models(models)
