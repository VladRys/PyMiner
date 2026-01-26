from typing import Any

class Item:
    def __init__(self):
        self.name = ""
        self.price = 0

    def __str__(self):
        return self.name
    
    def __eq__(self, other):
        if not isinstance(other, Item):
            raise NotImplemented
        
        return self.price == other.price

    def __gt__(self, other):
        if not isinstance(other, Item):
            raise NotImplemented

        return self.price > other.price

    def __lt__(self, other):
        if not isinstance(other, Item):
            raise NotImplemented

        return self.price < other.price
    
class Stone(Item):
    def __init__(self):
        self.name = "Stone"
        self.price = 2
    
class Coal(Item):
    def __init__(self):
        self.name = "Coal"
        self.price = 5

    
class Iron(Item):
    def __init__(self):
        self.name = "Iron"
        self.price = 15

    
class Gold(Item):
    def __init__(self):
        self.name = "Gold"
        self.price = 30

    
class Diamond(Item):
    def __init__(self):
        self.name = "Diamond"
        self.price = 75

ITEM_REGISTRY = {
    "Stone": Stone,
    "Coal": Coal,
    "Iron": Iron,
    "Gold": Gold,
    "Diamond": Diamond
}
ORE_POOL = [Stone, Coal, Iron, Gold, Diamond]