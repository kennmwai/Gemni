from ai_ml_api.image_generation_api import ImageGenerationAPI
from utils.config import get_api_key


class ImageInference:
    def __init__(self):
        self.api_key = get_api_key()
        self.api = ImageGenerationAPI(self.api_key)

    def generate_image(
        self,
        prompt,
        model="stabilityai/stable-diffusion-2-1",
        output_path="./generated_image.png",
    ):
        image_data = self.api.generate_image(prompt, model)
        with open(output_path, "wb") as file:
            file.write(image_data)
        return output_path


# Example usage
if __name__ == "__main__":
    image_inference = ImageInference()
    prompt = "A futuristic cityscape at sunset."
    output_path = image_inference.generate_image(prompt)
    print(f"Image saved at: {output_path}")
