import aiohttp
import logging
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        self.unsplash_access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        self.base_url = "https://api.unsplash.com"
        
    async def find_relevant_image(self, query: str) -> Optional[str]:
        """Find a relevant image URL for the given query using Unsplash API."""
        try:
            if not self.unsplash_access_key:
                logger.warning("Unsplash API key not found")
                return None
                
            async with aiohttp.ClientSession() as session:
                # Search for photos
                search_url = f"{self.base_url}/search/photos"
                params = {
                    "query": query,
                    "per_page": 1,
                    "orientation": "landscape"
                }
                headers = {
                    "Authorization": f"Client-ID {self.unsplash_access_key}"
                }
                
                async with session.get(search_url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data["results"]:
                            # Get the first image URL
                            image_url = data["results"][0]["urls"]["regular"]
                            logger.info(f"Found relevant image for query: {query}")
                            return image_url
                    else:
                        logger.error(f"Error fetching image: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error in image search: {str(e)}")
            return None
            
    async def get_tech_image(self, topic: str) -> Optional[str]:
        """Get a relevant tech-related image based on the topic."""
        # Map topics to search queries
        topic_queries = {
            "AI": "artificial intelligence technology",
            "machine learning": "machine learning visualization",
            "data science": "data visualization",
            "programming": "coding computer",
            "tech": "technology innovation",
            "startup": "startup office",
            "research": "scientific research",
            "education": "education technology",
            "open source": "open source code",
            "meta": "meta technology",
            "llama": "AI model visualization"
        }
        
        # Find the best matching query
        query = None
        for key, value in topic_queries.items():
            if key.lower() in topic.lower():
                query = value
                break
                
        if not query:
            query = "technology innovation"  # Default query
            
        return await self.find_relevant_image(query) 