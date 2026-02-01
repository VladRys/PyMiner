import time
import random

from config import BASIC_EVENT_PRINT_DELAY, CONSQ_EVENT_PRINT_DELAY, DECREASE_SPEED_EVENT_AREA, BASIC_EVENT_CHANCE


class EventManager:
    """Manages random events with probabilities"""
    
    def __init__(self, logger):
        self.logger = logger
        self.events_chances = {
            TraumaEvent: 0.1, 
            Event: 0.1,
            LuckyEvent: 0.1,
            EquipmentFailureEvent: 0.1,
            HelpStrangerEvent: 0.1,
        }
    
    def should_trigger(self) -> bool:
        """Determine if an event should be triggered based on BASIC_EVENT_CHANCE"""
        return random.random() < BASIC_EVENT_CHANCE
    
    def get_random_event(self):
        """Return a random event based on probabilities"""
        return random.choices(
            list(self.events_chances.keys()), 
            weights=list(self.events_chances.values()), 
            k=1
        )[0]
    
    def trigger_random_event(self, state, state_service, ui):
        """Trigger a random event if conditions are met"""
        if self.should_trigger():
            event_class = self.get_random_event()
            event = event_class(state, state_service, ui)
            event.trigger()
            self.logger.info(f"Random event triggered: {event_class.__name__}")

    def trigger_specific_event(self, event_class, state, state_service, ui):
        """Trigger a specific event"""
        event = event_class(state, state_service, ui)
        event.trigger()
        self.logger.info(f"Specific event triggered: {event_class.__name__}")

class Event:
    """Base class for events"""
    def __init__(self, state, state_service, ui):
        """
        :param state: GameState
        :param state_service: GameStateService
        :param ui: UI
        """
        self.state = state
        self.state_service = state_service
        self.ui = ui

        self.description = "An event has occurred."
        self.conseq = "Nothing happened."


    def trigger(self) -> None:
        """Trigger the event"""
        self.ui.clear()
        
        self.ui.slowprint("Event Triggered!", delay = BASIC_EVENT_PRINT_DELAY)
        time.sleep(1.5)
        
        self.ui.clear()
        self.ui.slowprint(self.description, delay = BASIC_EVENT_PRINT_DELAY)
        
        time.sleep(len(self.description) * BASIC_EVENT_PRINT_DELAY + 1)
        
        self._apply_consequence()

        self.ui.clear()
        self.ui.slowprint(self.conseq, delay = CONSQ_EVENT_PRINT_DELAY)

        self.ui.wait_for_input("\nPress enter to continue...")

    def _apply_consequence(self) -> bool:
        """Apply the consequence of the event"""
        return True

class TraumaEvent(Event):
    """Trauma event logic"""
    def __init__(self, state, state_service, ui):
        super().__init__(state, state_service, ui)
        self.description = "You suffered a traumatic injury while mining!"
        self.conseq = "You lost some mining speed."

    def _apply_consequence(self) -> bool:
        self.state_service.decrease_mining_speed(random.randint(*DECREASE_SPEED_EVENT_AREA) / 10)
        return True

class LuckyEvent(Event):
    """Lucky event logic"""
    def __init__(self, state, state_service, ui):
        super().__init__(state, state_service, ui)
        self.description = "You found a lucky break while mining!"
        self.conseq = "You gained some money."

    def _apply_consequence(self) -> bool:
        self.state_service.add_money(random.randint(10, 50))
        return True
    
class EquipmentFailureEvent(Event):
    """Equipment failure event logic"""
    def __init__(self, state, state_service, ui):
        super().__init__(state, state_service, ui)
        self.description = "Your mining equipment has failed!"
        self.conseq = "You lost some money to repair it."

    def _apply_consequence(self) -> bool:
        if self.state.money < 10:
            self.conseq = "You don't have enough money to repair the equipment. You lost all your money."
            self.state_service.deduct_money(self.state.money)
            return True
        
        max_repair_cost = max(10, self.state.money // 2)
        repair_cost = random.randint(10, max_repair_cost)

        self.conseq = f"You paid ${repair_cost} to repair your equipment."

        self.state_service.deduct_money(repair_cost)
        return True


class Consequence:
    """Base class for choice-event consequence"""
    def __init__(self, state, state_service):
        self.state = state
        self.state_service = state_service
        self.description = "Something happened."
    
    def apply(self) -> bool:
        """Apply the consequence to the game state"""
        raise NotImplementedError("Subclasses must implement apply()")


class EventWithChoice(Event):
    """Base class for events with player choices
    
    Subclasses should define:
    - self.description: event description
    - self.available_choices: dict {"key": "display name"}
    - self.choice_consequences: dict {"key": {"good": [Consequence], "bad": [Consequence]}}
    """
    
    def __init__(self, state, state_service, ui):
        super().__init__(state, state_service, ui)
        self.available_choices = {}
        self.choice_consequences = {}
        self.selected_consequence = None

    def trigger(self) -> None:
        """Trigger the event with choice"""
        self.ui.clear()
        
        self.ui.slowprint("Event Triggered!", delay=BASIC_EVENT_PRINT_DELAY)
        time.sleep(1.5)
        
        self.ui.clear()
        self.ui.slowprint(self.description, delay=BASIC_EVENT_PRINT_DELAY)

        for key, option_name in self.available_choices.items():
            self.ui.slowprint(f"[{key}]: {option_name}", delay=BASIC_EVENT_PRINT_DELAY)
        
        choice = self._get_valid_choice()
        
        self.selected_consequence = self._select_consequence(choice)
        
        if self.selected_consequence:
            self.selected_consequence.apply()

        self.ui.clear()
        self.ui.slowprint(self.selected_consequence.description, delay=CONSQ_EVENT_PRINT_DELAY)
        self.ui.wait_for_input("\nPress enter to continue...")

    def _get_valid_choice(self) -> str:
        """Get valid choice from player with retry logic"""
        max_attempts = 3
        for attempt in range(max_attempts):
            choice = self.ui.input_choice("Your choice: ")
            if choice in self.available_choices:
                return choice
            remaining = max_attempts - attempt - 1
            if remaining > 0:
                self.ui.slowprint(f"Invalid choice. Try again ({remaining} attempts left).", delay=BASIC_EVENT_PRINT_DELAY)
        
        return list(self.available_choices.keys())[0]

    def _select_consequence(self, choice: str) -> Consequence:
        """Randomly select good or bad consequence for the choice"""
        consequence_pool = self.choice_consequences[choice]
        
        # 50/50 chance for good or bad
        consequence_type = random.choice(["good", "bad"])
        consequence_callable = random.choice(consequence_pool[consequence_type])
        
        return consequence_callable()

class MoneyGainConsequence(Consequence):
    """Gain a random amount of money"""
    def __init__(self, state, state_service, gain: int, description: str):
        super().__init__(state, state_service)
        self.amount = gain
        self.description = description

    def apply(self) -> bool:
        self.state_service.add_money(self.amount)
        return True
    
class SpeedGainConsequence(Consequence):
    def __init__(self, state, state_service, gain, description):
        super().__init__(state, state_service)
        self.gain = gain
        self.description = description
    
    def apply(self) -> bool:
        self.state_service.increase_mining_speed(self.gain)
        return True

class MoneyLossConsequence(Consequence):
    """Lose a random amount of money"""
    def __init__(self, state, state_service, loss: int, description: str):
        super().__init__(state, state_service)
        self.amount = loss
        self.description = description


    def apply(self) -> bool:
        self.state_service.deduct_money(self.amount)
        return True


class SpeedLossConsequence(Consequence):
    def __init__(self, state, state_service, loss, description):
        super().__init__(state, state_service)
        self.loss = loss
        self.description = description
    
    def apply(self) -> bool:
        self.state_service.decrease_mining_speed(self.loss)
        return True
    
class HelpStrangerEvent(EventWithChoice):
    """
    Player can choose to help a stranger or ignore them.
    Each choice leads to random good/bad consequences.
    """
    def __init__(self, state, state_service, ui):
        super().__init__(state, state_service, ui)
        self.description = "A stranger asks you for help. What do you do?"
        
        self.available_choices = {
            "1": "Help them",
            "2": "Ignore and walk away"
        }
        
        self.choice_consequences = {
            "1": {  # Help
                "good": [
                    lambda s=state, ss=state_service: MoneyGainConsequence(s, ss, 50, "They thanked you! +$50"),
                    lambda s=state, ss=state_service: SpeedGainConsequence(s, ss, 0.05, "They blessed you! +5%")
                ],
                "bad": [
                    lambda s=state, ss=state_service: MoneyLossConsequence(s, ss, 20, "They took your money! -$20"),
                    lambda s=state, ss=state_service: SpeedLossConsequence(s, ss, 0.05, "They cursed you! -5%")
                ]
            },
            "2": {  # Ignore
                "good": [
                    lambda s=state, ss=state_service: MoneyGainConsequence(s, ss, 30, "You found some loose change! +$30"),
                    lambda s=state, ss=state_service: SpeedGainConsequence(s, ss, 0.05, "You were blessed with good luck! Mining speed +5%")
                ],

                "bad": [
                    lambda s=state, ss=state_service: MoneyLossConsequence(s, ss, 10, "You got bad karma! -$10"),
                    lambda s=state, ss=state_service: SpeedLossConsequence(s, ss, 0.05, "You were cursed! Mining speed -5%")
                ]
            }
        }