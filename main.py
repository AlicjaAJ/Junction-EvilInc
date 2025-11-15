"""
Bomb Hunt Game - Main Game Module

A turn-based strategy game where a player competes against an AI to find
each other's hidden bombs. Features include:
- LLM-generated dynamic narratives (AI vs Humanity theme)
- Difficulty selection (Easy, Medium, Hard)
- Grid-based bomb placement
- Turn-based gameplay with color-coded reveals
- Dialog system for hints (with honesty/lie mechanics)
- Grid numbering for easy identification
- Outcome-based story endings

Game Flow:
1. Opening story generation (LLM)
2. Select difficulty level
3. Player places bomb (beacon)
4. AI places bomb (artifact)
5. Dialog phase (exchange hints)
6. Turn-based reveal phase
7. Winner determination
8. Ending story generation (LLM)
"""

import pygame
import random
import threading

from cell import Cell
from story_generator import StoryGenerator
from opponent_ai import OpponentAI


# Color constants for game visuals
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PLAYER_COLOR = (180, 220, 255)  # Light blue for player reveals
AI_COLOR = (255, 180, 180)  # Light red for AI reveals
WIN_COLOR = (180, 255, 180)  # Green for winning reveal (bomb found)
PANEL_COLOR = (200, 200, 200)  # Gray for side panel


class Grid:
    """
    Manages the game grid and game state.

    The grid is a 2D array of cells that can contain bombs or be empty.
    Handles bomb placement, cell revelation, victory detection, and rendering.
    """

    def run_status(self):
        """Check if the game is still running."""
        return self.running

    def __init__(self, width, height, cell_size):
        """
        Initialize the game grid.

        Args:
            width: Number of columns in the grid
            height: Number of rows in the grid
            cell_size: Pixel size of each cell for rendering
        """
        self.width = width
        self.height = height
        self.cell_size = cell_size
        # Create 2D array of cells
        self.cells = [[Cell() for _ in range(height)] for _ in range(width)]
        self.running = True
        self.player_bomb_placed = False
        self.ai_bomb_placed = False
        self.player_turn = True
        self.victor = None  # 'Player' or 'AI' when game ends

    def place_player_bomb(self, col, row):
        """
        Place the player's bomb at the specified location.

        Args:
            col: Column index (0-based)
            row: Row index (0-based)

        Returns:
            True if bomb was placed successfully, False otherwise
        """
        # Only allow placement if player hasn't placed yet and cell is empty
        if not self.player_bomb_placed and not self.cells[col][row].item_type:
            self.cells[col][row].add_item(('P', 'B'))  # 'P' = Player, 'B' = Bomb
            self.player_bomb_placed = True
            return True
        return False

    def place_ai_bomb(self):
        """
        Place the AI's bomb at a random empty location.

        This ensures AI and Player items are NEVER in the same location because:
        1. Player places their item first
        2. AI only chooses from cells where item_type is None/Empty
        3. Player's cell is no longer empty, so it's excluded automatically
        
        This prevents same-location collision without the AI "knowing" where player is.
        """
        if self.ai_bomb_placed:
            return
        # Find all empty cells (excludes player's already-placed item)
        available = [(x, y) for x in range(self.width) for y in range(self.height)
                     if not self.cells[x][y].item_type]
        if available:
            col, row = random.choice(available)
            self.cells[col][row].add_item(('A', 'B'))  # 'A' = AI, 'B' = Bomb
            self.ai_bomb_placed = True

    def reveal_cell(self, col, row, revealed_by):
        """
        Reveal a cell and check for victory condition.

        Args:
            col: Column index
            row: Row index
            revealed_by: 'player' or 'ai' - who revealed this cell

        Returns:
            True if cell was revealed successfully, False otherwise
        """
        # Validate coordinates
        if col < 0 or col >= self.width or row < 0 or row >= self.height:
            return False
        cell = self.cells[col][row]
        # Don't reveal already revealed cells
        if cell.revealed:
            return False
        
        # CRITICAL: Prevent players from revealing their own item location
        # This ensures both items stay "in play" until opponent finds them
        if cell.item_type:
            item_owner = cell.item_type[0]
            if revealed_by == 'player' and item_owner == 'P':
                # Player trying to reveal their own item - not allowed!
                return False
            elif revealed_by == 'ai' and item_owner == 'A':
                # AI trying to reveal its own item - not allowed!
                return False
        
        cell.reveal(revealed_by)
        # Check if opponent's bomb was found (victory condition)
        # Player wins by finding AI's bomb ('A'), AI wins by finding Player's bomb ('P')
        if cell.item_type:
            item_owner = cell.item_type[0]  # 'P' for player's item, 'A' for AI's item
            if revealed_by == 'player' and item_owner == 'A':
                # Player found AI's item - Player wins!
                self.victor = 'Player'
            elif revealed_by == 'ai' and item_owner == 'P':
                # AI found Player's item - AI wins!
                self.victor = 'AI'
        return True

    def reset(self):
        """
        Reset the grid to initial state for a new game.

        Clears all cells and resets game state flags.
        """
        self.cells = [[Cell() for _ in range(self.height)]
                       for _ in range(self.width)]
        self.running = True
        self.player_bomb_placed = False
        self.ai_bomb_placed = False
        self.player_turn = True
        self.victor = None

    def get_unrevealed_cells(self):
        """
        Get list of coordinates for all unrevealed cells.

        Returns:
            List of (col, row) tuples for unrevealed cells
        """
        return [(x, y) for x in range(self.width) for y in range(self.height)
                if not self.cells[x][y].revealed]

    def ai_reveal(self, target_grid_num=None):
        """
        AI reveals a cell, either a specific target or random.

        Args:
            target_grid_num: Optional grid number to reveal (from player hint).
                            If None, chooses randomly from unrevealed cells.

        Returns:
            True if a cell was revealed, False otherwise
        """
        # If player gave a hint, try to reveal that grid number
        if target_grid_num:
            col, row = self.get_coords_from_number(target_grid_num)
            if not self.cells[col][row].revealed:
                self.reveal_cell(col, row, 'ai')
                return True
        # Otherwise, choose randomly from unrevealed cells
        unrevealed = self.get_unrevealed_cells()
        if unrevealed:
            col, row = random.choice(unrevealed)
            self.reveal_cell(col, row, 'ai')
            return True
        return False

    def handle_click(self, x, y, game_state, x_offset=0, y_offset=0):
        """
        Handle mouse click on the grid.

        Args:
            x: Mouse x coordinate in pixels
            y: Mouse y coordinate in pixels
            game_state: Current game state ('bomb_placement' or 'player_turn')
            x_offset: Horizontal offset of the grid
            y_offset: Vertical offset of the grid

        Returns:
            Grid number if click was handled, False otherwise
        """
        # Adjust for grid offset
        adjusted_x = x - x_offset
        adjusted_y = y - y_offset
        # Convert pixel coordinates to grid coordinates
        col = adjusted_x // self.cell_size
        row = adjusted_y // self.cell_size
        # Validate coordinates
        if col < 0 or col >= self.width or row < 0 or row >= self.height:
            return False
        if game_state == 'bomb_placement':
            success = self.place_player_bomb(col, row)
            return self.get_grid_number(col, row) if success else False
        elif game_state == 'player_turn' and self.player_turn:
            if self.reveal_cell(col, row, 'player'):
                self.player_turn = False  # Switch to AI turn
                return self.get_grid_number(col, row)
        return False

    def get_grid_number(self, col, row):
        """
        Convert grid coordinates to a sequential grid number (1-indexed).

        Grid numbers are assigned left-to-right, top-to-bottom.
        Example for 5x5 grid: (0,0)=1, (4,0)=5, (0,1)=6, (4,4)=25

        Args:
            col: Column index (0-based)
            row: Row index (0-based)

        Returns:
            Grid number (1-indexed)
        """
        return row * self.width + col + 1

    def get_coords_from_number(self, grid_num):
        """
        Convert grid number to grid coordinates.

        Args:
            grid_num: Grid number (1-indexed)

        Returns:
            Tuple of (col, row) coordinates (0-indexed)
        """
        grid_num -= 1  # Convert to 0-indexed
        row = grid_num // self.width
        col = grid_num % self.width
        return col, row

    def get_ai_bomb_location(self):
        """
        Find the grid number where the AI's bomb is located.

        Returns:
            Grid number (1-indexed) or None if not found
        """
        for x in range(self.width):
            for y in range(self.height):
                if self.cells[x][y].item_type and self.cells[x][y].item_type[0] == 'A':
                    return self.get_grid_number(x, y)
        return None

    def get_player_bomb_location(self):
        """
        Find the grid number where the player's bomb is located.

        Returns:
            Grid number (1-indexed) or None if not found
        """
        for x in range(self.width):
            for y in range(self.height):
                if self.cells[x][y].item_type and self.cells[x][y].item_type[0] == 'P':
                    return self.get_grid_number(x, y)
        return None

    def draw(self, surface, font, small_font, x_offset=0, y_offset=0):
        """
        Render the grid on the given surface.

        Args:
            surface: Pygame surface to draw on
            font: Font for bomb letters (P/A)
            small_font: Font for grid numbers
            x_offset: Horizontal offset for centering the grid
            y_offset: Vertical offset for centering the grid
        """
        for x in range(self.width):
            for y in range(self.height):
                cell = self.cells[x][y]
                # Calculate cell rectangle position with offset
                rect = (x * self.cell_size + x_offset, y * self.cell_size + y_offset,
                        self.cell_size, self.cell_size)
                # Draw cell border
                pygame.draw.rect(surface, BLACK, rect, 1)
                # Draw grid number in top-left corner
                grid_num = self.get_grid_number(x, y)
                num_text = small_font.render(str(grid_num), True, (100, 100, 100))
                surface.blit(num_text, (x * self.cell_size + x_offset + 2,
                                        y * self.cell_size + y_offset + 2))
                # Draw revealed cells with appropriate color
                if cell.revealed:
                    # Green if bomb found (winning reveal)
                    if cell.item_type and cell.item_type[0] in ['P', 'A']:
                        color = WIN_COLOR
                    # Blue for player reveals, red for AI reveals
                    elif cell.revealed_by == 'player':
                        color = PLAYER_COLOR
                    else:
                        color = AI_COLOR
                    pygame.draw.rect(surface, color, rect)
                    # Draw bomb letter if cell contains a bomb
                    if cell.item_type:
                        text = font.render(cell.item_type[0], True, BLACK)
                        surface.blit(text, (x * self.cell_size + x_offset + 5,
                                            y * self.cell_size + y_offset + 5))




def check_button_click(x, y, button_rect):
    """
    Check if a point is within a button rectangle.

    Args:
        x: X coordinate of the point
        y: Y coordinate of the point
        button_rect: Tuple of (x, y, width, height) defining button bounds

    Returns:
        True if point is within button, False otherwise
    """
    return (button_rect[0] <= x <= button_rect[0] + button_rect[2] and
            button_rect[1] <= y <= button_rect[1] + button_rect[3])


def get_difficulty_size(difficulty):
    """
    Get grid size based on difficulty level.

    Args:
        difficulty: 'easy', 'medium', or 'hard'

    Returns:
        Grid dimension (width and height are the same)
    """
    base_size = 5
    if difficulty == 'easy':
        return base_size  # 5x5
    elif difficulty == 'medium':
        return base_size * 2  # 10x10
    elif difficulty == 'hard':
        return base_size * 4  # 20x20
    return base_size


def ai_honesty_check():
    """
    DEPRECATED: Previously used to determine AI honesty.
    Now replaced by AI personality system ('honest', 'deceptive', '50-50').
    
    This function is kept for backwards compatibility but is no longer used.
    
    Returns:
        True if AI is honest (50% chance), False if AI lies
    """
    return random.randint(1, 2) == 1


def wrap_text(text, font, max_width):
    """
    Wrap text to fit within a specified width.

    Args:
        text: Text to wrap
        font: Pygame font object
        max_width: Maximum width in pixels

    Returns:
        List of text lines that fit within max_width
    """
    words = text.split(' ')
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        if font.size(test_line)[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return lines


def draw_chat_sidebar(surface, x, y, width, height, opponent_ai, chat_input, chat_input_active,
                      ai_response_loading, font, small_font):
    """
    Draw the chat interface sidebar with proper text wrapping and scrolling.

    Args:
        surface: Pygame surface to draw on
        x: X position of chat sidebar
        y: Y position of chat sidebar
        width: Width of chat sidebar
        height: Height of chat sidebar
        opponent_ai: OpponentAI instance for chat history
        chat_input: Current user input text
        chat_input_active: Whether chat input is focused
        ai_response_loading: Whether AI is generating a response
        font: Regular font for chat text
        small_font: Small font for labels
    """
    # Background
    pygame.draw.rect(surface, (240, 240, 245), (x, y, width, height))
    pygame.draw.rect(surface, (100, 100, 120), (x, y, width, height), 2)
    
    # Title with message count
    msg_count = len(opponent_ai.get_chat_history())
    title_text = f"AI Opponent Chat ({msg_count // 2})"  # Divide by 2 for msg pairs
    title = font.render(title_text, True, (0, 0, 0))
    surface.blit(title, (x + 10, y + 10))
    
    # Chat history area
    chat_area_x = x + 5
    chat_area_y = y + 45
    chat_area_width = width - 10
    chat_area_height = height - 95
    pygame.draw.rect(surface, (255, 255, 255), (chat_area_x, chat_area_y, chat_area_width, chat_area_height))
    pygame.draw.rect(surface, (180, 180, 180), (chat_area_x, chat_area_y, chat_area_width, chat_area_height), 1)
    
    # Calculate all wrapped lines first to enable auto-scroll
    chat_history = opponent_ai.get_chat_history()
    all_lines = []
    line_height = 20
    text_margin = 10
    available_width = chat_area_width - 2 * text_margin
    
    # Show help text if no messages yet
    if not chat_history:
        help_lines = [
            "Click the input box below to chat",
            "with your AI opponent!",
            "",
            "Ask about strategy, request hints,",
            "or engage in conversation."
        ]
        for help_line in help_lines:
            all_lines.append((help_line, (120, 120, 120), None))
    
    for sender, message in chat_history:
        color = (20, 80, 180) if sender == 'player' else (180, 40, 40)
        bg_color = (230, 240, 255) if sender == 'player' else (255, 240, 230)
        prefix = "You: " if sender == 'player' else "AI: "
        
        # Wrap message with proper width
        wrapped = wrap_text(prefix + message, small_font, available_width)
        for i, line in enumerate(wrapped):
            all_lines.append((line, color, bg_color if i == 0 else None))
        # Add small gap between messages
        all_lines.append(("", (0, 0, 0), None))  # Empty line for spacing
    
    # Auto-scroll: show the most recent messages that fit
    total_height_needed = len(all_lines) * line_height
    start_line = max(0, len(all_lines) - int(chat_area_height / line_height))
    
    # Draw visible lines with background highlighting
    y_offset = chat_area_y + 5
    for line_data in all_lines[start_line:]:
        if y_offset + line_height > chat_area_y + chat_area_height - 5:
            break
        line, color, bg_color = line_data
        if line:  # Skip empty lines
            # Draw background for first line of each message
            if bg_color:
                bg_rect = pygame.Rect(chat_area_x + 5, y_offset - 2, 
                                     chat_area_width - 10, line_height)
                pygame.draw.rect(surface, bg_color, bg_rect)
            
            text_surf = small_font.render(line, True, color)
            # Clip text if it's still too long
            if text_surf.get_width() > available_width:
                # Truncate with ellipsis
                truncated = line[:int(len(line) * available_width / text_surf.get_width()) - 3] + "..."
                text_surf = small_font.render(truncated, True, color)
            surface.blit(text_surf, (chat_area_x + text_margin, y_offset))
        y_offset += line_height
    
    # Loading indicator
    if ai_response_loading:
        loading_text = small_font.render("AI is typing...", True, (150, 150, 150))
        surface.blit(loading_text, (chat_area_x + text_margin, y_offset))
    
    # Input box
    input_y = y + height - 45
    input_box_color = (100, 100, 250) if chat_input_active else (200, 200, 200)
    pygame.draw.rect(surface, (255, 255, 255), (x + 5, input_y, width - 10, 35))
    pygame.draw.rect(surface, input_box_color, (x + 5, input_y, width - 10, 35), 2)
    
    # Input text with wrapping/truncation
    if chat_input:
        # Wrap input text if too long
        input_width = width - 30
        wrapped_input = wrap_text(chat_input, small_font, input_width)
        # Show only the last line if multiple lines (most recent typing)
        display_text = wrapped_input[-1] if wrapped_input else chat_input
        input_surf = small_font.render(display_text, True, (0, 0, 0))
    else:
        input_surf = small_font.render("Type your message...", True, (150, 150, 150))
    surface.blit(input_surf, (x + 10, input_y + 8))


def run_game():
    """
    Main game loop and state management.

    Handles all game states:
    - story_opening: Display LLM-generated opening narrative
    - difficulty_selection: Player chooses difficulty
    - bomb_placement: Player places bomb (beacon), then AI places bomb (artifact)
    - dialog: Exchange hints between player and AI
    - player_turn: Turn-based gameplay
    - story_ending: Display outcome-based ending narrative
    - game_over: Show results and restart/quit options
    """
    # Initialize pygame
    pygame.init()
    # Game constants
    CELL_SIZE = 40  # Pixel size of each grid cell
    CHAT_PANEL_WIDTH = 400  # Width of chat sidebar on the right
    GRID_TOP_MARGIN = 60  # Space above grid for prompts
    STORY_WIDTH = 600  # Width for story display
    STORY_HEIGHT = 500  # Height for story display
    # Font setup
    font = pygame.font.SysFont(None, 24)  # Standard font for text
    prompt_font = pygame.font.SysFont(None, 32)  # Larger font for prompts
    button_font = pygame.font.SysFont(None, 28)  # Font for buttons
    small_font = pygame.font.SysFont(None, 16)  # Small font for grid numbers
    story_font = pygame.font.SysFont(None, 22)  # Font for story text
    # Initial window size (for story screen) - make it resizable
    INITIAL_WIDTH = STORY_WIDTH
    INITIAL_HEIGHT = STORY_HEIGHT
    window = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Bomb Hunt Game")
    # Track current window dimensions
    current_width = INITIAL_WIDTH
    current_height = INITIAL_HEIGHT
    # Initialize story generator and opponent AI
    story_gen = StoryGenerator()
    opponent_ai = OpponentAI()
    # Game state variables
    game_state = 'loading_story'
    difficulty = None
    grid = None
    GRID_WIDTH = 0
    GRID_HEIGHT = 0
    ai_turn_pending = False  # Flag for AI turn delay
    ai_personality = None  # 'honest', 'deceptive', or '50-50'
    # Story variables
    opening_story = None
    ending_story = None
    mission_data = None  # Dict with player_item and ai_item
    story_loading = False
    story_error = None
    # Chat interface variables
    chat_input = ""  # Current chat message being typed
    chat_input_active = False  # Whether chat input is focused
    chat_scroll_offset = 0  # Scroll position for chat history
    ai_response_loading = False  # Flag for when AI is generating response
    clock = pygame.time.Clock()
    running = True

    # Start loading opening story in background thread
    def load_opening_story():
        nonlocal opening_story, mission_data, story_loading, story_error, game_state
        story_loading = True
        try:
            opening_story, mission_data = story_gen.generate_opening_story()
            game_state = 'story_opening'
        except Exception as e:
            story_error = str(e)
            game_state = 'story_opening'
        story_loading = False

    threading.Thread(target=load_opening_story, daemon=True).start()
    # Main game loop
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Handle window resize
            if event.type == pygame.VIDEORESIZE:
                current_width = event.w
                current_height = event.h
                window = pygame.display.set_mode((current_width, current_height), pygame.RESIZABLE)
            # Handle keyboard input for chat
            if event.type == pygame.KEYDOWN:
                if chat_input_active and game_state in ['bomb_placement', 'player_turn']:
                    if event.key == pygame.K_RETURN and chat_input.strip() and not ai_response_loading:
                        # Submit chat message to opponent AI (only if not already loading)
                        user_message = chat_input.strip()
                        chat_input = ""
                        # Generate AI response in background thread
                        def get_ai_response():
                            nonlocal ai_response_loading
                            ai_response_loading = True
                            try:
                                opponent_ai.generate_response(user_message)
                            except Exception as e:
                                # Add error message to chat on failure
                                opponent_ai.chat_history.append(("player", user_message))
                                opponent_ai.chat_history.append(("ai", f"[Error: {str(e)}]"))
                            finally:
                                ai_response_loading = False
                        threading.Thread(target=get_ai_response, daemon=True).start()
                    elif event.key == pygame.K_BACKSPACE:
                        chat_input = chat_input[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        # Deactivate chat input
                        chat_input_active = False
                    elif len(chat_input) < 200 and event.unicode.isprintable():
                        # Increased limit and only allow printable characters
                        chat_input += event.unicode
            # Handle mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                # Story opening screen - begin mission button
                if game_state == 'story_opening':
                    if opening_story:
                        begin_rect = (current_width // 2 - 100, current_height - 80, 200, 50)
                        if check_button_click(x, y, begin_rect):
                            window = pygame.display.set_mode((400, 300), pygame.RESIZABLE)
                            current_width = 400
                            current_height = 300
                            game_state = 'difficulty_selection'
                # Difficulty selection screen
                elif game_state == 'difficulty_selection':
                    easy_rect = (100, 100, 200, 40)
                    medium_rect = (100, 150, 200, 40)
                    hard_rect = (100, 200, 200, 40)
                    if check_button_click(x, y, easy_rect):
                        difficulty = 'easy'
                        GRID_WIDTH = GRID_HEIGHT = get_difficulty_size(difficulty)
                        WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE + CHAT_PANEL_WIDTH + 20
                        WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE + GRID_TOP_MARGIN + 20
                        window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                        current_width = WINDOW_WIDTH
                        current_height = WINDOW_HEIGHT
                        grid = Grid(GRID_WIDTH, GRID_HEIGHT, CELL_SIZE)
                        # Initialize opponent AI with random personality
                        ai_personality = random.choice(['honest', 'deceptive', '50-50'])
                        opponent_ai.initialize(
                            opening_story, mission_data, ai_personality, GRID_WIDTH * GRID_HEIGHT
                        )
                        game_state = 'bomb_placement'
                        chat_input = ""
                        chat_input_active = False
                    elif check_button_click(x, y, medium_rect):
                        difficulty = 'medium'
                        GRID_WIDTH = GRID_HEIGHT = get_difficulty_size(difficulty)
                        WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE + CHAT_PANEL_WIDTH + 20
                        WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE + GRID_TOP_MARGIN + 20
                        window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                        current_width = WINDOW_WIDTH
                        current_height = WINDOW_HEIGHT
                        grid = Grid(GRID_WIDTH, GRID_HEIGHT, CELL_SIZE)
                        # Initialize opponent AI with random personality
                        ai_personality = random.choice(['honest', 'deceptive', '50-50'])
                        opponent_ai.initialize(
                            opening_story, mission_data, ai_personality, GRID_WIDTH * GRID_HEIGHT
                        )
                        game_state = 'bomb_placement'
                        chat_input = ""
                        chat_input_active = False
                    elif check_button_click(x, y, hard_rect):
                        difficulty = 'hard'
                        GRID_WIDTH = GRID_HEIGHT = get_difficulty_size(difficulty)
                        WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE + CHAT_PANEL_WIDTH + 20
                        WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE + GRID_TOP_MARGIN + 20
                        window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                        current_width = WINDOW_WIDTH
                        current_height = WINDOW_HEIGHT
                        grid = Grid(GRID_WIDTH, GRID_HEIGHT, CELL_SIZE)
                        # Initialize opponent AI with random personality
                        ai_personality = random.choice(['honest', 'deceptive', '50-50'])
                        opponent_ai.initialize(
                            opening_story, mission_data, ai_personality, GRID_WIDTH * GRID_HEIGHT
                        )
                        game_state = 'bomb_placement'
                        chat_input = ""
                        chat_input_active = False
                # Story ending screen - restart or quit
                elif game_state == 'story_ending':
                    if ending_story:
                        new_mission_rect = (current_width // 2 - 210, current_height - 80, 180, 50)
                        quit_rect = (current_width // 2 + 30, current_height - 80, 180, 50)
                        if check_button_click(x, y, new_mission_rect):
                            # Start a new game
                            grid.reset()
                            game_state = 'loading_story'
                            grid = None
                            opening_story = None
                            ending_story = None
                            mission_data = None
                            story_error = None
                            window = pygame.display.set_mode((STORY_WIDTH, STORY_HEIGHT), pygame.RESIZABLE)
                            current_width = STORY_WIDTH
                            current_height = STORY_HEIGHT
                            ai_turn_pending = False
                            chat_input = ""
                            chat_input_active = False
                            # Load new opening story
                            threading.Thread(target=load_opening_story, daemon=True).start()
                        elif check_button_click(x, y, quit_rect):
                            running = False
                # Grid clicks and chat input clicks during gameplay
                elif grid and game_state in ['bomb_placement', 'player_turn']:
                    grid_pixel_width = GRID_WIDTH * CELL_SIZE
                    grid_pixel_height = GRID_HEIGHT * CELL_SIZE
                    total_content_width = grid_pixel_width + CHAT_PANEL_WIDTH + 20
                    temp_grid_x_offset = max(10, (current_width - total_content_width) // 2)
                    temp_grid_y_offset = GRID_TOP_MARGIN
                    
                    # Calculate chat input box position
                    temp_chat_x = temp_grid_x_offset + grid_pixel_width + 10
                    temp_chat_width = min(CHAT_PANEL_WIDTH, current_width - temp_chat_x - 10)
                    chat_input_y = temp_grid_y_offset + grid_pixel_height - 45
                    chat_input_rect = (temp_chat_x + 5, chat_input_y, temp_chat_width - 10, 35)
                    
                    # Check if click is in chat input
                    if temp_chat_width > 0 and check_button_click(x, y, chat_input_rect):
                        chat_input_active = True
                    # Check if click is within grid area
                    elif (temp_grid_x_offset <= x <= temp_grid_x_offset + grid_pixel_width and
                        temp_grid_y_offset <= y <= temp_grid_y_offset + grid_pixel_height):
                        chat_input_active = False  # Deactivate chat when clicking grid
                        if game_state == 'bomb_placement':
                            if grid.handle_click(x, y, game_state, temp_grid_x_offset, temp_grid_y_offset):
                                grid.place_ai_bomb()
                                # Record AI's bomb location in opponent AI
                                ai_bomb_loc = grid.get_ai_bomb_location()
                                opponent_ai.set_item_location(ai_bomb_loc)
                                game_state = 'player_turn'  # Go straight to gameplay
                        elif game_state == 'player_turn' and grid.player_turn:
                            revealed_grid = grid.handle_click(x, y, game_state, temp_grid_x_offset, temp_grid_y_offset)
                            if revealed_grid:
                                opponent_ai.update_revealed_grid(revealed_grid, 'player')
                                # Check if player won before triggering AI turn
                                if grid.victor:
                                    # Player won! Trigger ending story
                                    game_state = 'loading_ending'
                                    window = pygame.display.set_mode((STORY_WIDTH, STORY_HEIGHT), pygame.RESIZABLE)
                                    current_width = STORY_WIDTH
                                    current_height = STORY_HEIGHT

                                    def load_ending_story():
                                        nonlocal ending_story, story_loading, story_error, game_state
                                        try:
                                            player_won = (grid.victor == 'Player')
                                            ending_story = story_gen.generate_ending_story(
                                                opening_story, player_won
                                            )
                                            story_loading = False
                                            game_state = 'story_ending'
                                        except Exception as e:
                                            story_error = f"Error generating ending: {str(e)}"
                                            story_loading = False
                                            game_state = 'story_ending'

                                    threading.Thread(target=load_ending_story, daemon=True).start()
                                else:
                                    # Game continues - trigger AI turn
                                    ai_turn_pending = True
                    else:
                        # Click outside grid and chat deactivates chat input
                        if not (temp_chat_width > 0 and check_button_click(x, y, chat_input_rect)):
                            chat_input_active = False
        # AI turn processing (with delay for better UX)
        if grid and ai_turn_pending and game_state == 'player_turn' and not grid.player_turn:
            pygame.time.wait(500)  # Brief delay before AI move
            # Get unrevealed grids and let AI decide
            unrevealed = grid.get_unrevealed_cells()
            unrevealed_nums = [grid.get_grid_number(col, row) for col, row in unrevealed]
            # CRITICAL: Filter out AI's own item location from targets
            ai_item_location = grid.get_ai_bomb_location()
            if ai_item_location in unrevealed_nums:
                unrevealed_nums.remove(ai_item_location)
            # Let opponent AI decide strategically (from valid targets only)
            if unrevealed_nums:
                target_grid = opponent_ai.decide_next_move(unrevealed_nums)
                # Handle case where AI returns None (no valid targets)
                if target_grid is not None:
                    col, row = grid.get_coords_from_number(target_grid)
                    grid.reveal_cell(col, row, 'ai')
                    opponent_ai.update_revealed_grid(target_grid, 'ai')
            if grid.victor:
                # Game ended - generate ending story
                game_state = 'loading_ending'
                window = pygame.display.set_mode((STORY_WIDTH, STORY_HEIGHT), pygame.RESIZABLE)
                current_width = STORY_WIDTH
                current_height = STORY_HEIGHT

                def load_ending_story():
                    nonlocal ending_story, story_loading, story_error, game_state
                    story_loading = True
                    try:
                        player_won = grid.victor == 'Player'
                        ending_story = story_gen.generate_ending_story(
                            opening_story, player_won
                        )
                        game_state = 'story_ending'
                    except Exception as e:
                        story_error = str(e)
                        game_state = 'story_ending'
                    story_loading = False

                threading.Thread(target=load_ending_story, daemon=True).start()
            else:
                grid.player_turn = True  # Switch back to player
            ai_turn_pending = False
        # Rendering
        window.fill(WHITE)
        # Render current game state (use current_width and current_height for dynamic sizing)
        if game_state == 'loading_story':
            # Show loading screen while generating opening story
            loading_text = prompt_font.render("Generating Mission...", True, BLACK)
            window.blit(loading_text, (current_width // 2 - 150, current_height // 2 - 20))
            spinner_text = story_font.render("Please wait...", True, BLACK)
            window.blit(spinner_text, (current_width // 2 - 70, current_height // 2 + 20))
        elif game_state == 'story_opening':
            # Display opening story
            if story_error:
                error_text = prompt_font.render("Story Generation Error", True, BLACK)
                window.blit(error_text, (50, 50))
                error_msg = story_font.render(f"Error: {story_error}", True, BLACK)
                window.blit(error_msg, (50, 100))
            elif opening_story:
                title_text = prompt_font.render("MISSION BRIEFING", True, BLACK)
                window.blit(title_text, (current_width // 2 - 120, 30))
                # Wrap and display story text dynamically based on window width
                wrapped_lines = wrap_text(opening_story, story_font, current_width - 100)
                y_offset = 100
                for line in wrapped_lines:
                    line_surface = story_font.render(line, True, BLACK)
                    window.blit(line_surface, (50, y_offset))
                    y_offset += 30
                # Begin mission button
                begin_rect = (current_width // 2 - 100, current_height - 80, 200, 50)
                pygame.draw.rect(window, (100, 200, 100), begin_rect)
                begin_text = button_font.render("BEGIN MISSION", True, WHITE)
                window.blit(begin_text, (begin_rect[0] + 30, begin_rect[1] + 12))
        elif game_state == 'loading_ending':
            # Show loading screen while generating ending story
            loading_text = prompt_font.render("Processing Outcome...", True, BLACK)
            window.blit(loading_text, (current_width // 2 - 160, current_height // 2 - 20))
            spinner_text = story_font.render("Please wait...", True, BLACK)
            window.blit(spinner_text, (current_width // 2 - 70, current_height // 2 + 20))
        elif game_state == 'story_ending':
            # Display ending story
            if story_error:
                error_text = prompt_font.render("Story Generation Error", True, BLACK)
                window.blit(error_text, (50, 50))
                error_msg = story_font.render(f"Error: {story_error}", True, BLACK)
                window.blit(error_msg, (50, 100))
            elif ending_story:
                result = "MISSION SUCCESS" if grid.victor == 'Player' else "MISSION FAILED"
                color = (50, 150, 50) if grid.victor == 'Player' else (150, 50, 50)
                title_text = prompt_font.render(result, True, color)
                window.blit(title_text, (current_width // 2 - 120, 30))
                # Wrap and display story text dynamically based on window width
                wrapped_lines = wrap_text(ending_story, story_font, current_width - 100)
                y_offset = 100
                for line in wrapped_lines:
                    line_surface = story_font.render(line, True, BLACK)
                    window.blit(line_surface, (50, y_offset))
                    y_offset += 30
                # New Mission and Quit buttons
                new_mission_rect = (current_width // 2 - 210, current_height - 80, 180, 50)
                quit_rect = (current_width // 2 + 30, current_height - 80, 180, 50)
                pygame.draw.rect(window, (100, 200, 100), new_mission_rect)  # Green
                pygame.draw.rect(window, (200, 100, 100), quit_rect)  # Red
                new_mission_text = button_font.render("NEW MISSION", True, WHITE)
                quit_text = button_font.render("QUIT", True, WHITE)
                window.blit(new_mission_text, (new_mission_rect[0] + 30, new_mission_rect[1] + 12))
                window.blit(quit_text, (quit_rect[0] + 65, quit_rect[1] + 12))
        elif game_state == 'difficulty_selection':
            # Draw difficulty selection buttons
            prompt_text = prompt_font.render("Select Difficulty", True, BLACK)
            window.blit(prompt_text, (100, 50))
            easy_rect = (100, 100, 200, 40)
            medium_rect = (100, 150, 200, 40)
            hard_rect = (100, 200, 200, 40)
            pygame.draw.rect(window, (100, 200, 100), easy_rect)  # Green
            pygame.draw.rect(window, (200, 200, 100), medium_rect)  # Yellow
            pygame.draw.rect(window, (200, 100, 100), hard_rect)  # Red
            easy_text = button_font.render("Easy", True, WHITE)
            medium_text = button_font.render("Medium", True, WHITE)
            hard_text = button_font.render("Hard", True, WHITE)
            window.blit(easy_text, (easy_rect[0] + 80, easy_rect[1] + 10))
            window.blit(medium_text, (medium_rect[0] + 70, medium_rect[1] + 10))
            window.blit(hard_text, (hard_rect[0] + 80, hard_rect[1] + 10))
        elif grid and game_state in ['bomb_placement', 'player_turn']:
            # Calculate layout: grid on left, chat on right, prompts above grid
            grid_pixel_width = GRID_WIDTH * CELL_SIZE
            grid_pixel_height = GRID_HEIGHT * CELL_SIZE
            total_content_width = grid_pixel_width + CHAT_PANEL_WIDTH + 20
            
            # Position grid with some margin
            grid_x_offset = max(10, (current_width - total_content_width) // 2)
            grid_y_offset = GRID_TOP_MARGIN
            
            # Draw prompt above grid
            if game_state == 'bomb_placement':
                player_item = mission_data['player_item'] if mission_data else "bomb"
                prompt_text = f"Hide your {player_item}"
            elif game_state == 'player_turn':
                if grid.player_turn:
                    ai_item = mission_data['ai_item'] if mission_data else "target"
                    prompt_text = f"Find the {ai_item}"
                else:
                    prompt_text = "AI's turn..."
            
            prompt_surf = prompt_font.render(prompt_text, True, BLACK)
            prompt_x = grid_x_offset + (grid_pixel_width - prompt_surf.get_width()) // 2
            window.blit(prompt_surf, (prompt_x, grid_y_offset - 40))
            
            # Draw grid
            grid.draw(window, font, small_font, grid_x_offset, grid_y_offset)
            
            # Draw chat sidebar on the right
            chat_x = grid_x_offset + grid_pixel_width + 10
            chat_width = min(CHAT_PANEL_WIDTH, current_width - chat_x - 10)
            if chat_width > 100 and opponent_ai.story_context:
                draw_chat_sidebar(
                    window, chat_x, grid_y_offset, chat_width, grid_pixel_height,
                    opponent_ai, chat_input, chat_input_active, ai_response_loading,
                    button_font, small_font
                )
        # Update display and maintain 60 FPS
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    run_game()

