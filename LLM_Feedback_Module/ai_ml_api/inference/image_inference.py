from ai_ml_api.image_generation_api import ImageGenerationAPI
from utils.config import get_api_key

class ImageInference:
    def __init__(self):
        self.api_key = get_api_key()
        self.image_generation_api = ImageGenerationAPI(self.api_key)

    def generate_image(self, prompt, output_path="./image.png"):
        image_data = self.image_generation_api.generate_image(prompt)
        with open(output_path, "wb") as file:
            file.write(image_data)
        print(f"Image saved to {output_path}")

# Example usage
if __name__ == "__main__":
    image_inference = ImageInference()
    prompt = "Hyperrealistic art featuring a cat in costume."
    image_inference.generate_image(prompt)
