from ai_ml_api.speech_to_text_api import SpeechToTextAPI
from utils.config import get_api_key

class SpeechToText:
    def __init__(self):
        self.api_key = get_api_key()
        self.api = SpeechToTextAPI(self.api_key)

    def convert_audio_to_text(self, audio_url, model="#g1_nova-2-general"):
        text = self.api.convert_audio_to_text(audio_url, model)
        return text

# Example usage
if __name__ == "__main__":
    speech_to_text = SpeechToText()
    audio_url = "https://audio-samples.github.io/samples/mp3/blizzard_unconditional/sample-0.mp3"
    text = speech_to_text.convert_audio_to_text(audio_url)
    print(f"Converted Text: {text}")
