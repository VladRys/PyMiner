import random
import time
import json
import sys
import os

from items import *

class Saves:
    """Class for load & save data to json"""
    def __init__(self, path: str = "save.json"):
        self.path = path
        self.__data = json.load(open(self.path))
        
    def __str__(self):
        return f"{self.__data}"

    def __getitem__(self, key):
        return self.__data.get(key, f"[WARNING] {key} not found")

    def __setitem__(self, key, value):
        if key not in self.__data:
            raise KeyError
        
        self.__data[key] = value 
        with open(self.path, 'w') as save_file: json.dump(self.__data, save_file)

save = Saves()

class GameState:
    """Class for store a game state"""
    INVENTORY: list[Item] = [ITEM_REGISTRY[name]() for name in save["inventory"]]
    ITEMAMT: list = []
    MONEY: int = save["money"]
    ITEM_CAPACITY: int = save["itemcapacity"]
    MINING_TIME = save["miningtime"]
    ORE: list[Item] = [] 



class Game:
    def __init__(self):
        self.loot_generator(5, GameState.ORE, GameState.ITEMAMT)

    def run(self):
        if save["name"]:
            self.slowprint("Welcome back " + save["name"] + "!")
            time.sleep(2)
        
        else:
            self.welcome()

        while True:
            self.menu()

    def loot_generator(self, size: int, ore_list: list, amt_list: list):
        for _ in range(size):
            ore_list.append(random.choice(ORE_POOL)())
            amt_list.append(random.randint(1,2))

    def show_inventory(self):
        os.system("cls")
        totalval = 0
        for item in GameState.INVENTORY:
            print(item.name + " - $" + str(self.get_item_price(item)))
            totalval += self.get_item_price(item)
 
        print("\nTotal inventory value: $" + str(totalval) + "\n\n[1] sell all\n[2] back\n")
        choice = input("choice: ")
        
        if choice == "1":
            GameState.MONEY += totalval
            GameState.INVENTORY = []

        if choice == "2":
            return

    def get_item_price(self, item: Item):
        return item.price
    
    def upgrades(self):
        capacity_increase_cost = GameState.ITEM_CAPACITY * 25
        speed_increase_cost = 100-GameState.MINING_TIME*30

        os.system("cls")
        print("$"+str(round(GameState.MONEY)))
        print("\n[1] Increase mining speed by 0.2 seconds | $"+str(round(speed_increase_cost)))
        print("[2] Increase item capacity by 1 | $"+str(round(capacity_increase_cost)))
        print("[3] Exit")
        choice = input("\nchoice: ")

        if choice == "1" and GameState.MONEY >= speed_increase_cost:
            GameState.MONEY -= speed_increase_cost
            GameState.MINING_TIME -= 0.2
            os.system("cls")
            print("Mining speed has been increased!")
            time.sleep(1.5)
            self.upgrades()
            
        if choice == "2" and GameState.MONEY >= capacity_increase_cost:
            GameState.MONEY -= capacity_increase_cost
            GameState.ITEM_CAPACITY += 1
            os.system("cls")
            print("Item capacity has been increased!")
            time.sleep(1.5)
            self.upgrades()

        if choice == "3":
            return

    def mine(self):
        if len(GameState.INVENTORY) >= GameState.ITEM_CAPACITY:
            os.system("cls")
            print("Inventory is full")
            time.sleep(2)
            self.menu() 
            return
        
        step = GameState.MINING_TIME / 3
        
        for dots in range(1, 4):
            os.system("cls")
            print(f"mining{'.' * dots}")
            time.sleep(step)

        os.system("cls")
        print("Done!\n")
        
        if len(GameState.INVENTORY) == GameState.ITEM_CAPACITY - 1: 
            item = random.choice(GameState.ORE)
            price = self.get_item_price(item)
            print(f"{item} - ${price}")
            GameState.INVENTORY.append(item)
        else:
            for x in range(random.choice(GameState.ITEMAMT)):
                item = random.choice(GameState.ORE)
                print(item.name + " - $" + str(self.get_item_price(item)))
                GameState.INVENTORY.append(item)

        input("\nPress enter to continue...")
        return
    

    def menu(self):
        os.system("cls")
        print("pyminer\n\n"+"$"+str(round(GameState.MONEY))+"\n\nitem capacity: "+str(GameState.ITEM_CAPACITY)+"\nmining time: "+str(GameState.MINING_TIME)+"\n\n[1] go mining\n[2] inventory\n[3] upgrades\n[4] exit\n")
        choice = input("choice: ")
        if choice == "1":self.mine()
        if choice == "2":self.show_inventory()
        if choice == "3":self.upgrades()
        if choice == "4":
            data = {
                "name": save["name"],
                "money": GameState.MONEY,
                "inventory": [item.__class__.__name__ for item in GameState.INVENTORY],
                "itemcapacity": GameState.ITEM_CAPACITY,
                "miningtime": GameState.MINING_TIME
            }
            with open('save.json', 'w') as save_file:json.dump(data, save_file)
            sys.exit()

    def slowprint(self, s):
        for c in s + '\n':
            sys.stdout.write(c)
            sys.stdout.flush()
            time.sleep(.4/10)

    def welcome(self):
        self.slowprint("Welcome to pyminer, what's your name? ")
        name = input("")
        save["name"] = name
        data = {
                "name": save["name"],
                "money": GameState.MONEY,
                "inventory": [item.__class__.__name__ for item in GameState.INVENTORY],
                "itemcapacity": GameState.ITEM_CAPACITY,
                "miningtime": GameState.MINING_TIME
        }
        
        with open('save.json', 'w') as save_file:
            json.dump(data, save_file)

        self.slowprint("Hello " + data["name"] + "!")
        time.sleep(2)

game = Game()
game.run()