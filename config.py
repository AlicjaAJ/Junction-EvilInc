"""
Configuration Module

Loads configuration from environment variables for security.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Gemini API Configuration
USE_VERTEX_AI = os.getenv("USE_VERTEX_AI", "false").lower() == "true"

if USE_VERTEX_AI:
    # Google Cloud Vertex AI configuration
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
    LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
    
    if not PROJECT_ID:
        raise ValueError(
            "GOOGLE_CLOUD_PROJECT not found in environment variables. "
            "Please add your Google Cloud project ID to .env file. "
            "See .env.example for template."
        )
    
    GEMINI_API_KEY = None  # Not used for Vertex AI
else:
    # Google AI Studio configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
    PROJECT_ID = None
    LOCATION = None
    
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY not found in environment variables. "
            "Please create a .env file with your API key. "
            "See .env.example for template."
        )

