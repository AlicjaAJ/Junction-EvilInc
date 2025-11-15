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

    def ai_reveal(self):
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

    def draw(self, surface, font):
        for x in range(self.width):
            for y in range(self.height):
                cell = self.cells[x][y]
                rect = (x * self.cell_size, y * self.cell_size,
                        self.cell_size, self.cell_size)
                pygame.draw.rect(surface, BLACK, rect, 1)
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


def run_game():
    pygame.init()
    GRID_WIDTH = 5
    GRID_HEIGHT = 5
    CELL_SIZE = 40
    RIGHT_PANEL_WIDTH = 200
    WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE + RIGHT_PANEL_WIDTH
    WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Bomb Hunt Game")
    grid = Grid(GRID_WIDTH, GRID_HEIGHT, CELL_SIZE)
    font = pygame.font.SysFont(None, 24)
    prompt_font = pygame.font.SysFont(None, 32)
    button_font = pygame.font.SysFont(None, 28)
    game_state = 'bomb_placement'
    ai_turn_pending = False
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if game_state == 'game_over':
                    try_again_rect = (GRID_WIDTH * CELL_SIZE + 10, 120, 180, 40)
                    quit_rect = (GRID_WIDTH * CELL_SIZE + 10, 170, 180, 40)
                    if check_button_click(x, y, try_again_rect):
                        grid.reset()
                        game_state = 'bomb_placement'
                        ai_turn_pending = False
                    elif check_button_click(x, y, quit_rect):
                        running = False
                elif x < GRID_WIDTH * CELL_SIZE:
                    if game_state == 'bomb_placement':
                        if grid.handle_click(x, y, game_state):
                            grid.place_ai_bomb()
                            game_state = 'player_turn'
                    elif game_state == 'player_turn' and grid.player_turn:
                        if grid.handle_click(x, y, game_state):
                            ai_turn_pending = True
        if ai_turn_pending and game_state == 'player_turn' and not grid.player_turn:
            pygame.time.wait(500)
            grid.ai_reveal()
            if grid.victor:
                game_state = 'game_over'
            else:
                grid.player_turn = True
            ai_turn_pending = False
        window.fill(WHITE)
        grid.draw(window, font)
        pygame.draw.rect(window, PANEL_COLOR,
                         (GRID_WIDTH * CELL_SIZE, 0, RIGHT_PANEL_WIDTH,
                          WINDOW_HEIGHT))
        prompt_y = 20
        if game_state == 'bomb_placement':
            prompt_text = prompt_font.render("Hide your bomb", True, BLACK)
            window.blit(prompt_text, (GRID_WIDTH * CELL_SIZE + 10, prompt_y))
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

