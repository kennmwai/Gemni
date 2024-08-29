import json
import logging
import re
import pathlib
import concurrent.futures
from typing import Dict, List, Optional, Union
from model_selector import ModelSelector

TEMP_FILE = "data/cache.json"
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
        """
        self.model_selector = model_selector
        self.test_file = test_file
        self.cache_file = cache_file
        self.test_data = self.load_test_data()
        self.cache = self.load_cache()
        self.test_sets: Dict[str, List[Dict]] = {}

    def _read_json_file(self, file_path: str, default_value: dict) -> dict:
        """
        Reads JSON data from a file, checking if the file exists, and handles errors.
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
        """
        return self._read_json_file(self.test_file, {"questions": []})

    def load_cache(self) -> Dict[str, str]:
        """
        Loads cached responses from a JSON file.
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
        Gets a model's response to a question, with or without multiple choices.
        """
        cache_key = f"{model}:{question}"

        if cache_key in self.cache:
            logging.info(f"Cache hit for model {model} and question: {question}")
            return self.cache[cache_key]

        if choices:
            prompt = (
                f"Question: {question}\n"
                f"Choices: {', '.join(choices)}\n"
                f"Please select the best answer from the choices above.\n"
                f"Answer:"
            )
        else:
            prompt = (
                f"Question: {question}\n"
                f"Please provide a concise answer.\n"
                f"Answer:"
            )

        try:
            response = self.model_selector._get_model_response(
                model, prompt, system_prompt=""
            )
            parsed_response = self.parse_model_response(response, choices)

            self.cache[cache_key] = parsed_response
            self.save_cache()
            return parsed_response
        except Exception as e:
            logging.error(f"Error getting response from model {model}: {e}")
            return "Error"

    def parse_model_response(self, response: str, choices: List[str]) -> str:
        """
        Parses the response from the model to extract the answer.
        """
        response = response.strip().lower()

        if choices:
            choices_str = ", ".join(choice.lower() for choice in choices)
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
        else:
            # For questions without choices, return the full response
            return response

    def evaluate_model(self, model: str) -> Dict:
        """
        Evaluates a model's performance on the test data.
        """
        correct_count = 0
        total_count = len(self.test_data["questions"])

        for item in self.test_data["questions"]:
            question = item["question"]
            correct_answer = item["correct_answer"]
            choices = item.get("choices", [])

            try:
                if choices:
                    response = self.get_model_response(model, question, choices)
                else:
                    # For questions without choices (e.g., short answer questions)
                    response = self.get_model_response(model, question, [])

                # Compare the response to the correct answer
                if response.strip().lower() == correct_answer.lower():
                    correct_count += 1
            except Exception as e:
                logging.error(f"Error evaluating model on question '{question}': {e}")

        accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0
        return {
            "model": model,
            "total": total_count,
            "correct": correct_count,
            "accuracy": accuracy,
        }

    def evaluate_models(self, models: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Evaluates a list of models and returns their accuracy.
        """
        if models is None:
            models = list(self.model_selector.get_available_models().keys())

        results = {}
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_model = {
                executor.submit(self.evaluate_model, model): model for model in models
            }
            for future in concurrent.futures.as_completed(future_to_model):
                model = future_to_model[future]
                try:
                    result = future.result()
                    results[model] = result
                except Exception as e:
                    logging.error(f"Error evaluating model {model}: {e}")
                    results[model] = {"error": str(e)}
        return results

    def test_models(self, models: List[str]) -> None:
        """
        Tests multiple models and prints their accuracy.
        """
        results = self.evaluate_models(models)
        for model, result in results.items():
            if "error" in result:
                print(f"Model: {model}")
                print(f"Error: {result['error']}")
            else:
                print(f"Model: {model}")
                print(f"Total Questions: {result['total']}")
                print(f"Correct Answers: {result['correct']}")
                print(f"Accuracy: {result['accuracy']:.2f}%\n")

    def compare_models(self, models: List[str]) -> Dict:
        """
        Compares the performance of multiple models.
        """
        results = self.evaluate_models(models)
        comparison = {
            "best_model": max(results, key=lambda x: results[x].get("accuracy", 0)),
            "worst_model": min(results, key=lambda x: results[x].get("accuracy", 0)),
            "results": results,
        }
        return comparison

    def add_test_set(self, name: str, questions: List[Dict]) -> None:
        """
        Adds a new test set to the ModelTester.
        """
        self.test_sets[name] = questions

    def select_test_set(self, name: str) -> None:
        """
        Selects a test set for use in testing.
        """
        if name in self.test_sets:
            self.test_data["questions"] = self.test_sets[name]
        else:
            raise ValueError(f"Test set '{name}' not found")

    def combine_test_sets(self, names: List[str]) -> None:
        """
        Combines multiple test sets into one.
        """
        combined = []
        for name in names:
            if name in self.test_sets:
                combined.extend(self.test_sets[name])
        self.test_data["questions"] = combined

    def save_results(self, results: Dict[str, Dict], filename: str) -> None:
        """
        Saves the results to a JSON file.
        """
        try:
            with open(filename, "w") as f:
                json.dump(results, f, indent=4)
        except IOError as e:
            logging.error(f"Error saving results to file: {e}")

    def load_results(self, filename: str) -> Dict:
        """
        Loads results from a JSON file.
        """
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logging.error(f"Error loading results from file: {e}")
            return {}

    def analyze_errors(self, model: str) -> Dict:
        """
        Analyzes the errors made by a model and categorizes them.
        """
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
    test_file = "data/test_data.json"

    model_selector = ModelSelector(base_url)
    model_tester = ModelTester(model_selector, test_file)

    # Use _select_models to dynamically get model names
    num_models = 2
    model_selection_method = "random"  # Can be "random" or "manual"

    # Random model selection
    selected_models = model_selector._select_models(
        num_models, model_selection_method, None
    )

    # Test the models and print their performance
    model_tester.test_models(selected_models)

    model_eval = model_tester.evaluate_model(selected_models[0])
    print("Model Evaluation Results:")
    print(json.dumps(model_eval, indent=4))

    # comparison_results = model_tester.compare_models(selected_models)
    # print("Model Comparison:")
    # print(f"Best Model: {comparison_results['best_model']}")
    # print(f"Worst Model: {comparison_results['worst_model']}")
    # print(f"Comparison Results: {json.dumps(comparison_results['results'], indent=4)}")
