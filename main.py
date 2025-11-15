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

        The AI chooses randomly from all available (empty) cells.
        """
        if self.ai_bomb_placed:
            return
        # Find all empty cells
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
        cell.reveal(revealed_by)
        # Check if a bomb was found (victory condition)
        if cell.item_type and cell.item_type[0] in ['P', 'A']:
            # If player reveals AI bomb, player wins (and vice versa)
            self.victor = 'Player' if revealed_by == 'player' else 'AI'
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
            True if click was handled successfully, False otherwise
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
            return self.place_player_bomb(col, row)
        elif game_state == 'player_turn' and self.player_turn:
            if self.reveal_cell(col, row, 'player'):
                self.player_turn = False  # Switch to AI turn
                return True
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
    Determine if AI will be honest when giving a hint.

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
<<<<<<< HEAD
    RIGHT_PANEL_WIDTH = 200  # Width of side panel for UI
=======
    RIGHT_PANEL_WIDTH = 300  # Width of side panel for UI (increased for better text display)
>>>>>>> 8329a42 (add llm for story generation and narration)
    STORY_WIDTH = 600  # Width for story display
    STORY_HEIGHT = 500  # Height for story display
    # Font setup
    font = pygame.font.SysFont(None, 24)  # Standard font for text
    prompt_font = pygame.font.SysFont(None, 32)  # Larger font for prompts
    button_font = pygame.font.SysFont(None, 28)  # Font for buttons
    small_font = pygame.font.SysFont(None, 16)  # Small font for grid numbers
    story_font = pygame.font.SysFont(None, 22)  # Font for story text
<<<<<<< HEAD
    # Initial window size (for story screen)
    INITIAL_WIDTH = STORY_WIDTH
    INITIAL_HEIGHT = STORY_HEIGHT
    window = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT))
    pygame.display.set_caption("Bomb Hunt Game")
=======
    # Initial window size (for story screen) - make it resizable
    INITIAL_WIDTH = STORY_WIDTH
    INITIAL_HEIGHT = STORY_HEIGHT
    window = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Bomb Hunt Game")
    # Track current window dimensions
    current_width = INITIAL_WIDTH
    current_height = INITIAL_HEIGHT
>>>>>>> 8329a42 (add llm for story generation and narration)
    # Initialize story generator
    story_gen = StoryGenerator()
    # Game state variables
    game_state = 'loading_story'
    difficulty = None
    grid = None
    GRID_WIDTH = 0
    GRID_HEIGHT = 0
    ai_turn_pending = False  # Flag for AI turn delay
    # Story variables
    opening_story = None
    ending_story = None
    mission_data = None  # Dict with player_item and ai_item
    story_loading = False
    story_error = None
    # Dialog state variables
    dialog_completed = False
    ai_hint_grid = None  # Grid number AI claims its bomb is at
    player_hint_grid = None  # Grid number player claims their bomb is at
    ai_next_target = None  # Grid number AI will target next (from player hint)
    input_text = ""  # Text input for player hint
    input_active = False  # Whether text input is active
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
            # Handle keyboard input for dialog text entry
            if event.type == pygame.KEYDOWN:
                if input_active:
                    if event.key == pygame.K_RETURN:
                        # Submit player's hint
                        try:
                            grid_num = int(input_text)
                            max_grid = GRID_WIDTH * GRID_HEIGHT
                            if 1 <= grid_num <= max_grid:
                                player_hint_grid = grid_num
                                ai_next_target = grid_num  # AI will target this next
                                input_text = ""
                                input_active = False
                                dialog_completed = True
                                game_state = 'player_turn'
                        except ValueError:
                            pass
                    elif event.key == pygame.K_BACKSPACE:
                        # Delete last character
                        input_text = input_text[:-1]
                    else:
                        # Only allow digits
                        if event.unicode.isdigit():
                            input_text += event.unicode
            # Handle mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                # Story opening screen - begin mission button
                if game_state == 'story_opening':
                    if opening_story:
<<<<<<< HEAD
                        begin_rect = (STORY_WIDTH // 2 - 100, STORY_HEIGHT - 80, 200, 50)
                        if check_button_click(x, y, begin_rect):
                            window = pygame.display.set_mode((400, 300))
=======
                        begin_rect = (current_width // 2 - 100, current_height - 80, 200, 50)
                        if check_button_click(x, y, begin_rect):
                            window = pygame.display.set_mode((400, 300), pygame.RESIZABLE)
                            current_width = 400
                            current_height = 300
>>>>>>> 8329a42 (add llm for story generation and narration)
                            game_state = 'difficulty_selection'
                # Difficulty selection screen
                elif game_state == 'difficulty_selection':
                    easy_rect = (100, 100, 200, 40)
                    medium_rect = (100, 150, 200, 40)
                    hard_rect = (100, 200, 200, 40)
                    if check_button_click(x, y, easy_rect):
                        difficulty = 'easy'
                        GRID_WIDTH = GRID_HEIGHT = get_difficulty_size(difficulty)
                        WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE + RIGHT_PANEL_WIDTH
                        WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE
                        window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                        current_width = WINDOW_WIDTH
                        current_height = WINDOW_HEIGHT
                        grid = Grid(GRID_WIDTH, GRID_HEIGHT, CELL_SIZE)
                        game_state = 'bomb_placement'
                        dialog_completed = False
                        ai_hint_grid = None
                        player_hint_grid = None
                        ai_next_target = None
                        input_text = ""
                        input_active = False
                    elif check_button_click(x, y, medium_rect):
                        difficulty = 'medium'
                        GRID_WIDTH = GRID_HEIGHT = get_difficulty_size(difficulty)
                        WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE + RIGHT_PANEL_WIDTH
                        WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE
                        window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                        current_width = WINDOW_WIDTH
                        current_height = WINDOW_HEIGHT
                        grid = Grid(GRID_WIDTH, GRID_HEIGHT, CELL_SIZE)
                        game_state = 'bomb_placement'
                        dialog_completed = False
                        ai_hint_grid = None
                        player_hint_grid = None
                        ai_next_target = None
                        input_text = ""
                        input_active = False
                    elif check_button_click(x, y, hard_rect):
                        difficulty = 'hard'
                        GRID_WIDTH = GRID_HEIGHT = get_difficulty_size(difficulty)
                        WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE + RIGHT_PANEL_WIDTH
                        WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE
                        window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                        current_width = WINDOW_WIDTH
                        current_height = WINDOW_HEIGHT
                        grid = Grid(GRID_WIDTH, GRID_HEIGHT, CELL_SIZE)
                        game_state = 'bomb_placement'
                        dialog_completed = False
                        ai_hint_grid = None
                        player_hint_grid = None
                        ai_next_target = None
                        input_text = ""
                        input_active = False
                # Story ending screen - restart or quit
                elif game_state == 'story_ending':
                    if ending_story:
<<<<<<< HEAD
                        new_mission_rect = (STORY_WIDTH // 2 - 210, STORY_HEIGHT - 80, 180, 50)
                        quit_rect = (STORY_WIDTH // 2 + 30, STORY_HEIGHT - 80, 180, 50)
=======
                        new_mission_rect = (current_width // 2 - 210, current_height - 80, 180, 50)
                        quit_rect = (current_width // 2 + 30, current_height - 80, 180, 50)
>>>>>>> 8329a42 (add llm for story generation and narration)
                        if check_button_click(x, y, new_mission_rect):
                            # Start a new game
                            grid.reset()
                            game_state = 'loading_story'
                            grid = None
                            opening_story = None
                            ending_story = None
                            mission_data = None
                            story_error = None
<<<<<<< HEAD
                            window = pygame.display.set_mode((STORY_WIDTH, STORY_HEIGHT))
=======
                            window = pygame.display.set_mode((STORY_WIDTH, STORY_HEIGHT), pygame.RESIZABLE)
                            current_width = STORY_WIDTH
                            current_height = STORY_HEIGHT
>>>>>>> 8329a42 (add llm for story generation and narration)
                            ai_turn_pending = False
                            dialog_completed = False
                            ai_hint_grid = None
                            player_hint_grid = None
                            ai_next_target = None
                            input_text = ""
                            input_active = False
                            # Load new opening story
                            threading.Thread(target=load_opening_story, daemon=True).start()
                        elif check_button_click(x, y, quit_rect):
                            running = False
                # Dialog screen - ask AI for help
                elif game_state == 'dialog':
                    # Calculate dynamic position for Ask AI button
                    grid_pixel_width = GRID_WIDTH * CELL_SIZE
                    grid_pixel_height = GRID_HEIGHT * CELL_SIZE
                    total_content_width = grid_pixel_width + RIGHT_PANEL_WIDTH
                    temp_grid_x_offset = max(0, (current_width - total_content_width) // 2)
                    temp_grid_y_offset = max(0, (current_height - grid_pixel_height) // 2)
                    panel_x = temp_grid_x_offset + grid_pixel_width
                    ask_button = (panel_x + 10, temp_grid_y_offset + 100, 180, 40)
                    if check_button_click(x, y, ask_button):
                        ai_honest = ai_honesty_check()
                        ai_bomb_loc = grid.get_ai_bomb_location()
                        if ai_honest:
                            ai_hint_grid = ai_bomb_loc
                        else:
                            wrong_options = [i for i in range(1, GRID_WIDTH * GRID_HEIGHT + 1)
                                           if i != ai_bomb_loc]
                            ai_hint_grid = random.choice(wrong_options)
                        input_active = True  # Enable text input for player response
                # Grid clicks during gameplay (check if click is within grid bounds)
                elif grid:
                    grid_pixel_width = GRID_WIDTH * CELL_SIZE
                    grid_pixel_height = GRID_HEIGHT * CELL_SIZE
                    total_content_width = grid_pixel_width + RIGHT_PANEL_WIDTH
                    temp_grid_x_offset = max(0, (current_width - total_content_width) // 2)
                    temp_grid_y_offset = max(0, (current_height - grid_pixel_height) // 2)
                    # Check if click is within grid area
                    if (temp_grid_x_offset <= x <= temp_grid_x_offset + grid_pixel_width and
                        temp_grid_y_offset <= y <= temp_grid_y_offset + grid_pixel_height):
                        if game_state == 'bomb_placement':
                            if grid.handle_click(x, y, game_state, temp_grid_x_offset, temp_grid_y_offset):
                                grid.place_ai_bomb()
                                game_state = 'dialog'
                                dialog_completed = False
                        elif game_state == 'player_turn' and grid.player_turn:
                            if grid.handle_click(x, y, game_state, temp_grid_x_offset, temp_grid_y_offset):
                                ai_turn_pending = True  # Trigger AI turn after delay
        # AI turn processing (with delay for better UX)
        if grid and ai_turn_pending and game_state == 'player_turn' and not grid.player_turn:
            pygame.time.wait(500)  # Brief delay before AI move
            grid.ai_reveal(ai_next_target)  # AI reveals (uses hint if available)
            ai_next_target = None  # Clear hint after use
            if grid.victor:
                # Game ended - generate ending story
                game_state = 'loading_ending'
<<<<<<< HEAD
                window = pygame.display.set_mode((STORY_WIDTH, STORY_HEIGHT))
=======
                window = pygame.display.set_mode((STORY_WIDTH, STORY_HEIGHT), pygame.RESIZABLE)
                current_width = STORY_WIDTH
                current_height = STORY_HEIGHT
>>>>>>> 8329a42 (add llm for story generation and narration)

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
<<<<<<< HEAD
        # Render current game state
        if game_state == 'loading_story':
            # Show loading screen while generating opening story
            loading_text = prompt_font.render("Generating Mission...", True, BLACK)
            window.blit(loading_text, (STORY_WIDTH // 2 - 150, STORY_HEIGHT // 2 - 20))
            spinner_text = story_font.render("Please wait...", True, BLACK)
            window.blit(spinner_text, (STORY_WIDTH // 2 - 70, STORY_HEIGHT // 2 + 20))
=======
        # Render current game state (use current_width and current_height for dynamic sizing)
        if game_state == 'loading_story':
            # Show loading screen while generating opening story
            loading_text = prompt_font.render("Generating Mission...", True, BLACK)
            window.blit(loading_text, (current_width // 2 - 150, current_height // 2 - 20))
            spinner_text = story_font.render("Please wait...", True, BLACK)
            window.blit(spinner_text, (current_width // 2 - 70, current_height // 2 + 20))
>>>>>>> 8329a42 (add llm for story generation and narration)
        elif game_state == 'story_opening':
            # Display opening story
            if story_error:
                error_text = prompt_font.render("Story Generation Error", True, BLACK)
                window.blit(error_text, (50, 50))
                error_msg = story_font.render(f"Error: {story_error}", True, BLACK)
                window.blit(error_msg, (50, 100))
            elif opening_story:
                title_text = prompt_font.render("MISSION BRIEFING", True, BLACK)
<<<<<<< HEAD
                window.blit(title_text, (STORY_WIDTH // 2 - 120, 30))
                # Wrap and display story text
                wrapped_lines = wrap_text(opening_story, story_font, STORY_WIDTH - 100)
=======
                window.blit(title_text, (current_width // 2 - 120, 30))
                # Wrap and display story text dynamically based on window width
                wrapped_lines = wrap_text(opening_story, story_font, current_width - 100)
>>>>>>> 8329a42 (add llm for story generation and narration)
                y_offset = 100
                for line in wrapped_lines:
                    line_surface = story_font.render(line, True, BLACK)
                    window.blit(line_surface, (50, y_offset))
                    y_offset += 30
                # Begin mission button
<<<<<<< HEAD
                begin_rect = (STORY_WIDTH // 2 - 100, STORY_HEIGHT - 80, 200, 50)
=======
                begin_rect = (current_width // 2 - 100, current_height - 80, 200, 50)
>>>>>>> 8329a42 (add llm for story generation and narration)
                pygame.draw.rect(window, (100, 200, 100), begin_rect)
                begin_text = button_font.render("BEGIN MISSION", True, WHITE)
                window.blit(begin_text, (begin_rect[0] + 30, begin_rect[1] + 12))
        elif game_state == 'loading_ending':
            # Show loading screen while generating ending story
            loading_text = prompt_font.render("Processing Outcome...", True, BLACK)
<<<<<<< HEAD
            window.blit(loading_text, (STORY_WIDTH // 2 - 160, STORY_HEIGHT // 2 - 20))
            spinner_text = story_font.render("Please wait...", True, BLACK)
            window.blit(spinner_text, (STORY_WIDTH // 2 - 70, STORY_HEIGHT // 2 + 20))
=======
            window.blit(loading_text, (current_width // 2 - 160, current_height // 2 - 20))
            spinner_text = story_font.render("Please wait...", True, BLACK)
            window.blit(spinner_text, (current_width // 2 - 70, current_height // 2 + 20))
>>>>>>> 8329a42 (add llm for story generation and narration)
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
<<<<<<< HEAD
                window.blit(title_text, (STORY_WIDTH // 2 - 120, 30))
                # Wrap and display story text
                wrapped_lines = wrap_text(ending_story, story_font, STORY_WIDTH - 100)
=======
                window.blit(title_text, (current_width // 2 - 120, 30))
                # Wrap and display story text dynamically based on window width
                wrapped_lines = wrap_text(ending_story, story_font, current_width - 100)
>>>>>>> 8329a42 (add llm for story generation and narration)
                y_offset = 100
                for line in wrapped_lines:
                    line_surface = story_font.render(line, True, BLACK)
                    window.blit(line_surface, (50, y_offset))
                    y_offset += 30
                # New Mission and Quit buttons
<<<<<<< HEAD
                new_mission_rect = (STORY_WIDTH // 2 - 210, STORY_HEIGHT - 80, 180, 50)
                quit_rect = (STORY_WIDTH // 2 + 30, STORY_HEIGHT - 80, 180, 50)
=======
                new_mission_rect = (current_width // 2 - 210, current_height - 80, 180, 50)
                quit_rect = (current_width // 2 + 30, current_height - 80, 180, 50)
>>>>>>> 8329a42 (add llm for story generation and narration)
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
        elif grid:
            # Calculate offsets to center game content
            grid_pixel_width = GRID_WIDTH * CELL_SIZE
            grid_pixel_height = GRID_HEIGHT * CELL_SIZE
            total_content_width = grid_pixel_width + RIGHT_PANEL_WIDTH
            # If window is larger, use extra space; otherwise center content
            if current_width >= total_content_width:
                grid_x_offset = max(0, (current_width - total_content_width) // 2)
                panel_width = RIGHT_PANEL_WIDTH
            else:
                # Window too small, no centering
                grid_x_offset = 0
                panel_width = max(100, current_width - grid_pixel_width)
            grid_y_offset = max(0, (current_height - grid_pixel_height) // 2)
            # Draw grid with offset for centering
            grid.draw(window, font, small_font, grid_x_offset, grid_y_offset)
            # Calculate panel position
            panel_x = grid_x_offset + grid_pixel_width
            # If window is extra wide, expand panel width
            available_space = current_width - panel_x
            panel_width = max(panel_width, min(available_space - 20, 500))
            # Draw side panel background
            if panel_width > 0:
                pygame.draw.rect(window, PANEL_COLOR,
                                 (panel_x, grid_y_offset, panel_width,
                                  grid_pixel_height))
            # Calculate available panel width for text wrapping
            available_panel_width = max(100, panel_width - 20)
            prompt_y = grid_y_offset + 20
            # Render state-specific UI
            if game_state == 'bomb_placement':
                # Use mission-specific terminology from the story
                player_item = mission_data['player_item'] if mission_data else "bomb"
<<<<<<< HEAD
                prompt_text = prompt_font.render(f"Hide your {player_item}", True, BLACK)
                window.blit(prompt_text, (GRID_WIDTH * CELL_SIZE + 10, prompt_y))
            elif game_state == 'dialog':
                # Dialog phase UI - use mission-specific terminology
                ai_item = mission_data['ai_item'] if mission_data else "target"
                prompt_text = prompt_font.render(f"Locate {ai_item}", True, BLACK)
                window.blit(prompt_text, (GRID_WIDTH * CELL_SIZE + 10, prompt_y))
=======
                text_content = f"Hide your {player_item}"
                # Wrap text if needed
                wrapped = wrap_text(text_content, prompt_font, available_panel_width)
                for i, line in enumerate(wrapped):
                    line_surf = prompt_font.render(line, True, BLACK)
                    window.blit(line_surf, (panel_x + 10, prompt_y + i * 35))
            elif game_state == 'dialog':
                # Dialog phase UI - use mission-specific terminology
                ai_item = mission_data['ai_item'] if mission_data else "target"
                text_content = f"Locate {ai_item}"
                wrapped = wrap_text(text_content, prompt_font, available_panel_width)
                y_pos = prompt_y
                for line in wrapped:
                    line_surf = prompt_font.render(line, True, BLACK)
                    window.blit(line_surf, (panel_x + 10, y_pos))
                    y_pos += 35
                
>>>>>>> 8329a42 (add llm for story generation and narration)
                if ai_hint_grid:
                    # Show AI's response with mission-specific terminology
                    ai_item = mission_data['ai_item'] if mission_data else "target"
                    hint_text = f"AI says: {ai_item.capitalize()} at grid {ai_hint_grid}"
<<<<<<< HEAD
                    hint_surface = button_font.render(hint_text, True, BLACK)
                    window.blit(hint_surface, (GRID_WIDTH * CELL_SIZE + 10, 60))
                    # Show AI's question to player with mission-specific terminology
                    player_item = mission_data['player_item'] if mission_data else "position"
                    ai_question = button_font.render(f"AI asks: Where is your", True, BLACK)
                    window.blit(ai_question, (GRID_WIDTH * CELL_SIZE + 10, 100))
                    ai_question2 = button_font.render(f"{player_item}?", True, BLACK)
                    window.blit(ai_question2, (GRID_WIDTH * CELL_SIZE + 10, 120))
=======
                    hint_wrapped = wrap_text(hint_text, button_font, available_panel_width)
                    y_pos = grid_y_offset + 70
                    for line in hint_wrapped:
                        line_surf = button_font.render(line, True, BLACK)
                        window.blit(line_surf, (panel_x + 10, y_pos))
                        y_pos += 25
                    
                    # Show AI's question to player with mission-specific terminology
                    player_item = mission_data['player_item'] if mission_data else "position"
                    question_text = f"AI asks: Where is your {player_item}?"
                    question_wrapped = wrap_text(question_text, button_font, available_panel_width)
                    y_pos += 10
                    for line in question_wrapped:
                        line_surf = button_font.render(line, True, BLACK)
                        window.blit(line_surf, (panel_x + 10, y_pos))
                        y_pos += 25
                    
>>>>>>> 8329a42 (add llm for story generation and narration)
                    # Show input field if dialog not completed
                    if not dialog_completed:
                        y_pos += 10
                        input_prompt = button_font.render("Enter grid number:", True, BLACK)
                        window.blit(input_prompt, (panel_x + 10, y_pos))
                        y_pos += 30
                        input_display = button_font.render(input_text or "_", True, BLACK)
                        window.blit(input_display, (panel_x + 10, y_pos))
                else:
                    # Show "Ask AI" button before player clicks it
                    ask_button_rect = (panel_x + 10, grid_y_offset + 100, 180, 40)
                    pygame.draw.rect(window, (100, 150, 200), ask_button_rect)
                    ask_text = button_font.render("Ask AI", True, WHITE)
                    window.blit(ask_text, (ask_button_rect[0] + 60, ask_button_rect[1] + 10))
            elif game_state == 'player_turn':
                # Show whose turn it is with mission-specific terminology
                if grid.player_turn:
                    ai_item = mission_data['ai_item'] if mission_data else "target"
<<<<<<< HEAD
                    prompt_text = prompt_font.render(f"Find {ai_item}", True, BLACK)
                    window.blit(prompt_text, (GRID_WIDTH * CELL_SIZE + 10,
                                              prompt_y))
                else:
                    prompt_text = prompt_font.render("AI's turn...", True, BLACK)
                    window.blit(prompt_text, (GRID_WIDTH * CELL_SIZE + 10,
                                              prompt_y))
=======
                    text_content = f"Find {ai_item}"
                else:
                    text_content = "AI's turn..."
                wrapped = wrap_text(text_content, prompt_font, available_panel_width)
                for i, line in enumerate(wrapped):
                    line_surf = prompt_font.render(line, True, BLACK)
                    window.blit(line_surf, (panel_x + 10, prompt_y + i * 35))
>>>>>>> 8329a42 (add llm for story generation and narration)
        # Update display and maintain 60 FPS
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    run_game()

