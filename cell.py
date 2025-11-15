"""
Cell Module

Represents a single cell in the game grid.
Each cell can contain a bomb or be empty, and can be revealed or hidden.
"""


class Cell:
    """
    Represents a single cell in the game grid.

    A cell can:
    - Contain a bomb (item_type = ('P', 'B') for player or ('A', 'B') for AI)
    - Be revealed or hidden
    - Track who revealed it (for color coding)
    """

    def __init__(self):
        """Initialize a new cell as empty and unrevealed."""
        self.revealed = False  # Whether this cell has been revealed
        self.item_type = None  # ('P', 'B') or ('A', 'B') if bomb, None if empty
        self.revealed_by = None  # 'player' or 'ai' - who revealed this cell

    def add_item(self, item):
        """
        Place an item (bomb) in this cell.

        Args:
            item: Tuple like ('P', 'B') for player bomb or ('A', 'B') for AI bomb
        """
        self.item_type = item

    def reveal(self, revealed_by):
        """
        Mark this cell as revealed.

        Args:
            revealed_by: 'player' or 'ai' - who revealed this cell
        """
        self.revealed = True
        self.revealed_by = revealed_by

