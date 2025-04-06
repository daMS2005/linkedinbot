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
                    "content": "You are a professional LinkedIn content creator. Create engaging, professional posts that follow LinkedIn best practices. Return ONLY the post text without any explanations, formatting instructions, or meta-commentary."
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
            
            # Clean up the response to ensure it's just the post text
            post_text = result["choices"][0]["message"]["content"].strip()
            
            # Remove any markdown formatting if present
            post_text = post_text.replace("**", "").replace("*", "")
            
            return post_text
        except Exception as e:
            raise Exception(f"Failed to generate post: {str(e)}")

    def _create_prompt(self, description: str, image_url: str = None) -> str:
        """
        Create a prompt for the AI model to generate LinkedIn posts that are ready to post
        """
        base_prompt = f"""
        Create a professional LinkedIn post based on the following description:
        {description}
        
        Guidelines:
        1. Create ONLY the LinkedIn post text - no explanations, no extra output
        2. Format the post for immediate posting on LinkedIn
        3. Use appropriate hashtags (max 3)
        4. Include a call to action
        5. Keep it concise (max 1300 characters)
        6. Make it engaging and professional
        7. Do not include any meta-commentary or explanations about the post
        8. Do not include any placeholders like [Project Name] - use generic terms instead
        9. Do not include any formatting instructions or "Why this works" sections
        10. The output should be ONLY the LinkedIn post text, ready to be copied and pasted
        """
        
        if image_url:
            base_prompt += f"\n\nNote: This post will include an image at: {image_url}"
            
        return base_prompt 