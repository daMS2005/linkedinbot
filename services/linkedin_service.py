import os
import requests
import logging
from dotenv import load_dotenv
from typing import Optional, Dict
import urllib.parse
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class LinkedInService:
    # Class variable to store tokens across instances
    _tokens: Dict[str, str] = {}
    _token_file = "linkedin_token.json"

    def __init__(self):
        self.client_id = os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
        self.redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/api/auth/callback")
        
        if not self.client_id or not self.client_secret:
            raise ValueError("LinkedIn API credentials not found in environment variables")
        
        # Load token from file if exists
        self._load_token()

    def _load_token(self):
        """Load token from file if it exists"""
        try:
            if os.path.exists(self._token_file):
                with open(self._token_file, 'r') as f:
                    token_data = json.load(f)
                    self._tokens[self.client_id] = token_data.get('access_token')
                    logger.info("Loaded access token from file")
        except Exception as e:
            logger.error(f"Error loading token from file: {str(e)}")

    def _save_token(self):
        """Save token to file"""
        try:
            if self.access_token:
                with open(self._token_file, 'w') as f:
                    json.dump({'access_token': self.access_token}, f)
                logger.info("Saved access token to file")
        except Exception as e:
            logger.error(f"Error saving token to file: {str(e)}")

    @property
    def access_token(self) -> Optional[str]:
        """Get the stored access token"""
        return self._tokens.get(self.client_id)

    @access_token.setter
    def access_token(self, value: str):
        """Store the access token"""
        self._tokens[self.client_id] = value
        self._save_token()

    async def get_auth_url(self) -> str:
        """Generate LinkedIn OAuth authorization URL"""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "w_member_social",  # Only request posting permission
            "state": "random_state_string"
        }
        return f"https://www.linkedin.com/oauth/v2/authorization?{urllib.parse.urlencode(params)}"

    async def get_access_token(self, code: str) -> str:
        """Exchange authorization code for access token"""
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        try:
            logger.info(f"Exchanging code for token with data: {data}")
            response = requests.post(
                token_url,
                data=data,
                headers=headers
            )
            
            if response.status_code != 200:
                error_msg = f"LinkedIn API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            token_data = response.json()
            logger.info("Successfully obtained access token")
            self.access_token = token_data["access_token"]
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error while getting access token: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Failed to get LinkedIn access token: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def _get_user_urn(self) -> str:
        """
        Get the user's LinkedIn URN using the /v2/me endpoint
        
        Returns:
            str: User's LinkedIn ID/URN
        """
        if not self.access_token:
            raise Exception("Access token not available. Please authenticate first.")
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202304"
        }
        
        try:
            logger.info("Getting user profile using /v2/me endpoint")
            response = requests.get(
                "https://api.linkedin.com/v2/me",
                headers=headers
            )
            
            if response.status_code != 200:
                error_msg = f"LinkedIn API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            user_data = response.json()
            user_id = user_data.get("id")
            
            if not user_id:
                error_msg = "No user ID found in response"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            logger.info(f"Successfully retrieved user ID: {user_id}")
            return f"urn:li:person:{user_id}"
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error while getting user URN: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Failed to get user URN: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def create_post(self, content: str, image_url: Optional[str] = None) -> dict:
        """
        Create a post on LinkedIn and return post details
        
        Args:
            content (str): The text content of the post
            image_url (Optional[str]): URL of an image to include in the post
            
        Returns:
            dict: Contains post ID and post URL
        """
        if not self.access_token:
            raise Exception("Access token not available. Please authenticate first.")
        
        try:
            # Get user URN first
            user_urn = await self._get_user_urn()
            logger.info(f"Using user URN: {user_urn}")
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
                "LinkedIn-Version": "202304"
            }
            
            # Register the image with LinkedIn if provided
            image_urn = None
            if image_url:
                logger.info("Registering image with LinkedIn")
                # Register image upload
                register_upload_response = requests.post(
                    "https://api.linkedin.com/v2/assets?action=registerUpload",
                    headers=headers,
                    json={
                        "registerUploadRequest": {
                            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                            "owner": user_urn,
                            "serviceRelationships": [{
                                "relationshipType": "OWNER",
                                "identifier": "urn:li:userGeneratedContent"
                            }]
                        }
                    }
                )
                
                if register_upload_response.status_code != 200:
                    error_msg = f"Failed to register image upload: {register_upload_response.status_code} - {register_upload_response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                upload_data = register_upload_response.json()
                image_urn = upload_data["value"]["asset"]
                upload_url = upload_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
                
                # Read and upload the image
                with open(image_url, 'rb') as image_file:
                    image_data = image_file.read()
                    upload_response = requests.put(
                        upload_url,
                        data=image_data,
                        headers={
                            "Authorization": f"Bearer {self.access_token}"
                        }
                    )
                    
                    if upload_response.status_code != 201:
                        error_msg = f"Failed to upload image: {upload_response.status_code} - {upload_response.text}"
                        logger.error(error_msg)
                        raise Exception(error_msg)
            
            # Prepare post data
            post_data = {
                "author": user_urn,
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
            
            # Add image if uploaded successfully
            if image_urn:
                logger.info("Adding image to post")
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                    "status": "READY",
                    "media": image_urn,
                    "title": {
                        "text": "LinkedIn Post Image"
                    }
                }]
            
            logger.info("Sending post request to LinkedIn")
            response = requests.post(
                "https://api.linkedin.com/v2/ugcPosts",
                headers=headers,
                json=post_data
            )
            
            if response.status_code != 201:
                error_msg = f"LinkedIn API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            post_data = response.json()
            post_id = post_data.get("id")
            
            # Construct post URL
            post_url = f"https://www.linkedin.com/feed/update/{post_id}"
            
            logger.info(f"Successfully created LinkedIn post: {post_url}")
            return {
                "post_id": post_id,
                "post_url": post_url,
                "status": "success"
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error while creating LinkedIn post: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Failed to create LinkedIn post: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) 