# LinkedIn Post Assistant

An AI-powered LinkedIn post generator that helps you create professional posts with images.

## Features

- Upload images for your LinkedIn posts
- Generate professional LinkedIn posts using AI
- Preview posts before publishing
- Optional LinkedIn integration for direct posting

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys:
   ```
   DEEPSEEK_API_KEY=your_api_key_here
   LINKEDIN_CLIENT_ID=your_client_id_here
   LINKEDIN_CLIENT_SECRET=your_client_secret_here
   ```

## Running the Application

1. Start the FastAPI backend:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Start the Streamlit frontend:
   ```bash
   streamlit run streamlit_app.py
   ```

## Project Structure

- `app/`: FastAPI backend application
- `services/`: Business logic and external service integrations
- `routes/`: API endpoints
- `streamlit_app.py`: Streamlit frontend application

## Technologies Used

- FastAPI
- Streamlit
- Deepseek API
- LinkedIn API
- Python 3.8+