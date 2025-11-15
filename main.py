"""
Bomb Hunt Game - Main Game Module

A turn-based strategy game where a player competes against an AI to find
each other's hidden bombs. Features include:
- Difficulty selection (Easy, Medium, Hard)
- Grid-based bomb placement
- Turn-based gameplay with color-coded reveals
- Dialog system for hints (with honesty/lie mechanics)
- Grid numbering for easy identification

Game Flow:
1. Select difficulty level
2. Player places bomb
3. AI places bomb
4. Dialog phase (exchange hints)
5. Turn-based reveal phase
6. Winner determination
"""

import pygame
import random

from cell import Cell


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

    def handle_click(self, x, y, game_state):
        """
        Handle mouse click on the grid.

        Args:
            x: Mouse x coordinate in pixels
            y: Mouse y coordinate in pixels
            game_state: Current game state ('bomb_placement' or 'player_turn')

        Returns:
            True if click was handled successfully, False otherwise
        """
        # Convert pixel coordinates to grid coordinates
        col = x // self.cell_size
        row = y // self.cell_size
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

    def draw(self, surface, font, small_font):
        """
        Render the grid on the given surface.

        Args:
            surface: Pygame surface to draw on
            font: Font for bomb letters (P/A)
            small_font: Font for grid numbers
        """
        for x in range(self.width):
            for y in range(self.height):
                cell = self.cells[x][y]
                # Calculate cell rectangle position
                rect = (x * self.cell_size, y * self.cell_size,
                        self.cell_size, self.cell_size)
                # Draw cell border
                pygame.draw.rect(surface, BLACK, rect, 1)
                # Draw grid number in top-left corner
                grid_num = self.get_grid_number(x, y)
                num_text = small_font.render(str(grid_num), True, (100, 100, 100))
                surface.blit(num_text, (x * self.cell_size + 2, y * self.cell_size + 2))
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
                        surface.blit(text, (x * self.cell_size + 5,
                                            y * self.cell_size + 5))




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


def run_game():
    """
    Main game loop and state management.

    Handles all game states:
    - difficulty_selection: Player chooses difficulty
    - bomb_placement: Player places bomb, then AI places bomb
    - dialog: Exchange hints between player and AI
    - player_turn: Turn-based gameplay
    - game_over: Show results and restart/quit options
    """
    # Initialize pygame
    pygame.init()
    # Game constants
    CELL_SIZE = 40  # Pixel size of each grid cell
    RIGHT_PANEL_WIDTH = 200  # Width of side panel for UI
    # Font setup
    font = pygame.font.SysFont(None, 24)  # Standard font for text
    prompt_font = pygame.font.SysFont(None, 32)  # Larger font for prompts
    button_font = pygame.font.SysFont(None, 28)  # Font for buttons
    small_font = pygame.font.SysFont(None, 16)  # Small font for grid numbers
    # Initial window size (for difficulty selection screen)
    INITIAL_WIDTH = 400
    INITIAL_HEIGHT = 300
    window = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT))
    pygame.display.set_caption("Bomb Hunt Game")
    # Game state variables
    game_state = 'difficulty_selection'
    difficulty = None
    grid = None
    GRID_WIDTH = 0
    GRID_HEIGHT = 0
    ai_turn_pending = False  # Flag for AI turn delay
    # Dialog state variables
    dialog_completed = False
    ai_hint_grid = None  # Grid number AI claims its bomb is at
    player_hint_grid = None  # Grid number player claims their bomb is at
    ai_next_target = None  # Grid number AI will target next (from player hint)
    input_text = ""  # Text input for player hint
    input_active = False  # Whether text input is active
    clock = pygame.time.Clock()
    running = True
    # Main game loop
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
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
                # Difficulty selection screen
                if game_state == 'difficulty_selection':
                    easy_rect = (100, 100, 200, 40)
                    medium_rect = (100, 150, 200, 40)
                    hard_rect = (100, 200, 200, 40)
                    if check_button_click(x, y, easy_rect):
                        difficulty = 'easy'
                        GRID_WIDTH = GRID_HEIGHT = get_difficulty_size(difficulty)
                        WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE + RIGHT_PANEL_WIDTH
                        WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE
                        window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
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
                        window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
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
                        window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
                        grid = Grid(GRID_WIDTH, GRID_HEIGHT, CELL_SIZE)
                        game_state = 'bomb_placement'
                        dialog_completed = False
                        ai_hint_grid = None
                        player_hint_grid = None
                        ai_next_target = None
                        input_text = ""
                        input_active = False
                # Game over screen - restart or quit
                elif game_state == 'game_over':
                    try_again_rect = (GRID_WIDTH * CELL_SIZE + 10, 120, 180, 40)
                    quit_rect = (GRID_WIDTH * CELL_SIZE + 10, 170, 180, 40)
                    if check_button_click(x, y, try_again_rect):
                        grid.reset()
                        game_state = 'difficulty_selection'
                        grid = None
                        window = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT))
                        ai_turn_pending = False
                        dialog_completed = False
                        ai_hint_grid = None
                        player_hint_grid = None
                        ai_next_target = None
                        input_text = ""
                        input_active = False
                    elif check_button_click(x, y, quit_rect):
                        running = False
                # Dialog screen - ask AI for help
                elif game_state == 'dialog':
                    ask_button = (GRID_WIDTH * CELL_SIZE + 10, 150, 180, 40)
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
                # Grid clicks during gameplay
                elif grid and x < GRID_WIDTH * CELL_SIZE:
                    if game_state == 'bomb_placement':
                        if grid.handle_click(x, y, game_state):
                            grid.place_ai_bomb()
                            game_state = 'dialog'
                            dialog_completed = False
                    elif game_state == 'player_turn' and grid.player_turn:
                        if grid.handle_click(x, y, game_state):
                            ai_turn_pending = True  # Trigger AI turn after delay
        # AI turn processing (with delay for better UX)
        if grid and ai_turn_pending and game_state == 'player_turn' and not grid.player_turn:
            pygame.time.wait(500)  # Brief delay before AI move
            grid.ai_reveal(ai_next_target)  # AI reveals (uses hint if available)
            ai_next_target = None  # Clear hint after use
            if grid.victor:
                game_state = 'game_over'
            else:
                grid.player_turn = True  # Switch back to player
            ai_turn_pending = False
        # Rendering
        window.fill(WHITE)
        # Render current game state
        if game_state == 'difficulty_selection':
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
            # Draw grid and side panel
            grid.draw(window, font, small_font)
            # Draw side panel
            pygame.draw.rect(window, PANEL_COLOR,
                             (GRID_WIDTH * CELL_SIZE, 0, RIGHT_PANEL_WIDTH,
                              WINDOW_HEIGHT))
            prompt_y = 20
            # Render state-specific UI
            if game_state == 'bomb_placement':
                prompt_text = prompt_font.render("Hide your bomb", True, BLACK)
                window.blit(prompt_text, (GRID_WIDTH * CELL_SIZE + 10, prompt_y))
            elif game_state == 'dialog':
                # Dialog phase UI
                prompt_text = prompt_font.render("Ask AI for help", True, BLACK)
                window.blit(prompt_text, (GRID_WIDTH * CELL_SIZE + 10, prompt_y))
                if ai_hint_grid:
                    # Show AI's response
                    hint_text = f"AI says: Grid {ai_hint_grid}"
                    hint_surface = button_font.render(hint_text, True, BLACK)
                    window.blit(hint_surface, (GRID_WIDTH * CELL_SIZE + 10, 60))
                    # Show AI's question to player
                    ai_question = button_font.render("AI asks: Where is", True, BLACK)
                    window.blit(ai_question, (GRID_WIDTH * CELL_SIZE + 10, 100))
                    ai_question2 = button_font.render("your bomb?", True, BLACK)
                    window.blit(ai_question2, (GRID_WIDTH * CELL_SIZE + 10, 120))
                    # Show input field if dialog not completed
                    if not dialog_completed:
                        input_prompt = button_font.render("Enter grid number:", True, BLACK)
                        window.blit(input_prompt, (GRID_WIDTH * CELL_SIZE + 10, 150))
                        input_display = button_font.render(input_text or "_", True, BLACK)
                        window.blit(input_display, (GRID_WIDTH * CELL_SIZE + 10, 180))
                else:
                    # Show "Ask AI" button before player clicks it
                    ask_button_rect = (GRID_WIDTH * CELL_SIZE + 10, 150, 180, 40)
                    pygame.draw.rect(window, (100, 150, 200), ask_button_rect)
                    ask_text = button_font.render("Ask AI", True, WHITE)
                    window.blit(ask_text, (ask_button_rect[0] + 60, ask_button_rect[1] + 10))
            elif game_state == 'player_turn':
                # Show whose turn it is
                if grid.player_turn:
                    prompt_text = prompt_font.render("Find the bomb", True, BLACK)
                    window.blit(prompt_text, (GRID_WIDTH * CELL_SIZE + 10,
                                              prompt_y))
                else:
                    prompt_text = prompt_font.render("AI's turn...", True, BLACK)
                    window.blit(prompt_text, (GRID_WIDTH * CELL_SIZE + 10,
                                              prompt_y))
            elif game_state == 'game_over':
                # Show game result and restart/quit buttons
                result_text = "You win!" if grid.victor == 'Player' else "You lose!"
                prompt_text = prompt_font.render(result_text, True, BLACK)
                window.blit(prompt_text, (GRID_WIDTH * CELL_SIZE + 10, prompt_y))
                try_again_rect = (GRID_WIDTH * CELL_SIZE + 10, 120, 180, 40)
                quit_rect = (GRID_WIDTH * CELL_SIZE + 10, 170, 180, 40)
                pygame.draw.rect(window, (100, 200, 100), try_again_rect)  # Green
                pygame.draw.rect(window, (200, 100, 100), quit_rect)  # Red
                try_again_text = button_font.render("Try Again", True, WHITE)
                quit_text = button_font.render("Quit", True, WHITE)
                window.blit(try_again_text,
                            (try_again_rect[0] + 50, try_again_rect[1] + 10))
                window.blit(quit_text, (quit_rect[0] + 70, quit_rect[1] + 10))
        # Update display and maintain 60 FPS
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    run_game()

