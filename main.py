"""
Queen of hearts - Main Game Module

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


# Cyberpunk CRT Color Scheme (inspired by design reference)
BLACK = (0, 0, 0)  # Background
CYAN_700 = (14, 116, 144)  # Dark cyan for borders
CYAN_600 = (8, 145, 178)  # Cyan borders
CYAN_500 = (6, 182, 212)  # Primary cyan accent
CYAN_400 = (34, 211, 238)  # Bright cyan (hover/glow)
CYAN_300 = (103, 232, 249)  # Lightest cyan
BLUE_500 = (59, 130, 246)  # Player reveals (semi-transparent look)
BLUE_600 = (37, 99, 235)  # Player borders
RED_500 = (239, 68, 68)  # AI reveals/errors
RED_600 = (220, 38, 38)  # AI borders
RED_400 = (248, 113, 113)  # Light red (hover)
GREEN_300 = (134, 239, 172)  # Light green (hover)
GREEN_500 = (34, 197, 94)  # Success/winning cell
GREEN_600 = (22, 163, 74)  # Success border
GREEN_700 = (21, 128, 61)  # Dark green border
YELLOW_500 = (234, 179, 8)  # Warnings
WHITE = (255, 255, 255)  # Text
GRAY = (113, 113, 130)  # Muted text
# Legacy constants for compatibility
PLAYER_COLOR = BLUE_500
AI_COLOR = RED_500
WIN_COLOR = GREEN_500
PANEL_COLOR = (20, 20, 20)  # Very dark panel
RED = RED_500  # For timer warnings


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
        Render the grid with cyberpunk CRT styling.

        Args:
            surface: Pygame surface to draw on
            font: Font for bomb letters (P/A)
            small_font: Font for grid numbers
            x_offset: Horizontal offset for centering the grid
            y_offset: Vertical offset for centering the grid
        """
        # Draw outer glow border around entire grid
        grid_outer_rect = pygame.Rect(
            x_offset - 6, y_offset - 6,
            self.width * self.cell_size + 12, self.height * self.cell_size + 12
        )
        # Glow effect (multiple borders)
        for i in range(3, 0, -1):
            alpha = 40 * (4 - i)
            glow_surf = pygame.Surface((grid_outer_rect.width + i*2, grid_outer_rect.height + i*2))
            glow_surf.set_alpha(alpha)
            glow_surf.fill(CYAN_500)
            surface.blit(glow_surf, (grid_outer_rect.x - i, grid_outer_rect.y - i))
        
        # Draw thick cyan border around grid
        pygame.draw.rect(surface, CYAN_500, grid_outer_rect, 6)

        for x in range(self.width):
            for y in range(self.height):
                cell = self.cells[x][y]
                # Calculate cell rectangle position with offset
                rect = pygame.Rect(
                    x * self.cell_size + x_offset,
                    y * self.cell_size + y_offset,
                    self.cell_size,
                    self.cell_size
                )
                
                # Determine cell color and border
                if cell.revealed:
                    # Green if bomb found (winning reveal)
                    if cell.item_type and cell.item_type[0] in ['P', 'A']:
                        color = GREEN_500
                        border_color = GREEN_700
                    # Blue for player reveals
                    elif cell.revealed_by == 'player':
                        color = BLUE_500
                        border_color = BLUE_600
                    # Red for AI reveals
                    else:
                        color = RED_500
                        border_color = RED_600
                    
                    # Draw filled cell
                    pygame.draw.rect(surface, color, rect)
                    # Draw thick border
                    pygame.draw.rect(surface, border_color, rect, 4)
                    
                    # Draw bomb letter if cell contains a bomb
                    if cell.item_type:
                        text = font.render(cell.item_type[0], True, BLACK)
                        text_rect = text.get_rect(center=rect.center)
                        surface.blit(text, text_rect)
                else:
                    # Unrevealed cell - black with cyan border
                    pygame.draw.rect(surface, BLACK, rect)
                    pygame.draw.rect(surface, CYAN_700, rect, 4)
                    
                    # Draw grid number in top-left corner
                    grid_num = self.get_grid_number(x, y)
                    num_text = small_font.render(str(grid_num), True, CYAN_700)
                    surface.blit(num_text, (rect.x + 4, rect.y + 4))




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


def get_difficulty_timer(difficulty):
    """
    Get timer duration based on difficulty level.

    Args:
        difficulty: 'easy', 'medium', or 'hard'

    Returns:
        Time duration in seconds
    """
    if difficulty == 'easy':
        return 30  # 30 seconds
    elif difficulty == 'medium':
        return 40  # 40 seconds
    elif difficulty == 'hard':
        return 50  # 50 seconds
    return 30  # Default to easy


def get_difficulty_attempts(difficulty):
    """
    Get number of allowed attempts based on difficulty level.

    Args:
        difficulty: 'easy', 'medium', or 'hard'

    Returns:
        Number of attempts allowed
    """
    if difficulty == 'easy':
        return 5  # 5 attempts
    elif difficulty == 'medium':
        return 4  # 4 attempts
    elif difficulty == 'hard':
        return 3  # 3 attempts
    return 5  # Default to easy


def draw_cyberpunk_button(surface, rect, text, font, is_hovered=False, color_scheme='cyan'):
    """
    Draw a button with cyberpunk CRT styling (thick borders, neon glow).
    
    Args:
        surface: Pygame surface to draw on
        rect: Button rectangle (x, y, width, height) or tuple
        text: Button text
        font: Pygame font
        is_hovered: Whether mouse is hovering over button
        color_scheme: 'cyan', 'green', 'red', or 'yellow'
    """
    # Choose colors based on scheme
    if color_scheme == 'cyan':
        border_color = CYAN_600 if not is_hovered else CYAN_400
        text_color = CYAN_400 if not is_hovered else CYAN_300
        glow_color = CYAN_500
    elif color_scheme == 'green':
        border_color = GREEN_600 if not is_hovered else GREEN_500
        text_color = GREEN_500 if not is_hovered else GREEN_300
        glow_color = GREEN_500
    elif color_scheme == 'red':
        border_color = RED_600 if not is_hovered else RED_500
        text_color = RED_500 if not is_hovered else RED_400
        glow_color = RED_500
    else:  # yellow
        border_color = YELLOW_500
        text_color = YELLOW_500
        glow_color = YELLOW_500
    
    button_rect = pygame.Rect(rect)
    
    # Draw glow effect on hover
    if is_hovered:
        for i in range(2, 0, -1):
            glow_surf = pygame.Surface((button_rect.width + i*4, button_rect.height + i*4))
            glow_surf.set_alpha(60 * (3 - i))
            glow_surf.fill(glow_color)
            surface.blit(glow_surf, (button_rect.x - i*2, button_rect.y - i*2))
    
    # Draw button background (black)
    pygame.draw.rect(surface, BLACK, button_rect)
    # Draw thick border
    pygame.draw.rect(surface, border_color, button_rect, 6)
    
    # Draw text (centered)
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=button_rect.center)
    surface.blit(text_surf, text_rect)


def draw_scanlines(surface, opacity=20):
    """
    Draw horizontal scanlines for CRT effect.
    
    Args:
        surface: Pygame surface to draw on
        opacity: Alpha transparency (0-255)
    """
    width, height = surface.get_size()
    scanline_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Draw horizontal lines every 4 pixels
    for y in range(0, height, 4):
        pygame.draw.line(scanline_surf, (*CYAN_500, opacity), (0, y), (width, y), 1)
    
    surface.blit(scanline_surf, (0, 0))


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
    # Background (cyberpunk styling)
    panel_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, BLACK, panel_rect)
    # Glow effect
    for i in range(2, 0, -1):
        glow_surf = pygame.Surface((width + i*2, height + i*2))
        glow_surf.set_alpha(40 * (3 - i))
        glow_surf.fill(CYAN_500)
        surface.blit(glow_surf, (x - i, y - i))
    pygame.draw.rect(surface, CYAN_600, panel_rect, 6)
    
    # Title (without message count)
    title_text = ">> AI_OPPONENT_CHAT"
    title = font.render(title_text, True, CYAN_300)
    surface.blit(title, (x + 10, y + 10))
    
    # Calculate input box height dynamically based on text wrapping
    input_width = width - 30
    if chat_input:
        wrapped_input_lines = wrap_text(chat_input, small_font, input_width)
        num_input_lines = len(wrapped_input_lines)
        # Dynamic height: min 35px, max 200px, based on number of lines
        input_box_height = min(max(35, num_input_lines * 20 + 15), 200)
    else:
        wrapped_input_lines = []
        input_box_height = 35  # Default height
    
    # Chat history area (adjust height to account for dynamic input box)
    chat_area_x = x + 5
    chat_area_y = y + 45
    chat_area_width = width - 10
    chat_area_height = height - (95 + (input_box_height - 35))  # Adjust for input box expansion
    pygame.draw.rect(surface, BLACK, (chat_area_x, chat_area_y, chat_area_width, chat_area_height))
    pygame.draw.rect(surface, CYAN_700, (chat_area_x, chat_area_y, chat_area_width, chat_area_height), 3)
    
    # Calculate all wrapped lines first to enable auto-scroll
    chat_history = opponent_ai.get_chat_history()
    all_lines = []
    line_height = 20
    text_margin = 10
    available_width = chat_area_width - 2 * text_margin
    
    # Show help text if no messages yet
    if not chat_history:
        help_lines = [
            ">> CLICK_INPUT_BOX_TO_CHAT",
            ">> ASK_FOR_HINTS",
            ">> REQUEST_STRATEGY",
            ">> ENGAGE_AI_OPPONENT"
        ]
        for help_line in help_lines:
            all_lines.append((help_line, CYAN_700, None))
    
    for sender, message in chat_history:
        color = BLUE_500 if sender == 'player' else RED_500
        bg_color = (20, 40, 80) if sender == 'player' else (80, 20, 20)
        prefix = ">> YOU: " if sender == 'player' else ">> AI: "
        
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
        loading_text = small_font.render(">> AI_PROCESSING...", True, CYAN_400)
        surface.blit(loading_text, (chat_area_x + text_margin, y_offset))
    
    # Input box (cyberpunk styling) - dynamically sized
    input_y = y + height - (45 + (input_box_height - 35))  # Adjust position based on height
    input_box_color = CYAN_500 if chat_input_active else CYAN_700
    pygame.draw.rect(surface, BLACK, (x + 5, input_y, width - 10, input_box_height))
    pygame.draw.rect(surface, input_box_color, (x + 5, input_y, width - 10, input_box_height), 4)
    
    # Input text with intelligent wrapping - show all lines
    if chat_input:
        # Display all wrapped lines
        line_height = 20
        text_start_y = input_y + 8
        for i, line in enumerate(wrapped_input_lines):
            input_surf = small_font.render(line, True, CYAN_300)
            surface.blit(input_surf, (x + 10, text_start_y + i * line_height))
        
        # Show blinking cursor at the end of the last line
        if chat_input_active:
            cursor_surf = small_font.render("_", True, CYAN_400)
            if wrapped_input_lines:
                last_line = wrapped_input_lines[-1]
                last_line_surf = small_font.render(last_line, True, CYAN_300)
                cursor_x = x + 10 + last_line_surf.get_width()
            else:
                cursor_x = x + 10
            # Blink cursor (every 500ms)
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                surface.blit(cursor_surf, (cursor_x, text_start_y + (len(wrapped_input_lines) - 1) * line_height))
    else:
        placeholder_surf = small_font.render(">> TYPE_MESSAGE...", True, CYAN_700)
        surface.blit(placeholder_surf, (x + 10, input_y + 8))


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
    GRID_TOP_MARGIN = 100  # Space above grid for timer and prompts
    STORY_WIDTH = 900  # Width for story display (increased for better text visibility)
    STORY_HEIGHT = 700  # Height for story display (increased for better text visibility)
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
    pygame.display.set_caption("Queen of hearts")
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
    # Timer variables
    timer_start = None  # Time when gameplay started
    timer_duration = 0  # Total time allowed (seconds) - set based on difficulty
    # Attempts variables
    max_attempts = 0  # Maximum attempts allowed - set based on difficulty
    attempts_used = 0  # Number of attempts player has used
    # Story variables
    opening_story = None
    ending_story = None
    mission_data = None  # Dict with player_item and ai_item
    story_loading = False
    story_error = None
    story_stream_pos = 0  # Current character position for streaming effect
    story_stream_start_time = None  # When streaming started
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
                            # Keep current window size (don't resize)
                            game_state = 'difficulty_selection'
                # Difficulty selection screen
                elif game_state == 'difficulty_selection':
                    # Use same button positions as rendering (centered)
                    button_width, button_height = 250, 50
                    start_y = current_height // 2 - 100
                    button_x = (current_width - button_width) // 2
                    easy_rect = (button_x, start_y, button_width, button_height)
                    medium_rect = (button_x, start_y + 70, button_width, button_height)
                    hard_rect = (button_x, start_y + 140, button_width, button_height)
                    if check_button_click(x, y, easy_rect):
                        difficulty = 'easy'
                        GRID_WIDTH = GRID_HEIGHT = get_difficulty_size(difficulty)
                        timer_duration = get_difficulty_timer(difficulty)
                        max_attempts = get_difficulty_attempts(difficulty)
                        attempts_used = 0
                        # Calculate window size with proper margins (at least story screen size)
                        WINDOW_WIDTH = max(STORY_WIDTH, GRID_WIDTH * CELL_SIZE + CHAT_PANEL_WIDTH + 60)
                        WINDOW_HEIGHT = max(STORY_HEIGHT, GRID_HEIGHT * CELL_SIZE + GRID_TOP_MARGIN + 80)
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
                        timer_duration = get_difficulty_timer(difficulty)
                        max_attempts = get_difficulty_attempts(difficulty)
                        attempts_used = 0
                        # Calculate window size with proper margins (at least story screen size)
                        WINDOW_WIDTH = max(STORY_WIDTH, GRID_WIDTH * CELL_SIZE + CHAT_PANEL_WIDTH + 60)
                        WINDOW_HEIGHT = max(STORY_HEIGHT, GRID_HEIGHT * CELL_SIZE + GRID_TOP_MARGIN + 80)
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
                        timer_duration = get_difficulty_timer(difficulty)
                        max_attempts = get_difficulty_attempts(difficulty)
                        attempts_used = 0
                        # Calculate window size with proper margins (at least story screen size)
                        WINDOW_WIDTH = max(STORY_WIDTH, GRID_WIDTH * CELL_SIZE + CHAT_PANEL_WIDTH + 60)
                        WINDOW_HEIGHT = max(STORY_HEIGHT, GRID_HEIGHT * CELL_SIZE + GRID_TOP_MARGIN + 80)
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
                            timer_start = None  # Reset timer
                            attempts_used = 0  # Reset attempts
                            ending_story = None
                            mission_data = None
                            story_error = None
                            story_stream_pos = 0  # Reset streaming position
                            story_stream_start_time = None  # Reset streaming timer
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
                                timer_start = pygame.time.get_ticks() / 1000  # Start timer (in seconds)
                        elif game_state == 'player_turn' and grid.player_turn:
                            revealed_grid = grid.handle_click(x, y, game_state, temp_grid_x_offset, temp_grid_y_offset)
                            if revealed_grid:
                                attempts_used += 1  # Increment attempts counter
                                opponent_ai.update_revealed_grid(revealed_grid, 'player')
                                # Check if player won before triggering AI turn
                                if grid.victor:
                                    # Player won! Trigger ending story
                                    game_state = 'loading_ending'
                                    story_stream_pos = 0  # Reset streaming for ending story
                                    story_stream_start_time = None
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
                                elif attempts_used >= max_attempts:
                                    # Out of attempts! Player loses
                                    grid.victor = 'AI'
                                    game_state = 'loading_ending'
                                    story_stream_pos = 0  # Reset streaming for ending story
                                    story_stream_start_time = None
                                    window = pygame.display.set_mode((STORY_WIDTH, STORY_HEIGHT), pygame.RESIZABLE)
                                    current_width = STORY_WIDTH
                                    current_height = STORY_HEIGHT

                                    def load_ending_story():
                                        nonlocal ending_story, story_loading, story_error, game_state
                                        story_loading = True
                                        try:
                                            ending_story = story_gen.generate_ending_story(
                                                opening_story, False
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
        
        # Timer check - if time runs out, player loses
        if game_state == 'player_turn' and timer_start is not None:
            current_time = pygame.time.get_ticks() / 1000
            elapsed_time = current_time - timer_start
            if elapsed_time >= timer_duration:
                # Time's up! Player loses
                grid.victor = 'AI'
                game_state = 'loading_ending'
                story_stream_pos = 0  # Reset streaming for ending story
                story_stream_start_time = None
                window = pygame.display.set_mode((STORY_WIDTH, STORY_HEIGHT), pygame.RESIZABLE)
                current_width = STORY_WIDTH
                current_height = STORY_HEIGHT
                
                def load_ending_story():
                    nonlocal ending_story, story_loading, story_error, game_state
                    story_loading = True
                    try:
                        ending_story = story_gen.generate_ending_story(opening_story, False)
                        story_loading = False
                        game_state = 'story_ending'
                    except Exception as e:
                        story_error = f"Error generating ending: {str(e)}"
                        story_loading = False
                        game_state = 'story_ending'
                
                threading.Thread(target=load_ending_story, daemon=True).start()
        
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
                story_stream_pos = 0  # Reset streaming for ending story
                story_stream_start_time = None
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
        window.fill(BLACK)  # Cyberpunk black background
        # Add scanline overlay for CRT effect
        draw_scanlines(window, opacity=15)
        # Render current game state (use current_width and current_height for dynamic sizing)
        if game_state == 'loading_story':
            # Show loading screen while generating opening story
            loading_text = prompt_font.render(">> GENERATING_MISSION...", True, CYAN_400)
            text_rect = loading_text.get_rect(center=(current_width // 2, current_height // 2 - 20))
            window.blit(loading_text, text_rect)
            spinner_text = story_font.render(">> INITIALIZING_QUANTUM_PARAMETERS...", True, CYAN_700)
            text_rect2 = spinner_text.get_rect(center=(current_width // 2, current_height // 2 + 20))
            window.blit(spinner_text, text_rect2)
        elif game_state == 'story_opening':
            # Display opening story with streaming effect
            if story_error:
                error_text = prompt_font.render(">> ERROR", True, RED_500)
                window.blit(error_text, (50, 50))
                error_msg = story_font.render(f"{story_error}", True, RED_500)
                window.blit(error_msg, (50, 100))
            elif opening_story:
                # Initialize streaming when story first appears
                if story_stream_start_time is None:
                    story_stream_start_time = pygame.time.get_ticks()
                    story_stream_pos = 0
                
                # Update streaming position (characters per second)
                chars_per_second = 30  # Adjust speed here (higher = faster)
                elapsed_ms = pygame.time.get_ticks() - story_stream_start_time
                story_stream_pos = min(len(opening_story), int(chars_per_second * elapsed_ms / 1000))
                
                title_text = prompt_font.render(">> MISSION_BRIEFING", True, CYAN_400)
                title_rect = title_text.get_rect(center=(current_width // 2, 40))
                window.blit(title_text, title_rect)
                
                # Get only the visible portion of the story (streaming effect)
                visible_story = opening_story[:story_stream_pos]
                
                # Wrap and display story text dynamically based on window width
                wrapped_lines = wrap_text(visible_story, story_font, current_width - 100)
                y_offset = 90
                for line in wrapped_lines:
                    line_surface = story_font.render(line, True, WHITE)
                    window.blit(line_surface, (50, y_offset))
                    y_offset += 30
                
                # Show blinking cursor at the end if still streaming
                if story_stream_pos < len(opening_story):
                    cursor_x = 50
                    if wrapped_lines:
                        last_line = wrapped_lines[-1]
                        last_line_surf = story_font.render(last_line, True, WHITE)
                        cursor_x = 50 + last_line_surf.get_width()
                    cursor_surf = story_font.render("_", True, CYAN_400)
                    # Blink cursor (every 500ms)
                    if (pygame.time.get_ticks() // 500) % 2 == 0:
                        window.blit(cursor_surf, (cursor_x, y_offset - 30))
                # Begin mission button with cyberpunk styling
                begin_rect = (current_width // 2 - 100, current_height - 80, 200, 50)
                mouse_pos = pygame.mouse.get_pos()
                is_hovered = check_button_click(mouse_pos[0], mouse_pos[1], begin_rect)
                draw_cyberpunk_button(window, begin_rect, "BEGIN MISSION", button_font, is_hovered, 'green')
        elif game_state == 'loading_ending':
            # Show loading screen while generating ending story
            loading_text = prompt_font.render(">> ANALYZING_OUTCOME...", True, CYAN_400)
            text_rect = loading_text.get_rect(center=(current_width // 2, current_height // 2 - 20))
            window.blit(loading_text, text_rect)
            spinner_text = story_font.render(">> TIMELINE_CONVERGENCE_PROCESSING...", True, CYAN_700)
            text_rect2 = spinner_text.get_rect(center=(current_width // 2, current_height // 2 + 20))
            window.blit(spinner_text, text_rect2)
        elif game_state == 'story_ending':
            # Display ending story with streaming effect
            if story_error:
                error_text = prompt_font.render(">> ERROR", True, RED_500)
                window.blit(error_text, (50, 50))
                error_msg = story_font.render(f"{story_error}", True, RED_500)
                window.blit(error_msg, (50, 100))
            elif ending_story:
                # Initialize streaming when ending story first appears
                if story_stream_start_time is None:
                    story_stream_start_time = pygame.time.get_ticks()
                    story_stream_pos = 0
                
                # Update streaming position (characters per second)
                chars_per_second = 30  # Same speed as opening story
                elapsed_ms = pygame.time.get_ticks() - story_stream_start_time
                story_stream_pos = min(len(ending_story), int(chars_per_second * elapsed_ms / 1000))
                
                result = ">> MISSION_SUCCESS" if grid.victor == 'Player' else ">> MISSION_FAILED"
                color = GREEN_500 if grid.victor == 'Player' else RED_500
                title_text = prompt_font.render(result, True, color)
                title_rect = title_text.get_rect(center=(current_width // 2, 40))
                window.blit(title_text, title_rect)
                
                # Get only the visible portion of the story (streaming effect)
                visible_story = ending_story[:story_stream_pos]
                
                # Wrap and display story text dynamically based on window width
                wrapped_lines = wrap_text(visible_story, story_font, current_width - 100)
                y_offset = 90
                for line in wrapped_lines:
                    line_surface = story_font.render(line, True, WHITE)
                    window.blit(line_surface, (50, y_offset))
                    y_offset += 30
                
                # Show blinking cursor at the end if still streaming
                if story_stream_pos < len(ending_story):
                    cursor_x = 50
                    if wrapped_lines:
                        last_line = wrapped_lines[-1]
                        last_line_surf = story_font.render(last_line, True, WHITE)
                        cursor_x = 50 + last_line_surf.get_width()
                    cursor_surf = story_font.render("_", True, CYAN_400)
                    # Blink cursor (every 500ms)
                    if (pygame.time.get_ticks() // 500) % 2 == 0:
                        window.blit(cursor_surf, (cursor_x, y_offset - 30))
                # New Mission and Quit buttons with cyberpunk styling
                new_mission_rect = (current_width // 2 - 210, current_height - 80, 180, 50)
                quit_rect = (current_width // 2 + 30, current_height - 80, 180, 50)
                mouse_pos = pygame.mouse.get_pos()
                is_new_hovered = check_button_click(mouse_pos[0], mouse_pos[1], new_mission_rect)
                is_quit_hovered = check_button_click(mouse_pos[0], mouse_pos[1], quit_rect)
                draw_cyberpunk_button(window, new_mission_rect, "NEW MISSION", button_font, is_new_hovered, 'green')
                draw_cyberpunk_button(window, quit_rect, "QUIT", button_font, is_quit_hovered, 'red')
        elif game_state == 'difficulty_selection':
            # Draw difficulty selection buttons with cyberpunk styling
            prompt_text = prompt_font.render(">> SELECT_DIFFICULTY", True, CYAN_400)
            prompt_rect = prompt_text.get_rect(center=(current_width // 2, 60))
            window.blit(prompt_text, prompt_rect)
            # Center buttons horizontally
            button_width, button_height = 250, 50
            start_y = current_height // 2 - 100
            button_x = (current_width - button_width) // 2
            easy_rect = (button_x, start_y, button_width, button_height)
            medium_rect = (button_x, start_y + 70, button_width, button_height)
            hard_rect = (button_x, start_y + 140, button_width, button_height)
            mouse_pos = pygame.mouse.get_pos()
            is_easy_hovered = check_button_click(mouse_pos[0], mouse_pos[1], easy_rect)
            is_medium_hovered = check_button_click(mouse_pos[0], mouse_pos[1], medium_rect)
            is_hard_hovered = check_button_click(mouse_pos[0], mouse_pos[1], hard_rect)
            draw_cyberpunk_button(window, easy_rect, "EASY [5x5]", button_font, is_easy_hovered, 'green')
            draw_cyberpunk_button(window, medium_rect, "MEDIUM [10x10]", button_font, is_medium_hovered, 'yellow')
            draw_cyberpunk_button(window, hard_rect, "HARD [20x20]", button_font, is_hard_hovered, 'red')
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
            
            # Display timer and attempts above prompt (during player_turn only)
            if game_state == 'player_turn' and timer_start is not None:
                current_time = pygame.time.get_ticks() / 1000
                elapsed_time = current_time - timer_start
                remaining_time = max(0, timer_duration - elapsed_time)
                remaining_attempts = max_attempts - attempts_used
                
                # Timer text (cyberpunk styling)
                timer_text = f"TIME: {int(remaining_time)}s"
                timer_color = RED_500 if remaining_time < 10 else CYAN_400
                timer_surf = prompt_font.render(timer_text, True, timer_color)
                
                # Attempts text (more intuitive format, cyberpunk styling)
                attempts_text = f"ATTEMPTS: {remaining_attempts}"
                attempts_color = RED_500 if remaining_attempts <= 1 else CYAN_400
                attempts_surf = prompt_font.render(attempts_text, True, attempts_color)
                
                # Position them side by side, centered above grid
                total_width = timer_surf.get_width() + 50 + attempts_surf.get_width()
                start_x = max(10, grid_x_offset + (grid_pixel_width - total_width) // 2)
                
                window.blit(timer_surf, (start_x, grid_y_offset - 80))
                window.blit(attempts_surf, (start_x + timer_surf.get_width() + 50, grid_y_offset - 80))
            
            # Draw prompt with cyberpunk styling
            prompt_surf = prompt_font.render(f">> {prompt_text.upper()}", True, CYAN_300)
            prompt_x = grid_x_offset + (grid_pixel_width - prompt_surf.get_width()) // 2
            window.blit(prompt_surf, (prompt_x, grid_y_offset - 45))
            
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

