import random
import time
import json
import sys
import os
import logging

from modules.items import ITEM_REGISTRY, ORE_POOL, Item
from modules.actions import MiningAction, InventoryAction, UpgradesAction, ShopAction
from config import (INITIAL_ITEM_CAPACITY, INITIAL_MINING_TIME, INITIAL_MONEY, 
                    INITIAL_INVENTORY, ORE_POOL_SIZE, ITEM_DROP_RANGE, SLOWPRINT_DELAY)

from modules.events import EventManager, HelpStrangerEvent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('game.log')]
)
logger = logging.getLogger(__name__)

class Saves:
    """Class for load & save data to json"""
    def __init__(self, path: str = "save.json"):
        self.path = path
        try:
            with open(self.path, 'r') as f:
                self.__data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.__data = {
                "name": "", 
                "money": INITIAL_MONEY, 
                "inventory": INITIAL_INVENTORY, 
                "itemcapacity": INITIAL_ITEM_CAPACITY, 
                "miningtime": INITIAL_MINING_TIME,
                "eventdefencecounter": 0
            }
            self.save()

    def __getitem__(self, key):
        return self.__data.get(key, f"[WARNING] {key} not found")

    def __setitem__(self, key, value):
        if key not in self.__data:
            raise KeyError
        self.__data[key] = value
        self.save()

    def update_all(self, data: dict):
        """Update all data at once"""
        for key in data:
            if key in self.__data:
                self.__data[key] = data[key]
        self.save()

    def save(self):
        with open(self.path, 'w') as save_file:
            json.dump(self.__data, save_file)


class GameState:
    """Class for store a game state"""
    
    def __init__(self, saves: Saves):
        self.saves = saves if saves else Saves()

        self.inventory: list[Item] = [ITEM_REGISTRY[name]() for name in self.saves["inventory"]]
        self.item_amounts: list[int] = []
        self.money: int = self.saves["money"]
        self.item_capacity: int = self.saves["itemcapacity"]
        self._mining_time: float = self.saves["miningtime"]
        self.ore_pool: list[Item] = []
        self._auto_save_counter = 0
        self._event_defence_counter = self.saves["eventdefencecounter"]

    @property
    def mining_time(self) -> float:
        """Get mining time with minimum bound"""
        return max(0.1, self._mining_time)
    
    @mining_time.setter
    def mining_time(self, value: float):
        """Set mining time with validation"""
        self._mining_time = max(0.1, value)

    @property
    def event_defence_counter(self) -> int:
        return self._event_defence_counter
    
    @event_defence_counter.setter
    def event_defence_counter(self, value: int):
        self._event_defence_counter = max(0, value)


class GameStateService:
    """Service class for game state operations"""
    def __init__(self, state: GameState):
        self.state = state

    def save_state(self):
        """Save current game state to file"""
        data = {
            "name": self.state.saves["name"],
            "money": self.state.money,
            "inventory": [item.__class__.__name__ for item in self.state.inventory],
            "itemcapacity": self.state.item_capacity,
            "miningtime": self.state.mining_time,
            "eventdefencecounter": self.state.event_defence_counter
        }
        self.state.saves.update_all(data) 
        logger.info("Game state saved")

    def clear_inventory(self):
        """Clear the inventory"""
        self.state.inventory = []
        self.save_state()
        logger.info("Inventory cleared")
    
    def add_item_to_inventory(self, item: Item) -> bool:
        """Add item to inventory if capacity allows"""
        if len(self.state.inventory) < self.state.item_capacity:
            self.state.inventory.append(item)
            self.save_state()
            logger.info(f"Added {item.name} to inventory")
            return True
        logger.warning("Failed to add item: Inventory full")
        return False
    

    def add_money(self, amount: int) -> int:
        """Add money with auto-save every 5 transactions"""
        if amount < 0:
            raise ValueError("Amount must be non-negative")

        self.state.money += amount
        self.state._auto_save_counter += 1
        if self.state._auto_save_counter >= 5:
            self.save_state()
            self.state._auto_save_counter = 0
        
        logger.info(f"Added ${amount}, new balance: ${self.state.money}")
        return self.state.money

    def deduct_money(self, amount: int) -> int:
        """Deduct money if sufficient funds exist"""
        if amount < 0:
            raise ValueError("Amount must be non-negative")

        if self.state.money >= amount:
            self.state.money -= amount
            self.save_state()
            logger.info(f"Deducted ${amount}, new balance: ${self.state.money}")
            return self.state.money
        
        return self.state.money
    
    def increase_mining_speed(self, amount: float) -> float:
        """Increase mining speed (decrease mining time)"""
        if amount < 0:
            raise ValueError("Amount must be non-negative")

        self.state.mining_time = max(0.1, self.state.mining_time - amount)
        self.save_state()
        logger.info(f"Mining time increased, new time: {self.state.mining_time}")
        return self.state.mining_time

    def decrease_mining_speed(self, amount: float) -> float:
        """Decrease mining speed (increase mining time)"""
        if amount < 0:
            raise ValueError("Amount must be non-negative")

        self.state.mining_time += amount
        self.save_state()
        logger.info(f"Mining time decreased, new time: {self.state.mining_time}")
        return self.state.mining_time
        

    def increase_item_capacity(self, amount: int = 1) -> int:
        """Increase item capacity"""
        if amount < 0:
            raise ValueError("Amount must be non-negative")

        self.state.item_capacity += amount
        self.save_state()
        logger.info(f"Item capacity increased, new capacity: {self.state.item_capacity}")

        return self.state.item_capacity

    def decrease_item_capacity(self, amount: int = 1) -> int:
        """Decrease item capacity"""
        if amount < 0:
            raise ValueError("Amount must be non-negative")

        self.state.item_capacity = max(1, self.state.item_capacity - amount)
        self.save_state()
        logger.info(f"Item capacity decreased, new capacity: {self.state.item_capacity}")

        return self.state.item_capacity

    def add_event_defence(self, duration: int = 10) -> int:
        """Add event defence for a number of minings"""
        if duration < 0:
            raise ValueError("Duration must be non-negative")
        
        self.state.event_defence_counter += duration
        self.save_state()
        
        logger.info(f"Defent from event effect added for {duration} minings")
        return self.state.event_defence_counter

    def reduce_event_defence(self) -> int:
        """Reduce event defence counter by 1"""
        if self.state.event_defence_counter > 0:
            self.state.event_defence_counter -= 1
            self.save_state()
            logger.info("Event defence counter reduced by 1")
        
        return self.state.event_defence_counter

class UI:
    """Class for user interface methods"""
    
    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_menu(self, state: GameState):
        self.clear()
        print("PyMiner\n\n" + "$" + str(round(state.money)) + 
              "\n\nitem capacity: " + str(state.item_capacity) + 
              "\nmining time: " + str(state.mining_time) + 
              f"\nevent defence: {state.event_defence_counter if state.event_defence_counter > 0 else 'None'}" + 
              "\n\n[1] go mining\n[2] inventory\n[3] upgrades\n[4] shop\n[5] exit\n")

    def print_message(self, message: str):
        print(message)

    def print_inventory(self, items: list, total_value: int):
        self.clear()
        for item in items:
            print(f"{item.name} - ${item.price}")
        print(f"\nTotal inventory value: ${total_value}\n\n[1] sell all\n[2] back\n")

    def print_upgrades(self, money: int, speed_cost: int, capacity_cost: int):
        self.clear()
        print(f"${round(money)}")
        print(f"\n[1] Increase mining speed by 0.2 seconds | ${round(speed_cost)}")
        print(f"[2] Increase item capacity by 1 | ${round(capacity_cost)}")
        print("[3] Exit")

    def slowprint(self, text: str, delay: float = SLOWPRINT_DELAY):
        for c in text + '\n':
            sys.stdout.write(c)
            sys.stdout.flush()
            time.sleep(delay)
            
    def input_choice(self, prompt: str = "choice: ") -> str:
        return input(prompt)

    def wait_for_input(self, prompt: str = "Press enter to continue..."):
        input(prompt)


class Game:
    """Main game class"""
    
    def __init__(self, ui: UI, saves: Saves, event_manager: EventManager):
        self.ui = ui
        self.saves = saves
        self.state = GameState(self.saves)
        self.state_service = GameStateService(self.state)
        self.event_manager = event_manager

        self.actions = {
            "1": MiningAction(),
            "2": InventoryAction(),
            "3": UpgradesAction(),
            "4": ShopAction()
        }
        self._init_loot()

    def _init_loot(self):
        """Initialize loot"""
        for _ in range(ORE_POOL_SIZE):
            self.state.ore_pool.append(random.choice(ORE_POOL)())
            self.state.item_amounts.append(random.randint(*ITEM_DROP_RANGE))
            logger.info("Initialized loot pool and item amounts")
            

    def run(self):
        try:
            if self.state.saves["name"]:
                self.ui.slowprint("Welcome back " + self.state.saves["name"] + "!")
                time.sleep(2)
                logger.info(f"Player {self.state.saves['name']} logged in")
            else:
                self._welcome()

            while True:
                self._menu()
        except KeyboardInterrupt:
            logger.info("Game interrupted by user")
            self.state_service.save_state()
            self.ui.clear()
            print("Game saved. Goodbye!")
            sys.exit(0)

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            self.state_service.save_state()
            raise
    
    def _welcome(self):
        self.ui.slowprint("Welcome to PyMiner, what's your name? ")
        name = input("")
        self.state.saves["name"] = name
        self.state_service.save_state()
        self.ui.slowprint("Hello " + name + "!")
        time.sleep(2)

    def _menu(self):
        self.ui.print_menu(self.state)
        choice = self.ui.input_choice()

        if choice in self.actions:
            self.actions[choice].execute(self.state, self.state_service, self.ui)
            logger.info(f"Executed action {choice}")

               

            if choice == "1" and self.state.event_defence_counter <= 0:
                # Check for random event after mining action
                self.event_manager.trigger_random_event(self.state, self.state_service, self.ui)

        elif choice == "5":
            self.state_service.save_state()
            sys.exit()

        elif choice == "debug":
            self.event_manager.trigger_specific_event(HelpStrangerEvent, self.state, self.state_service, self.ui)
        else:
            self.ui.clear()
            print("Invalid choice!")
            time.sleep(1)


if __name__ == "__main__":
    game = Game(UI(), Saves(), EventManager(logger))
    game.run()
    logger.info("Game initialized successfully")