import os
import requests
import logging
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import urllib.parse
import json
from pathlib import Path
import time
from datetime import datetime
import secrets
import jwt
import random
import string
from urllib.parse import urlencode, quote
import traceback

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LinkedInService:
    """Service for interacting with LinkedIn API"""
    
    def __init__(self):
        """Initialize LinkedIn service with credentials from environment variables"""
        # Load credentials from environment variables
        self.client_id = os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
        self.redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI")
        
        # Validate required environment variables
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("Missing required LinkedIn credentials in environment variables")
            
        # API endpoints
        self.auth_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        self.api_url = "https://api.linkedin.com/v2"
        
        # Initialize state
        self.access_token = None
        self.user_id = None
        self.state = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        
        # Load existing token if available
        self._load_token()
        
    def _load_token(self) -> None:
        """Load access token from file"""
        try:
            if os.path.exists("linkedin_token.json"):
                with open("linkedin_token.json", "r") as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token")
                    self.user_id = data.get("user_id")
                    logger.info("Loaded access token and user ID from file")
            else:
                logger.info("No token file found")
        except Exception as e:
            logger.error(f"Error loading token: {str(e)}")
            self.access_token = None
            self.user_id = None
            
    def _save_token(self) -> None:
        """Save access token to file"""
        try:
            data = {
                "access_token": self.access_token,
                "user_id": self.user_id
            }
            with open("linkedin_token.json", "w") as f:
                json.dump(data, f)
            logger.info("Saved access token and user ID to file")
        except Exception as e:
            logger.error(f"Error saving token: {str(e)}")
            
    def _validate_token_and_user_id(self) -> bool:
        """Validate the access token and user ID"""
        try:
            if not self.access_token:
                logger.error("No access token available")
                return False
                
            # Get user info from OpenID Connect endpoint
            headers = self._get_headers()
            profile_response = requests.get(
                "https://api.linkedin.com/v2/userinfo",
                headers=headers
            )
            
            if profile_response.status_code != 200:
                error_msg = f"Token validation failed: {profile_response.status_code}"
                logger.error(error_msg)
                return False
                
            # Extract user ID from OpenID Connect response
            user_info = profile_response.json()
            self.user_id = user_info.get("sub")
            
            if not self.user_id:
                logger.error("No user ID found in userinfo response")
                return False
                
            logger.info("Token and user ID validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            return False

    def _get_user_urn(self) -> str:
        """Get the user URN for LinkedIn API requests"""
        if not self.user_id:
            logger.error("No user ID available")
            raise Exception("No user ID available")
        return f"urn:li:person:{self.user_id}"

    def get_auth_url(self) -> str:
        """Get the LinkedIn OAuth authorization URL."""
        try:
            # Required scopes for OpenID Connect and posting
            scopes = [
                "openid",  # Required for OpenID Connect
                "profile",  # Required for basic profile info
                "email",    # Required for email info
                "w_member_social"  # Required for posting
            ]
            
            # Construct the authorization URL
            auth_url = (
                f"{self.auth_url}?"
                f"response_type=code&"
                f"client_id={self.client_id}&"
                f"redirect_uri={quote(self.redirect_uri)}&"
                f"scope={'+'.join(scopes)}&"
                f"state={self.state}"
            )
            
            logger.info("Generated authorization URL")
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating auth URL: {str(e)}")
            raise Exception(f"Failed to generate auth URL: {str(e)}")

    def exchange_code_for_token(self, code: str) -> bool:
        """Exchange authorization code for access token and get user info."""
        try:
            # Prepare token request data
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri
            }
            
            # Make token request
            response = requests.post(
                self.token_url,
                data=data
            )
            
            if response.status_code != 200:
                error_msg = f"Failed to exchange code for token: {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
            # Extract access token
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            
            if not self.access_token:
                error_msg = "No access token in response"
                logger.error(error_msg)
                raise Exception(error_msg)
                
            # Get user info from OpenID Connect endpoint
            headers = self._get_headers()
            userinfo_response = requests.get(
                "https://api.linkedin.com/v2/userinfo",
                headers=headers
            )
            
            if userinfo_response.status_code != 200:
                error_msg = f"Failed to get user info: {userinfo_response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
            # Extract user ID from userinfo response
            user_info = userinfo_response.json()
            self.user_id = user_info.get("sub")
            
            if not self.user_id:
                error_msg = "No user ID in userinfo response"
                logger.error(error_msg)
                raise Exception(error_msg)
                
            # Save token and user ID
            self._save_token()
            logger.info("Successfully obtained access token and user ID")
            return True
            
        except Exception as e:
            error_msg = f"Error exchanging code for token: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def create_post(self, content: str, image_url: Optional[str] = None) -> bool:
        """Create a post on LinkedIn."""
        try:
            # Validate token and get user URN
            if not self._validate_token_and_user_id():
                raise Exception("Not authenticated with LinkedIn")
                
            # Get user URN
            author_urn = self._get_user_urn()
            logger.info(f"Using author URN: {author_urn}")
            
            # Prepare post data
            post_data = {
                "author": author_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # Add image if provided
            if image_url:
                # Register image with LinkedIn
                logger.info("Registering image with LinkedIn")
                asset_response = requests.post(
                    f"{self.api_url}/assets?action=registerUpload",
                    headers=self._get_headers(),
                    json={
                        "registerUploadRequest": {
                            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                            "owner": author_urn,
                            "serviceRelationships": [{
                                "relationshipType": "OWNER",
                                "identifier": "urn:li:userGeneratedContent"
                            }]
                        }
                    }
                )
                
                if asset_response.status_code != 200:
                    logger.error("Failed to get asset or upload URL from LinkedIn")
                    return False
                    
                asset_data = asset_response.json()
                asset = asset_data["value"]["asset"]
                upload_url = asset_data["value"]["uploadInstructions"]["uploadUrl"]
                
                # Upload image
                with requests.get(image_url) as img_response:
                    if img_response.status_code != 200:
                        logger.error("Failed to download image")
                        return False
                        
                    upload_response = requests.put(
                        upload_url,
                        data=img_response.content,
                        headers={"Content-Type": "image/jpeg"}
                    )
                    
                    if upload_response.status_code != 201:
                        logger.error("Failed to upload image to LinkedIn")
                        return False
                        
                # Add image to post
                logger.info("Adding image to post")
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                    "status": "READY",
                    "description": {
                        "text": "Generated image"
                    },
                    "media": asset,
                    "title": {
                        "text": "Generated image"
                    }
                }]
            
            # Send post request
            logger.info("Sending post request to LinkedIn")
            response = requests.post(
                f"{self.api_url}/ugcPosts",
                headers=self._get_headers(),
                json=post_data
            )
            
            if response.status_code != 201:
                logger.error(f"LinkedIn POST /ugcPosts status: {response.status_code}")
                logger.error(f"LinkedIn POST /ugcPosts response: {response.text}")
                return False
                
            logger.info("Successfully created LinkedIn post")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create LinkedIn post: {str(e)}")
            return False
            
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for LinkedIn API requests"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }