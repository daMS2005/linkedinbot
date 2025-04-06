import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import aiohttp
from bs4 import BeautifulSoup
import yt_dlp
from config.personality import PersonalityConfig

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ContentAnalyzer:
    def __init__(self, personality_config: PersonalityConfig):
        logger.debug(f"Initializing ContentAnalyzer with personality_config: {personality_config}")
        if not personality_config:
            logger.error("personality_config is None or empty")
            raise ValueError("personality_config is required")
        self.personality = personality_config
        logger.debug("ContentAnalyzer initialized successfully")
        
    async def analyze_content(self, content_url: str) -> Dict[str, Any]:
        """Analyze content from a URL and return structured information."""
        try:
            content_type = self._determine_content_type(content_url)
            
            if content_type == "article":
                return await self._analyze_article(content_url)
            elif content_type == "video":
                return await self._analyze_video(content_url)
            else:
                return await self._analyze_generic_content(content_url)
                
        except Exception as e:
            logger.error(f"Error analyzing content: {str(e)}")
            # Return a default response instead of raising the exception
            return {
                "type": "generic",
                "content": f"Content from: {content_url}",
                "url": content_url,
                "title": "Content Analysis Failed",
                "key_points": ["Unable to analyze content"],
                "topic": "general"
            }
            
    def _determine_content_type(self, url: str) -> str:
        """Determine the type of content from the URL."""
        domain = urlparse(url).netloc.lower()
        
        if any(video_domain in domain for video_domain in ["youtube.com", "vimeo.com"]):
            return "video"
        elif any(article_domain in domain for article_domain in ["medium.com", "dev.to", "blog"]):
            return "article"
        else:
            return "generic"
            
    async def _analyze_article(self, url: str) -> Dict[str, Any]:
        """Extract and analyze article content."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()
                
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract article content
        title = soup.find('title').text if soup.find('title') else ""
        paragraphs = [p.text for p in soup.find_all('p')]
        content = " ".join(paragraphs)
        
        # Analyze content based on personality preferences
        key_points = self._extract_key_points(content)
        topic = self._identify_topic(content)
        
        return {
            "type": "article",
            "title": title,
            "content": content,
            "key_points": key_points,
            "topic": topic,
            "url": url
        }
        
    async def _analyze_video(self, url: str) -> Dict[str, Any]:
        """Extract and analyze video content."""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        return {
            "type": "video",
            "title": info.get('title', ''),
            "description": info.get('description', ''),
            "duration": info.get('duration', 0),
            "url": url
        }
        
    async def _analyze_generic_content(self, url: str) -> Dict[str, Any]:
        """Analyze generic content that doesn't fit other categories."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()
                
        soup = BeautifulSoup(html, 'html.parser')
        content = soup.get_text()
        
        return {
            "type": "generic",
            "content": content,
            "url": url
        }
        
    def _extract_key_points(self, content: str) -> list:
        """Extract key points from content based on personality preferences."""
        # This would be enhanced with NLP in a production environment
        sentences = content.split('.')
        return [s.strip() for s in sentences if len(s.strip()) > 50][:3]
        
    def _identify_topic(self, content: str) -> str:
        """Identify the main topic of the content."""
        # This would be enhanced with topic modeling in a production environment
        words = content.lower().split()
        topic_scores = {topic: 0 for topic in self.personality.preferred_topics}
        
        for word in words:
            for topic in self.personality.preferred_topics:
                if topic in word:
                    topic_scores[topic] += 1
                    
        return max(topic_scores.items(), key=lambda x: x[1])[0] 