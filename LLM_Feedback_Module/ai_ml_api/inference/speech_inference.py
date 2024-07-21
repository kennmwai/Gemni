from ai_ml_api.speech_to_text_api import SpeechToTextAPI
from ai_ml_api.text_to_speech_api import TextToSpeechAPI
from utils.config import get_api_key

class SpeechInference:
    def __init__(self):
        self.api_key = get_api_key()
        self.speech_to_text_api = SpeechToTextAPI(self.api_key)
        self.text_to_speech_api = TextToSpeechAPI(self.api_key)

    def audio_to_text(self, audio_url):
        return self.speech_to_text_api.convert_audio_to_text(audio_url)

    def text_to_audio(self, text, output_path="output.wav"):
        audio_content = self.text_to_speech_api.convert_text_to_audio(text)
        with open(output_path, "wb") as file:
            file.write(audio_content)
        print(f"Audio saved to {output_path}")

# Example usage
if __name__ == "__main__":
    speech_inference = SpeechInference()
    audio_url = "https://audio-samples.github.io/samples/mp3/blizzard_unconditional/sample-0.mp3"
    text_response = speech_inference.audio_to_text(audio_url)
    print(f"Converted Text: {text_response}")

    text = "Hi! I'm your friendly assistant."
    speech_inference.text_to_audio(text)
