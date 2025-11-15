# grid.py
import pygame
import random

from cell import Cell


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PLAYER_COLOR = (180, 220, 255)
AI_COLOR = (255, 180, 180)
WIN_COLOR = (180, 255, 180)
PANEL_COLOR = (200, 200, 200)


class Grid:

    def run_status(self):
        return self.running

    def __init__(self, width, height, cell_size):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.cells = [[Cell() for _ in range(height)] for _ in range(width)]
        self.running = True
        self.player_bomb_placed = False
        self.ai_bomb_placed = False
        self.player_turn = True
        self.victor = None

    def place_player_bomb(self, col, row):
        if not self.player_bomb_placed and not self.cells[col][row].item_type:
            self.cells[col][row].add_item(('P', 'B'))
            self.player_bomb_placed = True
            return True
        return False

    def place_ai_bomb(self):
        if self.ai_bomb_placed:
            return
        available = [(x, y) for x in range(self.width) for y in range(self.height)
                     if not self.cells[x][y].item_type]
        if available:
            col, row = random.choice(available)
            self.cells[col][row].add_item(('A', 'B'))
            self.ai_bomb_placed = True

    def reveal_cell(self, col, row, revealed_by):
        if col < 0 or col >= self.width or row < 0 or row >= self.height:
            return False
        cell = self.cells[col][row]
        if cell.revealed:
            return False
        cell.reveal(revealed_by)
        if cell.item_type and cell.item_type[0] in ['P', 'A']:
            self.victor = 'Player' if revealed_by == 'player' else 'AI'
        return True

    def reset(self):
        self.cells = [[Cell() for _ in range(self.height)]
                       for _ in range(self.width)]
        self.running = True
        self.player_bomb_placed = False
        self.ai_bomb_placed = False
        self.player_turn = True
        self.victor = None

    def get_unrevealed_cells(self):
        return [(x, y) for x in range(self.width) for y in range(self.height)
                if not self.cells[x][y].revealed]

    def ai_reveal(self, target_grid_num=None):
        if target_grid_num:
            col, row = self.get_coords_from_number(target_grid_num)
            if not self.cells[col][row].revealed:
                self.reveal_cell(col, row, 'ai')
                return True
        unrevealed = self.get_unrevealed_cells()
        if unrevealed:
            col, row = random.choice(unrevealed)
            self.reveal_cell(col, row, 'ai')
            return True
        return False

    def handle_click(self, x, y, game_state):
        col = x // self.cell_size
        row = y // self.cell_size
        if col < 0 or col >= self.width or row < 0 or row >= self.height:
            return False
        if game_state == 'bomb_placement':
            return self.place_player_bomb(col, row)
        elif game_state == 'player_turn' and self.player_turn:
            if self.reveal_cell(col, row, 'player'):
                self.player_turn = False
                return True
        return False

    def get_grid_number(self, col, row):
        return row * self.width + col + 1

    def get_coords_from_number(self, grid_num):
        grid_num -= 1
        row = grid_num // self.width
        col = grid_num % self.width
        return col, row

    def get_ai_bomb_location(self):
        for x in range(self.width):
            for y in range(self.height):
                if self.cells[x][y].item_type and self.cells[x][y].item_type[0] == 'A':
                    return self.get_grid_number(x, y)
        return None

    def get_player_bomb_location(self):
        for x in range(self.width):
            for y in range(self.height):
                if self.cells[x][y].item_type and self.cells[x][y].item_type[0] == 'P':
                    return self.get_grid_number(x, y)
        return None

    def draw(self, surface, font, small_font):
        for x in range(self.width):
            for y in range(self.height):
                cell = self.cells[x][y]
                rect = (x * self.cell_size, y * self.cell_size,
                        self.cell_size, self.cell_size)
                pygame.draw.rect(surface, BLACK, rect, 1)
                grid_num = self.get_grid_number(x, y)
                num_text = small_font.render(str(grid_num), True, (100, 100, 100))
                surface.blit(num_text, (x * self.cell_size + 2, y * self.cell_size + 2))
                if cell.revealed:
                    if cell.item_type and cell.item_type[0] in ['P', 'A']:
                        color = WIN_COLOR
                    elif cell.revealed_by == 'player':
                        color = PLAYER_COLOR
                    else:
                        color = AI_COLOR
                    pygame.draw.rect(surface, color, rect)
                    if cell.item_type:
                        text = font.render(cell.item_type[0], True, BLACK)
                        surface.blit(text, (x * self.cell_size + 5,
                                            y * self.cell_size + 5))




def check_button_click(x, y, button_rect):
    return (button_rect[0] <= x <= button_rect[0] + button_rect[2] and
            button_rect[1] <= y <= button_rect[1] + button_rect[3])


def get_difficulty_size(difficulty):
    base_size = 5
    if difficulty == 'easy':
        return base_size
    elif difficulty == 'medium':
        return base_size * 2
    elif difficulty == 'hard':
        return base_size * 4
    return base_size


def ai_honesty_check():
    return random.randint(1, 2) == 1


def run_game():
    pygame.init()
    CELL_SIZE = 40
    RIGHT_PANEL_WIDTH = 200
    font = pygame.font.SysFont(None, 24)
    prompt_font = pygame.font.SysFont(None, 32)
    button_font = pygame.font.SysFont(None, 28)
    small_font = pygame.font.SysFont(None, 16)
    INITIAL_WIDTH = 400
    INITIAL_HEIGHT = 300
    window = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT))
    pygame.display.set_caption("Bomb Hunt Game")
    game_state = 'difficulty_selection'
    difficulty = None
    grid = None
    GRID_WIDTH = 0
    GRID_HEIGHT = 0
    ai_turn_pending = False
    dialog_completed = False
    ai_hint_grid = None
    player_hint_grid = None
    ai_next_target = None
    input_text = ""
    input_active = False
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if input_active:
                    if event.key == pygame.K_RETURN:
                        try:
                            grid_num = int(input_text)
                            max_grid = GRID_WIDTH * GRID_HEIGHT
                            if 1 <= grid_num <= max_grid:
                                player_hint_grid = grid_num
                                ai_next_target = grid_num
                                input_text = ""
                                input_active = False
                                dialog_completed = True
                                game_state = 'player_turn'
                        except ValueError:
                            pass
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        if event.unicode.isdigit():
                            input_text += event.unicode
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
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
                        input_active = True
                elif grid and x < GRID_WIDTH * CELL_SIZE:
                    if game_state == 'bomb_placement':
                        if grid.handle_click(x, y, game_state):
                            grid.place_ai_bomb()
                            game_state = 'dialog'
                            dialog_completed = False
                    elif game_state == 'player_turn' and grid.player_turn:
                        if grid.handle_click(x, y, game_state):
                            ai_turn_pending = True
        if grid and ai_turn_pending and game_state == 'player_turn' and not grid.player_turn:
            pygame.time.wait(500)
            grid.ai_reveal(ai_next_target)
            ai_next_target = None
            if grid.victor:
                game_state = 'game_over'
            else:
                grid.player_turn = True
            ai_turn_pending = False
        window.fill(WHITE)
        if game_state == 'difficulty_selection':
            prompt_text = prompt_font.render("Select Difficulty", True, BLACK)
            window.blit(prompt_text, (100, 50))
            easy_rect = (100, 100, 200, 40)
            medium_rect = (100, 150, 200, 40)
            hard_rect = (100, 200, 200, 40)
            pygame.draw.rect(window, (100, 200, 100), easy_rect)
            pygame.draw.rect(window, (200, 200, 100), medium_rect)
            pygame.draw.rect(window, (200, 100, 100), hard_rect)
            easy_text = button_font.render("Easy", True, WHITE)
            medium_text = button_font.render("Medium", True, WHITE)
            hard_text = button_font.render("Hard", True, WHITE)
            window.blit(easy_text, (easy_rect[0] + 80, easy_rect[1] + 10))
            window.blit(medium_text, (medium_rect[0] + 70, medium_rect[1] + 10))
            window.blit(hard_text, (hard_rect[0] + 80, hard_rect[1] + 10))
        elif grid:
            grid.draw(window, font, small_font)
            pygame.draw.rect(window, PANEL_COLOR,
                             (GRID_WIDTH * CELL_SIZE, 0, RIGHT_PANEL_WIDTH,
                              WINDOW_HEIGHT))
            prompt_y = 20
            if game_state == 'bomb_placement':
                prompt_text = prompt_font.render("Hide your bomb", True, BLACK)
                window.blit(prompt_text, (GRID_WIDTH * CELL_SIZE + 10, prompt_y))
            elif game_state == 'dialog':
                prompt_text = prompt_font.render("Ask AI for help", True, BLACK)
                window.blit(prompt_text, (GRID_WIDTH * CELL_SIZE + 10, prompt_y))
                if ai_hint_grid:
                    hint_text = f"AI says: Grid {ai_hint_grid}"
                    hint_surface = button_font.render(hint_text, True, BLACK)
                    window.blit(hint_surface, (GRID_WIDTH * CELL_SIZE + 10, 60))
                    ai_question = button_font.render("AI asks: Where is", True, BLACK)
                    window.blit(ai_question, (GRID_WIDTH * CELL_SIZE + 10, 100))
                    ai_question2 = button_font.render("your bomb?", True, BLACK)
                    window.blit(ai_question2, (GRID_WIDTH * CELL_SIZE + 10, 120))
                    if not dialog_completed:
                        input_prompt = button_font.render("Enter grid number:", True, BLACK)
                        window.blit(input_prompt, (GRID_WIDTH * CELL_SIZE + 10, 150))
                        input_display = button_font.render(input_text or "_", True, BLACK)
                        window.blit(input_display, (GRID_WIDTH * CELL_SIZE + 10, 180))
                else:
                    ask_button_rect = (GRID_WIDTH * CELL_SIZE + 10, 150, 180, 40)
                    pygame.draw.rect(window, (100, 150, 200), ask_button_rect)
                    ask_text = button_font.render("Ask AI", True, WHITE)
                    window.blit(ask_text, (ask_button_rect[0] + 60, ask_button_rect[1] + 10))
            elif game_state == 'player_turn':
                if grid.player_turn:
                    prompt_text = prompt_font.render("Find the bomb", True, BLACK)
                    window.blit(prompt_text, (GRID_WIDTH * CELL_SIZE + 10,
                                              prompt_y))
                else:
                    prompt_text = prompt_font.render("AI's turn...", True, BLACK)
                    window.blit(prompt_text, (GRID_WIDTH * CELL_SIZE + 10,
                                              prompt_y))
            elif game_state == 'game_over':
                result_text = "You win!" if grid.victor == 'Player' else "You lose!"
                prompt_text = prompt_font.render(result_text, True, BLACK)
                window.blit(prompt_text, (GRID_WIDTH * CELL_SIZE + 10, prompt_y))
                try_again_rect = (GRID_WIDTH * CELL_SIZE + 10, 120, 180, 40)
                quit_rect = (GRID_WIDTH * CELL_SIZE + 10, 170, 180, 40)
                pygame.draw.rect(window, (100, 200, 100), try_again_rect)
                pygame.draw.rect(window, (200, 100, 100), quit_rect)
                try_again_text = button_font.render("Try Again", True, WHITE)
                quit_text = button_font.render("Quit", True, WHITE)
                window.blit(try_again_text,
                            (try_again_rect[0] + 50, try_again_rect[1] + 10))
                window.blit(quit_text, (quit_rect[0] + 70, quit_rect[1] + 10))
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    run_game()

