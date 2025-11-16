# Bomb Hunt Game - Setup Instructions

## Overview
A turn-based strategy game with LLM-generated narratives where you compete against an AI opponent.

## Prerequisites
- Python 3.8 to 3.13
- Gemini API key from Google AI Studio

## Installation

### 1. Set up virtual environment
```bash
cd Junction-EvilInc   # change directory to project folder

# Create virtual environment
python3 -m venv venv  # or: python -m venv venv

# Activate virtual environment
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API

Create a `.env` file in the project root:
```bash
cp .env.example .env
```

#### Option A: Google Cloud Vertex AI (Recommended for Google Cloud users)

Edit `.env` and configure:
```
USE_VERTEX_AI=true
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.0-flash-exp
```

**Setup steps:**
1. Ensure you have a Google Cloud project with Vertex AI API enabled
2. Authenticate with gcloud: `gcloud auth application-default login`
3. Add your project ID to `.env`

#### Option B: Google AI Studio (For free API keys)

Edit `.env` and configure:
```
USE_VERTEX_AI=false
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-2.0-flash-exp
```

**Get your API key:**
1. Go to https://aistudio.google.com/
2. Click "Get API key"
3. Create a new API key
4. Copy and paste it into `.env`

**Security Note:** The `.env` file is in `.gitignore` and will NOT be committed to git.

## Running the Game

```bash

# Activate virtual environment if not already activated
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

python3 main.py               # or: python main.py

```

## Game Flow

1. **Opening Story**: LLM generates a unique mission briefing
2. **Difficulty Selection**: Choose Easy (5x5), Medium (10x10), or Hard (20x20)
3. **Bomb Placement**: Hide your beacon on the grid
4. **Dialog Phase**: Exchange hints with the AI (both can lie!)
5. **Turn-Based Gameplay**: Find the AI's artifact before it finds your beacon
6. **Ending Story**: LLM generates an outcome-based conclusion

## Features

- **Dynamic Narratives**: Each playthrough has a unique story
- **AI vs Humanity Theme**: Stories explore utopia/dystopia perspectives
- **Outcome-Based Endings**: Your victory or defeat shapes the story conclusion
- **Strategic Gameplay**: Use hints wisely - both you and the AI can lie!

## Troubleshooting

### API Key Issues
- Ensure your `.env` file exists and contains `GEMINI_API_KEY=your-key`
- No quotes needed around the API key in `.env`
- Check your API quota at https://aistudio.google.com/
- Verify the key has no extra spaces

### Import Errors
```bash
pip install --upgrade google-generativeai pygame
```

### Story Generation Errors
- Check your internet connection
- Verify API key is valid
- Ensure you haven't exceeded API rate limits

