import sys
import json
import string
import json
import math

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

def dist( p0: tuple[int,int], p1: tuple[int,int] ):
    a = abs(p0[0] - p1[0])
    b = abs(p0[1] - p1[1])
    return math.sqrt( a**2 + b**2 )

def ordered(pos: tuple[int,int], options: list) -> tuple[int,int]:
    opts_with_dist = []
    for opt in options:
        opts_with_dist.append({'p':opt, 'd':dist(opt,pos)})
    return list(sorted(opts_with_dist, key=lambda d:d['d']))

def get_base_pos(game_state: dict, team_color: str) -> tuple[int,int]:
    data = game_state[f"PlayerBase{team_color.upper()}"]
    return (int(data['x']),int(data['y']))

def other_color(color: str) -> str:
    return 'b' if color == 'r' else 'r'

def enemy_base_pos(game_state: dict, team_color: str) -> tuple[int,int]:
    return get_base_pos( game_state, other_color( team_color ) )

# -- AGENT --
class Agent:
    def initialize_and_set_name(self, initial_game_state: dict, team_color: str) -> str:
        self.team_color = team_color

        self.num_houses = 0
        self.num_cannons = 0
        self.num_crossbows = 0
        self.num_miniguns = 0
        self.num_churches = 0 

        # merc-related state
        self.last_merc_lane = None
        self.same_lane_count = 0
        self.burst_cooldown = 0
        self.burst_sent_this_cycle = 0

        return "AT"
    
    def do_turn(self, game_state: dict) -> AIAction:

        available_directions = get_available_queue_directions(game_state, self.team_color)
        available_spaces = get_available_build_spaces(game_state, self.team_color)

        ordered_build_options = ordered( enemy_base_pos( game_state, self.team_color ), available_spaces )
        house_x, house_y = ordered_build_options[-1]['p']
        defensive_x, defensive_y = ordered_build_options[0]['p']


        money = get_my_money_amount(game_state, self.team_color)
        team_towers = get_my_towers(game_state, self.team_color)
        
        turn = game_state['CurrentTurn']

        defensive_towers = 0

        tower_prices = game_state[f"TowerPrices{self.team_color.upper()}"]

        self.demons = list(filter(lambda o: o["Team"] == self.team_color, game_state.get("Demons", [])))
        num_demons = len(self.demons)

        enemy_mercs = list(filter(lambda o: o["Team"] != self.team_color, game_state.get("Mercenaries", [])))
        num_enemy_mercs = len(enemy_mercs)

        for t in team_towers:
            if t["Type"].lower() in ['cannon', 'crossbow', 'minigun']:
                defensive_towers += 1

        sorted_towers = sorted(tower_prices, key=lambda t: tower_prices[t])
        sorted_def_towers = list(filter(lambda k: k in ['Crossbow','Cannon','Minigun'], sorted_towers))
        cheapest_defensive = sorted_def_towers[0].lower() if sorted_def_towers else "crossbow"

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

        # -----------------------
        # MERCENARY STRATEGY HELPERS
        # -----------------------

        def get_my_lane_directions(game_state, team_color):
            # just return available directions
            return get_available_queue_directions(game_state, team_color)

        def lane_from_direction(game_state, team_color, direction):
            valid_dirs = get_available_queue_directions(game_state, team_color)
            if direction not in valid_dirs:
                return None
            sorted_dirs = sorted(valid_dirs)
            return sorted_dirs.index(direction)

        def score_lane(game_state, team_color, direction):
            lane_index = lane_from_direction(game_state, team_color, direction)
            if lane_index is None:
                return -9999

            my_towers = [t for t in game_state.get("Towers", []) if t["Team"] == team_color]
            enemy_mercs = [m for m in game_state.get("Mercenaries", []) if m["Team"] != team_color]

            score = 0
            defense = sum(1 for t in my_towers if t.get("Lane") == lane_index and t["Type"].lower() in ["crossbow","cannon","minigun"])
            score += max(0, 5 - defense) * 5

            enemy_pressure = sum(1 for m in enemy_mercs if m.get("Lane") == lane_index)
            score += enemy_pressure * 8

            score += random.randint(-2, 2)

            # Demon spawner proximity
            demon_spawners = game_state.get("DemonSpawners", [])
            for spawner in demon_spawners:
            # If this lane points to a spawner, add points
                if spawner.get("Lane") == lane_index:
                    score += 50  # weight to prioritize demon spawners

            return score

        def choose_best_lane(game_state, team_color):
            valid_dirs = get_my_lane_directions(game_state, team_color)
            if not valid_dirs:
                return None

            scored = [(score_lane(game_state, team_color, d), d) for d in valid_dirs]
            scored.sort(reverse=True, key=lambda x: x[0])
            return scored[0][1]

        def _choose_merc_direction():
            # pick best lane if possible
            if not available_directions or money < 10:
                return ""
            return choose_best_lane(game_state, self.team_color)

        def make_action(action: str, x: int, y: int, tower_type: str):
            return AIAction(action, x, y, tower_type, merc_direction=_choose_merc_direction())

        def make_action_no_build(action: str):
            return AIAction(action, 0, 0, "", merc_direction=_choose_merc_direction())

        if money <= 10:
            return make_action_no_build("nothing")
        
        

        # -----------
        # TURN LOGIC (unchanged behavior, only using make_action wrappers)
        # -----------

        if turn < 6:
            self.num_houses += 1
            return make_action('Build', house_x, house_y, 'house')
        
        elif turn == 6:

            if num_enemy_mercs >= 2:
                x,y = random.choice(available_spaces)
                self.num_crossbows += 1
                return make_action('Build', defensive_x, defensive_y, 'crossbow')               
                    
            else:
                self.num_houses += 1
                return make_action('Build', house_x, house_y, 'house')
            
        elif 7 <= turn <= 10:

            if defensive_towers == 0:
                x,y = random.choice(available_spaces)
                self.num_crossbows += 1
                return make_action('Build', defensive_x, defensive_y, 'crossbow')
            
            elif num_enemy_mercs >= 3:
                x,y = random.choice(available_spaces)
                self.num_cannons += 1
                return make_action('Build', defensive_x, defensive_y, 'cannon')
            
            else:
                self.num_houses += 1
                return make_action('Build', house_x, house_y, 'house')       
                        
        elif 11 <= turn <= 20:

            if defensive_towers < 3:
                x,y = random.choice(available_spaces)
                self.num_cannons += 1
                return make_action('Build', defensive_x, defensive_y, 'cannon')
            
            elif self.num_houses < 10 and num_enemy_mercs < 3:
                self.num_houses += 1
                return make_action('Build', house_x, house_y, 'house')
            
            elif num_enemy_mercs >= 3:
                x,y = random.choice(available_spaces)
                self.num_cannons += 1
                return make_action('Build', defensive_x, defensive_y, 'cannon')
            
            else:

                if church_condition:
                    x,y = random.choice(available_spaces)
                    self.num_churches += 1
                    return make_action('Build', x, y, 'church')
                
                else:

                    if money >= tower_prices['Minigun']:
                        x,y = random.choice(available_spaces)
                        self.num_miniguns += 1
                        return make_action('Build', defensive_x, defensive_y, 'minigun')
                    
                    elif money >= tower_prices['Cannon']:
                        x,y = random.choice(available_spaces)
                        self.num_cannons += 1
                        return make_action('Build', defensive_x, defensive_y, 'cannon')
                    
                    else:
                        x,y = random.choice(available_spaces)
                        self.num_crossbows += 1
                        return make_action('Build', defensive_x, defensive_y, 'crossbow')
                        
        elif 21 <= turn <= 30:

            if num_enemy_mercs >= 3:
                x,y = random.choice(available_spaces)
                self.num_cannons += 1
                return make_action('Build', defensive_x, defensive_y, 'cannon')
            
            elif self.num_crossbows < 2:
                x,y = random.choice(available_spaces)
                self.num_crossbows += 1
                return make_action('Build', defensive_x, defensive_y, 'crossbow')    
                        
            elif self.num_crossbows == 2 and self.num_cannons == 3 and self.num_churches < 2:
                x,y = random.choice(available_spaces)
                self.num_churches += 1
                return make_action('Build', x, y, 'church')  
            
            elif self.num_churches >= 2:

                if money > 50:
                    x,y = random.choice(available_spaces)
                    self.num_miniguns += 1
                    return make_action('Build', defensive_x, defensive_y, 'minigun')
                
                else:
                    x,y = random.choice(available_spaces)
                    if cheapest_defensive == 'crossbow':
                        self.num_crossbows += 1
                    elif cheapest_defensive == 'cannon':
                        self.num_cannons += 1
                    elif cheapest_defensive == 'minigun':
                        self.num_miniguns += 1

                    return make_action('Build', defensive_x, defensive_y, cheapest_defensive)

        elif turn >= 30:

            if not endgame_tower_requirement:
                if self.num_cannons <= 3:
                    x,y = random.choice(available_spaces)
                    self.num_cannons += 1
                    return make_action('Build', defensive_x, defensive_y, 'cannon')
                
                if self.num_churches <= 2:
                    x,y = random.choice(available_spaces)
                    self.num_churches += 1
                    return make_action('Build', x, y, 'church') 
                
                if self.num_crossbows <= 2:
                    x,y = random.choice(available_spaces)
                    self.num_crossbows += 1
                    return make_action('Build', defensive_x, defensive_y, 'crossbow')    
                
            elif num_demons >= 5:
                x,y = random.choice(available_spaces)
                self.num_crossbows += 1
                return make_action('Build', defensive_x, defensive_y, 'crossbow')

            elif num_enemy_mercs >= 3:
                x,y = random.choice(available_spaces)
                self.num_cannons += 1
                return make_action('Build', defensive_x, defensive_y, 'cannon')   

            elif money >= 50:
                x,y = random.choice(available_spaces)
                self.num_miniguns += 1
                return make_action('Build', defensive_x, defensive_y, 'minigun')   

        # fallback: attempt to send a merc if strategy allows, else do nothing
        md = _choose_merc_direction()
        if md and money >= 10:
            return AIAction('nothing', 0, 0, "", merc_direction=md)

        return make_action_no_build("nothing")


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