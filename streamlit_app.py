import streamlit as st
import requests
import json
import os
from pathlib import Path
import time
import tempfile
from datetime import datetime
import logging
from PIL import Image
import io
import base64
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
BACKEND_URL = "http://localhost:8000"
TOKEN_FILE = "linkedin_token.json"

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "description" not in st.session_state:
    st.session_state.description = ""
if "use_test_values" not in st.session_state:
    st.session_state.use_test_values = False

def get_test_values():
    """Return test values for development"""
    # Read the test caption
    try:
        with open('tests/caption.txt', 'r') as f:
            caption = f.read()
    except Exception as e:
        logger.error(f"Error reading caption file: {str(e)}")
        caption = "Excited to share my latest insights on AI and machine learning! 🤖✨ #AI #MachineLearning #Innovation"
    
    return {
        "description": caption
    }

def get_test_images():
    """Return list of test images"""
    try:
        image_dir = 'tests/images'
        images = [f for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
        return [os.path.join(image_dir, img) for img in images]
    except Exception as e:
        logger.error(f"Error reading images directory: {str(e)}")
        return []

def check_auth_status():
    """Check if user is authenticated with LinkedIn"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/auth/status")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Auth status check response: {data}")
            return data.get("authenticated", False)
        return False
    except Exception as e:
        logger.error(f"Error checking auth status: {str(e)}")
        return False

def start_linkedin_auth():
    """Start LinkedIn OAuth flow"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/auth/linkedin")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"LinkedIn auth response status: {response.status_code}")
            logger.info(f"LinkedIn auth response headers: {response.headers}")
            logger.info(f"LinkedIn auth response content: {data}")
            return data.get("auth_url")
        return None
    except Exception as e:
        logger.error(f"Error starting LinkedIn auth: {str(e)}")
        return None

def generate_post(prompt):
    """Generate a post using the DeepSeek service"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/generate-post",
            json={"description": prompt}
        )
        if response.status_code == 200:
            return response.json().get("post")
        return None
    except Exception as e:
        logger.error(f"Error generating post: {str(e)}")
        return None

def post_to_linkedin(content, image_url=None):
    """Post content to LinkedIn"""
    try:
        logger.info("Preparing to post to LinkedIn")
        logger.info(f"Content length: {len(content) if content else 0}")
        logger.info(f"Image URL: {image_url}")
        
        data = {"post": content}
        if image_url:
            data["image_url"] = image_url
            
        logger.info("Sending post request to backend")
        response = requests.post(
            "http://localhost:8000/api/post-to-linkedin",
            json=data
        )
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response content: {response.text}")
        
        if response.status_code == 200:
            logger.info("Successfully posted to LinkedIn")
            return True
        else:
            logger.error(f"Failed to post to LinkedIn: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error posting to LinkedIn: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        return False

def save_uploaded_image(uploaded_file):
    """Save uploaded image and return the URL"""
    try:
        # Convert the uploaded file to base64
        image = Image.open(uploaded_file)
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Send to backend
        response = requests.post(
            f"{BACKEND_URL}/api/upload-image",
            files={"file": ("image.png", buffered.getvalue(), "image/png")}
        )
        
        if response.status_code == 200:
            return response.json().get("image_url")
        return None
    except Exception as e:
        logger.error(f"Error saving image: {str(e)}")
        return None

# Set page config
st.set_page_config(
    page_title="LinkedIn Post Assistant",
    page_icon="💼",
    layout="wide"
)

# Add custom CSS
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        height: 3em;
        margin-top: 1em;
    }
    .stTextArea>div>div>textarea {
        height: 200px;
    }
    .uploadedFile {
        display: none;
    }
    .stMarkdown {
        margin-top: 1em;
    }
    .preview-box {
        border: 1px solid #ddd;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        background-color: #f8f9fa;
    }
    .preview-header {
        font-weight: bold;
        margin-bottom: 10px;
    }
    .preview-content {
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("LinkedIn Post Generator")
    
    # Check URL parameters for auth status
    params = st.query_params
    if "auth" in params:
        if params["auth"] == "success":
            st.success("Successfully connected to LinkedIn!")
            st.session_state.authenticated = True
        elif params["auth"] == "error":
            st.error(f"Authentication failed: {params.get('error', 'Unknown error')}")
            st.session_state.authenticated = False
    
    # Check authentication status
    if not st.session_state.authenticated:
        st.warning("Please connect your LinkedIn account first")
        if st.button("Connect LinkedIn"):
            auth_url = start_linkedin_auth()
            if auth_url:
                st.markdown(f'<a href="{auth_url}" target="_blank">Click here to connect LinkedIn</a>', unsafe_allow_html=True)
            else:
                st.error("Failed to get authentication URL")
        return
    
    # Test values toggle
    use_test = st.checkbox("Use test values", value=st.session_state.use_test_values)
    if use_test != st.session_state.use_test_values:
        st.session_state.use_test_values = use_test
        if use_test:
            test_values = get_test_values()
            st.session_state.description = test_values["description"]
    
    # Post generation form
    with st.form("post_form"):
        description = st.text_area(
            "Enter your post prompt",
            value=st.session_state.description,
            height=150
        )
        
        # Show test images if using test values
        if st.session_state.use_test_values:
            test_images = get_test_images()
            if test_images:
                st.write("Available test images:")
                for img_path in test_images:
                    st.image(img_path, caption=os.path.basename(img_path))
        
        uploaded_file = st.file_uploader("Upload an image (optional)", type=["png", "jpg", "jpeg"])
        
        submit = st.form_submit_button("Generate Post")
        
        if submit:
            if description:
                with st.spinner("Generating post..."):
                    generated_post = generate_post(description)
                    if generated_post:
                        st.session_state.description = generated_post
                        st.success("Post generated successfully!")
                    else:
                        st.error("Failed to generate post")
            else:
                st.warning("Please enter a post prompt")
    
    # Display generated content
    if st.session_state.description:
        st.subheader("Generated Content")
        st.write(st.session_state.description)
        
        # Image preview if uploaded
        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Image")
        
        # Post to LinkedIn button
        if st.button("Post to LinkedIn"):
            with st.spinner("Posting to LinkedIn..."):
                image_url = None
                if uploaded_file:
                    image_url = save_uploaded_image(uploaded_file)
                
                if post_to_linkedin(st.session_state.description, image_url):
                    st.success("Posted to LinkedIn successfully!")
                else:
                    st.error("Failed to post to LinkedIn")

if __name__ == "__main__":
    main()
