import re
import json
import logging
from model_selector_v2 import ModelSelector

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


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
            logging.error(f"Error loading test data: {e}")
            return {"questions": []}

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
        prompt = (
            f"Question: {question}\n"
            f"Choices: {', '.join(choices)}\n"
            f"Please select the best answer from the choices above.\n"
            f"Answer:"
        )
        try:
            response = self.model_selector._get_model_response(
                model, prompt, system_prompt=""
            )
            return self.parse_model_response(response)
        except Exception as e:
            logging.error(f"Error getting response from model {model}: {e}")
            return "Error"

    def parse_model_response(self, response: str) -> str:
        """
        Parses the response from the model to extract the answer.

        Args:
        - response (str): The raw response from the model.

        Returns:
        - str: The extracted answer.
        """
        response = response.strip().lower()
        choices_str = ", ".join(
            choice.lower() for choice in self.test_data["questions"][0]["choices"]
        )
        choice_pattern = re.compile(
            r"\b(?:"
            + "|".join(re.escape(choice) for choice in choices_str.split(", "))
            + r")\b"
        )
        matches = choice_pattern.findall(response)

        if matches:
            # Return the most frequently mentioned choice
            return max(set(matches), key=matches.count)
        else:
            logging.warning(f"No valid choice found in the response: {response}")
            return "No valid choice"

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

            try:
                response = self.get_model_response(model, question, choices)
                if response.strip().lower() == correct_answer.lower():
                    correct_count += 1
            except Exception as e:
                logging.error(f"Error evaluating model on question '{question}': {e}")

        accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0
        return {"total": total_count, "correct": correct_count, "accuracy": accuracy}

    def test_models(self, models: list) -> None:
        """
        Tests multiple models and prints their accuracy.

        Args:
        - models (list): A list of model names to test.
        """
        for model in models:
            try:
                result = self.evaluate_model(model)
                print(f"Model: {model}")
                print(f"Total Questions: {result['total']}")
                print(f"Correct Answers: {result['correct']}")
                print(f"Accuracy: {result['accuracy']:.2f}%\n")
            except Exception as e:
                logging.error(f"Error testing model {model}: {e}")


# Example usage
if __name__ == "__main__":
    base_url = "https://api.aimlapi.com"
    test_file = "test_data.json"

    model_selector = ModelSelector(base_url)
    model_tester = ModelTester(model_selector, test_file)

    models = ["model_1", "model_2"]  # Replace with actual model names
    model_tester.test_models(models)
