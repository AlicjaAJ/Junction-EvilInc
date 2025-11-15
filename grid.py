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
