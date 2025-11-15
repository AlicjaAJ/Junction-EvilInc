import pygame

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (100, 150, 255)

class Menu:
    def __init__(self, window, width, height):
        self.window = window
        self.width = width
        self.height = height
        self.font = pygame.font.SysFont(None, 36)
        self.options = [("Easy", (5, 5)), ("Medium", (8, 8)), ("Hard", (10, 10))]
        self.selected = 0
        self.running = True

    def draw(self):
        self.window.fill(WHITE)
        title = self.font.render("Select Level", True, BLACK)
        self.window.blit(title, ((self.width - title.get_width()) // 2, 50))

        for i, (name, _) in enumerate(self.options):
            color = BLUE if i == self.selected else GRAY
            rect = pygame.Rect(100, 150 + i * 60, self.width - 200, 50)
            pygame.draw.rect(self.window, color, rect)
            pygame.draw.rect(self.window, BLACK, rect, 2)
            text_surf = self.font.render(name, True, BLACK)
            self.window.blit(text_surf, (rect.x + (rect.width - text_surf.get_width()) // 2,
                                         rect.y + (rect.height - text_surf.get_height()) // 2))

        pygame.display.flip()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                self.running = False  # level selected

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                self.handle_event(event)
            self.draw()
            clock.tick(60)

        return self.options[self.selected][1]  # return selected grid size
