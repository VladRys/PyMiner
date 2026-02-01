class Item:
    def __init__(self):
        self.name = ""
        self.price = 0
        self.chance = 0.0

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
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, price={self.price})"
    
class Stone(Item):
    def __init__(self):
        self.name = "Stone"
        self.price = 2
        self.chance = 0.4

class Coal(Item):
    def __init__(self):
        self.name = "Coal"
        self.price = 5
        self.chance = 0.3
    
class Iron(Item):
    def __init__(self):
        self.name = "Iron"
        self.price = 15
        self.chance = 0.2

    
class Gold(Item):
    def __init__(self):
        self.name = "Gold"
        self.price = 30
        self.chance = 0.1

    
class Diamond(Item):
    def __init__(self):
        self.name = "Diamond"
        self.price = 75
        self.chance = 0.05

class Emerald(Item):
    def __init__(self):
        self.name = "Emerald"
        self.price = 100
        self.chance = 0.03

class Ruby(Item):
    def __init__(self):
        self.name = "Ruby"
        self.price = 150
        self.chance = 0.02

ITEM_REGISTRY = {
    "Stone": Stone,
    "Coal": Coal,
    "Iron": Iron,
    "Gold": Gold,
    "Diamond": Diamond,
    "Emerald": Emerald,
    "Ruby": Ruby
}

ORE_POOL = [Stone, Coal, Iron, Gold, Diamond, Emerald, Ruby]