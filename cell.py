# cell.py
from random import choice

class Cell:
    def __init__(self):
        self.revealed = False
        self.item_type = 'Empty'
