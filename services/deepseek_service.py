import os
import requests
from dotenv import load_dotenv

load_dotenv()

class DeepseekService:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is not set")

    async def generate_post(self, description: str, image_url: str = None) -> str:
        """
        Generate a LinkedIn post using the Deepseek API
        """
        prompt = self._create_prompt(description, image_url)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional LinkedIn content creator. Create engaging, professional posts that follow LinkedIn best practices."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            raise Exception(f"Failed to generate post: {str(e)}")

    def _create_prompt(self, description: str, image_url: str = None) -> str:
        """
        Create a prompt for the AI model
        """
        base_prompt = f"""
        Create a professional LinkedIn post based on the following description:
        {description}
        
        Guidelines:
        1. Keep it professional and engaging
        2. Use appropriate hashtags (max 3)
        3. Include a call to action
        4. Optimize for LinkedIn's algorithm
        5. Keep it concise (max 1300 characters)
        """
        
        if image_url:
            base_prompt += f"\n\nNote: This post will include an image at: {image_url}"
            
        return base_prompt 