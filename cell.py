# cell.py
from random import choice

class Cell:
    def __init__(self):
        self.revealed = False
        self.item_type = None

    def add_item(self,item):
        self.item_type = item

