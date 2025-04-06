# LinkedIn Bot

A Python application that automates posting to LinkedIn using AI-generated content. Built with FastAPI, Streamlit, and the LinkedIn API.

## Features

- AI-powered content generation
- LinkedIn authentication using OpenID Connect
- Automated posting to LinkedIn
- Modern web interface with Streamlit
- Secure token management
- Image upload support

## Prerequisites

- Python 3.10+
- LinkedIn Developer Account
- DeepSeek API Key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/linkedinbot.git
cd linkedinbot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your credentials:
```env
DEEPSEEK_API_KEY=your_deepseek_api_key
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/api/auth/callback
```

## Usage

1. Start the FastAPI backend:
```bash
uvicorn app.main:app --reload --port 8000
```

2. Start the Streamlit frontend:
```bash
streamlit run streamlit_app.py
```

3. Open your browser and navigate to:
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000

## Project Structure

```
linkedinbot/
├── app/
│   ├── main.py              # FastAPI application
│   └── routes/              # API routes
├── services/
│   ├── linkedin_service.py  # LinkedIn API integration
│   └── deepseek_service.py  # AI content generation
├── streamlit_app.py         # Streamlit frontend
├── requirements.txt         # Python dependencies
└── .env                     # Environment variables
```

## API Endpoints

- `GET /api/auth/linkedin` - Start LinkedIn OAuth flow
- `GET /api/auth/callback` - OAuth callback handler
- `POST /api/generate-post` - Generate AI content
- `POST /api/post-to-linkedin` - Post content to LinkedIn

## Security

- Environment variables for sensitive credentials
- Secure token storage
- OAuth 2.0 authentication
- Input validation and sanitization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.