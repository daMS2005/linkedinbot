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

def generate_post(description: str = None, content_url: str = None, commentary: str = None) -> str:
    """Generate a post using the FastAPI backend."""
    try:
        # Show a spinner while generating
        with st.spinner('Generating your post... This may take a minute...'):
            # Add a longer timeout to prevent hanging
            response = requests.post(
                f"{BACKEND_URL}/api/generate-post",
                json={"description": description, "content_url": content_url, "commentary": commentary},
                timeout=None  # 2 minute timeout
            )
            response.raise_for_status()
            data = response.json()
            logger.debug(f"API response: {data}")
            return data.get("post")
    except requests.Timeout:
        logger.error("Request to generate post timed out")
        st.error("The request took too long. Please try again. If this persists, try with a shorter description.")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to backend server")
        st.error("Could not connect to the server. Please make sure the backend is running.")
        return None
    except Exception as e:
        logger.error(f"Failed to generate post: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
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
    st.title("LinkedIn Content Generator")
    
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

    # User Context Configuration
    st.sidebar.header("User Context")
    with st.sidebar.expander("Professional Information", expanded=True):
        industry = st.text_input("Industry", value=st.session_state.get("industry", ""))
        role = st.text_input("Role", value=st.session_state.get("role", ""))
        expertise = st.text_input("Expertise Areas (comma-separated)", value=st.session_state.get("expertise", ""))
        years_exp = st.number_input("Years of Experience", min_value=0, max_value=50, value=st.session_state.get("years_exp", 0))
        
    with st.sidebar.expander("Content Preferences", expanded=True):
        content_style = st.selectbox(
            "Content Style",
            ["professional", "casual", "academic"],
            index=["professional", "casual", "academic"].index(st.session_state.get("content_style", "professional"))
        )
        target_audience = st.text_input("Target Audience", value=st.session_state.get("target_audience", "industry professionals"))
        preferred_hashtags = st.text_input("Preferred Hashtags (comma-separated)", value=st.session_state.get("hashtags", ""))
        
    with st.sidebar.expander("Commentary Style", expanded=True):
        commentary_style = st.selectbox(
            "Commentary Style",
            ["analytical", "opinionated", "balanced"],
            index=["analytical", "opinionated", "balanced"].index(st.session_state.get("commentary_style", "analytical"))
        )
        
    # Personality Configuration
    st.sidebar.header("Personality Configuration")
    formality = st.sidebar.slider("Formality Level", 0.0, 1.0, 0.7)
    enthusiasm = st.sidebar.slider("Enthusiasm Level", 0.0, 1.0, 0.8)
    humor = st.sidebar.slider("Humor Level", 0.0, 1.0, 0.5)
    expertise = st.sidebar.slider("Expertise Level", 0.0, 1.0, 0.9)
    
    # Test values toggle
    use_test = st.checkbox("Use test values", value=st.session_state.use_test_values)
    if use_test != st.session_state.use_test_values:
        st.session_state.use_test_values = use_test
        if use_test:
            test_values = get_test_values()
            st.session_state.description = test_values["description"]
    
    # Content Input
    content_type = st.radio("Choose content type:", ["Description", "URL"])
    
    # Post generation form
    with st.form("post_form"):
        if content_type == "Description":
            description = st.text_area(
                "Enter your post description",
                value=st.session_state.description,
                height=150
            )
        else:
            content_url = st.text_input("Enter content URL (article or video):")
            
        # Personal Commentary
        commentary = st.text_area(
            "Add your personal commentary or opinion (optional)",
            height=100
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
            if content_type == "Description" and description:
                with st.spinner("Generating post..."):
                    generated_post = generate_post(description=description, commentary=commentary)
                    if generated_post:
                        st.session_state.description = generated_post
                        st.success("Post generated successfully!")
                    else:
                        st.error("Failed to generate post")
            elif content_type == "URL" and content_url:
                with st.spinner("Generating post..."):
                    generated_post = generate_post(content_url=content_url, commentary=commentary)
                    if generated_post:
                        st.session_state.description = generated_post
                        st.success("Post generated successfully!")
                    else:
                        st.error("Failed to generate post")
            else:
                st.warning("Please enter a description or content URL")
    
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
