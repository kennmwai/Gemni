import json
import logging
import re
import pathlib
import concurrent.futures
from typing import Dict, List, Optional, Union
from model_selector_v2 import ModelSelector

TEMP_FILE = "cache.json"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


class ModelTester:
    def __init__(
        self,
        model_selector: ModelSelector,
        test_file: str,
        cache_file: str = TEMP_FILE,
    ):
        """
        Initializes the ModelTester with a ModelSelector instance, the path to the test data file, and an optional cache file.

        Args:
        - model_selector (ModelSelector): An instance of the ModelSelector class.
        - test_file (str): The path to the JSON file containing the test questions and answers.
        - cache_file (str): The path to the file where cache will be saved and loaded from.
        """
        self.model_selector = model_selector
        self.test_file = test_file
        self.cache_file = cache_file
        self.test_data = self.load_test_data()
        self.cache = self.load_cache()
        self.test_sets: Dict = {}

    def _read_json_file(self, file_path: str, default_value: dict) -> dict:
        """
        Reads JSON data from a file, checking if the file exists, and handles errors.

        Args:
        - file_path (str): The path to the JSON file.
        - default_value (dict): The default value to return in case of an error.

        Returns:
        - dict: The loaded JSON data or the default value if an error occurs.
        """
        path = pathlib.Path(file_path)

        if not path.exists():
            logging.error(f"File not found: {file_path}")
            return default_value

        try:
            with open(file_path, "r") as file:
                return json.load(file)
        except (IOError, json.JSONDecodeError) as e:
            logging.error(f"Error loading file {file_path}: {e}")
            return default_value

    def load_test_data(self) -> Dict:
        """
        Loads test data from a JSON file.

        Returns:
        - dict: A dictionary containing the test questions and correct answers.
        """
        return self._read_json_file(self.test_file, {"questions": []})

    def load_cache(self) -> Dict[str, str]:
        """
        Loads cached responses from a JSON file.

        Returns:
        - dict: A dictionary containing cached responses.
        """
        return self._read_json_file(self.cache_file, {})

    def save_cache(self) -> None:
        """
        Saves the cached responses to a JSON file.
        """
        try:
            with open(self.cache_file, "w") as file:
                json.dump(self.cache, file, indent=4)
        except IOError as e:
            logging.error(f"Error saving cache: {e}")

    def get_model_response(self, model: str, question: str, choices: List[str]) -> str:
        """
        Gets a model's response to a question with multiple choices, using cache to minimize API calls.

        Args:
        - model (str): The name of the model to use.
        - question (str): The question to ask the model.
        - choices (List[str]): A list of possible answers.

        Returns:
        - str: The model's response.
        """
        cache_key = f"{model}:{question}"

        if cache_key in self.cache:
            logging.info(f"Cache hit for model {model} and question: {question}")
            return self.cache[cache_key]

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
            parsed_response = self.parse_model_response(response)

            self.cache[cache_key] = parsed_response
            self.save_cache()
            return parsed_response
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
            return max(set(matches), key=matches.count)
        else:
            logging.warning(f"No valid choice found in the response: {response}")
            return "No valid choice"

    def evaluate_model(self, model: str) -> Dict:
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

    def test_models(self, models: List[str]) -> None:
        """
        Tests multiple models and prints their accuracy.

        Args:
        - models (List[str]): A list of model names to test.
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

    def test_models_v2(self, models: List[str]) -> Dict:
        """
        Tests multiple models using concurrent futures and returns the results.

        Args:
        - models (List[str]): A list of model names to test.

        Returns:
        - dict: A dictionary with the results of each model.
        """
        results = {}
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_model = {
                executor.submit(self.evaluate_model_v2, model): model
                for model in models
            }
            for future in concurrent.futures.as_completed(future_to_model):
                model = future_to_model[future]
                try:
                    results[model] = future.result()
                except Exception as e:
                    logging.error(f"Error testing model {model}: {e}")
                    results[model] = {"error": str(e)}
        return results

    def evaluate_model_v2(self, model: str) -> Dict:
        """
        Evaluates a model's performance on the test data with detailed results.

        Args:
        - model (str): The name of the model to evaluate.

        Returns:
        - dict: A dictionary with detailed results of the model evaluation.
        """
        results = {"total": 0, "correct": 0, "questions": []}

        for item in self.test_data["questions"]:
            question_result = self._evaluate_question(model, item)
            results["questions"].append(question_result)
            results["total"] += 1
            if question_result["correct"]:
                results["correct"] += 1

        results["accuracy"] = (
            (results["correct"] / results["total"]) * 100 if results["total"] > 0 else 0
        )
        return results

    def _evaluate_question(self, model: str, question: Dict) -> Dict:
        """
        Evaluates a single question from the test data using the specified model.

        Args:
        - model (str): The name of the model to use.
        - question (Dict[str, Union[str, List[str]]]): A dictionary containing the question, choices, and correct answer.

        Returns:
        - dict: A dictionary with the question, model's answer, correct answer, and whether the answer is correct.
        """
        response = self.get_model_response(
            model, question["question"], question["choices"]
        )
        is_correct = response.strip().lower() == question["correct_answer"].lower()
        return {
            "question": question["question"],
            "model_answer": response,
            "correct_answer": question["correct_answer"],
            "correct": is_correct,
        }

    def compare_models(self, models: List[str]) -> Dict:
        """
        Compares the performance of multiple models.

        Args:
        - models (List[str]): A list of model names to compare.

        Returns:
        - dict: A dictionary with the best and worst models and their results.
        """
        results = self.test_models_v2(models)
        comparison = {
            "best_model": max(results, key=lambda x: results[x]["accuracy"]),
            "worst_model": min(results, key=lambda x: results[x]["accuracy"]),
            "results": results,
        }
        return comparison

    def add_test_set(self, name: str, questions: List[Dict]) -> None:
        """
        Adds a new test set to the ModelTester.

        Args:
        - name (str): The name of the test set.
        - questions (List[Dict): A list of questions for the test set.
        """
        self.test_sets[name] = questions

    def select_test_set(self, name: str) -> None:
        """
        Selects a test set for use in testing.

        Args:
        - name (str): The name of the test set to select.

        Raises:
        - ValueError: If the test set name is not found.
        """
        if name in self.test_sets:
            self.test_data["questions"] = self.test_sets[name]
        else:
            raise ValueError(f"Test set '{name}' not found")

    def combine_test_sets(self, names: List[str]) -> None:
        """
        Combines multiple test sets into one.

        Args:
        - names (List[str]): A list of test set names to combine.
        """
        combined = []
        for name in names:
            if name in self.test_sets:
                combined.extend(self.test_sets[name])
        self.test_data["questions"] = combined

    def save_results(self, results: Dict, filename: str) -> None:
        """
        Saves the results to a JSON file.

        Args:
        - results (Dict[str, Dict[str, Union[int, float, str]]]): The results to save.
        - filename (str): The path to the file to save the results to.
        """
        with open(filename, "w") as f:
            json.dump(results, f, indent=4)

    def load_results(self, filename: str) -> Dict:
        """
        Loads results from a JSON file.

        Args:
        - filename (str): The path to the file to load results from.

        Returns:
        - dict: The loaded results.
        """
        with open(filename, "r") as f:
            return json.load(f)

    def analyze_errors(self, model: str) -> Dict:
        results = self.evaluate_model(model)
        error_analysis = {
            "total_errors": results["total"] - results["correct"],
            "error_rate": 100 - results["accuracy"],
            "error_categories": {},
        }

        for question in results["questions"]:
            if not question["correct"]:
                category = self._categorize_error(question)
                error_analysis["error_categories"].setdefault(category, 0)
                error_analysis["error_categories"][category] += 1

        return error_analysis

    def _categorize_error(self, question: Dict[str, Union[str, bool]]) -> str:
        """
        Categorizes errors based on the question and its characteristics.

        Args:
        - question (Dict[str, Union[str, bool]]): The question and its associated data.

        Returns:
        - str: The category of the error.
        """
        if "type" in question:
            if question["type"] == "multiple_choice":
                return "Multiple Choice Errors"
            elif question["type"] == "true_false":
                return "True/False Errors"
            elif question["type"] == "short_answer":
                return "Short Answer Errors"
            else:
                return "Other Types of Errors"

        # If no specific type is found, use a generic category
        return "Uncategorized Errors"



# Example usage
if __name__ == "__main__":
    base_url = "https://api.aimlapi.com"
    test_file = "test_data.json"

    model_selector = ModelSelector(base_url)
    model_tester = ModelTester(model_selector, test_file)

    models = ["model_1", "model_2"]  # Replace with actual model names
    model_tester.test_models(models)
