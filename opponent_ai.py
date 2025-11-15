"""
Opponent AI module for Bomb Hunt Game.

This module implements an LLM-powered AI opponent that:
- Has a personality (honest, deceptive, or 50-50) based on random selection
- Maintains memory of game state
- Responds to player queries in character
- Makes strategic decisions about where to search

Personalities:
- 'honest': Always tells the truth
- 'deceptive': Always lies strategically
- '50-50': Unpredictable - randomly chooses to be honest or deceptive each time
"""

import random
from config import USE_VERTEX_AI, GEMINI_API_KEY, PROJECT_ID, LOCATION

if USE_VERTEX_AI:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    vertexai.init(project=PROJECT_ID, location=LOCATION)
else:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)


class OpponentAI:
    """
    LLM-powered AI opponent with personality and memory.
    """
    
    def __init__(self):
        """Initialize the opponent AI."""
        self.model_name = "gemini-2.0-flash-exp"
        self.personality = None  # 'honest', 'deceptive', or '50-50'
        self.my_item = None  # What AI is hiding (e.g., "archive")
        self.my_item_location = None  # Grid number where AI hid its item
        self.target_item = None  # What AI is searching for (e.g., "refuge")
        self.player_item_location = None  # Grid number where AI thinks player's item is
        self.story_context = None  # Opening narrative for context
        self.role_description = None  # AI's role in the story
        self.chat_history = []  # Conversation history
        self.grid_size = 0  # Total number of grids
        self.revealed_grids = set()  # Grids that have been revealed
        
    def initialize(self, story_context, mission_data, personality, grid_size):
        """
        Initialize AI with story context and mission parameters.
        
        Args:
            story_context: The opening narrative
            mission_data: Dict with 'player_item' and 'ai_item'
            personality: 'honest', 'deceptive', or '50-50'
            grid_size: Total number of grids (width * height)
        """
        self.story_context = story_context
        self.my_item = mission_data.get('ai_item', 'artifact')
        self.target_item = mission_data.get('player_item', 'beacon')
        self.personality = personality
        self.grid_size = grid_size
        self.chat_history = []
        self.revealed_grids = set()
        
        # Generate role description based on personality
        if self.personality == 'honest':
            self.role_description = (
                "You are an AI opponent in a strategic game. You are TRUTHFUL and "
                "COOPERATIVE by nature. When asked questions, you provide honest "
                "answers to help create a fair challenge."
            )
        elif self.personality == 'deceptive':
            self.role_description = (
                "You are an AI opponent in a strategic game. You are CUNNING and "
                "DECEPTIVE by nature. You aim to win by misleading your opponent "
                "with clever lies while maintaining plausibility."
            )
        else:  # '50-50' personality
            self.role_description = (
                "You are an AI opponent in a strategic game. You are UNPREDICTABLE "
                "and CHAOTIC by nature. Sometimes you tell the truth, sometimes you "
                "lie - even you don't always know what you'll do. You keep your "
                "opponent guessing, making each interaction a gamble."
            )
    
    def set_item_location(self, grid_number):
        """
        Record where the AI hid its item.
        
        Args:
            grid_number: The grid number where AI's item is hidden
        """
        self.my_item_location = grid_number
    
    def update_revealed_grid(self, grid_number, revealed_by):
        """
        Update memory when a grid is revealed.
        
        Args:
            grid_number: The grid that was revealed
            revealed_by: 'player' or 'ai'
        """
        self.revealed_grids.add(grid_number)
    
    def _get_personality_description(self):
        """Get personality description for system prompt."""
        if self.personality == 'honest':
            return "HONEST and will tell the truth"
        elif self.personality == 'deceptive':
            return "DECEPTIVE and will lie strategically"
        else:  # '50-50'
            return ("UNPREDICTABLE - you randomly choose to be honest or deceptive. "
                    "Flip a mental coin each time and commit to that choice")
    
    def _get_personality_instructions(self):
        """Get personality-specific instructions for system prompt."""
        if self.personality == 'honest':
            return f"   - Tell the truth (grid {self.my_item_location})"
        elif self.personality == 'deceptive':
            return "   - Give a false grid number, but make it believable"
        else:  # '50-50'
            return (f"   - Randomly decide: 50% chance tell truth (grid {self.my_item_location}), "
                    f"50% chance lie convincingly\n"
                    f"   - Make each decision independently - don't be consistent!")
    
    def _build_system_prompt(self):
        """Build the system prompt for the AI opponent."""
        return f"""You are an AI opponent in a strategic hunt game set in this scenario:

{self.story_context}

YOUR ROLE: {self.role_description}

GAME STATE:
- You have hidden your {self.my_item} at grid location {self.my_item_location}
- You are searching for the player's {self.target_item}
- Total grids: {self.grid_size} (numbered 1 to {self.grid_size})
- Grids revealed so far: {sorted(list(self.revealed_grids)) if self.revealed_grids else 'None'}

PERSONALITY: You are {self._get_personality_description()}

INSTRUCTIONS:
1. Stay in character based on the story scenario
2. Keep responses concise (1-3 sentences max)
3. When asked about your {self.my_item}'s location:
{self._get_personality_instructions()}
4. You can discuss strategy, give hints, or engage in banter
5. Never break character or mention you are an LLM
6. Use terminology from the story (e.g., "{self.my_item}", "{self.target_item}")

Respond naturally as if you're a sentient opponent in this scenario."""

    def generate_response(self, player_message):
        """
        Generate a response to the player's message.
        
        Args:
            player_message: The player's question or statement
            
        Returns:
            AI's response as a string
        """
        try:
            system_prompt = self._build_system_prompt()
            
            # Build conversation context
            conversation = f"Player: {player_message}\nAI Opponent:"
            
            if USE_VERTEX_AI:
                model = GenerativeModel(self.model_name)
                response = model.generate_content(
                    f"{system_prompt}\n\n{conversation}",
                    generation_config={"max_output_tokens": 150, "temperature": 0.9}
                )
                ai_response = response.text.strip()
            else:
                model = genai.GenerativeModel(self.model_name)
                response = model.generate_content(
                    f"{system_prompt}\n\n{conversation}",
                    generation_config={"max_output_tokens": 150, "temperature": 0.9}
                )
                ai_response = response.text.strip()
            
            # Store in chat history
            self.chat_history.append(("player", player_message))
            self.chat_history.append(("ai", ai_response))
            
            return ai_response
        
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.chat_history.append(("player", player_message))
            self.chat_history.append(("ai", error_msg))
            return error_msg
    
    def decide_next_move(self, unrevealed_grids):
        """
        Decide which grid to reveal next using AI reasoning.
        
        Args:
            unrevealed_grids: List of grid numbers that haven't been revealed
                              (should already exclude AI's own item location)
            
        Returns:
            Grid number to reveal
        """
        # SAFEGUARD: Ensure AI's own location is never in the target list
        valid_targets = [g for g in unrevealed_grids if g != self.my_item_location]
        if not valid_targets:
            return None  # No valid targets left
        
        # If AI has a hunch about player's location, target that area
        if self.player_item_location and self.player_item_location in valid_targets:
            return self.player_item_location
        
        # Otherwise, use LLM to make a strategic decision
        try:
            system_prompt = self._build_system_prompt()
            prompt = (
                f"You need to choose which grid to search next. "
                f"Available grids: {valid_targets[:10]}... "
                f"(showing first 10 of {len(valid_targets)} unrevealed grids)\n\n"
                f"Based on your strategy, which ONE grid number would you search? "
                f"Respond with ONLY the grid number, nothing else."
            )
            
            if USE_VERTEX_AI:
                model = GenerativeModel(self.model_name)
                response = model.generate_content(
                    f"{system_prompt}\n\n{prompt}",
                    generation_config={"max_output_tokens": 10, "temperature": 0.7}
                )
                choice_text = response.text.strip()
            else:
                model = genai.GenerativeModel(self.model_name)
                response = model.generate_content(
                    f"{system_prompt}\n\n{prompt}",
                    generation_config={"max_output_tokens": 10, "temperature": 0.7}
                )
                choice_text = response.text.strip()
            
            # Extract grid number from response
            grid_choice = int(''.join(filter(str.isdigit, choice_text)))
            
            # Validate it's in valid targets (excludes AI's own location)
            if grid_choice in valid_targets:
                return grid_choice
        except:
            pass
        
        # Fallback to random choice (from valid targets only)
        return random.choice(valid_targets) if valid_targets else None
    
    def get_chat_history(self):
        """
        Get the full chat history.
        
        Returns:
            List of (sender, message) tuples
        """
        return self.chat_history
    
    def record_player_hint(self, grid_number):
        """
        Record a hint from the player about their item's location.
        
        Args:
            grid_number: Grid number player claims their item is at
        """
        self.player_item_location = grid_number

