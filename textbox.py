import pygame

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (180, 220, 255)

class TextBox:
    def __init__(self, x, y, width, height, font_size=24, visible_lines=6):
        self.rect = pygame.Rect(x, y, width, height)  # input box
        self.color = WHITE
        self.text = ""
        self.active = False
        self.font = pygame.font.SysFont(None, font_size)
        self.submitted_text = None
        self.lines = []  # all submitted lines
        self.scroll_offset_y = 0
        self.scroll_offset_x = 0
        self.line_height = font_size + 4
        self.visible_lines = visible_lines  # vertical lines visible in scroll area
        self.scroll_area_height = self.visible_lines * self.line_height

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                if self.text.strip() != "":
                    self.submitted_text = self.text
                    self.lines.append(self.text)
                    self.text = ""
                    # auto-scroll to bottom and left
                    self.scroll_offset_y = max(len(self.lines) - self.visible_lines, 0)
                    self.scroll_offset_x = 0
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
        elif event.type == pygame.MOUSEWHEEL:
            # vertical scrolling
            if len(self.lines) > self.visible_lines:
                self.scroll_offset_y -= event.y
                self.scroll_offset_y = max(0, min(self.scroll_offset_y, len(self.lines) - self.visible_lines))
        elif event.type == pygame.KEYDOWN:
            # horizontal scrolling with arrow keys
            if event.key == pygame.K_LEFT:
                self.scroll_offset_x = max(self.scroll_offset_x - 10, 0)
            elif event.key == pygame.K_RIGHT:
                self.scroll_offset_x += 10

    def draw(self, surface):
        # Draw input box at bottom
        pygame.draw.rect(surface, BLUE if self.active else GRAY, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        text_surf = self.font.render(self.text, True, BLACK)
        # Clip text if too wide
        surface.set_clip(self.rect)
        surface.blit(text_surf, (self.rect.x + 5, self.rect.y + 5))
        surface.set_clip(None)

        # Draw scrollable area
        scroll_rect = pygame.Rect(self.rect.x, self.rect.y - self.scroll_area_height - 5, self.rect.width, self.scroll_area_height)
        pygame.draw.rect(surface, WHITE, scroll_rect)
        pygame.draw.rect(surface, BLACK, scroll_rect, 2)

        # Draw visible lines with horizontal scroll
        start = self.scroll_offset_y
        end = start + self.visible_lines
        visible_lines = self.lines[start:end]

        # Clip scroll area
        surface.set_clip(scroll_rect)
        for i, line in enumerate(visible_lines):
            y = scroll_rect.y + i * self.line_height
            # Render text and clip to scroll_rect width
            line_surf = self.font.render(line, True, BLACK)
            surface.blit(line_surf, (scroll_rect.x + 5 - self.scroll_offset_x, y))
        surface.set_clip(None)

    def get_submitted_text(self):
        return self.submitted_text
