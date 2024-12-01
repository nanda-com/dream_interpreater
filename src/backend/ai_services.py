# src/backend/ai_services.py
import os
import openai
# from diffusers import StableDiffusionPipeline

class DreamAIService:
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')
        print(openai.api_key)
        # self.image_generator = StableDiffusionPipeline.from_pretrained("stabilityai/stable-diffusion-2-1")

    def generate_interpretation(self, dream_description):
        response = openai.ChatCompletion.create(
            model="gpt-3.5",
            messages=[
                {"role": "system", "content": "You are a dream interpretation expert"},
                {"role": "user", "content": f"Interpret this dream: {dream_description}"}
            ]
        )
        return response.choices[0].message.content

    # def generate_dream_image(self, interpretation):
    #     image = self.image_generator(
    #         prompt=interpretation,
    #         num_inference_steps=50
    #     ).images[0]
    #     return image