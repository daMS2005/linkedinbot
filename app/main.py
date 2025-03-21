from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
import os
import logging
from dotenv import load_dotenv
from services.deepseek_service import DeepseekService
from services.linkedin_service import LinkedInService
import requests
from urllib.parse import urlencode
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="LinkedIn Post Assistant API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
linkedin_service = LinkedInService()
deepseek_service = DeepseekService()

class PostRequest(BaseModel):
    description: str
    image_url: Optional[str] = None

@app.get("/api/auth/linkedin")
async def linkedin_auth():
    """Start LinkedIn OAuth flow"""
    auth_url = await linkedin_service.get_auth_url()
    logger.info(f"Starting LinkedIn OAuth flow. Auth URL: {auth_url}")
    return {"auth_url": auth_url}

@app.get("/api/auth/callback")
async def linkedin_callback(code: str, state: Optional[str] = None):
    """Handle LinkedIn OAuth callback"""
    try:
        # Exchange code for access token
        await linkedin_service.get_access_token(code)
        
        # Redirect back to Streamlit with success parameter
        return RedirectResponse(
            url=f"http://localhost:8501/?auth_success=true",
            status_code=302
        )
    except Exception as e:
        logger.error(f"Error in LinkedIn callback: {str(e)}")
        # Redirect back to Streamlit with error parameter
        return RedirectResponse(
            url=f"http://localhost:8501/?auth_error={str(e)}",
            status_code=302
        )

@app.post("/api/generate-post")
async def generate_post(request: PostRequest):
    """Generate a LinkedIn post using Deepseek AI"""
    try:
        post = await deepseek_service.generate_post(request.description, request.image_url)
        return {"post": post}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image and return its location"""
    try:
        # Create uploads directory if it doesn't exist
        os.makedirs("uploads", exist_ok=True)
        
        # Generate unique filename
        filename = f"{int(time.time() * 1000)}.jpeg"
        filepath = f"uploads/{filename}"
        
        # Save the file
        with open(filepath, "wb") as f:
            f.write(await file.read())
        
        return {"location": filepath}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/post-to-linkedin")
async def post_to_linkedin(request: PostRequest):
    """Create a post on LinkedIn"""
    try:
        result = await linkedin_service.create_post(
            content=request.description,
            image_url=request.image_url
        )
        return {
            "success": True,
            "post_id": result["post_id"],
            "post_url": result["post_url"]
        }
    except Exception as e:
        logger.error(f"Failed to post to LinkedIn: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to post to LinkedIn",
                "error": str(e)
            }
        )
