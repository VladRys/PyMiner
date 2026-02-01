from dataclasses import dataclass
import time
import random
from abc import ABC, abstractmethod
from config import (MINING_ANIMATION_FRAMES, UPGRADE_CAPACITY_MULTIPLIER, UPGRADE_SPEED_BASE, 
                    UPGRADE_SPEED_FACTOR, UPGRADE_SPEED_DECREASE, 
                    UPGRADE_SPEED_MIN_COST, CHOICE_TIMEOUT)

class Action(ABC):
    """Abstract class for all actions"""

    @abstractmethod
    def execute(self, state, state_service, ui) -> bool:
        """
        Execute the action. Returns True to return to menu
        
        :param state: GameState
        :param state_service: GameStateService
        :param ui: UI
        :return: bool
        """
        pass

class MiningAction(Action):
    """Mining logic"""

    def execute(self, state, state_service, ui) -> bool:
        if len(state.inventory) >= state.item_capacity:
            ui.clear()
            ui.print_message("Inventory is full")
            time.sleep(2)
            return True

        step = state.mining_time / MINING_ANIMATION_FRAMES

        for dots in range(1, 4):
            ui.clear()
            ui.print_message(f"mining{'.' * dots}")
            time.sleep(step)

        ui.clear()
        ui.print_message("Done!\n")

        items_to_add = random.choice(state.item_amounts)
        for _ in range(items_to_add):
                item = random.choice(state.ore_pool)
                if state_service.add_item_to_inventory(item):
                    ui.print_message(f"{item.name} - ${item.price}")
                else:
                    break
                

        ui.wait_for_input("\nPress enter to continue...")
        state_service.reduce_event_defence()
        
        return True
    
class InventoryAction(Action):
    """Inventory management logic"""

    def execute(self, state, state_service, ui) -> bool:
        while True:
            total_value = sum(item.price for item in state.inventory)
            ui.print_inventory(state.inventory, total_value)

            choice = ui.input_choice()

            if choice == "1":
                self._sell_inventory(state, state_service, ui)
                time.sleep(1.5)

                return True
            elif choice == "2":
                return True
            else:
                ui.clear()
                ui.print_message("Invalid choice!")
                time.sleep(CHOICE_TIMEOUT)

    def _sell_inventory(self, state, state_service, ui) -> int:
        total = sum(item.price for item in state.inventory)
        state_service.add_money(total)
        state_service.clear_inventory()
        
        ui.clear()
        ui.print_message(f"Sold all items for ${total}!")
        
        return total

class UpgradesAction(Action):
    """Upgrades management logic"""
    
    def execute(self, state, state_service, ui) -> bool:
        while True:
            capacity_cost = state.item_capacity * UPGRADE_CAPACITY_MULTIPLIER
            speed_cost = max(UPGRADE_SPEED_MIN_COST, 
                           UPGRADE_SPEED_BASE - state.mining_time * UPGRADE_SPEED_FACTOR)

            ui.print_upgrades(state.money, speed_cost, capacity_cost)
            choice = ui.input_choice()

            if choice == "1":
                self._upgrade_speed(state, state_service, ui)
                state_service.save_state()

            elif choice == "2":
                self._upgrade_capacity(state, state_service, ui)
                state_service.save_state()
            
            elif choice == "3":
                state_service.save_state()
                return True
            else:
                ui.clear()
                ui.print_message("Invalid choice!")
                time.sleep(CHOICE_TIMEOUT)

    def _upgrade_speed(self, state, state_service, ui) -> bool:
        cost = max(UPGRADE_SPEED_MIN_COST, 
                   UPGRADE_SPEED_BASE - state.mining_time * UPGRADE_SPEED_FACTOR)

        if state.money >= cost:
            state_service.deduct_money(cost)
            state_service.increase_mining_speed(UPGRADE_SPEED_DECREASE * state.mining_time)

            ui.clear()
            ui.print_message("Mining speed has been increased!")
            time.sleep(1.5)

            return True
        else:
            ui.clear()
            ui.print_message("Not enough money!")
            time.sleep(1.5)

            return False

    def _upgrade_capacity(self, state, state_service, ui) -> bool:
        cost = state.item_capacity * UPGRADE_CAPACITY_MULTIPLIER

        if state.money >= cost:
            state_service.deduct_money(cost)
            state_service.increase_item_capacity(1)

            ui.clear()
            ui.print_message("Item capacity has been increased! Current capacity: " + str(state.item_capacity))
            time.sleep(1.5)

            return True
        else:
            ui.clear()
            ui.print_message("Not enough money!")
            time.sleep(1.5)

            return False

class Deal:
    def __init__(self) -> None:
        self.name = "Deal Name"
        self.cost = 0
        self.description = "Do something special"

    """Shop deal abstract class"""
    @abstractmethod
    def apply_deal(self, state, state_service, ui) -> bool:
        pass

class GodBlessDeal(Deal):
    def __init__(self) -> None:
        self.name = "God bless."
        self.cost = 100
        self.description = "Defend yourself from all events for 10 minings"

    def apply_deal(self, state, state_service, ui) -> bool:
        if state.money >= self.cost:
            state_service.deduct_money(self.cost)
            state_service.add_event_defence(10)

            ui.clear()
            ui.print_message("You are now protected from all events for the next 10 minings!")
            time.sleep(1.5)

            return True
        else:
            ui.clear()
            ui.print_message("Not enough money!")
            time.sleep(1.5)

            return False


class ShopAction(Action):
    """Shop management logic"""
    def __init__(self) -> None:
        self.greeting_messages = [
            "... Who is there? Oh, it's you! Welcome to my shop!",
            "Looking for something special, stranger?",
            "Find the best deals here!",
            "Your adventure starts with the right gear!"
            ]
        
        self.options = {
            "1": "Look at deals",
            "2": "Leave shop"
        }

        self.deals: dict[str, Deal] = {
            "1": GodBlessDeal()
        }
        
    def execute(self, state, state_service, ui) -> bool:
        while True:
            ui.clear()
            ui.slowprint(random.choice(self.greeting_messages) + "\n")
            for key, value in self.options.items():
                ui.print_message(f"[{key}] {value}")

            choice = ui.input_choice()
    
            if choice.isdigit():
                choice = int(choice)
                if choice in [int(key) for key in self.options.keys()]:
                    if choice == 1:
                        ui.clear()
                        for key, deal in self.deals.items():
                            ui.print_message(f"[{key}] {deal.name}: {deal.description} (Cost: ${deal.cost})")
                        
                        choice = ui.input_choice("That's a good deals! I'll take it.\nChoose a deal number or press enter to go back: ")
                        if choice in self.deals.keys():
                            self._buy_deal(self.deals[choice], state, state_service, ui)
                            time.sleep(1.5)

                        else:
                            ui.clear()
                            ui.print_message("Returning to shop menu...")
                            time.sleep(1.5)
                        

                    elif choice == 2:
                        state_service.save_state()
                        return True
                    
                else:
                    ui.clear()
                    ui.print_message("Invalid choice!")
                    time.sleep(CHOICE_TIMEOUT)

            else:
                ui.clear()
                ui.print_message("Invalid choice!")
                time.sleep(CHOICE_TIMEOUT)
    
    def _buy_deal(self, deal: Deal, state, state_service, ui) -> bool:
        return deal.apply_deal(state, state_service, ui)

