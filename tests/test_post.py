import os
import asyncio
from services.linkedin_service import LinkedInService

# Test post formats
TEST_POSTS = {
    "frustration_innovation": {
        "title": "Turning Frustration into Innovation: Why I Built a LinkedIn Post Generator",
        "content": """I was tired of spending hours crafting the perfect LinkedIn post. Every time I wanted to share an update, I found myself staring at a blank screen, wondering how to make my message stand out.

That's when I decided to build something to solve this problem. I created a LinkedIn Post Generator that uses AI to help craft engaging posts in seconds.

Key features:
- AI-powered post generation
- Image upload support
- Professional formatting
- Time-saving automation

This tool has completely transformed how I share updates on LinkedIn. No more writer's block or hours spent editing!

What problems have you solved with technology? Share your story in the comments! 👇

#Innovation #Productivity #AI #LinkedInTips"""
    }
}

async def test_linkedin_post(post_type="frustration_innovation"):
    # Initialize LinkedIn service
    linkedin_service = LinkedInService()
    
    # Get the test post content
    post_data = TEST_POSTS[post_type]
    
    # Get the test image path (if exists)
    image_path = os.path.join("tests", "images", "test_image.jpg")
    if not os.path.exists(image_path):
        image_path = None
    
    try:
        # Create the post
        result = await linkedin_service.create_post(
            content=post_data["content"],
            image_url=image_path
        )
        print("Post created successfully!")
        print(f"Post URL: {result['post_url']}")
    except Exception as e:
        print(f"Error creating post: {str(e)}")

if __name__ == "__main__":
    # Run the test with the frustration_innovation format
    asyncio.run(test_linkedin_post("frustration_innovation")) 