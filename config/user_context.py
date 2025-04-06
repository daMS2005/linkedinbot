from typing import List, Dict, Optional
from pydantic import BaseModel

class UserContext(BaseModel):
    # Academic Information
    education_level: str = "Undergraduate"  # Undergraduate, Graduate, PhD
    major: str = "Computer Science"
    university: str = "University of Technology"
    graduation_year: int = 2026
    gpa: Optional[float] = 3.8
    academic_interests: List[str] = ["Artificial Intelligence", "Machine Learning", "Software Engineering"]
    
    # Professional Development
    career_goals: List[str] = ["AI Research", "Software Development", "Tech Innovation"]
    target_companies: List[str] = ["Meta", "Google", "OpenAI"]
    internship_experience: List[str] = ["Software Engineering Intern", "AI Research Assistant"]
    skills: List[str] = ["Python", "Machine Learning", "Data Structures", "Algorithms"]
    
    # Professional Information
    industry: str = ""
    role: str = ""
    expertise_areas: List[str] = []
    years_of_experience: int = 0
    
    # Content Preferences
    content_style: str = "Technical and Educational"
    target_audience: str = "Tech Professionals and Students"
    preferred_topics: List[str] = ["AI", "Machine Learning", "Tech Innovation", "Student Life"]
    preferred_hashtags: List[str] = ["#AI", "#MachineLearning", "#TechStudent", "#Innovation"]
    
    # Engagement Style
    commentary_style: str = "Analytical and Educational"
    expertise_level: str = "Student with Strong Technical Background"
    recent_topics: List[str] = ["AI Models", "Open Source", "Tech Innovation"]
    
    # Personal Brand
    personal_brand: str = "Tech-Savvy Student and AI Enthusiast"
    unique_value: str = "Combining academic knowledge with practical tech insights"
    tone: str = "Professional yet approachable"
    
    # Content Focus
    content_focus: List[str] = [
        "AI and Machine Learning Developments",
        "Tech Industry Insights",
        "Student Perspective on Tech",
        "Learning and Growth in Tech"
    ]
    
    # Writing Style
    writing_style: str = "Clear, concise, and technically accurate"
    engagement_approach: str = "Share insights and learn from others"
    content_structure: str = "Problem-Solution-Impact format"
    
    # Professional Goals
    short_term_goals: List[str] = [
        "Build strong technical foundation",
        "Gain industry experience through internships",
        "Network with tech professionals"
    ]
    
    long_term_goals: List[str] = [
        "Contribute to AI advancement",
        "Develop innovative tech solutions",
        "Mentor future tech students"
    ]
    
    # Personal Commentary
    personal_experiences: List[str] = []
    key_opinions: Dict[str, str] = {}  # topic -> opinion
    
    # Engagement Preferences
    call_to_action_style: str = "moderate"  # aggressive, moderate, passive
    networking_style: str = "professional"  # professional, casual, formal
    
    # Content History
    engagement_metrics: Dict[str, float] = {
        "likes": 0.0,
        "comments": 0.0,
        "shares": 0.0
    }
    
    def update_engagement_metrics(self, likes: int, comments: int, shares: int):
        """Update engagement metrics with new data."""
        self.engagement_metrics["likes"] = (self.engagement_metrics["likes"] + likes) / 2
        self.engagement_metrics["comments"] = (self.engagement_metrics["comments"] + comments) / 2
        self.engagement_metrics["shares"] = (self.engagement_metrics["shares"] + shares) / 2
        
    def add_personal_experience(self, experience: str):
        """Add a new personal experience."""
        self.personal_experiences.append(experience)
        
    def add_key_opinion(self, topic: str, opinion: str):
        """Add or update a key opinion on a topic."""
        self.key_opinions[topic] = opinion
        
    def add_recent_topic(self, topic: str):
        """Add a topic to recent topics list."""
        if topic not in self.recent_topics:
            self.recent_topics.append(topic)
            if len(self.recent_topics) > 10:  # Keep only last 10 topics
                self.recent_topics.pop(0)

# Default user context
default_user_context = UserContext() 