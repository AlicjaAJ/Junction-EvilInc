import pygame
from grid import Grid
from textbox import TextBox
from menu import Menu
from victory_screen import VictoryScreen

WHITE = (255, 255, 255)
RIGHT_PANEL_WIDTH = 200

def run_game():
    pygame.init()
    WINDOW_WIDTH, WINDOW_HEIGHT = 800, 400
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Grid Game with Menu")

    while True:
        # Show menu
        menu = Menu(window, WINDOW_WIDTH, WINDOW_HEIGHT)
        grid_size = menu.run()
        if grid_size is None:
            break  # exit

        GRID_WIDTH, GRID_HEIGHT = grid_size
        CELL_SIZE = 40
        grid = Grid(GRID_WIDTH, GRID_HEIGHT, CELL_SIZE)

        # Position textbox
        text_box_height = 40
        text_box = TextBox(GRID_WIDTH * CELL_SIZE + 20,
                           WINDOW_HEIGHT - text_box_height - 20,
                           RIGHT_PANEL_WIDTH - 40,
                           text_box_height,
                           visible_lines=6)

        player_bomb_insertion = True
        clock = pygame.time.Clock()

        while grid.run_status():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    if x < GRID_WIDTH * CELL_SIZE:
                        player_bomb_insertion = grid.handle_click(x, y, player_bomb_insertion)
                # Pass events to textbox
                text_box.handle_event(event)

            window.fill(WHITE)
            grid.draw(window)
            pygame.draw.rect(window, (200, 200, 200), (GRID_WIDTH * CELL_SIZE, 0, RIGHT_PANEL_WIDTH, WINDOW_HEIGHT))
            text_box.draw(window)
            pygame.display.flip()
            clock.tick(60)

            # Check if player won
            if not grid.run_status():
                victory = VictoryScreen(window, WINDOW_WIDTH, WINDOW_HEIGHT, "Player")
                victory.run()
                break  # back to menu

    pygame.quit()

if __name__ == "__main__":
    run_game()
