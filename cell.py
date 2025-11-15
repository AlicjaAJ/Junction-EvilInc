# cell.py

class Cell:
    def __init__(self):
        self.revealed = False
        self.item_type = None
        self.revealed_by = None

    def add_item(self, item):
        self.item_type = item

    def reveal(self, revealed_by):
        self.revealed = True
        self.revealed_by = revealed_by

