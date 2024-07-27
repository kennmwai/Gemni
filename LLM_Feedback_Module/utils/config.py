# Configuration file for the LLM Feedback Module.
import os


def get_api_key():
    api_key = os.getenv("AIML_API_KEY")
    if not api_key:
        raise ValueError("AI/ML API KEY environment variable not set.")
    return api_key


# Ignore these as would be used later:
#
# API Keys
AI_ML_API_KEY = "YOUR_AI_ML_API_KEY_HERE"
LLM_MODEL_API_KEY = "YOUR_LLM_MODEL_API_KEY_HERE"

# Model Settings
BASE_URL = "https://api.aimlapi.com"
DEFAULT_SYSTEM_PROMPT = "You are an AI assistant that only responds with jokes."
LLM_MODEL_NAME = "llm-feedback-model"
LLM_MODEL_VERSION = "1.0.0"
LLM_MODEL_TYPE = "text-generation"

# Inference Settings
INFERENCE_BATCH_SIZE = 16
INFERENCE_MAX_LENGTH = 512

# Feedback Generation Settings
FEEDBACK_MIN_LENGTH = 50
FEEDBACK_MAX_LENGTH = 200
FEEDBACK_NUM_SENTENCES = 3

# Resource Links
RESOURCE_LINKS = {
    "MSQ": "https://kennmwai.com/msq-resource",
    "OEQ": "https://kennmwai.com/oeq-resource"
}

# Assessment Settings
ASSESSMENT_TYPES = ["MSQ", "OEQ"]
ASSESSMENT_WEIGHTAGES = {"MSQ": 0.6, "OEQ": 0.4}

# Debug Settings
DEBUG_MODE = False

if __name__ == "__main__":
    try:
        api_key = get_api_key()
        print(f"API Key: {api_key}")
    except ValueError as e:
        print(f"Error: {e}")
