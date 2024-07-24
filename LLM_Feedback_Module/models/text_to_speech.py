from ai_ml_api.text_to_speech_api import TextToSpeechAPI
from utils.config import get_api_key


class TextToSpeech:
    def __init__(self):
        self.api_key = get_api_key()
        self.api = TextToSpeechAPI(self.api_key)

    def convert_text_to_audio(
        self, text, model="#g1_aura-asteria-en", output_path="output_audio.wav"
    ):
        audio_content = self.api.convert_text_to_audio(text)
        with open(output_path, "wb") as file:
            file.write(audio_content)
        return output_path


# Example usage
if __name__ == "__main__":
    text_to_speech = TextToSpeech()
    text = "Hello, this is a test of the text to speech conversion."
    output_path = text_to_speech.convert_text_to_audio(text)
    print(f"Audio saved at: {output_path}")
