"""
Story Generator Module

Uses Gemini LLM to generate dynamic narratives for the game.
Creates opening stories and outcome-based endings.
Supports both Google AI Studio and Google Cloud Vertex AI.
"""

from config import (
    USE_VERTEX_AI, GEMINI_API_KEY, GEMINI_MODEL,
    PROJECT_ID, LOCATION
)

if USE_VERTEX_AI:
    import vertexai
    from vertexai.generative_models import GenerativeModel
else:
    import google.generativeai as genai


class StoryGenerator:
    """Generates narrative content using Gemini LLM."""

    def __init__(self):
        """Initialize the Gemini API client."""
        if USE_VERTEX_AI:
            # Initialize Vertex AI
            vertexai.init(project=PROJECT_ID, location=LOCATION)
            self.use_vertex = True
            # Preferred model order (primary + fallbacks)
            self.model_names = [
                GEMINI_MODEL,
                "gemini-1.5-pro-preview-0409",
                "gemini-1.5-flash",
            ]
        else:
            # Initialize Google AI Studio
            genai.configure(api_key=GEMINI_API_KEY)
            self.use_vertex = False
            self.model_names = [
                GEMINI_MODEL,
                "gemini-2.0-flash-exp",
                "gemini-1.5-flash",
            ]

    def generate_opening_story(self):
        """
        Generate an opening story that sets up the game scenario.

        Returns:
            Tuple of (narrative_text, mission_data_dict) containing:
            - narrative_text: The story to display to the player
            - mission_data_dict: Dictionary with 'player_item' and 'ai_item' keys
        """
        system_context = """You are the narrator of a tactical strategy game set in an 
AI vs Humanity conflict. Your role is to create immersive mission briefings that 
place the player directly into urgent scenarios. You speak with authority and 
urgency, never offering options or explaining your process. You ARE the voice of 
the resistance/command/network briefing the operative."""

        prompt = """The year is 2157. You are briefing operative on a critical mission.

IMPORTANT: Structure your response EXACTLY like this:

[PLAYER_ITEM: single word/short phrase for what player must protect]
[AI_ITEM: single word/short phrase for what player must find]
[NARRATIVE]
Your mission briefing text here...
[/NARRATIVE]

Example format:
[PLAYER_ITEM: beacon]
[AI_ITEM: data core]
[NARRATIVE]
You are operative Nightingale in the abandoned Data Nexus...
[/NARRATIVE]

Write a 40-60 word mission briefing in second person ("You are...", "Your mission...").

SETTING (choose one, vary each time):
- Neural network infiltration in the Matrix
- Underground bunker defending last human archive
- Space station racing against AI fleet
- Quantum realm where time behaves strangely
- Abandoned megacity with rogue AI presence
- Deep sea facility hiding humanity's backup

MISSION STRUCTURE (always include both):
1. LOCATE: Find [artifact/data/coordinates/person/code/relic] before AI finds it
2. PROTECT: Keep your [beacon/base/signal/transmitter/node/coordinates] hidden from AI

Use creative terminology. Examples:
- Player items: beacon, transmitter, signal, coordinates, hideout, refuge, node, safehouse
- AI items: artifact, data core, cipher, relic, coordinates, archive, prototype, keystone

TONE: Urgent, declarative, immersive. You are IN the world, not describing it.

END with immediate call to action: "Your mission begins now." or "Time is running out."
"""

        # Combine system context with prompt
        full_prompt = f"{system_context}\n\n{prompt}"
        
        text = self._generate_text(full_prompt)
        
        # Parse the structured response
        return self._parse_opening_response(text)
    
    def _parse_opening_response(self, text):
        """
        Parse the LLM response to extract mission data and narrative.
        
        Args:
            text: Raw LLM response with [PLAYER_ITEM], [AI_ITEM], and [NARRATIVE] tags
            
        Returns:
            Tuple of (narrative_text, mission_data_dict)
        """
        import re
        
        # Extract player item
        player_match = re.search(r'\[PLAYER_ITEM:\s*([^\]]+)\]', text)
        player_item = player_match.group(1).strip() if player_match else "beacon"
        
        # Extract AI item  
        ai_match = re.search(r'\[AI_ITEM:\s*([^\]]+)\]', text)
        ai_item = ai_match.group(1).strip() if ai_match else "artifact"
        
        # Extract narrative
        narrative_match = re.search(r'\[NARRATIVE\](.*?)\[/NARRATIVE\]', text, re.DOTALL)
        narrative = narrative_match.group(1).strip() if narrative_match else text
        
        # Clean up narrative in case tags are visible
        narrative = re.sub(r'\[PLAYER_ITEM:[^\]]+\]', '', narrative)
        narrative = re.sub(r'\[AI_ITEM:[^\]]+\]', '', narrative)
        narrative = re.sub(r'\[/?NARRATIVE\]', '', narrative)
        narrative = narrative.strip()
        
        mission_data = {
            'player_item': player_item,
            'ai_item': ai_item
        }
        
        return narrative, mission_data

    def generate_ending_story(self, opening_story, player_won):
        """
        Generate an ending story based on the game outcome.

        Args:
            opening_story: The opening story that was shown
            player_won: Boolean indicating if player won

        Returns:
            String containing the ending narrative
        """
        outcome = "SUCCESS" if player_won else "FAILURE"
        
        system_context = """You are the narrator concluding a tactical mission. 
You speak with authority about what just happened and its consequences. 
You ARE the voice revealing the outcome, not explaining or proposing anything. 
Write in past tense about completed events."""

        prompt = f"""MISSION BRIEFING WAS:
{opening_story}

MISSION OUTCOME: {outcome}
{"Operative located target before AI. Mission objectives achieved." if player_won 
 else "AI discovered operative's position first. Mission compromised."}

Write a 15-30 word mission report/aftermath in second person past tense ("You secured...", "The AI found...").

SHOW THE CONSEQUENCES:
- What happened immediately after
- Impact on humanity's situation
- {"New hope/opportunity that emerged" if player_won else "What was lost but what remains"}
- Emotional weight of the outcome

TONE: {"Triumphant but grounded" if player_won else "Somber but resilient"}

END with a final statement about humanity's status or future.

Write the aftermath directly. No preamble like "here's the ending" - just the mission report itself."""

        # Combine system context with prompt
        full_prompt = f"{system_context}\n\n{prompt}"
        
        return self._generate_text(full_prompt)

    def _generate_text(self, prompt):
        """
        Try generating text using preferred models with graceful fallback.

        Args:
            prompt: Prompt string to send to the model

        Returns:
            Generated text string

        Raises:
            RuntimeError if all models fail
        """
        last_error = None
        for model_name in self.model_names:
            try:
                if self.use_vertex:
                    model = GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                else:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                if response and getattr(response, "text", None):
                    return response.text.strip()
            except Exception as exc:
                last_error = f"{model_name}: {exc}"
                continue
        raise RuntimeError(last_error or "All Gemini text models failed")

