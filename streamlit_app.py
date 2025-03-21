import streamlit as st
import requests
from PIL import Image
import io
import os
from dotenv import load_dotenv
import webbrowser

# Load environment variables
load_dotenv()

# Configure the page
st.set_page_config(
    page_title="LinkedIn Post Assistant",
    page_icon="💼",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        margin-top: 10px;
        background-color: #0077B5;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #006097;
    }
    .main {
        padding: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Title and description
st.title("💼 LinkedIn Post Assistant")
st.markdown("""
    Create professional LinkedIn posts with AI assistance. Upload an image, add a description,
    and let our AI generate an engaging post for you.
    """)

# Initialize session state for authentication
if 'linkedin_authenticated' not in st.session_state:
    st.session_state.linkedin_authenticated = False

# LinkedIn Authentication
if not st.session_state.linkedin_authenticated:
    st.subheader("🔑 LinkedIn Authentication")
    if st.button("Connect with LinkedIn"):
        try:
            response = requests.get("http://localhost:8000/api/auth/linkedin")
            if response.status_code == 200:
                auth_url = response.json()["auth_url"]
                webbrowser.open(auth_url)
                st.info("Please complete the LinkedIn authentication in your browser.")
            else:
                st.error("Failed to start LinkedIn authentication.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    
    # Check for authentication success using st.query_params
    query_params = st.query_params
    if "auth_success" in query_params:
        st.session_state.linkedin_authenticated = True
        st.success("Successfully authenticated with LinkedIn!")
    elif "auth_error" in query_params:
        st.error(f"Authentication failed: {query_params['auth_error']}")
    
    st.stop()

# Create two columns for the main content
col1, col2 = st.columns([1, 1])

# Initialize session state for image_url if it doesn't exist
if 'image_url' not in st.session_state:
    st.session_state.image_url = None

with col1:
    st.subheader("📝 Post Details")
    
    # Add checkbox for using test content
    use_test_content = st.checkbox("Use test content (no AI generation)", value=False)
    
    if not use_test_content:
        # Image upload
        uploaded_file = st.file_uploader("Upload an image (optional)", type=["jpg", "jpeg", "png"])
        
        # Description input
        description = st.text_area(
            "Describe your post",
            placeholder="Enter a brief description of what you want to post about...",
            height=150
        )
        
        # Generate button
        if st.button("Generate Post"):
            if not description:
                st.error("Please enter a description for your post.")
            else:
                with st.spinner("Generating your post..."):
                    try:
                        # Upload image if provided
                        if uploaded_file:
                            files = {"file": uploaded_file}
                            response = requests.post("http://localhost:8000/api/upload-image", files=files)
                            if response.status_code == 200:
                                st.session_state.image_url = response.json()["location"]
                            else:
                                st.error(f"Failed to upload image. Status code: {response.status_code}")
                                st.error(f"Error details: {response.text}")
                                st.session_state.image_url = None
                        else:
                            st.session_state.image_url = None
                        
                        # Generate post
                        response = requests.post(
                            "http://localhost:8000/api/generate-post",
                            json={"description": description, "image_url": st.session_state.image_url}
                        )
                        
                        if response.status_code == 200:
                            generated_post = response.json()["post"]
                            st.session_state.generated_post = generated_post
                        else:
                            st.error(f"Failed to generate post. Status code: {response.status_code}")
                            st.error(f"Error details: {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("Could not connect to the backend server. Make sure it's running on http://localhost:8000")
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
    else:
        # Load test content
        try:
            # Read test caption
            with open("tests/caption.txt", "r") as f:
                test_caption = f.read()
            
            # Set test image path
            test_image = "tests/images/Screenshot 2025-03-21 at 18.48.51.png"
            
            if os.path.exists(test_image):
                st.image(test_image, caption="Test Image", use_column_width=True)
                st.session_state.image_url = test_image
                st.session_state.generated_post = test_caption
                st.success("Test content loaded successfully!")
            else:
                st.error("Test image not found. Please check the file path.")
        except Exception as e:
            st.error(f"Error loading test content: {str(e)}")

with col2:
    st.subheader("✨ Generated Post")
    
    if "generated_post" in st.session_state:
        st.text_area(
            "Generated Post",
            value=st.session_state.generated_post,
            height=200,
            disabled=True
        )
        
        # Preview section
        st.subheader("👁️ Preview")
        if st.session_state.image_url:
            if use_test_content:
                st.image(st.session_state.image_url, caption="Post Image", use_column_width=True)
            else:
                st.image(uploaded_file, caption="Post Image", use_column_width=True)
        
        # Post to LinkedIn button
        if st.button("Post to LinkedIn"):
            with st.spinner("Posting to LinkedIn..."):
                try:
                    response = requests.post(
                        "http://localhost:8000/api/post-to-linkedin",
                        json={
                            "description": st.session_state.generated_post,
                            "image_url": st.session_state.image_url
                        }
                    )
                    
                    if response.status_code == 200:
                        st.success("Post successfully published to LinkedIn!")
                    else:
                        st.error(f"Failed to post to LinkedIn. Status code: {response.status_code}")
                        st.error(f"Error details: {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the backend server. Make sure it's running on http://localhost:8000")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
    else:
        st.info("Your generated post will appear here.")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Made with ❤️ using FastAPI and Streamlit</p>
        <p>Powered by Deepseek AI</p>
    </div>
    """, unsafe_allow_html=True)
