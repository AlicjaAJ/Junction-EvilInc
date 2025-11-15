# grid.py
import pygame

from cell import Cell


WHITE = (255, 255, 255)

BLACK = (0, 0, 0)
CELL_COLOR = (180, 220, 255)


class Grid:

    def run_status(self):
        return self.running

    def __init__(self, width, height, cell_size):

        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.cells = [[Cell() for _ in range(height)] for _ in range(width)]
        self.running = True



    def handle_click(self, x, y,player_bomb_insertion):

        col = x // self.cell_size
        row = y // self.cell_size

        if player_bomb_insertion:
            self.cells[col][row].add_item(('P','B'))
            return False


        self.cells[col][row].revealed = True
        return False


    def victory(self,victor):
        self.running=False
        print(victor)

    def draw(self, surface):

        for x in range(self.width):
            for y in range(self.height):

                cell = self.cells[x][y]
                rect = (x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                pygame.draw.rect(surface, BLACK, rect, 1)


                if cell.revealed:

                    pygame.draw.rect(surface, CELL_COLOR, rect)
                    if cell.item_type:
                        font = pygame.font.SysFont(None, 24)
                        text = font.render(cell.item_type[0], True, BLACK)
                        surface.blit(text, (x * self.cell_size + 5, y * self.cell_size + 5))
                        if cell.item_type[0]=='P':
                            self.victory('Player')




def run_game():
    pygame.init()

    GRID_WIDTH = 5
    GRID_HEIGHT = 5
    CELL_SIZE = 40


    # Window dimensions (with right-side empty section)

    RIGHT_PANEL_WIDTH = 200
    WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE + RIGHT_PANEL_WIDTH
    WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE


    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Simple Grid Game")
    grid = Grid(GRID_WIDTH, GRID_HEIGHT, CELL_SIZE)

    player_bomb_insertion=True



    while grid.run_status():

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                grid.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if x < GRID_WIDTH * CELL_SIZE:
                    player_bomb_insertion=grid.handle_click(x, y,player_bomb_insertion)


        window.fill(WHITE)
        grid.draw(window)
        pygame.draw.rect(window, (200, 200, 200), (GRID_WIDTH * CELL_SIZE, 0, RIGHT_PANEL_WIDTH, WINDOW_HEIGHT))
        pygame.display.flip()


    pygame.quit()


if __name__ == "__main__":
    run_game()

