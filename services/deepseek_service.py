import os
import json
import logging
import aiohttp
import asyncio
from typing import Optional, Dict, Any
from config.personality import PersonalityConfig, default_personality
from config.user_context import UserContext, default_user_context
from services.content_analyzer import ContentAnalyzer
from .image_service import ImageService

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class DeepseekService:
    def __init__(self, personality_config: PersonalityConfig = None, user_context: UserContext = None):
        logger.debug("Initializing DeepseekService")
        logger.debug(f"Received personality_config: {personality_config}")
        logger.debug(f"Received user_context: {user_context}")
        
        self.personality = personality_config or default_personality
        logger.debug(f"Using personality: {self.personality}")
        
        self.user_context = user_context or default_user_context
        logger.debug(f"Using user_context: {self.user_context}")
        
        try:
            logger.debug("Initializing ContentAnalyzer")
            self.content_analyzer = ContentAnalyzer(personality_config=self.personality)
            logger.debug("ContentAnalyzer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ContentAnalyzer: {str(e)}")
            raise
            
        try:
            logger.debug("Initializing ImageService")
            self.image_service = ImageService()
            logger.debug("ImageService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ImageService: {str(e)}")
            raise
            
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        logger.debug(f"API key present: {bool(self.api_key)}")
        if self.api_key:
            logger.debug(f"API key length: {len(self.api_key)}")
        
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        logger.debug(f"Using API URL: {self.api_url}")
        
        logger.debug("DeepseekService initialization complete")
        
        if not self.api_key:
            logger.warning("DeepSeek API key not found in environment variables")
        else:
            logger.info("DeepSeek API key loaded successfully")
        
    async def generate_post(self, content_url: Optional[str] = None, description: Optional[str] = None, commentary: Optional[str] = None) -> Dict[str, str]:
        """Generate a LinkedIn post based on content URL or description."""
        try:
            # Store the content URL for reference in formatting
            if content_url:
                self.last_content_url = content_url
                try:
                    content_info = await self.content_analyzer.analyze_content(content_url)
                    prompt = self._create_content_based_prompt(content_info, commentary)
                    
                    # Find relevant image for the content
                    topic = content_info.get("topic", "technology")  # Default to "technology" if topic is missing
                    image_url = await self.image_service.get_tech_image(topic)
                except Exception as e:
                    logger.error(f"Error analyzing content: {str(e)}")
                    # Fallback to description-based prompt if content analysis fails
                    prompt = self._create_description_based_prompt(f"Content from: {content_url}", commentary)
                    image_url = await self.image_service.get_tech_image("technology")
            else:
                self.last_content_url = None
                prompt = self._create_description_based_prompt(description, commentary)
                image_url = await self.image_service.get_tech_image(description or "technology")
                
            post = await self._generate_with_deepseek(prompt)
            formatted_post = self._format_post(post)
            
            return {
                "post": formatted_post,
                "image_url": image_url
            }
            
        except Exception as e:
            logger.error(f"Error generating post: {str(e)}")
            # Return a fallback response instead of raising an error
            return {
                "post": f"Excited to share this content! {commentary or ''}\n\nRead more: {content_url or 'Check out the link in comments'}",
                "image_url": None
            }
            
    def _create_content_based_prompt(self, content_info: Dict[str, Any], commentary: Optional[str] = None) -> str:
        """Create a prompt based on analyzed content."""
        content_type = content_info["type"]
        template = self.personality.response_templates.get(content_type, "")
        
        # Add comprehensive user context information
        user_context_info = f"""
        Academic Context:
        - Education: {self.user_context.education_level} in {self.user_context.major} at {self.user_context.university}
        - Academic Interests: {', '.join(self.user_context.academic_interests)}
        - Skills: {', '.join(self.user_context.skills)}
        
        Professional Context:
        - Career Goals: {', '.join(self.user_context.career_goals)}
        - Target Companies: {', '.join(self.user_context.target_companies)}
        - Internship Experience: {', '.join(self.user_context.internship_experience)}
        
        Content Style:
        - Personal Brand: {self.user_context.personal_brand}
        - Writing Style: {self.user_context.writing_style}
        - Content Focus: {', '.join(self.user_context.content_focus)}
        - Tone: {self.user_context.tone}
        
        Recent Topics: {', '.join(self.user_context.recent_topics)}
        Preferred Hashtags: {', '.join(self.user_context.preferred_hashtags)}
        """
        
        # Add personal commentary if provided
        commentary_section = ""
        if commentary:
            commentary_section = f"""
            Personal Commentary:
            {commentary}
            """
            
        if content_type == "article":
            return f"""
            Create a LinkedIn post about this article:
            Title: {content_info['title']}
            Key Points: {', '.join(content_info['key_points'])}
            Topic: {content_info['topic']}
            
            {user_context_info}
            
            {commentary_section}
            
            Use this template as a base:
            {template}
            
            Guidelines:
            1. Write from a student's perspective with strong technical understanding
            2. Focus on learning insights and industry implications
            3. Keep questions to a minimum (maximum 1 question if needed)
            4. Include relevant technical details that showcase your knowledge
            5. End with a clear call to action or key takeaway
            6. Use a mix of technical and educational language
            7. Reference your academic background when relevant
            8. Include 2-3 relevant hashtags from the preferred list
            
            Personality traits to incorporate:
            - Formality level: {self.personality.formality}
            - Enthusiasm level: {self.personality.enthusiasm}
            - Humor level: {self.personality.humor}
            - Expertise level: {self.personality.expertise_level}
            """
            
        elif content_type == "video":
            return f"""
            Create a LinkedIn post about this video:
            Title: {content_info['title']}
            Description: {content_info['description']}
            
            {user_context_info}
            
            {commentary_section}
            
            Use this template as a base:
            {template}
            
            Guidelines:
            1. Write from a student's perspective with strong technical understanding
            2. Focus on learning insights and industry implications
            3. Keep questions to a minimum (maximum 1 question if needed)
            4. Include relevant technical details that showcase your knowledge
            5. End with a clear call to action or key takeaway
            6. Use a mix of technical and educational language
            7. Reference your academic background when relevant
            8. Include 2-3 relevant hashtags from the preferred list
            
            Personality traits to incorporate:
            - Formality level: {self.personality.formality}
            - Enthusiasm level: {self.personality.enthusiasm}
            - Humor level: {self.personality.humor}
            - Expertise level: {self.personality.expertise_level}
            """
            
        else:
            return self._create_description_based_prompt(content_info['content'], commentary)
            
    def _create_description_based_prompt(self, description: str, commentary: Optional[str] = None) -> str:
        """Create a prompt based on description."""
        # Add comprehensive user context information
        user_context_info = f"""
        Academic Context:
        - Education: {self.user_context.education_level} in {self.user_context.major} at {self.user_context.university}
        - Academic Interests: {', '.join(self.user_context.academic_interests)}
        - Skills: {', '.join(self.user_context.skills)}
        
        Professional Context:
        - Career Goals: {', '.join(self.user_context.career_goals)}
        - Target Companies: {', '.join(self.user_context.target_companies)}
        - Internship Experience: {', '.join(self.user_context.internship_experience)}
        
        Content Style:
        - Personal Brand: {self.user_context.personal_brand}
        - Writing Style: {self.user_context.writing_style}
        - Content Focus: {', '.join(self.user_context.content_focus)}
        - Tone: {self.user_context.tone}
        
        Recent Topics: {', '.join(self.user_context.recent_topics)}
        Preferred Hashtags: {', '.join(self.user_context.preferred_hashtags)}
        """
        
        # Add personal commentary if provided
        commentary_section = ""
        if commentary:
            commentary_section = f"""
            Personal Commentary:
            {commentary}
            """
            
        return f"""
        Create a LinkedIn post about:
        {description}
        
        {user_context_info}
        
        {commentary_section}
        
        Guidelines:
        1. Write from a student's perspective with strong technical understanding
        2. Focus on learning insights and industry implications
        3. Keep questions to a minimum (maximum 1 question if needed)
        4. Include relevant technical details that showcase your knowledge
        5. End with a clear call to action or key takeaway
        6. Use a mix of technical and educational language
        7. Reference your academic background when relevant
        8. Include 2-3 relevant hashtags from the preferred list
        
        Personality traits to incorporate:
        - Formality level: {self.personality.formality}
        - Enthusiasm level: {self.personality.enthusiasm}
        - Humor level: {self.personality.humor}
        - Expertise level: {self.personality.expertise_level}
        """
        
    async def _generate_with_deepseek(self, prompt: str) -> str:
        """Generate content using the DeepSeek API with no timeout."""
        try:
            # Create a session with no timeout
            timeout = None
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                # Create a more detailed prompt that incorporates user context
                enhanced_prompt = f"""
                Create a detailed LinkedIn post with the following context:
                
                {prompt}
                
                Additional Context:
                - Writing Style: {self.user_context.writing_style}
                - Personal Brand: {self.user_context.personal_brand}
                - Tone: {self.user_context.tone}
                - Content Focus: {', '.join(self.user_context.content_focus)}
                - Preferred Hashtags: {', '.join(self.user_context.preferred_hashtags)}
                
                Guidelines:
                1. Write a comprehensive post (300-500 words)
                2. Include specific insights and analysis
                3. Reference your academic background when relevant
                4. Use a mix of technical and educational language
                5. Include 2-3 relevant hashtags
                6. End with a clear call to action
                7. Maintain a {self.personality.formality} level of formality
                8. Show {self.personality.enthusiasm} level of enthusiasm
                9. Include {self.personality.humor} level of humor
                10. Demonstrate {self.personality.expertise_level} level of expertise
                """
                
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are a professional LinkedIn content creator with expertise in technology and AI."},
                        {"role": "user", "content": enhanced_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
                
                # Make the API call with no timeout
                async with session.post(self.api_url, headers=headers, json=payload, timeout=None) as response:
                    if response.status != 200:
                        logger.error(f"API request failed with status {response.status}")
                        return self._generate_fallback_response(prompt)
                    
                    # Get the response text
                    response_text = await response.text()
                    
                    try:
                        response_data = json.loads(response_text)
                        if "choices" in response_data and len(response_data["choices"]) > 0:
                            return response_data["choices"][0]["message"]["content"]
                        else:
                            logger.error("Invalid response format from API")
                            return self._generate_fallback_response(prompt)
                    except json.JSONDecodeError:
                        logger.error("Failed to parse API response as JSON")
                        return self._generate_fallback_response(prompt)
                        
        except asyncio.TimeoutError:
            logger.error("API request timed out")
            return self._generate_fallback_response(prompt)
        except Exception as e:
            logger.error(f"Error calling DeepSeek API: {str(e)}")
            return self._generate_fallback_response(prompt)
            
    def _generate_fallback_response(self, prompt: str) -> str:
        """Generate a fallback response when the API call fails."""
        if "article" in prompt.lower():
            return "I found this article interesting and wanted to share it with my network. The key insights are worth discussing. What are your thoughts?"
        elif "video" in prompt.lower():
            return "Just watched this video and found it insightful. The content really makes you think about the future of technology. Has anyone else seen this?"
        else:
            return "Excited to share this content with my network. The insights are valuable for anyone interested in technology and innovation. What are your thoughts?"
        
    def _format_post(self, post: str) -> str:
        """Format the generated post according to personality preferences."""
        # Remove only bold Markdown formatting
        post = post.replace("**", "")
        
        # Add emojis based on content type and topic
        if "AI" in post or "artificial intelligence" in post.lower():
            post = "🤖 " + post
            if "learning" in post.lower():
                post = post.replace("learning", "learning 🧠")
        elif "tech" in post.lower() or "technology" in post.lower():
            post = "💻 " + post
        elif "innovation" in post.lower():
            post = "💡 " + post
        elif "data" in post.lower():
            post = "📊 " + post
        elif "research" in post.lower():
            post = "🔬 " + post
        elif "open source" in post.lower():
            post = "🌐 " + post
        elif "student" in post.lower() or "education" in post.lower():
            post = "🎓 " + post
            
        # Add engagement emojis based on personality
        if self.personality.enthusiasm > 0.7:
            post = post.replace(".", "! ✨")
            post = post.replace("?", "? 🤔")
        elif self.personality.enthusiasm > 0.4:
            post = post.replace(".", "! 👏")
            post = post.replace("?", "? 💭")
            
        # Add topic-specific emojis
        if "meta" in post.lower() or "facebook" in post.lower():
            post = post.replace("Meta", "Meta 🚀")
        if "model" in post.lower():
            post = post.replace("model", "model 🤖")
        if "release" in post.lower():
            post = post.replace("release", "release 🎉")
            
        # Ensure the post ends with a reference if it doesn't already have one
        if "Read more:" not in post and "Check it out:" not in post and "Link:" not in post:
            # Extract URL from the prompt if available
            if hasattr(self, 'last_content_url'):
                post += f"\n\nRead more: {self.last_content_url}"
            
        return post.strip()
        
    def _remove_markdown_formatting(self, text: str) -> str:
        """Remove only bold Markdown formatting from text while preserving other formatting."""
        # Remove bold formatting
        text = text.replace("**", "")
        
        return text 