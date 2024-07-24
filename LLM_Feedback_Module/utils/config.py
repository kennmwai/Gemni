# Configuration file for the LLM Feedback Module (wil use .env later for  python-dotenv)
import os


def get_api_key():
    return os.getenv("AIML_API_KEY", "YOUR_DEFAULT_API_KEY")


# Ignore these as would be used later:
#
# API Keys
AI_ML_API_KEY = "YOUR_AI_ML_API_KEY_HERE"
LLM_MODEL_API_KEY = "YOUR_LLM_MODEL_API_KEY_HERE"

# Model Settings
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
    "OEQ": "https://kennmwai.com/oeq-resource",
}

# Assessment Settings
ASSESSMENT_TYPES = ["MSQ", "OEQ"]
ASSESSMENT_WEIGHTAGES = {"MSQ": 0.6, "OEQ": 0.4}

# Debug Settings
DEBUG_MODE = False
