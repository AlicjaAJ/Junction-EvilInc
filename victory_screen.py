import pygame

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)

class VictoryScreen:
    def __init__(self, window, width, height, winner):
        self.window = window
        self.width = width
        self.height = height
        self.font = pygame.font.SysFont(None, 48)
        self.winner = winner

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    running = False
            self.window.fill(WHITE)
            text = self.font.render(f"{self.winner} Wins!", True, BLACK)
            self.window.blit(text, ((self.width - text.get_width()) // 2,
                                    (self.height - text.get_height()) // 2))
            prompt = self.font.render("Press any key to continue", True, GRAY)
            self.window.blit(prompt, ((self.width - prompt.get_width()) // 2,
                                      (self.height - prompt.get_height()) // 2 + 60))
            pygame.display.flip()
            clock.tick(60)
