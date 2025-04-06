from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import os
import logging
from dotenv import load_dotenv
from services.deepseek_service import DeepseekService
from services.linkedin_service import LinkedInService
import requests
from urllib.parse import urlencode, parse_qs
import time
from pathlib import Path
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="LinkedIn Post Assistant API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:8509"],  # Add both ports
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

class LinkedInPostRequest(BaseModel):
    post: str
    image_url: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LinkedIn Post Assistant</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            .container {
                background: #f9f9f9;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .button {
                display: inline-block;
                background: #0077b5;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 4px;
                margin: 10px 0;
            }
            .button:hover {
                background: #005582;
            }
            .section {
                margin: 20px 0;
            }
            h1 {
                color: #0077b5;
            }
            .error {
                color: #d9534f;
                background: #f9f2f2;
                padding: 10px;
                border-radius: 4px;
                margin: 10px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>LinkedIn Post Assistant</h1>
            
            <div class="section">
                <h2>Step 1: Authenticate with LinkedIn</h2>
                <a href="/api/auth/linkedin" class="button">Connect with LinkedIn</a>
            </div>

            <div class="section">
                <h2>Step 2: Create a Post</h2>
                <form action="/api/post-to-linkedin" method="post" enctype="multipart/form-data">
                    <div>
                        <label for="content">Post Content:</label><br>
                        <textarea name="content" id="content" rows="4" style="width: 100%"></textarea>
                    </div>
                    <div style="margin-top: 10px;">
                        <label for="image">Image (optional):</label><br>
                        <input type="file" name="image" id="image">
                    </div>
                    <button type="submit" class="button" style="margin-top: 10px;">Create Post</button>
                </form>
            </div>

            <div class="section">
                <h2>API Documentation</h2>
                <p>For developers: Access the API documentation at <a href="/docs">/docs</a></p>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/api/auth/status")
async def auth_status():
    """Check authentication status"""
    try:
        is_authenticated = linkedin_service._validate_token_and_user_id()
        return {"authenticated": is_authenticated}
    except Exception as e:
        error_msg = f"Error checking auth status: {str(e)}"
        logger.error(error_msg)
        return {"authenticated": False}

@app.get("/api/auth/linkedin")
async def linkedin_auth():
    """Start LinkedIn OAuth flow"""
    try:
        auth_url = linkedin_service.get_auth_url()
        logger.info(f"Starting LinkedIn OAuth flow. Auth URL: {auth_url}")
        return {"auth_url": auth_url}
    except Exception as e:
        error_msg = f"Error starting LinkedIn OAuth flow: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/auth/callback")
async def linkedin_callback(code: Optional[str] = None, error: Optional[str] = None, error_description: Optional[str] = None, state: Optional[str] = None):
    """Handle LinkedIn OAuth callback"""
    logger.info(f"Received callback with params: {{'code': {code}, 'error': {error}, 'error_description': {error_description}, 'state': {state}}}")
    
    if error:
        error_msg = f"LinkedIn OAuth error: {error} - {error_description}"
        logger.error(error_msg)
        return RedirectResponse(url=f"http://localhost:8501?auth=error&error={error}")
    
    if not code:
        error_msg = "No authorization code received"
        logger.error(error_msg)
        return RedirectResponse(url="http://localhost:8501?auth=error&error=no_code")
    
    try:
        if not linkedin_service.exchange_code_for_token(code):
            error_msg = "Failed to exchange code for token"
            logger.error(error_msg)
            return RedirectResponse(url="http://localhost:8501?auth=error&error=token_exchange_failed")
        
        return RedirectResponse(url="http://localhost:8501?auth=success")
    except Exception as e:
        error_msg = f"Error exchanging code for token: {str(e)}"
        logger.error(error_msg)
        logger.error("Stack trace:", exc_info=True)
        return RedirectResponse(url=f"http://localhost:8501?auth=error&error={str(e)}")

@app.post("/api/generate-post")
async def generate_post(request: Request):
    """Generate a post using DeepSeek"""
    try:
        data = await request.json()
        prompt = data.get("prompt")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="No prompt provided")
            
        post_content = deepseek_service.generate_post(prompt)
        return {"content": post_content}
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error generating post: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image for LinkedIn post"""
    try:
        # Save the uploaded file temporarily
        temp_path = Path("temp_image.jpg")
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return {"image_url": str(temp_path)}
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/post-to-linkedin")
async def post_to_linkedin(request: Request):
    """Post content to LinkedIn"""
    try:
        # Get post data from request
        data = await request.json()
        post_content = data.get("post", "")
        image_url = data.get("image_url")
        
        logger.info(f"Received post request with content length: {len(post_content)}")
        if image_url:
            logger.info(f"Image URL provided: {image_url}")
            
        # Validate token
        if not linkedin_service._validate_token_and_user_id():
            logger.error("Token validation failed")
            raise HTTPException(status_code=401, detail="Not authenticated with LinkedIn")
            
        # Create post
        logger.info("Attempting to create LinkedIn post")
        result = linkedin_service.create_post(post_content, image_url)
        
        if not result:
            raise Exception("LinkedInService.create_post returned False")
        return {"success": True, "message": "Post created successfully"}
        
    except Exception as e:
        logger.exception("Failed to post to LinkedIn")
        raise HTTPException(status_code=500, detail=f"Failed to create LinkedIn post: {str(e)}")
