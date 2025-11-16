import sys
import json
import string
import json

# Any imports from the standard library are allowed
import random

from typing import Optional
import json

class AIAction:
    """
    Represents one turn of actions in the game.
    
    Phase 1 - Pick ONE:
        - Build a tower: AIAction("build", x, y, tower_type)
        - Destroy a tower: AIAction("destroy", x, y)
        - Do nothing: AIAction("nothing", 0, 0)
    
    Phase 2 - Optional:
        - Buy mercenary: add merc_direction="N" (or "S", "E", "W")
    
    Phase 3 - Optional:
        - Provoke Demons: add provoke_demons=True
        - To be used with caution!
    
    Possible values of tower_type are:
        - "crossbow"
        - "cannon"
        - "minigun"
        - "house"
        - "church"
    
    Examples:
        AIAction("build", 5, 3, "cannon")
        AIAction("build", 5, 3, "crossbow", merc_direction="N")
        AIAction("destroy", 2, 4)
        AIAction("nothing", 0, 0, merc_direction="S", provoke_demons=True)
    """
    
    def __init__(
        self,
        action: str,
        x: int,
        y: int,
        tower_type: str = "",
        merc_direction: str = "",
        provoke_demons: bool = False
    ):
        self.action = action.lower().strip()  # "build", "destroy", or "nothing"
        self.x = x
        self.y = y
        self.tower_type = tower_type.strip()
        self.merc_direction = merc_direction.upper().strip()
        self.provoke_demons = provoke_demons
    
    def to_dict(self):
        """Convert to dictionary for saving/sending"""
        return {
            'action': self.action,
            'x': self.x,
            'y': self.y,
            'tower_type': self.tower_type,
            'merc_direction': self.merc_direction,
            'provoke_demons': self.provoke_demons
        }
    
    def to_json(self):
        return json.dumps(self.to_dict())


# -- HELPER FUNCTIONS --
def is_out_of_bounds(game_state: dict, x: int, y: int) -> bool:
    return x < 0 or x >= len(game_state['FloorTiles'][0]) or y < 0 or y >= len(game_state['FloorTiles'])

# team_color should be 'r' or 'b'
# Return a list of strings representing available mercenary queue directions like: ["N","S","W"]
def get_available_queue_directions(game_state: dict, team_color: str) -> list:
    result = []
    
    offsets = {
        (0, -1): "N",
        (0, 1): "S",
        (1, 0): "E",
        (-1, 0): "W"
    }
    
    for offset in offsets.keys():
        player = game_state['PlayerBaseR'] if team_color == 'r' else game_state['PlayerBaseB']
        target_x = player['x'] + offset[0]
        target_y = player['y'] + offset[1]
        if (not is_out_of_bounds(game_state, target_x, target_y) and
            game_state['FloorTiles'][target_y][target_x] == "O"):
            result.append(offsets[offset])
            
    return result

# team_color should be 'r' or 'b'
# Return a list of coordinates that are available for building
def get_available_build_spaces(game_state: dict, team_color: str):
    result = []
    for y, row in enumerate(game_state['FloorTiles']):
        for x, chr_at_x in enumerate(row):
            if chr_at_x == team_color:
                if game_state['EntityGrid'][y][x] == '':
                    result.append((x,y))

    return result

# team_color should be 'r' or 'b'
# Return a list of towers belonging to the selected team
def get_my_towers(game_state: dict, team_color: str):
    result = []

    for tower in game_state['Towers']:
        if tower["Team"] == team_color:
            result.append(tower)

    return result


def get_my_money_amount(game_state: dict, team_color: str) -> int:
    return game_state["RedTeamMoney"] if team_color == 'r' else game_state["BlueTeamMoney"]


# -- AGENT --
class Agent:
    def initialize_and_set_name(self, initial_game_state: dict, team_color: str) -> str:
        self.team_color = team_color

        self.num_houses = 0
        self.num_cannons = 0
        self.num_crossbows = 0
        self.num_miniguns = 0
        self.num_churches = 0 

        return "AT"
    
    def do_turn(self, game_state: dict) -> AIAction:

        available_directions = get_available_queue_directions(game_state, self.team_color)
        available_spaces = get_available_build_spaces(game_state, self.team_color)

        money = get_my_money_amount(game_state, self.team_color)
        team_towers = get_my_towers(game_state, self.team_color)
        
        turn = game_state['CurrentTurn']

        # Ensure variables exist before use
        defensive_towers = 0

        # TowerPrices fix
        tower_prices = game_state[f"TowerPrices{self.team_color.upper()}"]

        # Demons
        self.demons = list(filter(lambda o: o["Team"] == self.team_color, game_state["Demons"]))
        num_demons = len(self.demons)

        # Enemy mercenaries
        enemy_mercs = list(filter(lambda o: o["Team"] != self.team_color, game_state["Mercenaries"]))
        num_enemy_mercs = len(enemy_mercs)

        # Count defensive towers
        for t in team_towers:
            if t["Type"].lower() in ['cannon', 'crossbow', 'minigun']:
                defensive_towers += 1

        # Sorting towers
        sorted_towers = sorted(tower_prices, key=lambda t: tower_prices[t])
        sorted_def_towers = list(filter(lambda k: k in ['Crossbow','Cannon','Minigun'], sorted_towers))
        cheapest_defensive = sorted_def_towers[0].lower() if sorted_def_towers else "crossbow"

        # Conditions
        church_condition = (
            self.num_houses >= 10 and
            defensive_towers >= 3 and
            num_enemy_mercs <= 2
        )

        endgame_tower_requirement = (
            self.num_cannons >= 3 and
            self.num_crossbows >= 2 and
            self.num_churches >= 2
        )

        # If broke
        if money <= 10:
            return AIAction("nothing", 0, 0)

        # -----------
        # TURN LOGIC 
        # -----------

        if turn < 6:
            house_x, house_y = random.choice(available_spaces)
            self.num_houses += 1
            return AIAction('Build', house_x, house_y, 'house')
        
        elif turn == 6:

            if num_enemy_mercs >= 2:
                x,y = random.choice(available_spaces)
                self.num_crossbows += 1
                return AIAction('Build',x,y,'crossbow')               
                    
            else:
                house_x, house_y = random.choice(available_spaces)
                self.num_houses += 1
                return AIAction('Build', house_x, house_y,'house')
            
        elif 7 <= turn <= 10:

            if defensive_towers == 0:
                x,y = random.choice(available_spaces)
                self.num_crossbows += 1
                return AIAction('Build',x,y,'crossbow')
            
            elif num_enemy_mercs >= 3:
                x,y = random.choice(available_spaces)
                self.num_cannons += 1
                return AIAction('Build',x,y,'cannon')
            
            else:
                house_x, house_y = random.choice(available_spaces)
                self.num_houses += 1
                return AIAction('Build', house_x, house_y,'house')       
                        
        elif 11 <= turn <= 20:

            if defensive_towers < 3:
                x,y = random.choice(available_spaces)
                self.num_cannons += 1
                return AIAction('Build',x,y,'cannon')
            
            elif self.num_houses < 10 and num_enemy_mercs < 3:
                house_x, house_y = random.choice(available_spaces)
                self.num_houses += 1
                return AIAction('Build', house_x, house_y,'house')
            
            elif num_enemy_mercs >= 3:
                x,y = random.choice(available_spaces)
                self.num_cannons += 1
                return AIAction('Build',x,y,'cannon')
            
            else:

                if church_condition:
                    x,y = random.choice(available_spaces)
                    self.num_churches += 1
                    return AIAction('Build',x,y,'church')
                
                else:

                    if money >= tower_prices['Minigun']:
                        x,y = random.choice(available_spaces)
                        self.num_miniguns += 1
                        return AIAction('Build',x,y,'minigun')
                    
                    elif money >= tower_prices['Cannon']:
                        x,y = random.choice(available_spaces)
                        self.num_cannons += 1
                        return AIAction('Build',x,y,'cannon')
                    
                    else:
                        x,y = random.choice(available_spaces)
                        self.num_crossbows += 1
                        return AIAction('Build',x,y,'crossbow')
                        
        elif 21 <= turn <= 30:

            if num_enemy_mercs >= 3:
                x,y = random.choice(available_spaces)
                self.num_cannons += 1
                return AIAction('Build',x,y,'cannon')
            
            elif self.num_crossbows < 2:
                x,y = random.choice(available_spaces)
                self.num_crossbows += 1
                return AIAction('Build',x,y,'crossbow')    
                        
            elif self.num_crossbows == 2 and self.num_cannons == 3 and self.num_churches < 2:
                x,y = random.choice(available_spaces)
                self.num_churches += 1
                return AIAction('Build',x,y,'church')  
            
            elif self.num_churches >= 2:

                if money > 50:
                    x,y = random.choice(available_spaces)
                    self.num_miniguns += 1
                    return AIAction('Build',x,y,'minigun')
                
                else:
                    x,y = random.choice(available_spaces)
                    if cheapest_defensive == 'crossbow':
                        self.num_crossbows += 1
                    elif cheapest_defensive == 'cannon':
                        self.num_cannons += 1
                    elif cheapest_defensive == 'minigun':
                        self.num_miniguns += 1

                    return AIAction('Build',x,y,cheapest_defensive)

        elif turn >= 30:

            if not endgame_tower_requirement:
                if self.num_cannons <= 3:
                    x,y = random.choice(available_spaces)
                    self.num_cannons += 1
                    return AIAction('Build',x,y,'cannon')
                
                if self.num_churches <= 2:
                    x,y = random.choice(available_spaces)
                    self.num_churches += 1
                    return AIAction('Build',x,y,'church') 
                
                if self.num_crossbows <= 2:
                    x,y = random.choice(available_spaces)
                    self.num_crossbows += 1
                    return AIAction('Build',x,y,'crossbow')    
                
            elif num_demons >= 5:
                x,y = random.choice(available_spaces)
                self.num_crossbows += 1
                return AIAction('Build',x,y,'crossbow')

            elif num_enemy_mercs >= 3:
                x,y = random.choice(available_spaces)
                self.num_cannons += 1
                return AIAction('Build',x,y,'cannon')   

            elif money >= 50:
                x,y = random.choice(available_spaces)
                self.num_miniguns += 1
                return AIAction('Build',x,y,'minigun')   

        return AIAction("nothing", 0, 0)


# -- DRIVER CODE  --
if __name__ == '__main__':

    # figure out if we're red or blue
    team_color = 'r' if input() == "--YOU ARE RED--" else 'b'

    # get initial game state
    input_buffer = [input()]
    while input_buffer[-1] != "--END INITIAL GAME STATE--":
        input_buffer.append(input())
    game_state_init = json.loads(''.join(input_buffer[:-1]))

    # create and initialize agent, set team name
    agent = Agent()
    print(agent.initialize_and_set_name(game_state_init, team_color))

    # perform first action
    print(agent.do_turn(game_state_init).to_json())

    # loop until the game is over
    while True:
        # get this turn's state
        input_buffer = [input()]
        while input_buffer[-1] != "--END OF TURN--":
            input_buffer.append(input())
        game_state_this_turn = json.loads(''.join(input_buffer[:-1]))

        # get agent action, then send it to the game server
        print(agent.do_turn(game_state_this_turn).to_json())