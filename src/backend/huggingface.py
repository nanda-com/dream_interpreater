from transformers import pipeline

class HuggingFaceLLM:
    def __init__(self):
        self.generator = pipeline(
            'text-generation', 
            model='gpt2'  # Free model
        )
    
    def generate_interpretation(self, dream_description):
        prompt = f"Interpret this dream symbolically: {dream_description}"
        response = self.generator(prompt, max_length=200)
        return response[0]['generated_text']